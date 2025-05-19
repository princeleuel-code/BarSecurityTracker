#!/usr/bin/env python3
import asyncio
import json
import time
import prometheus_client as prom
from prometheus_client import Counter
import websockets

WS_PORT = 8767
PROM_PORT = 9105
CAM_ID = "ffd_01"

frames_total = Counter("ffd_frames_total", "Frames processed")
alerts_total = Counter("ffd_alerts_total", "Alerts emitted", ["event"])

async def detector_loop(ws):
    while True:
        frames_total.inc()
        await asyncio.sleep(1)
        if frames_total._value.get() % 10 == 0:
            event = "fall_detected" if frames_total._value.get() % 20 == 0 else "fight_detected"
            alert = {
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.%fZ", time.gmtime()),
                "camera_id": CAM_ID,
                "event": event,
                "confidence": 0.9,
                "bbox": [100, 100, 300, 300],
            }
            alerts_total.labels(event).inc()
            await ws.send(json.dumps(alert))
            print(f"Generated {event}")

async def main():
    prom.start_http_server(PROM_PORT)
    async with websockets.serve(detector_loop, "0.0.0.0", WS_PORT):
        print(f"FFD detector WebSocket @ :{WS_PORT}")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
