import os

import requests
from firebase_admin import credentials, initialize_app, auth
from flask import Flask, abort
from flask_cors import CORS
from flask_httpauth import HTTPTokenAuth
from flask_restful import Resource, Api, reqparse
from transloadit import client
import multiprocessing
import neuralsnap
from temporaryDirectory import TemporaryDirectory

app = Flask(__name__)
CORS(app)
api = Api(app)
http_token_auth = HTTPTokenAuth(scheme='Token')

app.config.from_pyfile("../config/app.default_settings")
app.config.from_envvar("POND_SERVICE_SETTINGS")

cred = credentials.Certificate(app.config["FIREBASE_CREDENTIAL"])
firebase_app = initialize_app(cred)

transloadit_client = client.Transloadit(app.config['TRANSLOADIT_KEY'], app.config['TRANSLOADIT_SECRET'])

IMAGE_URI = 'imageUri'
VIDEO_URI = 'videoUri'
MIME = 'mime'
VIDEO_DURATION = 'duration'


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

        with TemporaryDirectory() as temp_dir:
            download_media(args[IMAGE_URI], temp_dir, "img.{}".format(mime[1]))
            result = self.get_poetry(temp_dir)

        return {'poetry': result['text']}

    @staticmethod
    def get_poetry(folder_name):
        return get_image_narrator(folder_name, num_images=1).get_neuralsnap_result()[0]


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

        with TemporaryDirectory() as temp_dir:
            assembly = transloadit_client.new_assembly(params={
                "template_id": app.config['TRANSLOADIT_THUMBNAIL_TEMPLATE_ID'],
            })
            assembly.add_step("imported", "/http/import", {"url": args[VIDEO_URI]})
            assembly.add_step('thumbnailed', "/video/thumbs", {"count": args[VIDEO_DURATION] // 2})

            thumbnails = assembly.create(retries=5, wait=True).data["results"]["thumbnailed"]

            multiprocessing.Pool(processes=4).map(MediaDownloader(temp_dir), thumbnails)

            captions = self.get_video_caption(temp_dir)

        return {
            'captions':
                [{"offset": thumbnail["meta"]["thumb_offset"], "caption": caption["caption"]} for thumbnail, caption in zip(thumbnails, captions)]
        }

    @staticmethod
    def get_video_caption(folder_name):
        return get_image_narrator(folder_name).get_video_captions()


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


api.add_resource(PoetryApi, '/poetry')
api.add_resource(CaptionApi, '/caption')

if __name__ == '__main__':
    app.run(host="0.0.0.0")






