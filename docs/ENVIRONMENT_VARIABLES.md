# AGNI-NETRA — Environment Variables Specification

All configuration and secrets are managed via standard environment variables and read cleanly via Pydantic `BaseSettings`.

| Variable Name | Required | Default Value | Description / Purpose |
|---|---|---|---|
| **`PROJECT_NAME`** | No | `AGNI-NETRA` | Application title |
| **`ENVIRONMENT`** | No | `production` | Environment mode (`development`, `staging`, `production`) |
| **`SECRET_KEY`** | **Yes** | None | Cryptographic secret for JWT token generation |
| **`DATABASE_URL`** | **Yes** | `postgresql://postgres:postgres@localhost:5432/agninetra` | PostgreSQL + PostGIS connection string |
| **`REDIS_URL`** | No | `redis://localhost:6379/0` | Redis caching and Celery broker connection |
| **`FIRMS_MAP_KEY`** | No | `""` | NASA FIRMS MAP Key for real-time active fire API |
| **`COPERNICUS_CLIENT_ID`** | No | `""` | ESA Copernicus Data Space OAuth Client ID |
| **`COPERNICUS_CLIENT_SECRET`** | No | `""` | ESA Copernicus Data Space OAuth Client Secret |
| **`MOSDAC_USERNAME`** | No | `""` | ISRO MOSDAC Data Portal Username |
| **`MOSDAC_PASSWORD`** | No | `""` | ISRO MOSDAC Data Portal Password |
| **`EMAIL_ENABLED`** | No | `false` | Master toggle for email alert dispatch |
| **`SMTP_HOST`** | No | `smtp.gmail.com` | SMTP relay server hostname |
| **`SMTP_PORT`** | No | `587` | SMTP port (STARTTLS) |
| **`SMTP_USERNAME`** | No | `""` | SMTP authentication user |
| **`SMTP_PASSWORD`** | No | `""` | SMTP application-specific password |
| **`ALERT_FROM_EMAIL`** | No | `alerts@agninetra.gov.in`| Sender header for alert emails |
| **`SMS_ENABLED`** | No | `false` | Master toggle for SMS alert gateway |
| **`SMS_PROVIDER`** | No | `CONSOLE` | SMS gateway provider (`CONSOLE`, `TWILIO`, `TEXTLOCAL`) |
| **`SMS_API_KEY`** | No | `""` | Gateway provider API authentication key |
| **`S3_ENDPOINT`** | No | `http://localhost:9000` | S3-compatible MinIO object storage endpoint |
| **`S3_ACCESS_KEY`** | No | `minioadmin` | MinIO access key |
| **`S3_SECRET_KEY`** | No | `minioadmin` | MinIO secret key |
| **`S3_BUCKET_NAME`** | No | `agni-netra-artifacts` | Object storage bucket for satellite imagery and PDF dossiers |
