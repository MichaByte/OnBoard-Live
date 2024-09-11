FROM ubuntu:latest

RUN apt update

RUN apt install -y ffmpeg xvfb software-properties-common dbus-x11

RUN add-apt-repository -y ppa:xtradeb/apps

RUN apt update

RUN apt install -y chromium

RUN rm -rf /var/lib/apt/lists/*

RUN apt clean

COPY run.sh .

ENTRYPOINT ["./run.sh"]
