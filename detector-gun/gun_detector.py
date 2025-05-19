#!/usr/bin/env python3
import asyncio
import json
import time
import prometheus_client as prom
from prometheus_client import Counter
import websockets

WS_PORT = 9106
PROM_PORT = 9107
CAM_ID = "thermal_gun_01"

frames_total = Counter("gun_frames_total", "Frames processed")
alerts_total = Counter("gun_alerts_total", "Alerts emitted", ["event"])

async def detector_loop(ws):
    while True:
        frames_total.inc()
        await asyncio.sleep(1)
        if frames_total._value.get() % 10 == 0:
            alert = {
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.%fZ", time.gmtime()),
                "camera_id": CAM_ID,
                "event": "weapon_detected",
                "confidence": 0.9,
                "bbox": [100, 100, 300, 300],
            }
            alerts_total.labels(alert["event"]).inc()
            await ws.send(json.dumps(alert))
            print("Generated weapon_detected")

async def main():
    prom.start_http_server(PROM_PORT)
    async with websockets.serve(detector_loop, "0.0.0.0", WS_PORT):
        print(f"Gun detector WebSocket @ :{WS_PORT}")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
