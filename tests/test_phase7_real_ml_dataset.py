"""
AGNI-NETRA - Phase 7 Verification Suite
========================================
Validates the construction, integrity, Point-in-Time compliance, demo isolation,
and schema invariants of the real multi-year ML training dataset.
"""

import os
import sys
import json
import hashlib
import pytest
import pandas as pd
from sqlalchemy import create_engine, text

# Add project root to sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.app.core.config import settings
from ml.training.feature_pipeline import FEATURE_COLUMNS, CLASS_NAMES

DATASET_VERSION = "v3.0-real-authoritative"
CSV_PATH = os.path.join(PROJECT_ROOT, "ml", "dataset", f"dataset_{DATASET_VERSION}.csv")
MANIFEST_PATH = os.path.join(PROJECT_ROOT, "ml", "dataset", f"manifest_{DATASET_VERSION}.json")
REPORT_MD = os.path.join(PROJECT_ROOT, "PHASE7_ML_DATASET_REPORT.md")
REPORT_JSON = os.path.join(PROJECT_ROOT, "PHASE7_ML_DATASET.json")


def compute_sha256(filepath: str) -> str:
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def test_phase7_report_and_manifest_exist():
    """Verify all Phase 7 artifacts exist, are non-empty, and checksums match."""
    assert os.path.exists(REPORT_MD), f"Missing {REPORT_MD}"
    assert os.path.exists(REPORT_JSON), f"Missing {REPORT_JSON}"
    assert os.path.exists(CSV_PATH), f"Missing {CSV_PATH}"
    assert os.path.exists(MANIFEST_PATH), f"Missing {MANIFEST_PATH}"

    with open(REPORT_JSON, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)

    assert manifest_data["dataset_version"] == DATASET_VERSION
    assert manifest_data["total_records"] >= 1000
    assert manifest_data["feature_count"] == 18

    # Verify SHA-256 Checksum
    actual_csv_hash = compute_sha256(CSV_PATH)
    assert manifest_data["provenance_hash"] == actual_csv_hash


def test_phase7_database_registry_entry():
    """Verify the dataset is registered in PostgreSQL dataset_registry with correct metadata."""
    engine = create_engine(settings.DATABASE_URL)
    with engine.connect() as conn:
        row = conn.execute(text("""
            SELECT id, name, version, dataset_type, source, record_count, verified_count, training_eligible, manifest_path
            FROM dataset_registry
            WHERE version = :version;
        """), {"version": DATASET_VERSION}).fetchone()

        assert row is not None, f"Dataset version '{DATASET_VERSION}' not found in dataset_registry table!"
        d = dict(row._mapping)
        assert d["dataset_type"] == "REAL"
        assert d["training_eligible"] is True
        assert d["record_count"] >= 1000
        assert d["verified_count"] >= 10


def test_phase7_zero_demo_contamination():
    """Verify zero demo records exist in the generated dataset."""
    df = pd.read_csv(CSV_PATH)
    assert (df["is_demo"] == True).sum() == 0, "Demo records detected in real ML dataset!"
    assert (df["is_demo"] == False).all(), "Non-false is_demo values present!"


def test_phase7_point_in_time_compliance():
    """Verify 18 feature dimensions, no missing values, and Point-in-Time compliance."""
    df = pd.read_csv(CSV_PATH)
    assert len(df) >= 1000

    for col in FEATURE_COLUMNS:
        assert col in df.columns, f"Missing feature column: {col}"
        assert df[col].isna().sum() == 0, f"Missing/NaN values in feature {col}"
        assert not df[col].isin([float("inf"), float("-inf")]).any(), f"Infinite values in feature {col}"

    assert (df["point_in_time_compliant"] == True).all(), "Non-compliant Point-in-Time records found!"


def test_phase7_temporal_and_spatial_splits():
    """Verify chronological temporal partitions (Train: 2022-2024, Val: 2025, Test: 2026)."""
    df = pd.read_csv(CSV_PATH)

    split_counts = df["split"].value_counts().to_dict()
    assert "TRAIN" in split_counts and split_counts["TRAIN"] > 0
    assert "VALIDATION" in split_counts and split_counts["VALIDATION"] > 0
    assert "TEST" in split_counts and split_counts["TEST"] > 0

    # Verify chronological consistency
    train_dates = df[df["split"] == "TRAIN"]["acquisition_date"].astype(str)
    assert (train_dates <= "2024-12-31").all(), "Future records found in TRAIN split!"

    val_dates = df[df["split"] == "VALIDATION"]["acquisition_date"].astype(str)
    assert (val_dates >= "2025-01-01").all() and (val_dates <= "2025-12-31").all(), "Non-2025 dates in VALIDATION!"

    test_dates = df[df["split"] == "TEST"]["acquisition_date"].astype(str)
    assert (test_dates >= "2026-01-01").all(), "Non-2026 dates in TEST!"


def test_phase7_label_distribution_and_classes():
    """Verify 7-class label coverage and valid provenance categories."""
    df = pd.read_csv(CSV_PATH)

    labels = set(df["label"].unique())
    for c in CLASS_NAMES:
        assert c in labels, f"Expected target class '{c}' not found in dataset labels!"

    label_types = set(df["label_type"].unique())
    assert "HUMAN_VERIFIED" in label_types
    assert "REAL" in label_types
    assert "UNKNOWN" in label_types

    # Ensure no synthetic or demo label types
    assert "SYNTHETIC" not in label_types
    assert "DEMO" not in label_types


def test_historical_datasets_immutability():
    """Verify that historical FIRMS raw observations remain completely immutable."""
    engine = create_engine(settings.DATABASE_URL)
    with engine.connect() as conn:
        row = conn.execute(text("""
            SELECT 
                COUNT(CASE WHEN acq_timestamp >= '2022-01-01' AND acq_timestamp < '2023-01-01' AND is_demo = FALSE THEN 1 END) as c2022_real,
                COUNT(CASE WHEN acq_timestamp >= '2022-01-01' AND acq_timestamp < '2023-01-01' AND is_demo = TRUE THEN 1 END) as c2022_demo,
                COUNT(CASE WHEN acq_timestamp >= '2023-01-01' AND acq_timestamp < '2024-01-01' AND is_demo = FALSE THEN 1 END) as c2023_real,
                COUNT(CASE WHEN acq_timestamp >= '2024-01-01' AND acq_timestamp < '2025-01-01' AND is_demo = FALSE THEN 1 END) as c2024_real,
                COUNT(CASE WHEN acq_timestamp >= '2025-01-01' AND acq_timestamp < '2026-01-01' AND is_demo = FALSE THEN 1 END) as c2025_real,
                COUNT(CASE WHEN acq_timestamp >= '2026-01-01' AND is_demo = FALSE THEN 1 END) as c2026_real
            FROM thermal_detections;
        """)).fetchone()

        d = dict(row._mapping)
        assert d["c2022_real"] == 1274383, f"2022 real count modified: {d['c2022_real']}"
        assert d["c2022_demo"] == 210000, f"2022 pilot count modified: {d['c2022_demo']}"
        assert d["c2023_real"] == 1244759, f"2023 count modified: {d['c2023_real']}"
        assert d["c2024_real"] == 1711626, f"2024 count modified: {d['c2024_real']}"
        assert d["c2025_real"] == 2007898, f"2025 count modified: {d['c2025_real']}"
        assert d["c2026_real"] >= 1772694, f"2026 count modified: {d['c2026_real']}"
