# AGNI-NETRA — JARVIS Phase 11: Global Evidence Graph & Explainable Intelligence
**Status:** Implementation Complete & Fully Verified  
**Date:** September 2026  
**Safety Status:** Single Master Agent • Automated Dispatch Gate Strictly BLOCKED • Zero Synthetic Evidence

---

## 1. Executive Summary

Phase 11 implements the **Global Evidence Graph & Explainable Intelligence Engine** for AGNI-NETRA. Prior to Phase 11, JARVIS synthesized multi-source geospatial, temporal, and environmental telemetry to compute operational risk scores and classifications. Phase 11 establishes **end-to-end epistemic traceability**, making every JARVIS operational conclusion mathematically and structurally explainable backwards through candidate hypotheses, relationships, and multi-sensor observations down to primary physical telemetry.

### Core Architectural Invariants Maintained:
- **Single Master Agent:** One unified JARVIS orchestrator; no subagents, no autonomous dispatch, and no chatbot architecture.
- **Dispatch Gate BLOCKED:** The operational emergency dispatch gate remains permanently locked (`ENABLE_OPERATIONAL_DISPATCH_GATE = False`).
- **Frozen Baselines Intact:** Phases 7, 8, 9, 10, and 10.1 remain 100% frozen and operational. All 190 regression tests pass cleanly.
- **Model Stability:** XGBoost classifier champion (`xgb-v3.0-real-candidate`) weights, Platt calibrator, and 5-factor risk formula weights (`Intensity: 30%, Abnormality: 25%, Exposure: 20%, Persistence: 15%, Context: 10%`) remain mathematically identical.
- **Data Authenticity:** Zero synthetic evidence or simulated observations are introduced as operational facts.

---

## 2. Canonical Evidence Graph Model

The Global Evidence Graph is built on a directed acyclic graph structure connecting 12 canonical node types with 14 deterministic relationship types.

### 2.1 Node Ontology (`EvidenceGraphNode`)
Every node represents a discrete epistemic entity with full provenance metadata:
- `OBSERVATION`: Physical sensor detections (NASA FIRMS MODIS Terra/Aqua, VIIRS SNPP/NOAA-20/NOAA-21, Sentinel-1 SAR).
- `EVENT`: Spatiotemporally aggregated thermal hotspot clusters.
- `CONTEXT`: Infrastructure, administrative, and ecological proximity assets (OpenStreetMap refineries, CEA power stations, IBM mining blocks, FSI forest reserves).
- `TEMPORAL_PATTERN`: Multi-scale recurrence metrics, baseline deviation z-scores, and day/night ratios.
- `ENVIRONMENTAL_CONDITION`: Surface meteorology (ECMWF ERA5 / IMD), wind dispersion vectors, boundary layer height.
- `CROSS_MODAL_OBSERVATION`: Sentinel-2 MSI optical reflectance and Sentinel-1 SAR radar backscatter coherence.
- `RELATIONSHIP`: Causal, associative, or spatial linkages.
- `HYPOTHESIS`: Standardized candidate explanations (A through G) with deterministic Evidence Support Profiles.
- `EVIDENCE`: Calibrated supporting or contradicting evidence bundles.
- `ASSESSMENT`: Final operational disposition and composite risk evaluation.
- `UNCERTAINTY`: Quantified epistemic limitations and resolution recommendations.
- `DATA_GAP`: Explicit disclosures of unconfigured archives, orbital revisit latency, or cloud obscuration.
- `SOURCE`: Authoritative catalog or provider roots (NASA, ISRO, Copernicus, OSM, CEA, FSI, IMD).

### 2.2 Epistemic Nature Taxonomy
Every node is explicitly tagged with its epistemic nature:
- `OBSERVED`: Direct physical measurement from calibrated sensor instruments or authoritative registered database records.
- `DERIVED`: Deterministic mathematical or spatial computations from observations (e.g., PostGIS distance, 5-factor risk score, recurrence rate).
- `INFERRED`: Probabilistic model classifications, candidate hypotheses, or trajectory extrapolations.
- `MISSING`: Known information deficits, unconfigured provider feeds, or obscured sensor passes.
- `CONFLICTING`: Mutually exclusive signals or evidence contradicting dominant hypotheses.
- `TEST_FIXTURE`: Clearly labeled test fixtures (e.g., offline synthetic tests; strictly zero leakage into operations).

### 2.3 Directed Edge Relationships (`EvidenceGraphEdge`)
Deterministic relationships connect graph nodes with explainable rationale:
- `SUPPORTS`: Positive reinforcement strengthening a candidate hypothesis or operational assessment.
- `CONTRADICTS`: Empirical observation rejecting or penalizing an alternative candidate hypothesis.
- `DERIVED_FROM`: Mathematical lineage from raw observation to derived metric (e.g., FRP & Proximity -> Risk Score).
- `INFERRED_FROM`: Probabilistic linkage between telemetry and candidate explanations.
- `DEPENDS_ON`: Data dependence between physical observations and upstream provider catalogs.
- `OCCURS_NEAR`: PostGIS spatial proximity relationship.
- `OCCURS_DURING`: Temporal concurrency relationship.
- `CORROBORATES`: Multi-sensor cross-modal agreement.
- `LIMITS`: Missing observation that caps maximum confidence.
- `CHANGES_CONFIDENCE`: Observation that shifts epistemic uncertainty.
- `INDEPENDENT_OF`: Explicit declaration of provider and sensor independence.

---

## 3. Standardized Candidate Hypotheses & Evidence Support Profiles

The engine evaluates every event against 7 standardized candidate hypotheses:

| Hypothesis ID | Designation | Domain Definition |
|:---|:---|:---|
| **HYPOTHESIS_A** | Industrial Activity | Continuous or operational industrial thermal emissions (refinery, petrochemical, power plant). |
| **HYPOTHESIS_B** | Forest Fire | Wildfire or unmanaged biomass combustion within forest or woodland ecosystem. |
| **HYPOTHESIS_C** | Agricultural Burning | Seasonal crop residue, stubble burning, or localized agricultural clearing. |
| **HYPOTHESIS_D** | Mining Activity | Surface/subsurface mining operations, coal seam fires, or mineral extraction leases. |
| **HYPOTHESIS_E** | Gas Flaring | Combustion of associated petroleum gases or chemical process relief via flare stacks. |
| **HYPOTHESIS_F** | Other Thermal Source | Domestic burning, small brick kilns, urban waste incineration, or unclassified thermal source. |
| **HYPOTHESIS_G** | Uncertain | Available evidence is insufficient, severely occluded, or conflicting; requires human investigation. |

### Evidence Support Profile Calculation
For each candidate hypothesis $H$, the engine computes:
- $\text{Support Score} \in [0.0, 100.0]$: Calculated deterministically from reinforcing vs contradicting edge weights.
- $\text{Supporting Evidence Count}$: Explicit tally of positive edges (`SUPPORTS`, `CORROBORATES`).
- $\text{Contradicting Evidence Count}$: Explicit tally of negative edges (`CONTRADICTS`).
- $\text{Uncertainty Level}$: `LOW`, `MEDIUM`, or `HIGH`.

---

## 4. Multi-Domain Fusion Architecture (Phases 7–10.1)

```
[ NASA FIRMS VIIRS/MODIS ] (Phase 7)
       │ (OBSERVED)
       ▼
[ Spatiotemporal Thermal Event ] ──────────┐
       │ (DERIVED)                        │
       ├──────────────────────────────────┼──────────────────────────────┐
       ▼                                  ▼                              ▼
[ Spatial Context ] (Phase 8)   [ Temporal Pattern ] (Phase 9)  [ Environmental & Cross-Modal ] (Phase 10)
• OSM Petrochemical Perimeter   • 3-Year Historical Baseline    • ECMWF ERA5 Surface Meteorology
• CEA Power Station Proximity   • Day/Night Ratio: 1.05         • Vector Plume Dispersion (ENE)
• FSI Protected Area Reserve    • Recurrence Rate: 99.2%        • Sentinel-2 Optical Pass (No Scar)
• ISRO Bhuvan LULC: Industrial  • Baseline Deviation: +4.7σ     • Sentinel-1 SAR Radar Coherence
       │ (OBSERVED/LOCAL)                 │ (DERIVED)                    │ (DERIVED / INFERRED)
       └──────────────────────────────────┼──────────────────────────────┘
                                          ▼
                         [ Evidence Independence & Deduplication ]
                                          │
                                          ▼
                         [ 7 Candidate Hypotheses Evaluator ]
                                          │
                         ┌────────────────┴────────────────┐
                         ▼                                 ▼
              [ HYPOTHESIS_A: Winner ]           [ Rejected Candidates ]
              • Score: 92.4/100                  • Forest Fire: Contradicted by Land Use
              • 4 Supporting Nodes               • Crop Burning: Contradicted by Recurrence
                         │
                         ▼
             [ Operational Assessment ]
             • Risk Score: 75.3/100 (CRITICAL)
             • Human Verification: MANDATORY
             • Dispatch Gate: BLOCKED
```

---

## 5. REST API Endpoints

The intelligence router (`/api/v1/intelligence`) exposes 8 high-performance endpoints with role-based access control (RBAC):

1. `GET /api/v1/intelligence/events/{event_id}/evidence-graph`  
   Retrieves complete canonical evidence graph, nodes, edges, hypotheses, and uncertainty propagation.
2. `GET /api/v1/intelligence/events/{event_id}/evidence`  
   Returns all evidence nodes with epistemic nature breakdown and strength tiers.
3. `GET /api/v1/intelligence/events/{event_id}/evidence/supporting`  
   Retrieves evidence items directly substantiating the operational assessment.
4. `GET /api/v1/intelligence/events/{event_id}/evidence/conflicting`  
   Retrieves contradicting/limiting evidence items and conflicting hypotheses.
5. `GET /api/v1/intelligence/events/{event_id}/hypotheses`  
   Retrieves 7 standardized candidate hypotheses with Evidence Support Profiles.
6. `GET /api/v1/intelligence/events/{event_id}/assessment-lineage`  
   Traces operational conclusion backwards from synthesis to root observations.
7. `GET /api/v1/intelligence/events/{event_id}/data-gaps`  
   Lists unconfigured feeds, missing passes, and actionable resolution recommendations.
8. `GET /api/v1/intelligence/events/{event_id}/provenance-chain`  
   Returns end-to-end data provenance for all physical and derived nodes.

---

## 6. Primary Acceptance Verification: EVT-827

### Execution Command:
> *"JARVIS, explain the complete evidence chain for EVT-827. Show why the current assessment is supported, what evidence contradicts it, which evidence is observed, derived, or inferred, what information is missing, and what additional observation would most change the assessment."*

### Execution Output Summary:
- **Agent:** Master JARVIS Orchestrator (Single Unified Agent)
- **State Transition:** `IDLE -> UNDERSTANDING -> PLANNING -> EXECUTING -> EVALUATING -> REQUIRES_APPROVAL`
- **Graph Metrics:** 21 Nodes, 40 Explainable Edges
- **Epistemic Breakdown:**
  - `OBSERVED`: 6 nodes (NASA FIRMS VIIRS detections, OSM Refinery geometry, ISRO Bhuvan industrial LULC, FSI Protected Area baseline)
  - `DERIVED`: 4 nodes (Composite 5-factor risk score, multi-year temporal recurrence rate, baseline deviation +4.7σ, ECMWF ERA5 interpolated surface meteorology)
  - `INFERRED`: 9 nodes (7 candidate hypotheses, cross-modal corroboration synthesis, fine-grained plume trajectory)
  - `MISSING`: 2 nodes (Concurrent sub-10m optical pass, global cadastral mining concessions)
  - `CONFLICTING`: 0 unresolved internal contradictions; 2 explicit external contradiction edges rejecting rural wildfire/agricultural hypotheses
- **Dominant Hypothesis:** `HYPOTHESIS_A` (Industrial Activity / Authorized Flaring) — Support Score: 92.4/100
- **Rejected Hypotheses:**
  - `HYPOTHESIS_B` (Forest Fire): Contradicted by industrial land cover and lack of vegetation.
  - `HYPOTHESIS_C` (Agricultural Burning): Contradicted by 300+ continuous detection passes across 3 years.
- **Actionable Recommendations (What would most change the assessment):**
  1. Task sub-meter commercial optical pass (WorldView/PlanetScope) during cloud break to visually isolate flare stack tip from ground-level units.
  2. Ingest certified on-site plant DCS flare log or CPCB continuous emissions monitoring telemetry.
  3. Query Sentinel-1 SAR all-weather radar coherence to confirm structural stability.
- **Stopping Reason:** `SECTION_26_PHASE11_COMPLETE: Evaluated complete evidence chain for EVT-827. Generated 21 nodes and 40 edges. Dominant explanation: HYPOTHESIS_A. Dispatch gate held BLOCKED. Routed to mandatory HITL verification desk.`
- **Operational Dispatch Gate:** Strictly held in **BLOCKED** state.

---

## 7. Verification & Test Suite Summary

- **Total Test Suites Executed:** 8
- **Total Tests Passed:** 190 / 190 (100% Pass Rate)
  - `test_jarvis_evidence_graph.py`: 31 passed
  - `test_phase10_1_provenance_audit.py`: 23 passed
  - `test_jarvis_environmental_crossmodal.py`: 26 passed
  - `test_jarvis_temporal_intelligence.py`: 25 passed
  - `test_jarvis_global_context.py`: 19 passed
  - `test_jarvis_global_thermal.py`: 18 passed
  - `test_jarvis.py`: 28 passed
  - `test_jarvis_investigation_workspace.py`: 20 passed
- **Frontend Typecheck:** `tsc --noEmit` — 0 errors (Passed)
- **Frontend Production Bundle:** `next build` — Clean Compilation (Passed)

---

## 8. Safety Policy & Non-Negotiable Governance Compliance

1. **Autonomous Dispatch Strictly Blocked:** Live emergency services / drone dispatch remains permanently locked (`ENABLE_OPERATIONAL_DISPATCH_GATE = False`).
2. **Single Master Agent:** All evidence graph generation, hypothesis evaluation, and lineage queries execute via the central master JARVIS agent; zero independent subagents exist.
3. **Epistemic Traceability:** No conclusion can exist without backward traversal links to root observations.
4. **Frozen Baselines Intact:** Phases 7 through 10.1 baselines are completely preserved.
5. **No Deployment:** Project remains in local development mode for analyst review.
