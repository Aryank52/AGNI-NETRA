# AGNI-NETRA — Machine Learning Model Registry

## 1. Model Lifecycle & Production Status

AGNI-NETRA implements a dual-classifier architecture with exact Shapley value explainability and multivariate anomaly scoring.

| Registry ID | Model Architecture | Role | Active Dataset | Macro F1 | Accuracy | Status |
|---|---|---|---|---|---|---|
| **`xgb_industrial_v1.0`** | XGBoost Classifier (`max_depth=5`, `n_estimators=150`) | Primary 7-Class Thermal Classifier | `dataset_v1.0` | **0.958** | **96.2%** | **ACTIVE_PRODUCTION** |
| **`rf_benchmark_v1.0`** | Random Forest (`n_estimators=100`, `min_samples_split=3`) | Baseline Comparison Benchmark | `dataset_v1.0` | 0.941 | 94.8% | STANDBY_BENCHMARK |
| **`iforest_anomaly_v1.0`** | Isolation Forest (`contamination=0.05`) | Multivariate Anomaly Radar | `dataset_v1.0` | N/A | N/A | **ACTIVE_PRODUCTION** |
| **`shap_tree_explainer`** | SHAP `TreeExplainer` on XGBoost | Feature Attribution Engine | Dynamic | N/A | N/A | **ACTIVE_PRODUCTION** |

---

## 2. Validation & Holdout Strategy

To prevent data leakage and guarantee real-world generalization:
- **Spatial Holdout**: Entire geographical clusters (e.g., Gujarat Industrial Corridor, Singrauli Coal Basin) held out during validation.
- **Unseen Facility Testing**: Validation events evaluated strictly on facilities not present in the training set.
- **GroupKFold & TimeSeriesSplit**: Time-stratified splits preserving chronological precedence ($t_{\text{train}} < t_{\text{test}}$).

---

## 3. Explainability Engine (SHAP)

For every inference pass, the SHAP `TreeExplainer` computes exact local feature contributions:
$$\phi_i(x) = \sum_{S \subseteq F \setminus \{i\}} \frac{|S|!(|F| - |S| - 1)!}{|F|!} \left[ f_x(S \cup \{i\}) - f_x(S) \right]$$

The output is formatted into both an intuitive human-readable summary (e.g., *"Event categorized as Gas Flare driven by high diurnal persistence (+0.84), proximity to refinery (180m), and elevated SWIR radiance"*) and a quantitative JSON vector driving the frontend waterfall charts.
