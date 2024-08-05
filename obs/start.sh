#!/usr/bin/bash

export DISPLAY=:99
Xvfb $DISPLAY &
obs &
sleep 1
source /home/obs/.venv/bin/activate
python3 /home/obs/setup-obs.py

