# AGNI-NETRA — Complete API Reference & Documentation

## 1. Authentication & System Health

- `POST /api/v1/auth/login`: Authenticate and issue JWT Bearer token.
- `POST /api/v1/auth/register`: Register new user account with role assignment.
- `GET /api/v1/auth/me`: Retrieve current authenticated profile and RBAC permissions.
- `GET /health`: Top-level application health check.
- `GET /health/db`: Database engine status (`PostgreSQL + PostGIS` vs `SQLite (TEST/DEMO FALLBACK)`).

---

## 2. Thermal Events & Tactical GIS

- `GET /api/v1/events`: Filtered and paginated thermal events (Supports `state`, `risk_level`, `classification`, `days`, `limit`, `offset`).
- `GET /api/v1/events/{id}`: Detailed intelligence dossier for a single event.
- `GET /api/v1/events/{id}/trace`: 10/11-stage scientific data lineage trail.
- `GET /api/v1/events/stats/summary`: Aggregated KPI summary metrics.

---

## 3. Industrial Facilities & Candidates

- `GET /api/v1/facilities`: List registered canonical industrial facilities.
- `GET /api/v1/facilities/{id}`: Retrieve single facility profile.
- `GET /api/v1/candidates`: List autonomously discovered candidate facilities.
- `POST /api/v1/candidates/{id}/promote`: Promote candidate to verified facility.

---

## 4. AGNI-SAT Software Satellite Digital Twin

- `GET /api/v1/satellite/info`: Live digital twin parameters (Altitude, Inclination, Ground Speed, Sensors).
- `GET /api/v1/satellite/ground-track`: GeoJSON orbital ground track prediction line.
- `GET /api/v1/satellite/footprint`: Dynamic GeoJSON sensor swath footprint polygon.
- `GET /api/v1/satellite/scenarios`: 12 standardized incident simulation templates.
- `POST /api/v1/satellite/scenarios/{id}/run`: Execute end-to-end incident simulation.
- `POST /api/v1/satellite/tasking`: Schedule mission task AOI observation.
- `GET /api/v1/satellite/tasks`: List scheduled mission tasks.
- `POST /api/v1/satellite/replay`: Replay historical Indian observation through telemetry.

---

## 5. Baselines, Anomalies & Risk

- `GET /api/v1/baselines/facilities/{facility_id}`: Empirical statistical baseline ($\mu, \sigma, \text{P90}$).
- `GET /api/v1/baselines/grid`: Grid-cell empirical thermal baselines.
- `GET /api/v1/anomalies`: Anomaly radar feed (Isolation Forest + $Z$-score surge).
- `GET /api/v1/risk/matrix`: Multi-criteria risk scoring matrix and breakdown.

---

## 6. Verification, Reports & Evidence

- `GET /api/v1/verification/queue`: Human-in-the-loop analyst review queue.
- `POST /api/v1/verification/{event_id}/verify`: Submit analyst verification decision.
- `POST /api/v1/reports/generate/{event_id}`: Generate downloadable PDF intelligence dossier.
- `GET /api/v1/reports/export/csv`: Export tabular thermal incident dataset.
- `POST /api/v1/evidence`: Attach structured evidence records (Satellite context, field photos, notes).

---

## 7. Model Registry & Data Sources

- `GET /api/v1/ml/models`: Active models and validation performance metrics.
- `GET /api/v1/admin/data-sources`: Real-time data source status and latency monitor.
- `GET /api/v1/admin/audit-logs`: Immutable system audit log trail.
