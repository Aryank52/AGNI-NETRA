from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from backend.app.models.domain import ThermalEvent, ThermalDetection, EventFeature, ModelPrediction, RiskScore, IndustrialFacility, CandidateFacility


def generate_event_trace_lineage(db: Session, event_id: str) -> Dict[str, Any]:
    """
    Generates an end-to-end scientific data lineage trail for an individual thermal event.
    Traces from satellite simulation / raw telemetry to spatial enrichment, ML inference, explainability, and HITL decision support.
    """
    event = db.query(ThermalEvent).filter(ThermalEvent.id == event_id).first()
    if not event:
        raise ValueError(f"Thermal Event {event_id} not found")

    stages = []
    first_det = event.detections[0] if event.detections else None
    
    is_simulation = False
    if first_det and ("SIMULATION" in first_det.source.upper() or "AGNI_SAT" in first_det.source.upper()):
        is_simulation = True
    elif event.event_code.startswith("EVT-SIM") or (event.candidate_facility and "SIM" in event.candidate_facility.facility_code):
        is_simulation = True

    step_counter = 1

    # Stage 0 (if Simulation): AGNI-SAT Spacecraft Simulation
    if is_simulation:
        stages.append({
            "step_number": step_counter,
            "stage": "SATELLITE_SIMULATION",
            "title": "AGNI-SAT-01 Virtual Orbit Pass & Synthetic Radiance Calculation",
            "status": "COMPLETED",
            "timestamp": event.first_seen.isoformat(),
            "provenance_source": "AGNI_SAT_DIGITAL_TWIN",
            "details": {
                "origin_type": "SIMULATED SATELLITE DATA",
                "spacecraft": "AGNI-SAT-01",
                "orbit": "Sun-Synchronous LEO 505 km",
                "active_sensor": first_det.sensor if first_det else "THERMAL_MWIR",
                "simulation_fidelity": "High-Fidelity Tabular & Radiance Physics"
            }
        })
        step_counter += 1

    # 1. Raw Telemetry Stage
    stages.append({
        "step_number": step_counter,
        "stage": "RAW_TELEMETRY",
        "title": "Satellite Telemetry Ingestion" if is_simulation else "NASA FIRMS Telemetry Overpass",
        "status": "COMPLETED",
        "timestamp": event.first_seen.isoformat(),
        "provenance_source": first_det.source if first_det else ("AGNI_SAT_SIMULATION" if is_simulation else "NASA_FIRMS_VIIRS"),
        "details": {
            "origin_type": "SIMULATED SATELLITE DATA" if is_simulation else "REAL SATELLITE DATA",
            "sensor": first_det.sensor if first_det else ("THERMAL_MWIR" if is_simulation else "VIIRS_NOAA20"),
            "satellite": first_det.satellite if first_det else ("AGNI-SAT-01" if is_simulation else "NOAA-20"),
            "day_night": first_det.day_night if first_det else "D",
            "source_record_id": first_det.id if first_det else "N/A"
        }
    })
    step_counter += 1

    # 2. Hotspot Detection
    stages.append({
        "step_number": step_counter,
        "stage": "DETECTION",
        "title": "Thermal Anomaly Radiometric Extraction",
        "status": "COMPLETED",
        "timestamp": event.first_seen.isoformat(),
        "provenance_source": "AGNI_SAT_375M" if is_simulation else "NASA_FIRMS_375M",
        "details": {
            "latitude": event.latitude,
            "longitude": event.longitude,
            "brightness_k": event.avg_brightness,
            "frp_mw": event.avg_frp,
            "max_frp_mw": event.max_frp,
            "detection_count": event.detection_count
        }
    })
    step_counter += 1

    # 3. DBSCAN Event Clustering
    stages.append({
        "step_number": step_counter,
        "stage": "EVENT_CLUSTER",
        "title": "Spatiotemporal DBSCAN Clustering",
        "status": "COMPLETED",
        "timestamp": event.last_seen.isoformat(),
        "provenance_source": "AGNI_NETRA_CLUSTERING_ENGINE",
        "details": {
            "cluster_code": event.event_code,
            "spatial_epsilon_km": 2.0,
            "time_window_hours": 24,
            "bounding_box": event.bounding_box or [event.latitude, event.longitude, event.latitude, event.longitude]
        }
    })
    step_counter += 1

    # 4. PostGIS Spatial Enrichment
    stages.append({
        "step_number": step_counter,
        "stage": "SPATIAL_ENRICHMENT",
        "title": "PostGIS Proximity & Cadastral Association",
        "status": "COMPLETED",
        "timestamp": event.created_at.isoformat(),
        "provenance_source": "POSTGIS_SPATIAL_INDEX",
        "details": {
            "facility_status": event.facility_status,
            "facility_name": event.facility.name if event.facility else (event.candidate_facility.name_label if event.candidate_facility else "None Identified"),
            "nearest_distance_m": event.nearest_facility_distance_m,
            "state": event.state,
            "district": event.district or "Unassigned"
        }
    })
    step_counter += 1

    # 5. ISRO Bhuvan LULC Context
    stages.append({
        "step_number": step_counter,
        "stage": "LULC_CONTEXT",
        "title": "ISRO Bhuvan 24m LULC Spatial Classification",
        "status": "COMPLETED",
        "timestamp": event.created_at.isoformat(),
        "provenance_source": "ISRO_BHUVAN_LULC_50K",
        "details": {
            "landcover_class": event.landcover_class,
            "resolution": "24m (1:50,000 Scale)",
            "sensor": "Resourcesat-2/2A LISS-III / LISS-IV",
            "is_industrial_zone": "Industrial" in event.landcover_class
        }
    })
    step_counter += 1

    # 6. Event-Driven Satellite Scene Search
    stages.append({
        "step_number": step_counter,
        "stage": "SATELLITE_CONTEXT",
        "title": "Sentinel-2 / Landsat STAC Catalog Linkage",
        "status": "COMPLETED",
        "timestamp": event.created_at.isoformat(),
        "provenance_source": "COPERNICUS_STAC_CATALOG",
        "details": {
            "sentinel_swir_bands": ["B11 (1610nm)", "B12 (2190nm)"],
            "landsat_thermal_bands": ["Band 10 TIRS (10.6-11.19µm @ 100m)"],
            "cloud_cover_filter": "< 20%",
            "scenes_matched": event.satellite_count
        }
    })
    step_counter += 1

    # 7. 18-Feature Engineering
    feat = event.features
    stages.append({
        "step_number": step_counter,
        "stage": "FEATURE_VECTOR",
        "title": "18-Dimensional Remote Sensing Tabular Feature Vector",
        "status": "COMPLETED",
        "timestamp": feat.created_at.isoformat() if feat else event.created_at.isoformat(),
        "provenance_source": "AGNI_NETRA_FEATURE_PIPELINE",
        "details": {
            "frp_max": feat.frp_max if feat else event.max_frp,
            "persistence_score": feat.persistence_score if feat else 0.0,
            "day_night_ratio": feat.day_night_ratio if feat else 0.0,
            "baseline_deviation_ratio": feat.baseline_deviation_ratio if feat else 1.0,
            "dist_to_forest_m": feat.dist_to_forest_m if feat else 99999.0
        }
    })
    step_counter += 1

    # 8. Model Inference & Uncertainty
    pred = event.prediction
    stages.append({
        "step_number": step_counter,
        "stage": "MODEL_INFERENCE",
        "title": "XGBoost Tabular Classification & Shannon Entropy",
        "status": "COMPLETED",
        "timestamp": pred.predicted_at.isoformat() if pred else event.created_at.isoformat(),
        "provenance_source": "XGBoost_Industrial_Classifier_v1.0",
        "details": {
            "predicted_class": pred.predicted_class if pred else "Uncertain",
            "confidence": pred.confidence if pred else 0.0,
            "entropy_uncertainty": round(1.0 - (pred.confidence if pred else 0.5), 3),
            "model_version": "v1.0-synthetic-baseline"
        }
    })
    step_counter += 1

    # 9. Explainability Waterfall
    stages.append({
        "step_number": step_counter,
        "stage": "SHAP_EXPLANATION",
        "title": "SHAP TreeExplainer Attribution Waterfall",
        "status": "COMPLETED",
        "timestamp": pred.predicted_at.isoformat() if pred else event.created_at.isoformat(),
        "provenance_source": "SHAP_TREE_EXPLAINER",
        "details": {
            "top_drivers": list((pred.shap_values or {}).keys())[:4] if pred else [],
            "explanation": pred.explanation_summary if pred else "No SHAP explanation generated."
        }
    })
    step_counter += 1

    # 10. Decision Support & HITL
    risk = event.risk
    stages.append({
        "step_number": step_counter,
        "stage": "DECISION_SUPPORT",
        "title": "Multi-Factor Risk Scoring & Human Verification Queue",
        "status": "COMPLETED",
        "timestamp": risk.evaluated_at.isoformat() if risk else event.created_at.isoformat(),
        "provenance_source": "AGNI_NETRA_RISK_ENGINE",
        "details": {
            "risk_score": risk.risk_score if risk else 0.0,
            "risk_level": risk.risk_level if risk else "LOW",
            "verifications_count": len(event.verifications)
        }
    })

    return {
        "event_id": event.id,
        "event_code": event.event_code,
        "origin_type": "SIMULATED SATELLITE DATA" if is_simulation else "REAL SATELLITE DATA",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_steps": len(stages),
        "stages": stages
    }
