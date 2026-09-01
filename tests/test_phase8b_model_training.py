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
from ml.training.feature_pipeline import FEATURE_COLUMNS, CLASS_NAMES

PROJECT_DIR = r"E:\PROJECTS\AGNI-NETRA"
MD_REPORT_PATH = os.path.join(PROJECT_DIR, "PHASE8B_MODEL_TRAINING_REPORT.md")
JSON_MANIFEST_PATH = os.path.join(PROJECT_DIR, "PHASE8B_MODEL_TRAINING.json")
DATASET_CSV_PATH = os.path.join(PROJECT_DIR, "ml", "dataset", "dataset_v3.0-real-authoritative.csv")
MODELS_DIR = os.path.join(PROJECT_DIR, "ml", "models")
EXPECTED_DATASET_SHA256 = "9d246bedd1f52b3fd223148b6158ad22f310c2e72a06e6093668b5d72212b835"


def compute_sha256(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


def test_phase8b_report_and_json_manifest_exist():
    """Verify that Phase 8B report and JSON manifest exist and contain valid metadata."""
    assert os.path.exists(MD_REPORT_PATH), f"Report not found at {MD_REPORT_PATH}"
    assert os.path.exists(JSON_MANIFEST_PATH), f"JSON manifest not found at {JSON_MANIFEST_PATH}"

    with open(JSON_MANIFEST_PATH, "r", encoding="utf-8") as f:
        meta = json.load(f)

    assert meta["version"] == "xgb-v2.0-real-candidate"
    assert meta["benchmark_version"] == "rf-v2.0-real-candidate"
    assert meta["dataset_version"] == "v3.0-real-authoritative"
    assert meta["dataset_sha256"] == EXPECTED_DATASET_SHA256
    assert meta["supervised_sample_count"] == 849
    assert len(meta["feature_columns"]) == 18
    assert len(meta["target_classes"]) == 6


def test_phase8b_dataset_hash_and_invariants():
    """Verify dataset SHA-256, row count, zero demo contamination, and anti-leakage compliance."""
    assert os.path.exists(DATASET_CSV_PATH)
    actual_hash = compute_sha256(DATASET_CSV_PATH)
    assert actual_hash == EXPECTED_DATASET_SHA256, f"Hash mismatch: {actual_hash} != {EXPECTED_DATASET_SHA256}"

    import pandas as pd
    df = pd.read_csv(DATASET_CSV_PATH)
    assert len(df) == 1674, f"Expected 1,674 rows, got {len(df)}"

    labeled_df = df[df["label"] != "Uncertain"].copy()
    assert len(labeled_df) == 849, f"Expected 849 supervised events, got {len(labeled_df)}"

    # 0 demo records
    demo_count = (labeled_df["is_demo"] == True).sum() if "is_demo" in labeled_df.columns else 0
    assert demo_count == 0, f"Demo contamination found: {demo_count} records"

    # 100% point-in-time compliant
    pit_count = (labeled_df["point_in_time_compliant"] == True).sum()
    assert pit_count == 849, f"Point-in-time compliance failed: {pit_count}/849"

    # Split boundaries
    train_c = len(labeled_df[labeled_df["split"] == "TRAIN"])
    val_c = len(labeled_df[labeled_df["split"] == "VALIDATION"])
    test_c = len(labeled_df[labeled_df["split"] == "TEST"])
    assert train_c == 440, f"Expected 440 train rows, got {train_c}"
    assert val_c == 233, f"Expected 233 val rows, got {val_c}"
    assert test_c == 176, f"Expected 176 test rows, got {test_c}"


def test_phase8b_model_artifacts_and_hashes():
    """Verify serialized model artifacts exist, load properly, and hashes match manifest."""
    with open(JSON_MANIFEST_PATH, "r", encoding="utf-8") as f:
        meta = json.load(f)

    xgb_path = os.path.join(MODELS_DIR, "xgb_v2_real_candidate.joblib")
    rf_path = os.path.join(MODELS_DIR, "rf_v2_real_candidate.joblib")
    shap_path = os.path.join(MODELS_DIR, "shap_explainer_v2.joblib")

    assert os.path.exists(xgb_path), f"XGBoost artifact not found at {xgb_path}"
    assert os.path.exists(rf_path), f"RF artifact not found at {rf_path}"
    assert os.path.exists(shap_path), f"SHAP artifact not found at {shap_path}"

    assert compute_sha256(xgb_path) == meta["artifact_hashes"]["xgb_v2_real_candidate.joblib"]
    assert compute_sha256(rf_path) == meta["artifact_hashes"]["rf_v2_real_candidate.joblib"]
    assert compute_sha256(shap_path) == meta["artifact_hashes"]["shap_explainer_v2.joblib"]

    # Verify model loading
    xgb_clf = joblib.load(xgb_path)
    rf_clf = joblib.load(rf_path)
    shap_expl = joblib.load(shap_path)

    assert hasattr(xgb_clf, "predict_proba")
    assert hasattr(rf_clf, "predict_proba")
    assert hasattr(shap_expl, "shap_values")


def test_phase8b_postgresql_model_registry():
    """Verify newly trained candidate models are registered in PostgreSQL ml_model_registry without displacing baselines."""
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT version, model_name, dataset_version, algorithm, status, is_active, artifact_path
            FROM ml_model_registry
            ORDER BY version;
        """)).fetchall()

    reg_dict = {r[0]: {"name": r[1], "dataset_v": r[2], "algo": r[3], "status": r[4], "active": r[5]} for r in rows}

    # Verify baseline models preserved
    assert "iso-v1.0-anomaly" in reg_dict
    assert "rf-v1.0-benchmark" in reg_dict
    assert "v1.0-synthetic-baseline" in reg_dict

    # Verify new candidate models
    assert "xgb-v2.0-real-candidate" in reg_dict
    assert reg_dict["xgb-v2.0-real-candidate"]["status"] == "CANDIDATE"
    assert reg_dict["xgb-v2.0-real-candidate"]["active"] is False
    assert reg_dict["xgb-v2.0-real-candidate"]["algo"] == "XGBoost"

    assert "rf-v2.0-real-candidate" in reg_dict
    assert reg_dict["rf-v2.0-real-candidate"]["status"] == "CANDIDATE"
    assert reg_dict["rf-v2.0-real-candidate"]["active"] is False
    assert reg_dict["rf-v2.0-real-candidate"]["algo"] == "Random Forest"


def test_phase8b_model_performance_benchmarks():
    """Verify performance metrics, minority class recall, and temporal stability."""
    with open(JSON_MANIFEST_PATH, "r", encoding="utf-8") as f:
        meta = json.load(f)

    xgb_val = meta["xgboost_metrics"]["validation"]
    xgb_test = meta["xgboost_metrics"]["test"]
    rf_val = meta["random_forest_metrics"]["validation"]
    rf_test = meta["random_forest_metrics"]["test"]

    # F1 & Balanced Accuracy thresholds
    assert xgb_val["macro_f1"] >= 0.60, f"XGB Val Macro F1 too low: {xgb_val['macro_f1']}"
    assert xgb_test["macro_f1"] >= 0.60, f"XGB Test Macro F1 too low: {xgb_test['macro_f1']}"
    assert xgb_val["balanced_accuracy"] >= 0.65, f"XGB Val Bal Acc too low: {xgb_val['balanced_accuracy']}"
    assert xgb_test["balanced_accuracy"] >= 0.65, f"XGB Test Bal Acc too low: {xgb_test['balanced_accuracy']}"

    # XGBoost superiority over baseline on validation & test
    assert xgb_val["macro_f1"] >= rf_val["macro_f1"]
    assert xgb_test["macro_f1"] >= rf_test["macro_f1"]

    # Minority class non-zero recall on test set
    for cls_name in ["Mining Activity", "Gas Flare", "Industrial Fire"]:
        rec = xgb_test["per_class"][cls_name]["recall"]
        assert rec > 0.40, f"Minority class recall for {cls_name} too low: {rec}"

    # Temporal stability between Val (2025) and Test (2026)
    delta_f1 = abs(xgb_test["macro_f1"] - xgb_val["macro_f1"])
    assert delta_f1 <= 0.05, f"Excessive performance shift between Val and Test: {delta_f1}"


def test_phase8b_shap_and_feature_importance_validity():
    """Verify SHAP attributions and permutation importance cover all 18 features."""
    with open(JSON_MANIFEST_PATH, "r", encoding="utf-8") as f:
        meta = json.load(f)

    feat_meta = meta["feature_importance"]
    assert len(feat_meta["xgb_mdi_gain"]) == 18
    assert len(feat_meta["rf_mdi_gini"]) == 18
    assert len(feat_meta["permutation_importance"]) == 18
    assert len(feat_meta["shap_global_mean_abs"]) == 18
    assert len(feat_meta["shap_top_drivers_per_class"]) == 6

    # Top features should include physical proximities
    top_shap_feats = list(feat_meta["shap_global_mean_abs"].keys())[:5]
    assert any("dist_to_" in feat or "context" in feat or "persistence" in feat for feat in top_shap_feats)


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
