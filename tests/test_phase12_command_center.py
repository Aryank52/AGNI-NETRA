"""
AGNI-NETRA — PHASE 12: COMMAND CENTER & FRONTEND INTEGRATION TEST SUITE
Tests the Command Center APIs, GeoJSON pipeline, Tri-Tier queues, 7-layer dossiers,
analyst lifecycle transitions, administrative drill-downs, and production safety invariants.
"""

import pytest
from datetime import datetime, timezone
from sqlalchemy import text

from backend.app.core.database import SessionLocal
from backend.app.models.domain import Alert
from backend.app.services.live_ingestion_service import live_ingestion_service
from backend.app.services.alert_workflow_service import alert_workflow_service
from backend.app.api.v1.endpoints.analytics import get_command_center_overview, get_operational_trends
from backend.app.api.v1.endpoints.events import get_thermal_events_geojson
from backend.app.api.v1.endpoints.alerts import (
    list_operational_alerts, get_alert_investigation_dossier,
    acknowledge_alert, start_alert_investigation, verify_alert_decision, close_alert,
    ActionRequest, VerifyActionRequest
)
from backend.app.api.v1.endpoints.geography import list_states, list_districts


@pytest.fixture(scope="module")
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_historical_database_immutability_phase12(db_session):
    """Verifies that all 8,221,554 historical FIRMS records remain sealed and immutable."""
    c_2022_off = db_session.execute(text("SELECT COUNT(*) FROM thermal_detections WHERE acq_timestamp >= '2022-01-01' AND acq_timestamp < '2023-01-01' AND is_demo = false;")).scalar()
    c_2022_pil = db_session.execute(text("SELECT COUNT(*) FROM thermal_detections WHERE acq_timestamp >= '2022-01-01' AND acq_timestamp < '2023-01-01' AND is_demo = true;")).scalar()
    c_2023_off = db_session.execute(text("SELECT COUNT(*) FROM thermal_detections WHERE acq_timestamp >= '2023-01-01' AND acq_timestamp < '2024-01-01' AND is_demo = false;")).scalar()
    c_2024_rec = db_session.execute(text("SELECT COUNT(*) FROM thermal_detections WHERE acq_timestamp >= '2024-01-01' AND acq_timestamp < '2025-01-01';")).scalar()
    c_2025_off = db_session.execute(text("SELECT COUNT(*) FROM thermal_detections WHERE acq_timestamp >= '2025-01-01' AND acq_timestamp < '2026-01-01';")).scalar()
    c_2026_off = db_session.execute(text("SELECT COUNT(*) FROM thermal_detections WHERE acq_timestamp >= '2026-01-01';")).scalar()

    assert c_2022_off == 1_274_383
    assert c_2022_pil == 210_000
    assert c_2023_off == 1_244_759
    assert c_2024_rec == 1_711_626
    assert c_2025_off == 2_007_898
    assert c_2026_off >= 1_771_080


def test_model_registry_safety_invariants_phase12(db_session):
    """Verifies production candidate model registry invariants."""
    candidates = db_session.execute(text("""
        SELECT version, status, is_active 
        FROM ml_model_registry 
        WHERE version IN ('xgb-v3.0-real-candidate', 'rf-v3.0-real-candidate');
    """)).fetchall()

    assert len(candidates) >= 2
    for c in candidates:
        assert c[1] == "CANDIDATE"
        assert not c[2]


def test_command_center_telemetry_endpoint(db_session):
    """Verifies the /api/v1/analytics/command-center payload structure."""
    cc = get_command_center_overview(db_session)
    assert cc["status"] == "OPERATIONAL"
    assert "kpis" in cc
    assert cc["kpis"]["total_live_events"] > 0
    assert "alert_queues" in cc
    assert cc["alert_queues"]["tier_1_auto_dispatch_candidate"] >= 0
    assert cc["alert_queues"]["tier_2_analyst_review"] >= 0
    assert cc["alert_queues"]["tier_3_uncertainty"] >= 0
    assert cc["safety_invariants"]["is_operational_dispatch"] is False
    assert cc["safety_invariants"]["live_dispatches_emitted"] == 0
    assert cc["safety_invariants"]["dispatch_gate_status"] == "GATED_SAFE"


def test_geojson_feature_collection_pipeline(db_session):
    """Verifies MapLibre GeoJSON FeatureCollection pipeline."""
    geojson = get_thermal_events_geojson(db=db_session, is_demo=None)
    assert geojson["type"] == "FeatureCollection"
    assert len(geojson["features"]) > 0

    first_feat = geojson["features"][0]
    assert first_feat["type"] == "Feature"
    assert first_feat["geometry"]["type"] == "Point"
    assert len(first_feat["geometry"]["coordinates"]) == 2
    props = first_feat["properties"]
    assert "event_code" in props
    assert "predicted_class" in props
    assert "confidence" in props
    assert "risk_score" in props
    assert "provenance" in props


def test_tri_tier_alert_queues_and_priority(db_session):
    """Verifies Tri-Tier queue filtering and priority scoring."""
    t1 = list_operational_alerts(tier="TIER_1_AUTO_DISPATCH_CANDIDATE", sort_by="priority", limit=20, db=db_session)
    t2 = list_operational_alerts(tier="TIER_2_ANALYST_REVIEW_QUEUE", sort_by="priority", limit=20, db=db_session)
    t3 = list_operational_alerts(tier="TIER_3_UNCERTAINTY_QUEUE", sort_by="priority", limit=20, db=db_session)

    assert "alerts" in t1
    assert "alerts" in t2
    assert "alerts" in t3

    # Check priority ordering
    if len(t1["alerts"]) >= 2:
        for i in range(len(t1["alerts"]) - 1):
            assert t1["alerts"][i]["priority_score"] >= t1["alerts"][i+1]["priority_score"] - 0.01


def test_investigation_dossier_aggregation(db_session):
    """Verifies complete 7-layer evidence dossier structure."""
    latest_alert = db_session.query(Alert).order_by(Alert.created_at.desc()).first()
    assert latest_alert is not None

    dossier = get_alert_investigation_dossier(latest_alert.id, db_session)
    assert "alert_metadata" in dossier
    assert "thermal_event" in dossier
    assert "firms_observations" in dossier
    assert "ml_inference" in dossier
    assert "risk_assessment" in dossier
    assert "evidence_sources" in dossier
    assert "audit_trail" in dossier
    assert dossier["safety_invariants"]["is_operational_dispatch"] is False


def test_analyst_decision_lifecycle_workflow(db_session):
    """Verifies full state transition lifecycle: NEW -> ACKNOWLEDGED -> UNDER_INVESTIGATION -> VERIFIED -> CLOSED."""
    # Ingest test observation
    obs = [{
        "latitude": 21.7051,
        "longitude": 72.9959,
        "acq_timestamp": datetime.now(timezone.utc).isoformat(),
        "brightness": 348.0,
        "frp": 120.0,
        "confidence": "90",
        "day_night": "N",
        "satellite": "NOAA-21",
        "sensor": "VIIRS-375m"
    }]
    live_ingestion_service.ingest_observations(db_session, obs, source_name="PYTEST_LIFECYCLE_STREAM", dry_run=False)
    proc = live_ingestion_service.process_incremental_events(db_session, obs, dry_run=False)
    created_evt = proc["events"][0]
    alert_id = created_evt["alert_id"]

    # 1. Acknowledge
    ack = acknowledge_alert(alert_id, ActionRequest(notes="Pytest Acknowledge"), db_session)
    assert ack["new_state"] == "ACKNOWLEDGED"

    # 2. Investigate
    inv = start_alert_investigation(alert_id, ActionRequest(notes="Pytest Investigate"), db_session)
    assert inv["new_state"] == "UNDER_INVESTIGATION"

    # 3. Verify
    ver = verify_alert_decision(alert_id, VerifyActionRequest(
        ground_truth_class="Industrial Fire",
        verification_outcome="CONFIRM",
        notes="Pytest Ground Truth Verification"
    ), db_session)
    assert ver["new_state"] == "VERIFIED"

    # 4. Close
    cls = close_alert(alert_id, ActionRequest(notes="Pytest Close"), db_session)
    assert cls["new_state"] == "CLOSED"

    # Verify audit persistence
    audit_count = db_session.execute(text("SELECT COUNT(*) FROM alert_audit_logs WHERE alert_id = :aid;"), {"aid": alert_id}).scalar()
    assert audit_count >= 4


def test_administrative_geography_drilldown(db_session):
    """Verifies administrative states and districts drill-down APIs."""
    states = list_states(db_session)
    assert len(states) >= 36

    districts = list_districts(state="Gujarat", db=db_session)
    assert len(districts) > 0


def test_operational_trends_endpoint(db_session):
    """Verifies the /api/v1/analytics/operational-trends endpoint."""
    trends = get_operational_trends(db_session)
    assert "classifications" in trends
    assert "state_analytics" in trends
    assert "audit_outcomes" in trends


def test_zero_live_dispatch_safety_invariant(db_session):
    """Audits entire platform for zero live dispatches."""
    live_alerts = db_session.execute(text("SELECT COUNT(*) FROM alerts WHERE is_operational_dispatch = true;")).scalar()
    live_audits = db_session.execute(text("SELECT COUNT(*) FROM alert_audit_logs WHERE is_operational_dispatch = true;")).scalar()
    assert live_alerts == 0
    assert live_audits == 0
