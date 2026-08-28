import pytest
from datetime import datetime, timezone
from backend.app.services.clustering_service import cluster_thermal_detections
from backend.app.services.persistence_service import calculate_persistence_metrics
from backend.app.services.risk_service import calculate_risk_score
from ml.inference.predictor import thermal_predictor
from backend.app.services.report_service import generate_event_pdf_report


def test_spatiotemporal_clustering():
    now = datetime.now(timezone.utc)
    raw_points = [
        {"latitude": 22.3550, "longitude": 69.8650, "acq_timestamp": now, "frp": 120.0, "brightness": 340.0, "source": "FIRMS", "sensor": "VIIRS"},
        {"latitude": 22.3554, "longitude": 69.8655, "acq_timestamp": now, "frp": 130.0, "brightness": 345.0, "source": "FIRMS", "sensor": "VIIRS"},
        # Distinct far point (Delhi)
        {"latitude": 28.7040, "longitude": 77.1020, "acq_timestamp": now, "frp": 25.0, "brightness": 315.0, "source": "FIRMS", "sensor": "VIIRS"},
    ]

    events = cluster_thermal_detections(raw_points, eps_km=2.0)
    assert len(events) == 2  # Jamnagar cluster + Delhi cluster
    
    jamnagar_event = next(e for e in events if e["state"] == "Gujarat")
    assert jamnagar_event["detection_count"] == 2
    assert jamnagar_event["avg_frp"] == 125.0


def test_persistence_metrics():
    now = datetime.now(timezone.utc)
    detections = [
        {"acq_timestamp": now, "day_night": "N", "frp": 80.0},
        {"acq_timestamp": now, "day_night": "N", "frp": 90.0},
        {"acq_timestamp": now, "day_night": "D", "frp": 85.0}
    ]
    metrics = calculate_persistence_metrics(detections)
    assert metrics["day_night_ratio"] == 2.0  # 2 night / 1 day
    assert "persistence_score" in metrics


def test_ml_inference_and_shap():
    event_data = {
        "max_frp": 180.0,
        "avg_frp": 140.0,
        "frp_variance": 20.0,
        "avg_brightness": 360.0,
        "nearest_facility_distance_m": 80.0,
        "landcover_class": "Industrial",
        "persistence_score": 8.0,
        "recurrence_rate": 2.1,
        "day_night_ratio": 1.4,
        "baseline_deviation_ratio": 1.1,
        "industrial_context_score": 0.95
    }

    result = thermal_predictor.predict(event_data)
    assert result["predicted_class"] in ["Gas Flare", "Industrial Fire"]
    assert result["confidence"] > 0.5
    assert "top_contributors" in result["shap_values"]
    assert len(result["shap_values"]["top_contributors"]) > 0


def test_risk_score_engine():
    score, level, subscores, reasons = calculate_risk_score(
        max_frp=220.0,
        avg_frp=160.0,
        anomaly_info={"is_anomaly": True, "z_score": 3.2, "deviation_ratio": 2.5, "explanation": "Spike detected"},
        persistence_info={"persistence_score": 7.5},
        nearest_settlement_dist_m=800.0,
        nearest_facility_dist_m=120.0,
        landcover_class="Industrial",
        predicted_class="Industrial Fire"
    )

    assert score >= 70.0
    assert level in ["HIGH", "CRITICAL"]
    assert len(reasons) > 0


def test_pdf_report_generation():
    event_data = {
        "event_code": "EVT-TEST-001",
        "state": "Gujarat",
        "latitude": 22.355,
        "longitude": 69.865,
        "detection_count": 5,
        "max_frp": 120.0,
        "avg_frp": 95.0,
        "first_seen": datetime.now(timezone.utc),
        "last_seen": datetime.now(timezone.utc),
        "facility_status": "KNOWN",
        "landcover_class": "Industrial",
        "nearest_facility_distance_m": 120.0
    }
    pred_data = {
        "predicted_class": "Gas Flare",
        "confidence": 0.94,
        "explanation_summary": "Classified based on continuous 24x7 flaring pattern.",
        "shap_values": {"top_contributors": [{"feature": "day_night_ratio", "value": 1.4, "shap_value": 0.35}]}
    }
    risk_data = {
        "risk_level": "MODERATE",
        "risk_score": 48.5,
        "risk_reasons": ["Continuous flaring within refinery footprint"]
    }

    pdf_bytes = generate_event_pdf_report(event_data, pred_data, risk_data)
    assert len(pdf_bytes) > 1000
    assert pdf_bytes.startswith(b"%PDF")
