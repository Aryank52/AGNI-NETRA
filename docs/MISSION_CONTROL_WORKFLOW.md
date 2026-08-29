# AGNI-NETRA — Mission Control & War Room Workflow

## 1. Tactical Mission Control Interface (`/dashboard/mission-control`)

The Mission Control page provides an integrated simulation, testing, and operational environment structured into three primary panes:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ TOP BAR: AGNI-SAT-01 Status | Altitude 505km | Speed 7.6km/s | Swath 350km   │
├─────────────────┬───────────────────────────────────┬───────────────────────┤
│ LEFT PANEL:     │ CENTER PANEL:                     │ RIGHT PANEL:          │
│ • 12 Scenarios  │ • Interactive Tactical MapLibre   │ • 7-Class AI Classify │
│ • Virtual Task  │ • Sun-Sync LEO Ground Track       │ • SHAP Waterfall      │
│ • Archive Replay│ • Dynamic Sensor Footprint Swath  │ • Risk Multi-Criteria │
│                 │ • Thermal Hotspot Pulse Marker    │ • Expected vs Pred    │
├─────────────────┴───────────────────────────────────┴───────────────────────┤
│ BOTTOM PANEL: 21-Step Pipeline Execution Tracker | Real Stage Latency (ms)  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. 21-Step Live Pipeline Sequence

When a scenario simulation or historical replay is triggered:

1. **Scenario Initiated**: Simulation parameters loaded from catalog.
2. **Spacecraft Tasked**: Mission task dispatched to AGNI-SAT-01.
3. **Orbit Propagated**: Next-pass opportunity calculated.
4. **Sensor Activated**: Appropriate payload activated (`THERMAL_MWIR`).
5. **Observation Radiance Captured**: Synthetic or replayed radiance measured.
6. **Telemetry Packet Formatted**: Binary/JSON telemetry packet generated.
7. **Downlink Ingested**: Ground station receives packet into ingestion buffer.
8. **Normalized Thermal Observation**: Telemetry converted into canonical observation.
9. **Spatiotemporal DBSCAN**: DBSCAN clustering ($1.5\text{ km}$) groups hotspots.
10. **PostGIS Spatial Indexing**: Spatial lookup finds nearest facility.
11. **Bhuvan LULC Classified**: 24m land cover classification added.
12. **18-D Feature Vector Assembled**: Feature pipeline computes multi-spectral metrics.
13. **7-Class XGBoost Inference**: Primary classifier outputs class probabilities.
14. **Shannon Entropy Uncertainty**: Model confidence and entropy measured.
15. **Isolation Forest Anomaly Radar**: Multivariate anomaly score computed.
16. **Empirical Baseline Surge Test**: Facility baseline $\mu$ and $\sigma$ deviation tested.
17. **SHAP TreeExplainer Waterfall**: Local Shapley feature attributions generated.
18. **Multi-Criteria Risk Matrix**: Risk score ($0-100$) and level assigned.
19. **Incident Alert Dispatched**: Emergency alert evaluated and published.
20. **HITL Verification Queue**: Incident staged for human analyst review.
21. **Intelligence Dossier Resolved**: End-to-end dossier and PDF generated.

---

## 3. Real Independent Stage Latency Measurement

Every step in `pipeline_service.py` is timed using `time.perf_counter()`:
- `observation_to_telemetry_ms`
- `clustering_ms`
- `gis_enrichment_ms`
- `ml_inference_ms`
- `shap_explanation_ms`
- `risk_evaluation_ms`
- `db_commit_ms`
- `total_processing_ms` (typically $15 - 45\text{ ms}$ without SHAP; $1200 - 2500\text{ ms}$ with full SHAP waterfall tree calculation)
