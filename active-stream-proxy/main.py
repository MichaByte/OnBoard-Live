import subprocess
import time
import requests

time.sleep(5)

active_stream = requests.get("http://backend:8000/api/v1/active_stream").text
print(active_stream)

old_active_stream = active_stream

proc = None

if active_stream != "":
    proc = subprocess.Popen(["/bin/ffmpeg", "-re", "-i", f"rtmp://mediamtx:1935/{active_stream}", "-c:a copy", "rtmp://host.containers.internal:1936/active-input"])


while True:
    time.sleep(3)
    active_stream = requests.get("http://backend:8000/api/v1/active_stream").text
    if old_active_stream is not active_stream:
        if proc:
            proc.terminate()
        print("e")
        proc = subprocess.Popen(["/bin/ffmpeg", "-re", "-i", f"rtmp://mediamtx:1935/{active_stream}", "-c:a copy", "rtmp://host.containers.internal:1936/active-input"])
    old_active_stream = active_stream
