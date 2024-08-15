#!/usr/bin/bash

export DISPLAY=:99
xvfb-run obs &
sleep 5
source /home/obs/.venv/bin/activate
python3 /home/obs/setup_obs.py
sleep 100
