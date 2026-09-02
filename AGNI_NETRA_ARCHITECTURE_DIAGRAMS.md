# AGNI-NETRA: System Architecture & Engineering Diagrams

This document provides complete, high-resolution architectural diagrams illustrating the end-to-end engineering, geospatial fusion, machine learning, and operational workflow of the **AGNI-NETRA** platform.

---

## 1. Overall System Architecture

```mermaid
graph TB
    subgraph SATELLITE_INGESTION["Layer 1: Satellite Telemetry Ingestion"]
        FIRMS["NASA FIRMS API<br/>(VIIRS SNPP, NOAA-20/21, MODIS Aqua/Terra)"]
        INGEST["Ingestion Worker<br/>(Deduplication, BBox Validation, Integrity Checks)"]
        FIRMS --> INGEST
    end

    subgraph DATABASE_LAYER["Layer 2: PostGIS Database & Knowledge Base (EPSG:4326)"]
        DB_THERMAL[("thermal_detections<br/>(8.2M+ rows, Partitioned)")]
        DB_EVENTS[("thermal_events<br/>(DBSCAN Clustered)")]
        DB_FAC[("industrial_facilities<br/>(35,684 records)")]
        DB_POWER[("cea_power_stations<br/>(1,633 records)")]
        DB_MINE[("ibm_mining_leases<br/>(98,793 records)")]
        DB_FOREST[("fsi_isfr_forest_stats<br/>& protected_areas")]
        DB_LULC[("lulc_spatial_features<br/>(ISRO Bhuvan)")]
        DB_ADMIN[("admin_boundaries<br/>(36 States, 736 Districts)")]
        
        INGEST --> DB_THERMAL
        DB_THERMAL --> DB_EVENTS
    end

    subgraph SPATIAL_ENRICHMENT["Layer 3: PostGIS Spatial Intelligence & Feature Engineering"]
        DBSCAN["Incremental Spatiotemporal Clustering<br/>(DBSCAN: eps=0.015°, min_samples=3)"]
        POINT_IN_TIME["Point-in-Time Anti-Leakage Feature Engine<br/>(t_obs < t_event; 30d/365d Lookbacks)"]
        PROXIMITY["PostGIS Geodesic Proximity Engine<br/>(ST_Distance, ST_DWithin, ST_Intersects)"]
        
        DB_EVENTS --> DBSCAN
        DBSCAN --> POINT_IN_TIME
        DB_FAC & DB_POWER & DB_MINE & DB_FOREST & DB_LULC & DB_ADMIN --> PROXIMITY
        PROXIMITY --> POINT_IN_TIME
    end

    subgraph ML_INFERENCE["Layer 4: Machine Learning & Risk Intelligence"]
        XGB["XGBoost Multi-Class Classifier<br/>(v3.0-real-candidate, 26 Features)"]
        CALIB["Balanced Platt Calibrator<br/>(Log-Loss: 0.7124, ECE: 0.1294)"]
        SHAP_EXP["TreeExplainer SHAP Engine<br/>(Local Feature Attribution)"]
        RISK_ENG["Multi-Factor Risk Engine<br/>(Intensity 40% + Asset 35% + Ecology 25%)"]
        
        POINT_IN_TIME --> XGB
        XGB --> CALIB
        CALIB --> SHAP_EXP
        CALIB --> RISK_ENG
        SHAP_EXP --> RISK_ENG
    end

    subgraph HITL_DECISION["Layer 5: Human-in-the-Loop Tri-Tier Decision Support"]
        ROUTER{"Tri-Tier Routing Engine"}
        T1["Tier 1: High-Confidence Autonomous<br/>(Conf >= 0.85, 97.18% Selective Acc)"]
        T2["Tier 2: Analyst Review Queue<br/>(0.60 <= Conf < 0.85, 7-Layer Dossier)"]
        T3["Tier 3: Uncertainty / Active Learning<br/>(Conf < 0.60 or High Entropy)"]
        
        RISK_ENG --> ROUTER
        ROUTER -->|Conf >= 0.85| T1
        ROUTER -->|0.60 <= Conf < 0.85| T2
        ROUTER -->|Conf < 0.60| T3
    end

    subgraph DISPATCH_SAFETY["Layer 6: Operational Safety & Governance Gate"]
        GATE{"ENABLE_OPERATIONAL_DISPATCH_GATE<br/>(Enforced FALSE)"}
        DISPATCH_INACTIVE["DISPATCH INACTIVE<br/>(Alerts queued for Analyst Review)"]
        DISPATCH_ACTIVE["AUTHORIZED ACTIVATION<br/>(Future Agency Dispatch)"]
        
        T1 & T2 & T3 --> GATE
        GATE -->|False (Current)| DISPATCH_INACTIVE
        GATE -->|True (Controlled)| DISPATCH_ACTIVE
    end

    subgraph COMMAND_CENTER["Layer 7: National Command Center & GIS Frontend"]
        NEXTJS["Next.js 15 App Router & API Gateway"]
        MAPLIBRE["MapLibre GL JS 8-Layer Vector Canvas<br/>(Viewport Bounding Box Querying)"]
        DOSSIER_VIEW["7-Layer Investigation Dossier UI"]
        ALERTS_DESK["Tri-Tier Alert Triage Desk"]
        
        DISPATCH_INACTIVE --> NEXTJS
        NEXTJS --> MAPLIBRE
        NEXTJS --> DOSSIER_VIEW
        NEXTJS --> ALERTS_DESK
    end
```

---

## 2. Multi-Source Geospatial Intelligence Architecture

```mermaid
graph LR
    subgraph SATELLITE_THERMAL["Satellite Thermal Telemetry"]
        VIIRS["VIIRS (375m)"]
        MODIS["MODIS (1km)"]
    end

    subgraph INFRASTRUCTURE_BASE["Industrial & Energy Infrastructure"]
        OSM["OSM Industrial Registry<br/>(35,684 Facilities)"]
        CEA["CEA Power Registry<br/>(1,633 Power Stations)"]
        IBM["IBM Mining Blocks<br/>(98,793 Leases)"]
    end

    subgraph ECOLOGICAL_CONTEXT["Ecological & Land Cover Context"]
        FSI["FSI ISFR District Forest Stats"]
        WII["WII Protected Areas & ESZ"]
        BHUVAN["ISRO Bhuvan LULC (1:50k)"]
    end

    subgraph ADMIN_GEOGRAPHY["Administrative Geography"]
        SOI_STATE["Survey of India States (36)"]
        SOI_DIST["Survey of India Districts (736)"]
        PARIVESH["MoEFCC PARIVESH Clearances"]
    end

    subgraph POSTGIS_FUSION["PostGIS Spatial Fusion Engine (EPSG:4326)"]
        ST_DIST["ST_Distance / ST_DWithin"]
        ST_INT["ST_Intersects"]
        ST_BBOX["ST_MakeEnvelope (Viewport Bounding Box)"]
    end

    VIIRS & MODIS --> POSTGIS_FUSION
    OSM & CEA & IBM --> POSTGIS_FUSION
    FSI & WII & BHUVAN --> POSTGIS_FUSION
    SOI_STATE & SOI_DIST & PARIVESH --> POSTGIS_FUSION

    POSTGIS_FUSION --> FEATURE_VECTOR["26-Dimensional Unified Spatial Feature Vector"]
```

---

## 3. Point-in-Time Anti-Leakage Feature Pipeline

```mermaid
sequenceDiagram
    autonumber
    participant Event as Thermal Event (E_i at t_event, coords)
    participant PostGIS as PostgreSQL / PostGIS DB
    participant Engine as Feature Pipeline Engine
    participant Model as XGBoost Classifier (v3.0)

    Event->>Engine: Trigger Feature Extraction (t_event)
    Note over Engine,PostGIS: Strict Anti-Leakage Rule: WHERE acq_timestamp < t_event
    Engine->>PostGIS: Query FIRMS observations in (t_event - 30d, t_event) within 5km
    PostGIS-->>Engine: Return 30-day active days -> persistence_score
    Engine->>PostGIS: Query FIRMS observations in (t_event - 365d, t_event) within 5km
    PostGIS-->>Engine: Return 365-day observation count -> recurrence_rate
    Engine->>PostGIS: ST_Distance to nearest industrial facility (EPSG:4326)
    PostGIS-->>Engine: dist_to_industrial_m
    Engine->>PostGIS: ST_Distance to nearest CEA power station
    PostGIS-->>Engine: dist_to_power_m
    Engine->>PostGIS: ST_Distance to nearest IBM mining lease
    PostGIS-->>Engine: dist_to_mine_m
    Engine->>PostGIS: ST_Intersects with WII Protected Areas & 10km ESZ
    PostGIS-->>Engine: in_protected_area, dist_to_pa_m
    Engine->>PostGIS: Query FSI district forest canopy density
    PostGIS-->>Engine: forest_coverage_pct
    Engine->>Engine: Synthesize 26 Normalized Features
    Engine->>Model: Feed Feature Vector -> Output Prediction & Calibrated Probabilities
```

---

## 4. Shadow Drift Investigation & Feature Remediation Pipeline

```mermaid
graph TD
    subgraph PHASE_8D["Phase 8D: Shadow Mode Drift Detection"]
        S_RAW["2026 Shadow Stream (N=414)"]
        S_PSI["PSI Audit against 2022-2024 Baseline"]
        S_RAW --> S_PSI
        S_PSI -->|Flagged| S_FLAG["5 Drifted Features:<br/>persistence_score (PSI 2.25)<br/>recurrence_rate (PSI 0.77)<br/>baseline_dev_ratio (PSI 0.32)<br/>dist_to_water_m (PSI 0.29)<br/>bright_max (PSI 0.14)"]
    end

    subgraph PHASE_8E["Phase 8E: Root-Cause Decomposition"]
        S_FLAG --> RC_INVEST["Empirical Investigation"]
        RC_INVEST --> RC_1["Expanding Lookback Query<br/>(t_obs < t accum from 2022 to 2026)"]
        RC_INVEST --> RC_2["Archive Boundary Truncation<br/>(2022 events had only 182d mean history)"]
        RC_INVEST --> RC_3["Cold-Start Baseline Fallback in 2022"]
    end

    subgraph PHASE_8F["Phase 8F: Algorithmic Feature Remediation"]
        RC_1 & RC_2 & RC_3 --> REMED["Remediation Formulas"]
        REMED --> F1["persistence_score = active_days_30d / 30.0<br/>(Fixed 30-Day Window)"]
        REMED --> F2["recurrence_rate = log1p(count_365d * (365 / avail_days))<br/>(Lookback-Normalized)"]
        REMED --> F3["baseline_deviation_ratio = max(1.0, count_30d / (prior_mean + eps))"]
    end

    subgraph PHASE_8G["Phase 8G: Post-Remediation Verification"]
        F1 & F2 & F3 --> AUDIT["Split-to-Split PSI Audit"]
        AUDIT --> RES_MATURE["Mature 365d Partitions (VAL 2025 vs TEST 2026):<br/>persistence_score PSI = 0.0300 (STABLE)<br/>baseline_deviation_ratio PSI = 0.0384 (STABLE)<br/>recurrence_rate PSI = 0.1316 (STABLE)"]
    end
```

---

## 5. Tri-Tier Human-in-the-Loop Decision Architecture

```mermaid
graph TD
    EVT[Thermal Event & Features] --> ML[XGBoost Classifier v3.0]
    ML --> CALIB[Balanced Platt Calibrator]
    CALIB --> PROBS[Calibrated Probability Vector P]
    PROBS --> ENTROPY[Normalized Shannon Entropy H]
    
    PROBS & ENTROPY --> POLICY{Tri-Tier Routing Policy}
    
    POLICY -->|P_max >= 0.85 & H < 0.40| T1[Tier 1: High-Confidence Candidate<br/>Selective Accuracy: 97.18%<br/>Action: Auto-Classify & Risk Score]
    POLICY -->|0.60 <= P_max < 0.85 or 0.40 <= H < 0.70| T2[Tier 2: Mandatory Analyst Review<br/>Selective Accuracy: 50.00%<br/>Action: Route to Command Center Queue with 7-Layer Dossier]
    POLICY -->|P_max < 0.60 or H >= 0.70| T3[Tier 3: Uncertainty / Active Learning<br/>Action: Flag for Expert Adjudication & Model Retraining Dataset]
    
    T1 --> AUDIT[Audit Trail Log]
    T2 --> ANALYST[Analyst Review Desk]
    T3 --> ACTIVE_LEARN[Active Learning Repository]
    
    ANALYST -->|Confirm / Correct| VERIFY[verification_records]
    VERIFY --> AUDIT
```

---

## 6. Alert Lifecycle & State Transition Model

```mermaid
stateDiagram-v2
    [*] --> NEW: Event Detected & Risk >= Threshold
    
    NEW --> ACKNOWLEDGED: Analyst Claims Alert
    NEW --> DISMISSED: Analyst Rejects (False Positive)
    
    ACKNOWLEDGED --> UNDER_INVESTIGATION: 7-Layer Dossier Opened
    
    UNDER_INVESTIGATION --> VERIFIED: Ground/Evidence Confirmed
    UNDER_INVESTIGATION --> DISMISSED: Evidence Invalidated
    
    VERIFIED --> RESOLVED: Response Executed
    DISMISSED --> CLOSED: Archived with Justification
    RESOLVED --> CLOSED: Investigation Closed
    
    CLOSED --> [*]
```

---

## 7. PostgreSQL / PostGIS Relational Schema

```mermaid
erDiagram
    thermal_detections ||--o{ thermal_events : "clustered into"
    thermal_events ||--o| event_features : "features generated for"
    thermal_events ||--o| model_predictions : "classified as"
    thermal_events ||--o| risk_scores : "evaluated for"
    thermal_events ||--o{ alerts : "triggers"
    alerts ||--o{ alert_audit_logs : "audited by"
    alerts ||--o{ verification_records : "reviewed in"
    
    industrial_facilities ||--o{ thermal_events : "nearest plant to"
    protected_areas ||--o{ thermal_events : "ecological buffer for"
    admin_boundaries ||--o{ thermal_events : "jurisdiction of"
    
    thermal_detections {
        uuid id PK
        timestamp acq_timestamp
        float latitude
        float longitude
        float frp
        float brightness
        string satellite
        string confidence
        geometry geom
    }
    
    thermal_events {
        uuid id PK
        string event_code UK
        timestamp first_detected
        timestamp last_detected
        float centroid_lat
        float centroid_lon
        int detection_count
        float max_frp
        float avg_frp
        geometry geom
    }
    
    event_features {
        uuid id PK
        uuid event_id FK
        float persistence_score
        float recurrence_rate
        float baseline_deviation_ratio
        float dist_to_industrial_m
        float dist_to_power_m
        float dist_to_mine_m
        float forest_coverage_pct
        json feature_vector
    }
    
    model_predictions {
        uuid id PK
        uuid event_id FK
        string predicted_class
        float raw_probability
        float calibrated_probability
        json class_probabilities
        json shap_values
    }
    
    risk_scores {
        uuid id PK
        uuid event_id FK
        float overall_risk_score
        string risk_level
        float intensity_subscore
        float asset_subscore
        float ecology_subscore
    }
    
    alerts {
        uuid id PK
        uuid event_id FK
        string alert_level
        string alert_type
        string routing_tier
        string status
        boolean is_operational_dispatch
    }
```

---

## 8. Frontend GIS Architecture & Dynamic Viewport Querying

```mermaid
graph TD
    subgraph BROWSER["Next.js 15 Client Browser (React App Router)"]
        UI_MAP["MapLibre GL Canvas<br/>(WebGL Vector Engine)"]
        UI_CTRL["Layer Control Panel<br/>(8 Checkbox Toggles)"]
        UI_LEGEND["Tactical Map Legend"]
        UI_DOSSIER["7-Layer Investigation Dossier"]
        UI_KPI["Live Telemetry KPI Cards"]
    end

    subgraph CLIENT_STATE["Client-Side Viewport State Management"]
        BBOX_CALC["Compute Viewport Bounds<br/>(bbox = min_lon, min_lat, max_lon, max_lat)"]
        DEBOUNCE["400ms Debounce Filter"]
        UI_MAP -->|moveend / zoomend| BBOX_CALC
        BBOX_CALC --> DEBOUNCE
    end

    subgraph FASTAPI_GIS["Backend PostGIS Spatial Gateway (/api/v1/gis/*)"]
        API_LAYERS["/api/v1/gis/layers (Master Catalog)"]
        API_THERMAL["/api/v1/gis/thermal-events (Active Events GeoJSON)"]
        API_FAC["/api/v1/gis/industrial-facilities?bbox=... (BBox Spatial Index)"]
        API_POWER["/api/v1/gis/power-stations (CEA GeoJSON)"]
        API_MINE["/api/v1/gis/mining (IBM GeoJSON)"]
        API_PA["/api/v1/gis/protected-areas (WII GeoJSON)"]
        API_LULC["/api/v1/gis/lulc (Bhuvan GeoJSON)"]
        API_ADMIN["/api/v1/gis/admin/* (States & Districts)"]
        API_DOSSIER["/api/v1/gis/dossier/{event_id} (7-Layer Evidence Cascade)"]
    end

    DEBOUNCE --> API_FAC
    UI_CTRL --> API_LAYERS & API_THERMAL & API_POWER & API_MINE & API_PA & API_LULC & API_ADMIN
    UI_MAP -->|Feature Click| API_DOSSIER
    API_DOSSIER --> UI_DOSSIER
```
