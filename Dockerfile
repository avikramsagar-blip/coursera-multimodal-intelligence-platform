# --- Stage 1: build frontend ---
FROM node:20-bullseye-slim AS frontend_builder

WORKDIR /src/frontend

# Install CA certs so npm can fetch packages
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates && rm -rf /var/lib/apt/lists/*

# Copy package files and install deps first for caching
COPY frontend/package*.json ./

# Copy full frontend and build
COPY frontend/ .

# Use npm ci if lockfile present, otherwise npm install
RUN if [ -f package-lock.json ]; then npm ci --legacy-peer-deps; else npm install --legacy-peer-deps; fi
RUN npm run build

# --- Stage 2: python backend + static assets ---
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    APP_ENV=production \
    BACKEND_PORT=8000 \
    FRONTEND_DIST=/app/frontend_dist

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ffmpeg \
        build-essential \
        libpq-dev \
        curl \
        ca-certificates \
        libffi-dev \
        libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Python deps
COPY backend/requirements.txt /tmp/requirements.txt
RUN python -m pip install --upgrade pip setuptools wheel \
    && pip install -r /tmp/requirements.txt

# Copy backend source
COPY backend/ /app/backend

# Copy built frontend from builder
COPY --from=frontend_builder /src/frontend/dist ${FRONTEND_DIST}

WORKDIR /app
ENV PYTHONPATH=/app

EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
