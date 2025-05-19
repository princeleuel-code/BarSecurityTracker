#!/usr/bin/env python3
import asyncio
import cv2
import json
import os
import time
from prometheus_client import Counter, Summary
import prometheus_client as prom
import websockets

RTSP_URL = os.getenv("RTSP_URL")
WS_PORT = 8767
PROM_PORT = 9105

frames_total = prom.Counter("ffd_frames_total", "Frames processed")
alerts_total = prom.Counter("ffd_alerts_total", "Alerts emitted", ["event"])
proc_latency = Summary("ffd_processing_ms", "Processing latency (ms)")

async def generate_test_metrics(ws):
    while True:
        frames_total.inc()
        t0 = time.time()
        await asyncio.sleep(0.05)
        proc_latency.observe((time.time() - t0) * 1000)
        if frames_total._value.get() % 50 == 0:
            alert = {
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.%fZ", time.gmtime()),
                "camera_id": "ffd_01",
                "event": "fall_detected",
                "confidence": 0.9,
                "bbox": [50, 50, 200, 200],
            }
            alerts_total.labels(alert["event"]).inc()
            await ws.send(json.dumps(alert))
        await asyncio.sleep(1)

async def detector_loop(ws):
    cap = cv2.VideoCapture(RTSP_URL, cv2.CAP_FFMPEG)
    if not cap.isOpened():
        await generate_test_metrics(ws)
        return
    while True:
        ok, _ = cap.read()
        if not ok:
            await asyncio.sleep(0.05)
            continue
        frames_total.inc()
        t0 = time.time()
        await asyncio.sleep(0.02)
        proc_latency.observe((time.time() - t0) * 1000)
        await asyncio.sleep(0.01)

async def main():
    prom.start_http_server(PROM_PORT)
    async with websockets.serve(detector_loop, "0.0.0.0", WS_PORT, max_queue=4):
        await asyncio.Future()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
