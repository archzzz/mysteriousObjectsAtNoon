
# coding: utf-8

# NeuralSnap image-to-text poetry generator
# Copyright (C) 2016  Ross Goodwin

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# You may contact Ross Goodwin via email at ross.goodwin@gmail.com or
# address physical correspondence to:

#                     Ross Goodwin c/o ITP
#                     721 Broadway, 4th Floor
#                     New York, NY 10003


# NeuralSnap
# 
# Works by generating a caption for an image with recurrent and
# convolutional neural networks using NeuralTalk2. That
# (brief) caption is then expanded into a poem using a second
# recurrent neural network.
# 
# Ross Goodwin, 2016

import sys
import subprocess
import json
from pprint import pprint
import time


class ImageNarrator(object):

    def __init__(self, ntalk_model_fp, rnn_model_fp, image_folder_fp,
                 stanza_len=512, num_steps=16, tgt_steps=[9]):
        self.ntalk_model_fp = ntalk_model_fp
        self.rnn_model_fp = rnn_model_fp
        self.image_folder_fp = image_folder_fp

        self.num_images = '1'
        self.stanza_len = str(stanza_len)
        self.num_steps = num_steps
        self.tgt_steps = tgt_steps

        self.NEURALTALK2_PATH = "/opt/neural-networks/lib/neuraltalk2"
        self.CHARRNN_PATH = "/opt/neural-networks/lib/char-rnn"

    def get_result(self):
        self.neuraltalk()

        with open(self.image_folder_fp +'/vis.json') as caption_json:
            caption_obj_list = json.load(caption_json)

        if len(caption_obj_list) is not 1:
            raise Exception("Image folder should have only one image, not {}".format(len(caption_obj_list)))

        return self.charnn(caption_obj_list)

    def neuraltalk(self):
        # NeuralTalk2 Image Captioning
        ntalk_cmd_list = [
            'th',
            'eval.lua',
            '-model',
            self.ntalk_model_fp,
            '-image_folder',
            self.image_folder_fp,
            '-num_images',
            self.num_images,
            '-gpuid',
            '-1',
        ]

        print "INIT NEURALTALK2 CAPTIONING"

        ntalk_proc = subprocess.Popen(ntalk_cmd_list, cwd=self.NEURALTALK2_PATH)
        print ntalk_proc.communicate()[0]

    def charnn(self, caption_obj_list):
        expansion_obj_list = list()
        caption_obj_list *= self.num_steps

        print "INIT CHAR-RNN EXPANSION"

        for i in self.tgt_steps:
            obj = caption_obj_list[i]
            caption = obj['caption']
            prepped_caption = caption[0].upper() + caption[1:]
            
            temp = str((i+1.0)/float(self.num_steps))
            print "EXPANDING AT TEMPERATURE " + temp
            
            rnn_cmd_list = [
                'th',
                'sample.lua',
                self.rnn_model_fp,
                '-length',
                self.stanza_len,
                '-verbose',
                '0',
                '-temperature',
                temp,
                '-primetext',
                prepped_caption,
                '-gpuid',
                '-1'
            ]

            rnn_proc = subprocess.Popen(
                rnn_cmd_list,
                stdout=subprocess.PIPE,
                cwd=self.CHARRNN_PATH
            )
            expansion = rnn_proc.stdout.read()
            
            expansion_obj_list.append({
                'id': obj['image_id'],
                'text': expansion
            })

        return expansion_obj_list


if __name__ == '__main__':

    start_time = time.time()

    script, ntalk_model_fp, rnn_model_fp, image_folder_fp = sys.argv
    expander = ImageNarrator(ntalk_model_fp, rnn_model_fp, image_folder_fp)
    result = expander.get_result()
    pprint(result)

    end_time = time.time()
    print end_time - start_time


