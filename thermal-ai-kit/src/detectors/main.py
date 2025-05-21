import time
import os
from typing import Dict, Any, List
import numpy as np

try:
    from .y8_thermal.model import Y8ThermalDetector
except ImportError as e:
    print(f"Error importing Y8ThermalDetector: {e}. Ensure it is in the correct path.")
    Y8ThermalDetector = None

print("Detectors service main.py loaded")

Y8_THERMAL_MODEL_PATH = os.getenv("Y8_MODEL_PATH", "y8_thermal/weights/y8_thermal.onnx")
# Note: Adjusted default path to be relative to /app if src/detectors is copied to /app.
# If Y8_MODEL_PATH is an absolute path like /app/src/detectors/y8_thermal/weights/y8_thermal.onnx,
# then the Dockerfile COPY and this path need to align.
# Assuming WORKDIR /app and `COPY . .` from src/detectors, this path becomes /app/y8_thermal/weights/y8_thermal.onnx

detectors: Dict[str, Any] = {}

def initialize_detectors():
    global detectors
    print("Initializing detectors...")

    if Y8ThermalDetector:
        try:
            print(f"Attempting to initialize Y8 Thermal detector with default providers (ONNX_EXECUTOR env var based or CUDA > CPU preference in model.py)...")
            # Y8ThermalDetector's __init__ already tries to use ONNX_EXECUTOR or defaults.
            # For explicit fallback, we can try specific providers.
            
            primary_providers = None # Let model.py decide based on ONNX_EXECUTOR or its internal default
            onnx_executor_env = os.getenv('ONNX_EXECUTOR')
            if onnx_executor_env == "CUDAExecutionProvider":
                primary_providers = ['CUDAExecutionProvider', 'CPUExecutionProvider']
            elif onnx_executor_env == "OpenVINOExecutionProvider": # Example for OpenVINO
                 primary_providers = ['OpenVINOExecutionProvider', 'CPUExecutionProvider']
            # Add other specific providers as needed based on ONNX_EXECUTOR

            detector_instance = Y8ThermalDetector(model_path=Y8_THERMAL_MODEL_PATH, providers=primary_providers)
            print(f"Y8 Thermal detector initialized successfully with providers: {detector_instance.session.get_providers()}")

            # Warm-up call
            print("Warming up Y8 Thermal detector...")
            # Use the expected input dimensions from the model, or a common default
            warmup_h = detector_instance.input_height if detector_instance.input_height else 640
            warmup_w = detector_instance.input_width if detector_instance.input_width else 640
            dummy_frame = np.zeros((warmup_h, warmup_w, 3), dtype=np.uint8)
            detector_instance.detect(dummy_frame) # Perform a dummy inference
            print("Y8 Thermal detector warmed up.")
            
            detectors['y8_thermal'] = detector_instance

        except Exception as e_primary:
            print(f"Failed to initialize Y8 Thermal detector with primary providers: {e_primary}")
            print("Attempting fallback to CPUExecutionProvider...")
            try:
                cpu_providers = ['CPUExecutionProvider']
                detector_instance_cpu = Y8ThermalDetector(model_path=Y8_THERMAL_MODEL_PATH, providers=cpu_providers)
                print(f"Y8 Thermal detector initialized successfully with CPUExecutionProvider.")

                # Warm-up call for CPU
                print("Warming up Y8 Thermal detector on CPU...")
                warmup_h_cpu = detector_instance_cpu.input_height if detector_instance_cpu.input_height else 640
                warmup_w_cpu = detector_instance_cpu.input_width if detector_instance_cpu.input_width else 640
                dummy_frame_cpu = np.zeros((warmup_h_cpu, warmup_w_cpu, 3), dtype=np.uint8)
                detector_instance_cpu.detect(dummy_frame_cpu)
                print("Y8 Thermal detector (CPU) warmed up.")

                detectors['y8_thermal'] = detector_instance_cpu
            except Exception as e_cpu:
                print(f"Failed to initialize Y8 Thermal detector with CPUExecutionProvider as fallback: {e_cpu}")
                if 'y8_thermal' in detectors: del detectors['y8_thermal']
    else:
        print("Y8ThermalDetector class not available.")

    if not detectors:
        print("WARNING: No detectors were successfully initialized!")
    else:
        print(f"Initialized detectors: {list(detectors.keys())}")


def process_frame_for_detections(source_id: str, frame: np.ndarray, detector_name: str = 'y8_thermal', confidence_threshold=0.5, iou_threshold=0.45) -> Dict[str, Any]:
    start_time = time.time()
    if detector_name not in detectors:
        print(f"Detector '{detector_name}' not available or not initialized.")
        return {
            "error": f"Detector '{detector_name}' not available.",
            "source_id": source_id,
            "timestamp": start_time,
            "detections": []
        }
    detector_instance = detectors[detector_name]
    try:
        if not isinstance(frame, np.ndarray):            raise ValueError("Input frame is not a valid NumPy array.")
        raw_detections = detector_instance.detect(frame, confidence_threshold=confidence_threshold, iou_threshold=iou_threshold)
        processing_time = time.time() - start_time
        # print(f"Detector '{detector_name}' processed frame from '{source_id}' in {processing_time:.4f}s. Found {len(raw_detections)} objects.")
        return {
            "source_id": source_id,
            "timestamp": start_time,
            "detector_name": detector_name,
            "processing_time_ms": int(processing_time * 1000),
            "detections": raw_detections
        }
    except Exception as e:
        print(f"Error during detection with '{detector_name}' for source '{source_id}': {e}")
        return {
            "error": str(e),
            "source_id": source_id,
            "timestamp": start_time,
            "detections": []
        }

initialize_detectors()

if __name__ == "__main__":
    print("\nDetector service self-test section:")
    if not detectors:
        print("No detectors initialized, cannot run self-test.")
    else:
        print(f"Available detectors for test: {list(detectors.keys())}")
        dummy_frame_height, dummy_frame_width = 480, 640
        dummy_frame = np.random.randint(0, 255, (dummy_frame_height, dummy_frame_width, 3), dtype=np.uint8)
        test_source_id = "test_source_main"
        if 'y8_thermal' in detectors:
            print(f"\nTesting with 'y8_thermal' detector using a dummy {dummy_frame_width}x{dummy_frame_height} frame...")
            results = process_frame_for_detections(test_source_id, dummy_frame, detector_name='y8_thermal')
            if "error" in results:
                print(f"Test Detection Error (y8_thermal): {results['error']}")
            else:
                print(f"Test Detections (y8_thermal) for '{test_source_id}':")
                if results['detections']:
                    for det in results['detections']:
                        print(f"  Class: {det['class_name']}, Conf: {det['confidence']:.2f}, BBox: {det['bbox']}")
                else:
                    print("  No detections.")
                print(f"  Processing time: {results['processing_time_ms']}ms")
        else:
            print("\n'y8_thermal' detector not available for testing.")
    print("\nDetector service self-test finished.")
