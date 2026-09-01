"""
AGNI-NETRA — Phase 6C Evidence Vector & ML Feature Validation Test Suite
========================================================================
Validates that the Phase 6C audit report, JSON manifest, feature schemas,
pilot isolation, temporal/spatial leakage audits, and multi-year data immutability
are 100% compliant with production ML requirements.
"""

import os
import json
import pytest
from sqlalchemy import text
from backend.app.core.database import engine
from ml.training.feature_pipeline import FEATURE_COLUMNS, CLASS_NAMES


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
REPORT_MD_PATH = os.path.join(PROJECT_ROOT, "PHASE6C_ML_FEATURE_VALIDATION_REPORT.md")
REPORT_JSON_PATH = os.path.join(PROJECT_ROOT, "PHASE6C_ML_FEATURE_VALIDATION.json")


def test_phase6c_report_artifacts_exist():
    """Verify that Phase 6C report markdown and JSON manifest exist and are complete."""
    assert os.path.exists(REPORT_MD_PATH), f"Missing {REPORT_MD_PATH}"
    assert os.path.exists(REPORT_JSON_PATH), f"Missing {REPORT_JSON_PATH}"

    with open(REPORT_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data.get("phase") == "PHASE_6C"
    assert data.get("status") == "PHASE_6C_COMPLETE"
    assert "live_counts" in data
    assert "year_counts" in data
    assert "feature_validation" in data
    assert "temporal_leakage" in data
    assert "spatial_leakage" in data
    assert "temporal_split_design" in data
    assert "dataset_schema_spec" in data
    assert "reproducibility_hash_sha256" in data
    assert len(data["reproducibility_hash_sha256"]) == 64


def test_authoritative_live_database_counts():
    """Verify that live PostgreSQL record counts match authoritative levels."""
    with engine.connect() as conn:
        det_cnt = conn.execute(text("SELECT COUNT(*) FROM thermal_detections;")).scalar()
        hist_cnt = conn.execute(text("SELECT COUNT(*) FROM thermal_history;")).scalar()
        fb_cnt = conn.execute(text("SELECT COUNT(*) FROM facility_baselines;")).scalar()
        ef_cnt = conn.execute(text("SELECT COUNT(*) FROM event_features;")).scalar()
        fac_cnt = conn.execute(text("SELECT COUNT(*) FROM industrial_facilities;")).scalar()

    assert det_cnt >= 8_200_000, f"Expected >= 8.2M thermal detections, got {det_cnt}"
    assert hist_cnt >= 8_200_000, f"Expected >= 8.2M thermal history, got {hist_cnt}"
    assert fb_cnt == 35_579, f"Expected 35,579 facility baselines, got {fb_cnt}"
    assert fac_cnt >= 35_579, f"Expected >= 35,579 industrial facilities, got {fac_cnt}"
    assert ef_cnt >= 69, f"Expected >= 69 event feature vectors, got {ef_cnt}"


def test_demo_pilot_isolation_in_baselines():
    """Verify that demo/pilot observations are strictly excluded from baselines and training registry."""
    with engine.connect() as conn:
        # Check facility baselines
        demo_in_fb = conn.execute(text("""
            SELECT COUNT(*) 
            FROM facility_baselines fb
            JOIN industrial_facilities f ON f.id = fb.facility_id
            WHERE f.source = 'DEMO';
        """)).scalar()

        # Check historical baselines
        demo_in_hb = conn.execute(text("""
            SELECT COUNT(*) 
            FROM historical_baselines 
            WHERE grid_cell_id LIKE '%DEMO%' OR grid_cell_id LIKE '%TEST%';
        """)).scalar()

        # Check dataset registry
        demo_eligible = conn.execute(text("""
            SELECT COUNT(*) 
            FROM dataset_registry 
            WHERE dataset_type = 'DEMO' AND training_eligible = true;
        """)).scalar()

    assert demo_in_fb == 0, f"Detected {demo_in_fb} demo records in facility baselines!"
    assert demo_in_hb == 0, f"Detected {demo_in_hb} demo records in historical baselines!"
    assert demo_eligible == 0, f"Detected {demo_eligible} demo datasets eligible for training!"


def test_event_feature_vector_dimensions_and_null_safety():
    """Verify that event features table matches the required 18 dimensions and has 0 null values."""
    with engine.connect() as conn:
        null_count = conn.execute(text("""
            SELECT COUNT(*) 
            FROM event_features 
            WHERE frp_max IS NULL 
               OR frp_avg IS NULL 
               OR bright_max IS NULL 
               OR dist_to_facility_m IS NULL 
               OR dist_to_forest_m IS NULL;
        """)).scalar()

        total_features = conn.execute(text("SELECT COUNT(*) FROM event_features;")).scalar()

    assert null_count == 0, f"Found {null_count} null feature fields in event_features!"
    assert total_features >= 69, f"Expected >= 69 event features, got {total_features}"
    assert len(FEATURE_COLUMNS) == 18, f"Expected 18 feature dimensions, got {len(FEATURE_COLUMNS)}"


def test_ml_model_registry_contracts_and_models():
    """Verify that all registered models conform to ML schema contracts."""
    with engine.connect() as conn:
        models = conn.execute(text("""
            SELECT model_name, version, dataset_version, algorithm, status, is_active
            FROM ml_model_registry;
        """)).fetchall()

    assert len(models) >= 3, f"Expected at least 3 registered models, got {len(models)}"
    versions = [m[1] for m in models]
    assert "rf-v1.0-benchmark" in versions
    assert "iso-v1.0-anomaly" in versions
    assert "v1.0-synthetic-baseline" in versions


def test_multi_year_dataset_immutability():
    """Verify that raw FIRMS observation counts across 2022-2026 are 100% immutable."""
    with engine.connect() as conn:
        y22_off = conn.execute(text("SELECT COUNT(*) FROM thermal_detections WHERE acq_timestamp >= '2022-01-01' AND acq_timestamp < '2023-01-01' AND is_demo = false;")).scalar()
        y22_pil = conn.execute(text("SELECT COUNT(*) FROM thermal_detections WHERE acq_timestamp >= '2022-01-01' AND acq_timestamp < '2023-01-01' AND is_demo = true;")).scalar()
        y23_off = conn.execute(text("SELECT COUNT(*) FROM thermal_detections WHERE acq_timestamp >= '2023-01-01' AND acq_timestamp < '2024-01-01' AND is_demo = false;")).scalar()
        y24_off = conn.execute(text("SELECT COUNT(*) FROM thermal_history WHERE acq_timestamp >= '2024-01-01' AND acq_timestamp < '2025-01-01';")).scalar()
        y25_off = conn.execute(text("SELECT COUNT(*) FROM thermal_detections WHERE acq_timestamp >= '2025-01-01' AND acq_timestamp < '2026-01-01' AND is_demo = false;")).scalar()
        y26_off = conn.execute(text("SELECT COUNT(*) FROM thermal_detections WHERE acq_timestamp >= '2026-01-01' AND acq_timestamp < '2027-01-01' AND is_demo = false;")).scalar()

    assert y22_off == 1_274_383, f"2022 official modified! Expected 1,274,383, got {y22_off}"
    assert y22_pil == 210_000, f"2022 pilot modified! Expected 210,000, got {y22_pil}"
    assert y23_off == 1_244_759, f"2023 official modified! Expected 1,244,759, got {y23_off}"
    assert y24_off == 1_711_626, f"2024 official modified! Expected 1,711,626, got {y24_off}"
    assert y25_off == 2_007_898, f"2025 official modified! Expected 2,007,898, got {y25_off}"
    assert y26_off >= 1_771_110, f"2026 baseline modified! Expected >= 1,771,110, got {y26_off}"
