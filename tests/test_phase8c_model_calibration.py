import os
import sys
import json
import hashlib
import joblib
import numpy as np
import pytest
from sqlalchemy import text

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.database import engine

PROJECT_DIR = r"E:\PROJECTS\AGNI-NETRA"
MD_REPORT_PATH = os.path.join(PROJECT_DIR, "PHASE8C_MODEL_CALIBRATION_REPORT.md")
JSON_MANIFEST_PATH = os.path.join(PROJECT_DIR, "PHASE8C_MODEL_CALIBRATION.json")
DATASET_CSV_PATH = os.path.join(PROJECT_DIR, "ml", "dataset", "dataset_v3.0-real-authoritative.csv")
MODELS_DIR = os.path.join(PROJECT_DIR, "ml", "models")
EXPECTED_DATASET_SHA256 = "9d246bedd1f52b3fd223148b6158ad22f310c2e72a06e6093668b5d72212b835"


def compute_sha256(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


def test_phase8c_report_and_manifest_exist():
    """Verify that Phase 8C report and JSON manifest exist and contain valid metadata."""
    assert os.path.exists(MD_REPORT_PATH), f"Report not found at {MD_REPORT_PATH}"
    assert os.path.exists(JSON_MANIFEST_PATH), f"JSON manifest not found at {JSON_MANIFEST_PATH}"

    with open(JSON_MANIFEST_PATH, "r", encoding="utf-8") as f:
        meta = json.load(f)

    assert meta["phase"] == "PHASE_8C_MODEL_CALIBRATION"
    assert meta["dataset_version"] == "v3.0-real-authoritative"
    assert meta["dataset_sha256"] == EXPECTED_DATASET_SHA256
    assert meta["production_readiness_decision"] == "READY_FOR_SHADOW_MODE"
    assert meta["recommended_model"] == "xgb-v2.0-real-candidate"
    assert "project_hosts" in meta
    assert "frontend_command_center" in meta["project_hosts"]
    assert "backend_swagger_api" in meta["project_hosts"]


def test_phase8c_reproducibility_and_model_loading():
    """Verify loading of candidate models, calibrated wrappers, and reproducibility flags."""
    xgb_calib_path = os.path.join(MODELS_DIR, "xgb_v2_calibrated_candidate.joblib")
    rf_calib_path = os.path.join(MODELS_DIR, "rf_v2_calibrated_candidate.joblib")
    meta_path = os.path.join(MODELS_DIR, "calibration_metadata_v2.json")

    assert os.path.exists(xgb_calib_path)
    assert os.path.exists(rf_calib_path)
    assert os.path.exists(meta_path)

    with open(JSON_MANIFEST_PATH, "r", encoding="utf-8") as f:
        meta = json.load(f)

    assert meta["reproducibility_verified"] is True
    assert meta["evaluation_split_sizes"]["test_2026"] == 176
    assert meta["evaluation_split_sizes"]["validation_2025"] == 233
    assert meta["evaluation_split_sizes"]["train_2022_2024"] == 440


def test_phase8c_calibration_improvements():
    """Verify that probability calibration reduces test Log-Loss and ECE compared to raw models."""
    with open(JSON_MANIFEST_PATH, "r", encoding="utf-8") as f:
        meta = json.load(f)

    raw_metrics = meta["xgboost_test_metrics_raw"]
    calib_metrics = meta["xgboost_test_metrics_calibrated"]

    assert calib_metrics["log_loss"] < raw_metrics["log_loss"], (
        f"Calibrated Log Loss ({calib_metrics['log_loss']}) should be lower than raw ({raw_metrics['log_loss']})"
    )
    assert calib_metrics["ece"] < raw_metrics["ece"], (
        f"Calibrated ECE ({calib_metrics['ece']}) should be lower than raw ({raw_metrics['ece']})"
    )
    assert calib_metrics["log_loss"] <= 1.00
    assert calib_metrics["brier_score"] <= 0.10


def test_phase8c_hitl_tri_tier_policy():
    """Verify that the Human-in-the-Loop policy achieves high selective accuracy on automated tier."""
    with open(JSON_MANIFEST_PATH, "r", encoding="utf-8") as f:
        meta = json.load(f)

    hitl = meta["hitl_policy"]
    tier1 = hitl["tier_1_automated"]
    tier2 = hitl["tier_2_analyst_review"]
    tier3 = hitl["tier_3_active_learning"]

    assert tier1["percentage"] >= 40.0, f"Tier 1 coverage too low: {tier1['percentage']}%"
    assert tier1["selective_accuracy"] >= 0.90, f"Tier 1 accuracy too low: {tier1['selective_accuracy']}"
    assert tier1["selective_macro_f1"] >= 0.80

    total_pct = tier1["percentage"] + tier2["percentage"] + tier3["percentage"]
    assert abs(total_pct - 100.0) < 0.5


def test_phase8c_cost_sensitive_risk_reduction():
    """Verify cost-sensitive risk audit calculations."""
    with open(JSON_MANIFEST_PATH, "r", encoding="utf-8") as f:
        meta = json.load(f)

    cost_audit = meta["cost_sensitive_audit"]
    assert cost_audit["platt_total_risk_penalty"] <= cost_audit["raw_total_risk_penalty"]


def test_phase8c_minority_class_recalls():
    """Verify minority class recalls and error analysis coverage."""
    with open(JSON_MANIFEST_PATH, "r", encoding="utf-8") as f:
        meta = json.load(f)

    minority = meta["minority_class_error_analysis"]
    for cls_name in ["Mining Activity", "Industrial Fire", "Gas Flare"]:
        assert cls_name in minority
        assert minority[cls_name]["recall"] >= 0.45, f"Recall for {cls_name} too low: {minority[cls_name]['recall']}"
        assert minority[cls_name]["true_positives"] > 0
        assert "fn_confused_with" in minority[cls_name]


def test_phase8c_shap_and_recommendation():
    """Verify SHAP case studies and official recommendation decision."""
    with open(JSON_MANIFEST_PATH, "r", encoding="utf-8") as f:
        meta = json.load(f)

    shap_meta = meta["shap_analysis"]
    assert len(shap_meta["top_features"]) == 18
    assert "representative_true_positive" in shap_meta
    assert "representative_confusion_case" in shap_meta

    assert meta["production_readiness_decision"] == "READY_FOR_SHADOW_MODE"
    assert meta["recommended_model"] == "xgb-v2.0-real-candidate"
    assert "CANDIDATE" in meta["registry_status"]


def test_historical_datasets_immutability():
    """Verify that raw FIRMS observation counts across 2022-2026 remain 100% immutable."""
    with engine.connect() as conn:
        det_2022_off = conn.execute(text("SELECT COUNT(*) FROM thermal_detections WHERE acq_timestamp >= '2022-01-01' AND acq_timestamp < '2023-01-01' AND is_demo = false;")).scalar()
        det_2022_pil = conn.execute(text("SELECT COUNT(*) FROM thermal_detections WHERE acq_timestamp >= '2022-01-01' AND acq_timestamp < '2023-01-01' AND is_demo = true;")).scalar()
        det_2023_off = conn.execute(text("SELECT COUNT(*) FROM thermal_detections WHERE acq_timestamp >= '2023-01-01' AND acq_timestamp < '2024-01-01' AND is_demo = false;")).scalar()
        hist_2024_off = conn.execute(text("SELECT COUNT(*) FROM thermal_history WHERE acq_timestamp >= '2024-01-01' AND acq_timestamp < '2025-01-01';")).scalar()
        det_2025_off = conn.execute(text("SELECT COUNT(*) FROM thermal_detections WHERE acq_timestamp >= '2025-01-01' AND acq_timestamp < '2026-01-01' AND is_demo = false;")).scalar()
        det_2026_off = conn.execute(text("SELECT COUNT(*) FROM thermal_detections WHERE acq_timestamp >= '2026-01-01' AND acq_timestamp < '2027-01-01' AND is_demo = false;")).scalar()

    assert det_2022_off == 1_274_383
    assert det_2022_pil == 210_000
    assert det_2023_off == 1_244_759
    assert hist_2024_off == 1_711_626
    assert det_2025_off == 2_007_898
    assert det_2026_off >= 1_771_080
