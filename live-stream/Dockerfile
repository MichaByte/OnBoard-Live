FROM ubuntu:latest

RUN apt update

RUN apt install -y ffmpeg xvfb software-properties-common dbus-x11 pulseaudio

RUN add-apt-repository -y ppa:xtradeb/apps

RUN apt update

RUN apt install -y chromium

RUN apt install -y sudo

RUN rm -rf /var/lib/apt/lists/*

RUN apt clean

RUN useradd -ms /bin/bash stream

COPY run.sh ./

COPY user_run.sh /home/stream

ENTRYPOINT ["./run.sh"]
