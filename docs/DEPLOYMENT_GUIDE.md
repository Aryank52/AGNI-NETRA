# AGNI-NETRA — Production Deployment Guide

## 1. Local Development Quickstart

```bash
# 1. Start backend server
.\venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload

# 2. Start frontend dev server
cd frontend
npm.cmd run dev
```

---

## 2. Docker Compose Production Deployment

The repository includes a production multi-container orchestration configuration (`deployment/docker-compose.yml`):

```bash
# Build and launch all services in detached mode
docker-compose -f deployment/docker-compose.yml up --build -d
```

### Services Launched:
- `db`: PostgreSQL 16 with PostGIS 3.4 extensions enabled on Port 5432
- `redis`: Redis 7 in-memory cache and task broker on Port 6379
- `minio`: S3-compatible object storage on Port 9000 (Console: 9001)
- `backend`: FastAPI API server with Gunicorn Uvicorn workers on Port 8000
- `worker`: Celery asynchronous processing worker for background satellite ingestion
- `frontend`: Next.js 15 App Router optimized production build on Port 3000

---

## 3. Production Cloud Architecture

- **Frontend**: Next.js App Router deployed on Vercel / Cloudflare Pages / AWS ECS.
- **Backend**: FastAPI containerized service on AWS ECS / Google Cloud Run / Azure Container Apps.
- **Database**: Managed PostgreSQL with PostGIS extension (e.g. AWS RDS PostgreSQL with PostGIS).
- **Caching & Broker**: Managed Redis (e.g. AWS ElastiCache / Redis Enterprise).
- **Object Storage**: AWS S3 / Cloudflare R2 for multi-spectral imagery tiles and PDF dossiers.
