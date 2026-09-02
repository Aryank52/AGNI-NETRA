# AGNI-NETRA: Executive Project Summary & System Status

**Project Title**: AGNI-NETRA (Automated Geospatial Network for Industrial & Natural Event Thermal Risk Assessment)  
**Full Scientific Title**: *AGNI-NETRA: A Geospatial Intelligence and Machine-Learning Platform for Satellite-Based Thermal Event Detection, Contextualization, Risk Assessment, and Human-in-the-Loop Decision Support in India*  
**Platform Version**: Production-Ready v1.0 (Phase 16 Controlled Go-Live)  
**Database**: PostgreSQL 16 + PostGIS 3.4 (EPSG:4326)  
**Primary Language Stack**: Python 3.12 (FastAPI), TypeScript / React 19 (Next.js 15), MapLibre GL 4.7  
**Operational Status**: **`HEALTHY / PRODUCTION-READY (CONTROLLED ACTIVATION)`**  
**Autonomous Dispatch Status**: **`DISABLED`** (`ENABLE_OPERATIONAL_DISPATCH_GATE = False`)  

---

## 1. Executive Summary

AGNI-NETRA is a production-grade, end-to-end Geospatial Intelligence (GEOINT) and Machine-Learning platform engineered to transform raw, low-context satellite thermal observations into actionable, contextualized, calibrated, and auditable operational intelligence across the Indian subcontinent.

The system ingests high-volume thermal telemetry from NASA FIRMS (VIIRS 375m and MODIS 1km constellations) and fuses it against an authoritative multi-source geospatial knowledge base:
* **35,684** industrial manufacturing and processing facilities (OpenStreetMap National Registry)
* **1,633** power generation stations (Central Electricity Authority — CEA)
* **98,793** mining auction blocks and mineral leases (Indian Bureau of Mines — IBM)
* **11** major National Parks, Tiger Reserves, and Biosphere Reserves (Wildlife Institute of India — WII)
* **15** thematic land use / land cover classifications (ISRO Bhuvan / NRSC)
* **8,221,825+** authoritative historical and operational thermal observations (2022–2026)

Raw detections are clustered using incremental spatiotemporal DBSCAN into coherent thermal events. Events are enriched using a **Point-in-Time Anti-Leakage Feature Engine** ($t_{\text{obs}} < t_{\text{event}}$), classified across six distinct thermal categories via a 26-dimensional **XGBoost Classifier** (`xgb-v3.0-real-candidate`), calibrated using a **Balanced Platt Calibrator**, explained locally via **TreeExplainer SHAP**, and evaluated through a transparent **0–100 Multi-Factor Risk Engine**.

Decision-making is governed by a **Tri-Tier Human-in-the-Loop (HITL)** architecture achieving **97.18% selective accuracy** on high-confidence Tier 1 candidates, while routing ambiguous cases to a National Command Center featuring an **8-Layer PostGIS Vector Map**, live KPI telemetry, and a **7-Layer Spatial Investigation Dossier**.

---

## 2. Master System Status Snapshot

| Component / Subsystem | Operational Status | Technical Implementation / Verified Evidence |
|:---|:---:|:---|
| **Satellite Telemetry Ingestion** | **`HEALTHY`** | NASA FIRMS VIIRS & MODIS incremental polling, deduplication, bounding box validation |
| **Historical Thermal Archive** | **`100% SEALED`** | 6,448,666 historical records (2022–2025) immutable (0 diff against baseline) |
| **Operational Stream (2026)** | **`ACTIVE`** | 1,773,159+ live detections streaming into daily operational partitions |
| **PostgreSQL / PostGIS Engine** | **`OPERATIONAL`** | PostgreSQL 16 + PostGIS 3.4 on EPSG:4326 with GIST spatial indexing |
| **Geospatial Knowledge Base** | **`FUSED`** | 35,684 factories, 1,633 CEA plants, 98,793 IBM mines, WII PAs, Bhuvan LULC |
| **Thermal Event Clustering** | **`OPERATIONAL`** | Incremental DBSCAN ($\epsilon=0.015^\circ$, $\text{min\_samples}=3$) generating 215 active events |
| **Feature Engineering Pipeline** | **`REMEDIATED`** | 26 features with Point-in-Time anti-leakage ($t_{\text{obs}} < t$) & lookback normalization |
| **Machine-Learning Classifier** | **`GOVERNED`** | `xgb-v3.0-real-candidate` (5-Fold Spatial CV Macro F1: 93.18%, Mean Acc: 94.32%) |
| **Probability Calibration** | **`CALIBRATED`** | Balanced Platt Calibrator (ECE: 0.1294, Log-Loss: 0.7124, 55.7% reduction vs raw) |
| **Explainable AI Engine** | **`ACTIVE`** | TreeExplainer SHAP generating top-3 attribution waterfalls per event |
| **Multi-Factor Risk Engine** | **`OPERATIONAL`** | 0–100 score (Intensity 40% + Asset Proximity 35% + Ecological Context 25%) |
| **Tri-Tier HITL Decisioning** | **`OPERATIONAL`** | Tier 1 Selective Accuracy: **97.18%**; Tier 2/3 diverted to Analyst Review Queue |
| **Alert & Investigation Desk** | **`OPERATIONAL`** | Tri-Tier routing, 86 queued alerts, full lifecycle state machine & audit logs |
| **National Command Center (GIS)** | **`OPERATIONAL`** | Next.js 15 + MapLibre GL 4.7 with 8 vector layers & dynamic viewport bounding box querying |
| **7-Layer Investigation Dossier** | **`OPERATIONAL`** | Real-time multi-source spatial cascade with live geodesic proximity measurements |
| **Security & Safety Gate** | **`SECURED`** | `ENABLE_OPERATIONAL_DISPATCH_GATE = False`; 0 live dispatches emitted |
| **Disaster Recovery & Backup** | **`TESTED`** | Automated pg_dump backup verified with 100% isolated test database restore |
| **Integration Test Suite** | **`100% PASS`** | `pytest` integration test suite (12/12 passed); Next.js production build (28/28 routes) |

---

## 3. Key Research & Engineering Contributions

1. **Integrated Geospatial Intelligence vs. Pure Detection**: Moving beyond isolated coordinate detection to full multi-source situational awareness (ownership, capacity, mineral type, environmental clearance, and ecological vulnerability).
2. **Point-in-Time Feature Provenance**: Rigorous enforcement of temporal causality ($t_{\text{obs}} < t_{\text{event}}$) eliminating data leakage across multi-year training archives.
3. **Empirical Shadow Drift Discovery & Remediation**: Uncovering that apparent feature drift in `persistence_score` and `recurrence_rate` was an artifact of expanding database lookback windows and 2022 archive boundary truncation, resolved via lookback-normalized sliding windows.
4. **Probability Calibration for Operational Trust**: Reducing model expected calibration error (ECE) by 54.3% and log-loss by 55.7% using Balanced Platt Scaling.
5. **High-Precision Human-in-the-Loop Architecture**: Tri-Tier routing delivering **97.18% selective accuracy** on autonomous Tier 1 alerts while shielding operators from alert fatigue.
6. **Scalable Viewport Bounding-Box GIS Delivery**: Sub-100ms PostGIS vector streaming that handles 35,000+ facilities without browser memory exhaustion.

---

## 4. Operational Governance & Activation Policy

* **Controlled Activation**: The system is fully operational locally on `http://localhost:3000/dashboard` and `http://localhost:8000/api/v1/*`.
* **Autonomous Dispatch Isolation**: Direct dispatch to emergency services remains strictly **disabled** (`ENABLE_OPERATIONAL_DISPATCH_GATE = False`). All alerts are safely routed to the Human-in-the-Loop Analyst Review Queue for operator confirmation.
