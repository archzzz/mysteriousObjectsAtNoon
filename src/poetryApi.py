import os

import requests
from firebase_admin import credentials, initialize_app, auth, db
from flask import Flask, abort
from flask_cors import CORS
from flask_httpauth import HTTPTokenAuth
from flask_restful import Resource, Api, reqparse
from transloadit import client
import multiprocessing
import neuralsnap
from temporaryDirectory import TemporaryDirectory

from google.oauth2 import service_account
from google.auth.transport.requests import Request
from pprint import pprint
import firebasePython


app = Flask(__name__)
CORS(app)
api = Api(app)
http_token_auth = HTTPTokenAuth(scheme='Token')

app.config.from_pyfile("../config/app.default_settings")
app.config.from_envvar("POND_SERVICE_SETTINGS")

firebase_cred = credentials.Certificate(app.config["FIREBASE_CREDENTIAL"])
firebase_app = initialize_app(firebase_cred, {'databaseURL': app.config["FIREBASE_DATABASE_URL"]})
ref = db.reference()

transloadit_client = client.Transloadit(app.config['TRANSLOADIT_KEY'], app.config['TRANSLOADIT_SECRET'])

IMAGE_URI = 'imageUri'
VIDEO_URI = 'videoUri'
MIME = 'mime'
VIDEO_DURATION = 'duration'
PROCESSING_MSG = "the pond is singing and the pond is warm and the pond is starting to give form"


@http_token_auth.verify_token
def verify_token(token):
    if app.config["ENABLE_AUTH"]:
        try:
            auth.verify_id_token(token)
            return True
        except ValueError:
            print 'Authentication failed'
            return False
    return True


class PoetryApi(Resource):
    parse = reqparse.RequestParser()
    parse.add_argument(IMAGE_URI, type=str)
    parse.add_argument(MIME, type=str, default="")

    decorators = [http_token_auth.login_required]

    def get(self):
        args = self.parse.parse_args()
        mime = args[MIME].split('/')

        if mime[0] != 'image':
            abort(400, "Invalid input type: audio or video")

        result = ref.child('texts').child(encode_for_firebase(args[IMAGE_URI])).get()
        if result is None:
            pprint("Item not found in firebase, the image {} is being processed.".format(args[IMAGE_URI]))
            return {'poetry': PROCESSING_MSG}

        if 'text' in result:
            pprint("Returning result for {}".format(args[IMAGE_URI]))
            return result['text']

        if 'error' in result:
            pprint("Returning error for {}".format(args[IMAGE_URI]))
            return {'poetry': result['error']}


class CaptionApi(Resource):
    parse = reqparse.RequestParser()
    parse.add_argument(VIDEO_URI, type=str)
    parse.add_argument(MIME, type=str, default="")
    parse.add_argument(VIDEO_DURATION, type=float, default=2)

    decorators = [http_token_auth.login_required]

    def get(self):
        args = self.parse.parse_args()
        mime = args[MIME].split('/')

        if mime[0] != 'video':
            abort(400, "Invalid input type: image or audio")

        result = ref.child('texts').child(encode_for_firebase(args[VIDEO_URI])).get()
        if result is None:
            pprint("Item not found in firebase, the video {} is being processed.".format(args[VIDEO_URI]))
            return {'captions': PROCESSING_MSG}

        if 'text' in result:
            pprint("Returning result for {}".format(args[VIDEO_URI]))
            return result['text']

        if 'error' in result:
            pprint("Returning error for {}".format(args[VIDEO_URI]))
            return {'captions': result['error']}


class MediaDownloader(object):
    def __init__(self, folder_name):
        self.folder_name = folder_name

    def __call__(self, thumbnail):
        return download_media(
            thumbnail["ssl_url"],
            self.folder_name,
            "{}_{}".format(self.count_helper(thumbnail["meta"]["thumb_index"]), thumbnail["name"]))

    @staticmethod
    def count_helper(count):
        if count < 10:
            return "000" + str(count)
        elif count < 100:
            return "00" + str(count)
        elif count < 1000:
            return "0" + str(count)
        else:
            return str(count)


def download_media(url, folder_name, file_name):
    image_data = requests.get(url).content
    with open(os.path.join(folder_name, file_name), 'wb') as f:
        f.write(image_data)
        return f.name


def get_image_narrator(folder_name, num_images=-1):
    return neuralsnap.ImageNarrator(
        app.config["NEURALTALK_MODEL_PATH"],
        app.config["NEURALTALK_LIB_PATH"],
        app.config["RNN_MODEL_PATH"],
        app.config["RNN_LIB_PATH"],
        folder_name,
        str(num_images),
        enable_gpu=app.config["ENABLE_GPU"])


def get_poetry(mime, image_url):
    with TemporaryDirectory() as temp_dir:
        download_media(image_url, temp_dir, "img.{}".format(mime[1]))
        result = get_image_narrator(temp_dir, num_images=1).get_neuralsnap_result()[0]

    return {'poetry': result['text']}


def get_caption(video_url, duration):
    with TemporaryDirectory() as temp_dir:
        assembly = transloadit_client.new_assembly(params={
            "template_id": app.config['TRANSLOADIT_THUMBNAIL_TEMPLATE_ID'],
        })
        assembly.add_step("imported", "/http/import", {"url": video_url})
        assembly.add_step('thumbnailed', "/video/thumbs", {"count": duration // 2})

        thumbnails = assembly.create(retries=5, wait=True).data["results"]["thumbnailed"]

        multiprocessing.Pool(processes=4).map(MediaDownloader(temp_dir), thumbnails)

        captions = get_image_narrator(temp_dir).get_video_captions()

    return {
        'captions':
            [{"offset": thumbnail["meta"]["thumb_offset"], "caption": caption["caption"]} for thumbnail, caption in
             zip(thumbnails, captions)]
    }


#################################
# Listen on firebase item change and process new items.

# Define the required scopes
scopes = [
  "https://www.googleapis.com/auth/userinfo.email",
  "https://www.googleapis.com/auth/firebase.database"
]

def processStream(stream):
    data = stream[1]['data']
    if data is None:
        return
    try:
        if 'results' in data:
            generate_and_save_text(data)
        elif type(data) is dict:
            for key, value in data.items():
                if value is not None and 'results' in value:
                    url = value['results']['encode']['ssl_url']
                    text = ref.child('texts').child(encode_for_firebase(url)).get()
                    if text is not None:
                        pprint("Skipping url {}".format(url))
                        continue

                    generate_and_save_text(value)
    except:
        pprint("Failed to process data: {}".format(data))


def generate_and_save_text(data):
    mime = data['results']['encode']['mime'].split('/')
    url = data['results']['encode']['ssl_url']
    text_id = encode_for_firebase(url)

    result = None
    try:
        if mime[0] == 'image':
            pprint("Processing image: {}".format(url))
            result = get_poetry(mime, url)
        if mime[0] == 'video':
            pprint("Processing video: {}".format(url))
            duration = data['results']['original']['meta']['duration']
            result = get_caption(url, duration)
    except:
        pprint('Failed to process: {}'.format(url))
        ref.child('texts').child(text_id).set({
            'url': url,
            'error': 'Failed to process, please upload again'
        })
        return

    pprint("Getting result {} for {}".format(result, url))

    if result is not None:
        pprint("Uploading result for: {}".format(url))
        ref.child('texts').child(text_id).set({
            'url': url,
            'text': result
        })


def encode_for_firebase(text):
    return text.replace('/', '_S') \
        .replace('.', '_P') \
        .replace('$', '_D') \
        .replace('#', '_H') \
        .replace('[', '_O') \
        .replace(']', '_C')

# Authenticate a credential with the service account
oauth_credentials = service_account.Credentials.from_service_account_file(app.config["FIREBASE_CREDENTIAL"], scopes=scopes)
oauth_credentials.refresh(Request())
access_token = oauth_credentials.token

stream_url = "{}/items.json?access_token={}".format(app.config["FIREBASE_DATABASE_URL"], access_token)
pprint("stream url: {}".format(stream_url))
S = firebasePython.subscriber(stream_url, processStream)
S.start()

pprint(firebasePython.get(stream_url))

api.add_resource(PoetryApi, '/poetry')
api.add_resource(CaptionApi, '/caption')

if __name__ == '__main__':
    app.run(host="0.0.0.0")






