import subprocess
import time
import requests

active_stream = requests.get("http://backend:8000/api/v1/active_stream").text
old_active_stream = active_stream

proc = None

while True:
    proc = subprocess.Popen([f"ffmpeg -re -i rtmp://mediamtx:1935/{active_stream} -c:a copy rtmp://host.containers.internal:1936/active-input"], shell=True)
    time.sleep(3)
    active_stream = requests.get("http://backend:8000/api/v1/active_stream").text
    if old_active_stream is not active_stream:
        proc.terminate()
        proc = subprocess.Popen([f"ffmpeg -re -i rtmp://mediamtx:1935/{active_stream} -c:a copy rtmp://host.containers.internal:1936/active-input"], shell=True)
    old_active_stream = active_stream
