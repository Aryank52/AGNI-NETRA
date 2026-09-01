"""
Test Suite for Phase 8A: Final ML Pre-Training Gate
===================================================
Verifies dataset integrity, label quality, provenance distribution, feature quality,
temporal/spatial isolation, historical taxonomy, and model training contracts.
"""

import os
import json
import hashlib
import pytest
import pandas as pd
from sqlalchemy import create_engine, text

from backend.app.core.config import settings
from ml.training.feature_pipeline import FEATURE_COLUMNS, CLASS_NAMES

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
REPORT_MD_PATH = os.path.join(PROJECT_ROOT, "PHASE8A_ML_PRETRAINING_GATE.md")
REPORT_JSON_PATH = os.path.join(PROJECT_ROOT, "PHASE8A_ML_PRETRAINING_GATE.json")
CSV_PATH = os.path.join(PROJECT_ROOT, "ml", "dataset", "dataset_v3.0-real-authoritative.csv")
MANIFEST_PATH = os.path.join(PROJECT_ROOT, "ml", "dataset", "manifest_v3.0-real-authoritative.json")


def test_phase8a_report_and_manifest_exist():
    """Verify that Phase 8A markdown report and JSON metadata exist and are valid."""
    assert os.path.exists(REPORT_MD_PATH), f"Missing {REPORT_MD_PATH}"
    assert os.path.exists(REPORT_JSON_PATH), f"Missing {REPORT_JSON_PATH}"

    with open(REPORT_JSON_PATH, "r", encoding="utf-8") as f:
        meta = json.load(f)

    assert meta["dataset_version"] == "v3.0-real-authoritative"
    assert meta["final_status"] in ["PHASE_8A_READY_FOR_TRAINING", "TRAINING_BLOCKED_LABEL_QUALITY", "PHASE_8A_BLOCKED_DATA_INTEGRITY"]
    assert "dataset_artifact" in meta
    assert "label_quality" in meta
    assert "training_label_policy" in meta
    assert "feature_quality_audit" in meta
    assert "training_strategy" in meta


def test_phase8a_dataset_checksum_and_schema():
    """Verify dataset SHA-256 hash, row count (1,674), and 18 canonical features."""
    assert os.path.exists(CSV_PATH)
    assert os.path.exists(MANIFEST_PATH)

    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    with open(CSV_PATH, "rb") as f:
        actual_sha256 = hashlib.sha256(f.read()).hexdigest()

    assert manifest["provenance_hash"] == actual_sha256
    assert manifest["total_records"] == 1674
    assert manifest["feature_count"] == 18

    df = pd.read_csv(CSV_PATH)
    assert len(df) == 1674
    for feat in FEATURE_COLUMNS:
        assert feat in df.columns
        assert df[feat].isna().sum() == 0, f"Missing values found in feature {feat}"


def test_phase8a_label_policy_and_provenance():
    """Verify 7 classes, 0 demo records, 0 synthetic records, and label provenance."""
    df = pd.read_csv(CSV_PATH)

    # Demo & Synthetic isolation
    assert (df["is_demo"] == True).sum() == 0
    assert (df["label_type"] == "SYNTHETIC").sum() == 0

    # Label classes
    unique_labels = set(df["label"].unique())
    for c in ["Industrial Fire", "Gas Flare", "Forest Fire", "Agricultural Burning", "Mining Activity", "Other Thermal Source", "Uncertain"]:
        assert c in unique_labels

    # Provenance
    provenance_counts = df["label_type"].value_counts().to_dict()
    assert provenance_counts.get("HUMAN_VERIFIED", 0) == 14
    assert provenance_counts.get("REAL", 0) == 697
    assert provenance_counts.get("WEAKLY_LABELED", 0) == 138
    assert provenance_counts.get("UNKNOWN", 0) == 825


def test_phase8a_feature_quality_actions():
    """Verify that all 18 features have been categorized (KEEP/REVIEW) and have valid stats."""
    with open(REPORT_JSON_PATH, "r", encoding="utf-8") as f:
        meta = json.load(f)

    fqa = meta["feature_quality_audit"]
    assert fqa["total_features"] == 18
    assert fqa["keep_count"] >= 16

    actions = fqa["feature_actions"]
    assert "frp_max" in actions and "KEEP" in actions["frp_max"]["action"]
    assert "persistence_score" in actions and "KEEP" in actions["persistence_score"]["action"]
    assert "baseline_deviation_ratio" in actions and "KEEP" in actions["baseline_deviation_ratio"]["action"]


def test_phase8a_temporal_spatial_isolation():
    """Verify chronological split boundaries, Point-in-Time compliance, and spatial clusters."""
    df = pd.read_csv(CSV_PATH)

    train_dates = df[df["split"] == "TRAIN"]["acquisition_date"].astype(str)
    val_dates = df[df["split"] == "VALIDATION"]["acquisition_date"].astype(str)
    test_dates = df[df["split"] == "TEST"]["acquisition_date"].astype(str)

    assert str(train_dates.max()) <= "2024-12-31"
    assert str(val_dates.min()) >= "2025-01-01" and str(val_dates.max()) <= "2025-12-31"
    assert str(test_dates.min()) >= "2026-01-01"

    assert (df["point_in_time_compliant"] == True).all()

    # Regional holdout regions
    regions = df["spatial_holdout_region"].unique()
    assert "EASTERN_COAL_BELT" in regions
    assert "WESTERN_PETROCHEMICAL" in regions
    assert "NORTHERN_AGRICULTURE" in regions
    assert "GENERAL_INDIAN_TERRITORY" in regions


def test_phase8a_historical_count_definitions():
    """Verify PostgreSQL historical database counts and immutability invariants."""
    engine = create_engine(settings.DATABASE_URL)
    with engine.connect() as conn:
        td_official = conn.execute(text("SELECT COUNT(*) FROM thermal_detections WHERE is_demo = FALSE;")).scalar()
        td_pilot = conn.execute(text("SELECT COUNT(*) FROM thermal_detections WHERE is_demo = TRUE;")).scalar()
        th_official = conn.execute(text("SELECT COUNT(*) FROM thermal_history WHERE is_demo = FALSE;")).scalar()

    assert td_official >= 8011350
    assert td_pilot >= 210000
    assert th_official >= 8011350


def test_phase8a_model_contract_and_strategy():
    """Verify model contract compatibility with dataset_v3 and strategy metrics."""
    with open(REPORT_JSON_PATH, "r", encoding="utf-8") as f:
        meta = json.load(f)

    mc = meta["model_contract_audit"]
    assert mc["dataset_v3_feature_match"] is True
    assert mc["expected_feature_count"] == 18

    ts = meta["training_strategy"]
    assert ts["primary_model"]["algorithm"] == "XGBoost"
    assert ts["baseline_model"]["algorithm"] == "Random Forest"
    assert ts["anomaly_radar"]["algorithm"] == "Isolation Forest"
    assert "macro_f1" in ts["evaluation_metrics"]
    assert "weighted_f1" in ts["evaluation_metrics"]
    assert "balanced_accuracy" in ts["evaluation_metrics"]
    assert "multiclass_brier_score" in ts["evaluation_metrics"]
