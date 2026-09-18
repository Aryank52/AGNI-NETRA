# AGNI-NETRA — POST-FREEZE DEEP TECHNICAL AUDIT REPORT

**Project Root**: `E:\PROJECTS\AGNI-NETRA`  
**Baseline Commit**: `eb7824e6e58eb61f376a4dadb804984950f624e8` (Phase 26 Frozen Release)  
**Active Development Branch**: `development/post-freeze-intelligence-hardening`  
**Audit Standard**: Zero-Assumption Repository-Level Verification  
**Evaluation Date**: September 2026  

---

## 1. Executive Summary

A comprehensive post-freeze deep technical audit of the AGNI-NETRA platform was conducted to discover every remaining architecture gap, technical debt item, incomplete feature, scalability limitation, resilience vulnerability, and testing deficiency across the codebase.

The audit examined every subsystem end-to-end:
- **Backend API & Core Services**: FastAPI application layer, routing, dependencies, middlewares, and asynchronous Celery tasks.
- **Frontend Console**: Next.js 15 App Router, React 19, MapLibre GL geospatial map engine, and intelligence dossier views.
- **Geospatial & Remote Sensing**: Bhuvan LULC, FSI Protected Areas, CEA Power Infrastructure, IBM Mining Leases, and NASA FIRMS.
- **Machine Learning Layer**: Champion XGBoost (`xgb-v3.0-real-candidate`), Balanced Platt Calibrator, SHAP TreeExplainer, and inference services.
- **JARVIS Autonomous Orchestrator**: Mission workspaces, single master agent orchestration, situational awareness, and voice services.
- **AGNI-SAT Digital Twin**: LEO simulation engine, orbital mechanics, sensor footprint modeling, and scenario runs.
- **Database & Storage**: PostgreSQL 16 + PostGIS 3.4, SQLite test fallback, spatial indexing, table relationships, and Alembic migrations.
- **Security, RBAC & Observability**: JWT authentication lifecycle, RBAC filters, security headers, correlation tracing, and logging.

### Overall Assessment
AGNI-NETRA possesses a solid, highly sophisticated geospatial and analytical foundation. However, **22 confirmed architectural and implementation gaps** currently limit its autonomous operational capabilities, scalability, and lifecycle durability. The primary gaps include:
1. **Passive Pipeline Execution**: Scheduled ingestion relies on legacy processing without automatically triggering the 8-stage proactive intelligence lifecycle or evidence graph assembly.
2. **Ephemeral Lifecycle State**: Incident lifecycle transitions and deduplication fingerprints are maintained in ephemeral Python memory rather than a persisted, audited database ledger.
3. **Stubbed Background Tasks**: Celery scheduled tasks for baseline updates, anomaly detection, and alert generation contain placeholder queries that execute no analysis.
4. **Disconnected JARVIS Reasoning**: The agentic orchestrator relies on hardcoded hypothesis templates and static recommendation strings rather than executing the real Next-Best-Evidence and Cross-Modal reasoning engines.
5. **Spatial Query Bottlenecks**: Spatial facility lookup performs an unindexed $O(N)$ linear loop in pure Python over 35,684 facilities without PostGIS or spatial tree acceleration.
6. **Simulation Contamination Risk**: AGNI-SAT scenario executions write synthetic events to `thermal_events` with `is_demo=False`, without an `is_simulation` database column to isolate them from real observations.

---

## 2. Current Architecture Map

The repository is structured into distinct functional layers:

```
+-----------------------------------------------------------------------------------+
|                                  USER INTERFACE                                   |
|   Next.js 15 + React 19 | MapLibre GL Viewport | Intelligence Dossier & Analytics  |
+-----------------------------------------------------------------------------------+
                                         | REST / JSON
+-----------------------------------------------------------------------------------+
|                            FASTAPI BACKEND (v1 API)                               |
|   Middlewares: CorrelationID, RateLimit, SecurityHeaders, SafeExceptions          |
|   Endpoints: /events, /facilities, /gis, /jarvis, /analytics, /data-truth, etc.   |
+-----------------------------------------------------------------------------------+
                 |                                                |
+---------------------------------+             +-----------------------------------+
|       INTELLIGENCE CORE         |             |      JARVIS ORCHESTRATION         |
| - AutonomousIntelligenceCore    |             | - Single Master Agent             |
| - HistoricalComparisonEngine    |<----------->| - Command Interpreter / Voice     |
| - ProductionThermalPredictor    |  Events &   | - Governed Capability Selector    |
| - EvidenceGraphEngine           | Subscribers | - Situational Awareness Console   |
+---------------------------------+             +-----------------------------------+
                 |                                                |
+-----------------------------------------------------------------------------------+
|                            DATA INGESTION & PIPELINE                              |
|   Adapters: FIRMS, OSM, CEA, Bhuvan, FSI, IBM, WII, Sentinel, Landsat, MOSDAC     |
|   Celery Scheduled Workers: Ingestion, Heartbeat, Cataloging                      |
+-----------------------------------------------------------------------------------+
                                         |
+-----------------------------------------------------------------------------------+
|                        DATABASE & PERSISTENCE LAYER                               |
|   PostgreSQL 16 + PostGIS 3.4 (Production) | SQLite 3 Spatial Fallback (Local)   |
|   Tables: thermal_events, thermal_detections, industrial_facilities, baselines...|
+-----------------------------------------------------------------------------------+
```

---

## 3. Backend Audit

### Finding B-01: Multiple Divergent Ingestion and Pipeline Pathways
- **Exact Path**: `backend/app/services/pipeline_service.py` vs `backend/app/services/live_ingestion_service.py` vs `backend/app/services/autonomous_intelligence_service.py`
- **Current Behavior**: Three distinct services process thermal observations independently:
  1. `pipeline_service.py`: Used by Celery maintenance jobs; invokes legacy v1 ML predictor and writes legacy `ThermalEvent` records.
  2. `live_ingestion_service.py`: Used by phase 10-15 acceptance test scripts; performs SHA-256 deduplication and 18-feature extraction.
  3. `autonomous_intelligence_service.py`: Used only by `/api/v1/jarvis/autonomous/process`; executes the 8-stage lifecycle.
- **Why Limitation**: Feature drift and inconsistent behavior depending on how data enters the system.
- **Impact**: Ingestion jobs do not benefit from the autonomous lifecycle, while API-driven runs bypass standard celery workers.
- **Classification**: **A. CONFIRMED GAP**
- **Proposed Fix**: Unify all ingestion into `AutonomousIntelligenceCore` as the single canonical execution pipeline.
- **Required Tests**: `tests/test_proactive_intelligence_pipeline.py`
- **DB Migration**: No.
- **Frontend Changes**: No.

### Finding B-02: Celery Intelligence Maintenance Tasks are No-Op Stubs
- **Exact Path**: `backend/app/tasks/maintenance_tasks.py` (`baseline_update_job`, `anomaly_analysis_job`, `alert_generation_job`)
- **Current Behavior**:
  ```python
  @shared_task(name="backend.app.tasks.baseline_update_job")
  def baseline_update_job():
      db = SessionLocal()
      try:
          events = db.query(ThermalEvent).all()
          return {"status": "SUCCESS", "events_evaluated": len(events)}
      finally:
          db.close()
  ```
- **Why Limitation**: Tasks run on schedule and consume CPU cycles without updating baselines, calculating anomaly scores, or routing alerts.
- **Impact**: Background maintenance is non-operational.
- **Classification**: **C. CONFIRMED INCOMPLETE FEATURE**
- **Proposed Fix**: Wire `baseline_update_job` to `HistoricalComparisonEngine`, `anomaly_analysis_job` to `anomaly_service`, and `alert_generation_job` to `alert_workflow_service`.
- **Required Tests**: `tests/test_maintenance_tasks.py`
- **DB Migration**: No.
- **Frontend Changes**: No.

---

## 4. Frontend Audit

### Finding FE-01: Absence of Live Event Updates & Stale Data Indication
- **Exact Path**: `frontend/src/app/dashboard/page.tsx`
- **Current Behavior**: Dashboard data is fetched once on page load or on manual filter changes. There is no WebSocket, Server-Sent Events (SSE), or background polling timer.
- **Why Limitation**: Operators have no visibility into newly detected thermal events unless they manually refresh the page.
- **Impact**: Degraded real-time situational awareness during operational incidents.
- **Classification**: **A. CONFIRMED GAP**
- **Proposed Fix**: Implement configurable auto-refresh polling (e.g., 60-second bounded cadence) with a clear visual "Last Refreshed: X seconds ago" timestamp and a "Live Data Stale" warning banner if requests fail.
- **Required Tests**: Frontend component tests.
- **DB Migration**: No.
- **Frontend Changes**: Yes.

### Finding FE-02: Lack of Automated Frontend Test Suite
- **Exact Path**: `frontend/package.json`
- **Current Behavior**: `package.json` contains scripts for `dev`, `build`, `start`, `lint`, and `typecheck`, but no testing framework (no Jest, Vitest, or Playwright).
- **Why Limitation**: Frontend regressions in map interaction, dossier rendering, or auth state cannot be verified automatically in CI.
- **Impact**: High risk of UI breakage during component refactoring.
- **Classification**: **E. CONFIRMED TESTING GAP**
- **Proposed Fix**: Install Vitest + React Testing Library for unit tests and add a basic smoke test suite.
- **Required Tests**: Frontend test runner configuration.
- **DB Migration**: No.
- **Frontend Changes**: Yes.

---

## 5. GIS / PostGIS Audit

### Finding GIS-01: Unindexed $O(N)$ Linear Search for Industrial Facilities
- **Exact Path**: `backend/app/services/spatial_engine.py` (`SpatialIndex.find_nearest`) & `backend/app/services/pipeline_service.py` (L64-75)
- **Current Behavior**: All 35,684 facilities are queried into Python memory as raw dictionaries. For every thermal cluster, the engine loops through all 35,684 facilities calculating `haversine_distance_m()`.
- **Why Limitation**: For a batch of 500 clusters, this executes $500 \times 35,684 = 17,842,000$ haversine calculations in pure Python.
- **Impact**: Massive CPU bottleneck and pipeline execution stalls during large historical or multi-sensor batch ingestion.
- **Classification**: **D. CONFIRMED SCALABILITY LIMITATION**
- **Proposed Fix**: Implement spatial indexing using SciPy `cKDTree` / `BallTree` in memory for rapid nearest-neighbor search, or utilize PostGIS `ST_DWithin` / `ST_Distance` queries with GiST indexes.
- **Required Tests**: `tests/test_geospatial_pipeline.py`
- **DB Migration**: No.
- **Frontend Changes**: No.

### Finding GIS-02: MapLibre Viewport High-Density Rendering Overhead
- **Exact Path**: `frontend/src/components/map/MapLibreView.tsx` (L120-200)
- **Current Behavior**: GeoJSON sources for thermal events, industrial facilities, and power stations are loaded without client-side clustering (`cluster: true` is absent).
- **Why Limitation**: When zooming out to national view (Zoom 4-6), tens of thousands of individual DOM/WebGL circle elements are rendered concurrently.
- **Impact**: Browser memory spikes, frame-rate drops, and unresponsive pan/zoom interactions on standard analyst workstations.
- **Classification**: **D. CONFIRMED SCALABILITY LIMITATION**
- **Proposed Fix**: Enable MapLibre GL clustering (`cluster: true`, `clusterRadius: 50`, `clusterMaxZoom: 14`) on the `thermal_events` and `industrial_facilities` GeoJSON sources.
- **Required Tests**: Map rendering benchmark.
- **DB Migration**: No.
- **Frontend Changes**: Yes.

---

## 6. Ingestion / Data Audit

### Finding ING-01: Missing Webhook Receiver for Industrial SCADA & Flare Telemetry
- **Exact Path**: `backend/app/services/intelligence/next_best_evidence.py` (L62-78)
- **Current Behavior**: SCADA flare flow telemetry is identified across intelligence documents as a critical epistemic evidence source, but is hardcoded everywhere as `NOT CONFIGURED`. No ingestion endpoint or webhook receiver exists.
- **Why Limitation**: Facilities ready to provide authorized DCS / SCADA flare header logs have no automated ingestion interface.
- **Impact**: The system cannot ingest direct on-ground process evidence to resolve combustion ambiguities.
- **Classification**: **C. CONFIRMED INCOMPLETE FEATURE**
- **Proposed Fix**: Create an authenticated REST webhook endpoint (`/api/v1/ingestion/scada/webhook`) with HMAC-SHA256 signature verification, schema validation, and storage in a dedicated `scada_telemetry_logs` table.
- **Required Tests**: `tests/test_scada_ingestion.py`
- **DB Migration**: Yes (new table for SCADA records).
- **Frontend Changes**: No.

### Finding ING-02: Lack of ISRO EOS-04 (RISAT-1A) SAR Ingestion Adapter
- **Exact Path**: `data_pipeline/adapters/`
- **Current Behavior**: Sentinel-1 SAR and Landsat/Sentinel optical adapters exist, but no adapter exists for ISRO EOS-04 C-band Synthetic Aperture Radar data.
- **Why Limitation**: Indian sovereign radar satellite telemetry cannot be ingested directly into the cross-modal engine.
- **Impact**: Over-reliance on European Copernicus Sentinel-1 for radar backscatter analysis over Indian territory.
- **Classification**: **C. CONFIRMED INCOMPLETE FEATURE**
- **Proposed Fix**: Implement an `EOS04Adapter` adhering to `ThermalSourceAdapter` interface for processing ISRO EOS-04 level-1 GRD STAC metadata.
- **Required Tests**: `tests/test_eos04_adapter.py`
- **DB Migration**: No.
- **Frontend Changes**: No.

---

## 7. Machine Learning Audit

### Finding ML-01: Dual Model Predictor Discrepancy (v1 vs. v3 Champion)
- **Exact Path**: `ml/inference/predictor.py` vs `ml/inference/production_inference_service.py`
- **Current Behavior**:
  - `predictor.py`: Loads `v1.0.0-xgboost` (`xgboost_classifier_v1.joblib`) with a 7-class schema and is used by `pipeline_service.py`.
  - `production_inference_service.py`: Loads `xgb-v3.0-real-candidate` (`xgb_v3_real_candidate.joblib`) with Platt calibrator and 6-class schema, used by `autonomous_intelligence_service.py`.
- **Why Limitation**: Two distinct ML models with different feature schemas, class names, and weights operate concurrently in the codebase.
- **Impact**: Events processed through `pipeline_service` receive uncalibrated v1 predictions, while events processed through autonomous intelligence receive calibrated v3 predictions.
- **Classification**: **B. CONFIRMED TECHNICAL DEBT**
- **Proposed Fix**: Refactor `pipeline_service.py` to exclusively call `production_thermal_predictor` (`xgb-v3.0-real-candidate`) and deprecate `predictor.py`.
- **Required Tests**: `tests/test_phase9_production_inference.py`
- **DB Migration**: No.
- **Frontend Changes**: No.

### Finding ML-02: NumPy 2.5 / joblib Deserialization Warnings
- **Exact Path**: `venv/Lib/site-packages/joblib/numpy_pickle.py` (L204-207)
- **Current Behavior**: When loading `.joblib` model artifacts, Python raises:
  `DeprecationWarning: Setting the shape on a NumPy array has been deprecated in NumPy 2.5.`
- **Why Limitation**: The active virtualenv has `numpy==2.5.2` installed, violating the `requirements.txt` constraint (`numpy>=1.26.0,<2.1.0`).
- **Impact**: Unnecessary console noise and risk of serialization failures in future NumPy point releases.
- **Classification**: **B. CONFIRMED TECHNICAL DEBT**
- **Proposed Fix**: Re-serialize model artifacts using `numpy.save` / native joblib protocols compatible with modern NumPy, and ensure virtualenv package versions strictly adhere to pinned dependencies.
- **Required Tests**: Model loading reproducibility test.
- **DB Migration**: No.
- **Frontend Changes**: No.

### Finding ML-03: SHAP TreeExplainer Cold-Start Latency & Sequential Execution
- **Exact Path**: `ml/inference/production_inference_service.py` (`compute_shap_explanation`)
- **Current Behavior**: SHAP explanations are computed individually on single feature vectors inside the inference loop using `self.shap_explainer.shap_values(feat_vec)`.
- **Why Limitation**: `shap_explainer_v3.joblib` is ~3.9 MB. Evaluating single-row TreeExplainer attributions inside high-throughput loops adds 15-40ms overhead per observation.
- **Impact**: Slows down batch ingestion pipelines and creates latency spikes.
- **Classification**: **D. CONFIRMED SCALABILITY LIMITATION**
- **Proposed Fix**: Implement batched SHAP explanation evaluation for bulk inputs, and bypass full TreeExplainer calculations for Tier-3 Routine events.
- **Required Tests**: `tests/test_phase9_production_inference.py`
- **DB Migration**: No.
- **Frontend Changes**: No.

---

## 8. JARVIS Audit

### Finding JR-01: Disconnected Capability Invocation in Agentic Orchestrator
- **Exact Path**: `backend/app/services/jarvis/jarvis_agentic_orchestrator.py` (L170-198)
- **Current Behavior**: In `_execute_governed_investigation`, capabilities `competing_hypotheses_evaluator` and `next_best_evidence_recommender` return hardcoded mock responses:
  ```python
  if "competing_hypotheses_evaluator" in selected_capabilities:
      findings["competing_hypotheses"] = {
          "hypotheses": [
              {"id": "H1_INDUSTRIAL_PROCESS_FIRE", "support_score": 82.0}, ...
          ]
      }
  ```
- **Why Limitation**: Bypasses the actual algorithms implemented in `backend/app/services/intelligence/next_best_evidence.py` and `cross_modal_engine.py`.
- **Impact**: JARVIS reasoning displays static, non-dynamic evidence and recommendations to the user.
- **Classification**: **A. CONFIRMED GAP**
- **Proposed Fix**: Wire real calls to `next_best_evidence_engine.recommend_next_best_evidence()` and dynamic hypothesis generation based on actual event context.
- **Required Tests**: `tests/test_jarvis_autonomous_orchestration.py`
- **DB Migration**: No.
- **Frontend Changes**: No.

### Finding JR-02: Volatile In-Memory Mission Workspace Storage
- **Exact Path**: `backend/app/services/jarvis/jarvis_agentic_orchestrator.py` (L49, L254, L273)
- **Current Behavior**: `self._active_mission` stores only the single most recent mission in a Python variable.
- **Why Limitation**: Running a new investigation completely overwrites the previous mission summary. No history is kept across process restarts.
- **Impact**: Analysts cannot retrieve historical JARVIS autonomous investigation records.
- **Classification**: **D. CONFIRMED SCALABILITY LIMITATION**
- **Proposed Fix**: Persist investigation missions to the existing `investigation_workspaces` table in PostgreSQL.
- **Required Tests**: `tests/test_jarvis_investigation_workspace.py`
- **DB Migration**: No (table already exists).
- **Frontend Changes**: No.

---

## 9. Historical Intelligence Audit

### Finding HI-01: Parallel Inconsistent Baseline Tables
- **Exact Path**: `backend/app/models/domain.py` (`HistoricalBaseline` L596 vs `FacilityBaseline` L615)
- **Current Behavior**: Two separate tables model thermal baselines:
  - `historical_baselines`: Contains `grid_cell_id`, `std_frp`, `baseline_status`, `monthly_pattern`.
  - `facility_baselines`: Contains `facility_id`, `variance_frp`, `frp_distribution`, `status_band`.
- **Why Limitation**: `pipeline_service.py` queries `HistoricalBaseline`, while `historical_comparison_engine.py` queries `FacilityBaseline`.
- **Impact**: Inconsistent baseline statistics and deviation ratios depending on which service evaluates an event.
- **Classification**: **B. CONFIRMED TECHNICAL DEBT**
- **Proposed Fix**: Establish a unified baseline retrieval interface in `baseline_service.py` that hierarchically checks facility baselines first and falls back to spatial grid cell baselines.
- **Required Tests**: `tests/test_phase25_unified_historical_intelligence.py`
- **DB Migration**: No.
- **Frontend Changes**: No.

---

## 10. AGNI-SAT Audit

### Finding SAT-01: Simulation Events Contaminate Live DB Tables
- **Exact Path**: `backend/app/services/satellite_simulator.py` (L568) & `backend/app/models/domain.py` (L520-560)
- **Current Behavior**: In `satellite_simulator.run_scenario()`, simulated observations are created with `is_demo=False`, passed through `pipeline_service`, and inserted into `thermal_events`. `ThermalEvent` has NO `is_simulation` column.
- **Why Limitation**: Simulated satellite scenario events are permanently written into live database tables without being flaggable as simulation data.
- **Impact**: Violates core system invariant: *"AGNI-SAT remains SIMULATION / DIGITAL TWIN; no fabricated telemetry."*
- **Classification**: **A. CONFIRMED GAP**
- **Proposed Fix**: Add `is_simulation = Column(Boolean, default=False)` to `ThermalEvent` in `domain.py`, set `is_simulation=True` and `is_demo=True` on all simulator outputs, and filter out simulation records by default from operational API queries.
- **Required Tests**: `tests/test_agni_sat_mission_control.py`
- **DB Migration**: Yes (add `is_simulation` column to `thermal_events`).
- **Frontend Changes**: No.

---

## 11. Security Audit

### Finding SEC-01: Permissions-Policy Header Blocks Browser Microphone
- **Exact Path**: `backend/app/core/middleware.py` (L44)
- **Current Behavior**:
  ```python
  response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
  ```
- **Why Limitation**: `microphone=()` explicitly orders web browsers to block all microphone capture.
- **Impact**: Users cannot utilize voice commands in the JARVIS Operational Console (`/jarvis`).
- **Classification**: **A. CONFIRMED GAP**
- **Proposed Fix**: Update header to `Permissions-Policy: geolocation=(), camera=(), microphone=(self)` to allow microphone access on the application origin.
- **Required Tests**: `tests/test_phase15_security_resilience.py`
- **DB Migration**: No.
- **Frontend Changes**: No.

### Finding SEC-02: JWT Access Tokens Lack Blacklisting / Revocation
- **Exact Path**: `backend/app/core/security.py` (L14-27) & `backend/app/core/config.py` (L22)
- **Current Behavior**: Tokens expire after 24 hours (`ACCESS_TOKEN_EXPIRE_MINUTES = 1440`). There is no token blacklist table or Redis cache to revoke tokens upon user logout.
- **Why Limitation**: Compromised tokens remain valid until expiration even after an analyst logs out or is deactivated.
- **Impact**: Inability to immediately terminate sessions in the event of credential leakage.
- **Classification**: **A. CONFIRMED GAP**
- **Proposed Fix**: Store active/revoked JWT JTI identifiers in Redis with TTL matching remaining token lifespan.
- **Required Tests**: `tests/test_auth.py`
- **DB Migration**: No (uses Redis).
- **Frontend Changes**: No.

---

## 12. Resilience / Failure-Mode Audit

### Finding RES-01: In-Memory Rate Limiter Lacks Process Eviction & Worker Sync
- **Exact Path**: `backend/app/core/middleware.py` (`RateLimitMiddleware`)
- **Current Behavior**: Request timestamps are stored in an in-memory `defaultdict(list)`.
- **Why Limitation**: Memory grows unboundedly as unique client IPs connect. Rate limits are not shared across multiple Uvicorn worker processes.
- **Impact**: Inconsistent rate enforcement across processes and slow memory leak under sustained traffic.
- **Classification**: **D. CONFIRMED SCALABILITY LIMITATION**
- **Proposed Fix**: Implement sliding-window rate limiting in Redis, with fallback to an in-memory bounded LRU cache with periodic TTL eviction.
- **Required Tests**: `tests/test_phase15_security_resilience.py`
- **DB Migration**: No.
- **Frontend Changes**: No.

### Finding RES-02: Absence of Circuit Breaker on External HTTP Providers
- **Exact Path**: `data_pipeline/adapters/firms_adapter.py` & `data_plane/live_provider_service.py`
- **Current Behavior**: If the NASA EOSDIS API or remote STAC servers fail or hang, requests retry with exponential backoff on every query without tripping an open circuit state.
- **Why Limitation**: Repeated retries against a completely unavailable external provider consume thread pool connections and increase latency.
- **Impact**: Cascading delays in ingestion worker queues.
- **Classification**: **A. CONFIRMED GAP**
- **Proposed Fix**: Implement an explicit 3-state Circuit Breaker (`CLOSED`, `OPEN`, `HALF-OPEN`) with configurable failure threshold (e.g. 5 consecutive 5xx errors) and reset timeout (e.g. 180s).
- **Required Tests**: `tests/test_real_adapters_and_sources.py`
- **DB Migration**: No.
- **Frontend Changes**: No.

---

## 13. Database Audit

### Finding DB-01: Missing Foreign Key Index on `thermal_detections.event_id`
- **Exact Path**: `backend/app/models/domain.py` (L589)
- **Current Behavior**: `event_id = Column(String(36), ForeignKey("thermal_events.id"), nullable=True)` does not have `index=True`.
- **Why Limitation**: Any query filtering child detections for an event (`SELECT * FROM thermal_detections WHERE event_id = :id`) executes a full sequential scan across millions of detection rows.
- **Impact**: High database CPU usage and slow event dossier loading.
- **Classification**: **D. CONFIRMED SCALABILITY LIMITATION**
- **Proposed Fix**: Add `index=True` to `event_id` in `domain.py` and create index `ix_thermal_detections_event_id` in the database.
- **Required Tests**: Database index verification test.
- **DB Migration**: Yes (create index).
- **Frontend Changes**: No.

### Finding DB-02: Missing Composite Spatial-Temporal Index on `thermal_detections`
- **Exact Path**: `backend/app/models/domain.py` (L581-583)
- **Current Behavior**: `latitude` and `longitude` are unindexed; only `acq_timestamp` has an index.
- **Why Limitation**: Point-in-time historical lookups filter by `latitude BETWEEN ... AND longitude BETWEEN ... AND acq_timestamp < ...`.
- **Impact**: Forces large index range scans and heap fetches over massive tables.
- **Classification**: **D. CONFIRMED SCALABILITY LIMITATION**
- **Proposed Fix**: Add a composite index `(latitude, longitude, acq_timestamp)` on `thermal_detections`.
- **Required Tests**: `database/check_indexes.py`
- **DB Migration**: Yes (create composite index).
- **Frontend Changes**: No.

### Finding DB-03: Empty Downgrade and Non-Incremental Alembic Migrations
- **Exact Path**: `alembic/versions/001_initial_schema.py` & `002_complete_schema_and_telemetry.py`
- **Current Behavior**: Both migration scripts have `downgrade()` defined as empty `pass`. Revision 002 calls `Base.metadata.create_all()` rather than explicit DDL operations.
- **Why Limitation**: Automated schema rollbacks are impossible. Schema evolution cannot be tracked in version control.
- **Impact**: Database recovery and staging deployments require manual DDL intervention.
- **Classification**: **B. CONFIRMED TECHNICAL DEBT**
- **Proposed Fix**: Develop explicit, reversible Alembic migration scripts for all new columns and tables.
- **Required Tests**: `alembic check` and migration upgrade/downgrade test.
- **DB Migration**: Yes.
- **Frontend Changes**: No.

---

## 14. Observability Audit

### Finding OBS-01: Incomplete Lineage Context Propagation
- **Exact Path**: `backend/app/core/logging_config.py` (L10-15)
- **Current Behavior**: Context variables exist for `correlation_id`, `job_id`, `event_id`, `alert_id`, `analyst_id`. However, context variables are missing for `investigation_id`, `inference_id`, and `evidence_id`.
- **Why Limitation**: Logs emitted during model inference and JARVIS investigations cannot be correlated to a specific model run or evidence node.
- **Impact**: Difficulties tracing automated intelligence decisions through log aggregation pipelines.
- **Classification**: **B. CONFIRMED TECHNICAL DEBT**
- **Proposed Fix**: Add `investigation_id_ctx` and `inference_id_ctx` to `logging_config.py` and propagate them across ML and JARVIS services.
- **Required Tests**: `tests/test_phase9_production_inference.py`
- **DB Migration**: No.
- **Frontend Changes**: No.

---

## 15. Testing Audit

### Finding TST-01: Absence of Proactive Intelligence Pipeline End-to-End Test
- **Exact Path**: `tests/`
- **Current Behavior**: Existing tests cover individual components (clustering, ML inference, baseline calculation, and JARVIS voice), but there is no dedicated automated test that verifies the full 8-stage proactive lifecycle from raw observation ingestion through to incident formation and database transition logging without human intervention.
- **Why Limitation**: Cannot automatically verify that proactive intelligence remains unbroken during refactoring.
- **Impact**: Regressions in event lifecycle transitions can slip into production unnoticed.
- **Classification**: **E. CONFIRMED TESTING GAP**
- **Proposed Fix**: Create `tests/test_proactive_intelligence_pipeline.py` testing the complete autonomous chain.
- **Required Tests**: New test file.
- **DB Migration**: No.
- **Frontend Changes**: No.

---

## 16. Performance / Scalability Audit

### Finding PERF-01: High Memory Allocation During Full Historical Aggregations
- **Exact Path**: `backend/app/api/v1/endpoints/historical.py`
- **Current Behavior**: Several longitudinal aggregation endpoints fetch raw records into Python memory before computing monthly sums and percentiles.
- **Why Limitation**: For the 8.2 million row dataset, retrieving unaggregated rows causes severe RAM consumption.
- **Impact**: Potential out-of-memory (OOM) worker crashes under concurrent analyst usage.
- **Classification**: **D. CONFIRMED SCALABILITY LIMITATION**
- **Proposed Fix**: Push aggregations into SQL (`GROUP BY date_trunc('month', acq_timestamp)`, `percentile_cont()`).
- **Required Tests**: Performance benchmark script.
- **DB Migration**: No.
- **Frontend Changes**: No.

---

## 17. Documentation / Code Consistency Audit

### Finding DOC-01: Stale Documentation Referring to v1 ML Models
- **Exact Path**: `docs/ML.md` & `docs/MODEL_REGISTRY.md`
- **Current Behavior**: Documentation references `xgboost_classifier_v1.joblib` and 7 target classes, whereas the production system was frozen on `xgb-v3.0-real-candidate` with 6 classes.
- **Why Limitation**: Misleads developers and auditors regarding active model versions and target labels.
- **Impact**: Developer confusion and onboarding delays.
- **Classification**: **B. CONFIRMED TECHNICAL DEBT**
- **Proposed Fix**: Update documentation to reflect `xgb-v3.0-real-candidate` and the 6-class schema.
- **Required Tests**: None.
- **DB Migration**: No.
- **Frontend Changes**: No.

---

## 18. Deployment / Configuration Audit

### Finding DEP-01: Hardcoded Fallback Secret Key in Configuration
- **Exact Path**: `backend/app/core/config.py` (L22)
- **Current Behavior**: `SECRET_KEY: str = "agni_netra_secret_key_change_in_production_2026_super_secure_key_12345"`
- **Why Limitation**: If `SECRET_KEY` is omitted from the deployment environment, the backend silently falls back to a known static secret.
- **Impact**: Severe security vulnerability in production environments.
- **Classification**: **A. CONFIRMED GAP**
- **Proposed Fix**: In non-debug/production mode (`ENVIRONMENT == "production"`), raise an explicit startup error if `SECRET_KEY` is not provided or matches the default fallback string.
- **Required Tests**: Configuration validation test.
- **DB Migration**: No.
- **Frontend Changes**: No.

---

## 19. Confirmed Remaining Gaps (Complete List)

| Finding ID | Classification | Area | Affected File(s) | Description |
|---|---|---|---|---|
| **F-01** | CONFIRMED GAP | Pipeline | `maintenance_tasks.py`, `pipeline_service.py` | Passive ingestion pipeline; missing autonomous event engine integration. |
| **F-02** | CONFIRMED TECHNICAL DEBT | Lifecycle | `autonomous_intelligence_service.py` | Ephemeral in-memory lifecycle state and fingerprints. |
| **F-03** | CONFIRMED INCOMPLETE FEATURE | Background Tasks | `maintenance_tasks.py` | No-op stubs in scheduled maintenance tasks. |
| **F-04** | CONFIRMED GAP | JARVIS | `jarvis_agentic_orchestrator.py` | Disconnected real evidence generation engines in favor of hardcoded mocks. |
| **F-05** | CONFIRMED SCALABILITY LIMITATION | JARVIS | `jarvis_agentic_orchestrator.py` | Single in-memory mission storage overwriting past investigations. |
| **F-06** | CONFIRMED TECHNICAL DEBT | Historical | `domain.py`, `historical_comparison_engine.py` | Dual parallel baseline tables (`HistoricalBaseline` vs `FacilityBaseline`). |
| **F-07** | CONFIRMED TECHNICAL DEBT | ML | `predictor.py`, `production_inference_service.py` | Dual inference engines running v1 vs v3 models. |
| **F-08** | CONFIRMED SCALABILITY LIMITATION | ML | `production_inference_service.py` | Unbatched SHAP TreeExplainer calculation per observation. |
| **F-09** | CONFIRMED TECHNICAL DEBT | ML / Runtime | `venv/.../joblib/numpy_pickle.py` | NumPy 2.5 shape assignment deprecation warnings on model load. |
| **F-10** | CONFIRMED SCALABILITY LIMITATION | GIS | `spatial_engine.py` | O(N) unindexed linear search over 35,684 facilities in Python. |
| **F-11** | CONFIRMED DATABASE LIMITATION | Database | `domain.py` | Core detection and event tables lack PostGIS `Geometry` columns. |
| **F-12** | CONFIRMED DATABASE LIMITATION | Database | `domain.py` | Missing foreign key index on `thermal_detections.event_id`. |
| **F-13** | CONFIRMED DATABASE LIMITATION | Database | `domain.py` | Missing composite spatial-temporal index on `(latitude, longitude, acq_timestamp)`. |
| **F-14** | CONFIRMED TECHNICAL DEBT | Alembic | `alembic/versions/` | Empty downgrade handlers and non-reversible migrations. |
| **F-15** | CONFIRMED GAP | Security | `middleware.py` | `Permissions-Policy` header blocks microphone access for JARVIS. |
| **F-16** | CONFIRMED SCALABILITY LIMITATION | Resilience | `middleware.py` | In-memory rate limiter lacks eviction and multi-worker synchronization. |
| **F-17** | CONFIRMED SECURITY GAP | Security | `security.py` | JWT access tokens lack blacklisting and revocation mechanisms. |
| **F-18** | CONFIRMED GAP | AGNI-SAT | `satellite_simulator.py`, `domain.py` | Simulation scenario events contaminate live database without `is_simulation` flag. |
| **F-19** | CONFIRMED INCOMPLETE FEATURE | Data Quality | `data_quality_service.py` | Missing automated data quality and referential integrity scanning engine. |
| **F-20** | CONFIRMED TESTING GAP | Frontend | `package.json`, `dashboard/page.tsx` | Zero frontend automated tests; missing live polling & stale data warning. |
| **F-21** | CONFIRMED SCALABILITY LIMITATION | GIS / UX | `MapLibreView.tsx` | High-density vector layers lack client-side GeoJSON point clustering. |
| **F-22** | CONFIRMED INCOMPLETE FEATURE | Ingestion | `next_best_evidence.py`, `data_pipeline/` | Missing webhook receiver for SCADA flare logs and ISRO EOS-04 adapter. |

---

## 20. Suspected Gaps Requiring Validation

1. **Suspected Gap S-01: SQLite vs PostgreSQL Spatial Query Performance Parity**  
   - *Hypothesis*: The SQLite spatial emulation functions registered in `register_sqlite_gis_functions` using Shapely may exhibit substantial latency degradation when evaluating large polygon bounding box intersections compared to native PostGIS C-libraries.  
   - *Validation Plan*: Run spatial query benchmark comparing execution time of 1,000 polygon lookups under SQLite vs PostgreSQL 16 + PostGIS.

2. **Suspected Gap S-02: MapLibre WebGL Context Loss on Tab Switching**  
   - *Hypothesis*: Long-running dashboard sessions may suffer WebGL context loss when browser tabs are placed in background memory sleep mode by Chrome/Edge.  
   - *Validation Plan*: Simulate WebGL context loss event in browser E2E test and verify map auto-restoration.

---

## 21. Recommended Implementation Order

To maintain stability and adhere to the repository development rules, implementation must proceed through 8 sequential work packages:

1. **WP1: Proactive Intelligence Event Engine** *(Immediate Priority)*
2. **WP2: JARVIS Observer + Dynamic Orchestration**
3. **WP3: Historical Intelligence Expansion**
4. **WP4: ML Lifecycle + Model Quality Hardening**
5. **WP5: Data Ingestion + Industrial Sensor Interfaces**
6. **WP6: Resilience + Observability**
7. **WP7: GIS / Data Performance**
8. **WP8: Security + Deep Testing**

*End of Deep Technical Audit Report.*
