#!/bin/bash

if [ -z "$1" ]
    then
        echo "No AWS_ACCESS_KEY_ID supplied"
        exit 1
fi

if [ -z "$2" ]
    then
        echo "no AWS_SECRET_ACCESS_KEY supplied"
        exit 1
fi

export AWS_ACCESS_KEY_ID=$1
export AWS_SECRET_ACCESS_KEY=$2

rm -f *.t7*

aws s3 cp s3://pond-service/models/char-rnn_model_cpu_01.t7 char-rnn_model_cpu_01.t7
aws s3 cp s3://pond-service/models/char-rnn_model_gpu_01.t7 char-rnn_model_gpu_01.t7
aws s3 cp s3://pond-service/models/neuraltalk2_model_01.t7 neuraltalk2_model_01.t7