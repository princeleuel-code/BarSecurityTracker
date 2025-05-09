#!/bin/sh
set -e

# Ensure RTSP_IN is provided
if [ -z "$RTSP_IN" ]; then
  echo "ERROR: RTSP_IN environment variable is not set!" >&2
  exit 1
fi
echo "RTSP_IN is set to: $RTSP_IN"

ffmpeg -hide_banner -loglevel warning \
  -rtsp_transport tcp -user_agent "Mozilla/5.0" -i "$RTSP_IN" \
  -c:v copy -an \
  -f rtsp rtsp://127.0.0.1:8554/cam1-hls
