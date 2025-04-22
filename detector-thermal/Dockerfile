# ─────────────────────────────────────────────────────────────
# Thermal Detector – YOLOv11‑T (INT8) + SAM2
# Builds on NVIDIA's PyTorch base image for GPU support.
# ─────────────────────────────────────────────────────────────
FROM nvcr.io/nvidia/pytorch:24.04-py3

# 1. Minimal OS libs
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libgl1-mesa-glx \
        python3-pip && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /opt

# Remove any pre-existing OpenCV from dist-packages
RUN python -c "import subprocess, sys, pkg_resources, os, shutil; \
    p=[p for p in sys.path if '/dist-packages' in p and (p+'/cv2')]; \
    [shutil.rmtree(cv) for cv in p if os.path.isdir(cv+'/cv2')]" || true

# 2. Python deps
RUN pip3 install --no-cache-dir --force-reinstall --upgrade \
      opencv-python-headless==4.9.0.80 \
      torch==2.3.0 \
      ultralytics==8.3.112 \
      samurai==0.6 \
      norfair==2.3.1 \
      websockets==12.0 \
      prometheus_client==0.20.0

# 3. Copy detector script
COPY thermal_detector.py .

# 4. By default, run on CUDA if available; fallback to CPU
ENV BARSHIELD_DEVICE=cuda

# 5. Entrypoint
CMD ["python", "thermal_detector.py"]
