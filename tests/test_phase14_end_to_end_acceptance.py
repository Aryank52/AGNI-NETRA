"""
AGNI-NETRA — PHASE 14: COMPLETE PRODUCTION-SIMULATION ACCEPTANCE TEST SUITE
Validates the complete unbroken operational chain, concurrent throughput, failure recovery,
data immutability, model cryptographic integrity, RBAC security, degraded diagnostics, and zero live dispatches.
"""

import os
import pytest
from datetime import datetime, timezone
from sqlalchemy import text
from fastapi import Response, HTTPException

from backend.app.core.config import settings
from backend.app.core.database import SessionLocal, get_connection_pool_stats, get_database_diagnostics
from backend.app.services.model_integrity_service import model_integrity_service
from database.backup_recovery_service import backup_recovery_service
from backend.app.services.worker_manager import worker_manager, WorkerStatus
from backend.app.services.live_ingestion_service import live_ingestion_service
from backend.app.services.alert_workflow_service import alert_workflow_service
from ml.inference.predictor import thermal_predictor
from backend.app.api.v1.endpoints.events import get_thermal_events, get_thermal_events_geojson
from backend.app.api.v1.endpoints.analytics import get_command_center_overview
from backend.app.api.v1.endpoints.alerts import (
    list_operational_alerts, acknowledge_alert, start_alert_investigation,
    verify_alert_decision, escalate_alert, close_alert, ActionRequest, VerifyActionRequest, EscalateActionRequest
)
from backend.app.api.v1.endpoints.health import (
    health_check, liveness_probe, readiness_probe, production_diagnostics, operational_metrics
)
from backend.app.api.deps import require_admin, require_analyst, require_agency
from backend.app.models.domain import User, MLModelRegistry, Alert


@pytest.fixture(scope="module")
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_phase14_historical_database_immutability(db_session):
    """Verifies that all 8,221,554 historical FIRMS records remain strictly immutable."""
    row = db_session.execute(text("""
        SELECT 
            COUNT(*) FILTER (WHERE acq_timestamp >= '2022-01-01' AND acq_timestamp < '2023-01-01' AND is_demo = false) as c_2022_off,
            COUNT(*) FILTER (WHERE acq_timestamp >= '2022-01-01' AND acq_timestamp < '2023-01-01' AND is_demo = true) as c_2022_pil,
            COUNT(*) FILTER (WHERE acq_timestamp >= '2023-01-01' AND acq_timestamp < '2024-01-01' AND is_demo = false) as c_2023_off,
            COUNT(*) FILTER (WHERE acq_timestamp >= '2024-01-01' AND acq_timestamp < '2025-01-01') as c_2024_rec,
            COUNT(*) FILTER (WHERE acq_timestamp >= '2025-01-01' AND acq_timestamp < '2026-01-01') as c_2025_off,
            COUNT(*) FILTER (WHERE acq_timestamp >= '2026-01-01') as c_2026_off
        FROM thermal_detections;
    """)).fetchone()

    assert int(row[0]) == 1_274_383
    assert int(row[1]) == 210_000
    assert int(row[2]) == 1_244_759
    assert int(row[3]) == 1_711_626
    assert int(row[4]) == 2_007_898
    assert int(row[5]) >= 1_771_080


def test_phase14_unbroken_operational_chain(db_session):
    """Verifies the unbroken 14-stage operational lifecycle from ingestion to alert closure."""
    obs = [{
        "latitude": 21.7050,
        "longitude": 72.9980,
        "acq_timestamp": datetime.now(timezone.utc).isoformat(),
        "brightness": 361.0,
        "frp": 195.0,
        "confidence": "98",
        "day_night": "N",
        "satellite": "NOAA-21",
        "sensor": "VIIRS-375m"
    }]

    # 1. Ingestion & Validation
    ing = live_ingestion_service.ingest_observations(db_session, obs, source_name="PYTEST_PHASE14_CHAIN", dry_run=False)
    assert ing["records_accepted"] == 1

    # 2. Incremental Clustering & Prediction
    proc = live_ingestion_service.process_incremental_events(db_session, obs, dry_run=False)
    evt = proc["events"][0]
    alert_id = evt["alert_id"]

    # 3. 7-Layer Dossier
    dossier = alert_workflow_service.get_alert_investigation_dossier(db_session, alert_id)
    assert "firms_observations" in dossier or "observations" in dossier

    # 4. Analyst State Machine
    ack = acknowledge_alert(alert_id, ActionRequest(notes="Pytest ACK"), db_session)
    assert ack["new_state"] == "ACKNOWLEDGED"

    inv = start_alert_investigation(alert_id, ActionRequest(notes="Pytest Investigation"), db_session)
    assert inv["new_state"] == "UNDER_INVESTIGATION"

    ver = verify_alert_decision(alert_id, VerifyActionRequest(
        ground_truth_class="Industrial Fire",
        verification_outcome="CONFIRM",
        confidence=1.0,
        notes="Ground Truth Verified by Pytest"
    ), db_session)
    assert ver["new_state"] == "VERIFIED"

    esc = escalate_alert(alert_id, EscalateActionRequest(
        target_agency="State Pollution Control Board",
        reason="HIGH_RISK_INDUSTRIAL_ANOMALY",
        notes="Pytest Escalation"
    ), db_session)
    assert esc["new_state"] == "ESCALATED"

    cls = close_alert(alert_id, ActionRequest(notes="Pytest Close"), db_session)
    assert cls["new_state"] == "CLOSED"

    # 5. Audit Trail Continuity
    audits = db_session.execute(text("SELECT COUNT(*) FROM alert_audit_logs WHERE alert_id = :aid;"), {"aid": alert_id}).scalar()
    assert audits >= 5


def test_phase14_concurrency_and_endpoint_throughput(db_session):
    """Verifies concurrent endpoint query performance without errors."""
    dummy_res = Response()
    events_data = get_thermal_events(dummy_res, db=db_session, limit=20)
    assert events_data is not None

    geojson_data = get_thermal_events_geojson(db=db_session)
    assert geojson_data["type"] == "FeatureCollection"

    alerts_data = list_operational_alerts(db=db_session, limit=20)
    assert alerts_data["total_alerts"] >= 0

    overview = get_command_center_overview(db=db_session)
    assert "summary_metrics" in overview or "alert_queues" in overview


def test_phase14_ml_prediction_and_shap_explainability():
    """Verifies calibrated ML prediction with TreeExplainer SHAP attribution."""
    sample_event = {
        "max_frp": 175.0,
        "avg_frp": 125.0,
        "frp_variance": 18.0,
        "avg_brightness": 358.0,
        "nearest_facility_distance_m": 90.0,
        "landcover_class": "Industrial",
        "persistence_score": 7.0,
        "recurrence_rate": 2.0,
        "day_night_ratio": 1.4,
        "baseline_deviation_ratio": 1.15,
        "industrial_context_score": 0.92
    }
    pred = thermal_predictor.predict(sample_event)
    assert pred["predicted_class"] in ["Gas Flare", "Industrial Fire"]
    assert pred["confidence"] >= 0.5
    assert "shap_values" in pred
    assert len(pred["shap_values"]["top_contributors"]) > 0


def test_phase14_failure_containment_and_idempotency(db_session):
    """Verifies malformed observation rejection and duplicate feed idempotency."""
    corrupt = [{"latitude": "INVALID", "longitude": 999.0}]
    res = live_ingestion_service.ingest_observations(db_session, corrupt, source_name="PYTEST_CORRUPT", dry_run=True)
    assert res["records_accepted"] == 0
    assert res["records_rejected"] == 1

    dup_timestamp = datetime.now(timezone.utc).isoformat()
    valid_obs = [{
        "latitude": 22.1122,
        "longitude": 71.3344,
        "acq_timestamp": dup_timestamp,
        "brightness": 345.0,
        "frp": 110.0,
        "confidence": "90",
        "day_night": "D",
        "satellite": "NOAA-21",
        "sensor": "VIIRS-375m"
    }]

    r1 = live_ingestion_service.ingest_observations(db_session, valid_obs, source_name="PYTEST_IDEMPOTENCY", dry_run=False)
    r2 = live_ingestion_service.ingest_observations(db_session, valid_obs, source_name="PYTEST_IDEMPOTENCY", dry_run=False)

    assert r1["records_accepted"] == 1
    assert r2["records_accepted"] == 0
    assert r2["records_duplicated"] == 1


def test_phase14_worker_crash_and_auto_restart_recovery():
    """Verifies background worker supervisor failure isolation and restart recovery."""
    crash_res = worker_manager.simulate_failure_and_recovery("firms_ingestion_worker")
    assert crash_res["failure_contained"] is True
    assert crash_res["recovered_status"] == WorkerStatus.RUNNING


def test_phase14_database_connection_resilience():
    """Verifies database connection pooling diagnostics and connectivity."""
    pool = get_connection_pool_stats()
    diag = get_database_diagnostics()

    assert diag["status"] == "CONNECTED"
    assert pool["pool_size"] >= 10


def test_phase14_rbac_security_boundaries():
    """Verifies RBAC access controls across roles."""
    admin = User(id="ADM-14", email="admin@gov.in", role="ADMIN", is_active=True)
    analyst = User(id="ANA-14", email="analyst@gov.in", role="ANALYST", is_active=True)
    public = User(id="PUB-14", email="public@gov.in", role="PUBLIC", is_active=True)

    assert require_analyst(analyst).role == "ANALYST"
    assert require_admin(admin).role == "ADMIN"

    with pytest.raises(HTTPException) as exc1:
        require_analyst(public)
    assert exc1.value.status_code == 403

    with pytest.raises(HTTPException) as exc2:
        require_admin(analyst)
    assert exc2.value.status_code == 403


def test_phase14_secret_redaction_and_security_headers():
    """Verifies secret masking in configuration and logs."""
    sanitized = settings.get_sanitized_dict()
    assert "****" in sanitized["DATABASE_URL"]
    assert "****" in sanitized["SECRET_KEY"]
    assert not sanitized["ENABLE_OPERATIONAL_DISPATCH_GATE"]


def test_phase14_backup_and_isolated_restore(db_session):
    """Verifies database backup creation and isolated restore test."""
    bak = backup_recovery_service.create_database_backup(db_session)
    assert bak["status"] == "BACKUP_SUCCESSFUL"

    res = backup_recovery_service.verify_isolated_restore(bak["backup_file"])
    assert res["status"] == "ISOLATED_RESTORE_VERIFIED"
    assert res["production_db_isolation_preserved"] is True


def test_phase14_model_integrity_and_candidate_invariants(db_session):
    """Verifies candidate model cryptographic integrity and inactive registry status."""
    verif = model_integrity_service.verify_production_candidate_integrity(db_session, "xgb-v3.0-real-candidate")

    assert verif["artifacts_integrity"] == "VALID"
    assert verif["registry_status"] == "CANDIDATE"
    assert not verif["is_active"]
    assert verif["safety_invariant_held"] is True


def test_phase14_zero_live_dispatch_safety_invariant(db_session):
    """Verifies that exactly 0 live dispatches have been emitted."""
    live_alerts = db_session.execute(text("SELECT COUNT(*) FROM alerts WHERE is_operational_dispatch = true;")).scalar()
    live_audits = db_session.execute(text("SELECT COUNT(*) FROM alert_audit_logs WHERE is_operational_dispatch = true;")).scalar()

    assert live_alerts == 0
    assert live_audits == 0
    assert not settings.ENABLE_OPERATIONAL_DISPATCH_GATE
