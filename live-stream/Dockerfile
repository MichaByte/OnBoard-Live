FROM ubuntu:22.04

ARG DEBIAN_FRONTEND=noninteractive

RUN apt update

RUN apt install -y ffmpeg

RUN apt install -y libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev libgstreamer-plugins-bad1.0-dev gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly gstreamer1.0-libav gstreamer1.0-tools gstreamer1.0-x gstreamer1.0-alsa gstreamer1.0-wpe

RUN rm -rf /var/lib/apt/lists/*

RUN apt clean

COPY run.sh /

ENTRYPOINT ["/run.sh"]
