@echo off
REM Setup script for Windows (first-time setup)
SETLOCAL ENABLEDELAYEDEXPANSION

echo Creating Python virtual environment 'venv'...
python -m venv venv
if errorlevel 1 (
  echo Failed to create virtual environment. Make sure Python is installed and on PATH.
  exit /b 1
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Installing backend Python dependencies...
pip install --upgrade pip
pip install -r backend\requirements.txt

echo Installing frontend dependencies...
cd frontend
if exist node_modules (
  echo node_modules already exists, skipping npm install
) else (
  npm install
)
cd ..

echo Creating required directories...
mkdir backend\uploads 2>nul
mkdir backend\faiss_indexes 2>nul
mkdir backend\logs 2>nul
mkdir backend\temp 2>nul

echo Setup complete. Create a .env file by copying .env.example and filling values if needed.
echo To start backend: venv\Scripts\activate && python -m uvicorn backend.main:app --reload --port 8000
echo To start frontend: cd frontend && npm run dev
pause
