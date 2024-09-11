import subprocess
import time
import requests

time.sleep(8)

active_stream = requests.get("http://backend:8000/api/v1/active_stream").text.replace('"', '')
print(active_stream)

old_active_stream = active_stream

proc = None

if active_stream != "":
    proc = subprocess.Popen(["ffmpeg", "-re", "-i", f"rtmp://host.containers.internal:1935/{active_stream}", "-c:a", "libmp3lame", "-f", "flv", "rtmp://host.containers.internal:1936/active-input"])
else:
    proc = subprocess.Popen(["ffmpeg", "-f", "lavfi", "-i", "anullsrc", "-c:a", "libmp3lame", "-f", "flv", "rtmp://host.containers.internal:1936/active-input"])

while True:
    time.sleep(3)
    active_stream = requests.get("http://backend:8000/api/v1/active_stream").text.replace('"', '')
    if old_active_stream is not active_stream:
        if proc:
            proc.terminate()
        if active_stream != "":
            proc = subprocess.Popen(["ffmpeg", "-re", "-i", f"rtmp://host.containers.internal:1935/{active_stream}", "-c:a", "libmp3lame", "-f", "flv", "rtmp://host.containers.internal:1936/active-input"])
        else:
            proc = subprocess.Popen(["ffmpeg", "-f", "lavfi", "-i", "anullsrc", "-c:a", "libmp3lame", "-f", "flv", "rtmp://host.containers.internal:1936/active-input"])
    old_active_stream = active_stream
