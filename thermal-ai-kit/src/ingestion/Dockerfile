# Base image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# No CMD specified as this service's functions are currently designed 
# to be called by other services (e.g., API service triggering add_source).
# If it were a standalone polling service, a CMD would be needed here.
