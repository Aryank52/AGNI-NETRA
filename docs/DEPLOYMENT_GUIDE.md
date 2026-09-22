# AGNI-NETRA — Production Deployment Guide

> **Document Version**: 1.0.0-release  
> **Release Target**: Production Freeze Baseline  
> **Classification**: Official Institutional Platform Documentation  
> **Security Invariant**: Never store plain-text secrets in source control or environment templates.

---

## 1. Architectural Architecture Overview

AGNI-NETRA operates on a decoupled, cloud-ready architecture:

```text
[ Browser / Tactical Workstation ]
             │
             ▼ HTTPS / WSS
[ Next.js 15 Sovereign Frontend ] (Vercel / AWS Amplify / Docker / Node 20+)
             │
             ▼ REST / JSON API (Bearer JWT)
[ FastAPI Backend Application ] (Uvicorn / Gunicorn on Port 8000)
             │
             ├──────────────────────────┬──────────────────────────┐
             ▼                          ▼                          ▼
   [ PostgreSQL 16 + PostGIS ]     [ Redis 7 ]           [ S3 / MinIO Storage ]
   (Spatial Cadastre & Events)   (Cache & Broker)     (PDF Dossiers & GeoTIFFs)
```

---

## 2. Frontend Deployment Requirements

### 2.1 System Prerequisites
- **Node.js**: `v20.x` or `v22.x` / `v24.x`
- **Package Manager**: `npm >= 10.x`
- **Output Target**: Next.js Standalone / Server-Rendered

### 2.2 Environment Variables (Build & Runtime)
| Variable | Required | Description | Example |
| :--- | :--- | :--- | :--- |
| `NEXT_PUBLIC_API_URL` | **Yes** | Public-facing URL pointing to the FastAPI `/api/v1` prefix | `https://api.agninetra.gov.in/api/v1` |
| `NEXT_PUBLIC_MAPBOX_TOKEN` | *Optional* | Optional vector style token (empty string triggers native dark sovereign fallback) | `""` |
| `NODE_ENV` | **Yes** | Application environment | `production` |

### 2.3 Build & Deployment Commands
```bash
# Navigate to frontend
cd frontend

# Clean install dependencies
npm ci

# Verify type cleanliness
npm run typecheck

# Compile production bundle
npm run build

# Start Next.js production server (Port 3000 default)
npm run start -- -p 3000
```

---

## 3. Backend Deployment Requirements

### 3.1 System Prerequisites
- **Python**: `3.12.x`
- **C-Libraries**: `libpq-dev`, `gdal-bin`, `libgeos-dev`, `libproj-dev` (for spatial geometry processing)
- **ASGI Server**: Uvicorn with Gunicorn process management

### 3.2 Environment Variables
| Variable | Required | Description | Production Guidance |
| :--- | :--- | :--- | :--- |
| `DATABASE_URL` | **Yes** | Connection string for PostgreSQL + PostGIS | `postgresql+psycopg2://user:pass@host:5432/agni_netra` |
| `SECRET_KEY` | **Yes** | 256-bit cryptographic key for JWT HS256 signatures | High-entropy secret generated via `openssl rand -hex 32` |
| `BACKEND_CORS_ORIGINS` | **Yes** | Allowed CORS origins for frontend domain | `https://console.agninetra.gov.in,http://localhost:3000` |
| `ENABLE_OPERATIONAL_DISPATCH_GATE` | **Yes** | Statutory safety gate for automated emergency dispatch | **Must remain `False`** |
| `ENABLE_AUTOMATED_MODEL_ACTIVATION` | **Yes** | Statutory safety gate for automated ML retraining | **Must remain `False`** |
| `DEFAULT_MODEL_VERSION` | **Yes** | Governed candidate model | `xgb-v3.0-real-candidate` |
| `FIRMS_MAP_KEY` | *Optional* | NASA FIRMS sensor archive map key | Configured for live VIIRS/MODIS ingestion |
| `REDIS_URL` | *Optional* | Redis task broker and cache | `redis://localhost:6379/0` |
| `S3_ENDPOINT` | *Optional* | Object storage endpoint for reports and raster tiles | `http://localhost:9000` |

### 3.3 Production Process Execution
Using Gunicorn with Uvicorn workers:
```bash
# From repository root with PYTHONPATH set
gunicorn backend.app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120 \
  --access-logfile - \
  --error-logfile -
```

---

## 4. Database Operations & PostGIS Setup

### 4.1 PostGIS Extension Initialization
Prior to running database migrations or seeding, execute on the target PostgreSQL database:
```sql
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```

### 4.2 Migration Procedure
```bash
# Run schema migrations to HEAD
alembic upgrade head
```

### 4.3 Connection Pooling Invariants
- `DB_POOL_SIZE`: 15-25 persistent connections per API worker.
- `DB_MAX_OVERFLOW`: 25-50 burst connections.
- `pool_pre_ping`: Enabled to drop stale or terminated TCP connections automatically.

---

## 5. Health Check & Observability Probes

| Endpoint | Target Method | Expected Response | Role / Probe Use |
| :--- | :--- | :--- | :--- |
| `/health` | `GET` | `HTTP 200 {"status": "ok"}` | Liveness & Readiness Probes (K8s / Load Balancer) |
| `/api/v1/analytics/command-center` | `GET` | `HTTP 200` | High-level operational telemetry health probe |
| `/api/v1/auth/login` | `POST` | `HTTP 200` | End-to-end authentication gate |

---

## 6. Rollback & Disaster Recovery Procedures

1. **Frontend Rollback**:
   - Revert DNS / deployment pointer to previous immutable build SHA.
   - Flush CDN edge cache (Cloudflare / CloudFront) for `/dashboard` and `/jarvis`.
2. **Backend Rollback**:
   - Re-deploy previous container image tag.
   - Do **NOT** run destructive down-migrations against live PostgreSQL tables without offline analyst approval.
3. **Database Restoration**:
   - Point-in-time PostgreSQL recovery (`WAL` logs) or daily snapshots (`pg_dump -Fc agni_netra > backup.dump`).
