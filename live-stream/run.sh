#!/bin/bash

gst-launch-1.0 -e wpesrc location="https://en.wikipedia.org/wiki/Main_Page" \
          ! videoconvert ! videoscale ! videorate \
          ! "video/x-raw, format=BGRA, width=854, height=480, framerate=30/1" \
          ! videoconvert \
          ! x264enc speed-preset=1 \
          ! filesink location=/dev/stdout | ffmpeg -re -y -i - -listen 1 -i rtmp://0.0.0.0:1936/active-input -c:v copy -c:a aac -map 0:v:0 -map 1:a:0 -t 10 -f flv rtmp://x.rtmp.youtube.com/live2/no-way-am-i-doing-that-again
