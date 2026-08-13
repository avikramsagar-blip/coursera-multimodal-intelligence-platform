#!/usr/bin/env bash
set -e

echo "Setting up the project for first-time use..."

# Create Python virtual environment
if [ ! -d "venv" ]; then
  python3 -m venv venv
fi

# Activate
. venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install backend requirements
pip install -r backend/requirements.txt

# Install frontend dependencies
if [ -d "frontend/node_modules" ]; then
  echo "frontend/node_modules already exists, skipping npm install"
else
  (cd frontend && npm install)
fi

# Create directories
mkdir -p backend/uploads
mkdir -p backend/faiss_indexes
mkdir -p backend/logs
mkdir -p backend/temp

echo "Setup complete. Copy .env.example to .env and edit values as needed."
echo "Start backend: . venv/bin/activate && python -m uvicorn backend.main:app --reload --port 8000"
echo "Start frontend: cd frontend && npm run dev"
