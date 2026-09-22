# AGNI-NETRA — Production Configuration Specification

> **Classification**: Official Institutional Platform Documentation  
> **Target Release**: Production Baseline Freeze  
> **Security Policy**: Secret values MUST be provisioned via environment variables or secret vaults (AWS Secrets Manager, HashiCorp Vault, Kubernetes Secrets). Do NOT commit secrets to Git.

---

## 1. Frontend Configuration (`frontend/.env.production`)

```bash
# ==============================================================================
# AGNI-NETRA Frontend Production Configuration Template
# ==============================================================================

# Backend API Endpoint (HTTPS in production, pointing to /api/v1)
NEXT_PUBLIC_API_URL=https://api.agninetra.gov.in/api/v1

# MapLibre Vector Tile Style Token (Optional)
# Leave empty to utilize the sovereign offline dark canvas with PostGIS vector overlays
NEXT_PUBLIC_MAPBOX_TOKEN=

# Node Environment
NODE_ENV=production
```

---

## 2. Backend Configuration (`backend/.env.production`)

```bash
# ==============================================================================
# AGNI-NETRA FastAPI Backend Production Configuration Template
# ==============================================================================

# Platform Identity
PROJECT_NAME="AGNI-NETRA"
ENVIRONMENT="production"
DEBUG=False
API_V1_STR="/api/v1"

# Cryptographic Token Signing
# Generate via: openssl rand -hex 32
SECRET_KEY="<PROVISION_VIA_SECRETS_VAULT_HIGH_ENTROPY_256_BIT_HEX>"
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# PostgreSQL 16 + PostGIS Database URL
DATABASE_URL="postgresql+psycopg2://<DB_USER>:<DB_PASSWORD>@<DB_HOST>:5432/<DB_NAME>"

# Connection Pool Limits
DB_POOL_SIZE=25
DB_MAX_OVERFLOW=50
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=1800

# CORS Allowed Origins (Comma-separated list or JSON array)
BACKEND_CORS_ORIGINS="https://console.agninetra.gov.in,https://agency.agninetra.gov.in,https://public.agninetra.gov.in"

# Mandatory Operational Safety Invariants (DO NOT ALTER)
ENABLE_OPERATIONAL_DISPATCH_GATE=False
ENABLE_AUTOMATED_MODEL_ACTIVATION=False
DEFAULT_MODEL_VERSION="xgb-v3.0-real-candidate"

# Rate Limiting
RATE_LIMIT_PER_MINUTE=600
CORRELATION_ID_HEADER="X-Correlation-ID"

# Asynchronous Task Broker & Redis (Optional / Highly Recommended in Production)
REDIS_URL="redis://<REDIS_HOST>:6379/0"
CELERY_BROKER_URL="redis://<REDIS_HOST>:6379/0"
CELERY_RESULT_BACKEND="redis://<REDIS_HOST>:6379/0"

# Object Storage for PDF Dossiers & Spatial GeoTIFFs
S3_ENDPOINT="https://s3.<REGION>.amazonaws.com"
S3_ACCESS_KEY="<PROVISION_VIA_SECRETS_VAULT>"
S3_SECRET_KEY="<PROVISION_VIA_SECRETS_VAULT>"
S3_USE_SSL=True
S3_BUCKET_NAME="agni-netra-production"
S3_BUCKET_IMAGERY="agni-netra-imagery-production"
S3_BUCKET_REPORTS="agni-netra-reports-production"
```

---

## 3. Reverse Proxy & Web Server Rules (Nginx / Cloudflare)

### 3.1 Security Headers
The following security headers must be enforced at the reverse proxy layer:
- `Strict-Transport-Security: max-age=63072000; includeSubDomains; preload`
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: SAMEORIGIN`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Content-Security-Policy`: Must permit WebGL context, `blob:` URLs for PDF downloads, and `data:` URIs for raster tiles.

### 3.2 Proxy Pass & Caching Invariants
- Route `/api/v1/*` must pass with `proxy_set_header Host $host; proxy_set_header X-Real-IP $remote_addr;` and `proxy_buffering off;`.
- Route `/reports/*/download` must stream without payload truncation (`proxy_read_timeout 120s;`).
- API routes must NOT be cached at the CDN layer to guarantee real-time thermal telemetry freshness.
