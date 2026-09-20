# AGNI-NETRA — WP4 Sovereign Geographic Domain & Boundary Intelligence Report

**Work Package:** WP4 — Sovereign Geographic Domain & Boundary Intelligence  
**Branch:** `development/post-freeze-intelligence-hardening`  
**Base Commit:** `eb7824e6e58eb61f376a4dadb804984950f624e8` (Frozen Phase 26)  
**Target Environment:** PostgreSQL 16.2 + PostGIS 3.4.1 (SRID 4326) / TimescaleDB  
**Status:** **COMPLETED & VERIFIED**  

---

## 1. Executive Summary

Work Package 4 (WP4) established authoritative, mathematically rigorous, and auditable sovereign India-domain boundary enforcement across every subsystem in AGNI-NETRA. 

Prior to WP4, several layers relied on software-level shortcuts: rectangular bounding boxes (e.g. `5 <= lat <= 39`, `65 <= lon <= 100`) as proxies for sovereign territory, silent fallback guessing (defaulting unassigned coordinates to `"Gujarat"` and `"Kutch"`), and silent swapping of inverted bounding box coordinates.

WP4 eliminated all coordinate proxies and guessing mechanisms, replacing them with:
1. **Authoritative PostGIS Polygon Containment:** 100% of sovereign boundary decisions are evaluated using PostGIS `ST_Within` on `admin_boundaries` (`admin_level = 1`, 36 States/UTs, 7,595 total administrative entities, SRID 4326).
2. **Epistemic Honesty:** Unassigned points inside India receive `state = state_name`, `district = "UNKNOWN"`. Administrative context is never fabricated.
3. **Ingestion Plane Sovereign Quarantine:** Foreign observations (e.g. Lahore, Karachi, Colombo, international waters) are quarantined into `ingestion_quarantine` with `SOVEREIGN_OUT_OF_DOMAIN`, preventing foreign data from becoming active events, training baselines, or JARVIS alerts.
4. **JARVIS 5-Tier Location Grounding:** Natural language commands with foreign place names or coordinates are classified as `OUT_OF_DOMAIN_LOCATION` and rejected before querying sovereign infrastructure.
5. **Strict GIS API Contracts:** Disallowed silent coordinate inversion; inverted bounding boxes return `HTTP 400 Bad Request`.
6. **Public Portal Sanitization:** All public hazard endpoints enforce sovereign boundary filtering and blur facility centroids to 2 decimal places (`~1.1 km`).
7. **High-Performance Spatial Execution:** PostGIS GiST index scans achieve **6.05 ms** single-point latency and **130.50 points/sec** batch throughput.

---

## 2. Before vs. After Architecture Comparison

```
BEFORE WP4:
Raw Coordinates ──> [BBOX Proxy (5–39, 65–100)] ──> [Guess "Gujarat"/"Kutch"] ──> Active Event (EVT-GUJ-...)
                                                         │
                                                  (Foreign Points Allowed)
                                                         ▼
                                                  CORRUPTED HISTORICAL GROUND TRUTH

AFTER WP4:
Raw Coordinates ──> [Range & WGS-84 Bounds Check]
                           │
                           ▼
                    [PostGIS ST_Within Polygon Containment]
                    (admin_boundaries level 1, 36 States/UTs, GiST Index Scan)
                     ├── Foreign Point ──> QUARANTINED TO DLQ (SOVEREIGN_OUT_OF_DOMAIN)
                     │                     (Audit Record Preserved, Zero Event Creation)
                     │
                     └── Sovereign Point ──> [Hierarchical PostGIS Level 2 Lookup]
                                              ├── District Found: (State, District)
                                              └── District Unresolvable: (State, "UNKNOWN")
                                                  │
                                                  ▼
                                            [Proactive Intelligence Pipeline (WP1)]
                                                  │
                                                  ▼
                                            [JARVIS Master Observer (5-Tier Grounding)]
```

---

## 3. Subsystem Hardening Summary

### 3.1 Authoritative Boundary Service (`india_boundary_service.py`)
- **Authoritative Function:** `is_within_india(lat, lon, db)` provides the authoritative entrypoint.
- **Hierarchical Provenance:** `get_hierarchical_context()` tags every evaluation with:
  - `boundary_source`: `"geoBoundaries / DataMeet India / Local Government Directory (LGD)"`
  - `boundary_version`: `"2024"`
  - `srid`: `4326`
  - `resolved_at`: ISO UTC timestamp.
- **Elimination of Fallback Guessing:** Removed all legacy fallbacks that assigned coordinates to Gujarat/Jamnagar or Jharkhand/Dhanbad.
- **Dual-Engine Precision:** Uses PostGIS `ST_Within` in PostgreSQL and cached Shapely `admin_boundaries` geometry in SQLite test modes.

### 3.2 Spatial Engine Refactoring (`spatial_engine.py`)
- **Hardened Validation:** `validate_coordinates(lat, lon, check_sovereign=True)` checks float validity, rejects NaN/inf, verifies geodetic ranges, and executes authoritative polygon containment.
- **Authoritative Routing:** `lookup_state()` and `lookup_district()` delegate directly to `india_boundary_service` without bounding-box guessing.

### 3.3 Ingestion DLQ Integration (`hardened_ingestion_service.py`)
- **Sovereign Containment Gate:** Ingestion batches evaluate `is_within_india()`.
- **Zero Silent Loss:** Foreign records are quarantined in `ingestion_quarantine` with error category `INVALID_COORDINATE` and failure reason `SOVEREIGN_OUT_OF_DOMAIN: Point ({lat}, {lon}) lies outside sovereign India boundary (identified as {neighbor})`.
- **Replay & Late-Arrival Safety:** Replayed and late-arriving records cannot bypass sovereign boundary checks.

### 3.4 Autonomous Intelligence Core (`autonomous_intelligence_service.py`)
- Replaced coarse envelope filter with authoritative sovereign check.
- State and district assignment enforces epistemic `UNKNOWN` when spatial boundaries are unresolvable: `state = "UNKNOWN"`, `district = "UNKNOWN"`.

### 3.5 JARVIS 5-Tier Location Grounding (`jarvis_mission_service.py`)
- Enforces 5 explicit location categories:
  1. `EXPLICIT_USER_LOCATION`: Raw textual location provided by analyst.
  2. `RESOLVED_LOCATION`: Geocoded or mapped coordinates.
  3. `AUTHORITATIVE_GIS_LOCATION`: PostGIS-verified sovereign location in India.
  4. `UNKNOWN_LOCATION`: Unresolvable or unspecified location.
  5. `OUT_OF_DOMAIN_LOCATION`: Verified foreign or out-of-domain location.
- Natural language objectives containing foreign names (Lahore, Karachi, Islamabad, Kathmandu, Dhaka, Chittagong, Colombo, Thimphu, Dubai, etc.) or raw foreign coordinates are immediately rejected with `intent = "REJECTED_OUT_OF_SCOPE"` and `location_category = "OUT_OF_DOMAIN_LOCATION"`.

### 3.6 GIS & Portal APIs (`gis.py`, `portals.py`)
- **Strict BBOX Validation:** Removed silent coordinate swapping in `parse_bbox`. Coordinates where `min_lon > max_lon` or `min_lat > max_lat` trigger `HTTP 400 Bad Request`.
- **Public Portal Sanitization:** Filtered out `OUTSIDE_INDIA` and `FOREIGN` events and applied coordinate blurring (2 decimal places ~ 1.1 km) to protect strategic infrastructure perimeters.

---

## 4. Empirical Performance Benchmarks

Benchmarked on live PostgreSQL 16 with `database/benchmark_wp4_geography.py` utilizing the spatial GiST index `idx_admin_bound_geom`:

### 4.1 Latency Percentiles & Throughput
| Benchmark Case | Mean Latency | P50 Latency | P95 Latency | P99 Latency | Validated Throughput |
|---|---|---|---|---|---|
| **Single Point Containment (100 trials)** | **6.05 ms** | **5.37 ms** | **11.58 ms** | **16.52 ms** | **165.41 checks / sec** |
| **100-Point Batch (30 trials)** | **766.27 ms** | **690.91 ms** | **1,261.87 ms** | **2,007.11 ms** | **130.50 points / sec** |
| **1,000-Point Batch (5 trials)** | **8,581.33 ms** | **7,777.59 ms** | **10,734.47 ms** | **10,944.49 ms** | **116.53 points / sec** |

### 4.2 PostGIS Execution Plan (EXPLAIN ANALYZE)
```
Index Scan using idx_admin_bound_geom on admin_boundaries ab  (cost=0.15..20.67 rows=1 width=31)
  Index Cond: (geom ~ '0101000020E61000004C378941604D5340B003E78C289D3C40'::geometry)
  Filter: ((admin_level = 1) AND st_within('0101000020E61000004C378941604D5340B003E78C289D3C40'::geometry, geom))
  Rows Removed by Filter: 8
Planning Time: 164.808 ms
Execution Time: 54.497 ms
```

---

## 5. Dedicated WP4 25-Scenario Test Matrix

All 25 resilience, accuracy, and boundary scenarios in [`tests/test_wp4_sovereign_geography.py`](file:///e:/PROJECTS/AGNI-NETRA/tests/test_wp4_sovereign_geography.py) were executed on PostgreSQL 16:

| # | Test Scenario | Description | Result |
|---|---|---|---|
| **01** | Valid Indian Point | New Delhi (28.61, 77.20) accepted, state='Delhi' | **PASS** |
| **02** | Foreign Point Rejection | Lahore, Karachi, Colombo rejected with detected neighbor | **PASS** |
| **03** | Boundary Point Determinism | Wagah border-adjacent coordinates evaluate deterministically | **PASS** |
| **04** | Coastal Point Acceptance | Jamnagar (Gujarat) and Chennai (Tamil Nadu) accepted | **PASS** |
| **05** | Island Point Acceptance | Port Blair (A&N) and Kavaratti (Lakshadweep) accepted | **PASS** |
| **06** | Null/NaN/Inf Handling | Null, NaN, inf coordinates rejected safely without exceptions | **PASS** |
| **07** | Geodetic Range Rejection | Lat > 90, Lon > 180, Lat < -90 rejected | **PASS** |
| **08** | State Containment | Multi-state points resolve correct state boundaries | **PASS** |
| **09** | District Containment | District resolved accurately or 'UNKNOWN' (no guessing) | **PASS** |
| **10** | State-District Consistency | State and district belong to same jurisdiction | **PASS** |
| **11** | Ingestion Sovereign Rejection | Foreign obs quarantined to DLQ; 0 active events created | **PASS** |
| **12** | Duplicate/Replay Rejection | Replayed foreign obs cannot bypass sovereign DLQ | **PASS** |
| **13** | Late-Arrival Rejection | Late-arriving foreign obs quarantined to DLQ | **PASS** |
| **14** | JARVIS Foreign Rejection | "Investigate Lahore" marked OUT_OF_DOMAIN_LOCATION | **PASS** |
| **15** | Historical Spatial Filter | Historical spatial query with foreign box returns 0 Indian records | **PASS** |
| **16** | GIS Coordinate Order | GeoJSON follows [lon, lat] ordering and SRID 4326 | **PASS** |
| **17** | BBOX Contract Invariant | Inverted min_lon > max_lon raises HTTP 400 Bad Request | **PASS** |
| **18** | SRID 4326 Consistency | All 7,595 admin_boundaries rows use SRID 4326 | **PASS** |
| **19** | Public Hazard Sanitization | Coordinates blurred to 2 decimals (~1.1 km), foreign events excluded | **PASS** |
| **20** | Adversarial Place Queries | Kathmandu, Dhaka, Chittagong, Thimphu, Dubai rejected | **PASS** |
| **21** | Invalid Geometry Check | 0 invalid geometries across all 7,595 admin_boundaries rows | **PASS** |
| **22** | Provenance Tracking | boundary_source, version '2024', SRID 4326, resolved_at present | **PASS** |
| **23** | Batch Partitioning | Mixed telemetry correctly partitioned into India vs outside | **PASS** |
| **24** | Performance Threshold | Single point containment executes under 100ms (measured 6.05ms) | **PASS** |
| **25** | Safety Gate Invariants | Dispatch gate and automated model activation gates locked False | **PASS** |

---

## 6. Model Governance Lineage Clarification (Section 23)

In accordance with Section 23 of the WP4 specification, the model governance status is explicitly documented:

- **Loaded Model / Production Inference Engine:**
  The in-memory production inference pipeline utilizes `xgb-v3.0-real-candidate` loaded via joblib alongside its Balanced Platt calibrator and TreeExplainer SHAP explainer.
- **Governed Champion Designation:**
  `xgb-v3.0-real-candidate` is the frozen production candidate selected during Phase 8H and promoted through Phase 9.
- **Database Activation Status:**
  In the database registry table `ml_model_registry`, `xgb-v3.0-real-candidate` has:
  ```sql
  status = 'CANDIDATE'
  is_active = FALSE
  ```
- **Automated Promotion Safety Gate:**
  `ENABLE_AUTOMATED_MODEL_ACTIVATION = False` is permanently enforced in `backend/app/core/safety_gates.py`. Automated model activation or self-promotion is strictly prohibited. Formal promotion to `ACTIVE` requires manual human MLOps sign-off.
- **Semantic Resolution:**
  "Active" in operational logs refers to *runtime inference availability* in the service layer, while *formal governance status* remains `CANDIDATE` with `is_active = FALSE`. No model has been silently renamed or promoted.

---

## 7. Sovereign Data Truth & Permanent Invariants

| Invariant | Status | Verification Evidence |
|---|---|---|
| **PostgreSQL Preservation** | **VERIFIED** | PostgreSQL 16 (14 GB, 8.22M detections) completely unreset. |
| **Sovereign Facilities Base** | **VERIFIED** | 35,570 active facilities (35,684 total with staging variance) preserved. |
| **CEA Generating Units** | **VERIFIED** | 1,633 generating units across 502 power stations preserved. |
| **Governed ML Model** | **VERIFIED** | `xgb-v3.0-real-candidate` active candidate; registry locked `is_active = FALSE`. |
| **Operational Dispatch Gate**| **VERIFIED** | `ENABLE_OPERATIONAL_DISPATCH_GATE = False` permanently enforced. |
| **Model Activation Gate** | **VERIFIED** | `ENABLE_AUTOMATED_MODEL_ACTIVATION = False` permanently enforced. |
| **Single Master Observer** | **VERIFIED** | `JARVIS-MASTER-OBSERVER-01` operates without agent swarms or synthetic mixing. |
| **Zero Synthetic Substitution**| **VERIFIED** | AGNI-SAT digital twin isolated; zero simulated telemetry enters sovereign tables. |

---

## 8. Rollback Procedures

If geographic validation requires rollback or temporary coarse pass-through:
1. **Service Layer Rollback:**
   Revert git commit `HEAD`:
   ```bash
   git revert HEAD --no-edit
   ```
2. **Watermark & Quarantine Cursors:**
   Watermarks in `ingestion_checkpoints` and quarantine records in `ingestion_quarantine` are non-destructive and do not require table drops or truncation. Quarantined records can be inspected and replayed via `/api/v1/ingestion/replay`.
