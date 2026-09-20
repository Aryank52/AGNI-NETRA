# AGNI-NETRA — FINAL SYSTEM INVARIANTS

**Document Version:** 1.0.0  
**Classification:** Sovereign Engineering Invariant Specification  
**Authority:** AGNI-NETRA Architectural Board  
**Target Repository:** `E:\PROJECTS\AGNI-NETRA`  
**Branch:** `development/post-freeze-intelligence-hardening`  
**Frozen Reference:** Phase 26 (`eb7824e6e58eb61f376a4dadb804984950f624e8`)  

---

## Executive Mandate

This document specifies the thirteen (13) inviolable architectural, operational, and ethical invariants governing the AGNI-NETRA sovereign industrial thermal intelligence platform and its single-master JARVIS cognitive orchestration layer.

Under no circumstances may any pull request, dependency upgrade, deployment script, user prompt, agent instruction, or runtime configuration bypass, alter, or dilute these invariants.

---

## The Thirteen Inviolable System Invariants

### Invariant 1: India-First Sovereign Geographic Domain
- **Principle:** AGNI-NETRA is strictly bounded to the sovereign territory and Exclusive Economic Zone (EEZ) of the Republic of India.
- **Enforcement:**
  - Spatial containment checks are executed against canonical, legally bounded geometries (Survey of India / SOI-compliant boundaries: EPSG:4326).
  - Out-of-bounds telemetry (e.g. coordinates outside Indian terrestrial/maritime boundaries, or in neighboring states) is automatically and irrevocably quarantined (`GEOGRAPHIC_OUT_OF_BOUNDS_QUARANTINE`).
  - No international fire detections or non-Indian industrial monitoring shall be ingested or processed into active alert queues.
- **Coordinate Conventions:**
  - Storage: EPSG:4326 (WGS 84, PostGIS `geometry(Point, 4326)`).
  - API / GeoJSON: Standard GeoJSON `[longitude, latitude]`.
  - Frontend Projection: EPSG:3857 (Web Mercator), rendered with `renderWorldCopies: false` to eliminate spurious foreign wraparound projections.

### Invariant 2: Satellite-Derived Thermal Observations Are NOT Ground Truth
- **Principle:** Thermal anomaly detections sourced from orbital sensors (MODIS, VIIRS, Sentinel-3) represent unconfirmed electromagnetic radiances, not verified industrial fires or verified ground truth.
- **Enforcement:**
  - The epistemic status of all incoming detections begins strictly as `PROVISIONAL_OBSERVATION`.
  - Raw telemetry confidence scores (e.g. NASA FIRMS 0–100 or nominal/low/high) describe sensor algorithm confidence in a thermal anomaly, not fire severity or infrastructure damage.
  - Algorithms must never designate an automated alert as a "Confirmed Incident" without secondary spatial-temporal correlation and human validation.

### Invariant 3: Human Verification Remains Authoritative
- **Principle:** Only authorized human operators (Role: `ANALYST` or `ADMIN`) possess the legal and operational authority to certify an alert into a verified `INCIDENT`.
- **Enforcement:**
  - Automated ML pipelines and cognitive systems may generate `ALERTS`, compute `CONFIDENCE`, and calculate `SEVERITY_SCORES`.
  - The lifecycle state `VERIFIED_INCIDENT` can only be transitioned via an authenticated operator workflow with immutable audit log attribution (`actor_id`, `timestamp`, `transition_reason`).
  - Automated suppression or automated escalation to emergency status without human review is strictly prohibited.

### Invariant 4: AGNI-NETRA Intelligence Core Operates Independently of JARVIS
- **Principle:** The deterministic intelligence core (spatial clustering, infrastructure correlation, priority scoring, ML inference, lifecycle state machine) is fully decoupled from JARVIS.
- **Enforcement:**
  - If JARVIS (reasoning engine, LLM provider, voice STT/TTS) is completely offline, crashing, or unreachable, the AGNI-NETRA ingestion engine, spatial clustering, alerting pipelines, and database persist, process, and alert without degradation.
  - JARVIS is an analytical observer and operator copilot, not the core pipeline engine.

### Invariant 5: JARVIS Is a Single Master Reasoning/Orchestration Layer
- **Principle:** There exists exactly ONE master JARVIS cognitive orchestration layer (`JARVISReasoningEngine` / `JARVISOrchestrator`).
- **Enforcement:**
  - No secondary LLM engines, autonomous background bots, or rogue inference agents are permitted.
  - All reasoning requests must traverse the single-master orchestrator with explicit correlation IDs, step bounds, and deterministic tool dispatch.
  - Reasoning paths must be grounded in real platform evidence graphs with structured provenance.

### Invariant 6: No Subagents, Swarm Orchestration, or Generic Chatbot Architecture
- **Principle:** AGNI-NETRA explicitly rejects multi-agent swarms, recursive autonomous subagents, and conversational chatbot persona degradation.
- **Enforcement:**
  - Autonomous agents spawning sub-processes or delegating tasks to external unverified agents is prohibited.
  - JARVIS does not roleplay, generate speculative fiction, hallucinate operational facts, or answer out-of-domain trivia.
  - Interactions are strictly operator-copilot workflows: evidence synthesis, incident triage, facility risk query, spatial correlation, and structured briefing.

### Invariant 7: Permanent Block on Operational Dispatch (`ENABLE_OPERATIONAL_DISPATCH_GATE = False`)
- **Principle:** AGNI-NETRA does not dispatch emergency response personnel, fire tenders, or physical actuators.
- **Enforcement:**
  - The configuration constant `ENABLE_OPERATIONAL_DISPATCH_GATE` is hardcoded to `False`.
  - Any API call, CLI invocation, or prompt attempting to invoke physical dispatch or change this flag must fail with `HTTP 403 Forbidden` / `DispatchBlockedException`.
  - No user role (including `ADMIN`) can toggle this gate at runtime.

### Invariant 8: Permanent Block on Automated Model Activation (`ENABLE_AUTOMATED_MODEL_ACTIVATION = False`)
- **Principle:** Machine learning candidate models can never be promoted or activated in production autonomously.
- **Enforcement:**
  - The configuration constant `ENABLE_AUTOMATED_MODEL_ACTIVATION` is hardcoded to `False`.
  - Promotion from `CANDIDATE` to `CHAMPION` requires an explicit, multi-stage offline governance review, bias analysis, holdout validation sign-off, and manual cryptographic registry signature.
  - Automated CI/CD pipelines or runtime heuristics are blocked from mutating `is_active = True`.

### Invariant 9: Explicit and Distinct Candidate, Champion, and Model Provenance
- **Principle:** Provenance metadata must never be conflated or misrepresented.
- **Enforcement:**
  - **Git Commit SHA** (e.g. `eb7824e...` or `4f20a71...`) identifies source code revision. It must NEVER be represented as a model artifact hash.
  - **Model Artifact SHA-256** (e.g. `c52b6369...` for `xgb_v3_real_candidate.joblib`) represents the exact cryptographic checksum of the trained weights.
  - **Dataset SHA-256** (e.g. `9677c6d6...` for `dataset_v3.2-real-final.csv`) represents the exact training data lineage.
  - If no model is certified as governed champion, systems must explicitly declare: `"No governed production champion configured"`. Systems must never claim inference uses a governed champion unless backend registry verifies `is_active = True` and `governance_status = 'CHAMPION'`.

### Invariant 10: AGNI-SAT Is a Digital Twin Simulation (Simulated Telemetry Only)
- **Principle:** AGNI-SAT is an orbital mechanics simulation and thermal payload digital twin, not an active physical constellation.
- **Enforcement:**
  - All orbital paths (SGP4/TLE propagations), simulated detector swath observations, and thermal synthetic alerts must be explicitly tagged with `provenance_type: "SIMULATED_DIGITAL_TWIN"`.
  - Simulated telemetry must never be intermingled with real NASA/ESA FIRMS satellite feeds without clear epistemic demarcation.

### Invariant 11: Provenance and Epistemic States Are Preserved
- **Principle:** Every piece of intelligence, reasoning output, and tactical alert must carry its provenance trail and epistemic certainty tag.
- **Enforcement:**
  - Epistemic states (`OBSERVED`, `DERIVED`, `CORRELATED`, `HYPOTHESIZED`, `REFUTED`, `VERIFIED`) must accompany all evidence nodes in the JARVIS graph.
  - Audit logs must preserve actor, timestamp, input parameters, evidence sources, and execution latency.
  - Deletion or truncation of historical provenance trails is prohibited.

### Invariant 12: Manual Workflows Remain Fully Available
- **Principle:** The operator UI and platform APIs must support end-to-end mission workflows manually without requiring voice, AI, or automated assistants.
- **Enforcement:**
  - Map exploration, incident filtering, facility inspection, manual alert verification, report generation, and data export must be 100% accessible via deterministic keyboard/mouse UI and standard REST APIs.
  - Voice STT/TTS and JARVIS reasoning are augmentative copilots, never mandatory blockers.

### Invariant 13: External Consequential Actions Require Explicit Human Authorization
- **Principle:** Any action that affects external systems, triggers inter-agency notifications, or modifies critical infrastructure metadata requires dual-check human authorization.
- **Enforcement:**
  - Automated outbound messaging or webhooks to external defense/civil defense portals without operator review are disabled.
  - Deletion of audit logs, drop of database tables, or boundary modifications require administrative cryptographic authentication and explicit approval tokens.

---

## Architectural Sign-Off

| Domain | Invariant Enforcement Mechanism | Compliance Status |
|---|---|---|
| Geographic Domain | Spatial SOI WGS84 Geofencing (`data_pipeline/spatial_geofence.py`) | VERIFIED |
| Sensor Epistemics | Sensor Confidence Separation (`backend/app/models/event.py`) | VERIFIED |
| Human Verification | RBAC Role Gate + Audit Logger (`backend/app/services/audit.py`) | VERIFIED |
| Core Independence | Decoupled Event Pipeline Architecture | VERIFIED |
| Single Master | Single Orchestrator Architecture (`backend/app/services/jarvis/`) | VERIFIED |
| Swarm Prevention | Direct Dispatch Function Calls Only | VERIFIED |
| Dispatch Gate | `ENABLE_OPERATIONAL_DISPATCH_GATE = False` | VERIFIED |
| Model Activation Gate | `ENABLE_AUTOMATED_MODEL_ACTIVATION = False` | VERIFIED |
| Provenance Integrity | SHA-256 Cryptographic Verification (`jarvis_voice_service.py`) | VERIFIED |
| Simulation Demarcation | Digital Twin Provenance Tagging | VERIFIED |
| Epistemic Integrity | Structured Evidence Graph Schema | VERIFIED |
| Manual Fallbacks | Standalone Operational Console (`frontend/src/app/`) | VERIFIED |
| Consequential Action | Authenticated Operator Confirmation Required | VERIFIED |
