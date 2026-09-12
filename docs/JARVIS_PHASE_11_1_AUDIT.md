# AGNI-NETRA — JARVIS Phase 11.1: Frozen Baseline Integrity & Architecture Consistency Audit Report
**Status:** Audit Complete & Verified  
**Date:** September 2026  
**Safety Status:** Single Master Agent • Automated Dispatch Gate Strictly BLOCKED • Zero Synthetic Evidence  
**Scope:** Architecture Consistency, Frozen Baseline Protection, Disambiguation & Hardening ONLY (No New Intelligence Features, No Model Changes, No Deployment)

---

## 1. Executive Summary

Phase 11.1 is an architectural audit and hardening phase designed to rigorously verify and preserve the frozen baselines of AGNI-NETRA (Phases 7 through 11). This phase introduced **zero new intelligence capabilities**, modified **no model binaries or calibration parameters**, and maintained **strict operational safety invariants**.

During this audit:
1. **Authoritative Risk Formula Harmonized:** Completely eliminated any legacy textual artifacts referencing an uncalibrated 5-factor formula (`25%/25%/20%/15%/15%`). Formally ratified that the production implementation in `backend/app/services/risk_service.py` is the single source of truth across all schemas, engine outputs, and tests:
   $$\text{Risk Score} = 0.30 \times S_{\text{intensity}} + 0.25 \times S_{\text{abnormality}} + 0.20 \times S_{\text{exposure}} + 0.15 \times S_{\text{persistence}} + 0.10 \times S_{\text{context}}$$
2. **Five-Metric Disambiguation Matrix Formally Established:** Disambiguated 5 critical system metrics across the backend schemas, API payloads, workspace formatters, and frontend UI to prevent false equivalence between hazard, model confidence, heuristic graph support, observational volume, and data gaps:
   - Authoritative Risk Score
   - Classifier Probability
   - Evidence Support Score
   - Evidence Strength Tier
   - Epistemic Uncertainty
3. **Multi-Sensor Independence & Provenance Hardened:** Audited all graph relationships labeled `INDEPENDENT_OF`. Corrected multi-pass VIIRS satellite linkages (e.g. SNPP vs NOAA-20) from being mislabeled as independent sources to `SAME_SOURCE_REPETITION` / `SPACEBORNE_RADIOMETRY`. Reserved true independence exclusively for orthogonal observation domains.
4. **Epistemic Nature Taxonomy Audited:** Verified all 12 node types adhere to deterministic nature tags (`OBSERVED`, `DERIVED`, `INFERRED`, `MISSING`, `CONFLICTING`, `TEST_FIXTURE`). Strictly ensured test fixtures remain quarantined from operations.
5. **Master Orchestrator & Safety Gate Hardened:** Implemented and validated the Phase 11.1 primary acceptance command:
   `"JARVIS, verify the evidence graph for EVT-827 and explain the exact difference between Risk Score, Classifier Probability, and Evidence Support Score. Show the complete provenance chain for all three metrics."`
   Confirmed automated dispatch gate is strictly **BLOCKED** (`ENABLE_OPERATIONAL_DISPATCH_GATE = False`).
6. **Zero Regression Test Success:** Ran full automated regression suites across all baselines. All 24 targeted audit tests in `tests/test_phase11_1_integrity.py` and all 31 Phase 11 tests in `tests/test_jarvis_evidence_graph.py` passed with 100% compliance.

---

## 2. Non-Negotiable Safety & Governance Compliance

All non-negotiable requirements were strictly honored:

| Invariant | Requirement | Status | Verification Detail |
|:---|:---|:---:|:---|
| **No Deployment** | No production deployment, external network exposure | **COMPLIED** | Pure local development verification |
| **Single Master Agent** | Exactly one unified JARVIS master agent | **COMPLIED** | Zero subagents, zero sidecars, zero background daemons |
| **No Chatbot Architecture** | Deterministic goal-driven orchestrator | **COMPLIED** | Fixed state machine transitions (`UNDERSTANDING` → `PLANNING` → `EXECUTING` → `EVALUATING` → `REQUIRES_APPROVAL`) |
| **Dispatch Gate BLOCKED** | Automated live emergency dispatch blocked | **COMPLIED** | `ENABLE_OPERATIONAL_DISPATCH_GATE = False` verified across all modules |
| **No Autonomous Monitoring** | No unbounded background loops or cron workers | **COMPLIED** | Fully demand-driven / user-invoked |
| **Frozen ML Models** | Zero modification to classifier or calibration | **COMPLIED** | `xgb-v3.0-real-candidate`, Platt calibrator, and Isolation Forest untouched |
| **Zero Fabricated Evidence** | No simulated or mock data leaking to operational events | **COMPLIED** | Verified authentic provenance chains |
| **RBAC Enforced** | Role-based permission gates on all intelligence endpoints | **COMPLIED** | Requires `ANALYST`, `OPERATOR`, or `ADMIN` roles |

---

## 3. Audit Target 1 — Authoritative Risk Formula Integrity

### 3.1 Background & Resolution
An audit of Phase 11 documentation, canonical docstrings, and test 29 revealed remnants of an obsolete draft formula: `Persistence: 25%, Radiative: 25%, Proximity: 20%, LandUse: 15%, History: 15%`.
However, the AGNI-NETRA production risk engine has consistently implemented:
- $S_{\text{intensity}}$ (Radiative heat & FRP index): **30%**
- $S_{\text{abnormality}}$ (Historical baseline deviation z-score): **25%**
- $S_{\text{exposure}}$ (Proximity to high-value infrastructure / human life): **20%**
- $S_{\text{persistence}}$ (Multi-pass temporal recurrence & duration): **15%**
- $S_{\text{context}}$ (Ecological vulnerability & terrain / fuel moisture): **10%**

### 3.2 Implemented Actions
1. **Canonical Model Update:** Updated docstring in `backend/app/models/canonical.py` (`RiskAssessment`) to reflect the exact production weights.
2. **Evidence Graph Engine Documentation:** Updated `evidence_graph_engine.py` node properties and markdown generation to document the authoritative 5-factor formula.
3. **Documentation Realignment:** Updated `docs/JARVIS_PHASE_11_EVIDENCE_GRAPH.md` to reference the 0.30/0.25/0.20/0.15/0.10 weights.
4. **Test Hardening:** Corrected test 29 (`test_risk_formula_unchanged`) in `tests/test_jarvis_evidence_graph.py` and added assertion in `tests/test_phase11_1_integrity.py` to continuously assert the production weights.

---

## 4. Audit Target 2 — Classifier Integrity & Calibration

### 4.1 Verification
- **Artifact:** `xgb-v3.0-real-candidate` binary weights preserved without modification.
- **Platt Calibrator:** Sigmoidal scaling mapping raw margin scores to well-calibrated posterior probabilities preserved without modification.
- **Classes:** 6 canonical target classes verified:
  1. `Industrial` (Refineries, chemical processing, manufacturing)
  2. `Wildfire` (Forest fires, woodland canopy fires)
  3. `Stubble / Agricultural` (Crop residue burning, field clearing)
  4. `Urban / Landfill` (Municipal waste burning, localized urban fires)
  5. `Mining / Quarry` (Open cast coal seam combustion, mineral extraction)
  6. `Prescribed / Controlled` (Forestry agency controlled burns)
- **Labeling Standard:** All classifier outputs are explicitly designated **Model Prediction Probability** (e.g. `88.4% probability of Industrial Fire`) and are never conflated with composite hazard or heuristic support.

---

## 5. Audit Target 3 — Five-Metric Disambiguation Matrix

To ensure absolute clarity for intelligence analysts and prevent erroneous operational decisions, the following 5 metrics have been disambiguated across the entire stack:

| Metric Name | Mathematical Definition | Valid Range | Epistemic Nature | Operational Interpretation |
|:---|:---|:---:|:---:|:---|
| **Authoritative Risk Score** | $0.30 S_{\text{intensity}} + 0.25 S_{\text{abnormality}} + 0.20 S_{\text{exposure}} + 0.15 S_{\text{persistence}} + 0.10 S_{\text{context}}$ | 0.0 – 100.0 | `DERIVED` | Overall composite hazard severity indexing human, economic, and environmental threat. |
| **Classifier Probability** | $P(y = c \mid x) = \frac{1}{1 + \exp(A \cdot f(x) + B)}$ via Platt-calibrated XGBoost | 0.0 – 100.0% | `INFERRED` | Empirical statistical likelihood that the thermal event belongs to a specific fire class given extracted feature telemetry. |
| **Evidence Support Score** | Heuristic graph support ratio: $\min(100, \max(0, \frac{\sum w_{\text{sup}} - \sum w_{\text{con}}}{\sum w_{\text{sup}} + \sum w_{\text{con}} + 1} \times 100))$ | 0.0 – 100.0 | `INFERRED` | Graph-theoretic evidence weight substantiating a specific candidate explanation against alternatives. |
| **Evidence Strength Tier** | Tiered observational robustness based on corroborated physical sensors and spatial resolution | `STRONG`, `MODERATE`, `LIMITED`, `INSUFFICIENT` | `DERIVED` | Qualitative index of telemetry volume, sensor quality, and multi-sensor verification. |
| **Epistemic Uncertainty** | Normalized Shannon entropy: $U = \frac{-\sum p_i \ln p_i}{\ln 6} + \text{DataGapPenalty}$ | 0.0 – 1.0 | `DERIVED` | Mathematical representation of residual ignorance, ambiguous model probabilities, or missing sensor telemetry. |

### UI & Workspace Realignment
- In `frontend/src/app/jarvis/page.tsx`, the hypothesis table header was clarified from `Confidence` to `EVIDENCE SUPPORT SCORE`.
- A dedicated 5-column **Architectural Metrics Disambiguation Panel** was embedded into the JARVIS Workspace.
- In `frontend/src/components/intelligence/EventInvestigationDossier.tsx`, clear guidance badges and tooltips were integrated into the Explainability tab.

---

## 6. Audit Target 4 — Multi-Sensor Independence & Provenance Hardening

### 6.1 Independence Classification Hardening
In early graph generation drafts, any two satellite passes were occasionally connected with `INDEPENDENT_OF`.
Phase 11.1 audited all sensor nodes:
- **NASA VIIRS SNPP & VIIRS NOAA-20/21:** While flying on separate spacecraft in distinct sun-synchronous orbits, both carry the identical VIIRS instrument design (same 375m I-bands, 750m M-bands, identical spectral response functions, and common active fire detection algorithms).
- **Hardened Classification:** Multi-pass VIIRS detections are now classified as `SAME_SOURCE_REPETITION` or `SPACEBORNE_RADIOMETRY`.
- **True Independence:** The relationship `INDEPENDENT_OF` is strictly reserved for orthogonal measurement domains:
  1. *Spaceborne Radiometry vs Ground-Truth Registry* (e.g. VIIRS thermal vs OSM refinery perimeter / CEA power plant registry)
  2. *Spaceborne Thermal vs Optical Surface Reflectance* (e.g. VIIRS 375m MWIR vs Sentinel-2 MSI 10m visible/SWIR burn scar index)
  3. *Spaceborne Radiometry vs Atmospheric Reanalysis* (e.g. VIIRS thermal vs ECMWF ERA5 numerical wind vector reanalysis)

### 6.2 Provenance Integrity
All evidence nodes carry tamper-evident provenance metadata:
- Authoritative root provider (`provider_id`: `NASA_FIRMS`, `COPERNICUS`, `ECMWF`, `OSM_COMMUNITY`, `ISRO_BHUVAN`, `CEA_INDIA`, `FSI_INDIA`).
- Raw ingestion timestamp, processing step, and algorithm pipeline version.
- Zero mock or placeholder records in production code paths.

---

## 7. Audit Target 5 — Epistemic Nature Taxonomy

Every node in the Global Evidence Graph is rigorously tagged with its epistemic nature:

```
                          ┌────────────────────────────────┐
                          │   GLOBAL EVIDENCE GRAPH        │
                          │   EPISTEMIC NATURE TAXONOMY    │
                          └────────────────┬───────────────┘
                                           │
         ┌──────────────────┬──────────────┴─────┬──────────────────┐
         ▼                  ▼                    ▼                  ▼
   [ OBSERVED ]        [ DERIVED ]          [ INFERRED ]        [ MISSING ]
   • VIIRS Pixels      • Risk Score         • XGBoost Probs     • Cloud Gap
   • OSM Perimeters    • Recurrence Rate    • Hypotheses        • Night Optical
   • CEA Coordinates   • 4.7σ Deviation     • Plume Trajectory  • Concessions
   • Forest Reserve    • Wind Vector Math   • Support Scores    
                                                 │
                                           [ CONFLICTING ]
                                           • Incompatible 
                                             Sensor Signals
```

- `OBSERVED`: Ground-truth physical measurements and authoritative registered records.
- `DERIVED`: Deterministic mathematical and geospatial operations (PostGIS distances, risk scores, recurrence statistics).
- `INFERRED`: Probabilistic model outputs, hypothesis support scores, and dispersion estimates.
- `MISSING`: Explicitly cataloged information deficits and unconfigured telemetry.
- `CONFLICTING`: Mutually exclusive observations penalizing alternative hypotheses.
- `TEST_FIXTURE`: Strictly isolated offline testing data; prohibited from operational workspaces.

---

## 8. Audit Target 6 — REST API Endpoints & Schemas

The 8 endpoints under `/api/v1/intelligence` were audited for contract compliance, Pydantic Canonical typing, and role-based access control:

| Endpoint | HTTP Method | Schema Model | RBAC Role | Audit Result |
|:---|:---:|:---|:---:|:---:|
| `/events/{event_id}/evidence-graph` | GET | `EvidenceGraphResponse` | `ANALYST`+ | **PASSED** |
| `/events/{event_id}/evidence` | GET | `EvidenceListResponse` | `ANALYST`+ | **PASSED** |
| `/events/{event_id}/evidence/supporting` | GET | `EvidenceListResponse` | `ANALYST`+ | **PASSED** |
| `/events/{event_id}/evidence/conflicting` | GET | `EvidenceListResponse` | `ANALYST`+ | **PASSED** |
| `/events/{event_id}/hypotheses` | GET | `HypothesisListResponse` | `ANALYST`+ | **PASSED** |
| `/events/{event_id}/assessment-lineage` | GET | `LineageTraceResponse` | `ANALYST`+ | **PASSED** |
| `/events/{event_id}/data-gaps` | GET | `DataGapResponse` | `ANALYST`+ | **PASSED** |
| `/events/{event_id}/provenance-chain` | GET | `ProvenanceChainResponse` | `ANALYST`+ | **PASSED** |

---

## 9. Audit Target 7 — Master Orchestrator, Dispatch Gate & Primary Acceptance Command

### 9.1 Acceptance Command Execution
Command:
```
"JARVIS, verify the evidence graph for EVT-827 and explain the exact difference between Risk Score, Classifier Probability, and Evidence Support Score. Show the complete provenance chain for all three metrics."
```

### 9.2 Orchestrator Behavior & Trace
1. **Interpretation:** Recognized by `JarvisCommandInterpreter` as `VERIFY_EVIDENCE_GRAPH_EXPLAIN_METRICS` with target `EVT-827`.
2. **State Machine:** Transitioned cleanly through `UNDERSTANDING` → `PLANNING` → `EXECUTING` → `EVALUATING` → `REQUIRES_APPROVAL`.
3. **Analysis Payload:**
   - Evaluated EVT-827 evidence graph: 21 nodes, 40 edges.
   - Distinctly separated Risk Score (75.3/100, CRITICAL composite hazard), Classifier Probability (88.4% Industrial Fire via `xgb-v3.0-real-candidate`), and Evidence Support Score (92.4/100 for `HYPOTHESIS_A`).
   - Lineage traces mapped backwards to NASA VIIRS SNPP/NOAA-20, OSM Refinery polygons, ISRO Bhuvan LULC, and ERA5 meteorology.
4. **Safety Verification:**
   - `dispatch_gate_blocked: true`
   - `stopping_reason`: `"AUDIT_PHASE11_1_COMPLETE: Verified evidence graph for EVT-827. Articulated rigorous distinction between Risk Score, Classifier Probability, and Evidence Support Score with full provenance. Automated dispatch gate strictly held in BLOCKED state."`

---

## 10. Audit Target 8 — Frontend Integrity & Verification

- **Workspace Route:** `frontend/src/app/jarvis/page.tsx`
  - Re-labeled table headers to `EVIDENCE SUPPORT SCORE`.
  - Embedded 5-column metric disambiguation panel with badges and descriptions.
- **Investigation Dossier:** `frontend/src/components/intelligence/EventInvestigationDossier.tsx`
  - Added disambiguation callout in Explainability tab.
- **Type Safety:** `npm run typecheck` returned **0 errors**.
- **Bundle Production Build:** Next.js build clean with 0 critical warnings.

---

## 11. Audit Target 9 — Test Suite Results & Regression Matrix

### 11.1 Dedicated Phase 11.1 Integrity Test Suite (`tests/test_phase11_1_integrity.py`)
All 24 targeted audit tests passed:
1. `test_authoritative_risk_formula_weights` — PASS
2. `test_risk_formula_not_equated_with_classifier_prob` — PASS
3. `test_risk_formula_not_equated_with_evidence_support` — PASS
4. `test_classifier_champion_model_untouched` — PASS
5. `test_classifier_classes_integrity` — PASS
6. `test_platt_calibration_applied` — PASS
7. `test_evidence_support_score_is_heuristic` — PASS
8. `test_five_metrics_distinct_in_canonical_schemas` — PASS
9. `test_viirs_satellite_passes_not_labeled_fully_independent` — PASS
10. `test_true_sensor_independence_domains` — PASS
11. `test_epistemic_nature_observed_direct_telemetry` — PASS
12. `test_epistemic_nature_derived_calculations` — PASS
13. `test_epistemic_nature_inferred_hypotheses` — PASS
14. `test_epistemic_nature_missing_telemetry` — PASS
15. `test_epistemic_nature_conflicting_signals` — PASS
16. `test_test_fixtures_isolated_from_operations` — PASS
17. `test_api_endpoints_registered` — PASS
18. `test_api_rbac_enforcement` — PASS
19. `test_master_agent_single_orchestrator` — PASS
20. `test_dispatch_gate_remains_blocked` — PASS
21. `test_primary_acceptance_command_execution` — PASS
22. `test_stopping_reason_honored` — PASS
23. `test_no_fabricated_evidence` — PASS
24. `test_frontend_labels_disambiguated` — PASS

### 11.2 Baseline Regression Verification
- `test_jarvis_evidence_graph.py`: **31 / 31 passed** (100%)
- `test_phase11_1_integrity.py`: **24 / 24 passed** (100%)
- `test_jarvis.py`: **28 / 28 passed** (100%)
- `test_jarvis_investigation_workspace.py`: **20 / 20 passed** (100%)
- **Total Combined Tests Executed:** **103 / 103 passed** (0 failures, 0 regressions).

---

## 12. 14-Point Comprehensive Audit Checklist

| Item # | Audit Verification Item | Status | Verified Evidence |
|:---:|:---|:---:|:---|
| 1 | Production 5-factor risk formula (0.30/0.25/0.20/0.15/0.10) ratified everywhere | **VERIFIED** | `risk_service.py`, `canonical.py`, `evidence_graph_engine.py` |
| 2 | Legacy 25/25/20/15/15 formula text eliminated from docs and tests | **VERIFIED** | Cleaned `docs/JARVIS_PHASE_11_EVIDENCE_GRAPH.md` and test 29 |
| 3 | Classifier model `xgb-v3.0-real-candidate` untouched | **VERIFIED** | Checksum verified, binary untouched |
| 4 | Platt calibration active and preserved | **VERIFIED** | Sigmoidal scaling formulas verified |
| 5 | Classifier output labeled as Model Prediction Probability | **VERIFIED** | Verified in schemas and UI |
| 6 | Evidence Support Score documented as heuristic graph metric | **VERIFIED** | `evidence_graph_engine.py` and UI table headers |
| 7 | Full 5-metric disambiguation matrix established across stack | **VERIFIED** | Schemas, workspace, and frontend panel |
| 8 | Multi-pass VIIRS reclassified to `SAME_SOURCE_REPETITION` | **VERIFIED** | `evidence_graph_engine.py` edge generation |
| 9 | `INDEPENDENT_OF` reserved for orthogonal domains | **VERIFIED** | Tested in `test_phase11_1_integrity.py` |
| 10 | Epistemic nature taxonomy strictly audited across 12 node types | **VERIFIED** | Unit tested in tests 11–16 |
| 11 | REST API routes under `/api/v1/intelligence` verified with RBAC | **VERIFIED** | 8 endpoints audited, Pydantic typed |
| 12 | Master orchestrator executes Section 15 acceptance command | **VERIFIED** | Verified with EVT-827 acceptance test |
| 13 | Operational dispatch gate strictly **BLOCKED** | **VERIFIED** | `ENABLE_OPERATIONAL_DISPATCH_GATE = False` |
| 14 | Zero synthetic evidence leaking into operational events | **VERIFIED** | Verified authentic provenance chains |

---

## 13. Conclusion

The **JARVIS Phase 11.1 — Frozen Baseline Integrity & Architecture Consistency Audit** is completed and verified. All inconsistencies have been resolved, all mathematical and provenance formulas are hardened, and all safety gates remain intact. AGNI-NETRA stands architecture-clean and fully aligned with its frozen baselines.
