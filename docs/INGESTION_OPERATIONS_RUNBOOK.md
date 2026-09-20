# AGNI-NETRA — External Data Ingestion Operations Runbook

**Document ID:** RUNBOOK-INGEST-001  
**Classification:** Sovereign Operations / Unclassified  
**Component:** Real Ingestion Plane (VIIRS / MODIS / NASA FIRMS)  
**System Version:** WP3 Hardened Baseline  
**Target Environment:** Production / Sovereign Air-Gapped / Staging  

---

## 1. Architectural Overview & Invariants

The AGNI-NETRA external data ingestion plane connects real-world satellite-derived thermal observation feeds into the proactive intelligence pipeline and JARVIS autonomous observer.

```
+-----------------------------------------------------------------------------------+
|                            EXTERNAL DATA PROVIDER                                 |
|                       NASA FIRMS (VIIRS S-NPP / NOAA-20 / NOAA-21 / MODIS)         |
+-----------------------------------------------------------------------------------+
                                         │
                                         │ HTTPS / CSV Stream
                                         ▼
+-----------------------------------------------------------------------------------+
|                           INGESTION ADAPTER LAYER                                 |
|   • FirmsAdapter: Bounded Retry (Max 3), Exponential Backoff + Jitter            |
|   • Strict Secret Scrubbing (Zero FIRMS_MAP_KEY leakage in logs/traces)          |
|   • ProviderHealthState Tracker: HEALTHY | DEGRADED | STALE | FAILED | UNAVAILABLE|
+-----------------------------------------------------------------------------------+
                                         │ Raw Dicts
                                         ▼
+-----------------------------------------------------------------------------------+
|                        HARDENED INGESTION SERVICE                                 |
|   1. Structural & Spatial Validation (WGS-84 bounding, coordinate ranges)         |
|   2. SHA-256 Idempotency Engine (Chronological first_seen/last_seen tracking)     |
|   3. Dead-Letter Quarantine (Zero silent loss for malformed/corrupted records)    |
|   4. Durable Watermark Checkpoints (Per-provider cursor tracking in PostgreSQL)   |
|   5. Batch Failure Isolation (One bad record does not fail the batch)             |
+-----------------------------------------------------------------------------------+
                                         │ Valid, Deduplicated Detections
                                         ▼
+-----------------------------------------------------------------------------------+
|                        PROACTIVE INTELLIGENCE CORE (WP1)                          |
|   • 18-Feature Context Fusion (Spatial joins against 35,570 active facilities)    |
|   • XGBoost v3.0 ML Inference + Platt Scaling + TreeExplainer SHAP                |
|   • Anomaly & Historical Correlation Engines (8.22M Detection Baselines)          |
|   • Risk, Priority & Evidence Graph Persistence                                   |
+-----------------------------------------------------------------------------------+
                                         │ Significant State Changes
                                         ▼
+-----------------------------------------------------------------------------------+
|                        JARVIS AUTONOMOUS OBSERVER                                 |
|   • Single Master Agent (Zero multi-agent swarms)                                 |
|   • Autonomous Investigation of Critical Priority / High Anomaly Events           |
+-----------------------------------------------------------------------------------+
```

### Sovereign Invariants & Non-Negotiable Constraints
1. **Zero Synthetic Substitution:** Simulation generators (AGNI-SAT / digital twins) must NEVER be routed to real ingestion tables or mixed into sovereign thermal alerts.
2. **Permanent Safety Gates:** 
   - `ENABLE_OPERATIONAL_DISPATCH_GATE = False` (Mandatory human operator approval before field dispatch).
   - `ENABLE_AUTOMATED_MODEL_ACTIVATION = False` (Mandatory ML governance sign-off before candidate activation).
3. **Database Permanence:** Never truncate, reset, or drop PostgreSQL detection tables. Historical detections (8.22M records) are immutable.
4. **Secret Redaction:** API keys (`FIRMS_MAP_KEY`) must never appear in raw URLs, exception messages, quarantine tables, logs, or metrics.

---

## 2. Operating Modes & Ingestion Workflows

### Mode A: Continuous Daemon Loop (Production Recommended)
Runs as an independent long-running process that periodically pulls incremental updates based on checkpoints.

```powershell
# In production / staging shell
cd e:\PROJECTS\AGNI-NETRA
.\venv\Scripts\Activate.ps1

# Run continuous ingestion daemon (polls every 300s by default)
python -m data_pipeline.firms_ingest_loop

# Run single-cycle execution (ideal for cron or test triggers)
python -m data_pipeline.firms_ingest_loop --once
```

**Graceful Shutdown:** Send `SIGTERM` or `Ctrl+C` (`SIGINT`). The loop finishes the active batch commit, writes the watermark checkpoint, and shuts down cleanly within 5 seconds.

### Mode B: Celery Maintenance Task (Distributed Worker)
Scheduled via Celery Beat or triggered asynchronously via worker pools:

```python
from backend.app.tasks.maintenance_tasks import firms_ingestion_job

# Enqueue background ingestion task
task = firms_ingestion_job.delay(country="IND", sensor="VIIRS_SNPP")
print(f"Enqueued task ID: {task.id}")
```

### Mode C: Operator Sync REST API (Interactive Control)
Triggered directly via authenticated operator API:

```bash
# Ingest raw satellite observations directly via hardened pipeline
curl -X POST "http://127.0.0.1:8000/api/v1/ingestion/hardened-sync?provider=NASA_FIRMS&sensor=VIIRS_SNPP" \
     -H "Content-Type: application/json" \
     -d '[
       {
         "latitude": 23.456,
         "longitude": 85.123,
         "brightness": 345.2,
         "confidence": "nominal",
         "acq_date": "2026-09-19",
         "acq_time": "0215",
         "frp": 18.4,
         "daynight": "D"
       }
     ]'
```

---

## 3. Health Monitoring & Status Diagnostics

### Health Status Endpoint
Query provider status, latency, error counts, and availability:

```bash
curl -X GET "http://127.0.0.1:8000/api/v1/ingestion/provider-health"
```

**Sample Response:**
```json
{
  "provider": "NASA_FIRMS",
  "status": "HEALTHY",
  "consecutive_failures": 0,
  "total_requests": 142,
  "total_failures": 1,
  "last_successful_fetch": "2026-09-19T02:00:15Z",
  "last_error": null,
  "circuit_breaker_active": false
}
```

### Provider State Transitions
| State | Trigger Condition | System Action |
|---|---|---|
| `HEALTHY` | Consecutive failures = 0, recent fetch < 6h | Normal operation, full polling rate |
| `DEGRADED` | 1-2 transient network failures / rate-limits (HTTP 429) | Exponential backoff with jitter applied |
| `STALE` | No successful ingestion for > 12 hours | Operator warning emitted, heartbeat alert |
| `FAILED` | >= 3 consecutive request failures | Circuit breaker opened, sleep interval escalated |
| `UNAVAILABLE` | Missing credentials, DNS failure, persistent 503 | Fallback mode, human intervention alert |

---

## 4. Watermark & Checkpoint Administration

The `ingestion_checkpoints` table maintains durable watermarks preventing duplicate work upon crash or restart.

### Inspect Watermarks
```bash
curl -X GET "http://127.0.0.1:8000/api/v1/ingestion/checkpoints"
```

### Direct Database Query
```sql
SELECT provider, sensor, watermark_timestamp, records_processed, last_successful_batch
FROM ingestion_checkpoints
ORDER BY last_successful_batch DESC;
```

### Watermark Reset Procedures

#### Procedure 4.1: Historical Backfill Rewind
If satellite data was missing due to an upstream outage, rewind the watermark:
```sql
-- Rewind VIIRS SNPP watermark to 3 days ago for India
UPDATE ingestion_checkpoints
SET watermark_timestamp = NOW() - INTERVAL '3 days',
    status = 'PENDING_REPLAY'
WHERE provider = 'NASA_FIRMS' AND sensor = 'VIIRS_SNPP';
```
Then trigger `python -m data_pipeline.firms_ingest_loop --once`. The idempotency engine will skip already-persisted records and ingest only newly available detections.

#### Procedure 4.2: Fast-Forward Over Corrupted Provider Window
If the provider returns corrupt, unparseable streams for an isolated window:
```sql
UPDATE ingestion_checkpoints
SET watermark_timestamp = NOW()
WHERE provider = 'NASA_FIRMS' AND sensor = 'MODIS';
```

---

## 5. Dead-Letter Queue (Quarantine) Administration

When records fail structural validation (e.g. coordinates outside valid coordinate space, unparseable dates, negative FRP), they are **never dropped silently**. They are diverted to `ingestion_quarantine`.

### View Quarantined Records
```bash
curl -X GET "http://127.0.0.1:8000/api/v1/ingestion/quarantine?resolved=false&limit=50"
```

### Failure Categories
1. `MALFORMED_STRUCTURE`: Missing mandatory fields (`latitude`, `longitude`, `acq_date`).
2. `INVALID_COORDINATES`: Latitude < -90 or > 90, Longitude < -180 or > 180.
3. `TEMPORAL_ANACHRONISM`: Acquisition timestamp in the future (> 24h ahead of UTC).
4. `PAYLOAD_TRUNCATION`: Truncated CSV lines or missing delimiters.
5. `UPSTREAM_SCHEMA_DRIFT`: Unknown sensor header formatting.

### Replay & Remediation

#### Replay API
Once upstream schemas are patched or data is corrected, invoke the replay API:
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/ingestion/replay" \
     -H "Content-Type: application/json" \
     -d '{
       "quarantine_ids": ["c3a1e948-18e9-4e5a-9426-1b033d59e89a"],
       "force_revalidation": true
     }'
```

---

## 6. Secret Redaction & Key Rotation

### Redaction Guarantees
All NASA FIRMS URLs contain `FIRMS_MAP_KEY` in their path:
`https://firms.modaps.eosdis.nasa.gov/api/area/csv/<MAP_KEY>/VIIRS_SNPP_NRT/...`

The redaction engine automatically converts all URLs and log messages to:
`https://firms.modaps.eosdis.nasa.gov/api/area/csv/[REDACTED_MAP_KEY]/VIIRS_SNPP_NRT/...`

### Key Rotation Procedure
1. Obtain the new 32-character FIRMS MAP Key from NASA Earthdata.
2. Update `.env`:
   ```bash
   FIRMS_MAP_KEY=new_32_character_hex_string
   ```
3. Restart ingestion daemon:
   ```powershell
   Get-Process -Name python | Where-Object { $_.CommandLine -like "*firms_ingest_loop*" } | Stop-Process
   python -m data_pipeline.firms_ingest_loop
   ```
4. Verify provider health transitions to `HEALTHY`:
   ```bash
   curl -s http://127.0.0.1:8000/api/v1/ingestion/provider-health | jq .status
   ```

---

## 7. Incident Response Playbooks

### Playbook 7.1: NASA FIRMS 429 Rate Limiting
- **Symptom:** Logs report `NASA FIRMS HTTP 429 Rate Limited. Backing off...`, provider health transitions to `DEGRADED`.
- **Root Cause:** Multiple workers or external tools sharing the same `FIRMS_MAP_KEY`.
- **Mitigation:**
  1. Inspect active processes: verify only one `firms_ingest_loop` daemon is running.
  2. The adapter will automatically apply exponential backoff (e.g. 1.5s, 4.5s, 13.5s + jitter).
  3. Increase default polling interval in `.env`: `FIRMS_POLL_INTERVAL_SECONDS=600`.

### Playbook 7.2: Provider Outage (HTTP 502 / 503)
- **Symptom:** Provider status switches to `FAILED`, circuit breaker active.
- **Mitigation:**
  1. Check NASA Earthdata status dashboard.
  2. AGNI-NETRA will automatically maintain state without loss. Checkpoints preserve the last valid acquisition time.
  3. Once NASA restores service, the daemon will automatically resume and ingest all observations accumulated since the checkpoint.

### Playbook 7.3: Database Pressure / Lock Timeout
- **Symptom:** `batch_failures > 0` in ingestion metrics; PostgreSQL logs show transaction timeouts.
- **Mitigation:**
  1. The hardened service commits valid batches in chunks of 50 to prevent long-held table locks.
  2. Inspect running long-lived queries:
     ```sql
     SELECT pid, now() - query_start AS duration, query 
     FROM pg_stat_activity 
     WHERE state = 'active' AND now() - query_start > interval '30 seconds';
     ```
  3. Cancel offending reporting or heavy GIS queries if necessary.
