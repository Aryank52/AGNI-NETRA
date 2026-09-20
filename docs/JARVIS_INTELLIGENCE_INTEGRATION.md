# AGNI-NETRA — JARVIS INTELLIGENCE INTEGRATION SPECIFICATION
**Architecture Layer**: Central Governed Intelligence & Single-Master Reasoning Orchestrator  
**Version**: 1.0.0-final-freeze  
**Status**: COMPLETE & VERIFIED  

---

## 1. Executive Summary & Single-Master Invariant

JARVIS serves as the **Single Master Intelligence, Reasoning, and Orchestration Layer** for the AGNI-NETRA platform.
In accordance with strict architectural governance invariants:
1. **NO NEW AI / LLM ARCHITECTURE**:
   - Zero external LLMs (OpenAI, Anthropic, Gemini, Groq, etc.).
   - Zero local LLMs or secondary neural models.
   - Zero agent swarms, recursive subagents, autonomous loops, or hidden reasoning engines.
   - `MAX_RECURSION_DEPTH = 0`.
2. **Deterministic Context Integration**:
   - JARVIS does not generate or speculate; it synthesizes live factual data from existing operational databases, spatial engines, and machine learning pipelines.
   - Intelligence integration is accomplished via structured registries, typed schemas, and live context retrieval.
3. **Epistemic Integrity**:
   - Explicit 6-way epistemic qualification across all analytical outputs: `OBSERVED`, `DERIVED`, `INFERRED`, `UNKNOWN`, `MISSING`, `CONFLICTING`.
   - Clear invariant enforcement: `INFERRED != OBSERVED`, `MISSING != UNKNOWN factual certainty`, `CORRELATED != CAUSAL`, `MODEL OUTPUT != GROUND TRUTH`.

---

## 2. 21-Domain Intelligence Registry (Domains A – U)

The canonical registry is defined in `backend/app/services/jarvis/jarvis_capability_registry.py` and exposed via `GET /api/v1/jarvis/intelligence-registry`:

| Domain Code | Intelligence Domain | Core Capabilities | Primary Data Sources | Epistemic Category |
|-------------|---------------------|-------------------|----------------------|--------------------|
| **A** | **Thermal Observation** | Satellite thermal detection, FRP extraction, brightness temp, sensor telemetry | VIIRS (SNPP, NOAA-20, NOAA-21), MODIS (Terra, Aqua) | `OBSERVED` |
| **B** | **Ingestion Pipeline** | Watermark tracking, deduplication, retry queues, provider health | Ingestion log, Kafka/Queue watermarks, Quarantine table | `DERIVED` / `OBSERVED` |
| **C** | **Geographic Intelligence** | Sovereign India boundary validation, state/district containment, buffer analysis | Survey of India / MEA boundaries, Census shapes | `OBSERVED` |
| **D** | **GIS Context & Layers** | 9-layer spatial stack (Thermal, Facilities, Density, Admin, Forest, LULC, Power, Mining, Protected) | PostGIS spatial tables, Bhuvan LULC, CEA GeoJSON | `OBSERVED` / `DERIVED` |
| **E** | **Industrial Intelligence** | 35,570 active facilities, facility categorization, risk exposure | Central Pollution Control Board (CPCB) registry | `OBSERVED` |
| **F** | **Power Infrastructure** | 502 power stations, 1,633 generating units, thermal baseline correlation | Central Electricity Authority (CEA) Master Register | `OBSERVED` |
| **G** | **Mining Intelligence** | Active coal/mineral pits, flare zones, boundary buffers | Indian Bureau of Mines (IBM) spatial atlas | `OBSERVED` |
| **H** | **Historical Intelligence** | 30-day baselines, annual recurrence, diurnal profiles, similar event clusters | 8.22M historical detection archive (2018-2026) | `DERIVED` |
| **I** | **Anomaly Intelligence** | Contextual abnormality, intensity deviation, recurrence deviation | Statistical z-score, DBSCAN cluster density | `DERIVED` |
| **J** | **ML Model Intelligence** | XGBoost candidate inference (`xgb-v3.0-real-candidate`), TreeSHAP waterfalls | Candidate model artifact, Feature pipeline | `INFERRED` |
| **K** | **Risk Intelligence** | Governed 5-factor risk equation ($0.30I + 0.25A + 0.20E + 0.15P + 0.10C$), 4 tiers | Governed risk calculation engine | `DERIVED` |
| **L** | **Priority Intelligence** | Operational urgency tiering, analyst assignment urgency | Operational workflow rules | `DERIVED` |
| **M** | **Lifecycle Intelligence** | 13-stage event lifecycle (`OBSERVED` $\rightarrow$ `RESOLVED`), audit trails | Event lifecycle state machine | `OBSERVED` |
| **N** | **Epistemic Intelligence** | Epistemic tagging, causal decoupling (`CORRELATED != CAUSAL`) | Epistemic governance validator | `DERIVED` |
| **O** | **Human Verification** | Ground-truth adjudication, contestation logging, audit provenance | Verification records, Analyst audit logs | `OBSERVED` |
| **P** | **Prevention Intelligence** | Longitudinal prevention cases, corrective action tracking | Prevention case repository | `DERIVED` |
| **Q** | **Root-Cause Intelligence** | 13 deterministic physical/operational hypotheses | Root-cause evaluation matrix | `INFERRED` |
| **R** | **Prevention Recommendations** | Statutory preventive controls ("MAY REDUCE RECURRENCE RISK") | Prevention guideline catalog | `INFERRED` |
| **S** | **Reporting Pipeline** | 24-section dossiers, SHA-256 sealed PDFs, JSON exports | Report generation engine | `DERIVED` |
| **T** | **Authority Intelligence** | Multi-tier jurisdiction hierarchy (Central $\rightarrow$ State $\rightarrow$ District) | Statutory jurisdiction mapping | `OBSERVED` |
| **U** | **AGNI-SAT Simulation** | Digital twin orbit propagation, sensor dropout modeling (SIMULATED ONLY) | Satellite orbital mechanics simulator | `INFERRED` (SIMULATED) |

---

## 3. Live JarvisWorldState Architecture

When an analyst accesses the platform or selects an event, `backend/app/services/jarvis/jarvis_world_state.py` dynamically queries live backend storage to construct the 18-part `JarvisWorldState`:

```json
{
  "current_event": { "event_code": "EVT-GUJ-20260916-150D", "status": "ACTIVE" },
  "current_location": { "latitude": 22.4707, "longitude": 70.0577, "state": "Gujarat", "district": "Jamnagar" },
  "current_state": "INTELLIGENCE_READY",
  "active_alerts": { "total_alerts": 88, "critical_count": 14, "high_count": 28 },
  "recent_thermal_activity": { "cluster_count": 88, "operational_events": 82 },
  "historical_context": { "30_day_baseline_frp": 65.4, "recurrence_count": 12 },
  "GIS_context": { "layers_loaded": 9, "coordinate_system": "EPSG:4326" },
  "industrial_context": { "nearest_facility": "Reliance Industries Jamnagar Complex", "distance_km": 0.45 },
  "power_context": { "nearest_station": "Sikka Thermal Power Station", "units": 4 },
  "mining_context": { "active_pits_within_10km": 0 },
  "ML_context": { "candidate_model": "xgb-v3.0-real-candidate", "is_active": false },
  "risk_context": { "score": 80.3, "tier": "CRITICAL", "breakdown": { "intensity": 30.0, "abnormality": 22.5, "exposure": 16.0, "persistence": 12.0, "context": 8.0 } },
  "priority_context": { "priority": "P1_IMMEDIATE" },
  "lifecycle_context": { "current_stage": "INTELLIGENCE_READY", "history_count": 4 },
  "verification_context": { "verified": false, "requires_human_verification": true },
  "prevention_context": { "case_code": "PREV-GUJ-20260919-6DD8AB", "hypotheses_count": 13, "recommendations_count": 6 },
  "system_health": { "api": "HEALTHY", "database": "CONNECTED", "map_tiles": "HEALTHY" },
  "ingestion_health": { "status": "OPERATIONAL", "watermark": "2026-09-20T12:00:00Z" },
  "model_governance": { "automated_activation": false, "active_champion": null },
  "voice_state": { "speech_api_available": true, "cloud_exfiltration": false }
}
```

Endpoint: `GET /api/v1/jarvis/world-state?event_ref={event_code}`

---

## 4. The 18 Canonical Operational Questions

JARVIS is engineered to provide immediate, deterministic answers to the 18 standard operational questions facing defense, disaster management, and environmental regulatory analysts:

1. **What is happening at this event?**
   - Synthesizes detected FRP (MW), coordinates, cluster size, and current lifecycle stage.
2. **Why is the risk critical?**
   - Breaks down the governed 5-factor risk equation ($30\% I + 25\% A + 20\% E + 15\% P + 10\% C$).
3. **What changed from the baseline?**
   - Compares instantaneous FRP to the 30-day running baseline and 3-year historical average.
4. **What historical events are similar?**
   - Identifies past clustered thermal incidents at identical coordinates or matching facility footprints.
5. **Which industrial facilities are nearby?**
   - Evaluates PostGIS distance queries against the 35,570 active CPCB-registered industrial plants.
6. **What power infrastructure is nearby?**
   - Queries the 502 CEA power stations and 1,633 generating units within spatial proximity.
7. **What mining activity exists here?**
   - Correlates with the Indian Bureau of Mines (IBM) spatial atlas for active open-cast or quarrying sites.
8. **Why is the event classified this way?**
   - Reports candidate XGBoost probabilities and primary contributing sensor features.
9. **What evidence supports that classification?**
   - Presents TreeSHAP attribution waterfalls showing positive feature drivers.
10. **What is uncertain?**
    - Quantifies sensor accuracy limits, cloud coverage occlusion probability, and atmospheric attenuation.
11. **What evidence is missing?**
    - Highlights uncollected ground telemetry (e.g. `GAS COMPOSITION DATA UNAVAILABLE`, `ON-SITE SENSOR TELEMETRY MISSING`).
12. **Why might this location experience repeated thermal activity?**
    - Evaluates longitudinal persistence scores, operational flare cycles, or seasonal crop residue burning.
13. **What are the strongest root-cause hypotheses?**
    - Evaluates the 13 deterministic hypotheses (e.g., Elevated Flare Combustion, Coke Oven Gas Leaks, Equipment Overheating).
14. **What evidence contradicts those hypotheses?**
    - Identifies negative indicators (e.g., absence of multi-kilometer smoke plumes contradicting uncontained structure fires).
15. **What preventive measures may reduce recurrence risk?**
    - Formulates statutory preventive engineering recommendations prefixed with `"MAY REDUCE RECURRENCE RISK"`.
16. **Which authority should review the case?**
    - Resolves sovereign administrative hierarchy to specific State Pollution Control Boards and District Magistrates.
17. **Generate a prevention report.**
    - Triggers automated compilation of a 24-section tamper-evident regulatory dossier sealed with SHA-256.
18. **Show this event on the map.**
    - Returns exact map navigation coordinates `[latitude, longitude]` and recommended zoom level `14.5`.

---

## 5. 8-Part Structured Reasoning Engine

Every JARVIS response strictly adheres to the 8-part structured analytical format:
- **`ASSESSMENT`**: Immediate situational summary with explicit epistemic tier.
- **`EVIDENCE`**: Primary physical telemetry (FRP, brightness, coordinates, time).
- **`HISTORICAL`**: Baseline deviation and recurrence metrics.
- **`MODEL`**: Candidate ML classification, confidence, and SHAP drivers.
- **`UNCERTAINTY`**: Calibration limits and environmental confounds.
- **`NEXT_BEST_EVIDENCE`**: Identification of ground-truth evidence needed to eliminate ambiguity.
- **`PREVENTION`**: Root cause hypothesis and preventive engineering controls.
- **`HUMAN_ACTION`**: Authoritative step required by human analyst or regulator.

---

## 6. Offline Resilience & Decoupling

In the event of a total JARVIS subsystem outage:
- The AGNI-NETRA platform remains **100% operational**.
- The Sovereign Geospatial Atlas continues rendering thermal layers via WebGL or SVG fallback.
- Operational Alert queues, Event Dossiers, Ground-Truth Verification, and PDF Generation remain fully accessible.
- Analysts can perform all verification and statutory actions without JARVIS availability.
