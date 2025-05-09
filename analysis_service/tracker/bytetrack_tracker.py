from typing import List
from schemas import Detection
import numpy as np
from .bytetrack.byte_tracker import BYTETracker

class ByteTrackTracker:
    def __init__(self):
        self.tracker = BYTETracker(
            track_thresh=0.5,
            track_buffer=30,
            match_thresh=0.8,
            frame_rate=30
        )

    def update(self, detections: List[Detection]) -> List[Detection]:
        # Convert detections to ByteTrack format
        boxes = np.array([[d.x1, d.y1, d.x2, d.y2] for d in detections])
        scores = np.array([d.confidence for d in detections])
        classes = np.array([d.class_id for d in detections])
        
        # Run ByteTrack update
        online_targets = self.tracker.update(
            boxes,
            scores,
            classes
        )
        
        # Convert back to our Detection format
        tracked_detections = []
        for t in online_targets:
            tracked_detections.append(Detection(
                x1=float(t.tlwh[0]),
                y1=float(t.tlwh[1]),
                x2=float(t.tlwh[0] + t.tlwh[2]),
                y2=float(t.tlwh[1] + t.tlwh[3]),
                confidence=float(t.score),
                class_id=int(t.cls),
                track_id=int(t.track_id)
            ))
            
        return tracked_detections