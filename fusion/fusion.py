"""
Fusion Service
──────────────
• Connects to three upstream WebSocket alert streams:
    RGB     → ws://detector-rgb:8765
    Thermal → ws://detector-thermal:8766
    FFD     → ws://detector-ffd:8767
• Merges overlapping detections from the same timestamp
  (IoU ≥ 0.4  → keep higher‑confidence bbox, add ‑thermal flag).
• Passes through fight/fall detection events.
• Publishes a single fused alert stream on :8770.
• Exposes Prometheus metrics on :9104.

Environment variables
––––––––––––––––––––––
RGB_WS        WebSocket URL of RGB detector   (default ws://detector-rgb:8765)
THERMAL_WS    WebSocket URL of thermal detector (default ws://detector-thermal:8766)
FFD_WS        WebSocket URL of FFD detector (default ws://detector-ffd:8767)
"""

import os
import json
import time
import asyncio
import numpy as np
import websockets
import shapely.geometry as geom
import prometheus_client as prom
from collections import deque, defaultdict

RGB_WS      = os.getenv("RGB_WS", "ws://detector-rgb:8765")
THERMAL_WS  = os.getenv("THERMAL_WS", "ws://detector-thermal:8766")
FFD_WS      = os.getenv("FFD_WS", "ws://detector-ffd:8767")
GUN_WS      = os.getenv("GUN_WS", "ws://detector-gun:9106")
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
    Listens to RGB, Thermal, and FFD streams in background tasks,
    keeps latest alerts per timestamp bucket, fuses, then
    pushes to outgoing websocket.
    """
    rgb_q      = asyncio.Queue()
    thermal_q  = asyncio.Queue()
    ffd_q      = asyncio.Queue()
    gun_q      = asyncio.Queue()

    async def pump(url, q):
        try:
            async with websockets.connect(url) as websocket:
                print(f"Connected to {url}")
                async for msg in websocket:
                    try:
                        await q.put(json.loads(msg))
                    except json.JSONDecodeError as e:
                        print(f"Error decoding JSON from {url}: {e}")
        except Exception as e:
            print(f"Error connecting to {url}: {e}")
            # Wait a bit before retrying
            await asyncio.sleep(5)

    async def matcher():
        # Use defaultdict with deque for time-bucketed fusion
        # Each bucket contains lists of alerts from different sources with maxlen to prevent memory issues
        MAX_BUCKET_SIZE = 100  # Maximum number of alerts per source in a bucket
        buckets = defaultdict(lambda: [
            deque(maxlen=MAX_BUCKET_SIZE),  # RGB alerts
            deque(maxlen=MAX_BUCKET_SIZE),  # Thermal alerts
            deque(maxlen=MAX_BUCKET_SIZE),  # FFD alerts
            deque(maxlen=MAX_BUCKET_SIZE)   # Gun alerts
        ])
        # Keep track of active buckets with a deque to limit memory usage
        active_buckets = deque(maxlen=60)  # Store up to 60 seconds of buckets

        while True:
            # get whichever comes first
            rgb_task     = asyncio.create_task(rgb_q.get())
            thermal_task = asyncio.create_task(thermal_q.get())
            ffd_task     = asyncio.create_task(ffd_q.get())
            gun_task     = asyncio.create_task(gun_q.get())
            done, _ = await asyncio.wait({rgb_task, thermal_task, ffd_task, gun_task}, return_when=asyncio.FIRST_COMPLETED)
            alert = done.pop().result()
            # bucket by rounded second
            ts_sec = int(time.time())

            # Add current timestamp to active buckets if not already present
            if ts_sec not in active_buckets:
                active_buckets.append(ts_sec)

            # Handle special events directly (pass-through)
            if alert["event"] in ["fight_detected", "fall_detected", "weapon_detected"]:
                alerts_total.labels(alert["event"]).inc()
                alert["source"] = "fusion"
                alert["fused_at"] = time.strftime("%Y-%m-%dT%H:%M:%S.%fZ", time.gmtime())
                fuse_latency.observe((time.time() - ts_sec) * 1000)
                await websocket.send(json.dumps(alert))
                continue

            # Handle regular object detection events
            if alert["event"].endswith("_detected"):
                if alert["camera_id"].startswith("thermal_gun"):
                    buckets[ts_sec][3].append(alert)
                elif alert["camera_id"].startswith("Thermal"):
                    buckets[ts_sec][1].append(alert)
                elif alert["camera_id"].startswith("ffd"):
                    buckets[ts_sec][2].append(alert)
                else:
                    buckets[ts_sec][0].append(alert)

            # If both RGB and Thermal lists have entries in this bucket, fuse & flush
            rgb_list, th_list, _, gun_list = buckets[ts_sec]
            if rgb_list and th_list:
                fused = await fuse_lists(list(rgb_list), list(th_list))
                for out in fused:
                    alerts_total.labels(out["event"]).inc()
                    out["source"] = "fusion"
                    out["fused_at"] = time.strftime("%Y-%m-%dT%H:%M:%S.%fZ", time.gmtime())
                    fuse_latency.observe(
                        (time.time() - ts_sec) * 1000
                    )
                    await websocket.send(json.dumps(out))
                # clean bucket
                if ts_sec in buckets:
                    del buckets[ts_sec]
                    active_buckets.remove(ts_sec)

            # Clean up old buckets (older than 10 seconds)
            current_time = int(time.time())
            old_buckets = [ts for ts in list(active_buckets) if current_time - ts > 10]
            for old_ts in old_buckets:
                if old_ts in buckets:
                    del buckets[old_ts]
                    active_buckets.remove(old_ts)

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

    # spawn pumps & matcher with reconnection
    while True:
        try:
            await asyncio.gather(
                pump(RGB_WS, rgb_q),
                pump(THERMAL_WS, thermal_q),
                pump(FFD_WS, ffd_q),
                pump(GUN_WS, gun_q),
                matcher()
            )
        except Exception as e:
            print(f"Error in fusion loop: {e}")
            # Wait a bit before retrying
            await asyncio.sleep(5)

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
