# AGNI-NETRA — WP6 JARVIS Comprehensive Subsystem Audit

**Execution Context:** Post-Freeze Intelligence Hardening (Phase 26 Baseline: `eb7824e6e58eb61f376a4dadb804984950f624e8`)  
**Audit Scope:** `backend/app/services/jarvis/`, REST endpoints, workspace management, tool registry, evidence graph, multi-event correlation, dossier generation, voice interface, model provenance, and geographic boundaries.  
**Taxonomy Categories:** `IMPLEMENTED`, `VERIFIED`, `PARTIAL`, `DEGRADED`, `MISSING`, `SIMULATED`, `NOT CONFIGURED`, `FUTURE`, `OUT OF SCOPE`.

---

## 1. Executive Summary

JARVIS operates as an **orchestration, reasoning, explanation, and voice interaction layer** above the AGNI-NETRA intelligence core. The primary purpose of this audit is to rigorously inspect every component of the JARVIS subsystem, verify architectural invariants, eliminate legacy ambiguities (such as referring to capabilities as "specialist agents"), and confirm that JARVIS does not generate synthetic observations, bypass safety gates, or replace deterministic computational engines.

```
USER / SATELLITE EVENT
          ↓
[INTENT & OBJECTIVE NORMALIZATION] (Sovereign Geographic Scope Validation)
          ↓
[STRUCTURED INTELLIGENCE CONTEXT] (Consumes computed detections, risks, baselines)
          ↓
[DYNAMIC CAPABILITY SELECTION] (17 Governed, Typed Capabilities)
          ↓
[DATA RETRIEVAL & BOUNDED EXECUTION] (Budget limits, No infinite loops)
          ↓
[EPISTEMIC EVIDENCE FUSION] (Observed, Derived, Inferred, Unknown, Missing, Conflicting)
          ↓
[REASONING & COMPETING HYPOTHESES] (Richards Heuer ACH, Next-Best-Evidence)
          ↓
[BOUNDED STOPPING EVALUATION] (Budget, Sufficiency, Objective Satisfaction)
          ↓
[STRUCTURED RESPONSE / SPOKEN OUTPUT] (Voice interface, Operational Console)
```

---

## 2. Component-by-Component Canonical Audit

| Component / File | Functional Responsibility | Audit Status | Canonical Findings & Hardening Requirements |
| :--- | :--- | :---: | :--- |
| **`jarvis_agentic_orchestrator.py`** | Master event-driven observer & manual mission runner. | `VERIFIED` | Subscribes to `autonomous_intelligence_core`. Enforces single-master invariant. Prevents background swarms. Requires explicit integration with unified capability registry and structured context. |
| **`jarvis_orchestrator.py`** | Legacy command execution orchestrator & working memory. | `IMPLEMENTED` | Contains extensive command parsing and execution tracing. Operates as internal routing mechanism. Requires alignment with unified epistemic reasoning engine. |
| **`jarvis_capability_registry.py`** (WP6) | Catalog of 17 typed, permission-gated capabilities. | `IMPLEMENTED` (New) | Provides canonical capability schemas, latency expectations, epistemic mapping, and failure fallback behaviors. |
| **`jarvis_tools.py`** | Controlled deterministic tool implementations. | `VERIFIED` | Wraps underlying PostGIS spatial engine, ML predictor, anomaly engine, and baseline engine. Zero hallucinations; all queries execute against real database tables. |
| **`jarvis_mission_service.py`** | Governed mission runner with objective normalizer. | `VERIFIED` | Enforces Survey of India / LGD boundary checks, 5-factor risk, and 4-factor priority formulas. Blocks operational dispatch and automated model activation. |
| **`jarvis_workspace.py`** | Persistent investigation workspace & case management. | `VERIFIED` | Persists `InvestigationWorkspace` to PostgreSQL/SQLite. Tracks candidate sets, evidence reviews, open/resolved questions, and stopping conditions. Survives service restarts. |
| **`jarvis_voice_service.py`** | Speech transcript resolution & spoken response synthesis. | `VERIFIED` | Processes STT transcripts, triggers governed investigations, synthesizes spoken summaries, and manages proactive notifications with cooldowns. |
| **`jarvis_world_state.py`** | Real-time situational awareness summary across India. | `VERIFIED` | Compiles active event queues, state-wise breakdowns, high-risk thermal clusters, and attention items directly from database. |
| **`jarvis_command_interpreter.py`** | Natural language intent parsing and entity extraction. | `IMPLEMENTED` | Maps analyst phrases to structured command intents (`INVESTIGATE`, `SITUATION`, `FACILITY_CHECK`). Blocks SQL injection, prompt injection, and database mutations. |
| **`jarvis_evidence_fusion.py`** | Multi-source evidence evaluation and weighting. | `VERIFIED` | Fuses satellite telemetry, spatial buffers, ML predictions, and temporal baselines into an epistemic evidence record. |
| **`jarvis_specialists.py`** | Internal capability wrappers (Geo, ML, Anomaly, Risk, Sat). | `IMPLEMENTED` | Historically labeled "Specialist Agents", but operates strictly as synchronous capability functions under the single master orchestrator. No autonomous sub-agents spawned. |
| **`jarvis_guardian.py`** | Security gate & RBAC enforcement. | `VERIFIED` | Enforces permissions across roles (`ADMIN`, `ANALYST`, `AGENCY`, `RESEARCHER`, `INDUSTRY`, `PUBLIC`). Blocks unauthorized tools. |
| **`jarvis_policy.py`** | Operational boundaries and stopping thresholds. | `VERIFIED` | Governs maximum investigation depth, confidence cutoffs, and cooldown windows. |
| **`jarvis_memory.py`** | Ephemeral session memory and context continuity. | `VERIFIED` | Binds active analyst sessions to recent query history and active investigation workspaces. |
| **`jarvis_situational_service.py`** | 60-second brief, analyst brief, and India situation briefs. | `VERIFIED` | Builds structured briefings from live database records without generic LLM summarization. |
| **`jarvis_intelligence_depth.py`** | Deep multi-perspective investigation analysis. | `VERIFIED` | Decomposes complex investigations into spatial, temporal, physical, and historical dimensions. |
| **`jarvis_phase18_service.py`** | India-first geographic validation & territorial intelligence. | `VERIFIED` | Validates Survey of India coordinates and flags out-of-domain foreign points. |
| **`jarvis_phase19_service.py`** | Deep cadastral and mineral intelligence integration. | `VERIFIED` | Correlates thermal events with IBM mining leases, CEA thermal power stations, and PARIVESH clearances. |
| **`jarvis_phase20_service.py`** | Multi-criteria operational validation and compliance checks. | `VERIFIED` | Audits evidence completeness and confirms human-in-the-loop verification status. |

---

## 3. End-to-End Operational Lifecycle Trace

Every JARVIS interaction strictly follows a deterministic 9-stage operational lifecycle:

### Stage 1: Ingestion & Intent Recognition
- **Input:** Analyst natural language text, voice transcript, or autonomous event trigger from `autonomous_intelligence_core`.
- **Parsing:** Normalized by `JarvisObjectiveNormalizer` or `command_interpreter`.
- **Validation:** Prompt injection filtering, SQL keyword blocking, and sovereign boundary check (classifying location into `EXPLICIT_USER_LOCATION`, `RESOLVED_LOCATION`, `AUTHORITATIVE_GIS_LOCATION`, `UNKNOWN_LOCATION`, or `OUT_OF_DOMAIN_LOCATION`).

### Stage 2: Structured Intelligence Context Assembly
- **Context Construction:** Assembles `StructuredIntelligenceContext` directly from AGNI-NETRA databases:
  - Event telemetry (latitude, longitude, brightness, FRP, sensor, satellite, timestamp).
  - PostGIS administrative containment (State, District, Subdistrict).
  - Computed ML inference (`xgb-v3.0-real-candidate`) with calibrated probability.
  - Model provenance metadata (SHA-256 hash, candidate status, calibration version).
  - Frozen 5-factor risk score and 4-factor priority score.
  - Historical baseline (mean FRP, standard deviation, abnormality sigma).
  - Data freshness status (`CURRENT`, `STALE`, `DEGRADED`, `FAILED`, `UNKNOWN`).

### Stage 3: Governed Capability Selection
- Dynamic evaluation of missing intelligence dimensions.
- If spatial proximity is missing $\to$ selects `GET_SPATIAL_CONTEXT`.
- If historical comparison is missing $\to$ selects `GET_HISTORICAL_BASELINE`.
- If explainability is missing $\to$ selects `GET_SHAP_EXPLANATION`.
- If facility correlation is missing $\to$ selects `GET_INDUSTRIAL_CONTEXT` or `GET_POWER_CONTEXT`.

### Stage 4: Governed Execution with Budget Limits
- Execution managed by `JarvisReasoningEngine`.
- Enforces strict investigation budget:
  - Maximum capability calls: 10
  - Maximum repeated calls per capability: 2
  - Execution timeout: 15.0 seconds
  - Recursion depth: 0 (Strictly disallowed from spawning subagents)

### Stage 5: Epistemic Evidence Categorization
Every piece of gathered intelligence is mapped to an explicit epistemic category:
- **OBSERVED:** Direct physical satellite sensor observations (brightness, FRP, coordinates).
- **DERIVED:** Deterministic calculations (PostGIS distances, 5-factor risk, baseline sigma).
- **INFERRED:** Probabilistic candidate model predictions and SHAP attribution.
- **UNKNOWN:** Uncataloged facilities or unobserved parameters.
- **MISSING:** Feeds or providers currently unconfigured (e.g. SCADA, on-site sensors).
- **CONFLICTING:** Mutually inconsistent indicators (e.g. agricultural classification inside heavy industrial park).

### Stage 6: Analysis of Competing Hypotheses (ACH)
- Evaluates 7 canonical operational hypotheses:
  1. `INDUSTRIAL_FIRE`: High FRP, persistent, inside industrial buffer, high calibrated probability.
  2. `GAS_FLARE`: Recurring, elevated night/day ratio, near petrochemical facility, moderate FRP.
  3. `FOREST_FIRE`: Forest land cover, low historical baseline, rapid spread vector.
  4. `AGRICULTURAL_BURNING`: Seasonal peak, crop residue signature, rural agricultural zone.
  5. `MINING_ACTIVITY`: Within or adjacent to IBM lease boundary, heavy excavation context.
  6. `OTHER_THERMAL_SOURCE`: Brick kiln cluster, municipal landfill, biomass processing.
  7. `UNCERTAIN_CLASSIFICATION`: Contradictory or insufficient evidence; low confidence margin.
- Tracks supporting, contradicting, and missing evidence for each hypothesis. Does NOT force a winning hypothesis when evidence is inconclusive.

### Stage 7: Next-Best-Evidence Determination
- Identifies the highest-utility missing information item that would resolve remaining ambiguity.
- Explains *what* is missing, *why* it matters, and *which* governed capability or external sensor would provide it.

### Stage 8: Bounded Stopping Evaluation
The investigation halts if:
1. `EVIDENCE_SUFFICIENT`: Leading hypothesis supported with high confidence and minimal contradiction.
2. `OBJECTIVE_SATISFIED`: Analyst-specified query has been completely answered.
3. `NO_FURTHER_CAPABILITY`: All relevant capabilities executed; remaining gaps require external or unconfigured data.
4. `BUDGET_EXHAUSTED`: Governed limit (10 calls or timeout) reached.
5. `REQUIRED_EVIDENCE_UNAVAILABLE`: Critical data provider degraded or offline.

### Stage 9: Response Synthesis & Workspace Persistence
- **Response Contract:** Generates structured response object embedding `intent`, `summary`, `facts` (Observed), `derived_findings` (Derived), `inferences` (Inferred), `uncertainties` (Unknown/Conflicting), `missing_evidence` (Missing), `recommendations`, `citations`, `model_provenance`, `verification_state`, and `stop_reason`.
- **Spoken Text:** Generates concise, grounded narrative for voice synthesizer.
- **Persistence:** Updates or creates `InvestigationWorkspace` in PostgreSQL/SQLite for state recovery and auditability.

---

## 4. Operational Invariant Verification

| Invariant | Requirement | Audit Finding |
| :--- | :--- | :--- |
| **Single Master Orchestrator** | Exactly ONE user-facing agent. Zero autonomous subagents. | **VERIFIED:** Single master orchestrator controls all flows. Specialist classes are synchronous functional wrappers. |
| **AGNI-NETRA Independence** | Core pipeline functions if JARVIS is offline. | **VERIFIED:** Ingestion, clustering, classification, risk, and alerts execute independently via `autonomous_intelligence_core`. |
| **Operational Dispatch Gate** | `ENABLE_OPERATIONAL_DISPATCH_GATE = False` permanently enforced. | **VERIFIED:** Hardcoded constant enforced at guardian, orchestrator, and schema layers. Physical dispatch is completely blocked. |
| **Automated Model Activation** | `ENABLE_AUTOMATED_MODEL_ACTIVATION = False` permanently enforced. | **VERIFIED:** Candidate models cannot self-promote. Model promotion strictly requires human `ADMIN` authorization. |
| **Zero Synthetic Substitution** | No fabricated telemetry or simulated ground truth. | **VERIFIED:** Real NASA FIRMS data, real PostGIS spatial tables (35,570 facilities, 7,595 boundaries), and real 6-year baseline archive. |
| **Sovereign India Scope** | Rejection of foreign locations and coordinates. | **VERIFIED:** Rejects points outside Survey of India boundary (`OUT_OF_DOMAIN_LOCATION`). Foreign textual queries (e.g. Lahore) safely rejected. |

---

## 5. Audit Conclusion & WP6 Action Plan

The JARVIS architecture is fundamentally solid, highly capable, and free of autonomous agent swarm sprawl. To complete WP6 hardening to the highest production standard:
1. Formalize the 17-capability registry in [`backend/app/services/jarvis/jarvis_capability_registry.py`](file:///e:/PROJECTS/AGNI-NETRA/backend/app/services/jarvis/jarvis_capability_registry.py).
2. Author the explicit `StructuredIntelligenceContext` dataclass in [`backend/app/models/jarvis_context.py`](file:///e:/PROJECTS/AGNI-NETRA/backend/app/models/jarvis_context.py).
3. Author the unified `JarvisReasoningEngine` in [`backend/app/services/jarvis/jarvis_reasoning_engine.py`](file:///e:/PROJECTS/AGNI-NETRA/backend/app/services/jarvis/jarvis_reasoning_engine.py) implementing 6-way epistemic grounding, 7-hypothesis ACH, next-best-evidence, and bounded stopping.
4. Strengthen `jarvis_agentic_orchestrator.py` and `jarvis_voice_service.py` to leverage the unified reasoning engine.
5. Create comprehensive 35-scenario test suite (`tests/test_wp6_jarvis_reasoning.py`) and performance benchmarks.
