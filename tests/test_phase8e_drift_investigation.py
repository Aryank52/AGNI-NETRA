"""
AGNI-NETRA — PHASE 8E TEST SUITE
Test Suite for Shadow Drift Investigation & Model Adaptation Audit

Verifies:
1. Database immutability and candidate model registry protection.
2. Existence and completeness of Phase 8E report and JSON manifest.
3. Reproduction of PSI/KS statistics and drift classification.
4. Algorithmic feature-pipeline audit covering lookback windows.
5. Multi-split distribution statistics (TRAIN, VAL, TEST, SHADOW).
6. Seasonality decomposition across monsoon/burning/fire seasons.
7. Model performance stratified by drift severity.
8. Evidence-based decisions: FEATURE_PIPELINE_FIX_REQUIRED and CONTINUE_SHADOW_MODE.
"""

import os
import sys
import json
import hashlib
import pytest
from sqlalchemy import text

WORKSPACE_DIR = r"E:\PROJECTS\AGNI-NETRA"
if WORKSPACE_DIR not in sys.path:
    sys.path.insert(0, WORKSPACE_DIR)

from backend.app.core.database import engine

DATASET_CSV = os.path.join(WORKSPACE_DIR, "ml", "dataset", "dataset_v3.0-real-authoritative.csv")
EXPECTED_DATASET_SHA256 = "9d246bedd1f52b3fd223148b6158ad22f310c2e72a06e6093668b5d72212b835"
REPORT_MD_PATH = os.path.join(WORKSPACE_DIR, "PHASE8E_DRIFT_INVESTIGATION_REPORT.md")
REPORT_JSON_PATH = os.path.join(WORKSPACE_DIR, "PHASE8E_DRIFT_INVESTIGATION.json")


def compute_sha256(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


def test_phase8e_database_immutability_and_registry_invariants():
    """Verifies that all historical and operational raw observation tables are strictly immutable."""
    with engine.connect() as conn:
        c_2022_off = conn.execute(text("SELECT COUNT(*) FROM thermal_detections WHERE acq_timestamp >= '2022-01-01' AND acq_timestamp < '2023-01-01' AND is_demo = false;")).scalar()
        c_2022_pil = conn.execute(text("SELECT COUNT(*) FROM thermal_detections WHERE acq_timestamp >= '2022-01-01' AND acq_timestamp < '2023-01-01' AND is_demo = true;")).scalar()
        c_2023_off = conn.execute(text("SELECT COUNT(*) FROM thermal_detections WHERE acq_timestamp >= '2023-01-01' AND acq_timestamp < '2024-01-01' AND is_demo = false;")).scalar()
        c_2024_rec = conn.execute(text("SELECT COUNT(*) FROM thermal_detections WHERE acq_timestamp >= '2024-01-01' AND acq_timestamp < '2025-01-01';")).scalar()
        c_2025_off = conn.execute(text("SELECT COUNT(*) FROM thermal_detections WHERE acq_timestamp >= '2025-01-01' AND acq_timestamp < '2026-01-01';")).scalar()
        c_2026_off = conn.execute(text("SELECT COUNT(*) FROM thermal_detections WHERE acq_timestamp >= '2026-01-01';")).scalar()

        # Invariant check: candidate models MUST remain CANDIDATE and is_active = FALSE
        active_models = conn.execute(text("SELECT model_name, version, status, is_active FROM ml_model_registry WHERE version IN ('xgb-v2.0-real-candidate', 'rf-v2.0-real-candidate');")).fetchall()

    assert c_2022_off == 1_274_383
    assert c_2022_pil == 210_000
    assert c_2023_off == 1_244_759
    assert c_2024_rec == 1_711_626
    assert c_2025_off == 2_007_898
    assert c_2026_off >= 1_771_080

    for m in active_models:
        assert not m[3], f"Model {m[1]} must NOT be active!"
        assert m[2] == "CANDIDATE", f"Model {m[1]} must remain CANDIDATE status!"


def test_phase8e_dataset_checksum_and_schema():
    """Verifies that the authoritative dataset SHA-256 hash matches the authoritative reference."""
    assert os.path.exists(DATASET_CSV), f"Missing dataset {DATASET_CSV}"
    sha256 = compute_sha256(DATASET_CSV)
    assert sha256 == EXPECTED_DATASET_SHA256, f"Dataset hash mismatch: {sha256}"


def test_phase8e_artifacts_exist_and_valid():
    """Verifies that PHASE8E_DRIFT_INVESTIGATION.json and .md exist and contain required keys."""
    assert os.path.exists(REPORT_JSON_PATH), f"Missing {REPORT_JSON_PATH}"
    assert os.path.exists(REPORT_MD_PATH), f"Missing {REPORT_MD_PATH}"

    with open(REPORT_JSON_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    assert manifest["phase"] == "PHASE_8E"
    assert manifest["status"] == "PHASE_8E_COMPLETE"
    assert "drift_reproduction" in manifest
    assert "drift_typology" in manifest
    assert "pipeline_audit" in manifest
    assert "distribution_summary" in manifest
    assert "seasonality_audit" in manifest
    assert "drift_performance_report" in manifest
    assert "retraining_recommendation" in manifest
    assert "shadow_mode_recommendation" in manifest


def test_phase8e_drift_reproduction_metrics():
    """Verifies that PSI calculations accurately identify elevated drift features."""
    with open(REPORT_JSON_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    reprod = manifest["drift_reproduction"]
    assert "persistence_score" in reprod
    assert "recurrence_rate" in reprod
    assert "baseline_deviation_ratio" in reprod
    assert "dist_to_water_m" in reprod

    # Elevated PSI verification
    assert reprod["persistence_score"]["psi"] > 0.50
    assert reprod["recurrence_rate"]["psi"] > 0.50
    assert reprod["baseline_deviation_ratio"]["psi"] > 0.20


def test_phase8e_pipeline_audit_conclusions():
    """Verifies that feature pipeline audit diagnoses the lookback window root cause."""
    with open(REPORT_JSON_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    audit = manifest["pipeline_audit"]
    assert audit["persistence_score"]["drift_classification"] == "FEATURE_PIPELINE_DRIFT"
    assert audit["recurrence_rate"]["drift_classification"] == "FEATURE_PIPELINE_DRIFT"
    assert "remediation_action" in audit["persistence_score"]
    assert "sliding window" in audit["persistence_score"]["remediation_action"].lower()


def test_phase8e_drift_stratified_performance():
    """Verifies that model performance and abstention rates are evaluated across drift strata."""
    with open(REPORT_JSON_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    perf = manifest["drift_performance_report"]
    assert "LOW_DRIFT" in perf
    assert "MODERATE_DRIFT" in perf
    assert "HIGH_DRIFT" in perf

    # Low drift stratum should have higher accuracy than high drift stratum
    assert perf["LOW_DRIFT"]["accuracy"] > perf["HIGH_DRIFT"]["accuracy"]
    # High drift stratum should trigger higher abstention (safety mechanism)
    assert perf["HIGH_DRIFT"]["abstention_rate"] >= perf["LOW_DRIFT"]["abstention_rate"]


def test_phase8e_confidence_drift_and_calibration():
    """Verifies that multiclass log-loss and Brier score indicate stable calibration."""
    with open(REPORT_JSON_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    conf_audit = manifest["confidence_drift_audit"]
    assert "test_shadow_2026" in conf_audit
    assert conf_audit["test_shadow_2026"]["multiclass_log_loss"] < 1.05
    assert conf_audit["test_shadow_2026"]["multiclass_brier_score"] < 0.10


def test_phase8e_retraining_and_shadow_decisions():
    """Verifies that evidence-based retraining and shadow decisions are correctly formulated."""
    with open(REPORT_JSON_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    retrain = manifest["retraining_recommendation"]
    shadow = manifest["shadow_mode_recommendation"]

    assert retrain["decision"] == "FEATURE_PIPELINE_FIX_REQUIRED"
    assert shadow["decision"] == "CONTINUE_SHADOW_MODE"
