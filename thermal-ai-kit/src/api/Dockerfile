# Base image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code (ensure all necessary .py files are in src/api or subdirs)
COPY . .

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
# Healthcheck can be added later if needed
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
