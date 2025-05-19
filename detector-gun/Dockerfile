FROM python:3.10-slim
WORKDIR /opt
RUN pip install --no-cache-dir websockets prometheus_client
COPY gun_detector.py .
CMD ["python", "gun_detector.py"]
