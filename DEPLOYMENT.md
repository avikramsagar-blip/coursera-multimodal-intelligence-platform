# Deployment Guide

This repository is already configured for a production deployment model based on:

- PostgreSQL for application data
- Qdrant for vector search
- S3-compatible object storage for uploads
- Google Gemini for embeddings and generation
- FastAPI backend + React/Vite frontend

No application code changes are required for deployment. Set environment variables and deploy the services below.

## Local development with Docker Compose

### 1) Prerequisites

- Docker Desktop or Docker Engine
- Docker Compose v2
- Git

### 2) Clone and run

```bash
git clone <your-repo-url>
cd coursera-multimodal-intelligence-platform
cp .env.example .env
# edit .env with real values before starting

docker compose up --build
```

This starts:

- FastAPI backend on http://localhost:8000
- PostgreSQL on localhost:5432
- Qdrant on http://localhost:6333

### 3) Verify backend health

```bash
curl http://localhost:8000/health
```

### 4) Frontend development

If you want to run the Vite frontend separately:

```bash
cd frontend
npm install
npm run dev
```

The frontend will be served on http://localhost:5173.

### 5) Frontend production build

```bash
cd frontend
npm install
npm run build
```

The production build is emitted to the `frontend/dist` directory.

## Required environment variables

Copy `.env.example` to `.env` and populate these values before deployment.

Required:

```env
APP_ENV=production
BACKEND_PORT=8000
DATABASE_URL=postgresql+psycopg2://user:password@host:5432/coursera
JWT_SECRET_KEY=change-me-to-a-long-random-secret-at-least-32-chars
GEMINI_API_KEY=your_gemini_api_key
OBJECT_STORAGE_PROVIDER=s3
OBJECT_STORAGE_BUCKET=coursera-uploads
AWS_S3_BUCKET=coursera-uploads
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_S3_PUBLIC_URL=https://your-bucket-url.example.com
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION_PREFIX=course
CORS_ORIGINS=https://your-frontend.example.com
```

Optional / platform-specific:

```env
GOOGLE_API_KEY=
AWS_ENDPOINT_URL=
OBJECT_STORAGE_PUBLIC_URL=
QDRANT_API_KEY=
CLOUDINARY_CLOUD_NAME=
CLOUDINARY_API_KEY=
CLOUDINARY_API_SECRET=
MAX_REQUEST_SIZE_BYTES=10485760
MAX_UPLOAD_SIZE_BYTES=52428800
ENABLE_SECURITY_HEADERS=true
```

## Render deployment

### Option 1: Deploy from GitHub

1. Push this repository to GitHub.
2. Log in to Render.
3. Click New + -> Web Service.
4. Connect the GitHub repository.
5. Use the root Dockerfile.
6. Set the service to use the repo root.
7. Set the health check path to `/health`.
8. Add environment variables from the `.env.example` file.
9. Set `DATABASE_URL` to your Render Postgres connection string.
10. Set `QDRANT_URL` to your Qdrant service URL.
11. Deploy.

### Render notes

- Render can host the backend container.
- Use a managed PostgreSQL instance for the application database.
- Use a managed Qdrant or self-hosted Qdrant endpoint.
- Set `CORS_ORIGINS` to your frontend domain.

## Railway deployment

### 1) Create project

1. Log in to Railway.
2. Create a new project.
3. Add a PostgreSQL service.
4. Add a Qdrant service if desired, or use a managed Qdrant service provider.
5. Deploy the backend from the GitHub repository.

### 2) Configure environment variables

Set the same variables described above. Railway will expose the PostgreSQL connection string as an environment variable such as `DATABASE_URL` automatically.

### 3) Build settings

- Build command: leave default or set to your Docker build pipeline.
- Start command: use the container command from Dockerfile or a uvicorn command.

Example:

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

## Fly.io deployment

### 1) Install Fly CLI

```bash
curl -L https://fly.io/install.sh | sh
fly auth login
```

### 2) Create app

```bash
fly launch --no-deploy --name your-app-name
```

### 3) Set secrets

```bash
fly secrets set \
  DATABASE_URL="postgresql+psycopg2://user:password@host:5432/coursera" \
  JWT_SECRET_KEY="your-secret" \
  GEMINI_API_KEY="your-gemini-key" \
  AWS_S3_BUCKET="your-bucket" \
  AWS_ACCESS_KEY_ID="your-key" \
  AWS_SECRET_ACCESS_KEY="your-secret" \
  AWS_S3_PUBLIC_URL="https://your-bucket-url.example.com" \
  QDRANT_URL="https://your-qdrant-url" \
  QDRANT_API_KEY="your-qdrant-key"
```

### 4) Deploy

```bash
fly deploy
```

### 5) Health check

```bash
curl https://your-app-name.fly.dev/health
```

## Google Cloud Run deployment

1. Build the image and push to Google Artifact Registry.
2. Deploy the container to Cloud Run.
3. Set the environment variables from `.env.example`.
4. Configure a public ingress and health check endpoint `/health`.

Example:

```bash
gcloud builds submit --tag gcr.io/<PROJECT_ID>/coursera-backend .
gcloud run deploy coursera-backend \
  --image gcr.io/<PROJECT_ID>/coursera-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

## Production notes

- ffmpeg must be installed in the runtime image for video transcription and local media processing.
- Qdrant must be reachable by the backend service.
- PostgreSQL must remain reachable by the app container.
- Object storage should be public-read or served through a public URL configuration.
- Set a proper `CORS_ORIGINS` value for the frontend domain.

## Troubleshooting

### Backend cannot connect to PostgreSQL

- Verify `DATABASE_URL` is correct.
- Confirm the database service port is reachable from the container.

### Qdrant connection fails

- Check `QDRANT_URL`.
- If using a private network, ensure the backend container can access it.

### Uploads fail

- Check `AWS_S3_BUCKET`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and `AWS_S3_PUBLIC_URL`.
- Ensure the bucket exists and is writable.

### Health endpoint returns unhealthy

- Check `/health` logs.
- Confirm DB, Qdrant, storage, and Gemini configuration are all set.

## Summary

This repository is ready for deployment after environment setup. The app can be deployed with:

- `docker compose up` for local orchestration
- GitHub + Render for managed deployment
- Railway for managed app + database deployment
- Fly.io for container deployment
- Google Cloud Run for serverless container deployment
