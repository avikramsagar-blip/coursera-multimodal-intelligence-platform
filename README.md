# Coursera Multimodal Intelligence Platform

Overview
--------

A full-stack learning platform that supports course materials (PDF, video, audio, images) and an AI Tutor powered by Retrieval-Augmented Generation (RAG). This repository contains a FastAPI backend and a React + Vite frontend.

This README documents how to set up the project locally (Windows / macOS / Linux) so a new user can clone, install, and run the app.

Quick summary
-------------

- Backend: Python + FastAPI
- Frontend: React + Vite
- Vector DB: FAISS (local indexes)
- Embeddings: Google Generative AI / Gemini (optional)

Prerequisites
-------------

- Python 3.10+ installed and on PATH
- Node.js 18+ and npm
- Git
- (Optional, for RAG/whisper) ffmpeg installed on system PATH for media processing

Files added in this branch
-------------------------

- `.env.example` â€” sample environment variables
- `setup.bat` â€” Windows first-time setup script
- `setup.sh` â€” Unix (Linux/macOS) first-time setup script
- `frontend/src/pages/CreateCourse.jsx` â€” Create Course UI
- Updates to backend to provide `/health` endpoint and startup validation logs
- Fixes to frontend axios Authorization header

1. Create a virtual environment
-------------------------------

Windows (PowerShell):

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

macOS / Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

Or run the provided setup script (recommended for first-time users):

Windows:
```
setup.bat
```

macOS / Linux:
```
chmod +x setup.sh
./setup.sh
```

2. Environment variables
------------------------

Copy `.env.example` to `.env` and fill values.

Minimal dev values (recommended):

```
SECRET_KEY=dev-secret-key
DATABASE_URL=sqlite:///./dev.db
GEMINI_API_KEY=
CLOUDINARY_CLOUD_NAME=
CLOUDINARY_API_KEY=
CLOUDINARY_API_SECRET=
```

Notes:
- GEMINI_API_KEY is optional for development. If missing, vector indexing or embedding-based features will be limited. The startup logs will notify you if it is missing.

3. Installing dependencies
--------------------------

Backend (from repo root):

```bash
# activate venv
pip install -r backend/requirements.txt
```

Frontend:

```bash
cd frontend
npm install
```

4. Start backend and frontend
----------------------------

Backend (from repo root):

```bash
# activate venv
python -m uvicorn backend.main:app --reload --port 8000
```

Frontend (from repo root):

```bash
cd frontend
npm run dev
```

Default backend base URL in frontend is `http://127.0.0.1:8000`.

5. What to expect on first run
------------------------------

- On backend startup you will see startup validation logs in the terminal:
  - Database connectivity check
  - Tables created/verified
  - Upload directory existence
  - FAISS (vector store) directory existence
  - Gemini API key presence (detected/missing)

- Visit http://127.0.0.1:8000/docs for interactive Swagger UI. Use the Login endpoint to obtain a JWT and click Authorize to provide the token.

- Health endpoint: GET http://127.0.0.1:8000/health â€” reports database and RAG/index status.

6. Create Course (frontend)
---------------------------

- Log in (or register) in the frontend.
- On the Dashboard (when logged in) you will see a "Create Course" button.
- Click it to open the Create Course form; fill Title, Description, Category, Difficulty, Price and optional Thumbnail.
- After creating, you will be redirected to the Course Details page where you can upload PDFs and other media.

7. Upload PDFs and build vector store
------------------------------------

- Use the Course Details page to upload PDF materials.
- After uploading, call the "Generate Vector DB" action (button or endpoint) to build the FAISS index for that course.
- If the vector store is missing when querying, the API will return a clear 404 with a friendly message asking to generate the index.

8. Debugging & common issues
----------------------------

- If you see "Gemini API Key: NOT detected" in startup logs, the embedding step will be disabled until you provide an API key.
- If the frontend does not send authenticated requests, ensure the Authorization header is set in `localStorage.token`. The frontend code attaches `Authorization: Bearer <token>` automatically when a token is present.
- If you see "no such table" errors after a fresh clone, ensure backend started successfully and startup logs show "Database: tables created/verified".

9. Development notes
--------------------

- To run backend on a different port, set `BACKEND_PORT` in `.env` and update frontend baseURL in `frontend/src/api/api.js` if required.
- The sample scripts `setup.bat` and `setup.sh` will install requirements and create required directories.

10. Next improvements planned (not in this change)
--------------------------------------------------

- Demo seeding (disabled for now)
- Docker/Docker Compose for reproducible deployment
- Role-based access controls for admin/instructor features
- More robust test coverage and CI integration

If you encounter any issues during setup, please share the backend terminal logs and browser console logs so the problem can be diagnosed quickly.

After running:

cd frontend
npm run dev

Open:

http://localhost:5173

## First Login

1. Open http://127.0.0.1:8000/docs
2. Use POST /register
3. Create an account
4. Use POST /login
5. Copy the access token
6. Click Authorize
7. Paste:

Bearer <token>

## Verify Installation

1. Start backend
2. Start frontend
3. Register a user
4. Create a course
5. Upload a PDF
6. Generate Vector DB
7. Ask a question

## Demo Credentials

A demo user is created automatically on backend startup (if not already present). Use these credentials to log in for evaluation or demos:

Email: test@test.com
Password: test123