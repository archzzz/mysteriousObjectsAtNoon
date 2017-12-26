import os

import requests
from firebase_admin import credentials, initialize_app, auth
from flask import Flask, abort
from flask_cors import CORS
from flask_httpauth import HTTPTokenAuth
from flask_restful import Resource, Api, reqparse
from transloadit import client

import neuralsnap
from temporaryDirectory import TemporaryDirectory

app = Flask(__name__)
app.config.from_object("../app-config.cfg")
CORS(app)
api = Api(app)
http_token_auth = HTTPTokenAuth(scheme='Token')

cred = credentials.Certificate('/opt/neural-networks/firebase-key.json')
firebase_app = initialize_app(cred)

transloadit_client = client.Transloadit(app.config['TRANSLOADIT_KEY'], app.config['TRANSLOADIT_SECRET'])

RNN_MODEL = '/opt/neural-networks/models/2016-01-12_char-rnn_model_01_rg.t7'
NEURALTALK_MODEL = '/opt/neural-networks/models/2016-01-12_neuraltalk2_model_01_rg.t7'
IMAGE_URI = 'imageUri'
VIDEO_URI = 'videoUri'
MIME = 'mime'

@http_token_auth.verify_token
def verify_token(token):
    # try:
    #     auth.verify_id_token(token)
    #     return True
    # except ValueError:
    #     print 'Authentication failed'
    #     return False
    return True

class PoetryApi(Resource):
    parse = reqparse.RequestParser()
    parse.add_argument(IMAGE_URI, type=str)
    parse.add_argument(MIME, type=str)

    decorators = [http_token_auth.login_required]

    def get(self):
        args = self.parse.parse_args()
        mime = args[MIME].split('/')

        if mime == None or mime[0] != 'image':
            abort(400, "Invalid input type: audio or video")

        with TemporaryDirectory() as temp_dir:
            download_media(args[IMAGE_URI], mime[1], temp_dir)
            result = get_poetry(temp_dir)

        return {'poetry': result['text']}

class CaptionApi(Resource):
    parse = reqparse.RequestParser()
    parse.add_argument(VIDEO_URI, type=str)
    parse.add_argument(MIME, type=str)

    decorators = [http_token_auth.login_required]

    def get(self):
        args = self.parse.parse_args()
        mime = args[MIME].split('/')

        if mime == None or mime[0] != 'video':
            abort(400, "Invalid input type: image or audio")

        with TemporaryDirectory() as temp_dir:
            data = transloadit_client.new_assembly(params={
                "template_id": app.config['TRANSLOADIT_TEMPLATE_ID'],
                "steps": [
                    {"imported": {"url": args[VIDEO_URI]}},
                    {"thumbnailed": {"count": 5}},
                ],
            }).create(retries=5, wait=True).data

        return {'captions': data}


def download_media(url, type, folder_name):
    image_data = requests.get(url).content
    with open(os.path.join(folder_name, 'input.{}'.format(type)), 'wb') as f:
        f.write(image_data)
        return f.name

def get_poetry(folder_name):
    expander = neuralsnap.ImageNarrator(NEURALTALK_MODEL, RNN_MODEL, folder_name, "1")
    result = expander.get_neuralsnap_result()
    return result[0]


def get_video_caption(folder_name, video):
    expander = neuralsnap.ImageNarrator(NEURALTALK_MODEL, RNN_MODEL, folder_name, "-1")
    expander.get_video_captions(video)
    return ""


api.add_resource(PoetryApi, '/poetry')
api.add_resource(CaptionApi, '/caption')

if __name__ == '__main__':
    app.run(host="0.0.0.0")






