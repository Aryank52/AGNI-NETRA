# AGNI-NETRA — WP7 Operational Intelligence Console Architecture

**Execution Context:** Post-Freeze Intelligence Hardening (Base: Phase 26 `eb7824e6e58eb61f376a4dadb804984950f624e8` + WP1–WP6)  
**Scope:** Frontend state machine, structured intelligence rendering, epistemic visual segregation, historical analysis UI, MapLibre synchronization, and accessibility controls.

---

## 1. Console State Machine

The JARVIS Operational Console operates on an authoritative 10-state finite state machine derived directly from backend intelligence transitions, avoiding deceptive visual animations:

```
                  +-----------------------------------+
                  |               IDLE                |
                  +-----------------+-----------------+
                                    |
                          Incoming Intelligence
                                    |
                  +-----------------v-----------------+
                  |             OBSERVING             |
                  +-----------------+-----------------+
                                    |
                       Risk >= 65.0 or Uncertainty
                                    |
                  +-----------------v-----------------+
                  |           INVESTIGATING           |
                  +-----------------+-----------------+
                                    |
                        Capabilities Executed
                                    |
                  +-----------------v-----------------+
                  |        EVIDENCE_COLLECTED         |
                  +-----------------+-----------------+
                                    |
                   Epistemic Gap / Conflict Detected?
                   /                                 \
                 Yes                                  No
                 /                                     \
+----------------v------------------+    +--------------v--------------------+
|        UNCERTAINTY_PRESENT        |    |             COMPLETED             |
+----------------+------------------+    +-----------------------------------+
                 |
      Consequential Action?
                 |
+----------------v------------------+
|         WAITING_FOR_HUMAN         |
+----------------+------------------+
                 |
         Analyst Verdict
                 |
+----------------v------------------+
|              STOPPED              |
+-----------------------------------+
```

### State Definitions:
- **`IDLE`**: Master Orchestrator awaiting analyst query or sensor telemetry stream.
- **`OBSERVING`**: Autonomous listener monitoring background FIRMS telemetry without active investigation.
- **`INVESTIGATING`**: Executing dynamic capability chain with bounded budget limits.
- **`EVIDENCE_COLLECTED`**: Multi-source evidence graph populated with cryptographic provenance.
- **`UNCERTAINTY_PRESENT`**: Diagnostic ambiguity, uncataloged facilities, or conflicting sensor streams present.
- **`WAITING_FOR_HUMAN`**: Consequential boundary reached; waiting for human analyst inspection verdict.
- **`COMPLETED`**: Investigation successfully satisfied with high confidence.
- **`STOPPED`**: Investigation reached bounded budget limit or manual analyst stop.
- **`DEGRADED`**: Peripheral capability failure (e.g. GIS or SHAP offline); operating with fallback telemetry.
- **`FAILED`**: Database or critical network failure.

---

## 2. 6-Way Epistemic Visual Segregation

The console visually differentiates the 6 epistemic tiers using distinct color palettes, borders, badges, and icons so that status is never conveyed by color alone:

| Epistemic Tier | Semantic Meaning | Icon | Palette | UI Visual Elements |
| :--- | :--- | :---: | :---: | :--- |
| **`OBSERVED`** | Physical measurements from calibrated satellite instruments | `Eye` | Cyan / Sky | Border cyan-500/40, Badge "OBSERVED: Physical Sensor Pass", Value + Unit |
| **`DERIVED`** | Deterministic formulas and PostGIS calculations | `Cpu` | Indigo / Violet | Border indigo-500/40, Badge "DERIVED: Mathematical Formula", Formula citation |
| **`INFERRED`** | Probabilistic estimates from candidate machine learning models | `Sparkles` | Amber | Border amber-500/40, Badge "INFERRED: Candidate Model Prediction", Calibrated % |
| **`UNKNOWN`** | Uncataloged infrastructure or unobserved dimensions | `HelpCircle` | Slate / Gray | Border slate-600/40, Badge "UNKNOWN: Uncataloged Asset", Data acquisition step |
| **`MISSING`** | Data providers or sensors currently unconfigured | `AlertOctagon` | Rose / Red | Border rose-500/40, Badge "MISSING: Provider Offline / Unconfigured" |
| **`CONFLICTING`** | Mutually contradictory sensor or cadastral streams | `AlertTriangle` | Orange | Border orange-500/40, Badge "CONFLICTING: Contradictory Evidence" |

---

## 3. Model Lineage & Provenance Panel

To prevent candidate models from appearing as authoritative champions, the Model Provenance card renders:
- **Model Name:** `xgb-v3.0-real-candidate`
- **Model Status:** `CANDIDATE` (styled in amber pill badge)
- **Active Flag:** `is_active: FALSE` (styled with red lock icon)
- **Artifact SHA-256:** `c52b6369da19d4e423652a3001e38c72737f7f66684e5bc27b9bb1c2a9c754d8`
- **Feature Schema Version:** `v3.2` (18 production features)
- **Taxonomy Version:** `7-class-v1`
- **Calibration Version:** `platt-balanced-v1`
- **Governance Notice:** *"Candidate model in evaluation. Automated model activation is disabled. Human administrator approval required for promotion."*

---

## 4. Historical Intelligence Panel

Renders 6-year multi-sensor archive comparisons:
- **Historical Baseline Mean:** $\bar{x}\text{ FRP (MW)}$
- **Standard Deviation ($\sigma$):** Normal variability envelope
- **Abnormality Sigma:** $+z\sigma$ (standard deviations above baseline)
- **Recurrence Indicator:** Daily / weekly recurrence pattern
- **Persistence Indicator:** Number of consecutive satellite passes detecting thermal signal
- **Time Window:** 2020–2026 Archive
- **Data Freshness:** `CURRENT` ($< 3\text{ hours}$), `STALE` ($> 24\text{ hours}$), or `DEGRADED`

---

## 5. MapLibre GIS Synchronization Protocol

The Operational Console coordinates bi-directionally with the MapLibre GL map:
1. **Event Selection $\to$ JARVIS Focus:** Clicking any thermal event on the map sets `selectedEvent` in the console and displays its structured evidence.
2. **JARVIS Focus $\to$ Map FlyTo:** Clicking "Investigate" in the console centers the map on the event coordinate ($[lon, lat]$), zooms to level $12.5$, and highlights the 500m hazard buffer.
3. **Layer Toggling:** Map layer controls allow toggling OSM Industrial Facilities, CEA Power Stations, and IBM Mining Leases directly from the console header.

---

## 6. Accessibility & Keyboard Control

- **Microphone Toggle:** Spacebar / Enter on the Mic control or keyboard shortcut `Alt + M`.
- **Focus Management:** Focus returns to prompt input after spoken responses complete.
- **ARIA Attributes:**
  - `aria-label="Toggle voice microphone capture"`
  - `aria-live="polite"` on spoken response containers.
  - `aria-expanded` on collapsible evidence sections.
- **Color Independence:** Every metric combines text labels, numeric values, and icons alongside color coding.
