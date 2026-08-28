# AGNI-NETRA — System Architecture Document

## 1. Executive Summary

**AGNI-NETRA** (*AI Geospatial Network for Industrial Thermal Risk & Anomaly Analysis*) is a comprehensive, production-grade geospatial intelligence and decision support platform built for **Smart India Hackathon 2026 (SIH26162)**.

The system ingests raw satellite thermal observations (NASA FIRMS VIIRS & MODIS, Sentinel-2 SWIR, Landsat TIRS), spatial data from OpenStreetMap, and Land Use / Land Cover (LULC) datasets to perform:

$$\text{DETECT} \longrightarrow \text{CLASSIFY} \longrightarrow \text{ANALYZE} \longrightarrow \text{EXPLAIN} \longrightarrow \text{PRIORITIZE} \longrightarrow \text{VERIFY}$$

---

## 2. Core Architectural Pillars

1. **Sensor-Agnostic Ingestion Architecture**: Standardizes multi-satellite observations into a single `NormalizedThermalObservation` format via decoupled source adapters.
2. **Spatiotemporal Event Clustering**: Converts multiple raw detections into cohesive `ThermalEvents` using spherical DBSCAN with Haversine metrics and convex hull geometries.
3. **Multi-Source Facility Registry & Canonical Resolution**: Unifies OSM, state pollution board databases, and mining registries.
4. **Candidate Facility Discovery (USP)**: Autonomously detects unregistered industrial thermal sources using persistence span, 24x7 diurnal ratios, and LULC isolation.
5. **Historical Thermal Baseline & Fingerprinting**: Establishes running $\mu_{frp}$, $\sigma_{frp}$, and diurnal profiles to detect sudden spikes (+3σ).
6. **Dual-Method Anomaly Detection**: Statistical Z-Score baseline deviation combined with unsupervised multivariate Isolation Forest.
7. **Explainable AI with SHAP**: TreeExplainer Shapley attribution charts explaining why an event was categorized.
8. **Transparent Multi-Criteria Risk Matrix**: Evaluates radiative heat, abnormality, population proximity, and hazard exposure ($0 - 100$).
9. **Human-in-the-Loop (HITL) Active Learning**: Analyst verification and label correction workflow feeding back into future training.

---

## 3. Data Tiering: RAW $\rightarrow$ PROCESSED $\rightarrow$ INTELLIGENCE

| Tier | Representation | Key Entities |
|---|---|---|
| **RAW** | Unmodified external observations | `thermal_detections`, `satellite_observations`, `data_sources` |
| **PROCESSED** | Cleaned, clustered, and spatially enriched records | `thermal_events`, `industrial_facilities`, `candidate_facilities`, `landcover_areas` |
| **INTELLIGENCE** | Derived analytical scores and explainability | `model_predictions`, `event_features`, `risk_scores`, `alerts`, `verification_records`, `reports` |

---

## 4. Technology Stack

- **Frontend**: Next.js 15 (App Router), React 19, TypeScript, Tailwind CSS, MapLibre GL JS, Recharts, Lucide Icons.
- **Backend**: FastAPI 0.115+, Pydantic v2, SQLAlchemy 2.0, AsyncPG, GeoAlchemy2, ReportLab, Passlib/Bcrypt.
- **GIS & Remote Sensing**: Shapely 2.0, GeoPandas, PyProj, GDAL.
- **Machine Learning & Explainability**: Scikit-Learn, XGBoost, SHAP TreeExplainer, Joblib.
- **Data Persistence**: PostgreSQL 16 + PostGIS 3.4 (with pure Python Shapely fallback engine for instant local execution), Redis 7, MinIO.
