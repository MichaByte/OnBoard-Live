#!/bin/bash

sleep 1

LIBGL_ALWAYS_SOFTWARE=true gst-launch-1.0 -e wpesrc location="http://web-frontend:4173/" \
          ! queue \
          ! videoconvert ! videoscale ! videorate \
          ! "video/x-raw, format=BGRA, width=1920, height=1080, framerate=30/1" \
          ! videoconvert \
          ! x264enc speed-preset=1 \
          ! filesink location=/dev/stdout | ffmpeg -re -y -i - -listen 1 -i rtmp://0.0.0.0:1936/active-input -c:v copy -c:a libmp3lame -map 0:v:0 -map 1:a:0 -g 90 -framerate 30 -movflags faststart -bufsize 14000k -f flv rtmp://x.rtmp.youtube.com/live2/$YT_STREAM_KEY



