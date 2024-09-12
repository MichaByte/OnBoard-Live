#!/bin/bash

dbus-daemon --config-file=/usr/share/dbus-1/system.conf &

echo $YT_STREAM_KEY >/home/stream/key.txt

chown stream /home/stream/key.txt

chown stream /home/stream/user_run.sh

sudo -i -u stream bash /home/stream/user_run.sh
