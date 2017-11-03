import json
import os

import requests
from firebase_admin import credentials, initialize_app
from flask import Flask
from flask_httpauth import HTTPTokenAuth
from flask_restful import Resource, Api, reqparse

import neuralsnap
from temporaryDirectory import TemporaryDirectory

app = Flask(__name__)
api = Api(app)
http_token_auth = HTTPTokenAuth(scheme='Token')

cred = credentials.Certificate('/opt/neural-networks/firebase-key.json')
firebase_app = initialize_app(cred)


@http_token_auth.verify_token
def verify_token(token):
    # try:
    #     decoded_token = auth.verify_id_token(token)
    #     return True
    # except ValueError:
    #     print 'Authentication failed'
    #     return False
    return True


parse = reqparse.RequestParser()
parse.add_argument('imageUri', type=str)


class Brittany(Resource):
    decorators = [http_token_auth.login_required]

    def get(self):
        args = parse.parse_args()

        with TemporaryDirectory() as temp_dir:
            print "temp: " + temp_dir
            get_image_from_transloadit(args['imageUri'], temp_dir)
            result = get_poetry(temp_dir)

        return {'poetry': result['text']}


def get_image_from_transloadit(url, folder_name):
    print url
    response = json.loads(requests.get(url).content)
    image =response['results']['encode'][0]

    if image['type'] != 'image':
        raise Exception()

    image_data = requests.get(image['url']).content
    with open(os.path.join(folder_name, 'input.jpg'), 'wb') as f:
        f.write(image_data)


def get_poetry(folder_name):
    rnn_model_fp = '/opt/neural-networks/models/2016-01-12_char-rnn_model_01_rg.t7'
    ntalk_model_fp = '/opt/neural-networks/models/2016-01-12_neuraltalk2_model_01_rg.t7'

    expander = neuralsnap.ImageNarrator(ntalk_model_fp, rnn_model_fp, folder_name)

    result = expander.get_result()
    return result[0]


api.add_resource(Brittany, '/poetry')

if __name__ == '__main__':
    app.run(host="0.0.0.0")






