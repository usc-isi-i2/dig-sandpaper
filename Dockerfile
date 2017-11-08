FROM debian:jessie

RUN apt-get update && apt-get install -y \
    wget \
    python \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN wget https://bootstrap.pypa.io/get-pip.py && \
    python get-pip.py

RUN pip install --no-cache-dir virtualenv

RUN virtualenv ~/elasticsearch2
RUN virtualenv ~/elasticsearch5

RUN mkdir /etc/sandpaper
WORKDIR /etc/sandpaper

EXPOSE 9876
ENTRYPOINT ["/etc/sandpaper/docker-entrypoint.sh"]
CMD ["--config", "config/sandpaper.json", "--host", "0.0.0.0", "--endpoint", "http://elasticsearch:9200"]

RUN /bin/bash -c "source ~/elasticsearch2/bin/activate && ES_MAJOR_VERSION=2 pip install --no-cache-dir digsandpaper"
RUN /bin/bash -c "source ~/elasticsearch5/bin/activate && ES_MAJOR_VERSION=5 pip install --no-cache-dir digsandpaper"

RUN mkdir -p /etc/sandpaper/bin
RUN mkdir -p /etc/sandpaper/config

COPY bin/* /etc/sandpaper/bin/
COPY start.py /etc/sandpaper/
COPY config/sandpaper.json /etc/sandpaper/config
VOLUME /etc/sandpaper/config
