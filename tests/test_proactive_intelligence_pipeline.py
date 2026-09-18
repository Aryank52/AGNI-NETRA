"""
AGNI-NETRA — Proactive Intelligence Event Engine Test Suite (WP1 Hardening)
Verifies:
1. Unified proactive ingestion pipeline bridging observations through 8-stage lifecycle.
2. Full lifecycle transition recording in memory and persistence in incident_lifecycle_transitions DB table.
3. GET /api/v1/events/{event_id}/lifecycle endpoint response format and traceability.
4. Permanent blocking of automated operational dispatch (ENABLE_OPERATIONAL_DISPATCH_GATE = False).
5. Idempotent deduplication behavior on identical satellite observations.
6. Maintenance tasks execution (baseline update, anomaly analysis, alert generation).
"""

import uuid
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.main import app
from backend.app.core.database import SessionLocal
from backend.app.models.domain import (
    ThermalEvent, ThermalDetection, Alert, IndustrialFacility,
    IncidentLifecycleTransitionRecord
)
from backend.app.models.autonomous_lifecycle import IncidentLifecycleState
from backend.app.services.pipeline_service import pipeline_service
from backend.app.services.autonomous_intelligence_service import autonomous_intelligence_core
from backend.app.tasks.maintenance_tasks import (
    baseline_update_job, anomaly_analysis_job, alert_generation_job
)
from data_pipeline.adapters.firms_adapter import FIRMSAdapter

client = TestClient(app)


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_unified_proactive_pipeline_8_stage_lifecycle(db_session: Session):
    """
    Test 1: Verify that pipeline_service.process_observations executes through the
    proactive intelligence engine and persists the complete 8-stage lifecycle to DB.
    """
    unique_tag = uuid.uuid4().hex[:6].upper()
    csv_payload = f"""latitude,longitude,bright_ti4,scan,track,acq_date,acq_time,satellite,confidence,version,bright_ti5,frp,daynight
22.4820,70.0650,362.0,0.4,0.4,2026-09-01,0200,N,h,2.0NRT,298.0,145.0,N
22.4825,70.0655,358.0,0.4,0.4,2026-09-01,0200,N,h,2.0NRT,296.0,110.0,N
"""
    adapter = FIRMSAdapter()
    observations = adapter.parse_csv_content(csv_payload, source_name=f"TEST_WP1_{unique_tag}", is_demo=False)
    assert len(observations) == 2

    # Process observations through unified pipeline service
    result = pipeline_service.process_observations(
        db=db_session,
        observations=observations,
        source_name=f"TEST_FIRMS_{unique_tag}"
    )

    assert result["status"] == "SUCCESS"
    assert result["events_created"] >= 1
    assert result["detections_stored"] == 2
    assert "stage_timings_ms" in result
    timings = result["stage_timings_ms"]
    for key in ["ingestion_ms", "clustering_ms", "gis_enrichment_ms", "persistence_ms", "ml_inference_ms", "shap_explanation_ms", "risk_evaluation_ms", "db_commit_ms", "total_processing_ms"]:
        assert key in timings

    created_event_id = result["event_ids"][0]
    created_event = db_session.query(ThermalEvent).filter(ThermalEvent.id == created_event_id).first()
    assert created_event is not None
    assert created_event.lifecycle_state in [
        IncidentLifecycleState.INTELLIGENCE_READY.value,
        IncidentLifecycleState.REQUIRES_HUMAN_VERIFICATION.value
    ]

    # Verify lifecycle transitions persisted in DB table
    db_transitions = db_session.query(IncidentLifecycleTransitionRecord).filter(
        IncidentLifecycleTransitionRecord.event_id == created_event.event_code
    ).order_by(IncidentLifecycleTransitionRecord.created_at.asc()).all()

    assert len(db_transitions) >= 6
    transition_states = [t.to_state for t in db_transitions]
    assert "OBSERVED" in transition_states
    assert "VALIDATING" in transition_states
    assert "CONTEXTUALIZING" in transition_states
    assert "ANALYZING" in transition_states
    assert "CLASSIFYING" in transition_states
    assert "ASSESSING" in transition_states
    assert "CORRELATING" in transition_states

    # Verify transition metadata and traceability
    for rec in db_transitions:
        assert rec.correlation_id is not None
        assert rec.correlation_id.startswith("pipe-") or rec.correlation_id.startswith("auto-")
        assert rec.subsystem is not None and len(rec.subsystem) > 0
        assert rec.rationale is not None and len(rec.rationale) > 0


def test_get_event_lifecycle_endpoint(db_session: Session):
    """
    Test 2: Verify GET /api/v1/events/{event_id}/lifecycle returns full trace lineage.
    """
    event = db_session.query(ThermalEvent).first()
    assert event is not None, "At least one event should exist in test database"

    resp = client.get(f"/api/v1/events/{event.id}/lifecycle")
    assert resp.status_code == 200
    data = resp.json()

    assert data["event_id"] == event.id
    assert data["event_code"] == event.event_code
    assert "current_lifecycle_state" in data
    assert "transition_count" in data
    assert "transitions" in data
    assert isinstance(data["transitions"], list)

    # Also test by event_code lookup
    resp_code = client.get(f"/api/v1/events/{event.event_code}/lifecycle")
    assert resp_code.status_code == 200

    # Test 404 on nonexistent event
    resp_404 = client.get("/api/v1/events/NONEXISTENT-EVENT-ID-99999/lifecycle")
    assert resp_404.status_code == 404


def test_safety_invariants_operational_dispatch_blocked(db_session: Session):
    """
    Test 3: Verify strict non-negotiable safety invariant:
    Live operational dispatch is permanently disabled and is_operational_dispatch == False.
    """
    alerts = db_session.query(Alert).all()
    for alert in alerts:
        assert alert.is_operational_dispatch is False, f"Alert {alert.id} has operational dispatch enabled!"

    # Ingestion test with critical FRP to ensure dispatch is still blocked
    critical_obs = [
        {
            "latitude": 22.3550,
            "longitude": 69.8650,
            "brightness": 450.0,
            "frp": 2500.0,
            "confidence": 99.0,
            "sensor": "VIIRS_SAFETY_CHECK",
            "satellite": "NOAA-20",
            "acq_timestamp": datetime.now(timezone.utc).isoformat(),
            "day_night": "N"
        }
    ]

    outcomes = autonomous_intelligence_core.process_observations_autonomous(
        db=db_session,
        raw_observations=critical_obs,
        source_name="CRITICAL_SAFETY_TEST"
    )

    if outcomes:
        for out in outcomes:
            assert out.dispatch_blocked is True
            alert_rec = db_session.query(Alert).filter(Alert.event_id == out.event_id).first()
            if alert_rec:
                assert alert_rec.is_operational_dispatch is False


def test_idempotent_deduplication(db_session: Session):
    """
    Test 4: Verify duplicate observations are rejected gracefully by fingerprint tracking.
    """
    fixed_ts = "2026-09-01T12:00:00+00:00"
    duplicate_obs = [
        {
            "latitude": 23.5000,
            "longitude": 71.2000,
            "brightness": 330.0,
            "frp": 45.0,
            "confidence": 80.0,
            "sensor": "VIIRS_DEDUP_TEST",
            "satellite": "NOAA-20",
            "acq_timestamp": fixed_ts,
            "day_night": "D"
        }
    ]

    # First pass: processes 1 observation
    res1 = autonomous_intelligence_core.process_observations_autonomous(
        db=db_session,
        raw_observations=duplicate_obs,
        source_name="DEDUP_SOURCE"
    )
    assert len(res1) == 1

    # Second pass with identical fingerprint: deduplicated, 0 new events
    res2 = autonomous_intelligence_core.process_observations_autonomous(
        db=db_session,
        raw_observations=duplicate_obs,
        source_name="DEDUP_SOURCE"
    )
    assert len(res2) == 0


def test_maintenance_tasks_bounded_execution():
    """
    Test 5: Verify maintenance background tasks execute bounded logic without errors.
    """
    # 1. Baseline update job
    base_res = baseline_update_job()
    assert base_res["status"] == "SUCCESS"
    assert "facilities_evaluated" in base_res

    # 2. Anomaly analysis job
    anom_res = anomaly_analysis_job()
    assert anom_res["status"] == "SUCCESS"
    assert "active_events_checked" in anom_res

    # 3. Alert generation job
    alert_res = alert_generation_job()
    assert alert_res["status"] == "SUCCESS"
    assert "events_evaluated" in alert_res
