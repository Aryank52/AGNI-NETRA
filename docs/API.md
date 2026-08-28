# AGNI-NETRA — REST API Reference (v1)

Base URL: `http://localhost:8000/api/v1`

Interactive Swagger OpenAPI: `http://localhost:8000/api/v1/docs`  
ReDoc Reference: `http://localhost:8000/api/v1/redoc`

---

## 1. Authentication & RBAC

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/auth/register` | Register new user with designated role | No |
| `POST` | `/auth/login` | OAuth2 JWT password login (returns bearer token) | No |
| `GET` | `/auth/me` | Current user profile and active permissions | Bearer Token |

---

## 2. Thermal Events & Geospatial Intelligence

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/events` | List events with filters (`state`, `risk_level`, `status`, `min_frp`) |
| `GET` | `/events/geojson` | GeoJSON FeatureCollection optimized for MapLibre GL JS |
| `GET` | `/events/{id}` | Granular event dossier with SHAP values, risk scores, and features |
| `GET` | `/events/{id}/detections` | Raw multi-sensor satellite detections constituting this event |

---

## 3. Industrial Facilities & Baselines

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/facilities` | List registered industrial facilities |
| `GET` | `/facilities/{id}` | Facility details and historical baseline profiles |
| `GET` | `/facilities/{id}/fingerprint` | Analytical thermal fingerprint profile |

---

## 4. Candidate Facility Discovery (USP)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/candidates` | List discovered candidate industrial thermal sources |
| `POST` | `/candidates/{id}/promote` | Promote candidate to official facility registry (Analyst/Admin) |

---

## 5. Anomalies, Risk & Alerts

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/anomalies` | Events exhibiting critical baseline deviations (+3σ) |
| `GET` | `/alerts` | List system alerts with status/severity filters |
| `PATCH` | `/alerts/{id}` | Acknowledge or resolve an alert |

---

## 6. Human-In-The-Loop Verification

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/verification/queue` | Events awaiting human analyst review |
| `POST` | `/verification` | Submit analyst ground-truth confirmation or label correction |

---

## 7. Analytics & PDF Reports

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/analytics/kpis` | Top-level command center KPIs |
| `GET` | `/analytics/class-distribution` | Class breakdown percentages |
| `GET` | `/analytics/risk-distribution` | Risk severity breakdown |
| `GET` | `/analytics/state-summary` | State-wise active event count and mean FRP |
| `GET` | `/reports/event/{id}/download` | Stream and download formal PDF Intelligence Dossier |

---

## 8. Machine Learning & Ingestion

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/ml/model-info` | Active model architecture, metrics, and feature list |
| `POST` | `/ml/predict` | On-demand inference with SHAP explanations |
| `POST` | `/ingestion/trigger/demo-seed` | Re-seed sample Indian industrial dataset |
| `POST` | `/ingestion/trigger/firms` | Trigger live NASA FIRMS API ingestion |
