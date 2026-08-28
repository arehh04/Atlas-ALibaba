FROM python:3.12-slim

# Application root: the backend package lives at /srv/backend so that
# `import backend.main` resolves with PYTHONPATH=/srv.
WORKDIR /srv

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for layer caching
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Copy application code as the `backend` package
COPY . /srv/backend

# Set Python path to ensure module imports work seamlessly
ENV PYTHONPATH=/srv
ENV PORT=7860

# Create data directory for SQLite
RUN mkdir -p /srv/backend/data

# Expose Hugging Face (7860), Standard (8000), and Dev (8001) ports
EXPOSE 7860 8000 8001

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT:-7860}/health || exit 1

# Run with uvicorn listening on dynamic $PORT (default 7860 for HF Spaces)
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-7860}"]
