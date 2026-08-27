FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements from backend
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project code
COPY . .

# Set Python path
ENV PYTHONPATH=/app
ENV PORT=7860

# Create data directory for SQLite checkpointer
RUN mkdir -p /app/data

# Expose ports: 7860 (Hugging Face / Default), 8000 (Docker), 8001 (Dev)
EXPOSE 7860 8000 8001

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT:-7860}/health || exit 1

# Start Uvicorn on dynamic port
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-7860}"]
