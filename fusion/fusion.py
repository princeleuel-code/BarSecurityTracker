"""
Fusion Service
──────────────
• Connects to two upstream WebSocket alert streams:
    RGB     → ws://detector-rgb:8765
    Thermal → ws://detector-thermal:8766
• Merges overlapping detections from the same timestamp
  (IoU ≥ 0.4  → keep higher‑confidence bbox, add ‑thermal flag).
• Publishes a single fused alert stream on :8770.
• Exposes Prometheus metrics on :9104.

Environment variables
––––––––––––––––––––––
RGB_WS        WebSocket URL of RGB detector   (default ws://detector-rgb:8765)
THERMAL_WS    WebSocket URL of thermal detector (default ws://detector-thermal:8766)
"""

import os
import json
import time
import asyncio
import numpy as np
import websockets
import shapely.geometry as geom
import prometheus_client as prom

RGB_WS      = os.getenv("RGB_WS", "ws://detector-rgb:8765")
THERMAL_WS  = os.getenv("THERMAL_WS", "ws://detector-thermal:8766")
FUSE_PORT   = 8770
PROM_PORT   = 9104
IOU_THRESH  = 0.40

alerts_total   = prom.Counter("fusion_alerts_total", "Fused alerts", ["event"])
fuse_latency   = prom.Summary("fusion_latency_ms",  "Time between src & fuse (ms)")

# ─────────── helper: IoU between 2 bboxes ───────────
def iou(box1, box2):
    # boxes: [x1, y1, x2, y2]
    a = geom.box(*box1)
    b = geom.box(*box2)
    inter = a.intersection(b).area
    if inter == 0:
        return 0.0
    return inter / (a.area + b.area - inter)

# ─────────── Listen to both streams & fuse ───────────
async def fuse_loop(websocket):
    """
    Listens to RGB & Thermal streams in background tasks,
    keeps latest alerts per timestamp bucket, fuses, then
    pushes to outgoing websocket.
    """
    rgb_q      = asyncio.Queue()
    thermal_q  = asyncio.Queue()

    async def pump(url, q):
        async for msg in websockets.connect(url):
            await q.put(json.loads(msg))

    async def matcher():
        # Simple time‑bucket (1‑second) fusion
        buckets = {}  # key = second, value = [rgb_alerts, th_alerts]
        while True:
            # get whichever comes first
            rgb_task     = asyncio.create_task(rgb_q.get())
            thermal_task = asyncio.create_task(thermal_q.get())
            done, _ = await asyncio.wait({rgb_task, thermal_task}, return_when=asyncio.FIRST_COMPLETED)
            alert = done.pop().result()
            # bucket by rounded second
            ts_sec = int(time.time())
            if alert["event"].endswith("_detected"):
                buckets.setdefault(ts_sec, [[], []])
                if alert["camera_id"].startswith("Thermal"):
                    buckets[ts_sec][1].append(alert)
                else:
                    buckets[ts_sec][0].append(alert)

            # If both lists have entries in this bucket, fuse & flush
            rgb_list, th_list = buckets.get(ts_sec, ([], []))
            if rgb_list and th_list:
                fused = await fuse_lists(rgb_list, th_list)
                for out in fused:
                    alerts_total.labels(out["event"]).inc()
                    out["source"] = "fusion"
                    out["fused_at"] = time.strftime("%Y-%m-%dT%H:%M:%S.%fZ", time.gmtime())
                    fuse_latency.observe(
                        (time.time() - ts_sec) * 1000
                    )
                    await websocket.send(json.dumps(out))
                # clean bucket
                buckets.pop(ts_sec, None)

    async def fuse_lists(rgb_list, th_list):
        """Return list of fused alerts."""
        fused = []
        used_th = set()
        for r in rgb_list:
            best_iou = 0
            best_j = -1
            for j, t in enumerate(th_list):
                if j in used_th:
                    continue
                iou_val = iou(r["bbox"], t["bbox"])
                if iou_val >= IOU_THRESH and iou_val > best_iou:
                    best_iou = iou_val
                    best_j = j
            if best_j >= 0:
                used_th.add(best_j)
                # merge: keep higher confidence bbox
                t = th_list[best_j]
                fused.append(
                    max([r, t], key=lambda a: a["confidence"])
                )
            else:
                fused.append(r)
        # add unused thermal alerts
        for j, t in enumerate(th_list):
            if j not in used_th:
                fused.append(t)
        return fused

    # spawn pumps & matcher
    await asyncio.gather(
        pump(RGB_WS, rgb_q),
        pump(THERMAL_WS, thermal_q),
        matcher()
    )

async def main():
    prom.start_http_server(PROM_PORT)
    print(f"📈 Fusion Prometheus @ :{PROM_PORT}")
    async with websockets.serve(fuse_loop, "0.0.0.0", FUSE_PORT, max_queue=4):
        print(f"🔗 Fusion WebSocket @ :{FUSE_PORT}")
        await asyncio.Future()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🔻 Fusion stopped")
