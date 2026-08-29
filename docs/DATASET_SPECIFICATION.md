# AGNI-NETRA — Machine Learning Dataset Specification

## 1. Dataset Partitioning & Provenance Tiers

AGNI-NETRA strictly isolates real-world observational data, human analyst verified labels, weakly labeled cadastral heuristics, and synthetic simulation baselines.

```
ML DATASET ECOSYSTEM
├── dataset_v1.0 (Synthetic Calibration Baseline)
│   └── 1000 balanced calibration samples across 7 classes
│       Used strictly for algorithm verification & pipeline smoke tests.
│
├── dataset_v2_india_real (Real-World Indian Thermal Archives)
│   ├── Partition: REAL_OBSERVATION (NASA FIRMS Historical Archives 2021-2026)
│   ├── Partition: WEAKLY_LABELED (Spatial Intersection with CEA & OSM Facilities)
│   ├── Partition: HUMAN_VERIFIED (HITL Analyst Confirmed Verification Records)
│   └── Partition: ANOMALY_SURGES (Empirically Documented Thermal Accidents & Flaring)
```

---

## 2. 18-Dimensional Feature Space

Every thermal event is mapped into an 18-dimensional numerical feature vector before model inference:

| Index | Feature Name | Description | Units / Scale |
|---|---|---|---|
| 0 | `frp_max` | Maximum Fire Radiative Power in cluster | MW |
| 1 | `frp_avg` | Mean Fire Radiative Power | MW |
| 2 | `brightness_avg` | Mean Brightness Temperature | Kelvin |
| 3 | `brightness_max` | Peak Brightness Temperature | Kelvin |
| 4 | `detection_count` | Number of contributing satellite detections | Count |
| 5 | `satellite_count` | Number of distinct observing spacecraft | Count |
| 6 | `persistence_score` | Temporal recurrence span / days | Ratio [0.0 - 1.0] |
| 7 | `day_night_ratio` | Ratio of night-time detections to day-time | Ratio [0.0 - 1.0] |
| 8 | `baseline_deviation_ratio` | Current FRP relative to facility baseline $\mu$ | Ratio $\ge 0.0$ |
| 9 | `baseline_z_score` | Statistical Z-score deviation $(x - \mu)/\sigma$ | Standard Deviations ($\sigma$) |
| 10 | `dist_to_facility_m` | Distance to nearest registered industrial facility | Meters |
| 11 | `dist_to_candidate_m` | Distance to nearest candidate industrial cluster | Meters |
| 12 | `dist_to_forest_m` | Distance to nearest forest LULC polygon | Meters |
| 13 | `dist_to_agriculture_m`| Distance to nearest agricultural field | Meters |
| 14 | `dist_to_urban_m` | Distance to nearest urban built-up zone | Meters |
| 15 | `dist_to_water_m` | Distance to nearest water body | Meters |
| 16 | `is_industrial_lulc` | Binary indicator if centroid is inside industrial zone | $\{0, 1\}$ |
| 17 | `swir_reflectance_ratio`| Sentinel-2 B12/B11 or SWIR radiance ratio | Ratio $\ge 0.0$ |

---

## 3. Label Categories (7 Classes)

1. **`Industrial Fire`**: Uncontrolled structural, tank farm, or chemical fire within an industrial facility footprint.
2. **`Gas Flare`**: Controlled continuous or elevated flaring at refineries, petrochemical plants, and upstream offshore/onshore wells.
3. **`Forest Fire`**: Wildfire / biomass burning in reserve forests, national parks, and deciduous woodland.
4. **`Agricultural Burning`**: Seasonal post-harvest stubble / crop residue burning in rural agrarian belts.
5. **`Mining Activity`**: Coal seam fire, overburden dump fire, or opencast blasting thermal signature.
6. **`Other Thermal Source`**: Brick kilns, landfill spontaneous combustion, cremation sites, or localized urban burning.
7. **`Uncertain`**: High entropy / ambiguous feature signature requiring Human-in-the-Loop verification.
