# AGNI-NETRA — WP5 Model Governance, Lifecycle & Quality Report
**Document ID:** `DOC-WP5-GOV-REPORT-001`  
**Execution Date:** 2026-09-19  
**Branch:** `development/post-freeze-intelligence-hardening`  
**Baseline Reference:** Phase 26 Baseline (`eb7824e6e58eb61f376a4dadb804984950f624e8`) + WP1–WP4

---

## 1. Executive Summary & Governance Lifecycle

This report establishes the formal machine learning governance architecture for AGNI-NETRA following the execution of Work Package 5 (WP5). 

The goal of AGNI-NETRA ML governance is to enforce an auditable, reproducible, and non-bypassable model lifecycle:
$$\text{REAL TELEMETRY} \longrightarrow \text{POINT-IN-TIME ENRICHMENT} \longrightarrow \text{DATASET VERSION} \longrightarrow \text{CONTROLLED TRAINING} \longrightarrow \text{TEMPORAL & SPATIAL VALIDATION} \longrightarrow \text{PLATT CALIBRATION} \longrightarrow \text{SHAP ATTRIBUTION} \longrightarrow \text{CANDIDATE REGISTRATION} \longrightarrow \text{HUMAN GOVERNANCE REVIEW} \longrightarrow \text{AUTHORIZED ACTIVATION}$$

### Primary Governance Invariants:
1. **Permanent Candidate Invariant:** The production in-memory inference candidate `xgb-v3.0-real-candidate` operates under provisional evaluation and remains registered with `status = 'CANDIDATE'` and `is_active = FALSE` in PostgreSQL `ml_model_registry`.
2. **Automated Activation Gate:** `ENABLE_AUTOMATED_MODEL_ACTIVATION = False` remains strictly enforced in `backend/app/core/config.py`. No automated script, background job, or CI/CD pipeline can promote a candidate to `ACTIVE`.
3. **Operational Dispatch Gate:** `ENABLE_OPERATIONAL_DISPATCH_GATE = False` remains permanently locked; zero autonomous field dispatches can execute without human verification.
4. **Cryptographic Provenance:** Every serialized artifact binary must match its registered SHA-256 checksum before execution.

---

## 2. Model Registry Schema & State Disambiguation

### 2.1 Hardened PostgreSQL `ml_model_registry` Schema
The `ml_model_registry` table was upgraded with strict non-breaking governance columns:
- `id` (`VARCHAR(36)`): Unique identifier (UUID).
- `model_name` (`VARCHAR(100)`): Human-readable model title.
- `version` (`VARCHAR(50) UNIQUE`): Semantic version tag.
- `model_family` (`VARCHAR(50)`): Algorithmic family (`XGBoost`, `RandomForest`, `IsolationForest`, `ExtraTrees`).
- `dataset_version` (`VARCHAR(50)`): Linked dataset version (`v3.2-real-final`).
- `feature_schema_version` (`VARCHAR(50)`): Standardized feature schema (`v3.2`).
- `taxonomy_version` (`VARCHAR(50)`): Taxonomy version (`7-class-v1`).
- `calibration_version` (`VARCHAR(50)`): Linked calibration model version (`balanced-platt-v3.0`).
- `artifact_path` (`VARCHAR(255)`): Path to serialized binary.
- `artifact_sha256` (`VARCHAR(64)`): Cryptographic SHA-256 checksum of artifact.
- `metrics` (`JSONB`): Comprehensive test split, spatial CV, and calibration metrics.
- `status` (`VARCHAR(50)`): Governed state (`CANDIDATE`, `VALIDATION`, `APPROVED`, `ACTIVE`, `RETIRED`, `REJECTED`).
- `is_active` (`BOOLEAN`): Production active flag (Only 1 active model per family permitted).
- `training_period` (`VARCHAR(100)`): Chronological training window (`2022-01-01 to 2024-12-31`).
- `created_by` (`VARCHAR(100)`): Pipeline or actor that produced the model.
- `approved_by` (`VARCHAR(100)`): Authorized administrator ID (NULL for candidates).
- `approval_timestamp` (`TIMESTAMP WITH TIME ZONE`): Date of formal promotion.
- `notes` (`TEXT`): Lineage notes and selective accuracy metrics.

### 2.2 Authoritative Database Snapshot (PostgreSQL 16)
| Version | Model Family | Status | Active? | Artifact SHA-256 | Calibration | Operational Role |
|---|---|---|---|---|---|---|
| **`xgb-v3.0-real-candidate`** | `XGBoost` | **CANDIDATE** | **FALSE** | `c52b6369...` | `balanced-platt-v3.0` | **In-Memory Production Candidate** |
| **`xgb-v3.1-balanced-weights`** | `XGBoost` | **CANDIDATE** | **FALSE** | `e1858544...` | `balanced-platt-v3.0` | Cost-sensitive minority challenger |
| **`xgb-v3.2-refined`** | `XGBoost` | **CANDIDATE** | **FALSE** | `ac3fc111...` | `balanced-platt-v3.0` | Regularized tree depth challenger |
| **`rf-v3.0-real-candidate`** | `RandomForest`| **CANDIDATE** | **FALSE** | `4a893673...` | None | V3 Random Forest baseline |
| **`rf-v2.0-real-candidate`** | `RandomForest`| **RETIRED** | **FALSE** | `bb14f061...` | None | Deprecated V2 model |
| **`rf-v1.0-benchmark`** | `RandomForest`| **APPROVED** | **FALSE** | `b5b5d880...` | None | Legacy V1 synthetic benchmark |
| **`v1.0-synthetic-baseline`** | `XGBoost` | **APPROVED** | **FALSE** | `6b484b89...` | None | Legacy V1 synthetic model |
| **`iso-v1.0-anomaly`** | `IsolationForest`| **ACTIVE** | **TRUE** | `4215ae06...` | None | Live thermal anomaly radar |

---

## 3. Candidate Model Experiments & Performance Evidence

All candidate models were trained on canonical dataset `dataset_v3.2-real-final.csv` (1,674 rows, 18 features) with fixed seed 42, strict chronological splits (Train: 2022–24, Validation: 2025, Test: 2026), and spatial GroupKFold cross-validation across 4 regions:

| Candidate Model | Macro F1 | Balanced Accuracy | Multiclass Log Loss | Brier Score | ECE | Tier 1 Selective Acc | Latency (P50) |
|---|---|---|---|---|---|---|---|
| **`xgb-v3.0-real-candidate`** | 0.6444 | **74.01%** | **0.6916** | **0.0634** | 0.0956 | **97.26%** | 2.22 ms |
| **`xgb-v3.1-balanced-weights`**| **0.6480** | 73.93% | 0.6953 | 0.0637 | 0.1037 | **97.26%** | 2.15 ms |
| **`xgb-v3.2-refined`** | 0.6379 | 72.89% | 0.6944 | **0.0634** | **0.0855** | 93.42% | **1.81 ms** |
| **`rf-v3.0-real-candidate`** | 0.6066 | 70.14% | 1.7301 | 0.0848 | 0.1524 | 73.19% | 96.99 ms |
| **`et-v3.0-candidate`** | 0.5702 | 66.84% | 1.4004 | 0.0895 | 0.1150 | 68.80% | 48.50 ms |

### Experimental Conclusion:
- `xgb-v3.0-real-candidate` remains the production inference model.
- `xgb-v3.1-balanced-weights` demonstrates improved minority F1 on Mining Activity (0.6923 vs 0.6667) and is preserved as an audited challenger candidate in `ml/models/candidates/`.

---

## 4. Probability Calibration & Reliability Analysis

### 4.1 Calibration Protocol
- **Calibration Split:** Exclusively fit on the 2025 Validation split ($N = 506$).
- **Test Isolation:** Zero 2026 test observations were seen during calibrator fitting.
- **Formulation:** Balanced Platt multinomial logistic regression:
  $$P(Y = k \mid \mathbf{z}) = \frac{\exp(\mathbf{w}_k^T \mathbf{z} + b_k)}{\sum_{j=1}^K \exp(\mathbf{w}_j^T \mathbf{z} + b_j)}$$
  where $\mathbf{z}$ is the raw uncalibrated probability vector from XGBoost.

### 4.2 Impact on Calibration Error
- Uncalibrated Raw XGBoost ECE: **0.1842**
- Balanced Platt Calibrated XGBoost V3.0 ECE: **0.0956** (-48.1% calibration error reduction)
- Regularized XGBoost V3.2 ECE: **0.0855** (-53.6% calibration error reduction)

---

## 5. Tri-Tier Selective Prediction & Human-in-the-Loop Routing

To prevent false automation on ambiguous thermal events, the system enforces a 3-tier operational routing policy:

$$\text{Confidence } P \ge 0.65 \text{ and Margin } \Delta \ge 0.20 \implies \text{TIER 1 (Auto-Dispatch Candidate)}$$
$$\text{Confidence } P \ge 0.45 \text{ and Margin } \Delta \ge 0.08 \implies \text{TIER 2 (Analyst Review Queue)}$$
$$\text{Otherwise} \implies \text{TIER 3 (Uncertainty / Active Learning Queue)}$$

### Empirical Performance on 2026 Test Set (211 Labeled Events):
- **Tier 1 (Auto-Dispatch Candidate):** Coverage: **41.48%** (73 events) | Selective Accuracy: **97.26%** | Error Rate: **2.74%**.
- **Tier 2 (Analyst Review Queue):** Coverage: **53.98%** (95 events) | Selective Accuracy: **51.58%** | Human verification required.
- **Tier 3 (Uncertainty Queue):** Coverage: **4.55%** (8 events) | Residual Accuracy: **37.50%** | Abstention rate: **4.55%**.

---

## 6. Operational Drift Detection & Monitoring Service

The service `backend/app/services/ml/model_monitoring_service.py` continuously evaluates operational drift on streaming detections:
- **Feature Drift (PSI & KS):** Calculates Population Stability Index (PSI) and Kolmogorov-Smirnov test across all 18 features against the baseline training distribution.
- **Operational Health Tiers:**
  - `HEALTHY` ($\text{PSI} < 0.10$): Stable baseline.
  - `WATCH` ($0.10 \le \text{PSI} < 0.20$): Minor distribution variance.
  - `DRIFT_DETECTED` ($0.20 \le \text{PSI} < 0.25$): Statistically significant drift; alerts operator.
  - `SEVERE_DRIFT` ($\text{PSI} \ge 0.25$): Severe environmental or sensor shift; operator investigation required.
- **Non-Automatic Activation Rule:** Drift detection logs warnings and issues alerts to administrators, but **NEVER automatically activates or promotes models**.

---

## 7. Governed Retraining & Active Learning Pipeline

Implemented in `backend/app/services/ml/governed_retraining_service.py`:
- **HITL Segregation:** Analyst corrections in `verification_records` are strictly divided into:
  - `VERIFIED_GROUND_TRUTH` (`verification_action IN ('CONFIRM', 'CORRECT')` with verified label and $\ge 1$ corroborating evidence item).
  - `ANALYST_NOTE` / `UNVERIFIED_OPINION` (excluded from training data).
- **Retraining Cycle:**
  $$\text{MANUAL/SCHEDULED TRIGGER} \longrightarrow \text{VERIFIED DATA SNAPSHOT} \longrightarrow \text{POINT-IN-TIME CHECK} \longrightarrow \text{TRAIN CANDIDATE} \longrightarrow \text{EVALUATE} \longrightarrow \text{PLATT CALIBRATION} \longrightarrow \text{REGISTER AS CANDIDATE}$$
- A completed retraining run produces a new candidate with `status = 'CANDIDATE'` and `is_active = FALSE`. It never replaces the existing champion candidate.

---

## 8. Security & Deserialization Defenses

Hardened in `backend/app/services/ml/model_governance_service.py`:
1. **Directory Allowlist:** Artifact paths must strictly reside within `ml/models` or `ml/models/candidates`.
2. **Path Traversal Defense:** Paths containing `..` or relative directory traversal are rejected with `ModelGovernanceException`.
3. **Cryptographic Checksum Verification:** Before deserializing via `joblib.load()`, the file's SHA-256 hash is computed and verified against expected registry values.
4. **Promotion Authorization Gate:** Promotion requires an authorized administrator role (`ADMIN`), a detailed justification string ($\ge 20$ chars), and fails immediately if `ENABLE_AUTOMATED_MODEL_ACTIVATION` is enabled.

---

## 9. JARVIS Model Grounding & Epistemic Reasoning

JARVIS orchestrator and tool outputs have been aligned with strict probabilistic semantics:
- **Zero False Confirmation:** JARVIS is forbidden from stating "the model confirmed this". All references state *"the governed candidate model estimated [CLASS] with calibrated confidence X% (epistemic uncertainty: Y | human verification pending)"*.
- **Provenance Exposure:** JARVIS retrieves complete model metadata (`model_id`, `version`, `model_status = 'CANDIDATE'`, `artifact_sha256 = 'c52b6369...'`, `calibration_version`).

---

## 10. Rollback Runbook

If any ML candidate behavior causes operational regression:
```powershell
# 1. Verify current database registry state
python -c "from backend.app.core.database import SessionLocal; from sqlalchemy import text; db = SessionLocal(); [print(r) for r in db.execute(text('SELECT version, status, is_active FROM ml_model_registry')).fetchall()]"

# 2. Reset any candidate activation
python -c "from backend.app.core.database import SessionLocal; from sqlalchemy import text; db = SessionLocal(); db.execute(text(\"UPDATE ml_model_registry SET is_active = FALSE WHERE version = 'xgb-v3.0-real-candidate';\")); db.commit()"

# 3. Reload production inference service
# ProductionThermalInferenceService automatically reverts to xgb-v3.0-real-candidate
```
