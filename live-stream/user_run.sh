#!/bin/bash

pulseaudio -D &
sleep 2

pacmd load-module module-null-sink sink_name=VirtSink
pacmd update-sink-proplist VirtSink device.description=VirtSink

export CHROMIUM_FLAGS="--disable-software-rasterizer --disable-dev-shm-usage"
export LIBGL_ALWAYS_INDIRECT=1

bash -c "sleep 5 && DISPLAY=:99 ffmpeg -f x11grab -r 30 -s 2560x1440 -draw_mouse 0 -i :99.0 -f pulse -ac 2 -i default -vcodec libx264 -preset slow -b:v 15000k -framerate 30 -g 2 -pix_fmt yuv420p -acodec aac -f flv rtmp://x.rtmp.youtube.com/live2/$(cat /home/stream/key.txt)" &

DISPLAY=:99 xvfb-run \
    --server-num 99 \
    -s "-nocursor -ac -screen 0 2560x1440x24" \
    dbus-launch chromium \
    --temp-profile \
    --window-size=2560,1440 \
    --disable-gpu \
    --window-position=0,0 \
    --hide-scrollbars \
    --autoplay-policy=no-user-gesture-required \
    --app=http://localhost:4173
