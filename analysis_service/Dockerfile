FROM python:3.11-slim

# Install build dependencies first
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .
COPY ../schemas.py /app/schemas.py

# Environment variables
ENV PROMETHEUS_PORT=9105
ENV RABBITMQ_HOST=rabbitmq

CMD ["python", "main.py"]