"""
AGNI-NETRA — PHASE 15: GO-LIVE READINESS & ACTIVATION TEST SUITE
Validates all 17 readiness pillars, database immutability, worker supervision,
model cryptographic integrity, RBAC boundaries, disaster recovery, and zero-dispatch safety gates.
"""

import os
import pytest
from datetime import datetime, timezone
from sqlalchemy import text
from fastapi import Response, HTTPException

from backend.app.core.config import settings
from backend.app.core.database import SessionLocal, get_connection_pool_stats, get_database_diagnostics, check_postgis_available
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
    health_check, liveness_probe, readiness_probe, production_diagnostics
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


def test_phase15_database_schema_and_immutability(db_session):
    """Verifies PostGIS extension, core tables, and sealed historical FIRMS partitions."""
    postgis_res = check_postgis_available()
    assert (postgis_res[0] if isinstance(postgis_res, (tuple, list)) else bool(postgis_res)) is True

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
    assert (int(row[0]) + int(row[1]) + int(row[2]) + int(row[3]) + int(row[4])) == 6_448_666


def test_phase15_operational_ingestion_and_idempotency(db_session):
    """Verifies 2026 operational stream ingestion and deterministic duplicate rejection."""
    ts = datetime.now(timezone.utc).isoformat()
    obs = [{
        "latitude": 21.8845,
        "longitude": 72.3321,
        "acq_timestamp": ts,
        "brightness": 360.0,
        "frp": 165.0,
        "confidence": "98",
        "day_night": "N",
        "satellite": "NOAA-21",
        "sensor": "VIIRS-375m"
    }]

    r1 = live_ingestion_service.ingest_observations(db_session, obs, source_name="PYTEST_P15_FEED", dry_run=False)
    r2 = live_ingestion_service.ingest_observations(db_session, obs, source_name="PYTEST_P15_FEED", dry_run=False)

    assert r1["records_accepted"] == 1
    assert r2["records_accepted"] == 0
    assert r2["records_duplicated"] == 1


def test_phase15_worker_supervision_and_probes(db_session):
    """Verifies background workers, liveness/readiness probes, and self-healing restart."""
    res = Response()
    live = liveness_probe()
    read = readiness_probe(res, db_session)
    health = worker_manager.get_worker_health()

    assert live["pid_responsive"] is True
    assert read["ready"] is True
    assert health["overall_status"] == "HEALTHY"

    # Worker crash & auto-restart simulation
    crash = worker_manager.simulate_failure_and_recovery("alert_evaluation_worker")
    assert crash["failure_contained"] is True
    assert crash["recovered_status"] == WorkerStatus.RUNNING


def test_phase15_model_cryptographic_lineage_and_contract(db_session):
    """Verifies SHA-256 signatures for candidate models and candidate registry invariant."""
    checksums = model_integrity_service.get_artifact_checksums()
    for name, info in checksums.items():
        assert info["status"] == "VERIFIED_PRESENT"
        assert len(info["sha256"]) == 64

    reg_verif = model_integrity_service.verify_production_candidate_integrity(db_session, "xgb-v3.0-real-candidate")
    assert reg_verif["registry_registered"] is True
    assert reg_verif["registry_status"] == "CANDIDATE"
    assert reg_verif["is_active"] is False
    assert reg_verif["safety_invariant_held"] is True


def test_phase15_e2e_inference_risk_routing_chain(db_session):
    """Verifies full inference pipeline: Features -> Calibrated XGBoost -> SHAP -> Risk -> Tri-Tier Routing."""
    obs = [{
        "latitude": 21.6110,
        "longitude": 72.1890,
        "acq_timestamp": datetime.now(timezone.utc).isoformat(),
        "brightness": 365.0,
        "frp": 210.0,
        "confidence": "99",
        "day_night": "N",
        "satellite": "NOAA-21",
        "sensor": "VIIRS-375m"
    }]

    live_ingestion_service.ingest_observations(db_session, obs, source_name="PYTEST_P15_INFERENCE", dry_run=False)
    proc = live_ingestion_service.process_incremental_events(db_session, obs, dry_run=False)
    evt = proc["events"][0]
    alert_id = evt["alert_id"]

    assert alert_id is not None
    assert evt.get("routing_tier") is not None

    sample_feature_dict = {
        "max_frp": 210.0,
        "avg_frp": 140.0,
        "frp_variance": 20.0,
        "avg_brightness": 365.0,
        "nearest_facility_distance_m": 120.0,
        "landcover_class": "Industrial",
        "persistence_score": 6.0,
        "recurrence_rate": 1.5,
        "day_night_ratio": 1.4,
        "baseline_deviation_ratio": 1.2,
        "industrial_context_score": 0.88
    }
    pred_res = thermal_predictor.predict(sample_feature_dict)
    dossier = alert_workflow_service.get_alert_investigation_dossier(db_session, alert_id)
    shap_features = pred_res.get("shap_top_features", pred_res.get("shap_feature_importance", []))
    if not shap_features:
        shap_wf = dossier.get("ml_inference", {}).get("shap_waterfall", {})
        shap_features = list(shap_wf.keys()) if isinstance(shap_wf, dict) else shap_wf
    assert len(shap_features) >= 3


def test_phase15_alert_lifecycle_and_rbac_guards(db_session):
    """Verifies analyst state machine transitions and RBAC role boundaries."""
    admin = User(id="USR-ADM-TEST", email="admin@gov.in", role="ADMIN", is_active=True)
    analyst = User(id="USR-ANA-TEST", email="analyst@gov.in", role="ANALYST", is_active=True)
    public = User(id="USR-PUB-TEST", email="citizen@public.in", role="PUBLIC", is_active=True)

    assert require_analyst(analyst).role == "ANALYST"
    assert require_admin(admin).role == "ADMIN"

    with pytest.raises(HTTPException) as exc_pub:
        require_analyst(public)
    assert exc_pub.value.status_code == 403

    with pytest.raises(HTTPException) as exc_adm:
        require_admin(analyst)
    assert exc_adm.value.status_code == 403

    # State Machine test on active alert
    active_alert = db_session.query(Alert).filter(Alert.status == "NEW").first()
    if active_alert:
        aid = active_alert.id
        s1 = acknowledge_alert(aid, ActionRequest(notes="Pytest ACK"), db_session)
        assert s1["new_state"] == "ACKNOWLEDGED"
        s2 = start_alert_investigation(aid, ActionRequest(notes="Pytest INV"), db_session)
        assert s2["new_state"] == "UNDER_INVESTIGATION"
        s3 = verify_alert_decision(aid, VerifyActionRequest(
            ground_truth_class="Industrial Fire",
            verification_outcome="CONFIRM",
            confidence=1.0,
            notes="Pytest Ground Truth Confirmed"
        ), db_session)
        assert s3["new_state"] == "VERIFIED"
        s4 = escalate_alert(aid, EscalateActionRequest(
            target_agency="State PCB",
            reason="EMISSION_SPIKE",
            notes="Pytest Escalation"
        ), db_session)
        assert s4["new_state"] == "ESCALATED"
        s5 = close_alert(aid, ActionRequest(notes="Pytest Close"), db_session)
        assert s5["new_state"] == "CLOSED"


def test_phase15_command_center_and_api_endpoints(db_session):
    """Verifies Command Center overview, GeoJSON feature collection, and diagnostics."""
    cc = get_command_center_overview(db=db_session)
    assert cc is not None

    res = Response()
    evts = get_thermal_events(res, db=db_session, limit=5)
    geojson = get_thermal_events_geojson(db=db_session)
    diag = production_diagnostics(db=db_session)

    assert geojson.get("type") == "FeatureCollection"
    assert diag["safety_invariants"]["dispatch_gate_enabled"] is False


def test_phase15_security_and_secret_redaction():
    """Verifies that all credentials, database URLs, and API tokens are redacted."""
    sanitized = settings.get_sanitized_dict()
    assert "****" in sanitized["DATABASE_URL"]
    assert "****" in sanitized["SECRET_KEY"]
    assert "****" in sanitized["S3_ACCESS_KEY"]
    assert "****" in sanitized["S3_SECRET_KEY"]


def test_phase15_backup_and_isolated_restore_verification(db_session):
    """Verifies disaster recovery backup creation and isolated restore verification."""
    bak = backup_recovery_service.create_database_backup(db_session)
    assert bak["status"] == "BACKUP_SUCCESSFUL"

    restore_res = backup_recovery_service.verify_isolated_restore(bak["backup_file"])
    assert restore_res["status"] == "ISOLATED_RESTORE_VERIFIED"
    assert restore_res["production_db_isolation_preserved"] is True


def test_phase15_simulated_model_rollback_safeguards(db_session):
    """Verifies zero-downtime model rollback simulation."""
    rollback = model_integrity_service.simulate_model_rollback(db_session, "xgb-v2.0-real-candidate")
    assert rollback["status"] == "ROLLBACK_SIMULATION_SUCCESSFUL"


def test_phase15_zero_dispatch_safety_invariant(db_session):
    """Verifies strict zero-dispatch safety invariant across alerts and audit logs."""
    assert settings.ENABLE_OPERATIONAL_DISPATCH_GATE is False
    assert settings.IS_OPERATIONAL_DISPATCH_DEFAULT is False

    live_alerts = db_session.execute(text("SELECT COUNT(*) FROM alerts WHERE is_operational_dispatch = true;")).scalar()
    live_audits = db_session.execute(text("SELECT COUNT(*) FROM alert_audit_logs WHERE is_operational_dispatch = true;")).scalar()

    assert live_alerts == 0
    assert live_audits == 0
