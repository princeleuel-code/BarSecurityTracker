FROM nvcr.io/nvidia/pytorch:24.04-py3

# Install dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libgl1-mesa-glx \
        python3-pip && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /opt

# Fix OpenCV import issues
RUN python -c "import subprocess, sys, pkg_resources, os, shutil; \
    p=[p for p in sys.path if '/dist-packages' in p][0]; \
    os.makedirs(p, exist_ok=True); \
    shutil.rmtree(os.path.join(p, 'cv2'), ignore_errors=True)"

# Install Python packages
RUN pip3 install --no-cache-dir --force-reinstall --upgrade \
      opencv-python-headless==4.9.0.80 \
      torch==2.3.0 \
      torchvision==0.18.0 \
      ultralytics==8.1.0 \
      websockets==12.0 \
      prometheus_client==0.20.0 \
      norfair==2.2.0 \
      numpy==1.26.4

# Copy source code
COPY rgb_detector.py .

# Run the detector
CMD ["python", "rgb_detector.py"]
