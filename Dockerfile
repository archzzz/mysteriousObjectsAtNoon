FROM ubuntu:trusty

MAINTAINER Samuel Cozannet <samuel.cozannet@madeden.com>

ENV FIREBASE_CREDENTIAL "config/blazing-heat-1438-firebase-adminsdk-h3irc-12eaf69af0.json"

RUN apt-get update 
RUN sudo apt-get -y install \
        git \
        build-essential \
        cmake \
        wget \
        curl \
        libatlas-base-dev \
        gfortran \
        software-properties-common \
        python-software-properties \
        python-numpy

RUN apt-get upgrade -yqq && \
    apt-get install -yqq nano curl git wget libprotobuf-dev protobuf-compiler libhdf5-serial-dev hdf5-tools python-pip build-essential python-dev && \
    mkdir -p /opt/neural-networks

# Install torch
RUN cd /opt/neural-networks && \
    wget https://raw.githubusercontent.com/torch/ezinstall/master/install-deps && \
    chmod +x ./install-deps && \
    ./install-deps && \
    git clone https://github.com/torch/distro.git /opt/neural-networks/torch --recursive && \
    cd /opt/neural-networks/torch && \
    ./install.sh -b 

ENV PATH="/opt/neural-networks/torch/install/bin:${PATH}"

# Install additional dependencies
RUN cd /opt/neural-networks/torch && \
    . /opt/neural-networks/torch/install/bin/torch-activate && \
    luarocks install nn && \
    luarocks install nngraph && \
    luarocks install image && \
    luarocks install loadcaffe && \
    luarocks install optim

# Install HDF5 tools
RUN cd /opt/neural-networks && \
    . /opt/neural-networks/torch/install/bin/torch-activate && \
    git clone https://github.com/deepmind/torch-hdf5.git && \
    cd torch-hdf5 && \
    luarocks make hdf5-0-0.rockspec LIBHDF5_LIBDIR="/usr/lib/x86_64-linux-gnu/"

# Install h5py
RUN pip install --upgrade cython && \
    pip install --upgrade numpy && \
    pip install --upgrade h5py 

# Install cjson
RUN cd /opt/neural-networks/ && \
    . /opt/neural-networks/torch/install/bin/torch-activate && \
    wget -c http://www.kyne.com.au/%7Emark/software/download/lua-cjson-2.1.0.tar.gz && \
    tar xfz lua-cjson-2.1.0.tar.gz && \
    cd lua-cjson-2.1.0 && \
    luarocks make

# Install flask
RUN pip install flask-restful && \
    pip install Flask-HTTPAuth && \
    pip install -U flask-cors

# Install transloadit
RUN apt-get -yqq install libcurl4-openssl-dev && \
    pip install pytransloadit

# Download neuraltalk2 and cahr-rnn
RUN cd /opt/neural-networks && \
    mkdir lib && \
    cd lib && \
    git clone "https://github.com/archzzz/neuraltalk2.git" && \
    git clone "https://github.com/karpathy/char-rnn.git"

# Add models
RUN mkdir /opt/neural-networks/models
ADD models/neuraltalk2_model_01.t7 /opt/neural-networks/models/neuraltalk2_model_01.t7
ADD models/char-rnn_model_cpu_01.t7 /opt/neural-networks/models/char-rnn_model_cpu_01.t7

# Install and initialize firebase
RUN pip install firebase-admin
ADD $FIREBASE_CREDENTIAL /opt/neural-networks/firebase-key.json

# Install dependencies of firebasePython
RUN pip install requests
RUN pip install sseclient

# Add source code
RUN cd /opt/ && \
    mkdir server
ADD src /opt/server/src

# Add app configurations
RUN mkdir /opt/server/config
ADD "config/app.default_settings" /opt/server/config/app.default_settings
ADD "config/app_docker.cfg" /opt/server/config/app_docker.cfg
ENV POND_SERVICE_SETTINGS="/opt/server/config/app_docker.cfg"

# Clean up
RUN apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Expose default port
expose 5000


CMD [ "python", "-u", "/opt/server/src/poetryApi.py"]
