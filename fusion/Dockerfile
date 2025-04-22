# ─────────────────────────────────────────────────────────────
# Fusion Service
# Listens to RGB & Thermal detector WebSockets,
# merges overlapping detections, and publishes a single
# fused alert stream for downstream consumers.
# ─────────────────────────────────────────────────────────────
FROM python:3.10-slim

# 1. Minimal OS libs
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libgl1-mesa-glx && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /opt

# 2. Python deps
RUN pip install --no-cache-dir \
      websockets==12.0 \
      shapely==2.0.2 \
      numpy==1.26.4 \
      prometheus_client==0.20.0

# 3. Copy fusion script
COPY fusion.py .

# 4. Entrypoint
CMD ["python", "fusion.py"]
