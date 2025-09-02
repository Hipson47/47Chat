# syntax=docker/dockerfile:1

# Base image
FROM python:3.10-slim

# Prevent python from writing .pyc and enable unbuffered stdout
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# System deps (optional but useful)
RUN apt-get update && apt-get install -y --no-install-recommends \
    bash ca-certificates curl && \
    rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
# We copy backend/requirements.txt as a single requirements file
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install -r /app/requirements.txt

# Copy application source
COPY backend /app/backend
COPY frontend /app/frontend

# Expose default ports
EXPOSE 8000 8501

# Default command: run both backend (uvicorn) and frontend (streamlit)
# In docker-compose, each service will override this CMD to run individually
CMD bash -lc "\
  uvicorn backend.main:app --host 0.0.0.0 --port 8000 & \
  streamlit run frontend/app.py --server.port 8501 --server.address 0.0.0.0"
