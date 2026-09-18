# AGNI-NETRA — POST-FREEZE DEVELOPMENT ROADMAP

**Document**: Post-Freeze Intelligence Hardening Roadmap  
**Target Branch**: `development/post-freeze-intelligence-hardening`  
**Frozen Baseline**: Commit `eb7824e6e58eb61f376a4dadb804984950f624e8`  
**Architecture Principles**: India-First Sovereign Scope, Single Master JARVIS Agent, Zero Fabricated Telemetry, Permanent Operational Dispatch Safety Gate.

---

## Roadmap Overview

The post-freeze hardening program organizes all confirmed findings into **eight structured, sequential Work Packages (WP1 – WP8)**. Each work package is self-contained, bounded, idempotent, fully testable, and equipped with a clear rollback strategy.

```
+-------------------------------------------------------------------------------+
|                       POST-FREEZE WORK PACKAGE PIPELINE                       |
+-------------------------------------------------------------------------------+
  [WP1: Proactive Intelligence Event Engine]  <--- CURRENT IMPLEMENTATION SCOPE
         |
         v
  [WP2: JARVIS Observer + Dynamic Orchestration]
         |
         v
  [WP3: Historical Intelligence Expansion]
         |
         v
  [WP4: ML Lifecycle + Model Quality Hardening]
         |
         v
  [WP5: Data Ingestion + Industrial Sensor Interfaces]
         |
         v
  [WP6: Resilience + Observability]
         |
         v
  [WP7: GIS / Data Performance]
         |
         v
  [WP8: Security + Deep Testing]
```

---

## Work Package 1: Proactive Intelligence Event Engine (WP1)

- **Status**: **ACTIVE IMPLEMENTATION**
- **Objective**: Transition AGNI-NETRA from a passive, human-commanded pipeline into a proactive, event-driven intelligence engine. Whenever new raw thermal observations are ingested (via scheduled tasks, streaming feeds, or API), the system autonomously executes:
  $$\text{Observation} \rightarrow \text{Validation} \rightarrow \text{Deduplication} \rightarrow \text{Clustering} \rightarrow \text{Context Fusion} \rightarrow \text{Classification} \rightarrow \text{Anomaly Detection} \rightarrow \text{Risk/Priority} \rightarrow \text{Evidence Graph} \rightarrow \text{Incident Intelligence}$$
  without human intervention, while maintaining persistent audit records of all lifecycle transitions.
- **Files / Modules Affected**:
  - `backend/app/models/domain.py`
  - `backend/app/services/autonomous_intelligence_service.py`
  - `backend/app/services/pipeline_service.py`
  - `backend/app/tasks/maintenance_tasks.py`
  - `backend/app/api/v1/endpoints/events.py`
  - `tests/test_proactive_intelligence_pipeline.py`
- **API Changes**:
  - Enrich event responses with `lifecycle_state` and transition audit trail.
  - Provide `/api/v1/events/{event_id}/lifecycle` endpoint returning full transition history.
- **DB Changes**:
  - Add `incident_lifecycle_transitions` table: `id`, `event_id`, `incident_id`, `from_state`, `to_state`, `subsystem`, `rationale`, `correlation_id`, `created_at`, `meta_info`.
  - Add `lifecycle_state` column to `thermal_events` (indexed).
  - Add foreign key index on `thermal_detections.event_id`.
  - Add compound index on `thermal_detections(latitude, longitude, acq_timestamp)`.
- **UI Changes**: None in WP1 (backend and data plane foundation).
- **Tests**:
  - `tests/test_proactive_intelligence_pipeline.py` verifying the full 8-stage lifecycle.
  - Regression testing across `test_phase10_live_ingestion.py`, `test_database_configuration.py`.
- **Acceptance Criteria**:
  1. Ingestion of raw observations creates stored detections, clusters, features, ML predictions, and risk scores automatically.
  2. All lifecycle transitions (`OBSERVED` through `REQUIRES_HUMAN_VERIFICATION`) are persisted in PostgreSQL table `incident_lifecycle_transitions`.
  3. Strict safety gate is preserved: `ENABLE_OPERATIONAL_DISPATCH_GATE = False` and `dispatch_blocked = True`.
  4. Deduplication is idempotent: repeated batch ingestion produces zero duplicate events.
- **Rollback Strategy**: Git revert on `development/post-freeze-intelligence-hardening`; drop `incident_lifecycle_transitions` table via backward-compatible migration.

---

## Work Package 2: JARVIS Observer + Dynamic Orchestration (WP2)

- **Status**: QUEUED (Next Package)
- **Objective**: Connect the Single Master JARVIS Agent to the proactive intelligence event engine. Enable JARVIS to observe intelligence state changes, dynamically select real capabilities, integrate the actual Next-Best-Evidence engine, and persist investigation workspaces.
- **Files / Modules Affected**:
  - `backend/app/services/jarvis/jarvis_agentic_orchestrator.py`
  - `backend/app/services/jarvis/jarvis_workspace.py`
  - `backend/app/services/intelligence/next_best_evidence.py`
  - `backend/app/services/intelligence/cross_modal_engine.py`
  - `backend/app/models/domain.py` (`InvestigationWorkspace`)
  - `tests/test_jarvis_autonomous_orchestration.py`
- **API Changes**:
  - `/api/v1/jarvis/investigations` list and retrieval endpoints.
  - Structured epistemic uncertainty breakdown in mission summaries.
- **DB Changes**:
  - Wire persistence of autonomous investigation missions to `investigation_workspaces` table.
- **UI Changes**:
  - Update JARVIS Mission Workspace view to display persistent historical missions.
- **Tests**:
  - Dynamic capability selection tests under conditions A, B, C, D, E.
  - Verification that mock strings are eliminated and real Next-Best-Evidence recommendations are produced.
- **Acceptance Criteria**:
  1. JARVIS automatically receives outcomes from `AutonomousIntelligenceCore`.
  2. Capabilities dynamically generate evidence without hardcoded mock templates.
  3. Investigation missions are persisted to the database and retrievable after process restart.
- **Rollback Strategy**: Revert orchestrator modifications to point-in-time branch commit.

---

## Work Package 3: Historical Intelligence Expansion (WP3)

- **Status**: QUEUED
- **Objective**: Harmonize historical baseline modeling across `FacilityBaseline` and `HistoricalBaseline`, optimize longitudinal lookback queries, and eliminate N+1 queries during historical comparisons.
- **Files / Modules Affected**:
  - `backend/app/models/domain.py`
  - `backend/app/services/baseline_service.py`
  - `backend/app/services/intelligence/historical_comparison_engine.py`
  - `backend/app/api/v1/endpoints/historical.py`
  - `tests/test_phase25_unified_historical_intelligence.py`
- **API Changes**:
  - Unified historical comparison payload format with guaranteed point-in-time safety ($T < T_{obs}$).
- **DB Changes**:
  - Database view or unified query layer reconciling `historical_baselines` and `facility_baselines`.
- **UI Changes**:
  - Ensure Historical Intelligence Panel correctly displays both facility and grid baselines.
- **Tests**:
  - Zero temporal leakage validation tests.
  - Multi-year lookback performance benchmark.
- **Acceptance Criteria**:
  1. Single authoritative entry point for baseline queries across all services.
  2. Point-in-time safe calculations with zero future data leakage.
- **Rollback Strategy**: Git commit revert; baseline queries remain backward-compatible.

---

## Work Package 4: ML Lifecycle + Model Quality Hardening (WP4)

- **Status**: QUEUED
- **Objective**: Unify the entire platform under the champion classifier `xgb-v3.0-real-candidate`, resolve NumPy 2.5 deserialization warnings, implement batched SHAP TreeExplainer evaluation, and formalize candidate model registration.
- **Files / Modules Affected**:
  - `ml/inference/production_inference_service.py`
  - `ml/inference/predictor.py`
  - `ml/inference/explainer.py`
  - `ml/models/` artifacts
  - `tests/test_phase9_production_inference.py`
- **API Changes**:
  - Explicit model version and calibrator metadata returned in `/api/v1/ml/predict`.
- **DB Changes**: None.
- **UI Changes**: None.
- **Tests**:
  - Reproducibility test for model loading and inference.
  - SHAP batching performance benchmarks.
- **Acceptance Criteria**:
  1. `predictor.py` is deprecated; all inference runs through `production_thermal_predictor`.
  2. Zero deprecation warnings during model artifact loading.
  3. Batched SHAP evaluation reduces inference latency by at least 50% on batches > 50 events.
- **Rollback Strategy**: Revert model service bindings.

---

## Work Package 5: Data Ingestion + Industrial Sensor Interfaces (WP5)

- **Status**: QUEUED
- **Objective**: Implement secure HMAC-authenticated industrial SCADA / flare-meter webhook receiver and add an ISRO EOS-04 (RISAT-1A) SAR STAC metadata adapter.
- **Files / Modules Affected**:
  - `backend/app/api/v1/endpoints/ingestion.py`
  - `data_pipeline/adapters/eos04_adapter.py`
  - `backend/app/models/domain.py`
  - `tests/test_scada_ingestion.py`
- **API Changes**:
  - `POST /api/v1/ingestion/scada/webhook` with HMAC-SHA256 signature verification.
- **DB Changes**:
  - Add `scada_telemetry_logs` table for storing flare flow rates, pressure, and relief logs.
- **UI Changes**:
  - Add SCADA status indicator in Data Truth / Providers dashboard.
- **Tests**:
  - Webhook authentication, payload validation, and replay defense tests.
  - EOS-04 STAC parser tests.
- **Acceptance Criteria**:
  1. Authenticated webhook accepts valid flare telemetry and rejects unauthorized/tampered packets.
  2. Telemetry integrates into evidence graph as high-confidence ground truth.
- **Rollback Strategy**: Drop webhook route and associated database table.

---

## Work Package 6: Resilience + Observability (WP6)

- **Status**: QUEUED
- **Objective**: Add 3-state Circuit Breakers to external remote sensing APIs (NASA FIRMS, STAC), propagate correlation and inference IDs across all loggers, export Prometheus operational metrics, and implement bounded rate limiting.
- **Files / Modules Affected**:
  - `backend/app/core/middleware.py`
  - `backend/app/core/logging_config.py`
  - `data_pipeline/adapters/firms_adapter.py`
  - `backend/app/api/v1/endpoints/health.py`
  - `tests/test_phase15_security_resilience.py`
- **API Changes**:
  - `/health/metrics` endpoint exposing Prometheus metrics.
- **DB Changes**: None.
- **UI Changes**: None.
- **Tests**:
  - Failure injection tests (NASA API timeout, DB disconnection, worker stall).
- **Acceptance Criteria**:
  1. Circuit breaker trips after 5 consecutive failures and recovers via half-open probe.
  2. In-memory rate limiter features LRU eviction preventing memory leaks.
- **Rollback Strategy**: Git commit revert of middleware and adapter wrappers.

---

## Work Package 7: GIS / Data Performance (WP7)

- **Status**: QUEUED
- **Objective**: Accelerate geospatial operations by adding PostGIS spatial indexes, implementing MapLibre client-side clustering for high-density layers, and optimizing the facility spatial distance lookup using SciPy KDTree.
- **Files / Modules Affected**:
  - `backend/app/services/spatial_engine.py`
  - `frontend/src/components/map/MapLibreView.tsx`
  - `backend/app/api/v1/endpoints/gis.py`
  - `tests/test_geospatial_pipeline.py`
- **API Changes**:
  - Zoom-dependent bounding box filtering for vector endpoints.
- **DB Changes**:
  - Spatial indexes (`GIST`) on geometry columns in PostgreSQL.
- **UI Changes**:
  - Enable point clustering on thermal events and industrial facilities in MapLibre GL.
- **Tests**:
  - Spatial query execution speed benchmark.
  - Map rendering FPS verification.
- **Acceptance Criteria**:
  1. Facility distance lookup executes in under 5ms per event (down from 150ms).
  2. MapLibre smoothly renders national views without browser tab freezing.
- **Rollback Strategy**: Git revert of map components and spatial engine index.

---

## Work Package 8: Security + Deep Testing (WP8)

- **Status**: QUEUED
- **Objective**: Resolve the `Permissions-Policy` microphone header conflict for JARVIS voice commands, enforce JWT token revocation, isolate AGNI-SAT simulation records via `is_simulation` flag, and implement comprehensive automated test suites including frontend testing.
- **Files / Modules Affected**:
  - `backend/app/core/middleware.py`
  - `backend/app/core/security.py`
  - `backend/app/services/satellite_simulator.py`
  - `backend/app/models/domain.py`
  - `frontend/package.json`
  - `tests/`
- **API Changes**:
  - Exclude `is_simulation=True` events from operational queries unless explicitly requested.
- **DB Changes**:
  - Add `is_simulation` column to `thermal_events`.
- **UI Changes**:
  - Visual simulation badge for AGNI-SAT scenario records in Dossier.
- **Tests**:
  - Full end-to-end regression test suite covering all phases.
  - Frontend component smoke test suite via Vitest.
- **Acceptance Criteria**:
  1. JARVIS voice input functions without browser permissions denial.
  2. AGNI-SAT scenarios never contaminate production statistics or operational alerts.
  3. All 1,120+ backend tests and all new frontend tests pass cleanly.
- **Rollback Strategy**: Git commit revert.

---

## Invariant Verification Matrix

| Program Invariant | Enforcing Mechanism | Verification Gate |
|---|---|---|
| **India-First Sovereign Boundary** | Geodetic boundary envelope `(6.0-38.0 N, 68.0-98.0 E)` + territorial polygon clipping | `test_sovereignty.py` |
| **Operational Dispatch Gate** | `ENABLE_OPERATIONAL_DISPATCH_GATE = False` hardcoded in config & service layers | `test_rbac_access.py` |
| **Model Activation Frozen** | `ENABLE_AUTOMATED_MODEL_ACTIVATION = False` in config | `test_model_registry.py` |
| **Single Master JARVIS Agent** | Orchestrator singleton pattern without agent swarms or AGI claims | `verify_master_agent.py` |
| **Zero Synthetic Data Substitution** | Every missing provider declared `NOT CONFIGURED` / `MISSING` | `test_data_truth.py` |
| **AGNI-SAT Digital Twin Isolation** | `is_simulation = True` isolation flag on all simulated records | `test_agni_sat.py` |

*End of Development Roadmap.*
