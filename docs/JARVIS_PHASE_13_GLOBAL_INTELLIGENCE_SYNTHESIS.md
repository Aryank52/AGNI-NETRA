# AGNI-NETRA — JARVIS Phase 13: Global Intelligence Fusion & Decision-Support Synthesis

## 1. Architectural Overview & System Invariants

JARVIS Phase 13 establishes the top-level Global Intelligence Fusion and Decision-Support Synthesis layer for AGNI-NETRA. Its mission is to synthesize all prior validated intelligence layers into a single, auditable, structured intelligence assessment without adding opaque surrogate models, averaging distinct scores, or claiming definitive ground-truth certainty.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    JARVIS MASTER AGENT (SINGLETON)                          │
│           Operating Policy: Invariant 1 - ONE MASTER AGENT ONLY            │
│           Operating Policy: Invariant 2 - DISPATCH GATE STRICTLY BLOCKED    │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                ┌──────────────────────┴──────────────────────┐
                ▼                                             ▼
┌───────────────────────────────┐             ┌───────────────────────────────┐
│ Global Intelligence Synthesis │             │   Next-Best-Evidence Engine   │
│            Engine             │             │   (Targeted Uncertainty)      │
└───────────────┬───────────────┘             └───────────────┬───────────────┘
                │                                             │
   Synthesizes 8 Authoritative Layers                         │
   ┌──────────────────────────────────────────────┐           │
   │ Phase 7:    Global Thermal Fusion            │           │
   │ Phase 8:    Global Context Intelligence      │           │
   │ Phase 9:    Temporal Intelligence            │           │
   │ Phase 10:   Environmental & Cross-Modal      │           │
   │ Phase 10.1: Provenance & Authenticity        │           │
   │ Phase 11:   Evidence Graph & Explainability  │           │
   │ Phase 11.1: Frozen Baseline Integrity        │           │
   │ Phase 12:   Multi-Event Incident Correlation │           │
   └──────────────────────────────────────────────┘           │
                │                                             │
                ▼                                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    UnifiedIntelligenceAssessment Artifact                   │
│  - Strict Metric Disambiguation (Risk != Prob != Support != Strength)       │
│  - Deterministic Lineage ("Why?", "What Contradicts?", "What Changed?")     │
│  - 4 Stakeholder Modes (Analyst, Agency, Executive, Public-Safe)            │
│  - Ranked Next-Best-Evidence Recommendations (Information Value Tiers)       │
│  - Cryptographic Provenance Hash & Verification Checklist                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Core Invariants
1. **Exactly ONE Master Agent**: No subagents, no agent swarms, no delegated decision-making daemons. All reasoning flows through the primary JARVIS state machine and deterministic synthesis pipelines.
2. **Operational Dispatch Gate Blocked**: `ENABLE_OPERATIONAL_DISPATCH_GATE = False`. JARVIS is strictly decision-support; physical or inter-agency emergency deployment requires mandatory human verification and authorization.
3. **Strict Metric Disambiguation**: The authoritative 5-factor risk score is preserved without averaging or substitution. Classifier probabilities, evidence support scores, qualitative evidence strengths, epistemic uncertainties, and correlation strengths remain strictly separate.
4. **Epistemic Humility**: Data gaps are formally cataloged. Additional observation recommendations are ranked by information value without ever claiming definitive ground-truth resolution.

---

## 2. Metric Disambiguation Matrix

A critical design requirement of Phase 13 is preventing the conflation or blending of distinct analytical metrics into a single arbitrary score. The six primary metrics are strictly decoupled:

| Metric | Originating Engine / Formula | Range / Format | Semantic Meaning | Preservation Policy |
| :--- | :--- | :--- | :--- | :--- |
| **Authoritative Risk Score** | Production Risk Engine: $0.30 \cdot I + 0.25 \cdot A + 0.20 \cdot E + 0.15 \cdot P + 0.10 \cdot C$ | 0.0 – 100.0 (CRITICAL / HIGH / MODERATE / LOW) | Overall hazard consequence and physical exposure of the thermal event. | **Strictly preserved.** Sole official production risk score; never averaged or replaced by classifier output. |
| **Classifier Calibrated Probability** | XGBoost Champion (`xgb-v3.0-real-candidate`) with Platt calibration | 0.000 – 1.000 ($P(\text{class})$) | Statistical model probability that the observation represents a specific class (e.g. Routine Industrial Flaring). | Disclosed alongside SHAP feature contributions; never treated as event risk. |
| **Evidence Support Score** | Evidence Graph Engine (Phase 11) | 0.0 – 100.0 | Graph-derived metric indicating coherence and coverage of supporting nodes for a hypothesis. | Represents graph structural support; distinct from probabilistic classification. |
| **Evidence Strength** | Qualitative Evidence Framework | 4-Tier Categorical: `STRONG`, `MODERATE`, `LIMITED`, `INSUFFICIENT` | Qualitative assessment of sensor agreement, resolution, and boundary containment. | Summarizes evidence robustness without numerical reductionism. |
| **Epistemic Uncertainty** | Epistemic Gap Evaluator | `KNOWN`, `PARTIAL`, `HIGH_UNCERTAINTY` + Missing Factor Registry | Distinguishes stochastic observation noise from missing empirical telemetry (e.g. SCADA). | Guides collection priority via Next-Best-Evidence engine. |
| **Incident Correlation Strength** | Multi-Event Incident Engine (Phase 12) | 4-Tier Categorical: `STRONG`, `MODERATE`, `LIMITED`, `INSUFFICIENT` | Degree of spatial, temporal, and physical linkage among proximate events in a cluster. | Maintained at incident level; does not alter underlying member event risks. |

---

## 3. The 10-Stage Synthesis Pipeline

The `GlobalIntelligenceSynthesisEngine` executes a deterministic 10-stage pipeline:

1. **Target Event Resolution**: Resolves event identifiers (e.g., `EVT-827`, `Jamnagar`) and loads authoritative geospatial, thermal, and facility attributes.
2. **Multi-Layer Intelligence Harvesting**: Queries Phase 7 (Thermal Fusion), Phase 8 (Context), Phase 9 (Temporal), Phase 10/10.1 (Environmental & Cross-Modal), Phase 11/11.1 (Evidence Graph & Risk), and Phase 12 (Incident Correlation).
3. **Competing Hypotheses Evaluation**: Concurrently evaluates standardized competing hypotheses (e.g., Routine Industrial Flaring, Non-Routine Process Upset, Agricultural Wildfire, Sensor Artifact) tracking supporting, contradicting, and missing evidence.
4. **"Why This Assessment?" Derivation**: Compiles deterministic, numbered evidence points supporting the provisionally favored hypothesis.
5. **"What Contradicts It?" Derivation**: Formulates explicit counter-evidence, thermal anomalies (e.g. +1.45σ FRP), and plume dispersion variances.
6. **"What Changed?" Differential Analysis**: Compares the current workspace assessment with any prior assessment state, calculating deltas in observations, risk score, favored hypothesis, and correlation envelope.
7. **Next-Best-Evidence Ranking**: Leverages `NextBestEvidenceEngine` to rank missing observations by Information Value (`HIGH`, `MEDIUM`, `LOW`, `NOT_AVAILABLE`) across 9 observation sources.
8. **Statement Lineage Construction**: Formulates auditable `AssessmentStatement` objects with categorized tags (`OBSERVED`, `PREDICTED`, `RISK`, `CORRELATION`, `SUPPORTING`, `UNCERTAINTY`) and explicit source/evidence IDs.
9. **Decision-Support Packaging**: Generates 4 customized presentation views (`ANALYST`, `AGENCY`, `EXECUTIVE`, `PUBLIC_SAFE`) with role-based redaction and masking.
10. **Provenance Hash & Artifact Assembly**: Compiles the final immutable `UnifiedIntelligenceAssessment` with cryptographic SHA-256 verification hash.

---

## 4. Next-Best-Evidence Engine

The `NextBestEvidenceEngine` (`backend/app/services/intelligence/next_best_evidence.py`) evaluates epistemic data gaps and prioritizes future collections without over-claiming certainty:

- **Information Value Categories**:
  - `HIGH`: Direct process verification (e.g. Facility SCADA mass flow rate, high-resolution optical drone survey).
  - `MEDIUM`: Contextual corroboration (e.g. Next-pass VIIRS/MODIS overpass, meteorological sounding station).
  - `LOW`: Auxiliary regional data (e.g. Regional air quality monitoring station at distant perimeter).
  - `NOT_AVAILABLE`: Unconfigured or untelemetered sources (e.g. Classified radar or offline telemetry).
- **Core Philosophy**: Next-best-evidence recommendations guide human analysts toward high-yield investigative steps, acknowledging that no sensor observation replaces licensed ground verification.

---

## 5. Stakeholder Decision-Support Presentation Modes

| Presentation Mode | Target Audience | Primary Focus | Redaction & Masking Policy |
| :--- | :--- | :--- | :--- |
| **`ANALYST`** | Senior Intelligence Analysts | Complete technical audit, raw sensor observations, SHAP feature rankings, graph node IDs, and epistemic gaps. | Full disclosure; no masking. |
| **`AGENCY`** | Disaster Management & Environmental Agencies (NDRF, GPCB, MoEFCC) | Inter-agency operational brief, facility operational status, plume dispersion azimuth, cluster perimeter, and safety checklists. | Technical jargon streamlined; critical infrastructure names preserved. |
| **`EXECUTIVE`** | Executive Leadership & Operations Directors | Strategic situation brief, containment verification, high-level risk posture, and escalation recommendations. | Concise summaries; raw math formulas omitted. |
| **`PUBLIC_SAFE`** | Public Safety Advisories & Media Releases | Clear hazard category (e.g. Controlled Industrial Activity), public impact assessment, and precautionary advisories. | **Proprietary telemetry, internal facility schematics, and sensor IDs masked.** |

---

## 6. Database Migration & Schema Extensions

The migration script `database/migrate_phase13_intelligence_synthesis.py` adds 9 columns to `investigation_workspaces`:

1. `unified_assessment` (`JSONB` / `TEXT`): Full serialized `UnifiedIntelligenceAssessment`.
2. `assessment_history` (`JSONB` / `TEXT`): Chronological array of prior synthesized assessments.
3. `assessment_changes` (`JSONB` / `TEXT`): Delta comparison object between current and previous assessment.
4. `decision_support` (`JSONB` / `TEXT`): Serialized decision-support packages for all 4 modes.
5. `recommended_verification` (`JSONB` / `TEXT`): Array of recommended human verification actions.
6. `assessment_provenance` (`JSONB` / `TEXT`): Source integrity hashes and pipeline versioning metadata.
7. `assessment_evidence_ids` (`JSONB` / `TEXT`): Flat array of evidence IDs referenced in the assessment.
8. `assessment_uncertainty` (`JSONB` / `TEXT`): Structured epistemic uncertainty summary.
9. `assessment_mode` (`VARCHAR(32)`): Default or active presentation mode.

---

## 7. REST API Endpoints

All endpoints are registered under `/api/v1/intelligence/` and enforce RBAC:

1. `GET /api/v1/intelligence/events/{event_id}/assessment` — Unified assessment with mode selection.
2. `GET /api/v1/intelligence/events/{event_id}/assessment/history` — Assessment evolution history and deltas.
3. `GET /api/v1/intelligence/events/{event_id}/decision-support` — Stakeholder-tailored brief package.
4. `GET /api/v1/intelligence/events/{event_id}/next-best-evidence` — Ranked uncertainty reduction recommendations.
5. `GET /api/v1/intelligence/events/{event_id}/assessment/provenance` — Cryptographic audit trail and input hashes.
6. `GET /api/v1/intelligence/incidents/{incident_id}/assessment` — Multi-event incident synthesized assessment.
7. `GET /api/v1/intelligence/incidents/{incident_id}/decision-support` — Incident-level decision-support package.
8. `GET /api/v1/intelligence/incidents/{incident_id}/next-best-evidence` — Incident-level next-best-evidence recommendations.

---

## 8. Verification & Acceptance

The test suite `tests/test_jarvis_global_intelligence_synthesis.py` rigorously validates:
- **Section 31 Acceptance**: Complete 16-point assessment brief clearly separating observed, predicted, risk, evidence, and uncertainty.
- **Section 32 Acceptance**: Competing explanations comparison without treating classifier probability as risk.
- **Section 33 Acceptance**: Executive decision-support brief generation with public-safe masking.
- **Safety Invariants**: Operational dispatch gate remains blocked (`ENABLE_OPERATIONAL_DISPATCH_GATE = False`).
