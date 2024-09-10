FROM alpine:3.20

RUN apk add --no-cache gstreamer gstreamer-tools gst-plugins-bad

RUN apk add --no-cache ffmpeg

RUN apk add --no-cache bash libwpe libwpe-dev

COPY run.sh /

ENTRYPOINT ["/run.sh"]
