FROM python:3.10-slim
WORKDIR /opt
RUN pip install --no-cache-dir opencv-python-headless websockets prometheus_client
COPY ffd_detector.py .
CMD ["python", "ffd_detector.py"]
