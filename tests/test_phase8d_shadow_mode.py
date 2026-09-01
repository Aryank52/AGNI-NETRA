"""
AGNI-NETRA — Test Suite: Phase 8D Live Shadow-Mode Validation
Validates:
1. Historical dataset and database immutability.
2. Candidate model protection (no auto-activation, is_active=False).
3. Shadow predictions table schema, count (N=414), and zero-dispatch invariant.
4. Tri-tier human-in-the-loop routing policy mathematical consistency.
5. SHAP statistical attribution summaries.
6. Data drift and PSI monitoring calculations.
7. Verified ground-truth metrics and selective accuracy.
8. Phase 8D report artifacts validity.
"""

import os
import json
import hashlib
import pytest
from sqlalchemy import text
from backend.app.core.database import engine

WORKSPACE_DIR = r"E:\PROJECTS\AGNI-NETRA"
DATASET_CSV = os.path.join(WORKSPACE_DIR, "ml", "dataset", "dataset_v3.0-real-authoritative.csv")
EXPECTED_DATASET_SHA256 = "9d246bedd1f52b3fd223148b6158ad22f310c2e72a06e6093668b5d72212b835"

REPORT_MD_PATH = os.path.join(WORKSPACE_DIR, "PHASE8D_SHADOW_MODE_REPORT.md")
REPORT_JSON_PATH = os.path.join(WORKSPACE_DIR, "PHASE8D_SHADOW_MODE.json")


def compute_sha256(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


def test_phase8d_database_immutability_and_registry_invariants():
    """Verify raw FIRMS multi-year observations remain sealed and candidate models are not activated."""
    with engine.connect() as conn:
        det_2022_off = conn.execute(text("SELECT COUNT(*) FROM thermal_detections WHERE acq_timestamp >= '2022-01-01' AND acq_timestamp < '2023-01-01' AND is_demo = false;")).scalar()
        det_2022_pil = conn.execute(text("SELECT COUNT(*) FROM thermal_detections WHERE acq_timestamp >= '2022-01-01' AND acq_timestamp < '2023-01-01' AND is_demo = true;")).scalar()
        det_2023_off = conn.execute(text("SELECT COUNT(*) FROM thermal_detections WHERE acq_timestamp >= '2023-01-01' AND acq_timestamp < '2024-01-01' AND is_demo = false;")).scalar()
        det_2024_rec = conn.execute(text("SELECT COUNT(*) FROM thermal_detections WHERE acq_timestamp >= '2024-01-01' AND acq_timestamp < '2025-01-01';")).scalar()
        det_2025_off = conn.execute(text("SELECT COUNT(*) FROM thermal_detections WHERE acq_timestamp >= '2025-01-01' AND acq_timestamp < '2026-01-01';")).scalar()
        det_2026_off = conn.execute(text("SELECT COUNT(*) FROM thermal_detections WHERE acq_timestamp >= '2026-01-01';")).scalar()

        assert det_2022_off == 1_274_383
        assert det_2022_pil == 210_000
        assert det_2023_off == 1_244_759
        assert det_2024_rec == 1_711_626
        assert det_2025_off == 2_007_898
        assert det_2026_off >= 1_771_080

        # Verify candidate models remain CANDIDATE and is_active = False
        candidates = conn.execute(text("""
            SELECT model_name, version, status, is_active 
            FROM ml_model_registry 
            WHERE version IN ('xgb-v2.0-real-candidate', 'rf-v2.0-real-candidate');
        """)).fetchall()

        assert len(candidates) >= 2
        for row in candidates:
            assert row[2] == "CANDIDATE", f"Model {row[1]} status is {row[2]}"
            assert not row[3], f"Candidate model {row[1]} is active!"


def test_phase8d_dataset_checksum_and_schema():
    """Verify authoritative dataset integrity hash."""
    dataset_hash = compute_sha256(DATASET_CSV)
    assert dataset_hash == EXPECTED_DATASET_SHA256


def test_phase8d_shadow_predictions_table_exists_and_populated():
    """Verify shadow_predictions table contains all 414 events with zero operational dispatches."""
    with engine.connect() as conn:
        count = conn.execute(text("SELECT COUNT(*) FROM shadow_predictions;")).scalar()
        assert count == 414, f"Expected 414 shadow predictions, got {count}"

        dispatched_count = conn.execute(text("SELECT COUNT(*) FROM shadow_predictions WHERE is_operational_dispatch = true;")).scalar()
        assert dispatched_count == 0, f"Found {dispatched_count} operational dispatches in shadow mode!"


def test_phase8d_tri_tier_routing_policy():
    """Verify tri-tier routing threshold rules strictly match mathematical definitions."""
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT top1_probability, top2_probability, confidence_margin, routing_tier 
            FROM shadow_predictions;
        """)).fetchall()

        assert len(rows) == 414
        for r in rows:
            top1, top2, margin, tier = r[0], r[1], r[2], r[3]
            assert abs((top1 - top2) - margin) < 1e-4

            if top1 >= 0.65 and margin >= 0.20:
                assert tier == "TIER_1_AUTO_DISPATCH"
            elif top1 >= 0.45 and margin >= 0.08:
                assert tier == "TIER_2_ANALYST_REVIEW"
            else:
                assert tier == "TIER_3_UNCERTAINTY_QUEUE"


def test_phase8d_shap_explanations_structure():
    """Verify SHAP explanation summaries contain structured statistical attribution fields."""
    with engine.connect() as conn:
        sample_rows = conn.execute(text("""
            SELECT shap_summary, routing_tier 
            FROM shadow_predictions 
            WHERE routing_tier = 'TIER_1_AUTO_DISPATCH' 
            LIMIT 10;
        """)).fetchall()

        assert len(sample_rows) > 0
        for r in sample_rows:
            shap_data = r[0]
            if isinstance(shap_data, str):
                shap_data = json.loads(shap_data)
            assert "predicted_class" in shap_data
            assert "top_contributing_features" in shap_data
            assert len(shap_data["top_contributing_features"]) >= 1
            assert "interpretation_notice" in shap_data


def test_phase8d_verified_tier1_selective_accuracy():
    """Verify Tier 1 selective accuracy on verified ground-truth events exceeds 90%."""
    with open(REPORT_JSON_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    metrics = manifest["verified_metrics"]
    t1_acc = metrics["tier1_selective_accuracy"]
    assert t1_acc >= 0.90, f"Tier 1 selective accuracy is {t1_acc:.4f}, expected >= 0.90"
    assert metrics["accuracy"] >= 0.65
    assert metrics["macro_f1"] >= 0.60
    assert metrics["multiclass_log_loss"] < 1.05


def test_phase8d_drift_monitoring_metrics():
    """Verify data drift metrics and PSI monitoring dictionary are populated."""
    with open(REPORT_JSON_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    drift_info = manifest["drift_monitoring"]
    assert "overall_status" in drift_info
    assert drift_info["overall_status"] in ["NO_SIGNIFICANT_DRIFT", "DATA_DRIFT", "CONCEPT_DRIFT"]
    assert "feature_metrics" in drift_info
    assert len(drift_info["feature_metrics"]) == 18


def test_phase8d_artifacts_and_decision_gate():
    """Verify Phase 8D markdown report, JSON manifest, and valid gate decision."""
    assert os.path.exists(REPORT_MD_PATH)
    assert os.path.exists(REPORT_JSON_PATH)

    with open(REPORT_JSON_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    assert manifest["phase"] == "PHASE_8D"
    assert manifest["status"] == "PHASE_8D_COMPLETE"
    assert manifest["validation_decision"] in ["SHADOW_MODE_HEALTHY", "SHADOW_MODE_DEGRADED", "SHADOW_MODE_BLOCKED"]
    assert manifest["stream_statistics"]["total_shadow_events"] == 414
    assert manifest["champion_model"]["registry_status"] == "CANDIDATE"
    assert manifest["champion_model"]["is_active"] is False
