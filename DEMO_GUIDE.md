# AGNI-NETRA — Stakeholder Demonstration Guide
### Sovereign India AI Thermal Intelligence & Operational Decision Support Platform
**Version**: `1.0.0-RC1` | **Audience**: Operational Analysts, Regulators, Agency Leadership, and Technical Auditors

---

## 🎯 Demonstration Objective & Executive Narrative

This guide provides an end-to-end, scripted demonstration of the **AGNI-NETRA** platform. It demonstrates how spaceborne satellite thermal telemetry is transformed into actionable, legally defensible, and explainable operational intelligence strictly within the Sovereign Territory of India.

> **Key Talking Point**:
> *"Most satellite fire maps tell you where a heat hotspot was detected. AGNI-NETRA tells you what sovereign industrial facility or natural feature it is spatially associated with, whether it is abnormal compared to 6 years of historical behavior, how risky it is under frozen governance formulas, and what concrete evidence a human analyst must evaluate before any operational action is taken."*

---

## 🛠️ Pre-Demonstration Environment Setup

1. **Verify Services**:
   - Backend running at `http://127.0.0.1:8000`
   - Frontend running at `http://localhost:3000`
   - PostgreSQL 16 active on `127.0.0.1:5432`

2. **Terminal Walkthrough Execution**:
   To run the automated 14-stage CLI demonstration at any point:
   ```powershell
   $env:PYTHONPATH="."
   .venv\Scripts\python.exe tests/demonstration_phase21_e2e.py
   ```

---

## 📋 The 14-Stage Demonstration Walkthrough

### STAGE 1: Real Telemetry Ingestion & Spatial Grounding
- **Action**: Open `/dashboard` or query the Ingestion Status.
- **Narrative**: *"AGNI-NETRA ingests near-real-time observations from NASA's VIIRS 375m sensor constellation. Every single observation is authenticated, normalized into UTC timestamps and Kelvin temperatures, and deduplicated against existing detections."*
- **Evidence**: Over 96 real live ingestion records and 8.22 million historical detections grounded in PostGIS.

### STAGE 2: Sovereign India Geographic Containment (Survey of India / LGD)
- **Action**: In JARVIS or the spatial explorer, test coordinates inside vs outside India.
- **Narrative**: *"Unlike simple bounding boxes that accidentally capture neighboring territories, AGNI-NETRA utilizes official Survey of India / Local Government Directory cadastral boundaries across 7,595 polygons. Let's observe what happens when coordinates in Dahej, Gujarat are submitted versus coordinates in Colombo, Sri Lanka."*
- **Output**:
  - `[21.71°N, 72.58°E]` (Dahej, Gujarat) ➔ **Inside India: TRUE** (Assigned: Gujarat > Bharuch)
  - `[6.92°N, 79.86°E]` (Colombo, Sri Lanka) ➔ **Inside India: FALSE** (Excluded & Quarantined)

### STAGE 3: Operational Event Formation
- **Action**: Navigate to `/dashboard` to inspect clustered thermal events.
- **Narrative**: *"Raw satellite passes produce isolated pixel detections. AGNI-NETRA clusters multi-sensor detections across time and space into cohesive Thermal Events with calculated centroids, convex hulls, and maximum radiative power metrics."*

### STAGE 4: Machine Learning Classification & Attribution
- **Action**: Click on an event card to view the ML Attribution widget.
- **Narrative**: *"Our frozen 7-class XGBoost model analyzes radiometric features (FRP, brightness temperature, diurnal recurrence) to classify the thermal source (e.g. Industrial Fire vs Gas Flare vs Stubble Burning). Crucially, the raw probabilities are calibrated using isotonic regression to provide an authentic calibrated confidence score."*
- **Evidence**: Attribution Class: `Industrial Fire` | Calibrated Confidence: `0.97`.

### STAGE 5: Longitudinal Historical Baseline (6-Year Multi-Sensor Archive)
- **Action**: View the Historical Behavior tab.
- **Narrative**: *"Is this event routine or abnormal? AGNI-NETRA references an 8.22-million observation historical archive spanning 2020 through 2025. It computes location-specific baseline statistics ($\mu_{frp}, \sigma_{frp}$) to measure whether current thermal output represents a statistically significant surge (+3.2σ)."*

### STAGE 6: 5-Factor Operational Risk Evaluation (Frozen Formula)
- **Action**: Expand the Risk Breakdown panel.
- **Narrative**: *"To prevent subjective bias and ensure legal defensibility, the platform's 5-factor risk scoring formula is strictly frozen with fixed weights: 0.30 Intensity, 0.25 Abnormality, 0.20 Exposure, 0.15 Persistence, and 0.10 Context. The resulting score is bounded between 0 and 100."*

### STAGE 7: Governed Priority Ranking & Triage Routing
- **Action**: Navigate to `/dashboard/verification` (Analyst Triage Queue).
- **Narrative**: *"Risk alone does not determine queue priority. The Governed Priority formula fuses Risk Score (40%), Model Confidence (20%), Routing Tier Weight (30%), and Event Recency (10%). High-threat, verified events are automatically routed to Tier 1 or Tier 2 for immediate human analyst review."*

### STAGE 8: Cadastral Context Correlation (OSM, CEA, IBM, PARIVESH)
- **Action**: Inspect the Spatial Context tab on the event dossier.
- **Narrative**: *"AGNI-NETRA cross-references active hotspots with four national cadastral registries: 35,684 OSM industrial facilities, 1,633 CEA power plants, 414 IBM mining leases, and PARIVESH environmental clearances. Notice our language is strictly non-causal: 'spatially associated with', never 'caused by'."*

### STAGE 9: Structured Evidence Graph & Epistemic Uncertainty
- **Action**: View the Evidence Graph visualization.
- **Narrative**: *"We maintain a strict separation between Model Confidence, Evidence Strength, and Epistemic Uncertainty. If cloud cover obscures observation passes or an industrial registry lacks sub-meter tags, epistemic uncertainty is explicitly elevated to MEDIUM or HIGH, notifying the analyst of knowledge gaps."*

### STAGE 10: Analysis of Competing Hypotheses (5-Hypothesis ACH Matrix)
- **Action**: Open the Competing Hypotheses Review panel.
- **Narrative**: *"Rather than presenting a single AI guess, AGNI-NETRA structures the investigation using Richards Heuer's Analysis of Competing Hypotheses (ACH). Five hypotheses (Routine Industrial, Accidental Fire, Stubble Burning, Wildfire, Sensor Glint) are concurrently tracked with supporting and contradicting evidence."*

### STAGE 11: Master Agent JARVIS Command Interaction
- **Action**: Navigate to `/jarvis` and execute:
  `JARVIS, why was this event prioritized?`
- **Narrative**: *"JARVIS operates as a single Master Agent with zero autonomous subagents. It provides read-only conversational reasoning, explains the mathematical breakdown of priority scores, and returns deterministically to an IDLE state upon completion."*
- **Response**: JARVIS displays the exact mathematical weights, component contributions, and data lineage without hallucination.

### STAGE 12: Human-in-the-Loop Verification Gate
- **Action**: Attempt to trigger an automated dispatch, or review the safety modal.
- **Narrative**: *"Notice that AI is strictly forbidden from autonomously declaring emergencies or emitting dispatches. The Operational Dispatch Gate is hardcoded to BLOCKED (`ENABLE_OPERATIONAL_DISPATCH_GATE = False`), and automated model self-activation is DISABLED. Every operational action requires an authenticated human analyst."*

### STAGE 13: Case Lifecycle Governance
- **Action**: Transition an event from `TRIAGED` to `INVESTIGATING` and record an evidence decision.
- **Narrative**: *"All analyst actions, hypothesis assessments, and evidence validations are stored in immutable audit logs. Raw satellite telemetry remains completely untouched, ensuring total evidentiary integrity for regulatory proceedings."*

### STAGE 14: 17-Section Operational Analyst Report with SHA-256 Digest
- **Action**: Click 'Generate Operational Report'.
- **Narrative**: *"Finally, the system compiles an authoritative 17-section operational markdown report covering everything from Survey of India cadastral lineage to ACH hypotheses and dispatch constraints. The report is stamped with a cryptographic SHA-256 hash to guarantee that it cannot be altered after generation."*
- **Output**: Report generated with 17 standardized sections and a 64-character SHA-256 digest (e.g. `74f64206e0d6...`).

---

## ❓ Frequently Asked Questions by Stakeholders & Auditors

**Q: Can the AI send a false alarm to the fire department?**
*A: No. The platform's Operational Dispatch Gate is strictly hardcoded to `BLOCKED`. Live sirens, emergency dispatches, and public alarms cannot be emitted by the software.*

**Q: Does the platform hallucinate weather or satellite data when APIs are down?**
*A: Never. Unconfigured external feeds (Copernicus, ECMWF, NOAA, Planet) are declared `NOT_CONFIGURED`. Zero synthetic data is substituted.*

**Q: What prevents the machine learning model from drifting over time?**
*A: Automated model activation is disabled (`ENABLE_AUTOMATED_MODEL_ACTIVATION = False`). All model weights, encoders, and calibration curves are version-locked in serialized artifacts.*

**Q: Are borders accurately respected?**
*A: Yes. All spatial filtering operates via PostGIS polygon containment against the official Survey of India / LGD administrative dataset.*
