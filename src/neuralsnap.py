
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
from subprocess import PIPE


class ImageNarrator(object):

    def __init__(self, ntalk_model_fp, ntalk_lib_path, rnn_model_fp, rnn_lib_path, image_folder_fp, num_images,
                 stanza_len=512, num_steps=16, tgt_steps=[9], enable_gpu=False):
        self.ntalk_model_fp = ntalk_model_fp
        self.rnn_model_fp = rnn_model_fp
        self.image_folder_fp = image_folder_fp

        self.num_images = num_images
        self.stanza_len = str(stanza_len)
        self.num_steps = num_steps
        self.tgt_steps = tgt_steps

        self.ntalk_lib_path = ntalk_lib_path
        self.rnn_lib_path = rnn_lib_path

        self.enable_gpu = enable_gpu

    def get_neuralsnap_result(self):
        self.neuraltalk()

        with open(self.image_folder_fp +'/vis.json') as caption_json:
            caption_obj_list = json.load(caption_json)

        if len(caption_obj_list) is not 1:
            raise Exception("Image folder should have only one image, not {}".format(len(caption_obj_list)))

        return self.charnn(caption_obj_list)

    def get_video_captions(self):
        self.neuraltalk()
        with open(self.image_folder_fp + '/vis.json') as caption_json:
            return json.load(caption_json)

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
            '0' if self.enable_gpu else '-1',
        ]

        print "INIT NEURALTALK2 CAPTIONING"

        ntalk_proc = subprocess.Popen(ntalk_cmd_list, stdout=PIPE, stderr=PIPE, cwd=self.ntalk_lib_path)
        output, error = ntalk_proc.communicate()
        if ntalk_proc.returncode != 0:
            raise Exception("Neural talk failed: %d %s, %s" % (ntalk_proc.returncode, output, error))

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
                '0' if self.enable_gpu else '-1'
            ]

            rnn_proc = subprocess.Popen(rnn_cmd_list, stdout=PIPE, stderr=PIPE, cwd=self.rnn_lib_path)

            expansion, error = rnn_proc.communicate()
            if rnn_proc.returncode != 0:
                raise Exception("RNN failed with code: %d and error: %s" % (rnn_proc.returncode, error))

            expansion_obj_list.append({
                'id': obj['image_id'],
                'text': expansion
            })

        return expansion_obj_list


if __name__ == '__main__':

    start_time = time.time()

    script, ntalk_model_fp, rnn_model_fp, image_folder_fp = sys.argv
    expander = ImageNarrator(ntalk_model_fp, rnn_model_fp, image_folder_fp)
    result = expander.get_neuralsnap_result()
    pprint(result)

    end_time = time.time()
    print end_time - start_time


