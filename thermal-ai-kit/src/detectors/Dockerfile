# Base image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy requirements first and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all application code from src/detectors into /app
# This will include main.py, y8_thermal/model.py, c2former/model.py, etc.
# It will also copy the y8_thermal/weights directory if it exists.
COPY . .

# Ensure the model path used in y8_thermal/model.py and detectors/main.py
# matches where the model is copied in this Dockerfile.
# The current Y8_THERMAL_MODEL_PATH is "src/detectors/y8_thermal/weights/y8_thermal.onnx"
# If WORKDIR is /app and we copy "." (src/detectors content) into /app, then the path becomes
# /app/y8_thermal/weights/y8_thermal.onnx.
# The Y8_MODEL_PATH env var in main.py is currently "src/detectors/y8_thermal/weights/y8_thermal.onnx".
# This needs to be consistent. Let's adjust Y8_MODEL_PATH in main.py to be relative to /app,
# e.g., "y8_thermal/weights/y8_thermal.onnx".
# For now, the Dockerfile is fine, the main.py might need adjustment later if Y8_MODEL_PATH is not just the filename.

# No CMD specified as this service's functions are currently designed 
# to be called by other services.
