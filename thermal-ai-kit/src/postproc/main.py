import numpy as np
import cv2 # For NMS if needed
import time
from typing import List, Dict, Any, Optional

# --- TODO: REDIS CONSUMER / PRODUCER PIPELINE  (vNext – Post-processing Service) ---
#
# 1. Redis Client
#    r = redis.Redis(host=os.getenv("REDIS_HOST", "redis"),
#                    port=int(os.getenv("REDIS_PORT", 6379)),
#                    decode_responses=False) # Or True if payloads are strings
#
# 2. Detection Consumer Loop
#    - Stream key: f"detections:{source_id}" (e.g., detections:cam1)
#    - Use XREAD or XREADGROUP for blocking read (e.g., count=1, block=1000).
#    - Extract JSON payload from the stream message.
#    - Parse JSON into a Python dictionary representing detection results.
#
# 3. NMS / Tracking Logic (using _process_single_detection_payload or similar)
#    - Input: Detection dictionary from Redis.
#    - Apply NMS only if the upstream detector didn't definitively handle it
#      (YOLOv8 from Ultralytics usually includes NMS).
#    - Implement per-camera tracking state. Consider using DeepSORT via a library
#      like `deep_sort_realtime` if simple IoU is insufficient.
#      Tracker dict might look like: {source_id: tracker_object}.
#
# 4. Event Publisher / Output Stream
#    - Stream key: f"events:{source_id}" (e.g., events:cam1)
#    - Payload per event: A dictionary, e.g.,
#      { 
#        "ts": epoch_ts,          # Timestamp of the event (can be from detection or postproc)
#        "track_id": int,         # Object track ID from the tracker
#        "class_name": str,       # Detected class name
#        "bbox": [x1,y1,x2,y2],   # Bounding box coordinates
#        "confidence": float,     # Detection confidence
#        "source_id": str         # Source camera ID
#        # Potentially other metadata like zone, line crossing, etc.
#      }
#    - Convert payload to JSON string, then encode to bytes if decode_responses=False for Redis client.
#    - Use XADD to publish to the events stream, with MAXLEN (e.g., ~1000) for trimming.
#
# 5. Service Entrypoint / Main Loop
#    if __name__ == "__main__":
#        # Initialize Redis client
#        # Determine source_ids to monitor (e.g., from env var, config, or dynamic registration)
#        # For each source_id, potentially start a consumer thread.
#        # consume_streams_forever() function would contain the loop calling XREAD/XREADGROUP.
#        # Handle graceful shutdown (e.g., KeyboardInterrupt to stop threads).
#        print("Postprocessing service started. TODO: Implement main consumer loop.")
#
# NOTE: Keep MAXLEN ~1000 on Redis streams (detections:*, events:*) to cap memory.
# Log queue lag if XREAD/XREADGROUP indicates many pending messages or if processing time is high.
# ----------------------------------------------------------------------------------

print("Postprocessing service main.py loaded")

next_track_id: int = 0
active_tracks: Dict[int, Dict[str, Any]] = {}

def _iou(boxA, boxB) -> float:
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])
    interArea = max(0, xB - xA) * max(0, yB - yA)
    boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
    boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])
    iou_val = interArea / float(boxAArea + boxBArea - interArea) if (boxAArea + boxBArea - interArea) > 0 else 0
    return iou_val

def update_tracks(detections: List[Dict[str, Any]], iou_threshold_tracking=0.3) -> List[Dict[str, Any]]:
    global next_track_id, active_tracks
    current_time = time.time()
    tracks_to_remove = [tid for tid, track_data in active_tracks.items() if current_time - track_data.get('last_seen_time', 0) > 5.0]
    for tid in tracks_to_remove:
        del active_tracks[tid]

    unmatched_detections = list(range(len(detections)))
    # Iterate over a copy for modification if active_tracks is modified inside loop directly
    for track_id, track_data in list(active_tracks.items()):
        best_match_idx = -1
        best_iou = iou_threshold_tracking
        for i, det_idx in enumerate(unmatched_detections):
            detection = detections[det_idx]
            iou = _iou(track_data['bbox'], detection['bbox'])
            if iou > best_iou:
                best_iou = iou
                best_match_idx = i
        if best_match_idx != -1:
            det_idx_to_match = unmatched_detections.pop(best_match_idx)
            detections[det_idx_to_match]['track_id'] = track_id
            active_tracks[track_id]['bbox'] = detections[det_idx_to_match]['bbox']
            active_tracks[track_id]['last_seen_time'] = current_time

    for det_idx in unmatched_detections:
        detections[det_idx]['track_id'] = next_track_id
        active_tracks[next_track_id] = {
            'bbox': detections[det_idx]['bbox'],
            'class_name': detections[det_idx]['class_name'],
            'last_seen_time': current_time,
            'first_seen_time': current_time
        }
        next_track_id += 1
    return detections

def apply_nms(detections: List[Dict[str, Any]], confidence_threshold: float, iou_nms_threshold: float) -> List[Dict[str, Any]]:
    if not detections:
        return []
    filtered_detections = [d for d in detections if d['confidence'] >= confidence_threshold]
    if not filtered_detections:
        return []
    
    final_detections = []
    class_to_detections: Dict[Any, List[Dict[str, Any]]] = {}
    for det in filtered_detections:
        class_id = det['class_id']
        if class_id not in class_to_detections:
            class_to_detections[class_id] = []
        class_to_detections[class_id].append(det)

    for class_id, class_dets in class_to_detections.items():
        if not class_dets:
            continue
        # Assuming Y8ThermalDetector's NMS is primary. This is a pass-through placeholder.
        # For active NMS: convert bboxes to [x,y,w,h] for cv2.dnn.NMSBoxes or use custom NMS.
        # Example: boxes_xywh = [[b[0], b[1], b[2]-b[0], b[3]-b[1]] for b in bboxes_for_nms]
        # indices = cv2.dnn.NMSBoxes(boxes_xywh, confidences_for_nms, score_threshold=confidence_threshold, nms_threshold=iou_nms_threshold)
        final_detections.extend(class_dets)
    return final_detections

def process_detections(raw_detection_payload: Dict[str, Any],
                       enable_tracking=True,
                       enable_additional_nms=False,
                       confidence_threshold_postproc=0.1,
                       iou_nms_threshold_postproc=0.5
                       ) -> Dict[str, Any]:
    start_time = time.time()
    source_id = raw_detection_payload.get("source_id", "unknown_source")
    original_timestamp = raw_detection_payload.get("timestamp", start_time)
    detector_name = raw_detection_payload.get("detector_name", "unknown_detector")
    current_detections = raw_detection_payload.get("detections", [])

    if not isinstance(current_detections, list):
        current_detections = []

    if enable_additional_nms and current_detections:
        processed_detections_nms = apply_nms(current_detections,
                                             confidence_threshold=confidence_threshold_postproc,
                                             iou_nms_threshold=iou_nms_threshold_postproc)
    else:
        processed_detections_nms = current_detections

    if enable_tracking and processed_detections_nms:
        tracked_detections = update_tracks(processed_detections_nms)
    else:
        for det in processed_detections_nms:
            det['track_id'] = None
        tracked_detections = processed_detections_nms
        
    processing_time = time.time() - start_time
    output_payload = {
        "source_id": source_id,
        "original_timestamp": original_timestamp,
        "postproc_timestamp": start_time,
        "detector_name": detector_name,
        "processing_time_ms": int(processing_time * 1000),
        "processed_detections": tracked_detections
    }
    print(f"Postproc: Processed {len(tracked_detections)} detections for source '{source_id}'. Time: {processing_time*1000:.2f}ms.")
    return output_payload

if __name__ == "__main__":
    print("\nPostprocessing service self-test section:")
    mock_detector_output = {
        "source_id": "test_cam_01", "timestamp": time.time() - 0.5,
        "detector_name": "y8_thermal", "processing_time_ms": 50,
        "detections": [
            {"class_id": 3, "class_name": "handgun", "confidence": 0.85, "bbox": [150, 70, 210, 110]},
            {"class_id": 3, "class_name": "handgun", "confidence": 0.90, "bbox": [155, 75, 215, 115]},
            {"class_id": 0, "class_name": "person", "confidence": 0.70, "bbox": [10, 10, 60, 110]},
            {"class_id": 0, "class_name": "person", "confidence": 0.65, "bbox": [200, 50, 280, 180]},
        ]
    }
    print(f"\nInput (mock detector output for '{mock_detector_output['source_id']}'):")
    for det in mock_detector_output['detections']: print(f"  {det}")

    print("\n--- Test 1: Tracking ENABLED, Additional NMS DISABLED ---")
    processed_result_tracked = process_detections(mock_detector_output, True, False)
    for det in processed_result_tracked['processed_detections']: print(f"  Class: {det['class_name']}, Conf: {det['confidence']:.2f}, BBox: {det['bbox']}, TrackID: {det.get('track_id')}")
    print(f"  Postproc Time: {processed_result_tracked['processing_time_ms']}ms")

    mock_detector_output_frame2 = {
        "source_id": "test_cam_01", "timestamp": time.time() - 0.2,
        "detector_name": "y8_thermal", "processing_time_ms": 52,
        "detections": [
            {"class_id": 3, "class_name": "handgun", "confidence": 0.88, "bbox": [158, 72, 218, 112]},
            {"class_id": 0, "class_name": "person", "confidence": 0.78, "bbox": [300, 40, 350, 170]},
            {"class_id": 0, "class_name": "person", "confidence": 0.60, "bbox": [15, 12, 65, 112]},
        ]
    }
    print(f"\nInput (mock detector output FRAME 2 for '{mock_detector_output_frame2['source_id']}'):")
    for det in mock_detector_output_frame2['detections']: print(f"  {det}")
    processed_result_tracked_f2 = process_detections(mock_detector_output_frame2, True, False)
    print("Processed Result (Tracking Enabled, Frame 2):")
    for det in processed_result_tracked_f2['processed_detections']: print(f"  Class: {det['class_name']}, Conf: {det['confidence']:.2f}, BBox: {det['bbox']}, TrackID: {det.get('track_id')}")
    print(f"  Postproc Time: {processed_result_tracked_f2['processing_time_ms']}ms")

    print("\n--- Test 2: Tracking ENABLED, Additional NMS ENABLED ---")
    next_track_id = 0
    active_tracks.clear()
    processed_result_nms_tracked = process_detections(mock_detector_output, True, True, 0.6, 0.4)
    print("Processed Result (Additional NMS and Tracking Enabled):")
    for det in processed_result_nms_tracked['processed_detections']: print(f"  Class: {det['class_name']}, Conf: {det['confidence']:.2f}, BBox: {det['bbox']}, TrackID: {det.get('track_id')}")
    print(f"  Postproc Time: {processed_result_nms_tracked['processing_time_ms']}ms")
    print("\nPostprocessing service self-test finished.")
