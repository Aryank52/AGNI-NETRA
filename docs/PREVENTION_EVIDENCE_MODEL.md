# AGNI-NETRA — Prevention Evidence Model & Epistemic Boundaries
**Standard**: Multi-Source Telemetry Integration & Truth Grading  
**Governing Regulation**: Government of India National Disaster Management Guidelines & Factory Act  
**Core Invariant**: Epistemic Boundary Enforcement & Non-Fabrication of Unobserved Data

---

## 1. Multi-Source Evidence Lineage & Grading

Every data point evaluated in the AGNI-NETRA Proactive Prevention Engine is categorized by its epistemic modality:

```
+-------------------------------------------------------------------------+
| Level 1: OBSERVED (Direct Sensor / Telemetry)                           |
|   • NASA FIRMS VIIRS (NOAA-20, NOAA-21, Suomi-NPP 375m I-Band)          |
|   • NASA MODIS (Terra / Aqua 1km Thermal Telemetry)                     |
|   • Government of India Administrative Boundaries (Survey of India L2)  |
+-------------------------------------------------------------------------+
                                    │
                                    ▼
+-------------------------------------------------------------------------+
| Level 2: DERIVED (Deterministic Mathematical Transformations)           |
|   • Multi-Year Thermal Recurrence Frequency (episodes / year)           |
|   • 90-Day Footprint Spatial Persistence Index [0.0, 1.0]               |
|   • Historical Baseline FRP Deviation Ratio (Peak FRP / Median FRP)     |
|   • Spatial Point-in-Polygon Intersections (PostGIS ST_Contains)        |
+-------------------------------------------------------------------------+
                                    │
                                    ▼
+-------------------------------------------------------------------------+
| Level 3: INFERRED (Probabilistic & Heuristic Classifications)           |
|   • XGBoost Spatial-Temporal ML Classification & Confidence             |
|   • SHAP Local Feature Attribution Waterfall                            |
|   • 13 Root-Cause Hypothesis Confidence Rankings                        |
+-------------------------------------------------------------------------+
                                    │
                                    ▼
+-------------------------------------------------------------------------+
| Level 4: MISSING / RESTRICTED (Explicit Epistemic Boundaries)           |
|   • Ground Stack Gas Spectrometry Telemetry                             |
|   • Unverified Commercial News / Social Media Crawls                   |
|   • Sub-surface Valve & Pipeline Manifold Telemetry                     |
+-------------------------------------------------------------------------+
```

---

## 2. Epistemic Anti-Fabrication Invariants

### 2.1 Missing Atmospheric & Chemical Telemetry
The platform does not possess direct real-time ground chemical sensors on private industrial equipment. When gas concentrations or chemical compounds are queried, the system must never invent concentrations (e.g. "82% Methane, 12% Ethane").
- **Mandatory Output Standard**: `"GAS COMPOSITION DATA UNAVAILABLE"`
- **System Action**: Formulate preventive recommendations that suggest deploying certified ground infrared optical gas imaging (OGI) or fixed VOC sensors.

### 2.2 Missing News & Media Telemetry
Unverified web articles or social media reports are treated as unvetted claims, not ground truth.
- **Mandatory Output Standard**: `"NEWS EVIDENCE UNAVAILABLE"`
- **System Action**: Retain empty evidence structures rather than populating simulated news citations.

### 2.3 Regulatory Agency Investigations
Official judicial or regulatory determinations (e.g. by PESO, DISH, CPCB, or GPCB) are respected only when verified agency documents are linked.
- **Mandatory Output Standard**: `"No verified agency records available"`
- **System Action**: The system reports physical indicators without asserting legal culpability.

---

## 3. Correlation vs Causation Distinction

In longitudinal thermal monitoring, physical proximity and repeated detections can easily lead analysts to assume an event's cause is self-evident.
- **Epistemic Invariant**:
  ```
  "HISTORICAL CORRELATION DOES NOT IMPLY CAUSATION."
  ```
- **Operational Implementation**:
  - High recurrence near an industrial facility proves that thermal emissions regularly occur in that geographic footprint.
  - It does **not** prove negligence, criminal violation, or specific mechanical component failure without on-site physical inspection.
  - All recommendations are structured around risk reduction rather than definitive claims of causation:
    ```
    "MAY REDUCE RECURRENCE RISK"
    ```
