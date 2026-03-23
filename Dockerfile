FROM python:3.11-slim

WORKDIR /app

# Install dependencies first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source only — .dockerignore handles exclusions
# NEVER use "COPY . ." — it copies .env into the image
COPY src/ ./src/

EXPOSE 8001

# Use sh -c form for shell variable expansion (required for Railway PORT)
# Exec form does NOT expand ${PORT} — learned from Project 1 Phase 7
CMD sh -c "PYTHONPATH=/app/src uvicorn src.api.main:app --host 0.0.0.0 --port ${PORT:-8001}"
