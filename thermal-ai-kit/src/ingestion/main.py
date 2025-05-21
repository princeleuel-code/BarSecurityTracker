import cv2
import time
from typing import Dict, Any, Optional, List
import threading
import collections
import os
import redis

REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
redis_client = None
try:
    redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)
    redis_client.ping()
    print(f"Ingestion: Connected to Redis at {REDIS_HOST}:{REDIS_PORT}")
except redis.exceptions.ConnectionError as e:
    print(f"Ingestion ERROR: Could not connect to Redis: {e}")
    redis_client = None

active_sources: Dict[str, Dict[str, Any]] = {}
active_sources_lock = threading.Lock()

def frame_publisher_loop(source_id: str, frame_deque: collections.deque, control_flag: threading.Event, redis_conn: Optional[redis.Redis]):
    print(f"Ingestion ({source_id}): Starting frame publisher loop.")
    if not redis_conn:
        print(f"Ingestion ERROR ({source_id}): Redis client unavailable for publisher.")
        # Update status to reflect this critical error for this source
        with active_sources_lock:
            if source_id in active_sources:
                active_sources[source_id]['status'] = 'error_redis_unavailable_for_publisher'
        return

    stream_name = f"frames:{source_id}"
    # Maxlen for the Redis stream (number of messages)
    # Approximate trimming: ~ ensures performance by not being perfectly exact.
    stream_maxlen = 1000 

    while not control_flag.is_set():
        try:
            # Pop from deque with a short timeout to remain responsive to control_flag
            frame_data = frame_deque.popleft() 
            frame = frame_data['frame']
            timestamp = frame_data['timestamp']

            # Encode frame to JPEG format for efficient transfer
            ret, encoded_frame = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            if not ret:
                print(f"Ingestion WARNING ({source_id}): Failed to encode frame to JPEG.")
                continue
            
            frame_bytes = encoded_frame.tobytes()

            # Construct message for Redis Stream
            # Keys and values should be bytes for xadd if not automatically converted by redis-py
            message = {
                b'frame_bytes': frame_bytes,
                b'timestamp': str(timestamp).encode('utf-8'), # Ensure timestamp is string then bytes
                b'source_id': source_id.encode('utf-8'),
                b'height': str(frame.shape[0]).encode('utf-8'),
                b'width': str(frame.shape[1]).encode('utf-8'),
                b'format': b'jpeg' # Indicate frame format
            }

            # Add message to Redis Stream
            # The '*' tells Redis to auto-generate a unique ID for this entry.
            redis_conn.xadd(name=stream_name, fields=message, id='*', maxlen=stream_maxlen, approximate=True)
            # print(f"Ingestion ({source_id}): Published frame to Redis Stream '{stream_name}'. Queue: {len(frame_deque)}") # Can be noisy

        except IndexError:
            # Deque is empty, wait a bit or check control_flag
            if control_flag.is_set(): break
            time.sleep(0.005) # Wait briefly before trying to pop again (5ms)
        except redis.exceptions.RedisError as e:
            print(f"Ingestion ERROR ({source_id}): Redis error during xadd: {e}")
            # Potentially try to reconnect or signal error state
            if control_flag.is_set(): break
            time.sleep(1) # Wait longer after a Redis error
        except Exception as e:
            print(f"Ingestion ERROR ({source_id}): Unexpected error in frame publisher loop: {e}")
            if control_flag.is_set(): break
            time.sleep(0.1)
    print(f"Ingestion ({source_id}): Exiting frame publisher loop.")

def start_ingestion_thread(source_id: str, source_url: str, control_flag: threading.Event, frame_deque: collections.deque):
    print(f"Ingestion ({source_id}): Attempting to connect to '{source_url}'...")
    cap = cv2.VideoCapture(source_url)

    if not cap.isOpened():
        print(f"Ingestion ERROR ({source_id}): Could not open video source '{source_url}'.")
        with active_sources_lock: 
            if source_id in active_sources: active_sources[source_id]['status'] = 'error_disconnected'
        return

    print(f"Ingestion ({source_id}): Successfully connected to '{source_url}'. Starting frame capture.")
    with active_sources_lock:
        if source_id in active_sources: # Ensure entry still exists
            active_sources[source_id]['status'] = 'streaming'
            active_sources[source_id]['resolution'] = (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))
            active_sources[source_id]['fps'] = cap.get(cv2.CAP_PROP_FPS)
            # print(f"Ingestion ({source_id}): Resolution: {active_sources[source_id]['resolution']}, FPS: {active_sources[source_id]['fps']:.2f}")

    while not control_flag.is_set():
        ret, frame = cap.read()
        if not ret:
            print(f"Ingestion INFO ({source_id}): End of stream or read error for source. Attempting to reconnect...")
            cap.release(); time.sleep(5)
            if control_flag.is_set(): break
            cap = cv2.VideoCapture(source_url)
            if not cap.isOpened(): 
                print(f"Ingestion ERROR ({source_id}): Failed to reconnect to '{source_url}'.")
                with active_sources_lock: 
                    if source_id in active_sources: active_sources[source_id]['status'] = 'error_disconnected'
                break
            print(f"Ingestion ({source_id}): Reconnected to '{source_url}'.")
            with active_sources_lock: 
                if source_id in active_sources: active_sources[source_id]['status'] = 'streaming'
            continue
        
        frame_deque.append({"frame": frame, "timestamp": time.time()})
    
    cap.release()
    print(f"Ingestion ({source_id}): Stopped capture for source.")
    with active_sources_lock:
        if source_id in active_sources and active_sources[source_id]['status'] not in ['error_disconnected', 'error_redis_unavailable_for_publisher']:
             active_sources[source_id]['status'] = 'stopped_capture' # Indicate capture stopped, publisher might still be working

def add_source(source_id: str, source_url: str, frame_deque_maxlen: int = 10):
    global redis_client # Use the globally initialized redis_client
    if not redis_client:
        print("Ingestion ERROR: Cannot add source, Redis client is not available.")
        return {"status": "error_redis_unavailable", "source_id": source_id, "message": "Global Redis client not connected."}

    with active_sources_lock:
        if source_id in active_sources:
            # Check if threads are actually alive if entry exists
            capture_thread_obj = active_sources[source_id].get('capture_thread_obj')
            publisher_thread_obj = active_sources[source_id].get('publisher_thread_obj')
            if (capture_thread_obj and capture_thread_obj.is_alive()) or \
               (publisher_thread_obj and publisher_thread_obj.is_alive()):
                print(f"Ingestion INFO ({source_id}): Source is already running or attempting to run.")
                return {"status": "already_running", "source_id": source_id}

        control_flag = threading.Event()
        frame_deque = collections.deque(maxlen=frame_deque_maxlen)

        capture_thread = threading.Thread(target=start_ingestion_thread, args=(source_id, source_url, control_flag, frame_deque))
        # Pass the global redis_client to the publisher loop
        publisher_thread = threading.Thread(target=frame_publisher_loop, args=(source_id, frame_deque, control_flag, redis_client))
        
        active_sources[source_id] = {
            'capture_thread_obj': capture_thread,
            'publisher_thread_obj': publisher_thread,
            'control_flag': control_flag,
            'frame_deque': frame_deque,
            'url': source_url,
            'status': 'initializing',
            'resolution': None,
            'fps': None
        }
        capture_thread.daemon = True
        publisher_thread.daemon = True
        capture_thread.start()
        publisher_thread.start()
        print(f"Ingestion ({source_id}): Capture and publisher threads started.")
    return {"status": "started", "source_id": source_id}

def stop_source(source_id: str):
    thread_capture, thread_publisher = None, None
    source_exists_and_was_running = False

    with active_sources_lock:
        if source_id not in active_sources:
            print(f"Ingestion INFO ({source_id}): Source not found for stopping.")
            return {"status": "not_found"}
        
        s_data = active_sources.get(source_id)
        if s_data and (s_data.get('capture_thread_obj',{}).is_alive() or s_data.get('publisher_thread_obj',{}).is_alive()):
            source_exists_and_was_running = True
            print(f"Ingestion ({source_id}): Initiating stop sequence...")
            s_data['control_flag'].set() # Signal threads to stop
            thread_capture = s_data.get('capture_thread_obj')
            thread_publisher = s_data.get('publisher_thread_obj')
        else:
            print(f"Ingestion INFO ({source_id}): Source found but not in a running state or already stopped.")
            if source_id in active_sources: del active_sources[source_id] # Clean up if entry exists but not runnable
            return {"status": "not_running_or_already_stopped"}

    final_status_code = "stopped"
    # Join threads outside the lock
    for t_name, t_obj in [("Capture", thread_capture), ("Publisher", thread_publisher)]:
        if t_obj and t_obj.is_alive():
            print(f"Ingestion ({source_id}): Joining {t_name} thread...")
            t_obj.join(timeout=5.0)
            if t_obj.is_alive():
                print(f"Ingestion WARNING ({source_id}): {t_name} thread did not terminate in time.")
                final_status_code = f"warning_{t_name.lower()}_thread_not_terminated" if final_status_code == "stopped" else f"{final_status_code}_and_{t_name.lower()}"
    
    with active_sources_lock: # Re-acquire lock to safely remove/update the entry
        if source_id in active_sources: # Check if entry still exists
            # Check thread status again after join attempts
            capture_alive = active_sources[source_id].get('capture_thread_obj', {}).is_alive()
            publisher_alive = active_sources[source_id].get('publisher_thread_obj', {}).is_alive()
            if capture_alive or publisher_alive:
                active_sources[source_id]['status'] = f"error_threads_not_stopped (capture_alive: {capture_alive}, publisher_alive: {publisher_alive})"
            else: # Threads are confirmed dead
                print(f"Ingestion ({source_id}): Threads confirmed stopped. Removing entry.")
                del active_sources[source_id]
        elif source_exists_and_was_running:
             print(f"Ingestion WARNING ({source_id}): Entry disappeared during stop operation.")
             final_status_code = "error_entry_disappeared" if final_status_code == "stopped" else final_status_code

    return {"status": final_status_code, "message": f"Source '{source_id}' stop initiated."}


def get_source_status(source_id: str) -> Optional[Dict[str, Any]]:
    with active_sources_lock:
        if source_id in active_sources:
            s = active_sources[source_id]
            return {
                "source_id": source_id, "url": s.get('url'), "status": s.get('status'), 
                "resolution": s.get('resolution'), "fps": s.get('fps'), 
                "queue_size": len(s['frame_deque']) if s.get('frame_deque') else 0,
                "queue_maxlen": s['frame_deque'].maxlen if s.get('frame_deque') else None,
                "is_capture_alive": s.get('capture_thread_obj', {}).is_alive(),
                "is_publisher_alive": s.get('publisher_thread_obj', {}).is_alive(),
            }
    return None

def list_all_sources_status() -> List[Dict[str, Any]]:
    statuses = []
    with active_sources_lock: source_ids = list(active_sources.keys()) 
    for sid in source_ids:
        status = get_source_status(sid) 
        if status: statuses.append(status)
    return statuses

def stop_all_sources():
    print("Ingestion: Initiating shutdown of all sources...")
    with active_sources_lock: source_ids = list(active_sources.keys())
    for sid in source_ids: stop_source(sid)
    print("Ingestion: All source stop commands issued.")

if __name__ == "__main__":
    print("Ingestion service main.py started in test mode.")
    if not redis_client:
        print("CRITICAL: Ingestion service cannot connect to Redis. Frame publishing will fail.")
    else:
        print(f"Successfully connected to Redis: {REDIS_HOST}:{REDIS_PORT}")

    # Example test usage:
    # test_video_file = "path_to_your_test_video.mp4" # Replace with a real video file
    # if os.path.exists(test_video_file):
    #    print(f"Adding test source: {test_video_file}")
    #    add_source("test_file_cam", test_video_file, frame_deque_maxlen=5)
    # else:
    #    print(f"Test video file not found: {test_video_file}. Consider adding a webcam (e.g., ID 0).")
    #    # add_source("test_webcam", 0, frame_deque_maxlen=2) # Example for webcam

    # time.sleep(2)
    # print("\nStatus after adding source(s):")
    # for status in list_all_sources_status(): print(status)
    # time.sleep(10) # Let it run
    # print("\nStopping sources...")
    # if os.path.exists(test_video_file): stop_source("test_file_cam")
    # else: stop_source("test_webcam")
    
    print("\nIngestion service running. Press Ctrl+C to exit and gracefully shutdown sources.")
    try:
        while True: 
            time.sleep(5)
            # Optional: Periodically print status of all sources
            # print("\nPeriodic Status Check:", list_all_sources_status())
    except KeyboardInterrupt:
        print("\nIngestion: KeyboardInterrupt received. Shutting down all sources...")
    finally:
        stop_all_sources()
        if redis_client:
            redis_client.close() # Close Redis connection
            print("Ingestion: Redis client connection closed.")
        print("Ingestion: Test mode finished and all sources signaled to stop.")
