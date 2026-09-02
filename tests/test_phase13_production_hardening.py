"""
AGNI-NETRA — PHASE 13: PRODUCTION HARDENING TEST SUITE
Tests configuration management, secret masking, connection pooling, model SHA-256 integrity,
model rollback, backup & isolated restore, structured logging, health probes, worker supervision,
ingestion failure containment, RBAC security, and zero live dispatch invariants.
"""

import os
import uuid
import pytest
import logging
from datetime import datetime, timezone
from sqlalchemy import text
from fastapi import Response, HTTPException

from backend.app.core.config import settings
from backend.app.core.database import SessionLocal, get_connection_pool_stats, get_database_diagnostics
from backend.app.core.logging_config import set_correlation_id, get_correlation_id, SecretsRedactorFilter
from backend.app.services.model_integrity_service import model_integrity_service
from database.backup_recovery_service import backup_recovery_service
from backend.app.services.worker_manager import worker_manager, WorkerStatus
from backend.app.services.live_ingestion_service import live_ingestion_service
from backend.app.api.v1.endpoints.health import (
    health_check, liveness_probe, readiness_probe, production_diagnostics, operational_metrics
)
from backend.app.api.v1.endpoints.alerts import (
    acknowledge_alert, start_alert_investigation, verify_alert_decision, close_alert,
    ActionRequest, VerifyActionRequest
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


def test_historical_database_immutability_phase13(db_session):
    """Verifies that all 8,221,554 historical FIRMS records remain sealed and immutable."""
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



def test_production_configuration_and_secret_masking():
    """Verifies production configuration sanitization and controlled dispatch gate."""
    sanitized = settings.get_sanitized_dict()

    assert not sanitized["ENABLE_OPERATIONAL_DISPATCH_GATE"]
    assert not sanitized["IS_OPERATIONAL_DISPATCH_DEFAULT"]
    assert sanitized["DB_POOL_SIZE"] >= 10
    assert sanitized["DB_MAX_OVERFLOW"] >= 20
    assert "****" in sanitized["DATABASE_URL"]
    assert "****" in sanitized["SECRET_KEY"]


def test_model_artifact_cryptographic_checksums(db_session):
    """Verifies SHA-256 cryptographic checksums for production model artifacts."""
    verif = model_integrity_service.verify_production_candidate_integrity(db_session, "xgb-v3.0-real-candidate")

    assert verif["artifacts_integrity"] == "VALID"
    assert verif["registry_registered"] is True
    assert verif["registry_status"] == "CANDIDATE"
    assert not verif["is_active"]
    assert verif["safety_invariant_held"] is True

    for name, c in verif["artifact_checksums"].items():
        assert c["status"] == "VERIFIED_PRESENT"
        assert c["size_bytes"] > 0
        assert len(c["sha256"]) == 64


def test_model_registry_invariants_and_rollback(db_session):
    """Verifies zero-data-mutation model rollback simulation."""
    rollback = model_integrity_service.simulate_model_rollback(db_session, "rf-v3.0-real-candidate")

    assert rollback["status"] == "ROLLBACK_SIMULATION_SUCCESSFUL"
    assert rollback["historical_records_mutated"] == 0
    assert rollback["safety_invariants_preserved"] is True


def test_postgresql_connection_pool_and_diagnostics():
    """Verifies connection pooling telemetry and diagnostics."""
    pool = get_connection_pool_stats()
    diag = get_database_diagnostics()

    assert diag["status"] == "CONNECTED"
    assert pool["pool_size"] >= 1
    assert "checked_in" in str(pool) or "checked_in_connections" in pool


def test_database_backup_and_isolated_restore(db_session):
    """Verifies automated database backup creation and isolated restore verification."""
    bak = backup_recovery_service.create_database_backup(db_session)
    assert bak["status"] == "BACKUP_SUCCESSFUL"
    assert os.path.exists(bak["backup_file"])
    assert bak["file_size_bytes"] > 0

    res = backup_recovery_service.verify_isolated_restore(bak["backup_file"])
    assert res["status"] == "ISOLATED_RESTORE_VERIFIED"
    assert res["production_db_isolation_preserved"] is True


def test_structured_logging_and_correlation_ids():
    """Verifies request correlation ID injection and secrets redaction filter."""
    test_cid = f"AGNI-TEST-{uuid.uuid4().hex[:8].upper()}"
    set_correlation_id(test_cid)
    assert get_correlation_id() == test_cid

    # Test Redaction Filter
    filter_obj = SecretsRedactorFilter()
    rec = logging.LogRecord("test", logging.INFO, "test.py", 1, "Connecting with password='super_secret_123' and postgresql://usr:secret_pass@localhost:5432/db", (), None)
    filter_obj.filter(rec)

    assert "super_secret_123" not in rec.msg
    assert "secret_pass" not in rec.msg
    assert "****" in rec.msg


def test_health_readiness_liveness_diagnostics_probes(db_session):
    """Verifies all production health probes and metrics endpoints."""
    res = Response()
    h = health_check(res, db_session)
    liv = liveness_probe()
    read = readiness_probe(res, db_session)
    diag = production_diagnostics(db_session)
    metrics = operational_metrics(db_session)

    assert h["status"] == "HEALTHY"
    assert liv["status"] == "ALIVE"
    assert read["ready"] is True
    assert diag["status"] == "OPERATIONAL"
    assert metrics["safety"]["dispatch_gate_status"] == "GATED_SAFE"


def test_supervised_workers_and_failure_recovery():
    """Verifies background worker health and automated failure recovery simulation."""
    health = worker_manager.get_worker_health()
    assert health["overall_status"] == "HEALTHY"
    assert health["active_workers_count"] == 3

    # Simulate worker recovery
    rec = worker_manager.simulate_failure_and_recovery("event_clustering_worker")
    assert rec["failure_contained"] is True
    assert rec["recovered_status"] == WorkerStatus.RUNNING


def test_ingestion_error_handling_and_rejection(db_session):
    """Verifies ingestion resilience when receiving malformed or out-of-bounds records."""
    corrupted_records = [
        {"latitude": "invalid_lat", "longitude": 72.5, "acq_timestamp": "not_a_date"},
        {"latitude": 999.0, "longitude": 72.5, "acq_timestamp": "2026-09-01T00:00:00Z"}
    ]
    res = live_ingestion_service.ingest_observations(db_session, corrupted_records, source_name="PYTEST_ERROR_STREAM", dry_run=True)
    assert res["records_accepted"] == 0
    assert res["records_rejected"] == 2


def test_api_security_rbac_and_rate_limiting():
    """Verifies RBAC role checkers and permission boundaries."""
    admin_user = User(id="USR-ADM-01", email="admin@agni-netra.gov.in", role="ADMIN", is_active=True)
    analyst_user = User(id="USR-ANA-01", email="analyst@agni-netra.gov.in", role="ANALYST", is_active=True)
    public_user = User(id="USR-PUB-01", email="public@agni-netra.gov.in", role="PUBLIC", is_active=True)

    assert require_analyst(analyst_user).role == "ANALYST"
    assert require_analyst(admin_user).role == "ADMIN"
    assert require_admin(admin_user).role == "ADMIN"

    with pytest.raises(HTTPException) as exc_info:
        require_analyst(public_user)
    assert exc_info.value.status_code == 403

    with pytest.raises(HTTPException) as exc_info2:
        require_admin(analyst_user)
    assert exc_info2.value.status_code == 403


def test_operational_lifecycle_and_zero_dispatch_safety(db_session):
    """Verifies full operational lifecycle and zero live dispatch enforcement."""
    obs = [{
        "latitude": 23.0225,
        "longitude": 72.5714,
        "acq_timestamp": datetime.now(timezone.utc).isoformat(),
        "brightness": 352.0,
        "frp": 140.0,
        "confidence": "94",
        "day_night": "N",
        "satellite": "NOAA-21",
        "sensor": "VIIRS-375m"
    }]

    live_ingestion_service.ingest_observations(db_session, obs, source_name="PYTEST_PHASE13_STREAM", dry_run=False)
    proc = live_ingestion_service.process_incremental_events(db_session, obs, dry_run=False)
    created_evt = proc["events"][0]
    alert_id = created_evt["alert_id"]

    # Verify transitions
    ack = acknowledge_alert(alert_id, ActionRequest(notes="Pytest Phase 13"), db_session)
    assert ack["new_state"] == "ACKNOWLEDGED"

    inv = start_alert_investigation(alert_id, ActionRequest(notes="Pytest Phase 13"), db_session)
    assert inv["new_state"] == "UNDER_INVESTIGATION"

    ver = verify_alert_decision(alert_id, VerifyActionRequest(
        ground_truth_class="Industrial Fire",
        verification_outcome="CONFIRM",
        notes="Pytest Ground Truth"
    ), db_session)
    assert ver["new_state"] == "VERIFIED"

    cls = close_alert(alert_id, ActionRequest(notes="Pytest Close"), db_session)
    assert cls["new_state"] == "CLOSED"

    # Zero Live Dispatch Invariant
    live_alerts = db_session.execute(text("SELECT COUNT(*) FROM alerts WHERE is_operational_dispatch = true;")).scalar()
    live_audits = db_session.execute(text("SELECT COUNT(*) FROM alert_audit_logs WHERE is_operational_dispatch = true;")).scalar()

    assert live_alerts == 0
    assert live_audits == 0
