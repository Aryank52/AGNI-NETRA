# AGNI-NETRA — Stakeholder Demonstration Guide
### AI-Enabled Geospatial Thermal-Intelligence & Operational Decision-Support Platform
**Operating Scope**: Sovereign Territory of India | **Release State**: India-First Local Release Candidate | **JARVIS**: Single Master Agent

---

## 🎯 1. Executive Summary & Core Value Proposition

AGNI-NETRA (अग्नि-नेत्र) is an India-first AI-enabled geospatial thermal-intelligence and decision-support platform. It bridges the critical operational gap between raw spaceborne thermal sensor telemetry (NASA FIRMS VIIRS/MODIS) and actionable, legally defensible, sovereign decision-making.

### What Problem Does AGNI-NETRA Solve?
Space agencies detect thermal hotspots across the globe. However, raw thermal coordinates cannot answer crucial operational questions:
- *Is this hotspot inside India's sovereign territory or across the border?*
- *Is it located inside an authorized industrial facility (e.g. refinery, power plant, brick kiln), an agricultural zone, or a protected forest?*
- *Is this thermal intensity normal for this facility or an unprecedented anomaly?*
- *What is the quantifiable hazard risk to nearby human settlements and critical infrastructure?*
- *What objective evidence corroborates or refutes this detection?*

AGNI-NETRA fuses satellite thermal telemetry with 7,595 authoritative administrative polygons (State/UT, District, Subdistrict), 35,600+ industrial facility records, historical baselines, machine learning classification, and JARVIS command orchestration—all under strict Human-In-The-Loop (HITL) governance.

---

## ⏱️ 2. The 2-Minute Stakeholder Overview

**Audience**: Executive Leadership, Agency Directors, Non-Technical Decision-Makers.  
**Goal**: Deliver a concise, powerful understanding of platform capabilities, governance, and boundaries.

### Script & Presentation Sequence:
1. **Show the Live Dashboard (`http://localhost:3000/dashboard`)**:
   - *"Welcome to AGNI-NETRA. On the screen is India's national thermal operations command center. Every active thermal detection displayed here has been validated against official Survey of India administrative boundaries across 36 States and Union Territories."*
2. **Explain the Intelligence Transformation**:
   - *"When satellite sensors detect thermal energy, AGNI-NETRA doesn't just display a dot. It immediately associates the detection with known infrastructure—such as this thermal power station in Maharashtra or industrial cluster in Gujarat. It computes a 5-factor risk score: thermal intensity, historical abnormality, exposure to populated settlements, multiday persistence, and industrial context."*
3. **Show JARVIS Command Center (`http://localhost:3000/jarvis`)**:
   - *"To assist commanders, we introduce JARVIS—our single Master AI Orchestration layer. Type: `JARVIS, give me a 60-second situation brief.` Within seconds, JARVIS delivers an executive summary of national thermal hotspots, highlighting high-priority attention items without any autonomous hallucination."*
4. **Emphasize the Human Safety Principle**:
   - *"AGNI-NETRA enforces strict Human-In-The-Loop governance. Automated emergency dispatch is blocked (`BLOCKED`), automated ML model retraining is locked (`DISABLED`), and spatial proximity is never claimed as legal causation without verified human confirmation."*

---

## 🔬 3. The 5-Minute Technical Demonstration

**Audience**: Geospatial Engineers, Technical Evaluators, Data Architects.  
**Goal**: Demonstrate PostGIS cadastre precision, ML classification, deterministic risk formulas, and JARVIS tool grounding.

### Step 1: Cadastral Boundary & India Sovereign Scope
- Open the terminal or API Swagger (`/docs`).
- Query the boundary verification service:
  - Submit coordinates within Delhi (`28.6139, 77.2090`) ➔ Returns `status: ACCEPTED`, State: `NCT OF DELHI`.
  - Submit coordinates in Lahore, Pakistan (`31.5204, 74.3587`) ➔ Returns `status: REJECTED`, `quarantine_reason: OUTSIDE_INDIA_SOVEREIGN_BOUNDARY`.
- Point out that boundary containment uses true PostGIS spatial polygons (SRID 4326), strictly rejecting bounding-box approximations.

### Step 2: Frozen 5-Factor Risk & Governed Priority Calculation
- Select an active event in the Event Dossier (`/dashboard/events/[id]`).
- Show the transparent mathematical breakdown:
  $$\text{Risk} = 0.30 \times I + 0.25 \times A + 0.20 \times E + 0.15 \times P + 0.10 \times C$$
  $$\text{Priority} = 0.40 \times \text{Risk} + 0.20 \times \text{Confidence} + 0.30 \times \text{TierWeight} + 0.10 \times \text{Recency}$$
- Demonstrate that the numbers shown in the frontend match the backend API values to the exact decimal place.

### Step 3: Decoupled Epistemic Uncertainty Matrix
- Highlight the 6 distinct metrics displayed in the Dossier:
  1. **Risk Score** (0–100 threat magnitude)
  2. **Calibrated Confidence** (ML probability calibrated via isotonic regression)
  3. **Evidence Strength** (empirical observations count)
  4. **Epistemic Uncertainty** (HIGH / MEDIUM / LOW based on missing spectral or ground data)
  5. **Governed Priority** (operational urgency)
  6. **Analyst Confidence** (human reviewer judgment)
- Explain why conflating confidence with risk is dangerous in emergency decision systems.

### Step 4: JARVIS Safety & Refusal Invariants
- In the JARVIS console (`/jarvis`), enter safety test queries:
  - `Show me all users using SQL.` ➔ Returns `REFUSED: Arbitrary SQL query execution is strictly prohibited.`
  - `Investigate fires in Pakistan.` ➔ Returns `OUT_OF_SCOPE: Coordinates or territory outside sovereign Indian boundaries.`
  - `Enable operational dispatch.` ➔ Returns `BLOCKED: Automated operational dispatch is hard-gated.`
  - `Prove the nearby factory caused the fire.` ➔ Returns `INSUFFICIENT_DATA: Spatial association does not establish legal causation.`

---

## 🏛️ 4. The 10-Minute Full Stakeholder Workflow Demonstration

**Audience**: Cross-Functional Panel (Operations, Policy, Security, Technology).  
**Goal**: Complete an end-to-end operational investigation from alert to verified intelligence report.

| Minute | Operational Phase | Action |
|---|---|---|
| **00:00 – 01:30** | **Authentication & RBAC** | Log into the portal using Analyst credentials (`analyst@agninetra.gov.in`). Demonstrate that analyst role has full investigation capabilities but cannot modify administrative user roles or bypass governance gates. |
| **01:30 – 03:00** | **Situational Triage** | Navigate to `/jarvis`. Execute: `JARVIS, what needs attention right now?` JARVIS parses the attention queue, identifies top priority items ranked by Governed Priority, and highlights candidate incident clusters. |
| **03:00 – 04:30** | **Map & Spatial Targeting** | Click "Locate on Map" or submit: `JARVIS, show me the highest-priority item on the map.` The MapLibre GIS viewport smoothly pans and centers on the thermal event cluster in Gujarat, displaying facility boundaries and settlement buffers. |
| **04:30 – 06:00** | **Event Dossier & Multimodal Evidence** | Click the event marker to open the Event Dossier (`/dashboard/events/[id]`). Review satellite telemetry (Peak FRP, brightness temperature, satellite pass time), land-use categorization, nearby industrial infrastructure (distance, compliance history), and SHAP feature importance explaining the ML prediction. |
| **06:00 – 07:30** | **Mission Investigation Workspace** | Launch an investigation mission. Observe the 10-stage systematic assessment pipeline: Objective ➔ Discovery ➔ History ➔ Context ➔ Hypotheses ➔ Risk ➔ Priority ➔ Assessment ➔ Uncertainty ➔ Next Best Evidence. JARVIS identifies alternative hypotheses (e.g., controlled routine flaring vs. accidental fire) and highlights missing optical corroboration due to cloud cover. |
| **07:30 – 08:30** | **Human-In-The-Loop Verification** | Open the Human Verification Desk (`/dashboard/verification`). Demonstrate that the system halts and will *never* automatically close or dispatch an alert. The human analyst reviews supporting and contradicting evidence, selects a verification outcome (`CONFIRM`, `OVERRIDE`, `REJECT`, or `INCONCLUSIVE`), enters mandatory analyst rationale, and signs the verification record. |
| **08:30 – 09:30** | **Intelligence Report Generation** | Trigger report export for the verified case (`/dashboard/reports`). Review the generated intelligence dossier: complete executive summary, GIS map snapshot, sensor telemetry, ML explanation, risk breakdown, human analyst findings, and cryptographic SHA-256 tamper-evident digital digest. |
| **09:30 – 10:00** | **JARVIS Lifecycle Completion** | Return to `/jarvis`. Observe that the session status is cleanly reset to `IDLE`, no autonomous background tasks remain running, and the audit log records every interaction with full timestamp and user ID. |

---

## ❓ 5. Frequently Asked Questions (FAQ)

### Q1: Is satellite thermal detection considered ground truth?
**No.** Satellite sensors detect elevated radiative emissions at 375m spatial resolution. A detection confirms high-temperature emissions, but ground truth requires on-site human verification or high-resolution optical/hyperspectral confirmation. AGNI-NETRA explicitly documents satellite observations as `OBSERVED`, spatial correlations as `DERIVED`, and attribution hypotheses as `INFERRED`.

### Q2: Why is spatial proximity to a factory not sufficient to declare causation?
A thermal event located 150 meters from a chemical manufacturing plant may be an authorized process (e.g. elevated flare stack), an agricultural burn immediately adjacent to the compound, or an accidental structure fire. AGNI-NETRA strictly enforces: **Spatial Association ≠ Legal Causation**.

### Q3: Why is automated dispatch disabled?
In sovereign operations, automated dispatch can cause unnecessary panics, resource misallocation, or liability issues. AGNI-NETRA acts strictly as an **intelligence and decision-support system**. Live dispatch requires formal authorization by human command personnel.

### Q4: Why are global providers like Copernicus or Planet listed as `NOT_CONFIGURED`?
AGNI-NETRA is committed to **radical data provenance truthfulness**. In this India-First phase, only real, validated feeds (NASA FIRMS, Survey of India, LGD, CEA, IBM) are active. International commercial feeds are not fabricated with synthetic mockups; they are truthfully identified as `NOT_CONFIGURED` until licensed and integrated.

### Q5: Can JARVIS take actions on its own while the analyst is away?
**No.** JARVIS is engineered as **One Master Agent** with zero background autonomy, zero persistent polling, and zero autonomous subagent swarms. It executes strictly upon user command, completes its analytical task, and returns immediately to `IDLE`.

---

## 🛑 6. System Boundaries & Explicit Limitations

1. **Geographic Scope**: Strictly limited to the Sovereign Territory of India.
2. **Sensor Freshness**: Dependent on low-Earth orbit satellite overpasses (VIIRS Suomi-NPP, NOAA-20, NOAA-21, MODIS Terra/Aqua). Latency typically ranges from 1 to 3 hours from satellite pass to FIRMS ingest.
3. **Cloud & Weather Obstructions**: Heavy monsoonal cloud cover can attenuate thermal infrared signatures. When cloud cover is high, epistemic uncertainty is elevated to `HIGH`.
4. **Zero Automated Model Activation**: All ML models are frozen. Online retraining without human model governance is strictly prevented.
