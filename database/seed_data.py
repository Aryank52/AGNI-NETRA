import os
import sys
from datetime import datetime, timezone

# Add parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.orm import Session
from backend.app.core.database import SessionLocal, engine, Base
from backend.app.core.security import get_password_hash
from backend.app.models.domain import (
    User, DataSource, IndustrialFacility, CandidateFacility,
    ThermalEvent, ThermalDetection, HistoricalBaseline,
    EventFeature, ModelVersion, ModelPrediction, RiskScore, Alert
)
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

        # 2. Seed Data Sources
        sources = [
            {"name": "FIRMS_VIIRS", "adapter": "FIRMSAdapter", "desc": "NASA FIRMS 375m VIIRS Active Fire Product"},
            {"name": "OSM_INDUSTRIAL", "adapter": "OSMIndustrialAdapter", "desc": "OpenStreetMap Industrial Facility Registry"},
            {"name": "LULC_BHUVAN", "adapter": "LULCAdapter", "desc": "ISRO Bhuvan / ESA WorldCover Land Use Classification"},
            {"name": "SENTINEL_2", "adapter": "SentinelAdapter", "desc": "Copernicus Sentinel-2 MSI Multi-spectral SWIR Context"},
            {"name": "LANDSAT_TIRS", "adapter": "LandsatAdapter", "desc": "USGS/NASA Landsat 8/9 Thermal Infrared Sensor"}
        ]
        for s in sources:
            if not db.query(DataSource).filter(DataSource.source_name == s["name"]).first():
                ds = DataSource(
                    source_name=s["name"],
                    adapter_class=s["adapter"],
                    description=s["desc"],
                    is_active=True,
                    health_status="HEALTHY",
                    metadata_info={"coverage": "India", "latency_minutes": 180}
                )
                db.add(ds)
        db.commit()

        # 3. Seed Industrial Facilities & Baselines
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
                facility_map[hub["name"]] = fac
            else:
                facility_map[hub["name"]] = existing_fac
        db.commit()

        # 4. Ingest Raw Observations & Run Geospatial Intelligence Pipeline
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
                    # Check if matching candidate zone
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
                        # Assign non-industrial landcover based on location
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

    except Exception as e:
        db.rollback()
        print(f"[DATABASE SEED ERROR] {e}")
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
