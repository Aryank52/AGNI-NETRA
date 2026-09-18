"""
AGNI-NETRA — WP1 Resilience & JARVIS Observer Test Suite
Comprehensive testing of WP1 hardened proactive intelligence core & JARVIS Observer:

Scenarios:
1. Duplicate observations rejection & idempotency
2. Worker restart recovery (transitions and investigation workspaces persisted & retrievable)
3. Partial failure in batch (malformed coordinates skipped; tool fallback)
4. Stale data (>48 hours observation age handled cleanly with decayed recency)
5. Missing context (uncataloged facility and missing baseline handled without hallucination)
6. JARVIS unavailable (failing observer subscriber does not crash core ingestion pipeline)
7. Observer endpoints (GET /api/v1/jarvis/observer/status, GET /api/v1/jarvis/missions)
8. Governed safety gates (dispatch blocked, automated model activation disabled)
"""

import uuid
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.main import app
from backend.app.core.database import SessionLocal, engine
from backend.app.models.domain import (
    ThermalEvent, ThermalDetection, IncidentLifecycleTransitionRecord,
    InvestigationWorkspace
)
from backend.app.models.autonomous_lifecycle import IncidentLifecycleState
from backend.app.services.autonomous_intelligence_service import autonomous_intelligence_core
from backend.app.services.pipeline_service import pipeline_service
from backend.app.services.jarvis.jarvis_agentic_orchestrator import jarvis_agentic_orchestrator
from data_pipeline.adapters.firms_adapter import FIRMSAdapter

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_tables():
    InvestigationWorkspace.__table__.create(bind=engine, checkfirst=True)
    IncidentLifecycleTransitionRecord.__table__.create(bind=engine, checkfirst=True)


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# =========================================================================
# Scenario 1: Duplicate observations rejection & idempotency
# =========================================================================
def test_scenario_1_duplicate_observations_idempotency(db_session: Session):
    """
    Submitting duplicate raw observations in identical locations must not crash
    and must execute idempotently without duplicating events ungracefully.
    """
    unique_tag = uuid.uuid4().hex[:6].upper()
    lat, lon = 23.2156, 70.4567

    obs = [
        {
            "latitude": lat,
            "longitude": lon,
            "brightness": 350.0,
            "frp": 95.0,
            "confidence": 90.0,
            "sensor": "VIIRS",
            "satellite": "NOAA-20",
            "acq_timestamp": datetime.now(timezone.utc).isoformat(),
            "day_night": "N"
        }
    ]

    # First pass
    outcomes_1 = autonomous_intelligence_core.process_observations_autonomous(
        db=db_session,
        raw_observations=obs,
        source_name=f"IDEMP_TEST_1_{unique_tag}"
    )
    assert len(outcomes_1) >= 1
    code_1 = outcomes_1[0].event_code

    # Second pass with exact duplicate
    outcomes_2 = autonomous_intelligence_core.process_observations_autonomous(
        db=db_session,
        raw_observations=obs,
        source_name=f"IDEMP_TEST_2_{unique_tag}"
    )
    # Deduplication drops identical duplicate observation
    assert len(outcomes_2) == 0

    # Ingestion via pipeline_service CSV adapter duplicate checking
    csv_payload = f"""latitude,longitude,bright_ti4,scan,track,acq_date,acq_time,satellite,confidence,version,bright_ti5,frp,daynight
{lat},{lon},350.0,0.4,0.4,2026-09-02,0300,N,h,2.0NRT,295.0,95.0,N
{lat},{lon},350.0,0.4,0.4,2026-09-02,0300,N,h,2.0NRT,295.0,95.0,N
"""
    adapter = FIRMSAdapter()
    parsed_obs = adapter.parse_csv_content(csv_payload, source_name=f"IDEMP_CSV_{unique_tag}", is_demo=False)
    # Adapter parses both, but clustering groups them into the same cluster
    res = pipeline_service.process_observations(db_session, parsed_obs, source_name=f"IDEMP_FIRMS_{unique_tag}")
    assert res["status"] == "SUCCESS"
    assert res["events_created"] >= 1


# =========================================================================
# Scenario 2: Worker restart recovery
# =========================================================================
def test_scenario_2_worker_restart_recovery(db_session: Session):
    """
    Transitions and InvestigationWorkspace instances must be persisted to the DB
    and retrievable in a subsequent fresh session simulating worker restart.
    """
    unique_tag = uuid.uuid4().hex[:6].upper()
    event_code = f"EVT-RECOVERY-{unique_tag}"

    # Record transition with explicit db session
    rec = autonomous_intelligence_core.record_transition(
        event_id=event_code,
        from_state=IncidentLifecycleState.OBSERVED,
        to_state=IncidentLifecycleState.INTELLIGENCE_READY,
        subsystem="PROACTIVE_RECOVERY_TEST",
        rationale="Worker restart resilience test transition",
        db=db_session
    )
    assert rec is not None
    db_session.commit()


    # Simulate worker crash by closing db_session and opening a brand-new session
    fresh_session = SessionLocal()
    try:
        persisted = fresh_session.query(IncidentLifecycleTransitionRecord).filter(
            IncidentLifecycleTransitionRecord.event_id == event_code
        ).all()
        assert len(persisted) >= 1
        assert persisted[0].to_state == IncidentLifecycleState.INTELLIGENCE_READY.value
        assert persisted[0].subsystem == "PROACTIVE_RECOVERY_TEST"

        # Also verify InvestigationWorkspace recovery
        workspace = InvestigationWorkspace(
            investigation_id=f"INV-{event_code}",
            session_id=f"sess-{unique_tag}",
            created_by="JARVIS_OBSERVER",
            user_role="SYSTEM",
            status="REQUIRES_HUMAN_REVIEW",
            primary_objective="High risk flaring in industrial corridor",
            target_event_id=event_code,
            evidence_summary={
                "known": ["Thermal emission detected"],
                "inferred": ["Likely chemical facility"],
                "uncertain": [],
                "missing": [],
                "conflicting": []
            },
            verification_status="REQUIRES_HUMAN_REVIEW"
        )
        fresh_session.add(workspace)
        fresh_session.commit()

        # Retrieve in yet another fresh session
        another_session = SessionLocal()
        try:
            recovered_ws = another_session.query(InvestigationWorkspace).filter(
                InvestigationWorkspace.target_event_id == event_code
            ).first()
            assert recovered_ws is not None
            assert recovered_ws.status == "REQUIRES_HUMAN_REVIEW"
            assert "known" in recovered_ws.evidence_summary
            assert recovered_ws.evidence_summary["known"] == ["Thermal emission detected"]
        finally:
            another_session.close()

    finally:
        fresh_session.close()


# =========================================================================
# Scenario 3: Partial failure in batch
# =========================================================================
def test_scenario_3_partial_failure_in_batch(db_session: Session):
    """
    Ingestion batch containing malformed / out-of-bounds coordinates alongside
    valid coordinates must skip malformed items without crashing the valid batch.
    """
    mixed_observations = [
        # Valid observation
        {
            "latitude": 21.1959,
            "longitude": 72.8302,
            "brightness": 340.0,
            "frp": 60.0,
            "confidence": 85.0,
            "sensor": "VIIRS",
            "satellite": "NOAA-20",
            "acq_timestamp": datetime.now(timezone.utc).isoformat(),
            "day_night": "N"
        },
        # Invalid / Out-of-bounds coordinates (lat 999.0)
        {
            "latitude": 999.0,
            "longitude": -500.0,
            "brightness": 340.0,
            "frp": 60.0,
            "confidence": 85.0,
            "sensor": "VIIRS",
            "satellite": "NOAA-20",
            "acq_timestamp": datetime.now(timezone.utc).isoformat(),
            "day_night": "N"
        },
        # Invalid None coordinate
        {
            "latitude": None,
            "longitude": 72.8302,
            "brightness": 340.0,
            "frp": 60.0,
            "confidence": 85.0,
            "sensor": "VIIRS",
            "satellite": "NOAA-20",
            "acq_timestamp": datetime.now(timezone.utc).isoformat(),
            "day_night": "N"
        }
    ]

    outcomes = autonomous_intelligence_core.process_observations_autonomous(
        db=db_session,
        raw_observations=mixed_observations,
        source_name="TEST_PARTIAL_FAILURE"
    )

    # Valid observation must have been processed successfully
    assert len(outcomes) >= 1
    valid_outcome = outcomes[0]
    valid_evt = db_session.query(ThermalEvent).filter(
        ThermalEvent.event_code == valid_outcome.event_code
    ).first()
    assert valid_evt is not None
    assert valid_evt.latitude == pytest.approx(21.1959, abs=0.01)
    assert valid_evt.longitude == pytest.approx(72.8302, abs=0.01)



# =========================================================================
# Scenario 4: Stale data (>48 hours observation age)
# =========================================================================
def test_scenario_4_stale_data_handling(db_session: Session):
    """
    Thermal observations older than 48 hours must be processed cleanly;
    time recency scores decay without divide-by-zero or timestamp parsing failures.
    """
    stale_timestamp = (datetime.now(timezone.utc) - timedelta(hours=72)).isoformat()

    stale_obs = [
        {
            "latitude": 22.4707,
            "longitude": 70.0577,
            "brightness": 320.0,
            "frp": 40.0,
            "confidence": 70.0,
            "sensor": "MODIS",
            "satellite": "Terra",
            "acq_timestamp": stale_timestamp,
            "day_night": "D"
        }
    ]

    outcomes = autonomous_intelligence_core.process_observations_autonomous(
        db=db_session,
        raw_observations=stale_obs,
        source_name="TEST_STALE_DATA"
    )

    assert len(outcomes) >= 1
    out = outcomes[0]
    assert out.event_code.startswith("EVT-")
    # Stale observation risk must still be calculated cleanly (bounded [0, 100])
    assert 0.0 <= out.risk_score <= 100.0


# =========================================================================
# Scenario 5: Missing context (uncataloged facility and missing baseline)
# =========================================================================
def test_scenario_5_missing_context_uncataloged_facility(db_session: Session):
    """
    Observations in remote areas with no registered industrial facilities or baselines
    must be processed without hallucination or crashing; facility marked as UNCATALOGED.
    """
    # Thar desert remote coordinates
    remote_obs = [
        {
            "latitude": 27.5000,
            "longitude": 71.0000,
            "brightness": 310.0,
            "frp": 25.0,
            "confidence": 65.0,
            "sensor": "VIIRS",
            "satellite": "NOAA-20",
            "acq_timestamp": datetime.now(timezone.utc).isoformat(),
            "day_night": "N"
        }
    ]

    outcomes = autonomous_intelligence_core.process_observations_autonomous(
        db=db_session,
        raw_observations=remote_obs,
        source_name="TEST_REMOTE_LOCATION"
    )

    assert len(outcomes) >= 1
    out = outcomes[0]
    assert out.event_code.startswith("EVT-")
    # Facility should be None (uncataloged) in the database
    evt = db_session.query(ThermalEvent).filter(ThermalEvent.event_code == out.event_code).first()
    assert evt is not None
    assert evt.facility_id is None

    # Verify uncertainty tier handled cleanly without crashing
    assert out.uncertainty_tier in ["KNOWN", "UNCERTAIN", "MISSING"]



# =========================================================================
# Scenario 6: JARVIS unavailable
# =========================================================================
def test_scenario_6_jarvis_unavailable_pipeline_resilience(db_session: Session):
    """
    If JARVIS observer subscriber raises an unhandled exception or is offline,
    the core AGNI-NETRA pipeline must complete ingestion, ML classification,
    risk scoring, and DB persistence without failure.
    """
    # Inject a failing subscriber into autonomous_intelligence_core
    def failing_subscriber(event_code, outcome):
        raise RuntimeError("JARVIS Observer Subsystem Temporarily Offline!")

    autonomous_intelligence_core.subscribe(failing_subscriber)

    try:
        sample_obs = [
            {
                "latitude": 22.5000,
                "longitude": 70.1000,
                "brightness": 345.0,
                "frp": 80.0,
                "confidence": 90.0,
                "sensor": "VIIRS",
                "satellite": "NOAA-20",
                "acq_timestamp": datetime.now(timezone.utc).isoformat(),
                "day_night": "N"
            }
        ]

        # Ingestion must not raise RuntimeError even when subscriber fails
        outcomes = autonomous_intelligence_core.process_observations_autonomous(
            db=db_session,
            raw_observations=sample_obs,
            source_name="TEST_JARVIS_OFFLINE"
        )

        assert len(outcomes) >= 1
        assert outcomes[0].event_code.startswith("EVT-")
        assert outcomes[0].risk_score > 0.0

        # Verify DB persistence succeeded
        evt = db_session.query(ThermalEvent).filter(
            ThermalEvent.event_code == outcomes[0].event_code
        ).first()
        assert evt is not None
    finally:
        # Cleanup injected subscriber
        if failing_subscriber in autonomous_intelligence_core._subscribers:
            autonomous_intelligence_core._subscribers.remove(failing_subscriber)


# =========================================================================
# Scenario 7: Observer endpoints
# =========================================================================
def test_scenario_7_jarvis_observer_api_endpoints():
    """
    Verifies GET /api/v1/jarvis/observer/status and GET /api/v1/jarvis/missions.
    """
    # 1. Observer Status
    res = client.get("/api/v1/jarvis/observer/status")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ONLINE"
    assert data["is_master"] is True
    assert data["active_agent_count"] == 1
    assert data["agent_id"] == "JARVIS-MASTER-OBSERVER-01"
    assert data["consequential_actions_enabled"] is False
    assert data["operational_dispatch_gate_blocked"] is True
    assert data["automated_model_activation_blocked"] is True
    assert "investigation_threshold" in data
    assert "total_observed_events" in data

    # 2. Missions
    res_missions = client.get("/api/v1/jarvis/missions?limit=10")
    assert res_missions.status_code == 200
    m_data = res_missions.json()
    assert "count" in m_data
    assert "missions" in m_data
    assert isinstance(m_data["missions"], list)


# =========================================================================
# Scenario 8: Governed safety gates permanently enforced
# =========================================================================
def test_scenario_8_governed_safety_gates_permanently_enforced(db_session: Session):
    """
    Ensures ENABLE_OPERATIONAL_DISPATCH_GATE = False and ENABLE_AUTOMATED_MODEL_ACTIVATION = False.
    """
    from backend.app.core.config import settings

    # Operational dispatch gate
    assert hasattr(settings, "ENABLE_OPERATIONAL_DISPATCH_GATE")
    assert settings.ENABLE_OPERATIONAL_DISPATCH_GATE is False

    # Automated model activation
    assert hasattr(settings, "ENABLE_AUTOMATED_MODEL_ACTIVATION")
    assert settings.ENABLE_AUTOMATED_MODEL_ACTIVATION is False

    # Verify via jarvis orchestrator status
    obs_status = jarvis_agentic_orchestrator.get_observer_status()
    assert obs_status["operational_dispatch_gate_blocked"] is True
    assert obs_status["automated_model_activation_blocked"] is True
    assert obs_status["consequential_actions_enabled"] is False
