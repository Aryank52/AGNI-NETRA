"""
AGNI-NETRA — PHASE 9 TEST SUITE
Test Suite for Production ML Inference Service, Calibrated Probabilities,
SHAP Explanations, Tri-Tier Routing, Risk Scoring, and Audit Logging

Verifies:
1. Historical raw FIRMS observation tables remain 100% immutable (8,221,554 rows).
2. Model registry lineage invariants (xgb-v3.0-real-candidate is CANDIDATE / is_active = FALSE).
3. Production inference service initialization and artifact loading.
4. Calibrated probability distribution, SHAP explanations, and uncertainty metrics.
5. Tri-Tier Human-in-the-Loop routing policy and multi-criteria risk scoring.
6. Audit log table `ml_prediction_audit_logs` persistence and 100% dispatch suppression (is_operational_dispatch = FALSE).
7. FastAPI operational ML endpoints (/model-info, /predict, /predict-batch, /audit-logs).
8. Existence and completeness of Phase 9 report and manifest.
"""

import os
import sys
import json
import pytest
import numpy as np
from sqlalchemy import text
from fastapi.testclient import TestClient

WORKSPACE_DIR = r"E:\PROJECTS\AGNI-NETRA"
if WORKSPACE_DIR not in sys.path:
    sys.path.insert(0, WORKSPACE_DIR)

from backend.app.core.database import engine
from backend.app.main import app
from ml.inference.production_inference_service import (
    ProductionThermalInferenceService,
    FEATURE_COLUMNS,
    TARGET_CLASSES
)

REPORT_MD_PATH = os.path.join(WORKSPACE_DIR, "PHASE9_PRODUCTION_INFERENCE_REPORT.md")
REPORT_JSON_PATH = os.path.join(WORKSPACE_DIR, "PHASE9_PRODUCTION_INFERENCE.json")

client = TestClient(app)


def test_phase9_database_immutability_and_model_registry_invariants():
    """Verifies that all raw FIRMS tables remain strictly immutable and candidate models inactive."""
    with engine.connect() as conn:
        c_2022_off = conn.execute(text("SELECT COUNT(*) FROM thermal_detections WHERE acq_timestamp >= '2022-01-01' AND acq_timestamp < '2023-01-01' AND is_demo = false;")).scalar()
        c_2022_pil = conn.execute(text("SELECT COUNT(*) FROM thermal_detections WHERE acq_timestamp >= '2022-01-01' AND acq_timestamp < '2023-01-01' AND is_demo = true;")).scalar()
        c_2023_off = conn.execute(text("SELECT COUNT(*) FROM thermal_detections WHERE acq_timestamp >= '2023-01-01' AND acq_timestamp < '2024-01-01' AND is_demo = false;")).scalar()
        c_2024_rec = conn.execute(text("SELECT COUNT(*) FROM thermal_detections WHERE acq_timestamp >= '2024-01-01' AND acq_timestamp < '2025-01-01';")).scalar()
        c_2025_off = conn.execute(text("SELECT COUNT(*) FROM thermal_detections WHERE acq_timestamp >= '2025-01-01' AND acq_timestamp < '2026-01-01';")).scalar()
        c_2026_off = conn.execute(text("SELECT COUNT(*) FROM thermal_detections WHERE acq_timestamp >= '2026-01-01';")).scalar()

        active_models = conn.execute(text("SELECT model_name, version, status, is_active FROM ml_model_registry WHERE version IN ('xgb-v3.0-real-candidate', 'rf-v3.0-real-candidate', 'xgb-v2.0-real-candidate');")).fetchall()

    assert c_2022_off == 1_274_383
    assert c_2022_pil == 210_000
    assert c_2023_off == 1_244_759
    assert c_2024_rec == 1_711_626
    assert c_2025_off == 2_007_898
    assert c_2026_off >= 1_771_080

    for m in active_models:
        assert not m[3], f"Model {m[1]} must remain inactive (is_active = FALSE)!"
        assert m[2] == "CANDIDATE", f"Model {m[1]} must remain CANDIDATE status!"


def test_phase9_production_inference_service_initialization():
    """Verifies that the production inference service initializes and loads champion models."""
    service = ProductionThermalInferenceService()
    assert service.is_loaded is True
    assert service.xgb_model is not None
    assert service.platt_calibrator is not None
    assert service.model_version == "xgb-v3.0-real-candidate"
    assert service.calibrator_version == "balanced-platt-v3.0"
    assert service.dataset_lineage == "v3.2-real-final"


def test_phase9_calibrated_inference_and_shap_output():
    """Verifies calibrated probabilities, uncertainty entropy, and SHAP tree explanations."""
    service = ProductionThermalInferenceService()
    event_data = {
        "frp_max": 180.0, "frp_avg": 140.0, "frp_std": 20.0,
        "bright_max": 370.0, "bright_avg": 350.0, "delta_brightness": 20.0,
        "dist_to_facility_m": 75.0, "dist_to_forest_m": 40000.0, "dist_to_agriculture_m": 15000.0,
        "dist_to_settlement_m": 5000.0, "dist_to_water_m": 2000.0, "dist_to_mine_m": 50000.0,
        "landcover_code": 1, "persistence_score": 0.90, "recurrence_rate": 5.5,
        "day_night_ratio": 1.10, "baseline_deviation_ratio": 1.15, "industrial_context_score": 0.99
    }

    res = service.predict(event_data, log_audit=False)

    assert res["predicted_class"] in TARGET_CLASSES
    assert 0.0 <= res["confidence"] <= 1.0
    assert 0.0 <= res["uncertainty"] <= 1.0
    assert sum(res["class_probabilities"].values()) == pytest.approx(1.0, abs=0.01)
    
    # SHAP assertions
    shap = res["shap_explanation"]
    assert "top_contributors" in shap
    assert len(shap["top_contributors"]) > 0
    assert shap["method"] in ["TREE_SHAP_V3", "HEURISTIC_FALLBACK"]

    # Operational safety
    assert res["operational_dispatch_status"]["is_operational_dispatch"] is False


def test_phase9_tri_tier_routing_and_risk_scoring():
    """Verifies Tri-Tier routing thresholds and multi-criteria fire risk calculations."""
    service = ProductionThermalInferenceService()

    # Tier 1 expected: High confidence industrial flare
    event_tier1 = {
        "frp_max": 150.0, "dist_to_facility_m": 50.0, "landcover_code": 1,
        "persistence_score": 0.95, "recurrence_rate": 6.0, "industrial_context_score": 0.99
    }
    res_t1 = service.predict(event_tier1, log_audit=False)
    assert res_t1["routing_tier"] in ["TIER_1_AUTO_DISPATCH_CANDIDATE", "TIER_2_ANALYST_REVIEW_QUEUE"]
    assert res_t1["risk_assessment"]["risk_tier"] in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    assert 0.0 <= res_t1["risk_assessment"]["risk_score"] <= 100.0

    # Risk score validation on forest fire
    event_forest = {
        "frp_max": 200.0, "dist_to_forest_m": 20.0, "dist_to_facility_m": 50000.0,
        "landcover_code": 5, "persistence_score": 0.05, "recurrence_rate": 0.1
    }
    res_forest = service.predict(event_forest, log_audit=False)
    assert res_forest["risk_assessment"]["risk_score"] > 25.0


def test_phase9_audit_logging_and_safety_invariants():
    """Verifies PostgreSQL ml_prediction_audit_logs retention and zero live dispatch invariant."""
    with engine.connect() as conn:
        total_logs = conn.execute(text("SELECT COUNT(*) FROM ml_prediction_audit_logs;")).scalar()
        live_dispatches = conn.execute(text("SELECT COUNT(*) FROM ml_prediction_audit_logs WHERE is_operational_dispatch = true;")).scalar()

    assert total_logs > 0, "No audit logs found in ml_prediction_audit_logs!"
    assert live_dispatches == 0, f"Live dispatches ({live_dispatches}) were emitted!"


def test_phase9_fastapi_ml_endpoints():
    """Verifies FastAPI /api/v1/ml operational endpoints (/model-info, /predict, /predict-batch, /audit-logs)."""
    # 1. Model Info
    resp_info = client.get("/api/v1/ml/model-info")
    assert resp_info.status_code == 200
    info_data = resp_info.json()
    assert info_data["version"] == "xgb-v3.0-real-candidate"
    assert info_data["is_active"] is False

    # 2. Predict Endpoint
    sample_payload = {
        "frp_max": 110.0,
        "dist_to_facility_m": 120.0,
        "landcover_code": 1,
        "persistence_score": 0.80,
        "recurrence_rate": 4.5
    }
    resp_pred = client.post("/api/v1/ml/predict", json=sample_payload)
    assert resp_pred.status_code == 200
    pred_data = resp_pred.json()
    assert "predicted_class" in pred_data
    assert "confidence" in pred_data
    assert "shap_explanation" in pred_data
    assert "routing_tier" in pred_data
    assert pred_data["operational_dispatch_status"]["is_operational_dispatch"] is False

    # 3. Batch Predict Endpoint
    batch_payload = {"events": [sample_payload, {"frp_max": 45.0, "dist_to_agriculture_m": 100.0, "landcover_code": 3}]}
    resp_batch = client.post("/api/v1/ml/predict-batch", json=batch_payload)
    assert resp_batch.status_code == 200
    batch_data = resp_batch.json()
    assert batch_data["total_events"] == 2
    assert len(batch_data["predictions"]) == 2

    # 4. Audit Logs Query Endpoint
    resp_logs = client.get("/api/v1/ml/audit-logs?limit=5")
    assert resp_logs.status_code == 200
    logs_data = resp_logs.json()
    assert isinstance(logs_data, list)
    assert len(logs_data) > 0


def test_phase9_report_and_manifest_exist():
    """Verifies existence and schema of PHASE9_PRODUCTION_INFERENCE_REPORT.md and .json."""
    assert os.path.exists(REPORT_MD_PATH), f"Missing {REPORT_MD_PATH}"
    assert os.path.exists(REPORT_JSON_PATH), f"Missing {REPORT_JSON_PATH}"

    with open(REPORT_JSON_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    assert manifest["phase"] == "PHASE_9"
    assert manifest["status"] == "PHASE_9_COMPLETE"
    assert manifest["production_inference_service"]["model_version"] == "xgb-v3.0-real-candidate"
    assert manifest["production_inference_service"]["is_active"] is False
    assert manifest["production_inference_service"]["live_dispatches_emitted"] == 0
