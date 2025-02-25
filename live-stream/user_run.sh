#!/bin/bash

pulseaudio -D &
sleep 2

pacmd load-module module-null-sink sink_name=VirtSink
pacmd update-sink-proplist VirtSink device.description=VirtSink

export CHROMIUM_FLAGS="--disable-software-rasterizer"
export LIBGL_ALWAYS_INDIRECT=1


bash -c "DISPLAY=:99 xvfb-run \
    --server-num 99 \
    -s \"-nocursor -ac -screen 0 1920x1080x24\" \
    dbus-launch chromium \
    --temp-profile \
    --window-size=1920,1080 \
    --disable-gpu \
    --window-position=0,0 \
    --hide-scrollbars \
    --autoplay-policy=no-user-gesture-required \
    --app=http://tiling-frontend:4173" & disown

sleep 3

until bash -c "DISPLAY=:99 ffmpeg -xerror -f x11grab -r 30 -s 1920x1080 -draw_mouse 0 -i :99.0 -f pulse -ac 2 -i default -vcodec libx264 -preset veryfast -tune zerolatency -b:v 6000k -bufsize 12000k -framerate 30 -g 60 -pix_fmt yuv420p -acodec aac -f flv -flvflags no_duration_filesize rtmp://x.rtmp.youtube.com/live2/$(cat /home/stream/key.txt)"; do
        echo "Restarting FFmpeg..."
        sleep 1
done
