# AGNI-NETRA — Database Schema & Data Models

## 1. Relational Architecture

The system implements a dual-mode spatial architecture:
- **Production Mode**: PostgreSQL 16 + PostGIS 3.4 with GiST spatial indexing on geography/geometry types.
- **Standalone / Dev Mode**: High-performance SQLite engine with pure Python Shapely spatial joins, bounding box filters, and convex hull generation for instant local development without external dependencies.

---

## 2. Core Tables (16 Entities)

1. `users` — Role-based identity (PUBLIC, RESEARCHER, INDUSTRY, ANALYST, AGENCY, ADMIN).
2. `data_sources` — External satellite and GIS provider adapters with health tracking.
3. `data_ingestion_jobs` — Scheduled and manual ingestion run records.
4. `thermal_detections` — Raw satellite thermal observations (FIRMS VIIRS/MODIS, Sentinel-2, Landsat).
5. `industrial_facilities` — Canonical known and verified industrial facility registry.
6. `candidate_facilities` — Autonomously discovered uncataloged industrial thermal sources.
7. `thermal_events` — Spatiotemporally clustered logical thermal events (DBSCAN 1.5km).
8. `historical_baselines` — Running mean FRP, standard deviation, and diurnal signatures per facility/cell.
9. `event_features` — Tabular 17-dimensional engineered feature vectors for ML models.
10. `model_versions` — Model registry tracking algorithm, dataset version, and metrics.
11. `model_predictions` — Inferred class, confidence, softmax probabilities, and SHAP values.
12. `risk_scores` — Transparent multi-criteria risk matrix scores and reason lists.
13. `alerts` — Correlated incident alerts with lifecycle states (NEW, ACKNOWLEDGED, RESOLVED).
14. `verification_records` — Human-in-the-loop analyst confirmations, overrides, and notes.
15. `satellite_observations` — Optical/SWIR imagery references (Sentinel-2, Landsat-8/9).
16. `audit_logs` — Enterprise security and analytical audit trails.
