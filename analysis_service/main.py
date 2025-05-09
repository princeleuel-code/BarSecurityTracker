import os
import json
import pika
import time
from prometheus_client import start_http_server, Counter, Histogram
from typing import Dict

from schemas import DetectionBatch, AnalysisResult
from tracker.bytetrack_tracker import ByteTrackTracker

# Prometheus metrics
FRAMES_PROCESSED = Counter('analysis_frames_processed_total', 'Total frames processed')
TRACKER_LATENCY = Histogram('analysis_tracker_latency_seconds', 'Tracker processing latency')

def process_detection(ch, method, properties, body):
    try:
        detection_batch = DetectionBatch.parse_raw(body)
        start_time = time.time()
        
        # Process through ByteTrack
        tracked_objects = tracker.update(detection_batch.detections)
        
        analysis_time = time.time() - start_time
        TRACKER_LATENCY.observe(analysis_time)
        FRAMES_PROCESSED.inc()

        # Create and publish result
        result = AnalysisResult(
            frame_id=detection_batch.frame_id,
            timestamp=detection_batch.timestamp,
            tracked_objects=tracked_objects,
            source=detection_batch.source,
            analysis_time=analysis_time
        )
        
        # Publish to results queue
        channel.basic_publish(
            exchange='',
            routing_key='analysis_results',
            body=result.json()
        )

    except Exception as e:
        print(f"Error processing detection: {e}")

if __name__ == "__main__":
    # Start Prometheus metrics server
    prometheus_port = int(os.getenv('PROMETHEUS_PORT', '9105'))
    start_http_server(prometheus_port)
    
    # Initialize ByteTrack
    tracker = ByteTrackTracker()
    
    # Setup RabbitMQ connection
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=os.getenv('RABBITMQ_HOST', 'rabbitmq'))
    )
    channel = connection.channel()
    
    # Ensure queues exist
    channel.queue_declare(queue='detections_rgb')
    channel.queue_declare(queue='analysis_results')
    
    # Start consuming detections
    channel.basic_consume(
        queue='detections_rgb',
        on_message_callback=process_detection,
        auto_ack=True
    )
    
    print("Analysis service started. Waiting for DetectionBatch messages...")
    channel.start_consuming()