#!/bin/bash

export CHROMIUM_FLAGS="--disable-software-rasterizer --disable-dev-shm-usage"
dbus-daemon --config-file=/usr/share/dbus-1/system.conf --print-address
export LIBGL_ALWAYS_INDIRECT=1

bash -c "sleep 5 && DISPLAY=:99 ffmpeg -f x11grab -r 30 -s 1920x1080 -draw_mouse 0 -i :99.0 -f alsa -ac 2 -i hw:0 -vcodec libx264 -preset medium -b:v 7000k -framerate 30 -g 2 -pix_fmt yuv420p -acodec aac -f flv rtmp://x.rtmp.youtube.com/live2/$YT_STREAM_KEY" &

DISPLAY=:99 xvfb-run \
  --server-num 99 \
  -s "-nocursor -ac -screen 0 1920x1080x24" \
  dbus-launch chromium \
    --temp-profile \
    --window-size=1920,1080 \
    --disable-gpu \
    --window-position=0,0 \
    --no-sandbox \
    --hide-scrollbars \
    --disable-setuid-sandbox \
    --app=http://web-frontend:4173
