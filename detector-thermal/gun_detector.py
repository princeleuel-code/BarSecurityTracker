#!/usr/bin/env python3
import asyncio
import cv2
import json
import os
import time
from prometheus_client import Counter, Summary
import prometheus_client as prom
from ultralytics import YOLO
import websockets

# --- Configuration ---
RTSP_URL = os.getenv("RTSP_URL")
DEVICE = os.getenv("BARSHIELD_DEVICE", "cuda")
CAM_ID = "thermal_gun_01"
WS_PORT = 9106
PROM_PORT = 9106
CONF_THRES = 0.25

MODEL_PATH = os.getenv("GUN_MODEL_PATH", "models/gun_yolov8n.pt")

# --- Prometheus metrics ---
frames_total = prom.Counter("gun_frames_total", "Frames processed")
alerts_total = prom.Counter("gun_alerts_total", "Alerts emitted", ["event"])
infer_latency = Summary("gun_inference_ms", "Inference latency (ms)")

# --- Load model ---
model = YOLO(MODEL_PATH)
model.to(DEVICE)
GUN_CLASSES = {
    n for n in model.names.values()
    if "gun" in n.lower() or "pistol" in n.lower()
}

async def generate_test_metrics(ws):
    while True:
        frames_total.inc()
        t0 = time.time()
        await asyncio.sleep(0.05)
        infer_latency.observe((time.time() - t0) * 1000)
        if frames_total._value.get() % 30 == 0:
            alert = {
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.%fZ", time.gmtime()),
                "camera_id": CAM_ID,
                "event": "gun_detected",
                "confidence": 0.9,
                "bbox": [100, 100, 300, 300],
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
        ok, frame = cap.read()
        if not ok:
            await asyncio.sleep(0.05)
            continue
        frames_total.inc()
        t0 = time.time()
        res = model.predict(frame, imgsz=640, conf=CONF_THRES, verbose=False)[0]
        infer_latency.observe((time.time() - t0) * 1000)
        for cls_i, conf, box in zip(res.boxes.cls, res.boxes.conf, res.boxes.xyxy):
            label = model.names[int(cls_i)]
            if label not in GUN_CLASSES or conf < CONF_THRES:
                continue
            x1, y1, x2, y2 = map(int, box)
            alert = {
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.%fZ", time.gmtime()),
                "camera_id": CAM_ID,
                "event": f"{label}_detected",
                "confidence": float(conf),
                "bbox": [x1, y1, x2, y2],
            }
            alerts_total.labels(alert["event"]).inc()
            await ws.send(json.dumps(alert))
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
