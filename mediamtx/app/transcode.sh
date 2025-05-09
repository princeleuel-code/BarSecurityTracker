#!/bin/sh
set -e

# Ensure RTSP_IN is provided
[ -z "$RTSP_IN" ] && { echo "RTSP_IN missing, exiting" >&2; exit 1; }

# Delegate to ffmpeg-wrapper (TCP then UDP fallback, forced keyframes)
exec ffmpeg -hide_banner -loglevel warning \
  -user_agent "Mozilla/5.0" \
  -rtsp_transport tcp -i "$RTSP_IN" \
  -c:v copy -an \
  -force_key_frames "expr:gte(t,n_forced*2)" \
  -f rtsp "rtsp://127.0.0.1:8554/cam1-hls" \
|| exec ffmpeg -hide_banner -loglevel warning \
     -user_agent "Mozilla/5.0" \
     -rtsp_transport udp -i "$RTSP_IN" \
     -c:v copy -an \
     -force_key_frames "expr:gte(t,n_forced*2)" \
     -f rtsp "rtsp://127.0.0.1:8554/cam1-hls"
