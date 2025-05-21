from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict
import threading # Added for threading.Lock

app = FastAPI(title="Thermal AI Kit API")

# --- Thread Safety for Shared Resources ---
# Lock for controlling access to the video_sources dictionary
sources_lock = threading.Lock()

# In-memory storage for sources and detection results (for demonstration)
video_sources: Dict[str, 'SourceInfo'] = {}
# Mock detection results for demonstration
mock_detection_results: Dict[str, List[Dict]] = {
    "barcam_frame1": [{"class": "person", "bbox": [10, 10, 50, 100], "confidence": 0.9}],
    "barcam_frame2": [{"class": "handgun", "bbox": [150, 70, 60, 40], "confidence": 0.85}],
    "entry_cam_frame1": []
}


class Source(BaseModel):
    id: str
    url: str
    description: Optional[str] = None

class SourceInfo(Source):
    status: str = "disconnected"

class Query(BaseModel):
    q: str
    source_id: Optional[str] = None

class Detection(BaseModel):
    cls: str
    bbox: List[float]
    confidence: float
    track_id: Optional[int] = None

class FrameDetections(BaseModel):
    source_id: str
    frame_id: str
    detections: List[Detection]

@app.post("/source", response_model=SourceInfo)
async def add_or_update_source(source: Source):
    print(f"Received request to add/update source: id={source.id}, url={source.url}")
    with sources_lock: # Acquire lock before accessing video_sources
        if source.id in video_sources:
            video_sources[source.id].url = source.url
            video_sources[source.id].description = source.description
            action = "updated"
        else:
            video_sources[source.id] = SourceInfo(**source.dict(), status="pending_connection")
            action = "added"
        
        # Placeholder: Actual logic to connect to the source via the Ingestion service
        video_sources[source.id].status = "streaming" # Simulate connection
        source_info_copy = video_sources[source.id].copy(deep=True) # Return a copy

    print(f"Source '{source.id}' {action}. Current status: {source_info_copy.status}")
    return source_info_copy

@app.get("/source/{source_id}", response_model=SourceInfo)
async def get_source_info(source_id: str):
    with sources_lock: # Acquire lock
        source_info = video_sources.get(source_id)
        if not source_info:
            raise HTTPException(status_code=404, detail=f"Source ID '{source_id}' not found.")
        return source_info.copy(deep=True) # Return a copy

@app.get("/sources", response_model=List[SourceInfo])
async def list_sources():
    with sources_lock: # Acquire lock
        # Return a list of copies
        return [s_info.copy(deep=True) for s_info in video_sources.values()]

@app.post("/query", response_model=List[FrameDetections])
async def process_query(query: Query):
    print(f"Received query: '{query.q}' for source_id: {query.source_id}")
    
    # Check if specific source_id is provided and exists (if so)
    if query.source_id:
        with sources_lock: # Acquire lock for reading video_sources
            if query.source_id not in video_sources:
                raise HTTPException(status_code=404, detail=f"Source ID '{query.source_id}' not found for query.")
            # Further check if this source_id is present in mock_detection_results if that's the sole source of data
            # This part of logic might need refinement based on how data flows from ingestion/detection
            source_keys_in_mock = {k.split("_")[0] for k in mock_detection_results.keys()}
            if query.source_id not in source_keys_in_mock:
                 raise HTTPException(status_code=404, detail=f"Source ID '{query.source_id}' not found in mock detection results.")


    results: List[FrameDetections] = []
    if "handgun" in query.q.lower():
        for frame_key, detections_list in mock_detection_results.items():
            current_source_id = frame_key.split("_")[0]
            
            if query.source_id and query.source_id != current_source_id:
                continue

            processed_detections: List[Detection] = []
            for det in detections_list:
                if det["class"] == "handgun":
                    processed_detections.append(Detection(
                        cls=det["class"],
                        bbox=det["bbox"],
                        confidence=det["confidence"]
                    ))
            
            if processed_detections:
                results.append(FrameDetections(
                    source_id=current_source_id,
                    frame_id=frame_key,
                    detections=processed_detections
                ))
                
    elif query.q: # If query is not empty and not "handgun"
        # For now, if it's not a handgun query, return a placeholder indicating not implemented or no results
        # Depending on desired behavior, could be empty list or 501
        # For a query that is valid but has no results, empty list is fine.
        # For a query type that is not understood, 501 might be better.
        # Let's assume any query term not "handgun" is valid but just has no mock results for now.
        pass # Results will be an empty list if no specific non-handgun mock data exists

    # If results are empty after processing, and a specific source was queried that had no matching results,
    # this is not necessarily a 404 on the source itself (checked above), but simply no data for the query.
    # The current logic returns an empty list which is appropriate.
    
    return results

@app.get("/")
async def read_root():
    return {"message": "Thermal AI Kit API is running. See /docs for API documentation."}

@app.get("/healthz", status_code=200)
async def health_check():
    # Basic health check. Future: check Redis connection, other critical services.
    return {"status": "healthy"}

# To run this app (for development without Docker):
# uvicorn main:app --reload --port 8000
