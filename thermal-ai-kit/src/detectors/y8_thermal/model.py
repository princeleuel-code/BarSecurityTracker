import onnxruntime
import numpy as np
import os
import cv2 # For preprocessing, if needed

print("Y8 Thermal model.py loaded")

class Y8ThermalDetector:
    def __init__(self, model_path="y8_thermal.onnx", config_path=None, providers=None):
        """
        Initializes the YOLOv8-Thermal-Attn ONNX detector.

        Args:
            model_path (str): Path to the ONNX model file.
            config_path (str, optional): Path to a model-specific configuration file (e.g., for class names, thresholds).
            providers (list, optional): List of ONNXRuntime execution providers to use (e.g., ['CUDAExecutionProvider', 'CPUExecutionProvider']).
                                        If None, uses ONNX_EXECUTOR env var or defaults.
        """
        self.model_path = model_path
        self.config_path = config_path # Not used in this basic example, but good for future
        
        if providers is None:
            # Prioritize ONNX_EXECUTOR environment variable if set
            onnx_executor_env = os.getenv('ONNX_EXECUTOR')
            if onnx_executor_env:
                if onnx_executor_env == "CUDAExecutionProvider":
                    self.providers = ['CUDAExecutionProvider', 'CPUExecutionProvider']
                elif onnx_executor_env == "OpenVINOExecutionProvider":
                    # May require specific OpenVINO setup and provider options
                    self.providers = ['OpenVINOExecutionProvider', 'CPUExecutionProvider']
                else: # Default or CPU
                    self.providers = ['CPUExecutionProvider']
            else: # Default if env var is not set
                self.providers = ['CPUExecutionProvider']
        else:
            self.providers = providers

        print(f"Y8ThermalDetector: Initializing with ONNXRuntime providers: {self.providers}")

        try:
            self.session = onnxruntime.InferenceSession(self.model_path, providers=self.providers)
            print(f"Y8ThermalDetector: ONNX model loaded successfully from {self.model_path}")
            self.input_name = self.session.get_inputs()[0].name
            self.output_names = [output.name for output in self.session.get_outputs()]
            
            input_shape = self.session.get_inputs()[0].shape
            print(f"Y8ThermalDetector: Model input name: {self.input_name}, shape: {input_shape}")
            print(f"Y8ThermalDetector: Model output names: {self.output_names}")

            self.input_height = input_shape[2] if isinstance(input_shape[2], int) else 640
            self.input_width = input_shape[3] if isinstance(input_shape[3], int) else 640

        except Exception as e:
            print(f"Y8ThermalDetector ERROR: Failed to load ONNX model or configure session: {e}")
            print("Ensure the model path is correct and ONNXRuntime is installed with the chosen providers (e.g., onnxruntime-gpu for CUDA).")
            self.session = None
            raise

        self.class_names = {0: 'person', 1: 'vehicle', 2: 'bicycle', 3: 'handgun'} # Example for thermal

    def preprocess(self, frame: np.ndarray) -> np.ndarray:
        """
        Preprocesses the input frame to meet model requirements.
        """
        img_resized = cv2.resize(frame, (self.input_width, self.input_height))
        img_rgb = cv2.cvtColor(img_resized, cv2.COLOR_BGR2RGB)
        img_chw = np.transpose(img_rgb, (2, 0, 1))
        img_normalized = img_chw / 255.0
        input_tensor = np.expand_dims(img_normalized, axis=0).astype(np.float32)
        return input_tensor

    def postprocess(self, outputs: list, frame_shape: tuple, confidence_threshold=0.5, iou_threshold=0.45) -> list:
        """
        Postprocesses the raw output from the ONNX model.
        Adjust this function based on your model's output signature.
        """
        detections = []
        raw_output = outputs[0][0]

        if raw_output.shape[0] == (len(self.class_names) + 4) and raw_output.shape[1] > (len(self.class_names) + 4):
            raw_output = raw_output.T

        boxes = []
        confidences = []
        class_ids = []
        original_height, original_width = frame_shape

        for i in range(raw_output.shape[0]):
            proposal = raw_output[i]
            x_center, y_center, width, height = proposal[:4]
            class_scores = proposal[4:]
            class_id = np.argmax(class_scores)
            confidence = class_scores[class_id]

            if confidence >= confidence_threshold:
                x_min = (x_center - width / 2) * (original_width / self.input_width)
                y_min = (y_center - height / 2) * (original_height / self.input_height)
                x_max = (x_center + width / 2) * (original_width / self.input_width)
                y_max = (y_center + height / 2) * (original_height / self.input_height)
                boxes.append([int(x_min), int(y_min), int(x_max), int(y_max)])
                confidences.append(float(confidence))
                class_ids.append(int(class_id))

        indices = cv2.dnn.NMSBoxes(boxes, confidences, confidence_threshold, iou_threshold)
        
        if len(indices) > 0:
            selected_indices = indices.flatten() if hasattr(indices, 'flatten') else []
            for i in selected_indices:
                bbox = boxes[i]
                detections.append({
                    "class_id": class_ids[i],
                    "class_name": self.class_names.get(class_ids[i], "unknown"),
                    "confidence": confidences[i],
                    "bbox": bbox
                })
        return detections

    def detect(self, frame: np.ndarray, confidence_threshold=0.5, iou_threshold=0.45) -> list:
        """
        Performs detection on a single frame.
        """
        if self.session is None:
            print("Y8ThermalDetector ERROR: Model session not initialized.")
            return []
        original_shape = frame.shape[:2]
        input_tensor = self.preprocess(frame)
        try:
            outputs = self.session.run(self.output_names, {self.input_name: input_tensor})
        except Exception as e:
            print(f"Y8ThermalDetector ERROR: ONNX Runtime inference failed: {e}")
            return []
        return self.postprocess(outputs, original_shape, confidence_threshold, iou_threshold)

if __name__ == "__main__":
    print("Y8ThermalDetector self-test section")
    dummy_model_path = "dummy_y8_thermal.onnx"
    if not os.path.exists(dummy_model_path):
        print(f"Warning: Dummy model '{dummy_model_path}' not found. Create one or use a real model for testing.")
        print("Skipping detector instantiation for self-test without a model.")
    else:
        try:
            detector = Y8ThermalDetector(model_path=dummy_model_path, providers=['CPUExecutionProvider'])
            print(f"Successfully instantiated Y8ThermalDetector with dummy model {dummy_model_path}.")
            dummy_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            print("Performing dummy detection...")
            detections = detector.detect(dummy_frame)
            print(f"Dummy detections: {detections}")
        except Exception as e:
            print(f"Error during Y8ThermalDetector self-test: {e}")
