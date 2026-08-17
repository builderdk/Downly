# ==========================================
# DENO BINARY
# ==========================================
FROM denoland/deno:bin-2.9.4 AS deno

# ==========================================
# PYTHON BACKEND
# ==========================================
FROM python:3.11-slim

# Install FFmpeg
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# Copy Deno binary from official Deno image
COPY --from=deno /deno /usr/local/bin/deno

# Application directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy backend files
COPY app ./app
COPY main.py .

# Render provides PORT automatically
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}