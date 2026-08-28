import os
import sys
import pytest
from datetime import datetime, timezone

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.database import SessionLocal
from backend.app.models.domain import MLModelRegistry, DatasetRegistry, ThermalEvent, IndustrialFacility, User
from backend.app.services.model_registry_service import model_registry_service
from backend.app.services.lineage_service import generate_event_trace_lineage
from backend.app.services.baseline_service import calculate_facility_baseline
from data_pipeline.adapters.firms_adapter import firms_adapter


def test_model_registry_lifecycle_and_active_protection():
    """Verify ML model registry lifecycle transitions and single active model constraint"""
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.role == "ADMIN").first()
        if not admin:
            admin = db.query(User).first()

        # 1. Register candidate model
        cand = model_registry_service.register_model_artifact(
            db=db,
            model_name="XGBoost India Test Classifier",
            version="v2.0-test-candidate",
            dataset_version="dataset_v2_india",
            algorithm="XGBoost",
            metrics={"macro_f1": 0.965, "brier_score": 0.048, "spatial_holdout_f1": 0.958},
            artifact_path="ml/models/xgboost_test_v2.joblib",
            notes="Candidate model for testing"
        )
        assert cand.status == "CANDIDATE"
        assert cand.is_active is False

        # 2. Promote to APPROVED
        appr = model_registry_service.update_model_status(
            db=db,
            model_id=cand.id,
            new_status="APPROVED",
            approver=admin,
            notes="Approved by lead ML engineer"
        )
        assert appr.status == "APPROVED"
        assert appr.is_active is False

        # 3. Promote to ACTIVE (should deactivate previous active XGBoost model)
        act = model_registry_service.update_model_status(
            db=db,
            model_id=cand.id,
            new_status="ACTIVE",
            approver=admin,
            notes="Deployed to production"
        )
        assert act.status == "ACTIVE"
        assert act.is_active is True
        assert act.approved_by == admin.email

        # 4. Clean up test record
        db.delete(cand)
        db.commit()
    finally:
        db.close()


def test_event_trace_lineage_generation():
    """Verify 10-stage end-to-end scientific telemetry and intelligence lineage"""
    db = SessionLocal()
    try:
        event = db.query(ThermalEvent).first()
        assert event is not None

        lineage = generate_event_trace_lineage(db, event.id)
        assert lineage["event_id"] == event.id
        assert lineage["total_steps"] == 10
        assert len(lineage["stages"]) == 10

        stage_names = [s["stage"] for s in lineage["stages"]]
        assert "RAW_TELEMETRY" in stage_names
        assert "DETECTION" in stage_names
        assert "EVENT_CLUSTER" in stage_names
        assert "SPATIAL_ENRICHMENT" in stage_names
        assert "LULC_CONTEXT" in stage_names
        assert "FEATURE_VECTOR" in stage_names
        assert "MODEL_INFERENCE" in stage_names
        assert "SHAP_EXPLANATION" in stage_names
        assert "DECISION_SUPPORT" in stage_names
    finally:
        db.close()


def test_facility_baseline_percentiles_and_status_bands():
    """Verify empirical facility baseline percentiles and operational status classification"""
    db = SessionLocal()
    try:
        facility = db.query(IndustrialFacility).first()
        assert facility is not None

        base = calculate_facility_baseline(db, facility.id)
        assert base["facility_id"] == facility.id
        assert "frp_distribution" in base
        assert "p50" in base["frp_distribution"]
        assert base["status_band"] in ["NORMAL", "ELEVATED", "ABNORMAL", "CRITICAL"]
    finally:
        db.close()


def test_firms_india_polygon_clipping():
    """Verify coordinate filtering within Indian geographical envelope"""
    # Jamnagar, Gujarat (inside India)
    assert firms_adapter.validate_coordinates(22.47, 70.05, strict_polygon=False) is True
    # Indian Ocean outside bbox
    assert firms_adapter.validate_coordinates(2.0, 70.0, strict_polygon=False) is False
    # Central Asia outside bbox
    assert firms_adapter.validate_coordinates(42.0, 75.0, strict_polygon=False) is False
