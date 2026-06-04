# Stage 1: Build & Package Runner
FROM python:3.10-slim

# Prevent Python from writing pyc files and enable unbuffered stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies required for Pillow image compilation
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    libjpeg-dev \
    zlib1g-dev \
    libfreetype6-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy backend source files
COPY . /app/

# Expose FastAPI server port
EXPOSE 8000

# Execute server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
