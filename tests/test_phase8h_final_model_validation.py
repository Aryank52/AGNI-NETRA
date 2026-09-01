"""
AGNI-NETRA — PHASE 8H TEST SUITE
Test Suite for Final Point-in-Time Model Retraining, Calibration & Validation

Verifies:
1. Historical raw FIRMS observation tables remain 100% immutable (8,221,554 rows).
2. v3.2-real-final dataset integrity, checksum verification, and PostgreSQL registration.
3. Existence and validity of trained v3.0 model artifacts and calibration wrappers.
4. Frozen 2026 test evaluation acceptance gates (Balanced Accuracy >= 70%, Log-Loss < 0.75, Tier 1 Accuracy >= 95%).
5. Model registry lineage invariants (xgb-v3.0-real-candidate is CANDIDATE / is_active = FALSE).
6. Existence and completeness of Phase 8H validation report and JSON manifest.
"""

import os
import sys
import json
import hashlib
import joblib
import pytest
import numpy as np
import pandas as pd
from sqlalchemy import text

WORKSPACE_DIR = r"E:\PROJECTS\AGNI-NETRA"
if WORKSPACE_DIR not in sys.path:
    sys.path.insert(0, WORKSPACE_DIR)

from backend.app.core.database import engine

DATASET_V32_CSV = os.path.join(WORKSPACE_DIR, "ml", "dataset", "dataset_v3.2-real-final.csv")
MANIFEST_V32_JSON = os.path.join(WORKSPACE_DIR, "ml", "dataset", "manifest_v3.2-real-final.json")
REPORT_MD_PATH = os.path.join(WORKSPACE_DIR, "PHASE8H_FINAL_MODEL_VALIDATION_REPORT.md")
REPORT_JSON_PATH = os.path.join(WORKSPACE_DIR, "PHASE8H_FINAL_MODEL_VALIDATION.json")

XGB_V3_PATH = os.path.join(WORKSPACE_DIR, "ml", "models", "xgb_v3_real_candidate.joblib")
PLATT_V3_PATH = os.path.join(WORKSPACE_DIR, "ml", "models", "xgb_v3_calibrated_candidate.joblib")
RF_V3_PATH = os.path.join(WORKSPACE_DIR, "ml", "models", "rf_v3_real_candidate.joblib")
SHAP_V3_PATH = os.path.join(WORKSPACE_DIR, "ml", "models", "shap_explainer_v3.joblib")

EXPECTED_V32_SHA256 = "9677c6d65ef8f2ab388160079e868ed2bf17307a9e462e1fba26517ae9bedd0e"


def compute_sha256(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


def test_phase8h_database_immutability_and_model_invariants():
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


def test_phase8h_dataset_v32_integrity_and_registration():
    """Verifies that dataset v3.2-real-final exists, has valid checksum, and is registered in PostgreSQL."""
    assert os.path.exists(DATASET_V32_CSV), f"Missing {DATASET_V32_CSV}"
    assert os.path.exists(MANIFEST_V32_JSON), f"Missing {MANIFEST_V32_JSON}"

    v32_hash = compute_sha256(DATASET_V32_CSV)
    assert v32_hash == EXPECTED_V32_SHA256, f"v3.2 checksum mismatch: {v32_hash}"

    df = pd.read_csv(DATASET_V32_CSV)
    assert len(df) == 1674

    with engine.connect() as conn:
        reg = conn.execute(text("SELECT name, version, dataset_type, record_count, training_eligible FROM dataset_registry WHERE version = 'v3.2-real-final';")).fetchone()

    assert reg is not None, "v3.2-real-final is not registered in PostgreSQL dataset_registry!"
    assert reg.record_count == 1674
    assert reg.training_eligible is True


def test_phase8h_model_artifacts_loading():
    """Verifies that all trained v3.0 model artifacts exist on disk and can be loaded properly."""
    assert os.path.exists(XGB_V3_PATH), f"Missing {XGB_V3_PATH}"
    assert os.path.exists(PLATT_V3_PATH), f"Missing {PLATT_V3_PATH}"
    assert os.path.exists(RF_V3_PATH), f"Missing {RF_V3_PATH}"
    assert os.path.exists(SHAP_V3_PATH), f"Missing {SHAP_V3_PATH}"

    xgb_clf = joblib.load(XGB_V3_PATH)
    platt_cal = joblib.load(PLATT_V3_PATH)
    rf_clf = joblib.load(RF_V3_PATH)
    shap_exp = joblib.load(SHAP_V3_PATH)

    assert hasattr(xgb_clf, "predict_proba")
    assert hasattr(platt_cal, "predict_proba")
    assert hasattr(rf_clf, "predict_proba")
    assert hasattr(shap_exp, "shap_values")


def test_phase8h_frozen_2026_acceptance_gates():
    """Verifies that the calibrated champion candidate passes all operational acceptance gates."""
    with open(REPORT_JSON_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    evals = manifest["model_evaluations"]["calibrated_platt_xgboost"]
    hitl = manifest["tri_tier_hitl_metrics"]

    # Acceptance Gates
    assert evals["balanced_accuracy"] >= 0.70, f"Balanced accuracy {evals['balanced_accuracy']} below gate (0.70)"
    assert evals["log_loss"] < 0.75, f"Calibrated log loss {evals['log_loss']} above gate (0.75)"
    assert hitl["tier1_selective_accuracy"] >= 0.95, f"Tier 1 selective accuracy {hitl['tier1_selective_accuracy']} below gate (0.95)"
    assert hitl["tier1_events"] >= 50, f"Tier 1 events {hitl['tier1_events']} insufficient"


def test_phase8h_report_and_manifest_exist():
    """Verifies that PHASE8H_FINAL_MODEL_VALIDATION_REPORT.md and .json exist and have complete content."""
    assert os.path.exists(REPORT_MD_PATH), f"Missing {REPORT_MD_PATH}"
    assert os.path.exists(REPORT_JSON_PATH), f"Missing {REPORT_JSON_PATH}"

    with open(REPORT_JSON_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    assert manifest["phase"] == "PHASE_8H"
    assert manifest["status"] == "PHASE_8H_COMPLETE"
    assert "production_candidate_selection" in manifest
    assert manifest["production_candidate_selection"]["selected_model"] == "xgb-v3.0-real-candidate"
