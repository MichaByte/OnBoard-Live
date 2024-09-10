#!/bin/bash

sleep 1

LIBGL_ALWAYS_SOFTWARE=true gst-launch-1.0 -e wpesrc location="http://web-frontend:4173/" \
          ! videoconvert ! videoscale ! videorate \
          ! "video/x-raw, format=NV12, width=1920, height=1080, framerate=30/1" \
          ! filesink location=/dev/stdout | ffmpeg -re -y -f rawvideo -pixel_format nv12 -video_size 1920x1080 -framerate 30 -i - -listen 1 -i rtmp://0.0.0.0:1936/active-input -filter_complex "[0:v][0:v]overlay=-50:0[bg]; [bg][0:v]overlay=-50-W,format=nv12[out]" -map "[out]" -c:v libx264 -x264-params keyint=60 -preset ultrafast -b:v 6800k -c:a copy -map 1:a:0 -movflags faststart -f flv -pix_fmt nv12 rtmp://x.rtmp.youtube.com/live2/$YT_STREAM_KEY
