FROM docker.io/ubuntu:noble

ENV OBSWS_PASSWORD=""

RUN apt update && \
apt install software-properties-common -y && \
add-apt-repository ppa:obsproject/obs-studio -y && \
apt update && \
apt install ffmpeg obs-studio -y

RUN apt install python3-pip python3-venv xvfb -y

RUN useradd -ms /bin/bash obs

USER obs

RUN mkdir -p /home/obs/.config/obs-studio/basic/profiles/Untitled

RUN echo -e "\n[OBSWebSocket]\nFirstLoad=false\nServerEnabled=true\nServerPort=4455\nAlertsEnabled=false\nAuthRequired=true\nServerPassword=${OBSWS_PASSWORD}\n"  >> /home/obs/.config/obs-studio/global.ini

RUN echo '{"type":"rtmp_common","settings":{"service":"YouTube - RTMPS","protocol":"RTMPS","server":"rtmps://a.rtmps.youtube.com:443/live2","bwtest":false,"key":"${YT_STREAM_KEY}","stream_key_link":"https://www.youtube.com/live_dashboard","multitrack_video_name":"Multitrack Video","multitrack_video_disclaimer":"Multitrack Video automatically optimizes your settings to encode and send multiple video qualities to YouTube - RTMPS. Selecting this option will send YouTube - RTMPS information about your computer and software setup."}}' > /home/obs/.config/obs-studio/basic/profiles/Untitled/service.json

COPY requirements.txt /home/obs

RUN python3 -m venv /home/obs/.venv

RUN /home/obs/.venv/bin/pip install -r /home/obs/requirements.txt

COPY start.sh /home/obs

COPY setup-obs.py /home/obs

RUN echo $OBSWS_PASSWORD

ENTRYPOINT /home/obs/start.sh
