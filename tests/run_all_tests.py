import os
import sys
from datetime import datetime, timezone

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.security import verify_password, get_password_hash, create_access_token
from backend.app.services.spatial_engine import haversine_distance_m, lookup_state
from backend.app.services.clustering_service import cluster_thermal_detections
from backend.app.services.persistence_service import calculate_persistence_metrics
from backend.app.services.risk_service import calculate_risk_score
from ml.inference.predictor import thermal_predictor
from backend.app.services.report_service import generate_event_pdf_report


def run_unit_tests():
    print("================================================================")
    print("      AGNI-NETRA COMPREHENSIVE SYSTEM ACCEPTANCE TESTS          ")
    print("================================================================")

    # 1. Test Password & Security
    print("\n[TEST 1] Testing Password Hashing & JWT Token Generation...")
    pwd = "AgniNetraSecurePassword123"
    hashed = get_password_hash(pwd)
    assert verify_password(pwd, hashed) is True, "Password verification failed"
    assert verify_password("WrongPassword", hashed) is False, "Wrong password accepted"
    token = create_access_token(subject="test-user-id", role="ANALYST")
    assert len(token.split(".")) == 3, "Invalid JWT format"
    print("  [OK] Security & JWT tokens: PASSED")

    # 2. Test Spatial Engine
    print("\n[TEST 2] Testing Spatial Engine Distance & Containment...")
    dist = haversine_distance_m(19.0760, 72.8777, 28.7041, 77.1025)
    assert 1100000 < dist < 1200000, f"Unexpected distance: {dist}"
    assert lookup_state(22.35, 69.86) == "Gujarat", "State lookup failed for Jamnagar"
    assert lookup_state(30.24, 75.84) == "Punjab", "State lookup failed for Sangrur"
    print("  [OK] Spatial calculations & State containment: PASSED")

    # 3. Test Spatiotemporal Event Clustering (DBSCAN)
    print("\n[TEST 3] Testing DBSCAN Spatiotemporal Event Clustering...")
    now = datetime.now(timezone.utc)
    raw_points = [
        {"latitude": 22.3550, "longitude": 69.8650, "acq_timestamp": now, "frp": 120.0, "brightness": 340.0, "source": "FIRMS", "sensor": "VIIRS"},
        {"latitude": 22.3554, "longitude": 69.8655, "acq_timestamp": now, "frp": 130.0, "brightness": 345.0, "source": "FIRMS", "sensor": "VIIRS"},
        {"latitude": 28.7040, "longitude": 77.1020, "acq_timestamp": now, "frp": 25.0, "brightness": 315.0, "source": "FIRMS", "sensor": "VIIRS"},
    ]
    clusters = cluster_thermal_detections(raw_points, eps_km=2.0)
    assert len(clusters) == 2, f"Expected 2 clusters, got {len(clusters)}"
    jamnagar = next(c for c in clusters if c["state"] == "Gujarat")
    assert jamnagar["detection_count"] == 2, "Cluster count mismatch"
    assert jamnagar["avg_frp"] == 125.0, "Average FRP mismatch"
    print("  [OK] Spatiotemporal DBSCAN clustering: PASSED")

    # 4. Test Persistence & Diurnal Metric Engine
    print("\n[TEST 4] Testing Persistence Score & Day/Night Ratio Calculation...")
    detections = [
        {"acq_timestamp": now, "day_night": "N", "frp": 80.0},
        {"acq_timestamp": now, "day_night": "N", "frp": 90.0},
        {"acq_timestamp": now, "day_night": "D", "frp": 85.0}
    ]
    p_metrics = calculate_persistence_metrics(detections)
    assert p_metrics["day_night_ratio"] == 2.0, "Diurnal ratio mismatch"
    assert p_metrics["persistence_score"] > 0, "Persistence score calculation failed"
    print("  [OK] Persistence & Day/Night dynamics: PASSED")

    # 5. Test ML XGBoost Classification & SHAP TreeExplainer
    print("\n[TEST 5] Testing XGBoost 7-Class AI & SHAP Explainability Engine...")
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
    prediction = thermal_predictor.predict(event_data)
    assert prediction["predicted_class"] in ["Gas Flare", "Industrial Fire"], f"Unexpected class: {prediction['predicted_class']}"
    assert prediction["confidence"] >= 0.5, "Confidence too low"
    assert "shap_values" in prediction, "Missing SHAP values"
    assert len(prediction["shap_values"]["top_contributors"]) > 0, "Missing SHAP contributors"
    print(f"  [OK] Classification ({prediction['predicted_class']}, {prediction['confidence']*100:.1f}%) & SHAP: PASSED")

    # 6. Test Risk Matrix Engine
    print("\n[TEST 6] Testing AGNI-NETRA Transparent Risk Engine...")
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
    assert score >= 70.0, f"Expected high risk score, got {score}"
    assert level in ["HIGH", "CRITICAL"], f"Expected HIGH/CRITICAL, got {level}"
    assert len(reasons) > 0, "No risk reasons returned"
    print(f"  [OK] Multi-factor Risk Engine ({level}, score {score}/100): PASSED")

    # 7. Test PDF Report Generation
    print("\n[TEST 7] Testing Automated PDF Intelligence Dossier Generation...")
    pdf_bytes = generate_event_pdf_report(
        event_data={
            "event_code": "EVT-TEST-001",
            "state": "Gujarat",
            "latitude": 22.355,
            "longitude": 69.865,
            "detection_count": 5,
            "max_frp": 120.0,
            "avg_frp": 95.0,
            "first_seen": now,
            "last_seen": now,
            "facility_status": "KNOWN",
            "landcover_class": "Industrial",
            "nearest_facility_distance_m": 120.0
        },
        prediction_data={
            "predicted_class": "Gas Flare",
            "confidence": 0.94,
            "explanation_summary": "Continuous flaring pattern within refinery.",
            "shap_values": {"top_contributors": [{"feature": "day_night_ratio", "value": 1.4, "shap_value": 0.35}]}
        },
        risk_data={
            "risk_level": "MODERATE",
            "risk_score": 48.5,
            "risk_reasons": ["Continuous flaring within refinery boundary"]
        }
    )
    assert len(pdf_bytes) > 1000, "PDF byte stream too small"
    assert pdf_bytes.startswith(b"%PDF"), "Invalid PDF binary header"
    print(f"  [OK] PDF Dossier Generator ({len(pdf_bytes)} bytes): PASSED")

    print("\n================================================================")
    print("      ALL ACCEPTANCE TESTS PASSED SUCCESSFULLY! (7/7)           ")
    print("================================================================")


if __name__ == "__main__":
    run_unit_tests()
