from flask import Flask
from flask_restful import Resource, Api, reqparse
from flask_httpauth import HTTPTokenAuth
from firebase_admin import credentials, auth, initialize_app
import requests
import json
from pprint import pprint
import os
from neuralsnap import neuralsnap
from temporaryDirectory import TemporaryDirectory

app = Flask(__name__, instance_path='/tmp/instance')
api = Api(app)
http_token_auth = HTTPTokenAuth(scheme='Token')

cred = credentials.Certificate('/Users/annzhang/workspace/blazing-heat-1438-firebase-adminsdk-h3irc-12eaf69af0.json')
firebase_app = initialize_app(cred)


@http_token_auth.verify_token
def verify_token(token):
    # print 'Token: %s' % token
    # try:
    #     decoded_token = auth.verify_id_token(token)
    #     print decoded_token
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

    output_title = 'test'
    rnn_model_fp = '/Users/annzhang/PycharmProjects/brittanyService/neuralsnap/models/2016-01-12_char-rnn_model_01_rg.t7'
    ntalk_model_fp = '/Users/annzhang/PycharmProjects/brittanyService/neuralsnap/models/2016-01-12_neuraltalk2_model_01_rg.t7'
    image_folder_fp = os.path.join(app.instance_path, folder_name)

    expander = neuralsnap.ImageNarrator(output_title, ntalk_model_fp, rnn_model_fp, image_folder_fp)

    result = expander.get_result()
    return result[0]


api.add_resource(Brittany, '/poetry')

if __name__ == '__main__':
    app.run()







