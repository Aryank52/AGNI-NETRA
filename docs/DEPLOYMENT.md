# AGNI-NETRA — Deployment & Operations Guide

## 1. Quick Local Startup (Single Command)

### Option A: Local Development Server

```bash
# 1. Activate Python Virtual Environment
.\venv\Scripts\activate

# 2. Run Database Seeding & Acceptance Tests
python database\seed_data.py
python tests\run_all_tests.py

# 3. Start FastAPI Backend (Port 8000)
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload

# 4. In a separate terminal, start Next.js Frontend (Port 3000)
cd frontend
npm run dev
```

Visit `http://localhost:3000` to open the AGNI-NETRA Command Center.

---

## 2. Docker Compose Production Deployment

```bash
# From workspace root
docker-compose -f deployment/docker-compose.yml up --build -d
```

### Services Deployed:
- `agni_netra_postgres` (Port 5432) — PostgreSQL 16 + PostGIS 3.4
- `agni_netra_redis` (Port 6379) — Redis 7 In-Memory Broker & Cache
- `agni_netra_minio` (Port 9000/9001) — S3 Object Storage for Reports
- `agni_netra_backend` (Port 8000) — FastAPI REST Server
- `agni_netra_worker` — Celery Asynchronous Job Processor
- `agni_netra_frontend` (Port 3000) — Next.js 15 Web Application
