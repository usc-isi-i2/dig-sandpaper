FROM debian:jessie

RUN apt-get update && apt-get install -y \
    wget \
    python \
    && rm -rf /var/lib/apt/lists/*

RUN wget https://bootstrap.pypa.io/get-pip.py && \
    python get-pip.py

RUN pip install --no-cache-dir digsandpaper

EXPOSE 9876

RUN mkdir -p /etc/sandpaper/bin

COPY bin/* /etc/sandpaper/bin/
COPY start.py /etc/sandpaper/

RUN mkdir -p /etc/sandpaper/config
COPY config/sandpaper.json /etc/sandpaper/config
VOLUME /etc/sandpaper/config

WORKDIR /etc/sandpaper
CMD ["bin/start.sh", "--config", "config/sandpaper.json", "--host", "0.0.0.0"]
