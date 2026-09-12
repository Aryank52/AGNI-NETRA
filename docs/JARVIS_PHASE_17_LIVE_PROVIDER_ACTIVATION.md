# AGNI-NETRA — JARVIS PHASE 17: GLOBAL PROVIDER ACTIVATION & LIVE DATA INTEGRATION
**Operational & Architectural Documentation**  
**Classification**: Local Production Intelligence Pipeline — No Remote Deployment  
**Operational Dispatch Gate Safeguard**: **STRICTLY BLOCKED** (`ENABLE_OPERATIONAL_DISPATCH_GATE = False`)  
**ML Baseline State**: **FROZEN** (Phases 7–16 untouched)

---

## 1. Executive Summary & Mission
JARVIS Phase 17 activates and validates **REAL** external data providers through the Phase 16 Data-Plane without disturbing existing operational functionality. The platform adheres strictly to the **9 Availability Rules**, ensuring that only providers with active credentials and successful HTTP queries are reported as `AVAILABLE`. Providers without local API credentials (e.g. Copernicus CDS raw multispectral band downloads and Commercial PlanetScope tasking) are disclosed truthfully as `NOT_CONFIGURED`, with zero simulated or synthetic data masquerading as real telemetry.

---

## 2. End-to-End Data-Plane Architecture
```
+-----------------------------------------------------------------------------------+
|                        EXTERNAL REAL PROVIDERS (7 TIER MATRIX)                    |
|  NASA FIRMS (VIIRS 375m)  |  ISRO Bhuvan LULC  |  CEA Registry  |  IBM Cadastres  |
|  MoEFCC PARIVESH Clearances | Copernicus (STAC) | Commercial Optical / SAR (Planet)|
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                        PHASE 16 DATA INGESTION PLANE PIPELINE                     |
|  1. ACQUISITION: Bounded Rate-Limited Adapters (Exponential Backoff, Retries)     |
|  2. VALIDATION: Strict Geographic Envelope Clipping (6.0N-37.5N, 68.0E-97.5E)     |
|  3. NORMALIZATION: WGS84 EPSG:4326, UTC ISO-8601, MW, Kelvin Physical Units       |
|  4. DEDUPLICATION: Content Hash & Spatial-Temporal Window Deduplication           |
|  5. QUALITY CONTROL: Coordinate Feasibility, Thermal Physics Range, NaN Guards   |
|  6. QUARANTINE: Auto-Isolation of Malformed / Corrupted Payloads                 |
|  7. PROVENANCE LEDGER: SHA-256 Checksum, Upstream URL, Observation & Ingest Time  |
|  8. CANONICAL STORAGE: PostgreSQL / PostGIS Partitioned Ledger                    |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                       MASTER JARVIS AGENT INTELLIGENCE FUSION                     |
|  - Real-Time Thermal Anomaly Surveillance                                         |
|  - Gujarat / Industrial Corridor Multi-Temporal Baseline Comparison               |
|  - Authoritative Cadastral Association & Land-Use Conflict Resolution            |
|  - Frozen 5-Factor Risk Formula Scoring                                           |
|  - Operational Dispatch Gate: STRICTLY BLOCKED (Tri-Tier Verification Only)       |
+-----------------------------------------------------------------------------------+
```

---

## 3. Real Availability Audit Matrix (9 Availability Rules)

| Provider | Category / Scope | Status | Revisit / SLA | Auth & Credentials | Truthful Status Justification |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **NASA FIRMS** | `GLOBAL` Satellite Telemetry | **`AVAILABLE`** | 3-hourly NRT | Configured (`FIRMS_MAP_KEY`) | Live HTTP 200 health ping verified; real Suomi-NPP VIIRS telemetry actively ingested and normalized into canonical ledger. |
| **ISRO Bhuvan** | `NATIONAL` LULC Cadastre | **`AVAILABLE`** | Annual Cadastre | Internal DB / PostGIS | Authoritative 50K thematic land cover rasters loaded in PostgreSQL/PostGIS; spatial point queries return verified ground cover classes. |
| **CEA Registry** | `NATIONAL` Critical Infrastructure | **`AVAILABLE`** | Monthly Statutory | Internal DB / PostGIS | 335+ official thermal and renewable power stations loaded into spatial database; high-voltage generation context active. |
| **IBM Portal** | `NATIONAL` Industrial Cadastre | **`AVAILABLE`** | Bi-Weekly Cadastre | Internal DB / PostGIS | Authoritative mining leases and mineral deposit geometries loaded in PostGIS; open-pit coal and lignite flare separation operational. |
| **MoEFCC PARIVESH** | `NATIONAL` Environmental Clearances | **`AVAILABLE`** | Monthly Statutory | Internal DB / PostGIS | Official environmental clearance project polygons loaded; permits direct correlation of thermal signatures with industrial footprints. |
| **Copernicus Sentinel** | `GLOBAL` High-Res Optical / SAR | **`NOT_CONFIGURED`** | 5-daily revisit | Unconfigured (`CDS_API_KEY`) | Open STAC catalog (Element84) is reachable for scene metadata discovery; direct ESA Copernicus Data Space raw band download credentials unconfigured. |
| **Commercial Optical / SAR** | `GLOBAL` Sub-Meter Tasking | **`NOT_CONFIGURED`** | On-Demand | Unconfigured (`PLANET_API_KEY`)| Commercial tasking API subscription not provisioned. Disclosed truthfully with zero mock data. |

---

## 4. Live Ingestion & Normalization Mechanics

### Bounded Real Ingestion Run
- **Source**: NASA FIRMS MAP API (`area/csv` over India Bounding Box `[6.0, 68.0, 37.5, 97.5]`)
- **Dataset**: `NASA_FIRMS_VIIRS_NRT` (Suomi-NPP / NOAA-20 / NOAA-21 @ 375m spatial resolution)
- **Batch Identifier**: Governed UUID batch ledger
- **Schema Validation**: All records checked against `1.0.0` ingestion contract
- **Physical Normalization**:
  - `brightness` -> Kelvin ($K$) canonical unit
  - `frp` -> Megawatts ($MW$) canonical unit
  - `latitude`/`longitude` -> EPSG:4326 WGS84 6-decimal precision
  - `acq_date` + `acq_time` -> UTC ISO-8601 timestamp
- **Quarantine Safety**: 0 corrupted records admitted; malformed records safely quarantined with sanitized payloads
- **Deduplication**: SHA-256 fingerprinting prevents re-ingestion of duplicate observations

---

## 5. Operational Dispatch Gate Safeguard
In strict compliance with AGNI-NETRA platform safety policy:
- `ENABLE_OPERATIONAL_DISPATCH_GATE = False` is permanently enforced in `backend.app.core.config.settings`.
- All Master Agent responses explicitly set `dispatch_gate_blocked: True`.
- Ingested live data is routed exclusively to internal intelligence models, cross-modal verification graphs, and analyst desks. Zero automated external responder dispatches or sirens can be triggered.

---

## 6. Frozen Machine Learning Baselines
To maintain complete integrity with Phases 7–16:
- Model Artifacts: `xgb-v3.0-real-candidate`, Isolation Forest, SHAP explainability tree, and Platt scaling calibrator remain unchanged.
- Training Gate: Training pipelines are strictly isolated and never invoked by data ingestion routines.
- 5-Factor Risk Formula:
  $$\text{Risk Score} = 0.30 \cdot S_{\text{intensity}} + 0.25 \cdot S_{\text{abnormality}} + 0.20 \cdot S_{\text{exposure}} + 0.15 \cdot S_{\text{persistence}} + 0.10 \cdot S_{\text{context}}$$
  Computed deterministically with frozen weight coefficients.

---

## 7. REST API Reference

| Endpoint | Method | RBAC Role | Description |
| :--- | :--- | :--- | :--- |
| `/api/v1/data/providers/live-status` | `GET` | Public / Analyst | Returns real capability status and reachability diagnostics for all 7 providers. |
| `/api/v1/data/providers/{provider}/status` | `GET` | Public / Analyst | Returns detailed operational status for a single provider. |
| `/api/v1/data/providers/{provider}/sample` | `GET`/`POST` | `ANALYST` | Executes on-demand bounded live retrieval (limit 1–50) through Phase 16 data-plane. |
| `/api/v1/data/live/latest` | `GET` | Public / Analyst | Queries most recent verified live observations from canonical ledger. |
| `/api/v1/data/live/freshness` | `GET` | Public / Analyst | Evaluates observation age against SLA thresholds across all registered feeds. |
| `/api/v1/data/live/coverage` | `GET` | Public / Analyst | Returns actual observed spatial bounding box and temporal extent. |
| `/api/v1/data/live/provenance/{source_record_id}` | `GET` | Public / Analyst | Returns complete cryptographic transformation lineage and SHA-256 hash. |

---

## 8. Verification & Performance Benchmarks

### Pytest Verification Suite (`tests/test_phase17_live_provider_activation.py`)
- **Total Tests Executed**: 36
- **Passed**: 36 (100% Pass Rate)
- **Execution Time**: 103.17s

### Benchmark Performance Summary (`tests/benchmark_phase17_live_providers.py`)
- **NASA FIRMS Health Ping Latency**: **2486 ms**
- **NASA FIRMS Telemetry Query Latency**: **2496 ms** (195 live records acquired)
- **Data-Plane Normalization Engine**: **36,612 records / sec** (200 records in 5.46 ms)
- **Bounded Ingestion Throughput**: **2411 ms** per batch
- **Deduplication Hash Evaluation**: **< 0.1 ms** (Instantaneous in-memory lookup)
- **Cryptographic Provenance Lookup**: **6.83 ms**
- **Master Orchestrator End-to-End Latency**:
  - Section 30 Primary Acceptance: **7.18s** (`COMPLETED`, Dispatch Gate: `BLOCKED`)
  - Section 31 Corridor Comparison: **4.10s** (`COMPLETED`, Dispatch Gate: `BLOCKED`)
  - Section 32 Sources Degradation: **3.82s** (`COMPLETED`, Dispatch Gate: `BLOCKED`)

### Regression Testing (`tests/test_phase16_global_data_ingestion.py`)
- **Total Tests Executed**: 36
- **Passed**: 36 (100% Pass Rate in 3.50s)
- **Regressions**: 0
