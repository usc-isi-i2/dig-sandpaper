FROM debian:jessie

RUN apt-get update && apt-get install -y \
    wget \
    python3 \
    python3-pip \
    python3-venv \
    git \
    vim \
    curl \
    jq \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv ~/elasticsearch2
RUN python3 -m venv ~/elasticsearch5

RUN mkdir /etc/sandpaper
WORKDIR /etc/sandpaper

EXPOSE 9876
ENTRYPOINT ["/etc/sandpaper/docker-entrypoint.sh"]
CMD ["--config", "config/sandpaper.json", "--host", "0.0.0.0", "--endpoint", "http://elasticsearch:9200"]

RUN /bin/bash -c "source ~/elasticsearch2/bin/activate && ES_MAJOR_VERSION=2 pip3 install digsandpaper && pip3 install etk && python3 -m spacy download en"
RUN /bin/bash -c "source ~/elasticsearch5/bin/activate && ES_MAJOR_VERSION=5 pip3 install digsandpaper && pip3 install etk && python3 -m spacy download en"

RUN mkdir -p /etc/sandpaper/bin
RUN mkdir -p /etc/sandpaper/config

COPY bin/* /etc/sandpaper/bin/
COPY start.py /etc/sandpaper/
COPY config/sandpaper.json /etc/sandpaper/config
COPY docker-entrypoint.sh /etc/sandpaper/docker-entrypoint.sh
VOLUME /etc/sandpaper/config
