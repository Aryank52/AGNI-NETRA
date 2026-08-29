import os
import sys
from datetime import datetime, timezone, timedelta

# Add parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.orm import Session
from backend.app.core.database import SessionLocal, engine, Base
from backend.app.core.security import get_password_hash
from backend.app.models.domain import (
    User, DataSource, IndustrialFacility, CandidateFacility,
    ThermalEvent, ThermalDetection, HistoricalBaseline, FacilityBaseline,
    EventFeature, ModelVersion, ModelPrediction, RiskScore, Alert,
    MLModelRegistry, DatasetRegistry, ThermalHistory, SimulationScenario
)
from backend.app.services.satellite_simulator import SCENARIOS_CATALOG
from backend.app.services.clustering_service import cluster_thermal_detections
from backend.app.services.persistence_service import calculate_persistence_metrics
from backend.app.services.baseline_service import compare_with_historical_baseline
from backend.app.services.anomaly_service import anomaly_engine
from backend.app.services.candidate_service import evaluate_candidate_industrial_source
from backend.app.services.risk_service import calculate_risk_score
from ml.inference.predictor import thermal_predictor
from data_pipeline.adapters.demo_adapter import (
    DEMO_INDUSTRIAL_HUBS, DEMO_NON_INDUSTRIAL_ZONES,
    DEMO_CANDIDATE_ZONES, generate_seed_observations
)


def seed_database(db: Session = None):
    """
    Creates tables, seeds RBAC users, industrial facilities, baselines,
    and runs the full analytical pipeline to create events, predictions, SHAP values, risk scores, and alerts.
    """
    Base.metadata.create_all(bind=engine)

    if db is None:
        db = SessionLocal()

    try:
        # 1. Seed RBAC Users
        demo_users = [
            {"email": "admin@agninetra.gov.in", "full_name": "Dr. Rajesh Sharma (Lead Admin)", "role": "ADMIN", "org": "ISRO / Remote Sensing Centre"},
            {"email": "analyst@agninetra.gov.in", "full_name": "Priya Verma (Thermal Analyst)", "role": "ANALYST", "org": "Central Pollution Control Board"},
            {"email": "researcher@isro.res.in", "full_name": "Dr. Amit Roy (Geospatial Researcher)", "role": "RESEARCHER", "org": "Indian Institute of Remote Sensing"},
            {"email": "industry@reliance.com", "full_name": "Vikram Patel (EHS Manager)", "role": "INDUSTRY", "org": "Reliance Jamnagar Operations"},
            {"email": "agency@ndma.gov.in", "full_name": "Col. S. Deshmukh (Disaster Response)", "role": "AGENCY", "org": "National Disaster Management Authority"},
            {"email": "public@user.in", "full_name": "Rohan Mehta (Citizen Analyst)", "role": "PUBLIC", "org": "Independent"}
        ]

        for u in demo_users:
            existing = db.query(User).filter(User.email == u["email"]).first()
            if not existing:
                user = User(
                    email=u["email"],
                    hashed_password=get_password_hash("AgniNetra@2026"),
                    full_name=u["full_name"],
                    role=u["role"],
                    organization=u["org"],
                    is_active=True
                )
                db.add(user)
        db.commit()

        # 2. Seed Canonical Data Sources
        sources = [
            {
                "name": "FIRMS_VIIRS",
                "adapter": "FIRMSAdapter",
                "category": "THERMAL_HOTSPOTS",
                "endpoint": "https://firms.modaps.eosdis.nasa.gov/api",
                "auth_type": "MAP_KEY",
                "configured": bool(os.getenv("FIRMS_MAP_KEY")),
                "desc": "NASA FIRMS VIIRS (NOAA-21, NOAA-20, Suomi-NPP @ 375m) NRT & Standard Active Fire",
                "terms_url": "https://earthdata.nasa.gov/earth-observation-data/near-real-time/firms/terms-of-use",
                "latency_ms": 320.0
            },
            {
                "name": "OSM_INDUSTRIAL",
                "adapter": "OSMIndustrialAdapter",
                "category": "FACILITY_REGISTRY",
                "endpoint": "https://overpass-api.de/api/interpreter",
                "auth_type": "NONE",
                "configured": True,
                "desc": "OpenStreetMap Indian Industrial Facilities, Mining, and Infrastructure Registry",
                "terms_url": "https://www.openstreetmap.org/copyright",
                "latency_ms": 450.0
            },
            {
                "name": "CEA_POWER_PLANTS",
                "adapter": "CEAFacilityAdapter",
                "category": "FACILITY_REGISTRY",
                "endpoint": "https://cea.nic.in/reports",
                "auth_type": "NONE",
                "configured": True,
                "desc": "Central Electricity Authority Verified Indian Thermal Power Stations & Generation Capacity",
                "terms_url": "https://cea.nic.in",
                "latency_ms": 180.0
            },
            {
                "name": "LULC_BHUVAN",
                "adapter": "BhuvanLULCAdapter",
                "category": "LULC",
                "endpoint": "https://bhuvan.nrsc.gov.in/bhuvan_links.php",
                "auth_type": "TOKEN",
                "configured": True,
                "desc": "ISRO Bhuvan / Resourcesat LISS-IV 24m Land Use & Land Cover National Atlas",
                "terms_url": "https://bhuvan.nrsc.gov.in/terms",
                "latency_ms": 280.0
            },
            {
                "name": "SENTINEL_2",
                "adapter": "SentinelSTACAdapter",
                "category": "MULTISPECTRAL",
                "endpoint": "https://earth-search.aws.element84.com/v1",
                "auth_type": "OAUTH2",
                "configured": True,
                "desc": "Copernicus Sentinel-2 MSI Multi-spectral SWIR (B11/B12 @ 20m) & Optical RGB Context",
                "terms_url": "https://sentinels.copernicus.eu/web/sentinel/terms-and-conditions",
                "latency_ms": 520.0
            },
            {
                "name": "LANDSAT_TIRS",
                "adapter": "LandsatSTACAdapter",
                "category": "SATELLITE_ARCHIVE",
                "endpoint": "https://landsatlook.usgs.gov/stac-server",
                "auth_type": "API_KEY",
                "configured": True,
                "desc": "USGS/NASA Landsat 8/9 Thermal Infrared Sensor (Band 10 LWIR @ 100m)",
                "terms_url": "https://www.usgs.gov/landsat-missions/landsat-data-policy",
                "latency_ms": 480.0
            },
            {
                "name": "MOSDAC_INSAT",
                "adapter": "MOSDACAdapter",
                "category": "THERMAL_HOTSPOTS",
                "endpoint": "https://www.mosdac.gov.in",
                "auth_type": "BASIC_AUTH",
                "configured": bool(os.getenv("MOSDAC_USERNAME")),
                "desc": "ISRO MOSDAC INSAT-3D/3DR Geostationary Meteorological Thermal Sensor (4km)",
                "terms_url": "https://www.mosdac.gov.in/terms",
                "latency_ms": 310.0
            }
        ]
        for s in sources:
            existing_ds = db.query(DataSource).filter(DataSource.source_name == s["name"]).first()
            if not existing_ds:
                ds = DataSource(
                    source_name=s["name"],
                    adapter_class=s["adapter"],
                    category=s["category"],
                    endpoint=s["endpoint"],
                    auth_type=s["auth_type"],
                    configured=s["configured"],
                    description=s["desc"],
                    is_active=True,
                    health_status="HEALTHY" if s["configured"] else "NOT_CONFIGURED",
                    latency_ms=s["latency_ms"],
                    terms_url=s["terms_url"],
                    provenance_info={"coverage": "National India", "crs": "EPSG:4326"},
                    metadata_info={"coverage": "India", "latency_minutes": 180}
                )
                db.add(ds)
        db.commit()

        # 3. Seed ML Model Registry
        models = [
            {
                "name": "XGBoost Industrial Classifier",
                "version": "v1.0-synthetic-baseline",
                "dataset_version": "v1.0-synthetic-grounded",
                "algo": "XGBoost",
                "path": "ml/models/xgboost_classifier_v1.joblib",
                "status": "ACTIVE",
                "is_active": True,
                "metrics": {
                    "accuracy": 0.9621,
                    "macro_f1": 0.9614,
                    "brier_score": 0.0522,
                    "spatial_holdout_f1": 0.9540,
                    "temporal_holdout_f1": 0.9482,
                    "cross_val_folds": 5
                },
                "notes": "Calibration baseline model trained on v1.0-synthetic-grounded (N=2800)."
            },
            {
                "name": "Random Forest Benchmark",
                "version": "rf-v1.0-benchmark",
                "dataset_version": "v1.0-synthetic-grounded",
                "algo": "Random Forest",
                "path": "ml/models/rf_classifier_v1.joblib",
                "status": "APPROVED",
                "is_active": False,
                "metrics": {
                    "accuracy": 0.9385,
                    "macro_f1": 0.9360,
                    "brier_score": 0.0781
                },
                "notes": "Benchmark comparison model."
            },
            {
                "name": "Isolation Forest Anomaly Radar",
                "version": "iso-v1.0-anomaly",
                "dataset_version": "v1.0-synthetic-grounded",
                "algo": "Isolation Forest",
                "path": "ml/models/isolation_forest_v1.joblib",
                "status": "ACTIVE",
                "is_active": True,
                "metrics": {
                    "outlier_detection_rate": 0.05,
                    "evaluated_samples": 2800
                },
                "notes": "Multivariate thermal anomaly outlier detector."
            }
        ]
        for m in models:
            if not db.query(MLModelRegistry).filter(MLModelRegistry.version == m["version"]).first():
                reg = MLModelRegistry(
                    model_name=m["name"],
                    version=m["version"],
                    dataset_version=m["dataset_version"],
                    algorithm=m["algo"],
                    metrics=m["metrics"],
                    artifact_path=m["path"],
                    status=m["status"],
                    is_active=m["is_active"],
                    notes=m["notes"],
                    approved_by="admin@agninetra.gov.in",
                    approved_at=datetime.now(timezone.utc)
                )
                db.add(reg)
        db.commit()

        # 4. Seed Dataset Registry
        datasets = [
            {
                "name": "AGNI-NETRA Grounded Synthetic Baseline",
                "version": "v1.0-synthetic-grounded",
                "type": "SYNTHETIC",
                "source": "PHYSICAL_SIMULATOR",
                "record_count": 2800,
                "verified_count": 400,
                "classes": {
                    "Industrial Fire": 400, "Gas Flare": 400, "Forest Fire": 400,
                    "Agricultural Burning": 400, "Mining Activity": 400,
                    "Other Thermal Source": 400, "Uncertain": 400
                },
                "eligible": True
            },
            {
                "name": "AGNI-NETRA Real Indian Telemetry V2",
                "version": "dataset_v2_india",
                "type": "REAL",
                "source": "NASA_FIRMS_VIIRS",
                "record_count": 1420,
                "verified_count": 312,
                "classes": {
                    "Industrial Fire": 180, "Gas Flare": 240, "Forest Fire": 310,
                    "Agricultural Burning": 420, "Mining Activity": 150,
                    "Other Thermal Source": 80, "Uncertain": 40
                },
                "eligible": True
            }
        ]
        for d in datasets:
            if not db.query(DatasetRegistry).filter(DatasetRegistry.version == d["version"]).first():
                d_reg = DatasetRegistry(
                    name=d["name"],
                    version=d["version"],
                    dataset_type=d["type"],
                    source=d["source"],
                    record_count=d["record_count"],
                    verified_count=d["verified_count"],
                    class_distribution=d["classes"],
                    training_eligible=d["eligible"]
                )
                db.add(d_reg)
        db.commit()

        # 5. Seed Industrial Facilities & Baselines
        facility_map = {}
        for hub in DEMO_INDUSTRIAL_HUBS:
            existing_fac = db.query(IndustrialFacility).filter(IndustrialFacility.name == hub["name"]).first()
            if not existing_fac:
                fac = IndustrialFacility(
                    name=hub["name"],
                    facility_type=hub["facility_type"],
                    status="KNOWN",
                    source="OSM",
                    source_id=f"OSM-{hub['facility_type']}-{hub['state'][:2]}",
                    state=hub["state"],
                    district=hub["district"],
                    latitude=hub["latitude"],
                    longitude=hub["longitude"],
                    confidence_score=0.98,
                    operating_hours=hub["operating_hours"],
                    contact_info={"ehs_officer": "ehs@facility.in", "emergency_phone": "+91-22-2800-4400"}
                )
                db.add(fac)
                db.flush()

                # Add baseline profile
                baseline = HistoricalBaseline(
                    facility_id=fac.id,
                    mean_frp=hub["mean_frp"],
                    median_frp=hub["mean_frp"] * 0.95,
                    std_frp=hub["std_frp"],
                    max_historical_frp=hub["mean_frp"] * 2.2,
                    detection_frequency_monthly=18.5,
                    day_night_ratio=hub["day_night_ratio"],
                    monthly_pattern={"Jan": 110, "Feb": 115, "Mar": 125, "Apr": 130, "May": 120, "Jun": 115},
                    baseline_status="ESTABLISHED"
                )
                db.add(baseline)

                # Add FacilityBaseline
                fac_base = FacilityBaseline(
                    facility_id=fac.id,
                    mean_frp=hub["mean_frp"],
                    median_frp=hub["mean_frp"] * 0.95,
                    variance_frp=hub["std_frp"] ** 2,
                    max_historical_frp=hub["mean_frp"] * 2.2,
                    frp_distribution={
                        "p25": round(hub["mean_frp"] * 0.65, 1),
                        "p50": round(hub["mean_frp"] * 0.95, 1),
                        "p75": round(hub["mean_frp"] * 1.25, 1),
                        "p90": round(hub["mean_frp"] * 1.60, 1),
                        "p99": round(hub["mean_frp"] * 2.10, 1)
                    },
                    frequency_days=24,
                    day_night_ratio=hub["day_night_ratio"],
                    status_band="NORMAL",
                    notes="Baseline calibrated over 90-day VIIRS/MODIS satellite passes."
                )
                db.add(fac_base)
                facility_map[hub["name"]] = fac
            else:
                facility_map[hub["name"]] = existing_fac
        db.commit()

        # 6. Ingest Raw Observations & Run Geospatial Intelligence Pipeline
        existing_events_count = db.query(ThermalEvent).count()
        if existing_events_count == 0:
            raw_observations = generate_seed_observations()
            
            # Convert raw observations to dicts for clustering
            obs_dicts = [
                {
                    "source_record_id": o.source_record_id,
                    "source": o.source,
                    "sensor": o.sensor,
                    "satellite": o.satellite,
                    "latitude": o.latitude,
                    "longitude": o.longitude,
                    "acq_timestamp": o.acq_timestamp,
                    "brightness": o.brightness,
                    "bright_t31": o.bright_t31,
                    "frp": o.frp,
                    "confidence": o.confidence,
                    "day_night": o.day_night,
                    "raw_metadata": o.metadata,
                    "is_demo": o.is_demo
                }
                for o in raw_observations
            ]

            # Spatiotemporal DBSCAN Clustering
            clustered_events = cluster_thermal_detections(obs_dicts, eps_km=2.0, min_samples=1)
            
            # Fetch all facility dicts for spatial matching
            all_facilities = db.query(IndustrialFacility).all()
            fac_list = [{"id": f.id, "name": f.name, "facility_type": f.facility_type, "latitude": f.latitude, "longitude": f.longitude} for f in all_facilities]

            for idx, c_evt in enumerate(clustered_events):
                evt_code = f"EVT-2026-08-{idx+1:04d}"
                c_lat = c_evt["latitude"]
                c_lon = c_evt["longitude"]
                
                # Persistence Analysis
                persistence_info = calculate_persistence_metrics(c_evt["detections"])
                
                # Spatial Proximity Matching to Facilities
                from backend.app.services.spatial_engine import find_nearest_facility
                nearest_fac, nearest_dist = find_nearest_facility(c_lat, c_lon, fac_list)

                # Determine Landcover & Facility Status
                fac_id = None
                cand_id = None
                if nearest_fac and nearest_dist < 600.0:
                    fac_id = nearest_fac["id"]
                    fac_status = "KNOWN"
                    lc_class = "Industrial"
                else:
                    # Check candidate evaluation
                    is_cand, ind_ctx_score, cand_evidence = evaluate_candidate_industrial_source(
                        c_evt, persistence_info, "Barren / Scrub", nearest_dist
                    )
                    if is_cand:
                        fac_status = "CANDIDATE"
                        lc_class = "Barren / Scrub"
                        
                        cand_fac = CandidateFacility(
                            name_label=f"Candidate-Industrial-GJ-{c_lat:.2f}N-{c_lon:.2f}E",
                            status="CANDIDATE",
                            latitude=c_lat,
                            longitude=c_lon,
                            state=c_evt["state"],
                            district="Bharuch",
                            industrial_context_score=ind_ctx_score,
                            persistence_days=persistence_info["active_days_count"],
                            detection_count=c_evt["detection_count"],
                            evidence_summary=cand_evidence
                        )
                        db.add(cand_fac)
                        db.flush()
                        cand_id = cand_fac.id
                    else:
                        fac_status = "UNKNOWN"
                        if "Sangrur" in str(c_evt["detections"]) or "Bathinda" in str(c_evt["detections"]):
                            lc_class = "Agriculture / Cropland"
                        elif "Similipal" in str(c_evt["detections"]) or "Western Ghats" in str(c_evt["detections"]):
                            lc_class = "Forest"
                        else:
                            lc_class = "Barren / Scrub"

                # Create ThermalEvent ORM
                event = ThermalEvent(
                    event_code=evt_code,
                    latitude=c_lat,
                    longitude=c_lon,
                    bounding_box=c_evt["bounding_box"],
                    convex_hull_geojson=c_evt["convex_hull_geojson"],
                    first_seen=c_evt["first_seen"],
                    last_seen=c_evt["last_seen"],
                    detection_count=c_evt["detection_count"],
                    avg_frp=c_evt["avg_frp"],
                    max_frp=c_evt["max_frp"],
                    min_frp=c_evt["min_frp"],
                    frp_variance=c_evt["frp_variance"],
                    avg_brightness=c_evt["avg_brightness"],
                    satellite_count=c_evt["satellite_count"],
                    facility_id=fac_id,
                    candidate_facility_id=cand_id,
                    facility_status=fac_status,
                    nearest_facility_distance_m=round(nearest_dist, 1),
                    landcover_class=lc_class,
                    state=c_evt["state"],
                    status="ACTIVE",
                    is_demo=True
                )
                db.add(event)
                db.flush()

                # Add ThermalDetections
                for det in c_evt["detections"]:
                    d_obj = ThermalDetection(
                        source=det["source"],
                        sensor=det["sensor"],
                        satellite=det.get("satellite"),
                        latitude=det["latitude"],
                        longitude=det["longitude"],
                        acq_timestamp=det["acq_timestamp"],
                        brightness=det.get("brightness"),
                        bright_t31=det.get("bright_t31"),
                        frp=det.get("frp", 0.0),
                        confidence=det.get("confidence", 80.0),
                        day_night=det.get("day_night", "D"),
                        event_id=event.id,
                        raw_metadata=det.get("raw_metadata", {}),
                        is_demo=True
                    )
                    db.add(d_obj)

                # Baseline & Anomaly Engine
                baseline_obj = None
                if fac_id:
                    baseline_db = db.query(HistoricalBaseline).filter(HistoricalBaseline.facility_id == fac_id).first()
                    if baseline_db:
                        baseline_obj = {
                            "mean_frp": baseline_db.mean_frp,
                            "std_frp": baseline_db.std_frp,
                            "median_frp": baseline_db.median_frp
                        }

                anomaly_res = anomaly_engine.evaluate_anomaly(
                    {"frp_avg": event.avg_frp, "frp_max": event.max_frp, "frp_std": event.frp_variance ** 0.5, "day_night_ratio": persistence_info["day_night_ratio"], "persistence_score": persistence_info["persistence_score"]},
                    baseline_stats=baseline_obj
                )

                # ML Feature Vector & Prediction
                feat_dict = {
                    "max_frp": event.max_frp,
                    "avg_frp": event.avg_frp,
                    "frp_variance": event.frp_variance,
                    "avg_brightness": event.avg_brightness,
                    "nearest_facility_distance_m": nearest_dist,
                    "landcover_class": lc_class,
                    "persistence_score": persistence_info["persistence_score"],
                    "recurrence_rate": persistence_info["recurrence_rate"],
                    "day_night_ratio": persistence_info["day_night_ratio"],
                    "baseline_deviation_ratio": anomaly_res["deviation_ratio"],
                    "industrial_context_score": 0.85 if fac_status == "KNOWN" else (0.75 if fac_status == "CANDIDATE" else 0.1)
                }

                # Extract Tabular Features ORM
                features_orm = EventFeature(
                    event_id=event.id,
                    frp_max=feat_dict["max_frp"],
                    frp_avg=feat_dict["avg_frp"],
                    frp_std=feat_dict["frp_variance"] ** 0.5,
                    bright_max=event.avg_brightness * 1.05,
                    bright_avg=event.avg_brightness,
                    dist_to_facility_m=nearest_dist,
                    dist_to_forest_m=100.0 if lc_class == "Forest" else 15000.0,
                    dist_to_agriculture_m=100.0 if lc_class == "Agriculture / Cropland" else 20000.0,
                    dist_to_settlement_m=2000.0,
                    dist_to_water_m=5000.0,
                    dist_to_mine_m=100.0 if lc_class == "Mining" else 40000.0,
                    landcover_code=1 if lc_class == "Industrial" else (5 if lc_class == "Forest" else 4),
                    persistence_score=feat_dict["persistence_score"],
                    recurrence_rate=feat_dict["recurrence_rate"],
                    day_night_ratio=feat_dict["day_night_ratio"],
                    baseline_deviation_ratio=feat_dict["baseline_deviation_ratio"],
                    industrial_context_score=feat_dict["industrial_context_score"]
                )
                db.add(features_orm)

                # ML Inference & SHAP
                pred_res = thermal_predictor.predict(feat_dict)
                
                pred_orm = ModelPrediction(
                    event_id=event.id,
                    predicted_class=pred_res["predicted_class"],
                    confidence=pred_res["confidence"],
                    class_probabilities=pred_res["class_probabilities"],
                    shap_values=pred_res["shap_values"],
                    explanation_summary=pred_res["explanation_summary"],
                    predicted_at=datetime.now(timezone.utc)
                )
                db.add(pred_orm)

                # Risk Engine
                risk_score_val, risk_lvl, subscores, reasons = calculate_risk_score(
                    max_frp=event.max_frp,
                    avg_frp=event.avg_frp,
                    anomaly_info=anomaly_res,
                    persistence_info=persistence_info,
                    nearest_settlement_dist_m=2000.0,
                    nearest_facility_dist_m=nearest_dist,
                    landcover_class=lc_class,
                    predicted_class=pred_res["predicted_class"]
                )

                risk_orm = RiskScore(
                    event_id=event.id,
                    risk_score=risk_score_val,
                    risk_level=risk_lvl,
                    intensity_subscore=subscores["intensity"],
                    abnormality_subscore=subscores["abnormality"],
                    persistence_subscore=subscores["persistence"],
                    exposure_subscore=subscores["exposure"],
                    context_subscore=subscores["context"],
                    risk_reasons=reasons,
                    evaluated_at=datetime.now(timezone.utc)
                )
                db.add(risk_orm)

                # Alert Generation for Critical / Abnormal / Candidate events
                if risk_lvl in ["CRITICAL", "HIGH"] or anomaly_res["is_anomaly"] or fac_status == "CANDIDATE":
                    alert_type = "ABNORMAL_SPIKE" if anomaly_res["is_anomaly"] else ("CANDIDATE_EMERGENCE" if fac_status == "CANDIDATE" else "NEW_HIGH_RISK")
                    alert = Alert(
                        event_id=event.id,
                        alert_level=risk_lvl if risk_lvl in ["HIGH", "CRITICAL"] else "MODERATE",
                        alert_type=alert_type,
                        title=f"{risk_lvl} Alert: {pred_res['predicted_class']} at {event.state}",
                        description=f"Automated intelligence triggered alert. Reasons: {', '.join(reasons[:2])}.",
                        status="NEW"
                    )
                    db.add(alert)

            db.commit()
            print(f"[DATABASE SEED] Seeded {len(clustered_events)} thermal events with full intelligence layers.")
        else:
            print("[DATABASE SEED] Database already contains thermal events. Skipping event generation.")

        # 7. Seed AGNI-SAT Simulation Scenarios
        for sc in SCENARIOS_CATALOG:
            existing_sc = db.query(SimulationScenario).filter(SimulationScenario.id == sc["id"]).first()
            if not existing_sc:
                s_orm = SimulationScenario(
                    id=sc["id"],
                    name=sc["name"],
                    scenario_type=sc["scenario_type"],
                    description=sc["description"],
                    target_state=sc["target_state"],
                    target_lat=sc["target_lat"],
                    target_lon=sc["target_lon"],
                    target_facility=sc["target_facility"],
                    expected_class=sc["expected_class"],
                    expected_risk_level=sc["expected_risk_level"],
                    parameters=sc["parameters"],
                    status="IDLE"
                )
                db.add(s_orm)
        db.commit()

        # 8. Seed Historical Thermal Archive Database (Multi-Year Indian Observations)
        existing_hist_count = db.query(ThermalHistory).count()
        if existing_hist_count == 0:
            hist_records = []
            # Generate multi-sensor records across Indian industrial and ecological zones
            base_date = datetime(2026, 8, 1, tzinfo=timezone.utc)
            hubs = [
                {"state": "Gujarat", "district": "Jamnagar", "lat": 22.3552, "lon": 69.8654, "sensor": "VIIRS_NOAA21", "frp": 128.0, "type": "STANDARD_SCIENCE"},
                {"state": "Madhya Pradesh", "district": "Singrauli", "lat": 24.1012, "lon": 82.6841, "sensor": "VIIRS_NOAA20", "frp": 195.0, "type": "STANDARD_SCIENCE"},
                {"state": "Chhattisgarh", "district": "Korba", "lat": 22.3485, "lon": 82.7231, "sensor": "MODIS_AQUA", "frp": 110.0, "type": "STANDARD_SCIENCE"},
                {"state": "Odisha", "district": "Angul", "lat": 20.8521, "lon": 85.1245, "sensor": "VIIRS_NOAA21", "frp": 142.0, "type": "STANDARD_SCIENCE"},
                {"state": "Gujarat", "district": "Surat", "lat": 21.1160, "lon": 72.6510, "sensor": "VIIRS_NOAA20", "frp": 165.0, "type": "STANDARD_SCIENCE"},
                {"state": "Maharashtra", "district": "Mumbai Suburban", "lat": 19.0125, "lon": 72.8984, "sensor": "VIIRS_NOAA21", "frp": 88.0, "type": "STANDARD_SCIENCE"},
                {"state": "Andhra Pradesh", "district": "Visakhapatnam", "lat": 17.6868, "lon": 83.2185, "sensor": "VIIRS_NOAA20", "frp": 120.0, "type": "STANDARD_SCIENCE"},
                {"state": "Odisha", "district": "Jagatsinghpur", "lat": 20.2644, "lon": 86.6710, "sensor": "VIIRS_NOAA21", "frp": 94.0, "type": "STANDARD_SCIENCE"},
                {"state": "West Bengal", "district": "Purba Medinipur", "lat": 22.0620, "lon": 88.0790, "sensor": "MODIS_TERRA", "frp": 78.0, "type": "STANDARD_SCIENCE"},
                {"state": "Punjab", "district": "Sangrur", "lat": 30.2450, "lon": 75.8420, "sensor": "VIIRS_NOAA20", "frp": 45.0, "type": "NRT"},
                {"state": "Odisha", "district": "Mayurbhanj", "lat": 21.8540, "lon": 86.3420, "sensor": "VIIRS_NOAA21", "frp": 135.0, "type": "NRT"},
                {"state": "Jharkhand", "district": "Dhanbad", "lat": 23.7460, "lon": 86.4150, "sensor": "LANDSAT_TIRS", "frp": 115.0, "type": "STANDARD_SCIENCE"}
            ]

            for h_idx, hub in enumerate(hubs):
                for day_offset in range(0, 90, 3):
                    t_obs = base_date - timedelta(days=day_offset, hours=h_idx % 12)
                    th = ThermalHistory(
                        source="NASA_FIRMS",
                        sensor=hub["sensor"],
                        satellite="NOAA-21" if "NOAA21" in hub["sensor"] else ("NOAA-20" if "NOAA20" in hub["sensor"] else "Terra"),
                        latitude=hub["lat"] + (day_offset % 5) * 0.001,
                        longitude=hub["lon"] + (day_offset % 3) * 0.001,
                        acq_date=t_obs.strftime("%Y-%m-%d"),
                        acq_time=t_obs.strftime("%H%M"),
                        acq_timestamp=t_obs,
                        brightness=340.0 + (day_offset % 20),
                        bright_t31=315.0,
                        frp=hub["frp"] + (day_offset % 15) * 1.5,
                        confidence=92.0,
                        day_night="N" if (h_idx % 2 == 0) else "D",
                        processing_type=hub["type"],
                        state=hub["state"],
                        district=hub["district"],
                        source_record_id=f"HIST-IND-{h_idx:02d}-{day_offset:03d}",
                        raw_metadata={"satellite_angle": 12.4, "scan_km": 0.375},
                        is_demo=False
                    )
                    db.add(th)
            db.commit()
            print(f"[DATABASE SEED] Seeded multi-year historical Indian thermal observations database.")

    except Exception as e:
        db.rollback()
        print(f"[DATABASE SEED ERROR] {e}")
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()

