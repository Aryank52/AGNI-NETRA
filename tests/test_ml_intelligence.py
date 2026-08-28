import os
import sys
import pytest
import numpy as np
from fastapi.testclient import TestClient

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.database import SessionLocal
from backend.app.main import app
from backend.app.models.domain import User, ThermalEvent, ModelPrediction, VerificationRecord
from backend.app.core.security import create_access_token, get_password_hash
from ml.training.feature_pipeline import (
    FEATURE_COLUMNS, CLASS_NAMES, extract_feature_vector, calculate_prediction_uncertainty
)
from ml.training.train_classifier import train_and_export_models, generate_synthetic_training_data
from ml.training.evaluate import evaluate_saved_models
from ml.inference.predictor import thermal_predictor
from ml.inference.explainer import ShapExplainerWrapper

client = TestClient(app)


def test_feature_pipeline_dimensions_and_uncertainty():
    """Verify feature pipeline outputs exact 18 features and valid uncertainty bounds"""
    event_data = {
        "max_frp": 150.0,
        "avg_frp": 110.0,
        "frp_variance": 25.0,
        "avg_brightness": 355.0,
        "nearest_facility_distance_m": 120.0,
        "landcover_class": "Industrial",
        "persistence_score": 8.0,
        "recurrence_rate": 2.1,
        "day_night_ratio": 1.1,
        "baseline_deviation_ratio": 1.4,
        "industrial_context_score": 0.95
    }
    vec = extract_feature_vector(event_data)
    assert vec.shape == (1, 18)
    assert len(FEATURE_COLUMNS) == 18

    # Uncertainty calculation test
    # 1. Uniform distribution -> Maximum uncertainty ~ 1.0
    uniform_probs = np.full(7, 1.0 / 7.0)
    u_max = calculate_prediction_uncertainty(uniform_probs)
    assert round(u_max, 2) == 1.00

    # 2. Delta distribution -> Minimum uncertainty ~ 0.0
    certain_probs = np.array([1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
    u_min = calculate_prediction_uncertainty(certain_probs)
    assert round(u_min, 4) == 0.0


def test_model_training_and_artifacts():
    """Verify XGBoost, RF benchmark, Isolation Forest training, and metrics serialization"""
    metrics = train_and_export_models(output_dir="ml/models")
    
    assert "evaluation_metrics" in metrics
    assert metrics["evaluation_metrics"]["overall_accuracy"] > 0.85
    assert metrics["evaluation_metrics"]["macro_f1"] > 0.85
    assert metrics["evaluation_metrics"]["cv_5fold_xgb_f1_mean"] > 0.80
    assert metrics["algorithm"] == "XGBOOST"
    assert metrics["benchmark_algorithm"] == "RANDOM_FOREST"
    assert len(metrics["classes"]) == 7

    # Verify saved artifacts exist on disk
    for filename in [
        "xgboost_classifier_v1.joblib",
        "rf_classifier_v1.joblib",
        "isolation_forest_v1.joblib",
        "shap_explainer_v1.joblib",
        "metrics.json",
        "feature_schema.json"
    ]:
        assert os.path.exists(os.path.join("ml/models", filename))


def test_model_evaluation_on_holdout_set():
    """Verify evaluation script runs on holdout test set with classification metrics"""
    eval_result = evaluate_saved_models(models_dir="ml/models")
    assert "primary_model" in eval_result
    assert eval_result["primary_model"]["accuracy"] > 0.85
    assert eval_result["primary_model"]["macro_f1"] > 0.85
    assert "benchmark_comparison" in eval_result


def test_shap_tree_explainer_waterfall():
    """Verify SHAP TreeExplainer produces feature attribution breakdown"""
    pred = thermal_predictor.predict({
        "max_frp": 180.0,
        "avg_frp": 130.0,
        "nearest_facility_distance_m": 150.0,
        "landcover_class": "Industrial",
        "persistence_score": 7.5,
        "day_night_ratio": 1.2,
        "baseline_deviation_ratio": 3.2,
        "industrial_context_score": 0.92
    })

    assert "predicted_class" in pred
    assert "confidence" in pred
    assert "uncertainty" in pred
    assert "shap_values" in pred
    assert "top_contributing_features" in pred
    assert len(pred["top_contributing_features"]) > 0
    assert "anomaly_detection" in pred
    assert "model_version" in pred
    assert "data_sources" in pred


def test_ml_api_endpoints():
    """Verify GET /api/v1/ml/model-info and POST /api/v1/ml/predict"""
    # 1. Model info
    resp_info = client.get("/api/v1/ml/model-info")
    assert resp_info.status_code == 200
    info = resp_info.json()
    assert info["status"] == "OPERATIONAL"
    assert len(info["classes"]) == 7

    # 2. Live prediction endpoint
    resp_pred = client.post("/api/v1/ml/predict", json={
        "max_frp": 120.0,
        "avg_frp": 95.0,
        "frp_variance": 15.0,
        "avg_brightness": 345.0,
        "nearest_facility_distance_m": 150.0,
        "landcover_class": "Industrial",
        "persistence_score": 7.5,
        "recurrence_rate": 1.8,
        "day_night_ratio": 1.2,
        "baseline_deviation_ratio": 1.1,
        "industrial_context_score": 0.92
    })
    assert resp_pred.status_code == 200
    p = resp_pred.json()
    assert "predicted_class" in p
    assert "confidence" in p
    assert "uncertainty" in p
    assert "shap_values" in p


def test_human_verification_system_flow():
    """Verify Human-in-the-Loop (HITL) analyst verification queue and submission"""
    db = SessionLocal()
    try:
        # Fetch or create a test event
        event = db.query(ThermalEvent).first()
        if not event:
            return

        # Fetch verification queue
        resp_q = client.get("/api/v1/verification/queue")
        assert resp_q.status_code == 200

        # Create auth token for analyst
        analyst = db.query(User).filter(User.role == "ANALYST").first()
        if not analyst:
            analyst = db.query(User).first()

        token = create_access_token(subject=str(analyst.id), role=analyst.role)
        headers = {"Authorization": f"Bearer {token}"}

        # Submit verification confirmation
        resp_v = client.post("/api/v1/verification", json={
            "event_id": event.id,
            "verified_label": "Industrial Fire",
            "verification_action": "CONFIRM",
            "notes": "Verified by Automated Pytest Analyst via Sentinel-2 SWIR cross-reference"
        }, headers=headers)
        assert resp_v.status_code == 200
        v_data = resp_v.json()
        assert v_data["event_id"] == event.id
        assert v_data["verification_action"] == "CONFIRM"
    finally:
        db.close()
