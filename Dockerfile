FROM ubuntu:16.04

RUN apt-get update
RUN apt-get install -y software-properties-common vim
RUN add-apt-repository ppa:jonathonf/python-3.6
RUN apt-get update

RUN apt-get install -y build-essential python3.6 python3.6-dev python3-pip python3.6-venv

# update pip
RUN python3.6 -m pip install pip --upgrade && \
        python3.6 -m pip install wheel

RUN apt-get update && apt-get install -y \
    wget \
    git \
    vim \
    curl \
    jq \
    && rm -rf /var/lib/apt/lists/*

RUN python3.6 -m venv ~/elasticsearch2
RUN python3.6 -m venv ~/elasticsearch5

RUN mkdir /etc/sandpaper
WORKDIR /etc/sandpaper

EXPOSE 9876
ENTRYPOINT ["/etc/sandpaper/docker-entrypoint.sh"]
CMD ["--config", "config/sandpaper.json", "--host", "0.0.0.0", "--endpoint", "http://elasticsearch:9200"]

RUN /bin/bash -c "source ~/elasticsearch2/bin/activate && ES_MAJOR_VERSION=2 pip3.6 install --upgrade pip && pip3.6 install --upgrade setuptools && pip3.6 install digsandpaper && pip3.6 install etk && python3.6 -m spacy download en"
RUN /bin/bash -c "source ~/elasticsearch5/bin/activate && ES_MAJOR_VERSION=5 pip3.6 install --upgrade pip && pip3.6 install --upgrade setuptools && pip3.6 install digsandpaper && pip3.6 install etk && python3.6 -m spacy download en"

RUN mkdir -p /etc/sandpaper/bin
RUN mkdir -p /etc/sandpaper/config

COPY bin/* /etc/sandpaper/bin/
COPY start.py /etc/sandpaper/
COPY config/sandpaper.json /etc/sandpaper/config
COPY docker-entrypoint.sh /etc/sandpaper/docker-entrypoint.sh
VOLUME /etc/sandpaper/config
