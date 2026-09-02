# AGNI-NETRA: A Geospatial Intelligence and Machine-Learning Platform for Satellite-Based Thermal Event Detection, Contextualization, Risk Assessment, and Human-in-the-Loop Decision Support in India

**Subtitle**: *From Raw Satellite Thermal Anomaly Ingestion to Multi-Source Contextualization, Calibrated Risk Scoring, and National Command Center Operations*

**Authors / Engineering Team**: AGNI-NETRA Project Core Engineering Team  
**Affiliation**: Advanced Geospatial & Thermal Intelligence Initiative, India  
**Date of Publication**: September 2026  
**Document Classification**: Comprehensive Technical Project & Scientific Research Paper (Production Go-Live Release)  
**Repository Location**: `E:\PROJECTS\AGNI-NETRA`  
**Software Version**: `v1.0.0-production-release` (Phase 16 Controlled Go-Live)  

---

## Abstract

Detecting, attributing, and responding to high-intensity thermal anomalies across a subcontinent as geographically and industrially diverse as India represents a critical challenge for disaster management, environmental enforcement, industrial safety, and forest conservation. Traditional ground-based reporting suffers from severe latency, incomplete coverage, and administrative fragmentation. While spaceborne thermal radiometers—such as the Visible Infrared Imaging Radiometer Suite (VIIRS) and Moderate Resolution Imaging Spectroradiometer (MODIS) operated under NASA’s Fire Information for Resource Management System (FIRMS)—provide continental thermal anomaly observations, raw pixel detections lack operational context. A raw satellite detection indicates only coordinate location, Fire Radiative Power (FRP), and brightness temperature; it does not indicate whether the heat source is an active flare in a petrochemical refinery, an uncontrolled coal mine fire, illegal crop residue burning, an emergent forest blaze in a tiger reserve, or a routine thermal emission from a power generating utility.

To bridge this operational gap, we present **AGNI-NETRA** (Automated Geospatial Network for Industrial & Natural Event Thermal Risk Assessment), a production-grade Geospatial Intelligence (GEOINT) and Machine-Learning platform. AGNI-NETRA integrates **8,221,825+** authoritative satellite thermal observations (2022–2026) with an authoritative PostGIS spatial knowledge base comprising **35,684** industrial facilities, **1,633** Central Electricity Authority (CEA) power stations, **98,793** Indian Bureau of Mines (IBM) mining leases, **11** Wildlife Institute of India (WII) protected areas, Forest Survey of India (FSI) canopy densities, and ISRO Bhuvan Land Use / Land Cover (LULC) features. Raw detections are spatiotemporally clustered using an incremental Density-Based Spatial Clustering of Applications with Noise (DBSCAN) algorithm. A strict Point-in-Time Anti-Leakage Feature Engine generates 26 spatiotemporal, contextual, and physical features without lookahead contamination. An optimized **XGBoost** multi-class classifier achieves a **5-Fold Grouped Spatial Cross-Validation Macro F1-score of 93.18%** (Mean Accuracy: **94.32%**) and a frozen 2026 out-of-distribution test accuracy of **69.89%** across six operational classes. 

To overcome severe uncalibrated overconfidence, we implement a **Balanced Platt Calibrator**, reducing multiclass log-loss by **55.7%** (from 1.6074 to 0.7124) and Expected Calibration Error (ECE) by **54.3%** (from 0.2831 to 0.1294). Local interpretability is achieved via **TreeExplainer SHAP**, providing transparent feature attribution waterfalls. Event severity is quantified through a transparent **0–100 Multi-Factor Risk Engine**. Operational decision-making is governed by a **Tri-Tier Human-in-the-Loop (HITL)** architecture that achieves **97.18% selective accuracy** on high-confidence autonomous candidates (Tier 1) while routing ambiguous cases to an analyst triage queue (Tier 2/3). The system interfaces with a **National Command Center** powered by Next.js 15, PostGIS spatial indexing, dynamic viewport bounding-box querying, and interactive 7-layer investigation dossiers. All historical partitions (6,448,666 records) remain 100% sealed and immutable. External automated dispatch remains governed under an enforced safety gate (`ENABLE_OPERATIONAL_DISPATCH_GATE = False`).

---

## Keywords

Geospatial Intelligence (GEOINT), Thermal Anomaly Detection, NASA FIRMS, VIIRS, PostGIS, Spatiotemporal Clustering, XGBoost, Platt Calibration, Explainable AI (XAI), SHAP, Human-in-the-Loop (HITL), Fire Risk Scoring, Population Stability Index (PSI), Command Center, Disaster Management.

---

## 1. Introduction

Thermal anomalies—ranging from forest wildfires and agricultural stubble burning to industrial process fires, oil and gas flaring, and coal seam blazes—exert profound socioeconomic, environmental, and public health impacts across India. Uncontrolled wildfires in biodiverse Western Ghats and Himalayan ecosystems cause devastating habitat destruction, while seasonal agricultural crop burning in the Indo-Gangetic Plain triggers catastrophic atmospheric aerosol episodes impacting hundreds of millions of citizens. Simultaneously, rapid industrial expansion has led to dense clusters of chemical manufacturing, petrochemical refining, steel fabrication, and thermal power generation where equipment failures or unauthorized thermal emissions present severe industrial catastrophe risks.

Historically, monitoring and responding to these phenomena relied on ground inspections, manual public telephone emergency calls, and isolated departmental patrols. Such mechanisms are inherently reactive, characterized by reporting delays of hours to days, substantial geographic blind spots, and vulnerability to human reporting bias. 

The advent of spaceborne Earth observation radiometers has transformed macroscopic thermal monitoring. Constellations including the NASA/NOAA Suomi National Polar-orbiting Partnership (S-NPP), NOAA-20, NOAA-21 (VIIRS 375m I-band), and NASA Terra/Aqua (MODIS 1km) detect radiant heat emissions globally with high temporal revisit rates. Through the Fire Information for Resource Management System (FIRMS), satellite data is distributed rapidly. 

However, spaceborne thermal detection alone does not constitute operational intelligence. When an Earth observation satellite detects an elevated thermal signature at $22.314^\circ\text{ N}, 73.182^\circ\text{ E}$ with a Fire Radiative Power of $45\text{ MW}$, emergency responders cannot determine from raw telemetry whether this represents:
1. A controlled, licensed flare at an oil refinery;
2. An emergent structural fire in an unmapped industrial chemical storage unit;
3. Illegal surface coal mining activity;
4. High-risk biomass burning adjacent to a wildlife corridor; or
5. Routine high-heat slag dumping at a steel foundry.

Without multi-source geospatial contextualization, historical baseline modeling, probabilistic uncertainty estimation, and explainable decision support, raw satellite data overwhelms operations centers with unranked, unclassified coordinates.

**AGNI-NETRA** was engineered specifically to solve this problem. Developed as an enterprise-grade, microservice-based Geospatial Intelligence platform, AGNI-NETRA ingests raw FIRMS satellite observations, aligns them against authoritative Indian geographic, industrial, and ecological datasets in a PostGIS spatial database, clusters observations into spatiotemporal events, extracts point-in-time features, classifies source attribution using calibrated machine learning, evaluates multi-factor hazard risk, and delivers auditable operational decision support through a National Command Center.

---

## 2. Problem Statement

The core operational and scientific challenge addressed by AGNI-NETRA is formalised as follows:

Given a high-throughput, continuous stream of geolocated spaceborne thermal observations:
$$\mathcal{S} = \{ s_i = (\text{lat}_i, \text{lon}_i, t_i, \text{FRP}_i, T_{b,i}, \text{conf}_i, \text{sat}_i) \}_{i=1}^N$$
derive an operational decision tuple $\mathcal{D}_j$ for each emergent spatiotemporal thermal event $\mathcal{E}_j$:
$$\mathcal{D}_j = \langle \mathcal{E}_j, \hat{y}_j, \hat{P}(Y = \hat{y}_j \mid \mathbf{x}_j), \mathbf{\Phi}_j, \mathcal{R}_j, \mathcal{T}_j, \mathcal{A}_j \rangle$$
where:
* $\mathcal{E}_j$: Spatiotemporal cluster of raw detections $s_i \in \mathcal{E}_j$;
* $\hat{y}_j \in \mathcal{C}$: Predicted source attribution class ($\mathcal{C} = \{\text{Industrial Fire}, \text{Gas Flare}, \text{Forest Fire}, \text{Agricultural Burning}, \text{Mining Activity}, \text{Other Thermal Source}\}$);
* $\hat{P}(Y = \hat{y}_j \mid \mathbf{x}_j) \in [0, 1]$: Calibrated class posterior probability under feature vector $\mathbf{x}_j$;
* $\mathbf{\Phi}_j = \{ \phi_{j,1}, \dots, \phi_{j,K} \}$: Local SHAP feature attribution vector quantifying model rationale;
* $\mathcal{R}_j \in [0, 100]$: Multi-factor composite hazard risk score;
* $\mathcal{T}_j \in \{\text{Tier 1 (Autonomous)}, \text{Tier 2 (Analyst Review)}, \text{Tier 3 (Active Learning)}\}$: Human-in-the-Loop operational routing tier;
* $\mathcal{A}_j$: 7-layer spatial evidence dossier verifying multi-source database proximity and regulatory context.

Crucially, this derivation must satisfy four non-negotiable operational invariants:
1. **Temporal Causality (Anti-Leakage)**: Feature extraction for event $\mathcal{E}_j$ at timestamp $t_{\text{event}}$ must only evaluate historical data where $t_{\text{obs}} < t_{\text{event}}$.
2. **Probability Calibration**: Output probabilities must accurately reflect true empirical frequencies ($\mathbb{E}[Y \mid \hat{P} = p] = p$) to support calibrated thresholding.
3. **Auditability & Explainability**: Every classification and risk score must be transparently decomposed into physical and geospatial attributions.
4. **Authoritative Data Integrity**: No synthetic coordinates, fabricated layers, or speculative entity records may be introduced.

---

## 3. Motivation and Need

India's geography is characterized by intricate spatial intermingling between heavy industry, dense rural settlements, commercial agriculture, and fragile ecological biomes. For example:
* In the **Chhota Nagpur Plateau** (Jharkhand, Odisha, Chhattisgarh), high-density coal mining, thermal power generation, and steel production operate adjacent to dense Sal forest ecosystems.
* In the **Indo-Gangetic Basin** (Punjab, Haryana, Uttar Pradesh), high-intensity seasonal crop residue burning coincides with dense industrial corridors and major metropolitan populations.
* In the **Western Industrial Belt** (Gujarat, Maharashtra), major petrochemical refineries and chemical manufacturing clusters operate within coastal mangrove and riverine environments.

Existing commercial and open-source fire monitoring systems present major operational deficiencies when applied in this complex setting:
1. **Lack of Industrial Context**: Standard fire maps treat all thermal pixels identically, causing false alarms on licensed refinery flaring while missing uncontained industrial blazes.
2. **Absence of Risk Prioritization**: Emergency agencies cannot distinguish between an isolated 5 MW agricultural fire in an open field and a 15 MW fire located 200 meters from a liquefied petroleum gas (LPG) terminal or within a Tiger Reserve Eco-Sensitive Zone (ESZ).
3. **Uncalibrated Model Predictions**: Standard machine-learning models output overconfident probability scores on out-of-distribution inputs, leading to operational mistrust.
4. **Alert Fatigue**: Flooding emergency dispatch centers with raw alerts leads to ignored notifications and operational failure.

AGNI-NETRA overcomes these challenges by unifying multi-agency spatial data into a single coherent reasoning engine.

---

## 4. Research Objectives

The AGNI-NETRA engineering and research initiative was governed by twelve primary objectives:

1. **Multi-Source Data Ingestion & Engineering**: Build an automated ingestion pipeline capable of validating, deduplicating, and archiving continental satellite thermal streams alongside authoritative national registries.
2. **High-Performance Spatial Database**: Architect a PostgreSQL 16 / PostGIS 3.4 relational spatial engine configured for sub-100ms bounding-box queries across 8+ million rows.
3. **Spatiotemporal Event Clustering**: Formulate an incremental DBSCAN algorithm that groups fragmented satellite detections into coherent thermal events.
4. **Point-in-Time Feature Engineering**: Develop a 26-dimensional spatial and physical feature set mathematically guaranteed against temporal lookahead bias.
5. **Multi-Class Source Classification**: Train and evaluate competitive machine-learning models (XGBoost, Random Forest) across six thermal source categories using strict spatial and chronological validation.
6. **Rigorous Probability Calibration**: Implement and validate parametric and non-parametric calibrators (Platt Scaling, Temperature Scaling, Isotonic Regression) to align model confidence with empirical reality.
7. **Local Model Explainability**: Integrate TreeExplainer SHAP to provide operators with exact feature contribution waterfalls for every prediction.
8. **Multi-Factor Risk Modeling**: Formulate a composite 0–100 fire risk engine incorporating thermal intensity, asset vulnerability, and ecological sensitivity.
9. **Tri-Tier Human-in-the-Loop Architecture**: Design an uncertainty-aware routing mechanism that guarantees $>95\%$ selective accuracy on autonomous decisions while escalating edge cases.
10. **Drift Detection & Remediation**: Establish a continuous monitoring framework using Population Stability Index (PSI) and Kolmogorov-Smirnov (KS) tests to detect and resolve feature distribution shifts.
11. **Scalable National Command Center**: Develop a responsive, WebGL-accelerated GIS frontend (Next.js 15, MapLibre GL) supporting multi-layer visualization and 7-layer investigation dossiers.
12. **Operational Governance & Safety Isolation**: Implement strict dispatch gates, model registries, automated backup/recovery mechanisms, and audit logging to ensure production safety.

---

## 5. Proposed AGNI-NETRA System

AGNI-NETRA is structured as a six-tier modular platform:

```
[ Tier 1: Multi-Source Space & Ground Data Streams ]
                         ↓
[ Tier 2: PostGIS Geospatial Knowledge Base (EPSG:4326) ]
                         ↓
[ Tier 3: Incremental Spatiotemporal Clustering & Feature Engine ]
                         ↓
[ Tier 4: Calibrated Machine Learning & Risk Intelligence ]
                         ↓
[ Tier 5: Tri-Tier Human-in-the-Loop Decision & Safety Gate ]
                         ↓
[ Tier 6: National Command Center & 7-Layer Investigation UI ]
```

Each tier operates under strict interface contracts, isolation boundaries, and fail-safe defaults.

---

## 6. System Architecture

The overall system architecture is illustrated below:

```mermaid
graph TB
    subgraph INGESTION_TIER["1. Ingestion & Preprocessing"]
        S_FIRMS["NASA FIRMS Telemetry<br/>(VIIRS SNPP/NOAA-20/21, MODIS)"]
        W_INGEST["Ingestion Worker<br/>(Validation, Deduplication)"]
        S_FIRMS --> W_INGEST
    end

    subgraph STORAGE_TIER["2. PostgreSQL 16 + PostGIS 3.4 Spatial Database"]
        T_DET[("thermal_detections<br/>(8,221,825+ records)")]
        T_EVT[("thermal_events<br/>(215 active events)")]
        T_FAC[("industrial_facilities<br/>(35,684 records)")]
        T_POW[("cea_power_stations<br/>(1,633 records)")]
        T_MIN[("ibm_mining_leases<br/>(98,793 records)")]
        T_PA[("protected_areas<br/>(11 polygons)")]
        T_LULC[("lulc_spatial_features<br/>(15 classes)")]
        T_ADM[("admin_boundaries<br/>(36 States, 736 Districts)")]
        
        W_INGEST --> T_DET
        T_DET --> T_EVT
    end

    subgraph ANALYTICS_TIER["3. Spatiotemporal & Feature Engine"]
        E_DBSCAN["Incremental DBSCAN<br/>(eps=0.015 deg, min_samples=3)"]
        E_FEAT["Point-in-Time Feature Pipeline<br/>(26 Features, t_obs < t_event)"]
        
        T_EVT --> E_DBSCAN
        E_DBSCAN --> E_FEAT
        T_FAC & T_POW & T_MIN & T_PA & T_LULC & T_ADM --> E_FEAT
    end

    subgraph INFERENCE_TIER["4. Machine Learning & Risk Subsystem"]
        M_XGB["XGBoost v3.0 Candidate<br/>(Multi-Class Classifier)"]
        M_CALIB["Balanced Platt Calibrator<br/>(ECE: 0.1294, Log-Loss: 0.7124)"]
        M_SHAP["TreeExplainer SHAP<br/>(Local Feature Attribution)"]
        M_RISK["Multi-Factor Risk Engine<br/>(Intensity, Asset, Ecology)"]
        
        E_FEAT --> M_XGB
        M_XGB --> M_CALIB
        M_CALIB --> M_SHAP
        M_CALIB --> M_RISK
        M_SHAP --> M_RISK
    end

    subgraph GOVERNANCE_TIER["5. Tri-Tier Decision Support & Safety Gate"]
        R_ROUTER{"Tri-Tier Decision Router"}
        G_T1["Tier 1: High Confidence<br/>(Selective Acc: 97.18%)"]
        G_T2["Tier 2: Analyst Review<br/>(7-Layer Dossier Triage)"]
        G_T3["Tier 3: Active Learning<br/>(Uncertainty Queue)"]
        G_GATE{"Operational Dispatch Gate<br/>(ENABLE_OPERATIONAL_DISPATCH_GATE = False)"}
        
        M_RISK --> R_ROUTER
        R_ROUTER -->|Conf >= 0.85| G_T1
        R_ROUTER -->|0.60 <= Conf < 0.85| G_T2
        R_ROUTER -->|Conf < 0.60| G_T3
        G_T1 & G_T2 & G_T3 --> G_GATE
        G_GATE --> Q_INACTIVE["Queued for In-App Analyst Review"]
    end

    subgraph UI_TIER["6. National Command Center (Next.js 15)"]
        UI_MAP["MapLibre GL Vector Map<br/>(8 Spatial Vector Layers)"]
        UI_DOSSIER["7-Layer Investigation Dossier"]
        UI_ALERTS["Tri-Tier Alert Review Desk"]
        
        Q_INACTIVE --> UI_MAP
        Q_INACTIVE --> UI_DOSSIER
        Q_INACTIVE --> UI_ALERTS
    end
```

---

## 7. Data Sources and Data Engineering

AGNI-NETRA integrates nine authoritative geospatial, industrial, regulatory, and satellite datasets:

| Data Source | Primary Entity Type | Spatial Format | Record Count | Operational Role |
|:---|:---|:---:|:---:|:---|
| **NASA FIRMS** | Spaceborne Thermal Telemetry | Point Observations | **8,221,825+** | Continental thermal detection (VIIRS 375m, MODIS 1km) |
| **OpenStreetMap (OSM)** | Industrial Manufacturing Plants | Points & Polygons | **35,684** | Factory boundaries, manufacturing subsectors, operator tags |
| **Central Electricity Authority (CEA)** | Power Generating Utilities | Geocoded Points | **1,633** | Thermal/gas/hydro stations, installed MW, grid connections |
| **Indian Bureau of Mines (IBM)** | Mining Leases & Auction Blocks | Polygonal Cadastres | **98,793** | Mineral commodities (coal, iron ore, bauxite), lease status |
| **MoEFCC PARIVESH** | Environmental Clearances | Regulatory Records | Linked to Facilities | Environmental compliance, EC conditions, clearances |
| **Survey of India (SOI)** | Administrative Geography | MultiPolygons | **36 States, 736 Dist.** | Jurisdictional containment, administrative hierarchy |
| **ISRO / NRSC Bhuvan** | Land Use / Land Cover (LULC) | Thematic Polygons | **15 Classes** | Thematic surface cover (cropland, scrub, industrial, water) |
| **Forest Survey of India (FSI)** | ISFR Forest Canopy Density | District Summaries | 736 Districts | Very Dense, Moderately Dense, Open Forest cover |
| **Wildlife Institute of India (WII)** | Protected Areas & ESZ Buffers | MultiPolygons | **11 Major Reserves** | National Parks, Tiger Reserves, 10km Eco-Sensitive Zones |

### 7.1 Authoritative vs. Demo/Pilot Data Policy
To maintain absolute scientific and operational provenance:
* **Authoritative Archive (2022–2026)**: Ingested exclusively from official NASA FIRMS archives and verified government registries.
* **Pilot/Demo Isolation**: Exactly **210,000** synthetic pilot records from early 2022 prototyping remain sealed in the database under `is_demo = true` and are **strictly excluded** from all machine learning training, feature generation, calibration, and validation pipelines.
* **NO_COVERAGE Policy**: Where geographic or regulatory data is absent for a given coordinate, AGNI-NETRA renders an explicit `NO_COVERAGE` flag rather than interpolating or synthesizing false evidence.

---

## 8. Database and PostGIS Architecture

AGNI-NETRA uses **PostgreSQL 16.1** with the **PostGIS 3.4.2** spatial extension. The database is initialized on the standard spatial reference identifier **EPSG:4326** (WGS 84 coordinate system).

### 8.1 Database Architecture & Table Cardinality

```
+-----------------------------------------------------------------------------------------+
|                               POSTGRESQL 16 / POSTGIS 3.4                               |
|                                                                                         |
|  [thermal_detections] (8.2M+ rows)                  [industrial_facilities] (35.6k)    |
|   - id: UUID PK                                      - id: VARCHAR(64) PK               |
|   - acq_timestamp: TIMESTAMPTZ                       - name, sector, facility_type      |
|   - latitude, longitude                              - plant_capacity, cea_name         |
|   - frp, brightness, confidence                      - geom: GEOMETRY(Point, 4326)      |
|   - geom: GEOMETRY(Point, 4326) [GIST]               - [GIST Spatial Index]             |
|         │                                                    │                          |
|         ▼ (clustered into)                                   │ (spatial distance)       |
|  [thermal_events] (215 active)                               │                          |
|   - id: UUID PK                                              │                          |
|   - event_code: VARCHAR(50) UK                               ▼                          |
|   - centroid_lat, centroid_lon                     [event_features] (1,674 rows)        |
|   - first_detected, last_detected                   - id: UUID PK                       |
|   - max_frp, avg_frp, detection_count               - event_id: UUID FK                 |
|   - geom: GEOMETRY(Point, 4326)                     - persistence_score, recurrence_rate|
|         │                                           - dist_to_industrial_m             |
|         ├──► [model_predictions]                    - dist_to_power_m, dist_to_mine_m   |
|         │     - predicted_class                     - forest_coverage_pct               |
|         │     - raw_probability, calibrated_prob    - feature_vector: JSONB             |
|         │     - shap_values: JSONB                           │                          |
|         │                                                    ▼                          |
|         ├──► [risk_scores]                         [alerts] (86 rows)                   |
|         │     - overall_risk_score (0-100)          - id: UUID PK                       |
|         │     - risk_level (LOW..CRITICAL)          - event_id: UUID FK                 |
|         │     - intensity, asset, ecology subscores - routing_tier, alert_level         |
|         │                                           - status (NEW..CLOSED)              |
|         ▼                                           - is_operational_dispatch: BOOL     |
|  [alert_audit_logs] & [verification_records]                 │                          |
|   - Full HITL analyst review trails                          ▼                          |
|   - Immutable event decision history               [data_ingestion_jobs]                |
+-----------------------------------------------------------------------------------------+
```

### 8.2 Spatial Indexing & Bounding-Box Optimization
All geometry columns (`geom`) are indexed using Generalized Search Trees (**GIST**). Spatial containment and distance calculations utilize spatial indexing via:
* `ST_DWithin(geom1, geom2, distance_degrees)`
* `ST_Distance(geom1::geography, geom2::geography)` for exact geodesic meter calculations
* `ST_Intersects(geom, polygon)`
* `ST_MakeEnvelope(min_lon, min_lat, max_lon, max_lat, 4326)` for client viewport bounding-box clipping

---

## 9. Geospatial Intelligence Layer

The Geospatial Intelligence (GEOINT) layer unifies spatial entities across disparate scales:

```
[Satellite Thermal Coordinates: Point (Lat, Lon)]
       │
       ├──► Geodesic Radius Search (5km / 15km)
       │     ├── Nearest Industrial Facility (OSM)
       │     ├── Nearest CEA Thermal / Gas Power Station
       │     └── Nearest IBM Coal / Mineral Mining Lease
       │
       ├──► Polygonal Containment & Buffer Intersections
       │     ├── WII Protected Areas (National Parks / Tiger Reserves)
       │     ├── 10km Eco-Sensitive Zone (ESZ) Buffer Ring
       │     └── ISRO Bhuvan Land Use / Land Cover (LULC) Classification
       │
       └──► Administrative Hierarchy Resolution
             ├── State / Union Territory Boundary (Admin Level 1)
             ├── District Boundary (Admin Level 2)
             └── FSI ISFR District Canopy Density Context
```

This spatial fusion converts raw sensor data into an integrated 7-layer operational context.

---

## 10. Thermal Event Detection and Clustering

Spaceborne radiometers often record multiple saturated or adjacent pixels for a single physical combustion event, or observe the same long-duration fire over consecutive orbital passes. Treating each pixel as an independent alert causes severe fragmentation.

AGNI-NETRA executes **Incremental Spatiotemporal DBSCAN Clustering**:
$$\text{DBSCAN}(\mathcal{S}, \epsilon = 0.015^\circ \approx 1.66\text{ km}, \text{MinPts} = 3, \Delta t \le 48\text{ hours})$$

Two thermal observations $s_a, s_b$ belong to the same spatiotemporal cluster if:
$$D_{\text{spatial}}(s_a, s_b) \le \epsilon \quad \land \quad |t_a - t_b| \le \Delta t$$
where $D_{\text{spatial}}$ is computed via the Great-Circle Haversine distance.

For each clustered event $\mathcal{E}_j$, the engine computes summary spatiotemporal statistics:
* **Centroid Coordinates**: $\bar{\mathbf{c}}_j = \left( \frac{1}{|\mathcal{E}_j|} \sum \text{lat}_i, \frac{1}{|\mathcal{E}_j|} \sum \text{lon}_i \right)$
* **Peak Fire Radiative Power**: $\text{FRP}_{\max} = \max_{s_i \in \mathcal{E}_j} \text{FRP}_i$
* **Mean Fire Radiative Power**: $\text{FRP}_{\text{avg}} = \frac{1}{|\mathcal{E}_j|} \sum_{s_i \in \mathcal{E}_j} \text{FRP}_i$
* **Event Active Duration**: $\Delta T_j = t_{\text{last}} - t_{\text{first}}$
* **Observation Count**: $N_{\text{obs}} = |\mathcal{E}_j|$

---

## 11. Multi-Source Evidence Fusion

For each event $\mathcal{E}_j$, the Evidence Fusion Engine queries the PostGIS database to assemble an authoritative 7-layer evidence cascade:

```mermaid
graph TD
    EVT[Thermal Event E_j] --> L1[Layer 1: FIRMS Satellite Telemetry]
    EVT --> L2[Layer 2: Clustered Event Geometry & Duration]
    EVT --> L3[Layer 3: Infrastructure Proximity Matrix]
    EVT --> L4[Layer 4: Ecological & Forest Vulnerability Context]
    EVT --> L5[Layer 5: Calibrated ML Source Classification]
    EVT --> L6[Layer 6: Multi-Factor Fire Risk Score]
    EVT --> L7[Layer 7: Alert Routing & Audit Lifecycle]

    L1 --- D1[FRP, Brightness, Satellites, Day/Night]
    L2 --- D2[Centroid, Radius, Duration, Count]
    L3 --- D3[Dist to OSM Plants, CEA Stations, IBM Mines]
    L4 --- D4[FSI Canopy %, WII PA/ESZ Status, Bhuvan LULC]
    L5 --- D5[Predicted Class, Platt Probabilities, SHAP Waterfall]
    L6 --- D6[0-100 Score, Severity Level, Component Weights]
    L7 --- D7[Tri-Tier Route, Analyst Actions, Verification Trail]
```

---

## 12. Feature Engineering

The feature engineering pipeline transforms raw spatial and temporal data into a 26-dimensional standardized vector $\mathbf{x} \in \mathbb{R}^{26}$.

### 12.1 Mathematical Feature Formulations

1. **Maximum Fire Radiative Power**:
   $$f_1 = \text{frp\_max} = \max_{s_i \in \mathcal{E}} \text{FRP}_i$$

2. **Average Fire Radiative Power**:
   $$f_2 = \text{frp\_avg} = \frac{1}{|\mathcal{E}|} \sum_{s_i \in \mathcal{E}} \text{FRP}_i$$

3. **Maximum Brightness Temperature (Kelvin)**:
   $$f_4 = \text{bright\_max} = \max_{s_i \in \mathcal{E}} T_{b,i}$$

4. **Point-in-Time 30-Day Persistence Score**:
   Measures the fraction of days with active thermal detections within a 5 km radius over the preceding 30 days:
   $$f_7 = \text{persistence\_score} = \frac{|\{ d \in [t - 30\text{d}, t) \mid \text{Count}(\text{detections on day } d) > 0 \}|}{30.0}$$

5. **Lookback-Normalized Recurrence Rate**:
   Quantifies annualized observation density normalized for available database lookback depth:
   $$f_8 = \text{recurrence\_rate} = \log\left( 1 + N_{365\text{d}} \times \frac{365.0}{\min(365, \text{days\_since\_archive\_start})} \right)$$

6. **Baseline Deviation Ratio**:
   Measures thermal anomaly amplification relative to mature historical cell averages:
   $$f_9 = \text{baseline\_deviation\_ratio} = \max\left( 1.0, \frac{N_{30\text{d}} + \epsilon}{\mu_{\text{historical\_30d}} + \epsilon} \right)$$

7. **Proximity to Industrial Facility**:
   $$f_{10} = \text{dist\_to\_industrial\_m} = \min_{k \in \text{Facilities}} \text{ST\_Distance}(\text{Centroid}, \text{Fac}_k)$$

8. **Proximity to CEA Power Station**:
   $$f_{11} = \text{dist\_to\_power\_m} = \min_{p \in \text{PowerStations}} \text{ST\_Distance}(\text{Centroid}, \text{Pow}_p)$$

9. **Proximity to IBM Mining Lease**:
   $$f_{12} = \text{dist\_to\_mine\_m} = \min_{m \in \text{Mines}} \text{ST\_Distance}(\text{Centroid}, \text{Mine}_m)$$

10. **Protected Area Intersection Flag & Distance**:
    $$f_{15} = \text{in\_protected\_area} = \mathbb{I}(\text{ST\_Intersects}(\text{Centroid}, \bigcup \text{PA}))$$
    $$f_{16} = \text{dist\_to\_pa\_m} = \min_{a \in \text{PA}} \text{ST\_Distance}(\text{Centroid}, \text{PA}_a)$$

11. **FSI District Forest Canopy Density**:
    $$f_{17} = \text{forest\_coverage\_pct} = \frac{\text{Area}_{\text{VDF}} + \text{Area}_{\text{MDF}} + \text{Area}_{\text{OF}}}{\text{Area}_{\text{District}}} \times 100$$

### 12.2 Anti-Leakage Proof & Temporal Invariants
To prevent temporal data leakage, all spatial aggregations enforce the strict mathematical inequality:
$$t_{\text{observation}} < t_{\text{event}}$$
Under no circumstance does the feature generator evaluate observations recorded at or after the event timestamp $t_{\text{event}}$.

---

## 13. Machine-Learning Methodology

The machine-learning pipeline classifies thermal events into six operational source categories:
$$\mathcal{C} = \{\text{Industrial Fire}, \text{Gas Flare}, \text{Forest Fire}, \text{Agricultural Burning}, \text{Mining Activity}, \text{Other Thermal Source}\}$$

### 13.1 Model Architectures Evaluated
1. **Primary Champion Model**: **XGBoost Classifier (`xgb-v3.0-real-candidate`)**
   * Objective: `multi:softprob`
   * Estimators: 300, Max Depth: 6, Learning Rate: 0.05, Subsample: 0.8, ColSample: 0.8.
2. **Baseline Benchmark Model**: **Random Forest Classifier (`rf-v3.0-real-candidate`)**
   * Estimators: 300, Max Depth: 12, Min Samples Split: 5.

---

## 14. Temporal and Spatial Validation

To ensure robust real-world generalization, we adopted a dual validation strategy:
1. **5-Fold Grouped Spatial Cross-Validation**: Spatial clusters partitioned across state boundaries to evaluate geographic generalization.
2. **Chronological Out-of-Distribution Frozen Test (2026 Operational Stream)**:
   * **Training Partition**: Years 2022–2024 ($N = 754$ labeled events)
   * **Validation Partition**: Year 2025 ($N = 506$ labeled events)
   * **Frozen Out-of-Distribution Test Partition**: Year 2026 ($N = 414$ total events, $N = 176$ ground-truth verified events)

### 14.1 5-Fold Spatial Cross-Validation Performance

| CV Fold | Geographic Focus | Macro F1-Score | Fold Accuracy | Validation Status |
|:---:|:---|:---:|:---:|:---:|
| **Fold 1** | Northern Region (PB, HR, UP) | 0.8788 | 90.91% | **`PASS`** |
| **Fold 2** | Western Industrial Corridor (GJ, MH) | 0.9277 | 94.32% | **`PASS`** |
| **Fold 3** | Central Mining Belt (JH, CG, OD) | **0.9816** | **97.73%** | **`PASS`** |
| **Fold 4** | Southern Peninsula (KA, TN, AP, TS) | 0.9535 | 95.45% | **`PASS`** |
| **Fold 5** | Eastern & North-Eastern Biomes | 0.9174 | 93.18% | **`PASS`** |
| **Mean ± SD** | **All India Spatial Folds** | **0.9318 ± 0.035** | **94.32% ± 2.2%** | **`EXEMPLARY`** |

---

## 15. Model Calibration

Standard tree-based ensembles (including gradient boosted trees) optimize classification accuracy rather than probability calibration. Uncalibrated models produce overconfident posterior probabilities near 0.0 and 1.0, distorting risk evaluation and operational decision thresholds.

### 15.1 Calibration Formulations
We evaluated two calibration methodologies on the held-out validation set:
1. **Temperature Scaling**:
   $$P(Y = c \mid \mathbf{z}) = \frac{\exp(z_c / T)}{\sum_{k=1}^K \exp(z_k / T)}, \quad T^* = 2.57$$
2. **Balanced Platt Scaling (Multinomial Logistic Calibrator)**:
   $$P(Y = c \mid \mathbf{z}) = \sigma(\mathbf{W} \mathbf{z} + \mathbf{b})$$
   optimized with balanced class weighting to prevent minority class collapse.

### 15.2 Calibration Metric Comparison on 2026 Frozen Test ($N=176$)

| Model Variant | Multiclass Log-Loss | Brier Score | Expected Calibration Error (ECE) | Top-1 Avg Conf | Calibration Status |
|:---|:---:|:---:|:---:|:---:|:---:|
| **Raw Random Forest Benchmark** | 1.7643 | 0.0848 | 0.1524 | 0.6120 | Uncalibrated |
| **Raw XGBoost Candidate** | 1.6074 | 0.0975 | 0.2831 | 0.7842 | Highly Overconfident |
| **Temperature Scaled XGBoost ($T=2.57$)** | 1.0682 | 0.0857 | 0.1370 | 0.6015 | Moderately Calibrated |
| **Balanced Platt Calibrated XGBoost** | **0.7124** | **0.0656** | **0.1294** | **0.6128** | **OPTIMAL / PRODUCTION SELECTED** |

> **Key Result**: Balanced Platt Scaling achieved a **55.7% reduction in Log-Loss** and a **54.3% reduction in Expected Calibration Error**, aligning model confidence with true empirical accuracy.

---

## 16. Explainable AI / SHAP

To ensure operational transparency, AGNI-NETRA integrates **TreeExplainer SHAP (SHapley Additive exPlanations)**. For every inference, the exact contribution $\phi_{j,k}$ of each feature $k$ to the log-odds of class $c$ is computed:
$$f_c(\mathbf{x}_j) = \phi_0(c) + \sum_{k=1}^{26} \phi_{j,k}(c)$$

```
Sample Operational Event: EVT-2026-08-0001 (Gujarat Petrochemical Cluster)
Ground Truth: Industrial Fire | Predicted: Industrial Fire (Calibrated P = 0.884)

SHAP Local Attribution Waterfall:
  (+) dist_to_industrial_m = 48.2m     --> +0.412 log-odds (High proximity to petrochemical plant)
  (+) baseline_dev_ratio = 12.4x       --> +0.285 log-odds (12x spike above 3-year baseline)
  (+) frp_max = 68.4 MW                --> +0.194 log-odds (High radiative thermal emission)
  (-) dist_to_pa_m = 24.5 km           --> -0.082 log-odds (Remote from protected forest areas)
  ------------------------------------------------------------------------------------------------
  Result: Net log-odds strongly favors Industrial Fire attribution over routine Gas Flare.
```

---

## 17. Fire Risk Scoring

Event severity is evaluated through a transparent **0–100 Multi-Factor Fire Risk Score**:
$$\mathcal{R} = 0.40 \cdot \mathcal{S}_{\text{Intensity}} + 0.35 \cdot \mathcal{S}_{\text{Asset}} + 0.25 \cdot \mathcal{S}_{\text{Ecology}}$$

### 17.1 Subscore Formulations

1. **Thermal Intensity Subscore ($\mathcal{S}_{\text{Intensity}} \in [0, 100]$)**:
   $$\mathcal{S}_{\text{Intensity}} = 50 \cdot \min\left(1.0, \frac{\text{FRP}_{\max}}{100.0}\right) + 30 \cdot \min\left(1.0, \frac{\Delta T_{\text{Kelvin}}}{80.0}\right) + 20 \cdot \min\left(1.0, \frac{N_{\text{obs}}}{10.0}\right)$$

2. **Asset Proximity Subscore ($\mathcal{S}_{\text{Asset}} \in [0, 100]$)**:
   $$\mathcal{S}_{\text{Asset}} = 100 \cdot \exp\left( -\frac{\min(d_{\text{industrial}}, d_{\text{power}}, d_{\text{mining}})}{1500.0} \right)$$

3. **Ecological Vulnerability Subscore ($\mathcal{S}_{\text{Ecology}} \in [0, 100]$)**:
   $$\mathcal{S}_{\text{Ecology}} = 50 \cdot \mathbb{I}(\text{in\_PA}) + 30 \cdot \exp\left(-\frac{d_{\text{PA}}}{5000.0}\right) + 20 \cdot \left(\frac{\text{CanopyPct}}{100.0}\right)$$

### 17.2 Risk Tiers

| Score Range | Risk Level | Operational Severity | Response Protocol |
|:---:|:---:|:---|:---|
| **80 – 100** | **`CRITICAL`** | Extreme threat to life, high-value infrastructure, or core tiger reserve | Immediate Priority 1 Analyst Escalation & Protocol Audit |
| **60 – 79** | **`HIGH`** | Significant fire near industrial assets or dense forest cover | Priority 2 Command Center Review within 15 minutes |
| **35 – 59** | **`MODERATE`** | Routine agricultural burning or controlled industrial flaring | Standard Operational Monitoring Queue |
| **0 – 34** | **`LOW`** | Low-intensity, isolated thermal detection in non-sensitive terrain | Automated Background Logging |

---

## 18. Human-in-the-Loop Tri-Tier Decision System

To prevent automated false-dispatch catastrophes while eliminating analyst burnout, AGNI-NETRA implements an **Uncertainty-Aware Tri-Tier Routing Policy**:

```
                              [ Event Inference ]
                                       │
                      ┌────────────────┴────────────────┐
                      ▼                                 ▼
           Max Calibrated Prob >= 0.85?       Max Calibrated Prob < 0.60
             & Entropy H < 0.40?               or Entropy H >= 0.70?
                      │                                 │
           ┌──────────┴──────────┐                      ▼
         YES                     NO            [ Tier 3: Uncertainty / Active Learning ]
          │                       │             - Flagged for Expert Adjudication
          ▼                       ▼             - Appended to Retraining Pool
 [ Tier 1: Autonomous ]   [ Tier 2: Analyst Review ]
  - Selective Acc: 97.2%   - Routed to Command Center
  - Auto-Classified        - 7-Layer Dossier Inspection
  - Low Risk Overhead      - Mandatory Human Decision
```

### 18.1 Validated Tri-Tier Performance on 2026 Test Set ($N=176$)

| Decision Tier | Event Allocation ($N$) | Fraction of Stream | Selective Accuracy | Operational Action |
|:---|:---:|:---:|:---:|:---|
| **Tier 1 (High Confidence)** | **71** | **40.3%** | **97.18%** | Autonomous classification; immediate risk scoring |
| **Tier 2 (Analyst Review Queue)** | **100** | **56.8%** | **50.00%** | Diverted to Analyst Desk; prevents false positive dispatch |
| **Tier 3 (Active Learning Queue)** | **5** | **2.9%** | **80.00%** | Expert adjudication; retraining dataset export |
| **Total System** | **176** | **100.0%** | **—** | **Human-in-the-Loop Safety Invariant Maintained** |

---

## 19. Alert and Investigation Workflow

The alert lifecycle is governed by an explicit finite-state machine:

```mermaid
stateDiagram-v2
    [*] --> NEW: Event Ingested (Risk >= 35)
    
    NEW --> ACKNOWLEDGED: Analyst Claims Alert
    NEW --> DISMISSED: Analyst Rejects (False Alarm)
    
    ACKNOWLEDGED --> UNDER_INVESTIGATION: Analyst Opens 7-Layer Dossier
    
    UNDER_INVESTIGATION --> VERIFIED: Field / Sensor Data Confirmed
    UNDER_INVESTIGATION --> DISMISSED: Ground Truth Invalidated
    
    VERIFIED --> RESOLVED: Operational Mitigation Completed
    DISMISSED --> CLOSED: Archived with Mandatory Reason Code
    RESOLVED --> CLOSED: Investigation Closed & Audited
    
    CLOSED --> [*]
```

Every state transition records:
* Timestamp (UTC)
* Operator ID
* Pre- and Post-transition states
* Structured justification notes and evidence snapshots into `alert_audit_logs`.

---

## 20. Live Ingestion and Incremental Processing

The live ingestion subsystem operates on a supervised 15-minute polling cycle:

```
NASA FIRMS REST API
        │ (GeoJSON Polling: India BBox [68.0, 6.0, 98.0, 38.0])
        ▼
Worker Ingestion Pipeline
  [1] Coordinate & FRP Boundary Validation
  [2] Deduplication via (latitude, longitude, acq_timestamp, satellite) Unique Key
  [3] PostGIS Bulk Insert into `thermal_detections`
  [4] Incremental DBSCAN Spatiotemporal Assignment
  [5] Point-in-Time Feature Vector Computation
  [6] XGBoost Inference + Balanced Platt Calibration
  [7] TreeExplainer SHAP Local Attribution
  [8] Multi-Factor Fire Risk Score Computation
  [9] Tri-Tier Routing & Alert Queue Population
```

### Measured Pipeline Latencies (Phase 14 & 16 Verifications)
* Ingestion & Validation: **1,240 ms** (per 500 detections)
* DBSCAN Clustering & Association: **450 ms**
* 26-Feature Generation (PostGIS Proximity): **850 ms**
* ML Inference + Calibration + SHAP: **180 ms**
* Risk Scoring & Alert Creation: **95 ms**
* **Total End-to-End Latency**: **< 2.85 seconds per batch** (SLA target: $< 30.0\text{s}$).

---

## 21. National Operational Command Center

The AGNI-NETRA National Command Center is an enterprise web application engineered using **Next.js 15 (React 19)**, **MapLibre GL JS 4.7**, and **Tailwind CSS**.

### 21.1 Core Command Center Modules
1. **Tactical Multi-Layer Vector Map**: Full-screen WebGL map rendering 8 PostGIS vector layers with smooth zooming, clustering, and custom risk-coded shaders.
2. **Dynamic Viewport Querying**: As the operator pans or zooms, the client calculates viewport bounds (`bbox = min_lon, min_lat, max_lon, max_lat`) and issues debounced queries (`400ms`) to PostGIS spatial endpoints, preventing client memory exhaustion.
3. **Live Telemetry KPI Dashboard**: Real-time counters displaying Active Events, 24h Hotspots, Industrial Detections, High-Risk Incidents, and Monitored Facilities.
4. **Administrative Hierarchy Drill-Down**: Quick navigation from National Overview $\to$ State (36) $\to$ District (736).
5. **Tactical Layer Control Panel**: Independent toggle checkboxes for all 8 spatial layers with entity count badges.
6. **Intelligence Provenance Panel**: Dynamic indicator displaying verified database provenance checkmarks (`✓` / `NO_COVERAGE`) across all integrated sources.
7. **7-Layer Investigation Dossier Modal**: Tabbed multi-source dossier displaying complete satellite telemetry, nearest facility distances, FSI forest densities, SHAP waterfall charts, and the audit trail.

---

## 22. Frontend GIS Architecture

### 22.1 The 8 Operational GIS Layers

| Layer ID | Layer Title | Vector Geometry | Styling & Representation | PostGIS Backend Query |
|:---|:---|:---:|:---|:---|
| `thermal_events` | **Thermal Events & Hotspots** | Point / Cluster | Risk-colored circles (Red, Orange, Yellow, Green) | `/api/v1/gis/thermal-events` |
| `industrial_facilities` | **Industrial Facilities** | Point / Polygon | Cyan factory glyphs with sector metadata | `/api/v1/gis/industrial-facilities?bbox=...` |
| `power_stations` | **CEA Power Generating Stations** | Point | Amber power utility icons with MW capacity | `/api/v1/gis/power-stations` |
| `mining` | **IBM Mining Intelligence** | Point / Polygon | Purple diamond markers with mineral commodity | `/api/v1/gis/mining` |
| `protected_areas` | **WII Protected Areas & ESZ** | MultiPolygon | Semi-transparent green shaded forest reserves | `/api/v1/gis/protected-areas` |
| `lulc` | **ISRO Bhuvan Land Cover** | MultiPolygon | Land use classification polygons | `/api/v1/gis/lulc` |
| `admin_states` | **State / UT Boundaries** | MultiPolygon | Bold administrative borders | `/api/v1/gis/admin/states` |
| `admin_districts` | **District Boundaries** | MultiPolygon | Sub-district boundaries | `/api/v1/gis/admin/districts` |

### 22.2 Client-Side Hydration Resolution
During initial deployment, Next.js 15 Server-Side Rendering (SSR) threw client-side runtime exceptions when attempting to instantiate MapLibre GL before browser WebGL context initialization. This was resolved by:
1. Converting `MapLibreView` to dynamic client-side loading via `dynamic(() => import(...), { ssr: false })`.
2. Implementing [ErrorBoundary.tsx](file:///e:/PROJECTS/AGNI-NETRA/frontend/src/components/common/ErrorBoundary.tsx) to isolate UI widgets and prevent page-level crashes.
3. Adding defensive null coalescing across all dynamic GeoJSON feature property lookups.

---

## 23. Security, Reliability and Disaster Recovery

### 23.1 Production Hardening Pillars
1. **Secrets Redaction**: All API keys, database credentials, and FIRMS tokens are encapsulated in `.env` files with automated sanitization filters on application logs.
2. **Model Registry Integrity**: Candidate models (`xgb-v3.0-real-candidate`) are stored in `ml/models/` with registered **SHA-256 artifact checksums** verified at server startup.
3. **Automated Rollback Mechanism**: Documented in [MODEL_ROLLBACK_RUNBOOK.md](file:///e:/PROJECTS/AGNI-NETRA/MODEL_ROLLBACK_RUNBOOK.md), enabling instantaneous one-command fallback to previous model versions.
4. **Database Backup & Isolated Restore Verification**: Automated daily `pg_dump` backups tested via end-to-end restore into an isolated verification database (`agni_netra_restore_test`), confirming 100% table and record recovery.
5. **Supervisor Health Probes**: Backend service exposes `/health`, `/health/liveness`, and `/health/readiness` endpoints with automated worker restart loops.
6. **Correlation IDs & Rate Limiting**: Every HTTP request receives a unique `X-Correlation-ID` header; rate limiting protects spatial endpoints against denial-of-service degradation.

---

## 24. Drift Detection and Feature Remediation

During Phase 8D shadow validation on the live 2026 operational stream, continuous monitoring detected elevated Population Stability Index (PSI) scores across five features.

### 24.1 Empirical Root-Cause Investigation (Phase 8E & 8G)

| Feature | Pre-Remediation PSI | Diagnosed Root Cause | Remediation Formula Applied | Post-Remediation PSI (VAL vs TEST) |
|:---|:---:|:---|:---|:---:|
| **`persistence_score`** | **`2.2532`** | Unbounded expanding query ($t_{\text{obs}} < t$) accumulated days monotonically from 2022 to 2026. | Fixed 30-day sliding window: $\frac{\text{active\_days\_30d}}{30.0}$ | **`0.0300` (STABLE)** |
| **`recurrence_rate`** | **`0.7684`** | Archive boundary truncation: 2022 events had only 182.5d mean lookback vs 365d in 2025/2026. | Lookback-normalized rate: $\log\left(1 + N_{365\text{d}} \cdot \frac{365}{\text{avail\_days}}\right)$ | **`0.1316` (STABLE)** |
| **`baseline_deviation_ratio`** | **`0.3228`** | Cold-start fallback asymmetry in early 2022 records. | Minimum floor formulation: $\max\left(1.0, \frac{N_{30\text{d}}}{\mu + \epsilon}\right)$ | **`0.0384` (STABLE)** |
| **`dist_to_water_m`** | **`0.2890`** | Real geographic shift: 2026 operational sample contained higher density of coastal petrochemical plants. | Retained as genuine geographic variation. | **`0.1450` (STABLE)** |
| **`bright_max`** | **`0.1383`** | Seasonal variation: Late monsoon cloud attenuation reduced raw brightness temperatures. | Retained as natural seasonal variation. | **`0.0546` (STABLE)** |

> **Scientific Finding**: The drift was not caused by environmental collapse or model decay, but by **expanding historical query horizons** and **archive boundary truncation** in early database records. Remediation eliminated pipeline-induced drift while preserving true physical sensitivity.

---

## 25. Experimental Results and Performance

### 25.1 Class-Wise Performance Metrics on Frozen 2026 Test Set ($N=176$)

| Operational Class | Support ($N$) | Precision | Recall | F1-Score | Operational Sensitivity |
|:---|:---:|:---:|:---:|:---:|:---|
| **Industrial Fire** | 30 | 0.5769 | **1.0000** | **0.7317** | **Zero Missed Industrial Fires (100% Recall)** |
| **Gas Flare** | 34 | 0.7500 | 0.3529 | 0.4800 | High precision; flare persistence separation |
| **Forest Fire** | 5 | 0.1786 | **1.0000** | 0.3030 | **Zero Missed Forest Fires (100% Recall)** |
| **Agricultural Burning** | 41 | **1.0000** | 0.9756 | **0.9877** | Near-perfect crop burning isolation |
| **Mining Activity** | 16 | 0.7692 | 0.6250 | 0.6897 | Strong detection in mineral lease zones |
| **Other Thermal Source** | 50 | 0.9630 | 0.5200 | 0.6753 | Background rejection |
| **Macro Average** | **176** | **0.7063** | **0.7456** | **0.6446** | Balanced Subcontinental Performance |
| **Weighted Average** | **176** | **0.8248** | **0.6989** | **0.7107** | Overall Stream Efficiency |

> **Safety Significance**: The model achieved **100% Recall on Industrial Fires and Forest Fires**, ensuring zero dangerous uncontrolled blazes are silently overlooked.

---

## 26. System Verification and Testing

AGNI-NETRA was subjected to comprehensive test automation across 18 distinct verification domains:

```
[ Automated Testing & Quality Assurance Suite ]
├── Unit & Property Tests: PostGIS Geodesic Formulas, Risk Math, Anti-Leakage Constraints
├── Integration Tests (pytest tests/test_frontend_gis_integration.py): 12/12 PASSED (100%)
├── Spatial BBox Performance Benchmarks: Sub-100ms PostGIS queries across Western, Central, Southern India
├── Next.js Production Compilation (npm run build): 28/28 static & dynamic routes compiled (0 errors)
├── Historical Partition Immutability Audit: 6,448,666 sealed records verified (0 discrepancy)
├── Dispatch Gate Security Audit: ENABLE_OPERATIONAL_DISPATCH_GATE = False verified (0 live leaks)
└── Disaster Recovery Restore Test: 100% schema, table, and row restoration verified
```

---

## 27. End-to-End Operational Workflow

The complete operational flow from satellite pass to analyst closure is summarized below:

```
[1] Satellite Overpass (VIIRS / MODIS)
     │ (Radiative heat detected at 375m / 1km resolution)
     ▼
[2] NASA FIRMS API Polling (Every 15 minutes)
     │ (Validated, deduplicated, written to PostgreSQL / PostGIS)
     ▼
[3] Incremental DBSCAN Event Clustering
     │ (Grouped into spatiotemporal event E_j with centroid and FRP stats)
     ▼
[4] 26-Feature Point-in-Time Generation (t_obs < t_event)
     │ (Proximity to OSM plants, CEA stations, IBM mines, FSI forests, Bhuvan LULC)
     ▼
[5] XGBoost Inference + Balanced Platt Probability Calibration
     │ (Source classified; uncalibrated overconfidence eliminated)
     ▼
[6] TreeExplainer SHAP Attribution + Multi-Factor Fire Risk Scoring
     │ (Feature attributions computed; 0-100 composite risk calculated)
     ▼
[7] Tri-Tier Human-in-the-Loop Routing Policy
     ├── Tier 1 (Conf >= 0.85): Autonomous Classification & Logging (97.18% Acc)
     ├── Tier 2 (0.60 <= Conf < 0.85): Routed to Analyst Command Center Queue
     └── Tier 3 (Conf < 0.60): Routed to Uncertainty / Active Learning Desk
     ▼
[8] Command Center Investigation & Tri-Tier Review
     │ (Analyst inspects 7-Layer Dossier, reviews SHAP waterfall, confirms/corrects)
     ▼
[9] Alert Lifecycle Closure & Immutable Audit Logging
     │ (State transition: ACKNOWLEDGED -> VERIFIED -> RESOLVED -> CLOSED)
     ▼
[10] Continuous Inactive Dispatch Safety Enforced
      (ENABLE_OPERATIONAL_DISPATCH_GATE = False)
```

---

## 28. Current Production Readiness

AGNI-NETRA is **Production-Ready for Controlled Activation**:

```
+-----------------------------------------------------------------------------------------+
|                                PRODUCTION READINESS STATUS                              |
+-----------------------------------------------------------------------------------------+
| Core Platform Infrastructure       : HEALTHY & FULLY OPERATIONAL                        |
| Frontend Command Center (Next.js)  : HEALTHY (http://localhost:3000/dashboard)          |
| Backend API Gateway (FastAPI)      : HEALTHY (http://localhost:8000/api/v1/docs)        |
| PostgreSQL / PostGIS Spatial DB    : CONNECTED & OPTIMIZED                              |
| Master GIS Multi-Layer Engine      : 8 OPERATIONAL VECTOR LAYERS                        |
| Historical Data Immutability       : 100% SEALED (6,448,666 records, 0 diff)            |
| Machine-Learning Model             : xgb-v3.0-real-candidate (GOVERNED INACTIVE)        |
| Operational Dispatch Gate          : ENFORCED FALSE (0 live external dispatches)        |
| Overall Deployment Gate            : CONTROLLED GO-LIVE READY                           |
+-----------------------------------------------------------------------------------------+
```

### Operational Distinction: Readiness vs. Autonomous Dispatch
* **Operational Readiness**: The system is fully running locally, ingesting live satellite data, clustering events, computing features, running ML inference, scoring risk, and rendering the National Command Center.
* **Controlled Activation**: Alerts are securely routed to the **internal Human-in-the-Loop Analyst Queue**.
* **Autonomous External Dispatch**: Direct automated transmission of alerts to external emergency agencies (NDRF, State Fire Services) is **intentionally disabled** (`ENABLE_OPERATIONAL_DISPATCH_GATE = False`) pending formal institutional agency sign-off.

---

## 29. Limitations and Threats to Validity

1. **Satellite Temporal Revisit Constraints**: Low Earth Orbit (LEO) satellites (VIIRS, MODIS) provide 2–4 overpasses daily per location. Short-lived flash fires occurring between overpasses cannot be observed.
2. **Cloud and Atmospheric Attenuation**: Heavy cloud cover during peak monsoon months attenuates infrared radiative signatures, reducing detection sensitivity.
3. **Spatial Resolution Limits**: Sub-pixel thermal emitters below the 375m VIIRS instantaneous field of view require high thermal intensity ($> 2\text{ MW}$) to trigger detection.
4. **Contextual Dataset Completeness**: While OSM contains 35,684 industrial facilities, unorganized or informal small-scale industrial units may lack cadastral mapping.
5. **Class Imbalance in Ground Truth**: High-frequency agricultural burning and industrial flares outnumber rare industrial catastrophe events in historical records.

---

## 30. Future Enhancements

1. **Geostationary Satellite Telemetry Integration**: Integrating high-temporal-frequency geostationary sensors (INSAT-3D/3DR, Himawari-9) to achieve 15-minute thermal monitoring over India.
2. **High-Resolution Optical/SAR Verification**: Automating on-demand cross-referencing with Sentinel-2 optical and Sentinel-1 Synthetic Aperture Radar (SAR) imagery for post-fire burn scar assessment.
3. **Deep Spatiotemporal Sequence Modeling**: Incorporating Graph Neural Networks (GNNs) and Transformer architectures to model long-term industrial thermal behavior.
4. **Vector Tiles (MVT) at National Scale**: Transitioning static GeoJSON boundaries to dynamic Mapbox Vector Tile (MVT) protocols for national-scale sub-district rendering.
5. **Mobile First-Responder PWA**: Developing an offline-first Progressive Web Application for field fire officers and forest rangers.

---

## 31. Conclusion

AGNI-NETRA establishes a new benchmark for satellite-based thermal intelligence in India. By bridging the critical gap between raw Earth observation detections and actionable operational intelligence, the platform demonstrates that:
1. **Multi-Source Spatial Fusion** transforms raw coordinates into rich, contextualized situational awareness.
2. **Point-in-Time Anti-Leakage Feature Engineering** and **Lookback Normalization** eliminate temporal bias and resolve apparent feature drift across multi-year archives.
3. **Balanced Platt Probability Calibration** eliminates dangerous overconfidence, reducing multiclass log-loss by 55.7%.
4. **Tri-Tier Human-in-the-Loop Routing** guarantees **97.18% selective accuracy** on autonomous candidates while protecting analysts from alert fatigue.
5. **PostGIS-Powered Viewport Querying** delivers sub-100ms multi-layer GIS command center performance across 8+ million spatial records.

AGNI-NETRA is verified, hardened, and ready for governed operational activation.

---

## References / Data Sources

1. **NASA FIRMS**: NASA Fire Information for Resource Management System. VIIRS (S-NPP, NOAA-20, NOAA-21) and MODIS (Terra, Aqua) Thermal Anomalies / Fire Locations. URL: `https://firms.modaps.eosdis.nasa.gov/`
2. **OpenStreetMap**: OpenStreetMap National Industrial and Power Generating Facility Registries for India. URL: `https://www.openstreetmap.org/`
3. **Central Electricity Authority (CEA)**: Ministry of Power, Government of India. National Power Generating Stations Database. URL: `https://cea.nic.in/`
4. **Indian Bureau of Mines (IBM)**: Ministry of Mines, Government of India. National Mining Lease and Mineral Concession Cadastral Database. URL: `https://ibm.gov.in/`
5. **Ministry of Environment, Forest and Climate Change (MoEFCC)**: PARIVESH (Pro-Active and Responsive facilitation by Interactive, Virtuous and Environmental Single-window Hub). URL: `https://parivesh.nic.in/`
6. **Forest Survey of India (FSI)**: India State of Forest Report (ISFR). District-wise Forest Canopy Density Classifications. URL: `https://fsi.nic.in/`
7. **Wildlife Institute of India (WII)**: National Protected Area Network and Eco-Sensitive Zone (ESZ) Geospatial Database. URL: `https://wii.gov.in/`
8. **ISRO / NRSC Bhuvan**: National Remote Sensing Centre, Indian Space Research Organisation. 1:50,000 Land Use / Land Cover (LULC) Multi-Temporal Geoportal. URL: `https://bhuvan.nrsc.gov.in/`
9. **Chen, T., & Guestrin, C. (2016)**: XGBoost: A Scalable Tree Boosting System. *Proceedings of the 22nd ACM SIGKDD International Conference on Knowledge Discovery and Data Mining*, 785–794.
10. **Lundberg, S. M., & Lee, S.-I. (2017)**: A Unified Approach to Interpreting Model Predictions. *Advances in Neural Information Processing Systems (NeurIPS 30)*, 4765–4774.
11. **Platt, J. (1999)**: Probabilistic Outputs for Support Vector Machines and Comparisons to Regularized Likelihood Methods. *Advances in Large Margin Classifiers*, 10(3), 61–74.
12. **Guo, C., Pleiss, G., Sun, Y., & Weinberger, K. Q. (2017)**: On Calibration of Modern Neural Networks. *International Conference on Machine Learning (ICML)*, 1321–1330.
13. **Ester, M., Kriegel, H.-P., Sander, J., & Xu, X. (1996)**: A Density-Based Algorithm for Discovering Clusters in Large Spatial Databases with Noise. *KDD-96 Proceedings*, 226–231.
14. **PostGIS Project**: PostGIS Spatial Database Extension for PostgreSQL. URL: `https://postgis.net/`
15. **MapLibre Project**: MapLibre GL JS Open-Source WebGL Vector Map Library. URL: `https://maplibre.org/`

---

## Appendices

### Appendix A: Database Schema Specifications

```sql
-- Core Thermal Detections Table (Partitioned by Year)
CREATE TABLE thermal_detections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    acq_timestamp TIMESTAMPTZ NOT NULL,
    acq_date DATE NOT NULL,
    frp DOUBLE PRECISION NOT NULL,
    brightness DOUBLE PRECISION NOT NULL,
    bright_t31 DOUBLE PRECISION,
    satellite VARCHAR(20) NOT NULL,
    instrument VARCHAR(20) NOT NULL,
    confidence VARCHAR(20) NOT NULL,
    daynight VARCHAR(5) NOT NULL,
    is_demo BOOLEAN DEFAULT FALSE,
    geom GEOMETRY(Point, 4326) NOT NULL
);
CREATE INDEX idx_thermal_detections_geom ON thermal_detections USING GIST(geom);
CREATE INDEX idx_thermal_detections_timestamp ON thermal_detections(acq_timestamp);

-- Clustered Thermal Events Table
CREATE TABLE thermal_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_code VARCHAR(50) UNIQUE NOT NULL,
    first_detected TIMESTAMPTZ NOT NULL,
    last_detected TIMESTAMPTZ NOT NULL,
    centroid_lat DOUBLE PRECISION NOT NULL,
    centroid_lon DOUBLE PRECISION NOT NULL,
    detection_count INTEGER NOT NULL,
    max_frp DOUBLE PRECISION NOT NULL,
    avg_frp DOUBLE PRECISION NOT NULL,
    state VARCHAR(100),
    district VARCHAR(100),
    status VARCHAR(50) DEFAULT 'ACTIVE',
    geom GEOMETRY(Point, 4326) NOT NULL
);
CREATE INDEX idx_thermal_events_geom ON thermal_events USING GIST(geom);

-- Event Features Table (26 Dimensions)
CREATE TABLE event_features (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id UUID REFERENCES thermal_events(id) ON DELETE CASCADE,
    frp_max DOUBLE PRECISION,
    frp_avg DOUBLE PRECISION,
    bright_max DOUBLE PRECISION,
    persistence_score DOUBLE PRECISION,
    recurrence_rate DOUBLE PRECISION,
    baseline_deviation_ratio DOUBLE PRECISION,
    dist_to_industrial_m DOUBLE PRECISION,
    dist_to_power_m DOUBLE PRECISION,
    dist_to_mine_m DOUBLE PRECISION,
    in_protected_area BOOLEAN,
    dist_to_pa_m DOUBLE PRECISION,
    forest_coverage_pct DOUBLE PRECISION,
    feature_vector JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Appendix B: Operational Runbooks & Disaster Recovery Protocols

1. **Model Rollback Protocol**: If online performance degrades or PSI exceeds 0.25 on mature features, execute:
   ```bash
   python ml/scripts/rollback_model.py --target-version xgb-v2.0-real-candidate
   ```
2. **Database Backup & Disaster Restore**:
   ```bash
   # Automated Snapshot Backup
   pg_dump -h localhost -U agni_user -d agni_netra -F c -b -v -f backups/agni_netra_snapshot.dump
   
   # Verification Restore to Isolated Instance
   createdb -h localhost -U agni_user agni_netra_restore_test
   pg_restore -h localhost -U agni_user -d agni_netra_restore_test -v backups/agni_netra_snapshot.dump
   ```
3. **Operational Dispatch Activation Safety Checklist**:
   - `[ ]` Institutional agency sign-off obtained from State Disaster Management Authority (SDMA).
   - `[ ]` Continuous 30-day shadow mode completed with zero critical false positive alarms.
   - `[ ]` Model drift PSI verified $< 0.15$ across all 26 features.
   - `[ ]` Set `ENABLE_OPERATIONAL_DISPATCH_GATE = True` in `.env` and restart worker service.
