# AGNI-NETRA -- PHASE 6C: EVIDENCE VECTOR + ML FEATURE VALIDATION REPORT

**Generated:** 2026-09-01T07:42:40.719311+00:00  
**Status:** `PHASE_6C_COMPLETE`  
**Database Authority:** PostgreSQL 16.15 / PostGIS 3.4.2 (`agni_netra`)  
**Provenance Hash (SHA-256):** `9a73ac9ca55aedb50423e679df27b3eb5a958cabf15c49c1e831cc22c99672ab`

---

## 1. Live Authoritative Database Inventory

| Table Name | Live Authoritative Record Count | Purpose & Description |
| :--- | :--- | :--- |
| `thermal_detections` | **8,221,474** | Active VIIRS/MODIS thermal observation telemetry (2022, 2023, 2025, 2026). |
| `thermal_history` | **8,221,562** | Historical FIRMS telemetry repository (Authoritative 2024 archive). |
| `industrial_facilities` | **35,675** | Validated industrial installations, refineries, power stations & chemical facilities. |
| `facility_baselines` | **35,579** | Multi-year empirical thermal baselines, percentiles (P25--P99), active days & frequency. |
| `mining_thermal_associations` | **98,793** | Multi-distance (500m, 1km, 2km) PostGIS spatial associations to mining leases. |
| `facility_mining_evidence` | **203** | Synchronized evidence records fusing OSM facilities with IBM mineral resources. |
| `historical_baselines` | **18** | Regional 0.25 deg grid baselines with Jan--Dec monthly seasonality profiles. |
| `thermal_events` | **73** | Spatiotemporally clustered thermal event entities. |
| `event_features` | **73** | Multivariate 18-dimensional engineered feature vectors. |
| `model_predictions` | **73** | AI inference records with class probabilities and SHAP explanations. |
| `risk_scores` | **73** | Transparent multi-factor risk scores (0--100) and operational risk bands. |
| `alerts` | **7** | Operational dispatch alerts with multi-channel routing. |
| `verification_records` | **24** | Ground truth analyst verifications with Sentinel-2 SWIR evidence. |
| `ml_model_registry` | **3** | Model versioning, lineage, holdout metrics & deployment status. |
| `dataset_registry` | **2** | Dataset versioning with explicit provenance tracking. |

### Year-wise Authoritative FIRMS Observations
* **2022 Official Authoritative:** `1,274,383`
* **2022 Isolated Pilot/Demo:** `210,000`
* **2023 Official Authoritative:** `1,244,759`
* **2024 Official Authoritative:** `1,711,626`
* **2025 Official Authoritative:** `2,007,898`
* **2026 Baseline Authoritative:** `1,772,684`
* **Total Multi-Year Official Observations:** **`8,011,350`**

---

## 2. Historical Count Definition Taxonomy & Divergence Analysis

```
+--------------------------------+------------------------------------------------+
| Terminology                    | Exact Definition & Scope                       |
+--------------------------------+------------------------------------------------+
| Source Raw CSV Rows            | Raw lines in upstream NASA FIRMS archive ZIPs  |
| Unique Source Observations     | Spatially clipped to Survey of India bounds    |
| Database Partition Rows        | Sub-second deduped authoritative records       |
| Isolated Pilot Rows            | Separated demo data (is_demo = TRUE)           |
| Derived Intelligence Records   | Baselines, spatial joins & feature vectors     |
+--------------------------------+------------------------------------------------+
```

* **Explanatory Divergence Note (2025 Data):**
  - Raw Source CSV rows: `2,015,957`
  - In-Bounds Indian Territorial observations: `2,008,112` (7,845 non-Indian oceanic / cross-border points excluded)
  - Deduplicated Database records: `2,007,898` (214 duplicate instrument sensor pings resolved)
  - *No raw records were modified or deleted; strict deterministic spatial containment explains all differences.*

---

## 3. Demo / Pilot Contamination Test Results

* **Facility Baselines Demo Records:** `0` violations
* **Historical Baselines Demo Records:** `0` violations
* **Event Features Legacy Demo Events:** `15` legacy demo events
* **Dataset Registry Demo Eligibility:** `0` violations
* **Baseline Isolation Verdict:** **`ZERO_CONTAMINATION_IN_BASELINES`** -- All production baselines exclude demo records.

---

## 4. 18-Dimensional Event Feature Validation

| Feature Column | Physical Unit | Valid Range | Observed Min | Observed Max | Observed Mean | Range Status | Leakage Risk |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `frp_max` | Megawatts (MW) | `[0.0, 15000.0]` | 39.1 | 285.0 | 148.69 | `PASS` | `SAFE` |
| `frp_avg` | Megawatts (MW) | `[0.0, 10000.0]` | 28.4 | 249.38 | 135.37 | `PASS` | `SAFE` |
| `frp_std` | Megawatts (MW) | `[0.0, 5000.0]` | 0.0 | 52.69 | 3.08 | `PASS` | `SAFE` |
| `bright_max` | Kelvin (K) | `[200.0, 550.0]` | 336.0 | 403.86 | 344.22 | `PASS` | `SAFE` |
| `bright_avg` | Kelvin (K) | `[200.0, 550.0]` | 320.0 | 384.63 | 328.77 | `PASS` | `SAFE` |
| `delta_brightness` | Kelvin (K) | `[0.0, 250.0]` | 0.0 | 19.23 | 15.44 | `PASS` | `SAFE` |
| `dist_to_facility_m` | Meters (m) | `[0.0, 2000000.0]` | 0.0 | 964136.6 | 46032.46 | `PASS` | `SAFE` |
| `dist_to_forest_m` | Meters (m) | `[0.0, 2000000.0]` | 0.0 | 1128614.5 | 192768.37 | `PASS` | `SAFE` |
| `dist_to_agriculture_m` | Meters (m) | `[0.0, 2000000.0]` | 5000.0 | 1305299.3 | 79377.15 | `PASS` | `SAFE` |
| `dist_to_settlement_m` | Meters (m) | `[0.0, 2000000.0]` | 4200.0 | 12000.0 | 11572.6 | `PASS` | `SAFE` |
| `dist_to_water_m` | Meters (m) | `[0.0, 2000000.0]` | 15000.0 | 1335938.1 | 74574.94 | `PASS` | `SAFE` |
| `dist_to_mine_m` | Meters (m) | `[0.0, 2000000.0]` | 299611.2 | 1302902.4 | 1002849.98 | `PASS` | `SAFE` |
| `landcover_code` | Categorical Integer [0..7] | `[0, 7]` | 1.0 | 4.0 | 1.23 | `PASS` | `SAFE` |
| `persistence_score` | Score [0.0..10.0] | `[0.0, 10.0]` | 1.73 | 8.23 | 3.32 | `PASS` | `POTENTIAL_LEAKAGE` |
| `recurrence_rate` | Rate [0.0..10.0] | `[0.0, 10.0]` | 0.03 | 6.0 | 0.26 | `PASS` | `POTENTIAL_LEAKAGE` |
| `day_night_ratio` | Ratio [0.0..50.0] | `[0.0, 50.0]` | 0.85 | 6.0 | 0.94 | `PASS` | `SAFE` |
| `baseline_deviation_ratio` | Ratio [0.0..100.0] | `[0.0, 100.0]` | 1.0 | 34.94 | 7.88 | `PASS` | `POTENTIAL_LEAKAGE` |
| `industrial_context_score` | Score [0.0..1.0] | `[0.0, 1.0]` | 0.2 | 0.95 | 0.88 | `PASS` | `SAFE` |

---

## 5. Temporal Leakage Audit & Point-in-Time Protocol

* **Safe Features (15/18):** `frp_max`, `frp_avg`, `frp_std`, `bright_max`, `bright_avg`, `delta_brightness`, `dist_to_facility_m`, `dist_to_forest_m`, `dist_to_agriculture_m`, `dist_to_settlement_m`, `dist_to_water_m`, `dist_to_mine_m`, `landcover_code`, `day_night_ratio`, `industrial_context_score`.
* **Potential Leakage Features (3/18):** `persistence_score`, `recurrence_rate`, `baseline_deviation_ratio`.
* **Enforced Remedy for ML Training Dataset (v3.0):**
  > [!IMPORTANT]
  > **Point-in-Time Expanding Window Protocol:** All recurrence rates, active days, and facility baseline percentiles for any historical event at timestamp $t$ MUST be computed strictly using historical observations prior to $t$ ($t_{obs} < t$). Full 5-year future baselines must never be evaluated against past events during model training.

---

## 6. Spatial Leakage Audit & Grouped Split Design

* **Autocorrelation Hazard:** Thermal observations from the same refinery, power station, or coal mine across different days share invariant spatial context. Random train/test splits cause data leakage and artificially inflated performance.
* **Spatial Split Strategy:** **`FACILITY_AND_DISTRICT_GROUP_SPLIT` (GroupKFold)**
* **Geographic Holdout Clusters:**
  1. *Eastern Coal Belt (Angul, Jharsuguda, Korba, Dhanbad, Bokaro)*
  2. *Western Petrochemical Hub (Jamnagar, Bharuch, Surat)*
  3. *Northern Agricultural Corridor (Bathinda, Sangrur, Ludhiana, Karnal)*
  4. *Southern Mineral Belt (Bellary, Cuddalore, Visakhapatnam)*

---

## 7. Chronological Temporal Split Specification

```
2022                 2023                 2024                 2025                 2026
[------------------ TRAINING PERIOD -------------------] [--- VALIDATION ---] [--- TEST (HOLDOUT) ---]
          4,230,768 Multi-Year Observations                   2,007,898 Obs        1,772,684 Obs
       (Baseline Learning & Model Fitting)               (Threshold Tuning)    (True Out-of-Time Eval)
```

---

## 8. Multi-Source Evidence Provenance Audit

| Evidence Source | Provenance Type | Total Coverage | Real-Time Latency | Missingness Rate | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **NASA FIRMS** | `REAL` | 8.22M Observations | <30s Post-Pass | 0.0% | **AUTHORITATIVE** |
| **OSM Facilities** | `REAL` | 35,674 Facilities | Precomputed R-Tree | 0.0% | **AUTHORITATIVE** |
| **CEA Registry** | `REAL` | 323 Power Stations | Precomputed PostGIS | 0.0% | **AUTHORITATIVE** |
| **IBM Mines** | `REAL` | 4,983 Mining Leases | Precomputed PostGIS | 0.0% | **AUTHORITATIVE** |
| **PARIVESH EC** | `REAL` | 3,224 Clearances | Precomputed Context | 0.0% | **AUTHORITATIVE** |
| **Admin Geography** | `REAL` | 7,595 Polygons | Containment <5ms | 0.0% | **AUTHORITATIVE** |
| **Bhuvan LULC** | `REAL` | National 50m Raster | Spatial Query <10ms | 0.0% | **AUTHORITATIVE** |
| **ESA WorldCover** | `REAL` | 10m Fallback Raster | Complementary Grid | 0.0% | **COMPLEMENTARY** |
| **FSI ISFR** | `REAL` | 755 District Stats | Spatial Aggregation | 0.0% | **AUTHORITATIVE** |
| **WII Protected** | `REAL` | 1,014 PAs | Spatial Buffer Join | 0.0% | **AUTHORITATIVE** |

---

## 9. Feature Colinearity & Redundancy Analysis

* **Identified Collinear Pairs (|r| >= 0.70):**
  - `frp_max` <--> `frp_avg` (r = 0.966): Max and average radiative power in small clusters.
  - `bright_max` <--> `bright_avg` (r = 0.978): Maximum and average brightness temperature.
  - `dist_to_agriculture_m` <--> `dist_to_settlement_m` (r = -0.987): Settlement-agriculture proximity inverse relationship.
  - `recurrence_rate` <--> `day_night_ratio` (r = 0.968): Recurrence diurnal signature correlation.
* **Mitigation:** Retain both in tree-based XGBoost models (non-linear splitters handle colinearity natively); regularize via `colsample_bytree = 0.8` and `subsample = 0.8`.

---

## 10. Model Contract & Registry Audit

| Model Name | Registry Version | Algorithm | Dataset Lineage | Contract Status |
| :--- | :--- | :--- | :--- | :--- |
| **Random Forest Benchmark** | `rf-v1.0-benchmark` | Random Forest | `v1.0-synthetic-grounded` | **BENCHMARK BASELINE** |
| **Isolation Forest Radar** | `iso-v1.0-anomaly` | Isolation Forest | `v1.0-synthetic-grounded` | **ACTIVE ANOMALY RADAR** |
| **XGBoost Classifier** | `v1.0-synthetic-baseline` | XGBoost | `v1.0-synthetic-grounded` | **CALIBRATION BASELINE** |

* **Model Input Contract:** All models expect standard 18-dimensional feature vectors (`FEATURE_COLUMNS`).
* **Production Lineage Requirement:** Final models must be trained on `v3.0-authoritative-multiyear` following Point-in-Time feature extraction.

---

## 11. Required Pre-Training Prerequisites (Action Plan for Phase 7)

1. **Construct `dataset_v3_authoritative`**: Generate point-in-time feature vectors for the 2022--2024 training split ($t_{obs} < t$). Filter out any events with `is_demo = true`.
2. **Apply Spatial Grouping**: Assign `district_id` and `facility_id` group markers to eliminate spatial leakage.
3. **Execute Chronological Validation**: Fit models on 2022--2024, tune thresholds on 2025, and evaluate on 2026.
4. **Lock Provenance Manifest**: Register dataset artifact in `dataset_registry` with SHA-256 hash.

```
==========================================================================================
  PHASE 6C VALIDATION RESULT: PHASE_6C_COMPLETE
==========================================================================================
```
