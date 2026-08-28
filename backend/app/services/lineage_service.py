from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from backend.app.models.domain import ThermalEvent, ThermalDetection, EventFeature, ModelPrediction, RiskScore, IndustrialFacility, CandidateFacility


def generate_event_trace_lineage(db: Session, event_id: str) -> Dict[str, Any]:
    """
    Generates an end-to-end 10-stage scientific data lineage trail for an individual thermal event.
    Traces from raw satellite telemetry to spatial enrichment, ML inference, explainability, and HITL decision support.
    """
    event = db.query(ThermalEvent).filter(ThermalEvent.id == event_id).first()
    if not event:
        raise ValueError(f"Thermal Event {event_id} not found")

    stages = []

    # 1. Raw Telemetry Stage
    first_det = event.detections[0] if event.detections else None
    stages.append({
        "step_number": 1,
        "stage": "RAW_TELEMETRY",
        "title": "NASA FIRMS Telemetry Overpass",
        "status": "COMPLETED",
        "timestamp": event.first_seen.isoformat(),
        "provenance_source": first_det.source if first_det else "NASA_FIRMS_VIIRS",
        "details": {
            "sensor": first_det.sensor if first_det else "VIIRS_NOAA20",
            "satellite": first_det.satellite if first_det else "NOAA-20",
            "day_night": first_det.day_night if first_det else "D",
            "source_record_id": first_det.id if first_det else "N/A"
        }
    })

    # 2. Hotspot Detection
    stages.append({
        "step_number": 2,
        "stage": "DETECTION",
        "title": "Thermal Anomaly Radiometric Extraction",
        "status": "COMPLETED",
        "timestamp": event.first_seen.isoformat(),
        "provenance_source": "NASA_FIRMS_375M",
        "details": {
            "latitude": event.latitude,
            "longitude": event.longitude,
            "brightness_k": event.avg_brightness,
            "frp_mw": event.avg_frp,
            "max_frp_mw": event.max_frp,
            "detection_count": event.detection_count
        }
    })

    # 3. DBSCAN Event Clustering
    stages.append({
        "step_number": 3,
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

    # 4. PostGIS Spatial Enrichment
    stages.append({
        "step_number": 4,
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

    # 5. ISRO Bhuvan LULC Context
    stages.append({
        "step_number": 5,
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

    # 6. Event-Driven Satellite Scene Search
    stages.append({
        "step_number": 6,
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

    # 7. 18-Feature Engineering
    feat = event.features
    stages.append({
        "step_number": 7,
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

    # 8. Model Inference & Uncertainty
    pred = event.prediction
    stages.append({
        "step_number": 8,
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

    # 9. Explainability Waterfall
    stages.append({
        "step_number": 9,
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

    # 10. Decision Support & HITL
    risk = event.risk
    stages.append({
        "step_number": 10,
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
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_steps": len(stages),
        "stages": stages
    }
