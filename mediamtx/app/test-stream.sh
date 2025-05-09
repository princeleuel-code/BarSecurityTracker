#!/bin/sh
set -e

# Generate a test pattern and stream it to RTSP
exec ffmpeg -hide_banner -loglevel warning \
  -re -f lavfi -i "testsrc=size=1280x720:rate=30" \
  -c:v libx264 -preset ultrafast -tune zerolatency \
  -force_key_frames "expr:gte(t,n_forced*2)" \
  -f rtsp "rtsp://127.0.0.1:8554/cam1-hls"
