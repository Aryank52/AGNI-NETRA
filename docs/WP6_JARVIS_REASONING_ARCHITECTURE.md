# AGNI-NETRA — WP6 JARVIS Reasoning & Orchestration Architecture

**Execution Context:** Post-Freeze Intelligence Hardening (Base: Phase 26 `eb7824e6e58eb61f376a4dadb804984950f624e8` + WP1–WP5)  
**Document Purpose:** Defines the formal architectural specification for the Single-Master JARVIS Reasoning Engine, Epistemic Evidence Framework, Analysis of Competing Hypotheses (ACH), and Bounded Stopping Policy.

---

## 1. Architectural Separation of Concerns

AGNI-NETRA strictly maintains an immutable hierarchy between computed intelligence and synthetic operational reasoning:

```
+-----------------------------------------------------------------------------------+
|                        JARVIS REASONING & ORCHESTRATION LAYER                     |
|                                                                                   |
|   +---------------------------------------------------------------------------+   |
|   |                        SINGLE MASTER ORCHESTRATOR                         |   |
|   |   - Intent Parsing & Geographic Normalization                            |   |
|   |   - Epistemic Evidence Classification (Observed / Derived / Inferred)     |   |
|   |   - Richards Heuer Analysis of Competing Hypotheses (ACH)                 |   |
|   |   - Next-Best-Evidence Determination                                      |   |
|   |   - Bounded Stopping Policy (Budget, Sufficiency, Timeout)                |   |
|   |   - Voice Speech-to-Text & Grounded Spoken Response Synthesis            |   |
|   +-------------------------------------+-------------------------------------+   |
|                                         |                                         |
|                       DYNAMIC CAPABILITY INVOCATION                               |
|                                         |                                         |
+-----------------------------------------v-----------------------------------------+
|                       AGNI-NETRA COMPUTED INTELLIGENCE CORE                       |
|                                                                                   |
|   +-----------------------+ +-----------------------+ +-----------------------+   |
|   |   SATELLITE SENSORS   | |     POSTGIS CADASTRAL  | |    CANDIDATE ML ENGINE  |   |
|   | - NASA FIRMS VIIRS    | | - 7,595 Admin Polygons| | - xgb-v3.0 (Calibrated) |   |
|   | - NOAA-20 / SNPP / MOD| | - 35,570 Facilities   | | - Platt Calibrator    |   |
|   | - Spatial Clustering  | | - Multi-Buffer Proxim.| | - TreeExplainer SHAP  |   |
|   +-----------------------+ +-----------------------+ +-----------------------+   |
|   +-----------------------+ +-----------------------+ +-----------------------+   |
|   |  HISTORICAL BASELINE  | |   RISK & PRIORITY     | |   DATA PLANE ENGINE   |   |
|   | - 6-Year Archive      | | - Frozen 5-Factor Risk| | - Freshness Monitor   |   |
|   | - 8.22M Detections    | | - Frozen 4-Factor Prio| | - Coverage Matrix     |   |
|   | - Abnormality Sigma   | | - Human Queue (HITL)  | | - Ingestion Gate      |   |
|   +-----------------------+ +-----------------------+ +-----------------------+   |
+-----------------------------------------------------------------------------------+
```

### Invariant Rules:
1. **Source of Computed Truth:** AGNI-NETRA is the sole authority for physical detections, coordinates, spatial containment, risk scores, priority ratings, and ML predictions. JARVIS *never* re-computes or fabricates these values.
2. **Epistemic Honesty:** JARVIS *never* presents an inferred model output as an observed physical fact, nor does it convert correlation into causation.
3. **Safety Locks:**
   - `ENABLE_OPERATIONAL_DISPATCH_GATE = False` (JARVIS cannot dispatch emergency units).
   - `ENABLE_AUTOMATED_MODEL_ACTIVATION = False` (JARVIS cannot promote candidate ML models).

---

## 2. Single-Master Pattern vs Disallowed Swarms

| System Attribute | Disallowed Generic Agent Swarm | AGNI-NETRA Single Master JARVIS |
| :--- | :--- | :--- |
| **Agent Topology** | Autonomous sub-agents spawning other agents recursively. | **Exactly ONE master orchestrator.** Zero sub-agents spawned. |
| **Execution Path** | Non-deterministic delegation chains and message queues. | **Deterministic capability execution** with fixed budget limits. |
| **Tool Execution** | Arbitrary shell, Python execution, or unrestricted APIs. | **Strictly typed, permission-gated capability registry.** |
| **Stopping Behavior**| Often loops indefinitely or exhausts prompt token limits. | **Explicit bounded stopping** evaluated after every capability call. |
| **State Persistence**| Ephemeral in-memory context easily lost on crash. | **Relational DB persistence** (`investigation_workspaces` table). |

---

## 3. The 17 Governed Capabilities

All capabilities adhere to the `JarvisCapability` specification:
$$\text{Capability} = \langle \text{ID}, \text{Name}, \text{InputSchema}, \text{OutputSchema}, \text{Permissions}, \text{DataSources}, \text{LatencyMs}, \text{SideEffects}, \text{EpistemicType}, \text{Fallback} \rangle$$

```
1.  GET_EVENT                    -> Authoritative event record & sensor telemetry
2.  GET_HISTORICAL_BASELINE      -> 6-year multi-sensor baseline & sigma deviation
3.  GET_SPATIAL_CONTEXT          -> PostGIS cadastral proximity (OSM, CEA, IBM)
4.  GET_INDUSTRIAL_CONTEXT       -> Facility name, industry sector, fuel, compliance
5.  GET_POWER_CONTEXT            -> CEA power station matching & MW capacity
6.  GET_MINING_CONTEXT           -> IBM lease status, mineral type, lease buffer
7.  GET_LULC_CONTEXT             -> Bhuvan LULC land use / land cover category
8.  GET_PROTECTED_AREA_CONTEXT   -> FSI forest classification, national parks buffer
9.  GET_MODEL_PREDICTION         -> Calibrated candidate XGBoost prediction
10. GET_MODEL_PROVENANCE         -> Model version, SHA-256 hash, candidate status
11. GET_SHAP_EXPLANATION         -> TreeExplainer feature attribution drivers
12. GET_ANOMALY_SCORE            -> Isolation forest radar & anomaly score
13. GET_RISK                     -> Frozen 5-factor risk score & level
14. GET_PRIORITY                 -> Frozen 4-factor operational priority rating
15. GET_VERIFICATION_HISTORY     -> On-site inspection logs and analyst reviews
16. CORRELATE_EVENTS             -> Multi-event spatial-temporal clustering
17. GENERATE_DOSSIER             -> 7-dimension operational dossier with SHA-256
```

---

## 4. Structured Intelligence Context

JARVIS operates on a strongly typed context object (`StructuredIntelligenceContext`), avoiding repeated database queries and ensuring idempotency:

```python
@dataclass
class StructuredIntelligenceContext:
    event_id: str
    incident_id: Optional[str]
    latitude: float
    longitude: float
    state: str
    district: Optional[str]
    location_category: str        # EXPLICIT_USER_LOCATION, AUTHORITATIVE_GIS, OUT_OF_DOMAIN
    predicted_class: str
    confidence: float
    calibrated_confidence: float
    model_provenance: Dict[str, Any]
    risk_score: float
    risk_level: str
    priority_score: float
    anomaly_score: float
    historical_context: Dict[str, Any]
    spatial_context: Dict[str, Any]
    evidence_graph: Dict[str, Any]
    epistemic_uncertainty: str    # RESOLVED, UNCERTAIN, CONFLICTING, MISSING_DATA
    verification_state: str       # NOT_REQUIRED, REQUIRES_HUMAN_REVIEW, VERIFIED, REJECTED
    data_freshness: str           # CURRENT, STALE, DEGRADED, FAILED, UNKNOWN
    source_health: Dict[str, Any]
```

---

## 5. The 6-Way Epistemic Framework

To maintain scientific defensibility, all intelligence elements are segregated into six explicit categories:

1. **`OBSERVED`**: Physical measurements from calibrated satellite instruments.
   - Examples: Brightness temperature ($355.0\text{ K}$), FRP ($125.4\text{ MW}$), VIIRS coordinate $[22.4707, 70.0577]$.
2. **`DERIVED`**: Deterministic computations using verified formulas or spatial algorithms.
   - Examples: PostGIS distance to boundary ($181.9\text{ m}$), 5-factor risk score ($78.4$), baseline deviation ($+3.2\sigma$).
3. **`INFERRED`**: Probabilistic estimates produced by machine learning models.
   - Examples: XGBoost candidate prediction (`Industrial Flaring`), calibrated probability ($0.92$), SHAP top positive contributor (`max_frp`).
4. **`UNKNOWN`**: Aspects for which AGNI-NETRA currently lacks data or catalogs.
   - Examples: Uncataloged industrial facilities in rural clusters, exact stack height.
5. **`MISSING`**: Required information feeds that are currently unconfigured or offline.
   - Examples: Real-time plant SCADA telemetry, high-resolution optical imagery pass.
6. **`CONFLICTING`**: Evidence streams that contradict one another.
   - Examples: Satellite model infers `Agricultural Burning`, but PostGIS places the event within an active petrochemical refinery complex.

*Strict Rule: Inferred cannot be stated as Observed. Model predictions are hypotheses, never confirmed physical facts without human on-site verification.*

---

## 6. Richards Heuer Analysis of Competing Hypotheses (ACH)

For every significant investigation, JARVIS constructs an ACH evaluation matrix evaluating 7 canonical operational hypotheses:

| Hypothesis ID | Operational Meaning | Diagnostic Supporting Indicators | Inconsistent / Contradicting Indicators |
| :--- | :--- | :--- | :--- |
| **`INDUSTRIAL_FIRE`** | Uncontrolled accidental fire at facility | Persistent high FRP, industrial buffer $< 500\text{m}$, daytime or sudden night spike, non-flaring asset | Agricultural LULC, baseline flaring pattern, low FRP |
| **`GAS_FLARE`** | Routine or process upset flaring | Recurring night/day ratio, petrochemical/refinery buffer $< 200\text{m}$, historical baseline flaring | Forest LULC, remote mining pit, zero industrial proximity |
| **`FOREST_FIRE`** | Wildfire in forested or wilderness terrain | FSI forest cover $> 40\%$, rapid spreading perimeter, zero industrial assets | Urban industrial park, continuous single-point flaring |
| **`AGRICULTURAL_BURNING`** | Crop residue burning (stubble) | Bhuvan agricultural LULC, post-harvest season, low persistence, multiple dispersed points | Petrochemical complex, sub-zero winter non-harvest |
| **`MINING_ACTIVITY`** | Blasting, overburden fire, equipment heat | Inside or adjacent to IBM lease boundary, mining LULC, active excavation status | Marine coastal waters, protected wildlife sanctuary |
| **`OTHER_THERMAL`** | Brick kiln, municipal solid waste, biomass | Brick kiln cluster polygon, municipal landfill boundary, moderate intermittent FRP | Heavy refinery flare stack, deep forest |
| **`UNCERTAIN`** | Inconclusive or conflicting evidence | High classification entropy, conflicting spatial vs spectral indicators | High confidence with zero contradictions |

---

## 7. Next-Best-Evidence Formulation

When an investigation terminates with residual uncertainty ($\text{Tier} \ne \text{RESOLVED}$), JARVIS generates targeted, prioritized information recommendations:
1. **Identify Missing Data:** Evaluates unconfigured or missing data providers (SCADA, high-res optical, UAV inspection).
2. **Quantify Value:** Computes Expected Information Value (`HIGH`, `MEDIUM`, `LOW`).
3. **Actionable Steps:** Prescribes exact queries or analyst steps to resolve the leading hypothesis.

---

## 8. Bounded Stopping Policy & Governed Budgets

JARVIS evaluates stopping conditions after **every single capability execution**:

$$\text{Should Stop} = (\text{Budget Exhausted}) \lor (\text{Timeout}) \lor (\text{Evidence Sufficient}) \lor (\text{Objective Satisfied}) \lor (\text{No Additional Capabilities})$$

### Governed Budget Constraints:
- **`MAX_CAPABILITY_CALLS`**: $10$
- **`MAX_REPEATED_CALLS_PER_CAPABILITY`**: $2$
- **`MAX_INVESTIGATION_DURATION_SEC`**: $15.0\text{ s}$
- **`MAX_RECURSION_DEPTH`**: $0$ (Zero autonomous subagents)

Every investigation records its exact terminal state in `stop_reason`.

---

## 9. Voice Architecture & Security Boundaries

Voice interaction operates strictly as a peripheral interface to the master orchestrator:

$$\text{Microphone} \longrightarrow \text{STT Transcript} \longrightarrow \text{Intent Normalizer} \longrightarrow \text{Master Orchestrator} \longrightarrow \text{Structured Response} \longrightarrow \text{TTS Spoken Output}$$

### Security & Invariant Rules:
1. **RBAC Enforcement:** Voice commands operate under the authenticated operator's role. A voice command from role `PUBLIC` cannot access sensitive internal coordinates or audit logs.
2. **No Natural Language Database Mutation:** Commands like "Drop database", "Delete event", or "Alter table" are permanently blocked.
3. **No Safety Bypass:** Commands like "Ignore safety rules", "Dispatch fire trucks", or "Activate candidate model" are safely neutralized and reported to audit logs.
4. **Voice Failure Independence:** Complete failure of STT or TTS does not degrade underlying AGNI-NETRA intelligence or database operations.
