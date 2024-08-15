FROM docker.io/ubuntu:noble

RUN apt update && \
apt install software-properties-common -y && \
add-apt-repository ppa:obsproject/obs-studio -y && \
apt update && \
apt install ffmpeg obs-studio -y

RUN apt install python3-pip python3-venv xvfb -y

RUN useradd -ms /bin/bash obs

USER obs

RUN mkdir -p /home/obs/.config/obs-studio/basic/profiles/Untitled

RUN echo -e "\n[OBSWebSocket]\nFirstLoad=false\nServerEnabled=true\nServerPort=4455\nAlertsEnabled=false\nAuthRequired=false\nServerPassword=does_not_matter\n"  >> /home/obs/.config/obs-studio/global.ini

COPY requirements.txt /home/obs

RUN python3 -m venv /home/obs/.venv

RUN /home/obs/.venv/bin/pip install -r /home/obs/requirements.txt

COPY start.sh /home/obs

COPY setup_obs.py /home/obs

ENTRYPOINT /home/obs/start.sh
