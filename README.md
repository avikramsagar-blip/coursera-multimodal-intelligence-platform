# Coursera Multimodal Intelligence Platform

A full-stack learning platform with a FastAPI backend, React + Vite frontend, PostgreSQL persistence, and a Qdrant vector store for course material retrieval. The backend also supports uploads, media processing, and AI-assisted course chat using Gemini embeddings and generation.

## Stack

- Backend: Python 3.12, FastAPI, SQLAlchemy, PostgreSQL/SQLite, JWT auth
- Frontend: React 19, Vite, MUI, Bootstrap, React Router, React Hook Form, Yup, Axios, React Markdown
- AI/RAG: Gemini embeddings via `langchain-google-genai`, Qdrant vector search, LangChain text splitting
- Media: ffmpeg, Whisper, Cloudinary/Local upload storage, yt-dlp

## Prerequisites

- Python 3.10+ (project is tested with Python 3.12 in Docker)
- Node.js 18+ and npm
- Git
- Docker + Docker Compose for the containerized workflow
- ffmpeg on PATH for transcription and media processing

## Repository layout

- `backend/` — FastAPI API, SQLAlchemy models, RAG, vector search, media utilities
- `frontend/` — Vite React app
- `docker-compose.yml` — PostgreSQL + Qdrant + backend container
- `Dockerfile` — single-image production build for the backend and bundled frontend
- `.env.example` — environment variables used by the backend
- `frontend/.env` — frontend config; defaults to `VITE_API_URL=http://localhost:8000`

## Environment variables

Copy `.env.example` to `.env` in the repo root and fill in the required values before starting the app.

```env
APP_ENV=development
BACKEND_PORT=8000
DATABASE_URL=postgresql://coursera:coursera@localhost:5432/coursera
JWT_SECRET_KEY=change-me-to-a-long-random-secret-at-least-32-chars
SECRET_KEY=${JWT_SECRET_KEY}
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

GEMINI_API_KEY=your_gemini_key
GOOGLE_API_KEY=your_gemini_key

OBJECT_STORAGE_PROVIDER=local
LOCAL_UPLOAD_DIR=backend/uploads
CLOUDINARY_CLOUD_NAME=
CLOUDINARY_API_KEY=
CLOUDINARY_API_SECRET=

QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=
QDRANT_COLLECTION_PREFIX=course

CORS_ORIGINS=http://localhost:5173,http://localhost:3000
MAX_REQUEST_SIZE_BYTES=10485760
MAX_UPLOAD_SIZE_BYTES=52428800
```

Notes:
- The backend uses Qdrant, not FAISS, for course vector indexes.
- `DATABASE_URL` defaults to a SQLite file only for simple local development; PostgreSQL is the primary production configuration.
- `GEMINI_API_KEY` is required for embeddings and RAG indexing. If it is missing, embedding functionality will not work correctly.
- The frontend reads its API URL from `frontend/.env` using `VITE_API_URL`; if this is unset, it will call the same origin instead of the backend.

## Install dependencies

### Backend

```bash
python -m venv .venv
# Windows PowerShell
# .\.venv\Scripts\Activate.ps1
# macOS/Linux
# source .venv/bin/activate

pip install -r backend/requirements.txt
```

### Frontend

```bash
cd frontend
npm install
```

If you want the frontend to call a local API server instead of the same origin, create or edit `frontend/.env`:

```env
VITE_API_URL=http://localhost:8000
```

## Run locally

### Start the backend

From the repo root:

```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --reload --port 8000
```

The app exposes the API and documentation at:

- http://localhost:8000/docs
- http://localhost:8000/health

### Start the frontend

From the repo root:

```bash
npm run dev
```

or directly in the frontend folder:

```bash
cd frontend
npm run dev -- --host 0.0.0.0
```

The Vite dev server is typically available at:

- http://localhost:5173

## Production frontend build

```bash
cd frontend
npm run build
```

The produced `dist/` bundle is copied into the Docker image and served by the FastAPI app. In production the backend is the app entrypoint on port 8000.

## Docker and deployment

### Local containers

```bash
docker compose up --build
```

This repo's compose setup runs:

- PostgreSQL on http://localhost:5432
- Qdrant on http://localhost:6333
- Qdrant gRPC on http://localhost:6334
- Backend on http://localhost:8000

The backend service is defined in `docker-compose.yml` and uses:

- `dockerfile: Dockerfile`
- `ports: ["8000:8000"]`
- `depends_on: [postgres, qdrant]`
- `env_file: .env`
- health checks and volume mounts for PostgreSQL/Qdrant persistence

### Single-container production build

```bash
docker build -t coursera-platform .
docker run --rm -p 8000:8000 --env-file .env coursera-platform
```

The Dockerfile builds the React app, copies the frontend bundle into `frontend_dist`, installs the backend requirements, and starts uvicorn with:

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --proxy-headers
```

## Day-to-day usage

1. Register an account or log in via the frontend.
2. Create a course from the dashboard.
3. Upload PDFs or other media.
4. Generate the vector index for that course.
5. Ask questions in the course chat workflow to trigger retrieval-augmented answers.

## Demo login

A demo user is created automatically on backend startup if it does not yet exist.

- Email: `test@test.com`
- Password: `test123`

## Troubleshooting

- If the backend says Qdrant is unavailable, confirm `QDRANT_URL` and that `docker compose up` has started the `qdrant` service.
- If the frontend API calls fail, ensure `frontend/.env` sets `VITE_API_URL=http://localhost:8000`.
- If startup logs report a missing Gemini key, add `GEMINI_API_KEY` before generating vector stores.
- If database tables are missing, confirm the backend booted successfully and the app created them on startup.

## Notes

- This repo does not use a separate frontend container in the Docker Compose setup; the FastAPI backend serves the production frontend bundle on the same port (8000).
- The local Vite frontend remains the normal development path for front-end work.
- The project uses Qdrant rather than FAISS for its vector database implementation.
