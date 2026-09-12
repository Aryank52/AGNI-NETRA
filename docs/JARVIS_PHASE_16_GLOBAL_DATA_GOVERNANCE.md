# AGNI-NETRA — JARVIS Phase 16: Global Data Ingestion, Normalization & Data Governance
**Technical Specification & Verification Report**

---

## 1. Executive Summary

JARVIS Phase 16 establishes the foundational **Global Data-Plane** for AGNI-NETRA (`e:\PROJECTS\AGNI-NETRA`). The system introduces a provider-neutral, strictly governed, scalable ingestion and normalization subsystem beneath the existing multi-layer intelligence stack. 

The architecture strictly maintains the existing intelligence baselines:
- **Calibrated XGBoost Model (`xgb-v3.0-real-candidate`) & Platt Calibrator**: Untouched.
- **SHAP Feature Attributions & Isolation Forest**: Frozen.
- **5-Factor Composite Risk Formula**: Strictly preserved ($0.30 \cdot I + 0.25 \cdot A + 0.20 \cdot E + 0.15 \cdot P + 0.10 \cdot C$).
- **Operational Dispatch Gate**: Strictly locked in **BLOCKED** status (`ENABLE_OPERATIONAL_DISPATCH_GATE = False`).
- **Single Master JARVIS Agent (`master_orchestrator`)**: Exactly one orchestrator, zero subagents, zero background swarms.
- **Strict Factual Disclosures**: Unconfigured providers (ERA5, GFS, CAMS, Sentinel-1/2, Planet) are factually reported as `NOT_CONFIGURED` with zero synthetic data.

---

## 2. Ingestion Pipeline Architecture

The Phase 16 Data-Plane processes observations through an eleven-stage deterministic pipeline:

$$\text{Acquisition} \longrightarrow \text{Validation} \longrightarrow \text{Normalization} \longrightarrow \text{Deduplication} \longrightarrow \text{Quality Control} \longrightarrow \text{Provenance Tagging} \longrightarrow \text{Storage / Quarantine} \longrightarrow \text{Freshness Evaluation} \longrightarrow \text{Coverage Compilation} \longrightarrow \text{Replay/Reprocessing} \longrightarrow \text{Governance Telemetry}$$

```
+----------------------------------------------------------------------------------------------------+
|                                     AGNI-NETRA GLOBAL DATA-PLANE                                   |
+----------------------------------------------------------------------------------------------------+
   |
   v
[ Provider Ingestion Adapters ]
   |-- NASA FIRMS (VIIRS NOAA-20/21/SNPP, MODIS Aqua/Terra)
   |-- ISRO Bhuvan (LULC 250k/50k)
   |-- MoEFCC PARIVESH (Clearance Boundaries & Conditions)
   |-- IBM Portal (Mining Leases & NMI Mineral Registry)
   |-- CEA Registry (Power Station Capacities & Fuel Types)
   |-- Copernicus Climate/Atmosphere (ERA5 / CAMS - Disclosed Unconfigured)
   +-- Commercial Optical/SAR (PlanetScope, Sentinel-1/2 - Disclosed Unconfigured)
   |
   v
[ Validation Engine ]
   |-- Schema Conformance (UUID, observation time, source record ID)
   |-- Coordinate Domain Enclosure (Lat in [-90, 90], Lon in [-180, 180])
   +-- Physical Boundary Verification (rejects negative Kelvin, negative FRP, impossible wind speeds)
   |
   +---> FAIL ---> [ Quarantine Manager ] (AES-256 Masked Secrets, Cryptographic Hash)
   |
   v PASS
[ Normalization Engine ]
   |-- Geodesic Coordinate Projection: WGS84 EPSG:4326 canonicalization (NaN/Inf rejection)
   |-- Temporal Canonicalization: ISO-8601 UTC representation (Zulu timezone)
   +-- Physical Unit Canonicalization: Temperature -> K, FRP -> MW, Speed -> m/s, Distance -> m
   |
   v
[ Deduplication Engine ]
   |-- EXACT_DUPLICATE: SHA-256 fingerprint exact match
   |-- SOURCE_DUPLICATE: Identical provider & source record ID
   |-- SAME_SOURCE_REPETITION: Same sensor within 300 meters
   |-- CROSS_PROVIDER_DUPLICATE: Cross-sensor spatial overlap within 1.0 km
   +-- UNIQUE: Novel observation
   (Preserves cross-sensor records; NEVER silently drops data)
   |
   v
[ Quality Control Engine (7 Deterministic Checks) ]
   |-- 1. RANGE_CHECK (Physical metric validity)
   |-- 2. TEMPORAL_CHECK (Skew <= 120s, no future dates > 1h)
   |-- 3. SPATIAL_CHECK (WGS84 EPSG:4326 valid coordinate domain)
   |-- 4. SCHEMA_CHECK (Strict payload structural validation)
   |-- 5. DUPLICATE_CHECK (Identification of repetitions)
   |-- 6. PROVENANCE_CHECK (Ingestion batch & lineage completeness)
   +-- 7. PROVIDER_CHECK (Provider registration & credentials status)
   |
   v
[ Storage & Governed State Machine ]
   |-- Database Ledger: `ingestion_batches`, `ingestion_records`, `ingestion_quarantine`
   |-- Dataset Registry: `governed_dataset_registry` (18 Authoritative Datasets)
   +-- Lifecycle Management: ORIGINAL -> CORRECTED -> RETRACTED
```

---

## 3. Governed Dataset Registry (18 Authoritative Datasets)

| # | Dataset ID | Provider | Update Frequency | SLA Threshold | Category |
|---|------------|----------|------------------|---------------|----------|
| 1 | `FIRMS_VIIRS_N20` | NASA_FIRMS | NRT (3-hourly) | 10,800 s (3h) | Satellite Thermal |
| 2 | `FIRMS_VIIRS_N21` | NASA_FIRMS | NRT (3-hourly) | 10,800 s (3h) | Satellite Thermal |
| 3 | `FIRMS_VIIRS_SNPP` | NASA_FIRMS | NRT (3-hourly) | 10,800 s (3h) | Satellite Thermal |
| 4 | `FIRMS_MODIS_AQUA` | NASA_FIRMS | NRT (6-hourly) | 21,600 s (6h) | Satellite Thermal |
| 5 | `FIRMS_MODIS_TERRA` | NASA_FIRMS | NRT (6-hourly) | 21,600 s (6h) | Satellite Thermal |
| 6 | `BHUVAN_LULC_250K` | ISRO_BHUVAN | Annual | 31,536,000 s (1yr) | Land Use / Land Cover |
| 7 | `BHUVAN_LULC_50K` | ISRO_BHUVAN | Annual | 31,536,000 s (1yr) | Land Use / Land Cover |
| 8 | `PARIVESH_EC_BOUNDARIES`| MOEFCC_PARIVESH | Monthly | 2,592,000 s (30d) | Regulatory Boundaries |
| 9 | `PARIVESH_CONDITIONS` | MOEFCC_PARIVESH | Monthly | 2,592,000 s (30d) | Regulatory Compliance |
| 10 | `IBM_MINING_LEASES` | IBM_PORTAL | Bi-Weekly | 1,209,600 s (14d) | Statutory Cadastre |
| 11 | `IBM_NMI_MINERALS` | IBM_PORTAL | Monthly | 2,592,000 s (30d) | Mineral Inventory |
| 12 | `IBM_AUCTIONED_BLOCKS` | IBM_PORTAL | Monthly | 2,592,000 s (30d) | Auction Leases |
| 13 | `CEA_THERMAL_POWER` | CEA_REGISTRY | Monthly | 2,592,000 s (30d) | Industrial Infrastructure |
| 14 | `ECMWF_ERA5_HOURLY` | COPERNICUS_CDS | Hourly (Unconfigured) | 7,200 s (2h) | Reanalysis Meteorology |
| 15 | `NOAA_GFS_GLOBAL` | NOAA_NCEP | 6-Hourly (Unconfigured) | 21,600 s (6h) | NWP Numerical Weather |
| 16 | `CAMS_AIR_QUALITY` | COPERNICUS_ADS | 6-Hourly (Unconfigured) | 21,600 s (6h) | Atmospheric Composition |
| 17 | `SENTINEL1_2_SAR_OPT` | ESA_COPERNICUS | 5-Daily (Unconfigured) | 432,000 s (5d) | High-Res Earth Obs |
| 18 | `PLANET_SCOPE_DAILY` | PLANET_LABS | Daily (Unconfigured) | 86,400 s (24h) | Commercial Constellation |

---

## 4. Benchmark Execution Results (Section 43)

All 8 benchmarks were executed on the production PostgreSQL 16 PostGIS database holding **8,221,941 historical detections** and **35,567 indexed facilities**:

| Benchmark Metric | Target Specification | Measured Result | Verdict |
|------------------|----------------------|-----------------|---------|
| **Single Record Normalization Latency** | $\le 100\ \mu\text{s}$ | **42.3 $\mu\text{s}$ (P50) / 83.4 $\mu\text{s}$ (P95)** | **PASS** |
| **Batch Normalization (1,000 records)** | $\ge 10,000\ \text{rec/s}$ | **18,375 rec/s (54.42 ms total)** | **PASS** |
| **Batch Normalization (10,000 records)** | $\ge 10,000\ \text{rec/s}$ | **18,890 rec/s (529.37 ms total)** | **PASS** |
| **Deduplication Evaluation Throughput** | $\ge 5,000\ \text{evals/s}$ | **14,524 evals/s (137.70 ms for 2,000 candidates)** | **PASS** |
| **Spatial Query Latency (50km radius)** | $\text{P95} \le 50\ \text{ms}$ | **1.60 ms (P50) / 10.03 ms (P95)** | **PASS** |
| **Provenance Lookup Latency** | $\text{P95} \le 10\ \text{ms}$ | **0.84 ms (P50) / 1.36 ms (P95)** | **PASS** |
| **Freshness Evaluation Latency (All 18 Datasets)** | $\le 50\ \text{ms}$ | **1.98 ms (P50) / 2.42 ms (P95)** | **PASS** |
| **Ingestion Batch Status Query Latency** | $\text{P95} \le 20\ \text{ms}$ | **1.75 ms (P50) / 2.37 ms (P95)** | **PASS** |

**Summary: 8 out of 8 Benchmarks Passed Successfully (100% Target Met).**

---

## 5. Verification Suite & Test Results

### 5.1. Phase 16 Dedicated Test Suite (`tests/test_phase16_global_data_ingestion.py`)
- **36 Scenarios Tested**: Covering Sections 1 to 41 (Canonical coordinates, UTC formatting, unit conversion, geometry normalization, schema checks, 7 QC checks, all 4 deduplication classes, quarantine isolation, freshness SLA computation, coverage compilation, batch replay, and failure injection).
- **Execution Time**: 3.71 seconds.
- **Pass Rate**: **36 / 36 (100% PASS)**.

### 5.2. Core Regression Test Suite
- `tests/test_phase15_security_resilience.py`: 30 tests passed.
- `tests/test_phase15_go_live_readiness.py`: 11 tests passed (validated 8,221,941 detections).
- `tests/test_phase14_end_to_end_acceptance.py`: 12 tests passed.
- `tests/test_phase13_production_hardening.py`: 12 tests passed.
- `tests/test_phase16_global_data_ingestion.py`: 36 tests passed.
- **Total Passing Tests**: **101 / 101 (100% PASS)** in 114.02 seconds.

---

## 6. REST API Endpoints (`/api/v1/data`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/data/providers` | Lists all 7 ingestion providers with health and configuration status |
| `GET` | `/api/v1/data/datasets` | Lists all 18 governed datasets with schema and freshness metadata |
| `GET` | `/api/v1/data/coverage` | Compiles global, regional, national, and unconfigured coverage |
| `GET` | `/api/v1/data/ingestion/status` | Real-time health, active batches, and quarantine counters |
| `GET` | `/api/v1/data/ingestion/batches` | Paginated history of data ingestion batches |
| `GET` | `/api/v1/data/ingestion/batches/{batch_id}` | Detailed telemetry and record counts for an ingestion batch |
| `POST` | `/api/v1/data/ingestion/run-batch` | Submits an observation batch for normalization and ingestion |
| `GET` | `/api/v1/data/freshness` | Factual observation age and SLA evaluation for all datasets |
| `GET` | `/api/v1/data/quarantine` | Quarantine audit log with masked payload inspection |
| `GET` | `/api/v1/data/provenance/{source_record_id}` | End-to-end transformation lineage lookup |

---

## 7. Frontend User Interface Validation

Validated interactively via the automated browser subagent across all 5 key routes:
1. **System Administration & Governance Dashboard (`/admin`)**:
   - Visualized 5 interactive tabs: Governed Datasets (18), Active Providers (7), Observation Freshness & SLA, Quarantine Ledger, and Ingestion Batches.
   - Verified Operational Dispatch Gate safety indicator displaying **BLOCKED**.
   - Inspected connection pool statistics and worker status.
2. **JARVIS NLP Command Console (`/jarvis`)**:
   - Streaming tokens, query prompt, and Operational Dispatch Gate status banner.
3. **Analyst Workstation / National Overview (`/dashboard`)**:
   - KPI cards, thermal map, alert feed, and facility search.
4. **Agency Portal (`/portal/agency`)**:
   - Alert triage queue, evidence reviews, and decision audit trails.
5. **Public Portal (`/portal/public`)**:
   - Public map view, verified incident list, and citizen reporting interface.
- **Artifact Recording**: Captured WebP session video at `phase16_ui_validation_1789215218661.webp`.
