# JARVIS PHASE 12: MULTI-EVENT GLOBAL INCIDENT CORRELATION
**Platform:** AGNI-NETRA  
**Document Version:** 1.0.0  
**Status:** IMPLEMENTED & AUDITED  
**Policy Gate:** `ENABLE_OPERATIONAL_DISPATCH_GATE = False` (STRICTLY BLOCKED)  

---

## 1. Executive Architectural Summary

JARVIS Phase 12 extends AGNI-NETRA from single-event explainable intelligence into **deterministic multi-event incident correlation and episode differentiation**.

The system enables human operators and analysts to determine whether multiple thermal detections represent:
1. **The same physical incident** (continuous expanding fire front)
2. **The same operational episode** (multi-day flare-ups or shift-based industrial operations)
3. **A recurring source** (stationary flare stack, kiln, or furnace across satellite revisits)
4. **Geographically related activity** (events in the same industrial cluster or administrative unit)
5. **Temporally related activity** (concurrent detections across separate jurisdictions)
6. **Downwind-related activity** (corroborated spatial alignment with plume dispersal vector)
7. **Coordinated/synchronized activity** (deliberate or agricultural burn patterns)
8. **Independent unrelated events** (distant, coincident, or structurally separate sources)
9. **Insufficiently related events** (telemetry too sparse or ambiguous to link)

### 1.1 Frozen Architectural Baselines (Protected)
- **Phase 7 (Thermal Fusion):** Multi-provider thermal telemetry, sensor agreement, and deduplication logic remain untouched.
- **Phase 8 (Context Fusion):** Multi-domain PostGIS proximity, land-use layers, and facility registries remain untouched.
- **Phase 9 (Temporal Baselines):** Historical baselines, 5-tier persistence scoring, and zero-synthetic data requirements remain untouched.
- **Phase 10 (Environmental Fusion):** Meteorological boundary layer and plume transport logic remain untouched.
- **Phase 10.1 (Data Provenance):** Strict data origin tracking and transparency remain untouched.
- **Phase 11 & 11.1 (Evidence Graph & Baseline Integrity):** 7-class candidate hypotheses, Platt-calibrated XGBoost classifier, and authoritative 5-factor risk formula remain untouched.

---

## 2. Key Architecture Invariants & Anti-Hallucination Guarantees

1. **One Master Agent Architecture:**
   - JARVIS remains **ONE MASTER AGENT**.
   - **Zero subagents**, zero agent swarms, and zero autonomous background daemons.
   - All correlation logic executes deterministically on-demand upon operator command.

2. **Automated Dispatch Gate Invariant:**
   - `ENABLE_OPERATIONAL_DISPATCH_GATE = False` is strictly enforced.
   - Automated physical dispatch is **BLOCKED** across all correlation tiers.
   - Human-in-the-Loop (HITL) manual sign-off is mandatory before any action.

3. **Three Distinct, Unentangled Intelligence Axes:**
   - **Physical Hazard (0–100):** Authoritative 5-factor risk score ($0.30 \cdot S_{\text{intensity}} + 0.25 \cdot S_{\text{abnormality}} + 0.20 \cdot S_{\text{exposure}} + 0.15 \cdot S_{\text{persistence}} + 0.10 \cdot S_{\text{context}}$). Preserved at the event level. Never diluted or averaged across unrelated events.
   - **Classifier Probability (0.0–1.0):** Platt-calibrated XGBoost probability across 6 classes. Distinct from spatial-temporal correlation.
   - **Correlation Strength (`STRONG`, `MODERATE`, `LIMITED`, `INSUFFICIENT`):** Deterministic evaluation of spatial proximity, temporal delta, downwind alignment, and historical recurrence.

4. **Honest Spatial Labeling:**
   - Incident spatial boundaries are strictly labeled `INCIDENT_CORRELATION_ENVELOPE`.
   - Never misrepresented as a validated physical fire front or perimeter.
   - Explicit disclaimers warn operators of satellite resolution limits and gaps.

5. **Downwind Transport Corroboration:**
   - Derived spatial alignment with surface wind vectors is documented as a **correlation feature**, **never claimed as proof of direct causation or ignition**.

6. **Multi-Pass VIIRS Revisit Disambiguation:**
   - Successive satellite overpasses over an existing stationary hotspot are explicitly flagged as `SAME_SOURCE_REPETITION`, preventing false "fire growth" illusions.

---

## 3. The 9 Pairwise Relationship Types

| Relationship Type | Spatial Threshold | Temporal Threshold | Core Deterministic Logic |
| :--- | :--- | :--- | :--- |
| `SAME_PHYSICAL_INCIDENT` | $\le 1.5$ km | $\le 6$ hours | Continuous spread, high FRP, concurrent or rapid progression |
| `SAME_OPERATIONAL_EPISODE` | $\le 3.0$ km | $\le 24$ hours | Same licensed facility or industrial unit across work shifts |
| `RECURRING_SOURCE_ACTIVITY` | $\le 0.5$ km | $\ge 24$ hours | Stationary emitter detected over multiple satellite overpasses |
| `GEOGRAPHICALLY_RELATED` | $\le 10.0$ km | $> 24$ hours | Common industrial complex, mineral belt, or district boundary |
| `TEMPORALLY_RELATED` | $> 10.0$ km | $\le 6$ hours | Concurrent events in separate geographic jurisdictions |
| `DOWNWIND_HAZARD` | $\le 5.0$ km | $\le 12$ hours | Alignment within $\pm 45^\circ$ of prevailing downwind plume vector |
| `COORDINATED_SYNCHRONIZED` | $\le 15.0$ km | $\le 2$ hours | Synchronized agricultural clearing or simultaneous ignition patterns |
| `INDEPENDENT_UNRELATED` | $> 15.0$ km | $> 24$ hours | Unrelated locations, discordant timing, distinct owners |
| `INSUFFICIENTLY_RELATED` | Ambiguous | Ambiguous | Sparse telemetry, missing passes, low correlation confidence |

---

## 4. The 9 Standardized Incident Hypotheses (H1–H9)

Every multi-event evaluation computes deterministic support scores ($0–100$) for 9 standardized candidate hypotheses:

- **H1 (Single Continuous Fire Front):** Expanding wildfire or major industrial conflagration with unbroken spatial-temporal continuity.
- **H2 (Dispersed Multi-Ignition Incident):** Multiple spot fires or separate ignition points within a single localized crisis event.
- **H3 (Recurring Industrial Source):** Routine flaring, smelting, or kiln operations revisited by successive satellite passes.
- **H4 (Multi-Facility Industrial Episode):** Widespread emissions across multiple adjacent plants in an industrial corridor.
- **H5 (Downwind Secondary Ignitions):** Spot fires or hazard alerts aligned downwind of an active primary source.
- **H6 (Coordinated Land-Use Activity):** Broad regional agricultural stubble burning or prescribed forestry management.
- **H7 (Independent Coincident Events):** Unrelated events occurring simultaneously purely by orbital coincidence.
- **H8 (Multi-Pass Same-Source Repetition):** Identical coordinates re-imaged across morning/afternoon satellite constellations.
- **H9 (Insufficient Correlation):** Evidence is contradictory, ambiguous, or too sparse to link events reliably.

---

## 5. REST API Endpoints (Section 21)

All endpoints are read-only, authenticated, and enforce RBAC masking for PUBLIC users:

### Event-Centric
- `GET /api/v1/intelligence/events/{event_id}/related` — Correlated event IDs
- `GET /api/v1/intelligence/events/{event_id}/relationships` — Pairwise typed relationships
- `GET /api/v1/intelligence/events/{event_id}/cluster` — DBSCAN density clusters
- `GET /api/v1/intelligence/events/{event_id}/incident` — Complete correlation result

### Incident-Centric
- `GET /api/v1/intelligence/incidents/{incident_id}` — Incident assessment and impact profile
- `GET /api/v1/intelligence/incidents/{incident_id}/events` — Member events
- `GET /api/v1/intelligence/incidents/{incident_id}/evidence` — Evidence nodes, uncertainty, and data gaps
- `GET /api/v1/intelligence/incidents/{incident_id}/hypotheses` — 9 candidate hypotheses
- `GET /api/v1/intelligence/incidents/{incident_id}/provenance` — Full provenance audit trail

---

## 6. Verification & Test Suite

The Phase 12 test suite is implemented in `tests/test_jarvis_multi_event_correlation.py`:
- **Total Tests:** 33 / 33 required tests implemented.
- **Coverage:** Complete coverage of pairwise classifications, DBSCAN clustering, downwind corroboration, 9 incident hypotheses, undiluted risk preservation, dispatch gate invariants, workspace persistence, and frozen baselines.
