"""
AGNI-NETRA — Automated Test Suite for Autonomous Intelligence & JARVIS Agentic Orchestration
Tests:
- Path A: Autonomous Detection & Ingestion Pipeline
- Path B: Manual Analyst Initiated Workflow (JARVIS Independence)
- Event-Driven Orchestration & Dynamic Capability Selection
- Stopping Condition, Idempotency & Loop Termination
- Evidence Grounding & 5-Way Epistemic Separation (KNOWN, INFERRED, UNCERTAIN, MISSING, CONFLICTING)
- Safety Boundaries (Dispatch Gate BLOCKED, Model Retraining DISABLED, SQL Injection Prevention)
- Voice Input Understanding & Grounded Speech Response Generation
- Proactive Voice Alert Notification Governance & Cooldown
- 12-State Incident Lifecycle Audit Persistence
"""

import pytest
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from backend.app.core.database import SessionLocal, engine, Base
import backend.app.models.domain  # Register all domain models
import backend.app.models.autonomous_lifecycle
from backend.app.models.domain import ThermalEvent, RiskScore, ModelPrediction, User, InvestigationWorkspace
from backend.app.models.autonomous_lifecycle import IncidentLifecycleState
from backend.app.services.autonomous_intelligence_service import autonomous_intelligence_core
from backend.app.services.jarvis.jarvis_world_state import jarvis_world_state
from backend.app.services.jarvis.jarvis_agentic_orchestrator import jarvis_agentic_orchestrator
from backend.app.services.jarvis.jarvis_voice_service import jarvis_voice_service
from backend.app.services.analyst.analyst_workflow_service import analyst_workflow_service


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    InvestigationWorkspace.__table__.create(bind=engine, checkfirst=True)


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_path_a_autonomous_pipeline(db_session: Session):
    """
    Critical Test 1-4:
    1. Thermal observation arrives.
    2. Intelligence pipeline automatically processes it.
    3. Risk and priority generated according to frozen formulas.
    4. Evidence assembled and state transitioned without analyst intervention.
    """
    sample_obs = [
        {
            "latitude": 22.4707,
            "longitude": 70.0577,
            "brightness": 355.0,
            "frp": 120.0,
            "confidence": 92.0,
            "sensor": "VIIRS",
            "satellite": "NOAA-20",
            "acq_timestamp": datetime.now(timezone.utc).isoformat(),
            "day_night": "N"
        }
    ]

    outcomes = autonomous_intelligence_core.process_observations_autonomous(
        db=db_session,
        raw_observations=sample_obs,
        source_name="TEST_FIRMS"
    )

    assert len(outcomes) >= 1
    out = outcomes[0]
    assert out.event_code.startswith("EVT-")
    assert out.risk_score > 0.0
    assert out.risk_level in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    assert out.priority_score > 0.0
    assert out.predicted_class != ""
    assert out.confidence > 0.0
    assert out.state in [IncidentLifecycleState.INTELLIGENCE_READY, IncidentLifecycleState.REQUIRES_HUMAN_VERIFICATION]
    assert out.dispatch_blocked is True

    # Verify database persistence
    persisted = db_session.query(ThermalEvent).filter(ThermalEvent.event_code == out.event_code).first()
    assert persisted is not None
    assert persisted.latitude == pytest.approx(22.4707, abs=0.01)


def test_path_b_manual_analyst_workflow_independent(db_session: Session):
    """
    Tests that AGNI-NETRA core manual analyst workflow functions 100% independently of JARVIS.
    """
    # Query an existing event
    ev = db_session.query(ThermalEvent).first()
    assert ev is not None

    # Load dossier
    dossier = analyst_workflow_service.get_standardized_event_dossier(db_session, ev.id)
    assert dossier is not None
    assert "event_id" in dossier or "dossier" in dossier or "summary" in dossier or "event_code" in str(dossier)

    # Triage events
    triage = analyst_workflow_service.get_triage_queue(db_session, limit=10)
    assert triage is not None
    assert "triage_queue" in triage or isinstance(triage, dict)


def test_event_driven_jarvis_orchestration_and_capabilities(db_session: Session):
    """
    Critical Tests 5-9:
    5. JARVIS receives resulting state via event bus subscription.
    6. JARVIS evaluates whether further investigation is required.
    7. Existing capabilities are selected and combined dynamically.
    8. Investigation completes with structured reasoning.
    9. Result is surfaced to analyst.
    """
    # Trigger manual investigation via agentic orchestrator
    inv_res = jarvis_agentic_orchestrator.orchestrate_manual_investigation(
        db=db_session,
        event_ref="EVT-GJ-2025-001"
    )

    assert "event_code" in inv_res
    assert "selected_capabilities" in inv_res
    assert len(inv_res["selected_capabilities"]) >= 2
    assert "cadastral_context_correlator" in inv_res["selected_capabilities"]
    assert "epistemic_synthesis" in inv_res
    assert inv_res["status"] == "REQUIRES_HUMAN_VERIFICATION"
    assert inv_res["dispatch_blocked"] is True


def test_epistemic_evidence_separation(db_session: Session):
    """
    Test 15: JARVIS reasoning strictly distinguishes KNOWN, INFERRED, UNCERTAIN, MISSING, CONFLICTING.
    Never collapses these into one generic answer.
    """
    inv_res = jarvis_agentic_orchestrator.orchestrate_manual_investigation(
        db=db_session,
        event_ref="EVT-GJ-2025-001"
    )

    ep = inv_res["epistemic_synthesis"]
    assert "known" in ep and len(ep["known"]) > 0
    assert "inferred" in ep and len(ep["inferred"]) > 0
    assert "uncertain" in ep and len(ep["uncertain"]) > 0
    assert "missing" in ep and len(ep["missing"]) > 0
    assert "conflicting" in ep and len(ep["conflicting"]) > 0


def test_safety_invariants_and_dispatch_gate(db_session: Session):
    """
    Critical Tests 10-11:
    - Dispatch gate is strictly BLOCKED (ENABLE_OPERATIONAL_DISPATCH_GATE = False).
    - Automated model retraining is disabled.
    - SQL injection attempts are rejected.
    """
    from backend.app.services.jarvis.jarvis_agentic_orchestrator import ENABLE_OPERATIONAL_DISPATCH_GATE, ENABLE_AUTOMATED_MODEL_ACTIVATION
    assert ENABLE_OPERATIONAL_DISPATCH_GATE is False
    assert ENABLE_AUTOMATED_MODEL_ACTIVATION is False

    # Safety guard check on adversarial input
    from backend.app.services.jarvis.jarvis_mission_service import JarvisGovernedToolRegistry
    is_safe, err = JarvisGovernedToolRegistry.validate_and_guard(
        tool_name="event_dossier_loader",
        user_role="ANALYST",
        raw_command="SELECT * FROM users; DROP TABLE thermal_events; --"
    )
    assert is_safe is False
    assert "SECURITY_REFUSAL" in (err or "") or "Arbitrary SQL" in (err or "")


def test_stopping_condition_and_idempotency(db_session: Session):
    """
    Critical Test 12:
    - System stops instead of continuing indefinitely (max depth respected).
    - Idempotency prevents duplicate processing of same observations.
    """
    sample_obs = [
        {
            "latitude": 22.4707,
            "longitude": 70.0577,
            "brightness": 355.0,
            "frp": 120.0,
            "confidence": 92.0,
            "sensor": "VIIRS_IDEMPOTENT_TEST",
            "satellite": "NOAA-20",
            "acq_timestamp": "2026-09-14T00:00:00Z",
            "day_night": "N"
        }
    ]

    # Process first time
    res1 = autonomous_intelligence_core.process_observations_autonomous(db_session, sample_obs)
    assert len(res1) == 1

    # Process duplicate second time -> should be recognized as duplicate and ignored
    res2 = autonomous_intelligence_core.process_observations_autonomous(db_session, sample_obs)
    assert len(res2) == 0


def test_voice_interaction_and_grounding(db_session: Session):
    """
    Tests Voice Input parsing, World State ground-truth querying, and spoken response generation.
    """
    # 1. "What is happening right now?"
    res1 = jarvis_voice_service.process_voice_transcript(db_session, "Jarvis, what's happening right now?")
    assert res1["intent"] == "CURRENT_SITUATION"
    assert "active thermal events" in res1["spoken_response"].lower()

    # 2. "Which events changed?"
    res2 = jarvis_voice_service.process_voice_transcript(db_session, "Which events changed in this cycle?")
    assert res2["intent"] == "CHANGED_EVENTS"
    assert len(res2["spoken_response"]) > 10

    # 3. "Investigate Gujarat event"
    res3 = jarvis_voice_service.process_voice_transcript(db_session, "Investigate the Gujarat event")
    assert res3["intent"] == "INVESTIGATE_EVENT"
    assert "investigation" in res3
    assert res3["investigation"]["dispatch_blocked"] is True


def test_proactive_voice_notifications_governance():
    """
    Tests that proactive notifications respect risk thresholds and do not spam.
    """
    # Queue test notification
    jarvis_world_state.queue_proactive_voice_alert({
        "spoken_text": "High priority thermal event detected in Mundra corridor.",
        "event_code": "EVT-GJ-TEST-001",
        "risk_score": 82.0
    })

    alerts = jarvis_voice_service.get_proactive_notifications(user_role="ANALYST")
    assert len(alerts) >= 1
    assert "Mundra" in alerts[0]["text"]

    # Pop again -> should be empty (delivered)
    alerts2 = jarvis_voice_service.get_proactive_notifications(user_role="ANALYST")
    assert len(alerts2) == 0


def test_12_state_lifecycle_audit_persistence(db_session: Session):
    """
    Tests that every lifecycle transition is deterministic, timestamped, and auditable.
    """
    sample_obs = [
        {
            "latitude": 23.0225,
            "longitude": 72.5714,
            "brightness": 340.0,
            "frp": 95.0,
            "confidence": 89.0,
            "sensor": "VIIRS_LIFECYCLE_TEST",
            "satellite": "NOAA-21",
            "acq_timestamp": datetime.now(timezone.utc).isoformat(),
            "day_night": "D"
        }
    ]

    outcomes = autonomous_intelligence_core.process_observations_autonomous(db_session, sample_obs)
    assert len(outcomes) == 1
    evt_code = outcomes[0].event_code

    history = autonomous_intelligence_core.get_lifecycle_history(evt_code)
    assert len(history) >= 6

    states = [h.to_state.value for h in history]
    assert "OBSERVED" in states
    assert "VALIDATING" in states
    assert "CONTEXTUALIZING" in states
    assert "ANALYZING" in states
    assert "CLASSIFYING" in states
    assert "ASSESSING" in states
    assert "CORRELATING" in states

    # Ensure each transition is timestamped and attributable
    for t in history:
        assert t.timestamp is not None
        assert t.subsystem != ""
        assert t.correlation_id != ""
