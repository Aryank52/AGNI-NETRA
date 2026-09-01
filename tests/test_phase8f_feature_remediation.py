"""
AGNI-NETRA — PHASE 8F TEST SUITE
Test Suite for Feature Pipeline Remediation & Validation

Verifies:
1. Database immutability and candidate model registry protection.
2. Existence and integrity of v3.1 remediated dataset CSV and manifest.
3. Successful registration of v3.1-real-remediated in PostgreSQL `dataset_registry`.
4. Significant PSI reduction for `persistence_score` (from >2.0 down to <0.20).
5. Stability of remediated shadow metrics (multiclass log-loss < 0.85, balanced accuracy >= 70%).
6. Complete model inactivity invariants (is_active = FALSE, status = CANDIDATE).
"""

import os
import sys
import json
import hashlib
import pytest
import pandas as pd
from sqlalchemy import text

WORKSPACE_DIR = r"E:\PROJECTS\AGNI-NETRA"
if WORKSPACE_DIR not in sys.path:
    sys.path.insert(0, WORKSPACE_DIR)

from backend.app.core.database import engine

DATASET_V30_CSV = os.path.join(WORKSPACE_DIR, "ml", "dataset", "dataset_v3.0-real-authoritative.csv")
DATASET_V31_CSV = os.path.join(WORKSPACE_DIR, "ml", "dataset", "dataset_v3.1-real-remediated.csv")
MANIFEST_V31_JSON = os.path.join(WORKSPACE_DIR, "ml", "dataset", "manifest_v3.1-real-remediated.json")
REPORT_MD_PATH = os.path.join(WORKSPACE_DIR, "PHASE8F_FEATURE_REMEDIATION_REPORT.md")
REPORT_JSON_PATH = os.path.join(WORKSPACE_DIR, "PHASE8F_FEATURE_REMEDIATION.json")

EXPECTED_V30_SHA256 = "9d246bedd1f52b3fd223148b6158ad22f310c2e72a06e6093668b5d72212b835"
EXPECTED_V31_SHA256 = "7a02238da771aee642cad73fea924e2b18b8e974e981bf1da60d5130cf7927db"


def compute_sha256(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


def test_phase8f_database_immutability_and_registry_invariants():
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


def test_phase8f_dataset_v30_and_v31_integrity():
    """Verifies that both v3.0 authoritative and v3.1 remediated datasets exist and match checksums."""
    assert os.path.exists(DATASET_V30_CSV), f"Missing {DATASET_V30_CSV}"
    assert os.path.exists(DATASET_V31_CSV), f"Missing {DATASET_V31_CSV}"
    assert os.path.exists(MANIFEST_V31_JSON), f"Missing {MANIFEST_V31_JSON}"

    v30_hash = compute_sha256(DATASET_V30_CSV)
    v31_hash = compute_sha256(DATASET_V31_CSV)

    assert v30_hash == EXPECTED_V30_SHA256, f"v3.0 checksum modified: {v30_hash}"
    assert v31_hash == EXPECTED_V31_SHA256, f"v3.1 checksum mismatch: {v31_hash}"

    df_v31 = pd.read_csv(DATASET_V31_CSV)
    assert len(df_v31) == 1674
    assert set(df_v31["split"].unique()) == {"TRAIN", "VALIDATION", "TEST"}


def test_phase8f_postgresql_dataset_registration():
    """Verifies that v3.1-real-remediated is registered in dataset_registry."""
    with engine.connect() as conn:
        row = conn.execute(text("SELECT name, version, dataset_type, record_count, training_eligible FROM dataset_registry WHERE version = 'v3.1-real-remediated';")).fetchone()

    assert row is not None, "v3.1-real-remediated not registered in dataset_registry!"
    assert row.record_count == 1674
    assert row.training_eligible is True


def test_phase8f_artifacts_exist_and_valid():
    """Verifies that PHASE8F_FEATURE_REMEDIATION.json and .md exist and have complete content."""
    assert os.path.exists(REPORT_JSON_PATH), f"Missing {REPORT_JSON_PATH}"
    assert os.path.exists(REPORT_MD_PATH), f"Missing {REPORT_MD_PATH}"

    with open(REPORT_JSON_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    assert manifest["phase"] == "PHASE_8F"
    assert manifest["status"] == "PHASE_8F_COMPLETE"
    assert "drift_comparison" in manifest
    assert "distribution_comparison" in manifest
    assert "remediated_shadow_metrics" in manifest


def test_phase8f_persistence_score_psi_reduction():
    """Verifies that persistence_score PSI drops significantly after remediation."""
    with open(REPORT_JSON_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    dist_comp = manifest["distribution_comparison"]
    p_comp = dist_comp["persistence_score"]

    assert p_comp["v30_psi"] > 2.0, f"Expected v3.0 PSI > 2.0, got {p_comp['v30_psi']}"
    assert p_comp["v31_psi"] < 0.20, f"Expected v3.1 remediated PSI < 0.20, got {p_comp['v31_psi']}"
    assert p_comp["v31_psi"] < p_comp["v30_psi"] * 0.10, "Remediation must achieve >90% PSI reduction on persistence_score"


def test_phase8f_remediated_shadow_performance():
    """Verifies that model shadow metrics on the remediated stream remain high quality."""
    with open(REPORT_JSON_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    metrics = manifest["remediated_shadow_metrics"]
    assert metrics["multiclass_log_loss"] < 0.85
    assert metrics["balanced_accuracy"] >= 0.70
    assert metrics["tier1_selective_accuracy"] >= 0.80
    assert metrics["total_shadow_events"] == 414
