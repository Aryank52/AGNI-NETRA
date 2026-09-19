# AGNI-NETRA — WP5 Machine Learning Subsystem Audit
**Document ID:** `DOC-WP5-ML-AUDIT-001`  
**Execution Date:** 2026-09-19  
**Branch:** `development/post-freeze-intelligence-hardening`  
**Baseline Reference:** Phase 26 Baseline (`eb7824e6e58eb61f376a4dadb804984950f624e8`) + WP1–WP4

---

## 1. Executive Summary

This audit establishes a zero-assumption, empirically verified baseline of AGNI-NETRA's machine-learning stack prior to WP5 enhancements. Every artifact, training pipeline, inference path, and governance record was directly inspected.

### Core Audit Findings:
1. **Model Governance Clarity:** In PostgreSQL `ml_model_registry`, `xgb-v3.0-real-candidate` is registered with `status = 'CANDIDATE'` and `is_active = FALSE`. However, `ml/inference/production_inference_service.py` loads this candidate artifact into memory to serve live production inference for the proactive intelligence core. This dual reality (*in-memory operational candidate vs. inactive registry status*) is properly governed by `ENABLE_AUTOMATED_MODEL_ACTIVATION = False`, but requires explicit architectural disambiguation between **INFERENCE ARTIFACT** and **GOVERNED ACTIVE CHAMPION**.
2. **Canonical Dataset Integrity:** The canonical training dataset `dataset_v3.2-real-final.csv` (SHA-256: `9677c6d6...`) contains 1,674 rows (754 Train, 506 Validation, 414 Test). It incorporates lookback-normalized recurrence rates and enforces 100% point-in-time compliance ($t_{\text{feature}} \le t_{\text{obs}}$).
3. **Weak Class Performance:** While the model achieves 93.18% spatial cross-validation Macro F1 on synthetic/semi-synthetic splits, its frozen chronological 2026 test split reveals sharp class-wise disparity: High performance on Forest Fire (F1: 0.88) and Agricultural Burning (F1: 0.85), but weak generalization on minority classes: **Gas Flare** (F1: 0.54, recall: 0.44) and **Mining Activity** (F1: 0.52, recall: 0.38).
4. **SHAP Cold-Start Penalty:** SHAP `TreeExplainer` initialization from `shap_explainer_v3.joblib` incurs a 1,200 ms latency spike on the first prediction call due to JIT compilation of the tree structures, though warm calls complete in ~3.8 ms.
5. **Untrusted Deserialization Vulnerability:** Artifact loading currently accepts arbitrary filesystem paths without cryptographic checksum validation or path traversal protection.

---

## 2. Complete ML Stack Component Audit Matrix

Each ML subsystem component is classified according to the canonical taxonomy:
`IMPLEMENTED`, `VERIFIED`, `PARTIAL`, `DEGRADED`, `MISSING`, `CANDIDATE`, `NOT CONFIGURED`, `SIMULATED`, `FUTURE`, `OUT OF SCOPE`.

| # | Subsystem / Component | Path / Location | Classification | Empirical Findings & Rationale |
|---|---|---|---|---|
| **1** | Canonical Training Dataset | `ml/dataset/dataset_v3.2-real-final.csv` | **VERIFIED** | 1,674 rows, 18 features, SHA-256: `9677c6d6...`. Includes lookback normalization. Zero synthetic substitution. |
| **2** | Historical Raw Telemetry | PostgreSQL `thermal_detections` | **VERIFIED** | 8.22M observations (2022–2026) intact. 0 observations deleted or modified. |
| **3** | Feature Schema Definition | `FEATURE_COLUMNS` in `ml/inference/production_inference_service.py` | **VERIFIED** | 18 standardized features (6 physical thermal, 6 geodetic proximity, 1 LULC, 5 contextual/temporal). |
| **4** | Point-in-Time Discipline | `ml/dataset/dataset_builder.py` | **VERIFIED** | Enforces $t_{\text{feature}} \le t_{\text{obs}}$. Sliding 30d persistence and 365d recurrence are strictly backward-looking. |
| **5** | Primary Classifier Artifact | `ml/models/xgb_v3_real_candidate.joblib` | **CANDIDATE** | XGBoost v3 model binary (960,235 bytes, SHA-256: `c52b6369...`). Loaded in memory; `status = CANDIDATE` in DB. |
| **6** | Baseline Model Artifact | `ml/models/rf_v3_real_candidate.joblib` | **CANDIDATE** | Random Forest baseline (2,010,137 bytes, SHA-256: `4a893673...`). 220 estimators, max_depth=11. Inactive in DB. |
| **7** | Legacy Synthetic Models | `ml/models/xgboost_classifier_v1.joblib` | **RETIRED / DEGRADED** | V1 synthetic model trained on 2,800 synthetic points. Replaced by V3 real telemetry models. |
| **8** | Probability Calibrator | `ml/models/xgb_v3_calibrated_candidate.joblib` | **VERIFIED** | Balanced Platt multinomial logistic regression fit strictly on 2025 Validation split. Brier: 0.0656. |
| **9** | SHAP Explainer Artifact | `ml/models/shap_explainer_v3.joblib` | **PARTIAL** | TreeExplainer (3,926,131 bytes, SHA-256: `58537e26...`). Explanations are valid, but cold start is 1,200 ms. |
| **10** | Anomaly Detection Model | `ml/models/isolation_forest_v1.joblib` | **IMPLEMENTED** | Isolation Forest for thermal signature anomaly radar (`iso-v1.0-anomaly`). Status: ACTIVE in registry. |
| **11** | Model Registry Table | PostgreSQL `ml_model_registry` | **PARTIAL** | 7 records. Tracks id, version, dataset_version, status, is_active. Missing explicit SHA-256 and promotion audit log columns. |
| **12** | Dataset Registry Table | PostgreSQL `dataset_registry` | **VERIFIED** | Tracks dataset versions, record counts, verification status, and JSON manifest paths. |
| **13** | Production Inference Service | `ml/inference/production_inference_service.py` | **IMPLEMENTED** | Calibrated inference, SHAP extraction, Tri-Tier routing, risk score, audit logging to `ml_prediction_audit_logs`. |
| **14** | Secondary Predictor Path | `ml/inference/predictor.py` | **DEGRADED** | Legacy v1 inference engine using deprecated `xgboost_classifier_v1.joblib`. Tech debt; retained for backward API compat. |
| **15** | Feature Drift Monitoring | `database/phase8g_feature_drift_audit.py` | **PARTIAL** | PSI formulation implemented and tested offline, but lacks a continuous online streaming evaluation service. |
| **16** | Tri-Tier HITL Routing | `production_inference_service.py` (`determine_tri_tier_routing`) | **VERIFIED** | Tier 1 (Auto-dispatch candidate: $P \ge 0.65, \Delta \ge 0.20$), Tier 2 (Review queue), Tier 3 (Uncertainty queue). |
| **17** | Active Learning Feedback | PostgreSQL `verification_records` | **PARTIAL** | Stores analyst corrections (`CONFIRM`, `CORRECT`, `MARK_UNCERTAIN`), but lacks an authoritative retraining dataset builder. |
| **18** | Retraining Automation | `ml/training/train_classifier.py` | **DEGRADED** | Script still contains v1 synthetic data generation defaults. Lacks automated governance gate against candidate promotion. |
| **19** | Model Deserialization Security | `joblib.load()` across codebase | **DEGRADED** | No cryptographic SHA-256 validation before unpickling; vulnerable to path traversal if exposed to untrusted input. |
| **20** | JARVIS Model Grounding | `backend/app/services/jarvis/` | **PARTIAL** | Correctly queries model version, but occasionally uses assertive language ("Authoritative Model") instead of epistemic estimates. |
| **21** | Admin ML Monitoring View | `backend/app/api/v1/endpoints/ml.py` | **VERIFIED** | `/model-info` returns candidate metrics, calibration info, and gate status. Requires cryptographic hash display. |
| **22** | Automated Model Activation Gate | `ENABLE_AUTOMATED_MODEL_ACTIVATION = False` | **VERIFIED** | Hard-blocked in `backend/app/core/config.py`. Prevents automated champion displacement. |

---

## 3. Dataset Governance & Provenance Deep-Dive

### 3.1 Canonical Dataset: `v3.2-real-final`
- **Path:** `E:\PROJECTS\AGNI-NETRA\ml\dataset\dataset_v3.2-real-final.csv`
- **SHA-256:** `9677c6d65ef8f2ab388160079e868ed2bf17307a9e462e1fba26517ae9bedd0e`
- **Total Records:** 1,674
- **Temporal Partitions:**
  - **TRAIN (2022-01-01 to 2024-12-31):** 754 rows (Labeled: 382, Uncertain: 372)
  - **VALIDATION (2025-01-01 to 2025-12-31):** 506 rows (Labeled: 256, Uncertain: 250) — *Exclusively reserved for calibration fitting.*
  - **TEST (2026-01-01 to 2026-09-01):** 414 rows (Labeled: 211, Uncertain: 203) — *Frozen chronological out-of-time evaluation.*

### 3.2 Label Distribution Across Splits (Labeled Subset = 849 rows)
| Target Class | Full Dataset | TRAIN (2022–24) | VAL (2025) | TEST (2026) | Operational Significance |
|---|---|---|---|---|---|
| **Forest Fire** | 181 | 82 | 54 | 45 | High ecological hazard; daytime dominant |
| **Other Thermal Source** | 183 | 81 | 56 | 46 | Ambient/unclassified industrial baseline |
| **Agricultural Burning** | 176 | 79 | 53 | 44 | Seasonal crop residue burns; low FRP |
| **Industrial Fire** | 134 | 60 | 41 | 33 | Catastrophic plant emergency; high risk |
| **Gas Flare** | 100 | 45 | 30 | 25 | Stationary 24x7 refinery/wellhead emission |
| **Mining Activity** | 75 | 35 | 22 | 18 | Deep opencast/coal seam thermal signature |
| **Uncertain (Unlabeled)** | 825 | 372 | 250 | 203 | Epistemic ambiguity; routed to HITL Tier 3 |
| **Total** | **1,674** | **754** | **506** | **414** | |

---

## 4. Feature Engineering & Leakage Analysis

### 4.1 Feature Schema (18 Features)
All features are standardized in `ml/inference/production_inference_service.py`:
1. `frp_max` (MW): Maximum Fire Radiative Power in cluster.
2. `frp_avg` (MW): Mean cluster FRP.
3. `frp_std` (MW): Standard deviation of FRP across cluster observations.
4. `bright_max` (K): Peak brightness temperature in channel 4 (375m).
5. `bright_avg` (K): Mean brightness temperature.
6. `delta_brightness` (K): Peak minus average brightness.
7. `dist_to_facility_m` (m): Haversine distance to nearest industrial facility (35,570 active facilities).
8. `dist_to_forest_m` (m): Distance to nearest FSI classified forest boundary.
9. `dist_to_agriculture_m` (m): Distance to agricultural land cover.
10. `dist_to_settlement_m` (m): Distance to human settlement / urban area.
11. `dist_to_water_m` (m): Distance to water body / coastline.
12. `dist_to_mine_m` (m): Distance to nearest IBM mineral lease boundary.
13. `landcover_code` (1–8): Categorical LULC code (1=Industrial, 2=Settlement, 3=Agri, 4=Water, 5=Forest, 6=Mining, 7=Barren, 8=Other).
14. `persistence_score` (0.0–1.0): Active observation days in trailing 30-day window divided by 30.
15. `recurrence_rate` (log scale): $\log(1 + \text{count}_{365d} \times \frac{365}{\text{avail\_days}})$. Boundary-safe lookback formulation.
16. `day_night_ratio` (ratio): Daytime detections divided by nighttime detections.
17. `baseline_deviation_ratio` (ratio): FRP max divided by prior 365-day mean FRP for 0.1° cell.
18. `industrial_context_score` (0.0–1.0): Spatial kernel density of industrial infrastructure.

### 4.2 Temporal Leakage Verification
- **Audit Result:** **ZERO LEAKAGE CONFIRMED.**
- All temporal features (`persistence_score`, `recurrence_rate`, `baseline_deviation_ratio`) strictly query observations where:
  $$t_{\text{historical}} < t_{\text{event}}$$
- Future observations are never visible to feature extraction queries.

---

## 5. Model Registry & Governance Audit

### 5.1 Active Registry Records in PostgreSQL (`ml_model_registry`)
```
- iso-v1.0-anomaly:          status = ACTIVE,    is_active = TRUE   (Isolation Forest Anomaly Radar)
- rf-v1.0-benchmark:         status = APPROVED,  is_active = FALSE  (Random Forest Benchmark v1)
- rf-v2.0-real-candidate:    status = ACTIVE,    is_active = TRUE   (Legacy V2 active marker)
- rf-v3.0-real-candidate:    status = CANDIDATE, is_active = FALSE  (V3 RF Baseline)
- v1.0-synthetic-baseline:   status = APPROVED,  is_active = FALSE  (Legacy Synthetic XGBoost)
- xgb-v2.0-real-candidate:   status = CANDIDATE, is_active = FALSE  (V2 Candidate)
- xgb-v3.0-real-candidate:   status = CANDIDATE, is_active = FALSE  (V3 Champion Inference Candidate)
```

### 5.2 Architectural Disambiguation Required
- **The Problem:** `rf-v2.0-real-candidate` currently has `is_active = TRUE` in the registry table, while `xgb-v3.0-real-candidate` has `is_active = FALSE`, yet the live codebase (`production_inference_service.py`) exclusively loads and evaluates `xgb-v3.0-real-candidate`.
- **The Remedy:**
  1. Retire `rf-v2.0-real-candidate` (`status = RETIRED, is_active = FALSE`).
  2. Maintain `xgb-v3.0-real-candidate` as `status = CANDIDATE, is_active = FALSE` in accordance with `ENABLE_AUTOMATED_MODEL_ACTIVATION = False`.
  3. Clearly document that `xgb-v3.0-real-candidate` is the **GOVERNED INFERENCE CANDIDATE**, operating under provisional operational evaluation.

---

## 6. Weak Class Performance Analysis

Evaluation of `xgb-v3.0-real-candidate` on the frozen 2026 Test split (211 labeled cases):
| Class | Precision | Recall | F1-Score | Support | Operational Risk Profile |
|---|---|---|---|---|---|
| **Forest Fire** | 0.86 | 0.91 | **0.88** | 45 | Robust canopy detection; clear thermal/spatial signature. |
| **Agricultural Burning** | 0.83 | 0.86 | **0.85** | 44 | Distinct seasonal/daytime signature in agri zones. |
| **Industrial Fire** | 0.76 | 0.73 | **0.74** | 33 | Moderate performance; occasional confusion with high-FRP flares. |
| **Other Thermal Source** | 0.65 | 0.70 | **0.67** | 46 | Catch-all class with heterogeneous characteristics. |
| **Gas Flare** | 0.69 | **0.44** | **0.54** | 25 | **Weak recall.** Flare stacks confused with industrial fires. |
| **Mining Activity** | 0.78 | **0.38** | **0.52** | 18 | **Critical recall failure.** 62% of mine fires missed due to small training support ($N=35$). |

### Root Cause of Weak Classes:
1. **Support Imbalance:** Mining Activity has only 35 training examples compared to 82 for Forest Fire.
2. **Feature Overlap:** Gas Flares and Industrial Fires share near-zero distance to industrial facilities (`dist_to_facility_m < 200m`). Differentiation relies heavily on `persistence_score` and `frp_std`.

---

## 7. Explainability & SHAP Latency Audit

- **Artifact:** `ml/models/shap_explainer_v3.joblib` (3.92 MB)
- **Engine:** `shap.TreeExplainer(xgb_model)`
- **Cold-Start Latency:** **1,248 ms** on process initialization (first prediction).
- **Warm Latency:** **3.82 ms** per prediction.
- **Optimization Strategy:** Execute a lightweight dummy warmup vector (`np.zeros((1, 18))`) during `load_artifacts()`. This pre-compiles internal tree structures so that the first incoming production request experiences zero cold-start delay.

---

## 8. Security & Deserialization Defense Audit

- **Current Practice:** Models are deserialized directly using `joblib.load(path)`.
- **Vulnerabilities:**
  1. No check for directory traversal (`../`).
  2. No validation of file SHA-256 against authorized manifest.
  3. No validation of deserialized object class type.
- **Hardening Mandate for WP5:** Implement a secure loading envelope in `model_governance_service.py` that enforces strict allowlists, verifies SHA-256 hashes, and prevents untrusted object execution.

---

## 9. WP5 Implementation Action Plan Summary

1. **Registry Hardening:** Enrich `ml_model_registry` schema with `artifact_sha256`, `model_family`, `feature_schema_version`, and `taxonomy_version`.
2. **Secure Artifact Loading:** Add SHA-256 checksum verification and path canonicalization.
3. **SHAP Warmup:** Eliminate cold-start latency spike in `production_inference_service.py`.
4. **Candidate Experiments:** Train and evaluate 5 candidate architectures on `dataset_v3.2-real-final` with cost-sensitive class weights to target Gas Flare and Mining Activity recall.
5. **Continuous Drift Monitoring:** Implement online PSI service with health states (`HEALTHY`, `WATCH`, `DRIFT_DETECTED`, `SEVERE_DRIFT`).
6. **HITL Feedback Segregation:** Isolate verified ground truth from analyst notes.
7. **JARVIS Epistemic Alignment:** Standardize probabilistic reporting language across JARVIS orchestrator and tools.
8. **25-Scenario Test Suite:** Build `tests/test_wp5_ml_governance.py` validating all invariants and regression gates.
