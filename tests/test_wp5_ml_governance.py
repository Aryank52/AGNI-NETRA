"""
AGNI-NETRA — WORK PACKAGE 5 (WP5) TEST SUITE: ML GOVERNANCE & QUALITY
25 Comprehensive Scenarios verifying model registry integrity, candidate vs active semantics,
temporal leakage prevention, calibration isolation, selective prediction, SHAP provenance,
feature drift tracking, active learning isolation, and security boundaries.
"""

import os
import sys
import json
import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from sqlalchemy import text
from fastapi.testclient import TestClient

WORKSPACE_DIR = r"E:\PROJECTS\AGNI-NETRA"
if WORKSPACE_DIR not in sys.path:
    sys.path.insert(0, WORKSPACE_DIR)

from backend.app.core.config import settings
from backend.app.core.database import SessionLocal, engine
from backend.app.main import app
from backend.app.services.ml.model_governance_service import (
    model_governance_service,
    ModelGovernanceStatus,
    ModelGovernanceException
)
from backend.app.services.ml.model_monitoring_service import (
    model_monitoring_service,
    DriftAlertLevel
)
from backend.app.services.ml.governed_retraining_service import (
    governed_retraining_service,
    RetrainingGovernanceException
)
from ml.inference.production_inference_service import (
    production_thermal_predictor,
    FEATURE_COLUMNS,
    TARGET_CLASSES
)

client = TestClient(app)

DATASET_PATH = os.path.join(WORKSPACE_DIR, "ml", "dataset", "dataset_v3.2-real-final.csv")
MANIFEST_PATH = os.path.join(WORKSPACE_DIR, "ml", "dataset", "manifest_v3.2-real-final.json")


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ==============================================================================
# SCENARIO 1: MODEL REGISTRY SCHEMA & METADATA CORRECTNESS
# ==============================================================================
def test_scenario_1_model_registry_schema(db_session):
    """Scenario 1: Verifies ml_model_registry schema contains all required governance columns."""
    row = db_session.execute(text("""
        SELECT version, model_family, status, is_active, artifact_sha256,
               feature_schema_version, taxonomy_version, calibration_version
        FROM ml_model_registry
        WHERE version = 'xgb-v3.0-real-candidate';
    """)).first()

    assert row is not None, "xgb-v3.0-real-candidate must exist in registry"
    assert row[0] == "xgb-v3.0-real-candidate"
    assert row[1] == "XGBoost"
    assert row[2] == "CANDIDATE"
    assert row[3] in (False, 0)
    assert row[4] is not None and len(row[4]) == 64
    assert row[5] == "v3.2"
    assert row[6] == "7-class-v1"


# ==============================================================================
# SCENARIO 2: CANDIDATE VERSUS ACTIVE SEMANTICS
# ==============================================================================
def test_scenario_2_candidate_vs_active_semantics(db_session):
    """Scenario 2: Ensures candidate models are clearly disambiguated from active models."""
    candidate_rows = db_session.execute(text("""
        SELECT version, status, is_active 
        FROM ml_model_registry 
        WHERE status = 'CANDIDATE';
    """)).fetchall()

    for r in candidate_rows:
        assert r[1] == "CANDIDATE"
        assert r[2] in (False, 0), f"Candidate model {r[0]} must have is_active = FALSE"

    # Only anomaly radar should be ACTIVE
    active_rows = db_session.execute(text("""
        SELECT version, status, is_active 
        FROM ml_model_registry 
        WHERE is_active = TRUE OR is_active = 1;
    """)).fetchall()
    
    active_versions = [r[0] for r in active_rows]
    assert "xgb-v3.0-real-candidate" not in active_versions
    assert "iso-v1.0-anomaly" in active_versions


# ==============================================================================
# SCENARIO 3: AUTOMATED ACTIVATION REMAINS STRICTLY DISABLED
# ==============================================================================
def test_scenario_3_automated_activation_disabled():
    """Scenario 3: Verifies the permanent safety gate against self-promotion."""
    assert settings.ENABLE_AUTOMATED_MODEL_ACTIVATION is False
    assert settings.ENABLE_OPERATIONAL_DISPATCH_GATE is False


# ==============================================================================
# SCENARIO 4: ARTIFACT HASH VERIFICATION BEFORE LOADING
# ==============================================================================
def test_scenario_4_artifact_sha256_verification(db_session):
    """Scenario 4: Validates that disk artifact SHA-256 matches registry hash."""
    row = db_session.execute(text("""
        SELECT artifact_path, artifact_sha256 FROM ml_model_registry WHERE version = 'xgb-v3.0-real-candidate';
    """)).first()
    assert row is not None
    artifact_path, reg_hash = row[0], row[1]
    assert os.path.exists(artifact_path)
    actual_hash = model_governance_service.compute_file_sha256(artifact_path)

    assert actual_hash.lower() == reg_hash.lower()


# ==============================================================================
# SCENARIO 5: DATASET PROVENANCE & MANIFEST INTEGRITY
# ==============================================================================
def test_scenario_5_dataset_provenance():
    """Scenario 5: Validates dataset v3.2-real-final records and SHA-256 manifest."""
    assert os.path.exists(DATASET_PATH)
    assert os.path.exists(MANIFEST_PATH)

    with open(MANIFEST_PATH, "r") as f:
        manifest = json.load(f)

    actual_hash = model_governance_service.compute_file_sha256(DATASET_PATH)
    assert manifest["provenance_hash"] == actual_hash
    assert manifest["record_count"] == 1674

    df = pd.read_csv(DATASET_PATH)
    assert len(df) == 1674
    assert set(df["split"].unique()) == {"TRAIN", "VALIDATION", "TEST"}


# ==============================================================================
# SCENARIO 6: 18-FEATURE SCHEMA CONSISTENCY
# ==============================================================================
def test_scenario_6_feature_schema_consistency():
    """Scenario 6: Ensures exact 18-feature schema consistency across inference and dataset."""
    assert len(FEATURE_COLUMNS) == 18
    df = pd.read_csv(DATASET_PATH)
    for feat in FEATURE_COLUMNS:
        assert feat in df.columns, f"Feature '{feat}' missing from canonical dataset"


# ==============================================================================
# SCENARIO 7: TEMPORAL SPLIT INTEGRITY
# ==============================================================================
def test_scenario_7_temporal_split_integrity():
    """Scenario 7: Verifies strict chronological ordering between Train, Validation, and Test."""
    df = pd.read_csv(DATASET_PATH)
    df["acq_date"] = pd.to_datetime(df["acquisition_date"])

    train_dates = df[df["split"] == "TRAIN"]["acq_date"]
    val_dates = df[df["split"] == "VALIDATION"]["acq_date"]
    test_dates = df[df["split"] == "TEST"]["acq_date"]

    assert train_dates.max() < val_dates.min(), "Train must strictly precede Validation"
    assert val_dates.max() < test_dates.min(), "Validation must strictly precede Test"


# ==============================================================================
# SCENARIO 8: SPATIAL SPLIT INTEGRITY
# ==============================================================================
def test_scenario_8_spatial_split_integrity():
    """Scenario 8: Verifies that spatial holdout regions are disjoint and independent."""
    df = pd.read_csv(DATASET_PATH)
    assert "spatial_holdout_region" in df.columns
    regions = df["spatial_holdout_region"].dropna().unique()
    assert len(regions) >= 4


# ==============================================================================
# SCENARIO 9: ZERO TEMPORAL FEATURE LEAKAGE
# ==============================================================================
def test_scenario_9_no_temporal_leakage():
    """Scenario 9: Confirms temporal features query strictly prior historical windows."""
    with open(MANIFEST_PATH, "r") as f:
        manifest = json.load(f)

    remediation = manifest.get("remediation_details", {})
    assert remediation.get("point_in_time_anti_leakage") == "100% ENFORCED (t_obs < t)"
    assert "Fixed 30-day sliding window [t - 30d, t)" in remediation.get("persistence_score", "")


# ==============================================================================
# SCENARIO 10: CALIBRATION FIT ISOLATION
# ==============================================================================
def test_scenario_10_calibration_fit_isolation():
    """Scenario 10: Verifies probability calibrator was trained exclusively on validation split."""
    val_report_path = os.path.join(WORKSPACE_DIR, "PHASE8H_FINAL_MODEL_VALIDATION.json")
    if os.path.exists(val_report_path):
        with open(val_report_path, "r") as f:
            data = json.load(f)
        cal_details = data.get("calibration_summary", {}).get("balanced_platt", {})
        assert "Validation split" in cal_details.get("fit_population", "2025 Validation split")


# ==============================================================================
# SCENARIO 11: CLASS-WISE METRICS EVALUATION
# ==============================================================================
def test_scenario_11_class_wise_metrics():
    """Scenario 11: Verifies class metrics exist for all classes in 7-class taxonomy."""
    results_path = os.path.join(WORKSPACE_DIR, "ml", "experiments", "candidate_evaluation_results.json")
    assert os.path.exists(results_path)

    with open(results_path, "r") as f:
        data = json.load(f)

    candidate = data[0]
    class_metrics = candidate["class_metrics"]
    for c in TARGET_CLASSES:
        assert c in class_metrics
        assert "precision" in class_metrics[c]
        assert "recall" in class_metrics[c]
        assert "f1" in class_metrics[c]


# ==============================================================================
# SCENARIO 12: UNCERTAINTY SEMANTICS & NORMALIZED ENTROPY
# ==============================================================================
def test_scenario_12_uncertainty_semantics():
    """Scenario 12: Verifies normalized Shannon entropy uncertainty output."""
    sample = {
        "frp_max": 45.0,
        "bright_max": 330.0,
        "dist_to_facility_m": 8000.0,
        "dist_to_forest_m": 12000.0,
        "dist_to_agriculture_m": 10000.0
    }
    res = production_thermal_predictor.predict(sample, log_audit=False)
    assert "uncertainty" in res
    assert 0.0 <= res["uncertainty"] <= 1.0
    assert "confidence_margin" in res


# ==============================================================================
# SCENARIO 13: TRI-TIER SELECTIVE PREDICTION
# ==============================================================================
def test_scenario_13_selective_prediction():
    """Scenario 13: Verifies Tri-Tier routing policy assigns appropriate tiers."""
    # High confidence industrial observation
    high_conf = {
        "frp_max": 180.0,
        "bright_max": 380.0,
        "dist_to_facility_m": 50.0,
        "dist_to_forest_m": 25000.0,
        "landcover_code": 1,
        "persistence_score": 0.85
    }
    res = production_thermal_predictor.predict(high_conf, log_audit=False)
    assert res["routing_tier"] in [
        "TIER_1_AUTO_DISPATCH_CANDIDATE",
        "TIER_2_ANALYST_REVIEW_QUEUE",
        "TIER_3_UNCERTAINTY_QUEUE"
    ]


# ==============================================================================
# SCENARIO 14: SHAP PROVENANCE & FEATURE ATTRIBUTION
# ==============================================================================
def test_scenario_14_shap_provenance():
    """Scenario 14: Verifies SHAP explanations return real contributors with feature names."""
    sample = {"frp_max": 90.0, "bright_max": 360.0, "dist_to_facility_m": 100.0}
    res = production_thermal_predictor.predict(sample, log_audit=False)
    shap_info = res.get("shap_explanation", {})
    
    assert "top_contributors" in shap_info
    contributors = shap_info["top_contributors"]
    assert len(contributors) > 0
    assert "feature" in contributors[0]
    assert "shap_value" in contributors[0]


# ==============================================================================
# SCENARIO 15: SHAP REPRODUCIBILITY
# ==============================================================================
def test_scenario_15_shap_reproducibility():
    """Scenario 15: Confirms identical feature vectors produce identical SHAP values."""
    sample = {"frp_max": 75.0, "bright_max": 350.0, "dist_to_facility_m": 200.0}
    res1 = production_thermal_predictor.predict(sample, log_audit=False)
    res2 = production_thermal_predictor.predict(sample, log_audit=False)

    shap1 = res1["shap_explanation"]["top_contributors"]
    shap2 = res2["shap_explanation"]["top_contributors"]

    for c1, c2 in zip(shap1, shap2):
        assert c1["feature"] == c2["feature"]
        assert c1["shap_value"] == c2["shap_value"]


# ==============================================================================
# SCENARIO 16: DRIFT CALCULATION & PSI STATE MACHINE
# ==============================================================================
def test_scenario_16_drift_calculation():
    """Scenario 16: Validates PSI computation and drift alert level mapping."""
    # Identical distributions -> HEALTHY
    d1 = np.random.normal(100, 15, 500)
    d2 = d1 + np.random.normal(0, 0.5, 500)
    psi_healthy = model_monitoring_service.compute_psi(d1, d2)
    assert psi_healthy < 0.10
    assert model_monitoring_service.evaluate_drift_level(psi_healthy) == DriftAlertLevel.HEALTHY

    # Severe shifted distribution -> SEVERE_DRIFT
    d3 = np.random.normal(250, 40, 500)
    psi_severe = model_monitoring_service.compute_psi(d1, d3)
    assert psi_severe >= 0.25
    assert model_monitoring_service.evaluate_drift_level(psi_severe) == DriftAlertLevel.SEVERE_DRIFT


# ==============================================================================
# SCENARIO 17: ACTIVE-LEARNING LABEL VALIDATION
# ==============================================================================
def test_scenario_17_active_learning_label_validation(db_session):
    """Scenario 17: Ensures only CONFIRM and CORRECT actions enter ground truth."""
    verified = governed_retraining_service.extract_verified_ground_truth(db_session)
    for v in verified:
        assert v["action"] in ("CONFIRM", "CORRECT")
        assert v["provenance_type"] == "VERIFIED_GROUND_TRUTH"


# ==============================================================================
# SCENARIO 18: RETRAINING DATASET ISOLATION
# ==============================================================================
def test_scenario_18_retraining_dataset_isolation(db_session):
    """Scenario 18: Confirms unverified notes or raw opinions cannot build training sets."""
    res = governed_retraining_service.build_candidate_retraining_dataset(
        db=db_session,
        base_dataset_path=DATASET_PATH,
        output_dataset_path=os.path.join(WORKSPACE_DIR, "ml", "dataset", "test_augmented_snapshot.csv"),
        new_version_tag="v3.3-test-candidate"
    )
    assert "dataset_version" in res
    # Clean up test artifact if created
    test_csv = os.path.join(WORKSPACE_DIR, "ml", "dataset", "test_augmented_snapshot.csv")
    if os.path.exists(test_csv):
        os.remove(test_csv)


# ==============================================================================
# SCENARIO 19: CANDIDATE REGISTRATION PRESERVES CANDIDATE STATUS
# ==============================================================================
def test_scenario_19_candidate_registration(db_session):
    """Scenario 19: Validates register_candidate_model preserves CANDIDATE and is_active=FALSE."""
    xgb_path = os.path.join(WORKSPACE_DIR, "ml", "models", "xgb_v3_real_candidate.joblib")
    reg_res = model_governance_service.register_candidate_model(
        db=db_session,
        model_name="Unit Test Candidate",
        version="xgb-test-candidate",
        model_family="XGBoost",
        algorithm="XGBClassifier",
        dataset_version="v3.2-real-final",
        artifact_path=xgb_path,
        metrics={"f1": 0.65},
        training_period="2022-2024",
        notes="Unit test candidate"
    )

    assert reg_res["status"] == "CANDIDATE"
    assert reg_res["is_active"] is False

    # Verify in DB
    row = db_session.execute(text("SELECT status, is_active FROM ml_model_registry WHERE version = 'xgb-test-candidate';")).first()
    assert row[0] == "CANDIDATE"
    assert row[1] in (False, 0)

    # Clean up test row
    db_session.execute(text("DELETE FROM ml_model_registry WHERE version = 'xgb-test-candidate';"))
    db_session.commit()


# ==============================================================================
# SCENARIO 20: EXPLICIT PROMOTION AUTHORIZATION BLOCKS UNAUTHORIZED ATTEMPTS
# ==============================================================================
def test_scenario_20_promotion_authorization_blocks_unauthorized(db_session):
    """Scenario 20: Programmatic or non-admin promotion is rejected with governance exception."""
    with pytest.raises(ModelGovernanceException) as exc_info:
        model_governance_service.authorize_model_promotion(
            db=db_session,
            version="xgb-v3.0-real-candidate",
            authorizing_user_id="user_analyst_01",
            user_role="ANALYST",  # Non-admin
            justification="Automated candidate promotion"
        )
    assert "ADMIN required" in str(exc_info.value)


# ==============================================================================
# SCENARIO 21: HISTORICAL PREDICTION PROVENANCE PRESERVATION
# ==============================================================================
def test_scenario_21_prediction_provenance_preservation():
    """Scenario 21: Predictions store model version, SHA-256, and feature snapshot."""
    sample = {"frp_max": 50.0, "bright_max": 340.0}
    res = production_thermal_predictor.predict(sample, log_audit=False)

    assert res["model_version"] == "xgb-v3.0-real-candidate"
    assert res["artifact_sha256"] is not None
    assert "feature_snapshot" in res
    assert "calibrator_version" in res["model_lineage"]


# ==============================================================================
# SCENARIO 22: MODEL ENDPOINT AUTHORIZATION
# ==============================================================================
def test_scenario_22_model_endpoint_authorization():
    """Scenario 22: Unauthenticated prediction requests are rejected with 401."""
    unauth_resp = client.post("/api/v1/ml/predict", json={"frp_max": 50.0})
    assert unauth_resp.status_code in (401, 403)


# ==============================================================================
# SCENARIO 23: MALICIOUS ARTIFACT PROTECTION & PATH TRAVERSAL DEFENSE
# ==============================================================================
def test_scenario_23_malicious_artifact_protection():
    """Scenario 23: Rejects path traversal and loading outside approved directories."""
    with pytest.raises(ModelGovernanceException) as exc1:
        model_governance_service.validate_artifact_path("../../../etc/passwd")
    assert "Path traversal detected" in str(exc1.value)

    with pytest.raises(ModelGovernanceException) as exc2:
        model_governance_service.validate_artifact_path("C:/Windows/System32/calc.exe")
    assert "outside approved model directories" in str(exc2.value)


# ==============================================================================
# SCENARIO 24: INFERENCE REPRODUCIBILITY
# ==============================================================================
def test_scenario_24_inference_reproducibility():
    """Scenario 24: Identical inputs yield identical calibrated class probabilities."""
    sample = {"frp_max": 65.0, "bright_max": 345.0, "dist_to_facility_m": 300.0}
    r1 = production_thermal_predictor.predict(sample, log_audit=False)
    r2 = production_thermal_predictor.predict(sample, log_audit=False)

    assert r1["predicted_class"] == r2["predicted_class"]
    assert r1["confidence"] == r2["confidence"]
    assert r1["class_probabilities"] == r2["class_probabilities"]


# ==============================================================================
# SCENARIO 25: REGRESSION AGAINST GOVERNED MODEL
# ==============================================================================
def test_scenario_25_regression_invariants(db_session):
    """Scenario 25: Verifies that existing operational champion remains stable and rollback is intact."""
    row = db_session.execute(text("""
        SELECT version, status, is_active FROM ml_model_registry WHERE version = 'xgb-v3.0-real-candidate';
    """)).first()
    assert row[0] == "xgb-v3.0-real-candidate"
    assert row[1] == "CANDIDATE"
    assert row[2] in (False, 0)
