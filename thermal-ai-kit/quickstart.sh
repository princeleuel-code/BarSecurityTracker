#!/bin/bash

# Simple hardware check placeholder - replace with more robust detection
ONNX_EXECUTOR="CPUExecutionProvider" # Default to CPU

if command -v nvidia-smi &> /dev/null; then
    echo "NVIDIA GPU detected. Setting ONNX_EXECUTOR to CUDAExecutionProvider."
    ONNX_EXECUTOR="CUDAExecutionProvider"
# Add Intel iGPU detection here if needed
# elif [ -d /dev/dri ] && ls /dev/dri/renderD* &> /dev/null; then
# echo "Intel iGPU detected. Setting ONNX_EXECUTOR for OpenVINO."
# ONNX_EXECUTOR="OpenVINOExecutionProvider" # Or appropriate for OpenVINO
fi

export ONNX_EXECUTOR

echo "Using ONNX Executor: $ONNX_EXECUTOR"

# Placeholder for pulling Docker images
echo "Pulling Docker images..."
# docker pull your-repo/detector:latest
# docker pull your-repo/fusion:latest
# docker pull your-repo/api:latest
# docker pull your-repo/ui:latest

echo "Launching services with Docker Compose..."
if [ -f docker-compose.yml ]; then
    docker-compose up -d
elif [ -f compose.yaml ]; then
    docker compose up -d
else
    echo "Error: Neither docker-compose.yml nor compose.yaml found."
    exit 1
fi

echo "Services should be starting up."
echo "API will be available at http://localhost:8000"
echo "UI will be available at http://localhost:5173 (if configured in compose.yaml)"
