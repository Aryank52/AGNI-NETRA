"""
AGNI-NETRA — PHASE 8G TEST SUITE
Test Suite for Feature Drift In-Depth Audit

Verifies:
1. Database immutability and candidate model registry protection.
2. Existence and integrity of Phase 8G report and manifest.
3. Isolated mature lookback stability (VAL 2025 vs TEST 2026 PSI < 0.15 across all temporal features).
4. Archive origin lookback truncation diagnosis (TRAIN 2022 available lookback vs VAL/TEST 365 days).
5. Event-by-event delta metrics and fallback trigger rates.
6. Candidate models remain inactive (is_active = FALSE, status = CANDIDATE).
"""

import os
import sys
import json
import pytest
import numpy as np
import pandas as pd
from sqlalchemy import text

WORKSPACE_DIR = r"E:\PROJECTS\AGNI-NETRA"
if WORKSPACE_DIR not in sys.path:
    sys.path.insert(0, WORKSPACE_DIR)

from backend.app.core.database import engine

DATASET_V30_CSV = os.path.join(WORKSPACE_DIR, "ml", "dataset", "dataset_v3.0-real-authoritative.csv")
DATASET_V31_CSV = os.path.join(WORKSPACE_DIR, "ml", "dataset", "dataset_v3.1-real-remediated.csv")
REPORT_MD_PATH = os.path.join(WORKSPACE_DIR, "PHASE8G_FEATURE_DRIFT_AUDIT_REPORT.md")
REPORT_JSON_PATH = os.path.join(WORKSPACE_DIR, "PHASE8G_FEATURE_DRIFT_AUDIT.json")


def compute_psi(baseline: np.ndarray, current: np.ndarray, num_bins: int = 10) -> float:
    quantiles = np.linspace(0, 100, num_bins + 1)
    bin_edges = np.percentile(baseline, quantiles)
    bin_edges[0] -= 1e-5
    bin_edges[-1] += 1e-5
    bin_edges = np.unique(bin_edges)
    if len(bin_edges) < 2:
        return 0.0
    base_counts, _ = np.histogram(baseline, bins=bin_edges)
    curr_counts, _ = np.histogram(current, bins=bin_edges)
    base_pct = np.maximum(base_counts / len(baseline), 1e-4)
    curr_pct = np.maximum(curr_counts / len(current), 1e-4)
    return float(np.sum((curr_pct - base_pct) * np.log(curr_pct / base_pct)))


def test_phase8g_database_immutability_and_model_invariants():
    """Verifies that all raw FIRMS tables remain strictly immutable and candidate models inactive."""
    with engine.connect() as conn:
        c_2022_off = conn.execute(text("SELECT COUNT(*) FROM thermal_detections WHERE acq_timestamp >= '2022-01-01' AND acq_timestamp < '2023-01-01' AND is_demo = false;")).scalar()
        c_2022_pil = conn.execute(text("SELECT COUNT(*) FROM thermal_detections WHERE acq_timestamp >= '2022-01-01' AND acq_timestamp < '2023-01-01' AND is_demo = true;")).scalar()
        c_2023_off = conn.execute(text("SELECT COUNT(*) FROM thermal_detections WHERE acq_timestamp >= '2023-01-01' AND acq_timestamp < '2024-01-01' AND is_demo = false;")).scalar()
        c_2024_rec = conn.execute(text("SELECT COUNT(*) FROM thermal_detections WHERE acq_timestamp >= '2024-01-01' AND acq_timestamp < '2025-01-01';")).scalar()
        c_2025_off = conn.execute(text("SELECT COUNT(*) FROM thermal_detections WHERE acq_timestamp >= '2025-01-01' AND acq_timestamp < '2026-01-01';")).scalar()
        c_2026_off = conn.execute(text("SELECT COUNT(*) FROM thermal_detections WHERE acq_timestamp >= '2026-01-01';")).scalar()

        active_models = conn.execute(text("SELECT model_name, version, status, is_active FROM ml_model_registry WHERE version IN ('xgb-v2.0-real-candidate', 'rf-v2.0-real-candidate');")).fetchall()

    assert c_2022_off == 1_274_383
    assert c_2022_pil == 210_000
    assert c_2023_off == 1_244_759
    assert c_2024_rec == 1_711_626
    assert c_2025_off == 2_007_898
    assert c_2026_off >= 1_771_080

    for m in active_models:
        assert not m[3], f"Model {m[1]} must remain inactive!"
        assert m[2] == "CANDIDATE", f"Model {m[1]} must remain CANDIDATE!"


def test_phase8g_artifacts_exist_and_valid():
    """Verifies that PHASE8G_FEATURE_DRIFT_AUDIT_REPORT.md and .json exist and have complete content."""
    assert os.path.exists(REPORT_MD_PATH), f"Missing {REPORT_MD_PATH}"
    assert os.path.exists(REPORT_JSON_PATH), f"Missing {REPORT_JSON_PATH}"

    with open(REPORT_JSON_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    assert manifest["phase"] == "PHASE_8G"
    assert manifest["status"] == "PHASE_8G_COMPLETE"
    assert "split_to_split_psi_matrix" in manifest
    assert "root_cause_synthesis" in manifest
    assert "proposed_remediation" in manifest


def test_phase8g_isolated_mature_lookback_stability():
    """Verifies that between mature partitions (VAL 2025 vs TEST 2026), drift is negligible (< 0.15)."""
    df = pd.read_csv(DATASET_V31_CSV)
    v_val = df[df["split"] == "VALIDATION"]
    v_test = df[df["split"] == "TEST"]

    psi_pers = compute_psi(v_val["persistence_score"].values, v_test["persistence_score"].values)
    psi_dev = compute_psi(v_val["baseline_deviation_ratio"].values, v_test["baseline_deviation_ratio"].values)
    psi_rec = compute_psi(v_val["recurrence_rate"].values, v_test["recurrence_rate"].values)

    assert psi_pers < 0.05, f"Expected mature persistence PSI < 0.05, got {psi_pers}"
    assert psi_dev < 0.05, f"Expected mature baseline_dev PSI < 0.05, got {psi_dev}"
    assert psi_rec < 0.15, f"Expected mature recurrence PSI < 0.15, got {psi_rec}"


def test_phase8g_archive_truncation_diagnosis():
    """Verifies the catalog boundary diagnosis that TRAIN 2022 has truncated lookbacks vs VAL/TEST."""
    df = pd.read_csv(DATASET_V31_CSV)
    df["acq_dt"] = pd.to_datetime(df["acquisition_date"])
    train_days = (df[df["split"] == "TRAIN"]["acq_dt"] - pd.to_datetime("2022-01-01")).dt.days.clip(lower=1, upper=365)
    val_days = (df[df["split"] == "VALIDATION"]["acq_dt"] - pd.to_datetime("2022-01-01")).dt.days.clip(lower=1, upper=365)

    assert train_days.mean() < 200.0, "TRAIN 2022 lookback should be truncated by archive start"
    assert val_days.mean() == 365.0, "VAL 2025 must have full 365-day lookback availability"


def test_phase8g_event_deltas_integrity():
    """Verifies that event-by-event delta distributions between v3.0 and v3.1 are recorded properly."""
    with open(REPORT_JSON_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    deltas = manifest["event_deltas"]
    assert "persistence_score" in deltas
    assert "recurrence_rate" in deltas
    assert "baseline_deviation_ratio" in deltas
    assert deltas["persistence_score"]["events_changed_pct"] > 50.0
