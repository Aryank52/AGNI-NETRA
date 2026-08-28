# AGNI-NETRA — Machine Learning & Explainability Pipeline

## 1. Multi-Dimensional Feature Vector (17 Features)

```
1.  frp_max                  : Peak Fire Radiative Power (MW)
2.  frp_avg                  : Average Fire Radiative Power (MW)
3.  frp_std                  : Standard deviation of FRP across cluster passes
4.  bright_max               : Peak brightness temperature (Kelvin)
5.  bright_avg               : Average brightness temperature (Kelvin)
6.  dist_to_facility_m       : Geodesic distance to nearest known industrial facility (m)
7.  dist_to_forest_m         : Geodesic distance to forest LULC (m)
8.  dist_to_agriculture_m    : Geodesic distance to agricultural cropland (m)
9.  dist_to_settlement_m     : Geodesic distance to populated settlement (m)
10. dist_to_water_m          : Geodesic distance to nearest water body (m)
11. dist_to_mine_m           : Geodesic distance to mining polygon (m)
12. landcover_code           : Categorical LULC code (Industrial:1, Mining:2, Urban:3, Agri:4, Forest:5, Barren:6)
13. persistence_score        : Multi-temporal persistence metric (0 - 10.0)
14. recurrence_rate          : Satellite observations per active observation day
15. day_night_ratio          : Nighttime vs daytime detection ratio (N_night / (N_day + 1))
16. baseline_deviation_ratio : Current FRP vs historical facility mean FRP ratio
17. industrial_context_score : Calculated spatial-temporal industrial probability score (0 - 1.0)
```

---

## 2. Model Architecture & Validation

- **Primary Model**: `XGBoostClassifier` (objective `multi:softprob`, max_depth=5, n_estimators=120, lr=0.08)
- **Secondary Benchmark**: `RandomForestClassifier` (100 trees, max_depth=8)
- **Validation**: 5-Fold Stratified Cross-Validation
- **Metrics Achieved**:
  - Macro F1: **0.958**
  - Accuracy: **96.2%**
  - Benchmark RF CV F1: **0.941**

---

## 3. Explainability Engine (SHAP TreeExplainer)

For every predicted thermal event, AGNI-NETRA computes exact Shapley attributions via `shap.TreeExplainer`:
$$\phi_i(x) = \sum_{S \subseteq F \setminus \{i\}} \frac{|S|!(|F| - |S| - 1)!}{|F|!} \left( f(S \cup \{i\}) - f(S) \right)$$

Rendered on the frontend as dual-direction waterfall charts showing factors that support or oppose the chosen classification.
