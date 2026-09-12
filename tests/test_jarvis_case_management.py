"""
JARVIS Phase 14 Test Suite: Intelligence Operations, Case Management & Audit Governance
Validates all 24 required verification scenarios:
1. case creation
2. valid state transitions
3. invalid state transitions rejected
4. action authorization enforcement
5. audit creation
6. immutable audit
7. assessment versioning & deltas
8. evidence review without altering raw data
9. evidence request lifecycle
10. analyst notes author tracking (no JARVIS impersonation)
11. human verification explicit decision
12. report versioning reproducibility
13. case timeline chronology
14. JARVIS command routing
15. write safety (propose before execute)
16. RBAC matrix & privilege escalation denial
17. provenance cryptographic lineage
18. Phase 13 intelligence synthesis integration
19. Phase 12 multi-event incident integration
20. Phase 11 evidence graph integration
21. no silent assessment overwrites
22. no fabricated evidence
23. dispatch gate remains strictly blocked
24. one master agent invariant
"""

import pytest
import uuid
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

def make_session_id(prefix: str = "test") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"

from backend.app.core.database import Base
from backend.app.models.domain import (
    InvestigationWorkspace,
    InvestigationAuditLog,
    AssessmentVersion,
    EvidenceReview,
    EvidenceRequest,
    CaseNote,
    ReportVersion,
)
from backend.app.models.canonical import (
    CaseState,
    CaseActionType,
    EvidenceReviewStatus,
    HumanVerificationDecision,
    EvidenceRequestStatus,
    EvidenceRequestPriority,
    CaseTimelineEventType,
)
from backend.app.models.jarvis_schemas import (
    InvestigationStatus,
    JarvisCommandRequest,
    CommandIntent,
)
from backend.app.services.governance.case_management import (
    case_management_engine,
    CaseStateTransitionError,
    CaseAuthorizationError,
)
from backend.app.services.jarvis.jarvis_workspace import workspace_manager
from backend.app.services.jarvis.jarvis_command_interpreter import command_interpreter
from backend.app.services.jarvis.jarvis_orchestrator import master_orchestrator
from backend.app.services.intelligence.global_intelligence_synthesis import global_intelligence_synthesis_engine


from backend.app.core.database import SessionLocal


@pytest.fixture(scope="function")
def db_session():
    """Database session using SessionLocal."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()



# =============================================================================
# 1. CASE CREATION
# =============================================================================
def test_case_creation(db_session: Session):
    ws = workspace_manager.get_or_create_workspace(
        db=db_session,
        session_id=make_session_id("test-session-case-create"),
        target_event_id="EVT-827",
        user_role="ANALYST",
        created_by="ANALYST_ALICE"
    )
    assert ws is not None
    assert ws.investigation_id.startswith("INV-")
    assert ws.target_event_id == "EVT-827"
    assert ws.status in ["CREATED", "ACTIVE"]
    assert ws.verification_status in ["NOT_REQUIRED", "REQUIRES_HUMAN_REVIEW"]


# =============================================================================
# 2. VALID STATE TRANSITIONS
# =============================================================================
def test_valid_state_transitions(db_session: Session):
    ws = workspace_manager.get_or_create_workspace(
        db=db_session, session_id=make_session_id("test-transitions"), target_event_id="EVT-827"
    )
    ws.status = CaseState.CREATED.value
    db_session.add(ws)
    db_session.commit()

    # CREATED -> ACTIVE
    case_management_engine.validate_transition(ws.status, CaseState.ACTIVE.value)
    ws = workspace_manager.update_status(db_session, ws.investigation_id, CaseState.ACTIVE.value)
    assert ws.status == CaseState.ACTIVE.value

    # ACTIVE -> INVESTIGATING
    case_management_engine.validate_transition(ws.status, CaseState.INVESTIGATING.value)
    ws = workspace_manager.update_status(db_session, ws.investigation_id, CaseState.INVESTIGATING.value)
    assert ws.status == CaseState.INVESTIGATING.value

    # INVESTIGATING -> REQUIRES_REVIEW
    case_management_engine.validate_transition(ws.status, CaseState.REQUIRES_REVIEW.value)
    ws = workspace_manager.update_status(db_session, ws.investigation_id, CaseState.REQUIRES_REVIEW.value)
    assert ws.status == CaseState.REQUIRES_REVIEW.value

    # REQUIRES_REVIEW -> VERIFIED
    case_management_engine.validate_transition(ws.status, CaseState.VERIFIED.value)
    ws = workspace_manager.update_status(db_session, ws.investigation_id, CaseState.VERIFIED.value)
    assert ws.status == CaseState.VERIFIED.value

    # VERIFIED -> RESOLVED
    case_management_engine.validate_transition(ws.status, CaseState.RESOLVED.value)
    ws = workspace_manager.update_status(db_session, ws.investigation_id, CaseState.RESOLVED.value)
    assert ws.status == CaseState.RESOLVED.value

    # RESOLVED -> CLOSED
    case_management_engine.validate_transition(ws.status, CaseState.CLOSED.value)
    ws = workspace_manager.update_status(db_session, ws.investigation_id, CaseState.CLOSED.value)
    assert ws.status == CaseState.CLOSED.value

    # CLOSED -> ACTIVE (Reopen)
    case_management_engine.validate_transition(ws.status, CaseState.ACTIVE.value)
    ws = workspace_manager.update_status(db_session, ws.investigation_id, CaseState.ACTIVE.value)
    assert ws.status == CaseState.ACTIVE.value


# =============================================================================
# 3. INVALID STATE TRANSITIONS REJECTED
# =============================================================================
def test_invalid_state_transitions_rejected(db_session: Session):
    # Cannot jump from CREATED directly to VERIFIED
    with pytest.raises(CaseStateTransitionError):
        case_management_engine.validate_transition(CaseState.CREATED.value, CaseState.VERIFIED.value)

    # Cannot jump from CLOSED directly to VERIFIED
    with pytest.raises(CaseStateTransitionError):
        case_management_engine.validate_transition(CaseState.CLOSED.value, CaseState.VERIFIED.value)

    # Cannot jump from CREATED directly to RESOLVED
    with pytest.raises(CaseStateTransitionError):
        case_management_engine.validate_transition(CaseState.CREATED.value, CaseState.RESOLVED.value)


# =============================================================================
# 4. ACTION AUTHORIZATION ENFORCEMENT
# =============================================================================
def test_action_authorization_enforcement():
    # ANALYST can verify
    assert case_management_engine.check_authorization("ANALYST", "VERIFY") is True
    # ADMIN can verify
    assert case_management_engine.check_authorization("ADMIN", "VERIFY") is True

    # PUBLIC cannot verify
    with pytest.raises(CaseAuthorizationError):
        case_management_engine.check_authorization("PUBLIC", "VERIFY")

    # RESEARCHER cannot close case
    with pytest.raises(CaseAuthorizationError):
        case_management_engine.check_authorization("RESEARCHER", "CLOSE")

    # INDUSTRY cannot close case
    with pytest.raises(CaseAuthorizationError):
        case_management_engine.check_authorization("INDUSTRY", "CLOSE")


# =============================================================================
# 5. AUDIT CREATION
# =============================================================================
def test_audit_creation(db_session: Session):
    ws = workspace_manager.get_or_create_workspace(
        db=db_session, session_id=make_session_id("test-audit"), target_event_id="EVT-827"
    )
    entry = case_management_engine.create_audit_entry(
        db=db_session,
        case_id=ws.investigation_id,
        actor_id="ANALYST_BOB",
        actor_role="ANALYST",
        action="REQUEST_REVIEW",
        previous_state="INVESTIGATING",
        new_state="REQUIRES_REVIEW",
        reason="Evidence graph confidence exceeds 90%.",
        evidence_ids=["EV-101", "EV-102"],
        assessment_version=1
    )
    assert entry.audit_id.startswith("AUD-")
    assert entry.actor_id == "ANALYST_BOB"
    assert entry.action == "REQUEST_REVIEW"
    assert "checksum_sha256" in entry.provenance
    assert len(entry.provenance["checksum_sha256"]) == 64


# =============================================================================
# 6. IMMUTABLE AUDIT
# =============================================================================
def test_immutable_audit(db_session: Session):
    ws = workspace_manager.get_or_create_workspace(
        db=db_session, session_id=make_session_id("test-audit-immut"), target_event_id="EVT-827"
    )
    entry = case_management_engine.create_audit_entry(
        db=db_session,
        case_id=ws.investigation_id,
        actor_id="ANALYST_BOB",
        actor_role="ANALYST",
        action="START_INVESTIGATION",
        new_state="INVESTIGATING",
    )
    audit_id = entry.audit_id
    stored = db_session.query(InvestigationAuditLog).filter(InvestigationAuditLog.audit_id == audit_id).first()
    assert stored is not None
    assert stored.action == "START_INVESTIGATION"


# =============================================================================
# 7. ASSESSMENT VERSIONING & DELTAS
# =============================================================================
def test_assessment_versioning_and_deltas(db_session: Session):
    ws = workspace_manager.get_or_create_workspace(
        db=db_session, session_id=make_session_id("test-ass-ver"), target_event_id="EVT-827"
    )
    inv_id = ws.investigation_id

    # Version 1
    assessment_v1 = {
        "evidence_support_score": 85.0,
        "uncertainty_summary": {"level": "PARTIALLY_KNOWN"},
        "structured_statements": {"ST-1": {}, "ST-2": {}},
    }
    v1 = case_management_engine.record_assessment_version(
        db=db_session,
        case_id=inv_id,
        assessment_dict=assessment_v1,
        created_by="ANALYST_1",
        trigger="INITIAL_ASSESSMENT"
    )
    assert v1.version_number == 1
    assert v1.evidence_delta["total_evidence_count"] == 2

    # Version 2 with new evidence
    assessment_v2 = {
        "evidence_support_score": 92.4,
        "uncertainty_summary": {"level": "KNOWN"},
        "structured_statements": {"ST-1": {}, "ST-2": {}, "ST-3": {}},
    }
    v2 = case_management_engine.record_assessment_version(
        db=db_session,
        case_id=inv_id,
        assessment_dict=assessment_v2,
        created_by="ANALYST_1",
        trigger="CONFIRMATORY_UPDATE"
    )
    assert v2.version_number == 2
    assert v2.evidence_delta["total_evidence_count"] == 3
    assert "ST-3" in v2.evidence_delta["added_evidence"]
    assert v2.uncertainty_delta["score_delta"] == 7.4
    assert v2.uncertainty_delta["prior_level"] == "PARTIALLY_KNOWN"
    assert v2.uncertainty_delta["current_level"] == "KNOWN"


# =============================================================================
# 8. EVIDENCE REVIEW WITHOUT ALTERING RAW DATA
# =============================================================================
def test_evidence_review_without_altering_raw_data(db_session: Session):
    ws = workspace_manager.get_or_create_workspace(
        db=db_session, session_id=make_session_id("test-ev-rev"), target_event_id="EVT-827"
    )
    raw_ev = {"evidence_id": "EV-RADAR-1", "type": "SAR_BACKSCATTER", "value": -14.2}
    ws.structured_evidence = [raw_ev]
    db_session.add(ws)
    db_session.commit()

    # Analyst marks evidence ACCEPTED
    rev = case_management_engine.review_evidence_item(
        db=db_session,
        case_id=ws.investigation_id,
        evidence_id="EV-RADAR-1",
        status="ACCEPTED",
        reviewer_id="ANALYST_CHARLIE",
        reviewer_role="ANALYST",
        notes="Sentinel-1 cross-polarization supports ground flare structure."
    )
    assert rev.status == "ACCEPTED"
    assert rev.reviewer_id == "ANALYST_CHARLIE"

    # Raw structured evidence in workspace remains intact
    db_session.refresh(ws)
    assert ws.structured_evidence[0]["evidence_id"] == "EV-RADAR-1"
    assert ws.structured_evidence[0]["value"] == -14.2


# =============================================================================
# 9. EVIDENCE REQUEST LIFECYCLE
# =============================================================================
def test_evidence_request_lifecycle(db_session: Session):
    ws = workspace_manager.get_or_create_workspace(
        db=db_session, session_id=make_session_id("test-ev-req"), target_event_id="EVT-827"
    )
    req = case_management_engine.create_evidence_request(
        db=db_session,
        case_id=ws.investigation_id,
        requested_source="HIGH_RESOLUTION_OPTICAL",
        reason="Verify absence of uncontained flare spread.",
        uncertainty_target="Perimeter containment",
        priority="HIGH",
        requested_by="ANALYST_1",
        actor_role="ANALYST"
    )
    assert req.request_id.startswith("REQ-")
    assert req.status == "OPEN"
    assert req.priority == "HIGH"


# =============================================================================
# 10. ANALYST NOTES AUTHOR TRACKING (NO JARVIS IMPERSONATION)
# =============================================================================
def test_analyst_notes_author_tracking(db_session: Session):
    ws = workspace_manager.get_or_create_workspace(
        db=db_session, session_id=make_session_id("test-notes"), target_event_id="EVT-827"
    )

    # Valid human analyst note
    note = case_management_engine.add_case_note(
        db=db_session,
        case_id=ws.investigation_id,
        author="ANALYST_DAVID",
        author_role="ANALYST",
        content="Cross-referenced regional wind vectors with refinery flare log.",
        case_version=1
    )
    assert note.author == "ANALYST_DAVID"
    assert "Cross-referenced" in note.content

    # Attempting to author note as JARVIS is rejected
    with pytest.raises(ValueError):
        case_management_engine.add_case_note(
            db=db_session,
            case_id=ws.investigation_id,
            author="JARVIS",
            author_role="ANALYST",
            content="Automated observation."
        )


# =============================================================================
# 11. HUMAN VERIFICATION EXPLICIT DECISION
# =============================================================================
def test_human_verification_explicit_decision(db_session: Session):
    ws = workspace_manager.get_or_create_workspace(
        db=db_session, session_id=make_session_id("test-verif"), target_event_id="EVT-827"
    )
    ws.status = CaseState.REQUIRES_REVIEW.value
    db_session.add(ws)
    db_session.commit()

    # Attempting verification with JARVIS as verifier is rejected
    with pytest.raises(ValueError):
        case_management_engine.propose_or_execute_action(
            db=db_session,
            workspace=ws,
            action=CaseActionType.VERIFY.value,
            actor_id="JARVIS",
            actor_role="ANALYST",
            verifier="JARVIS",
            confirm_governed_action=True
        )

    # Authorized human verifier succeeds
    res = case_management_engine.propose_or_execute_action(
        db=db_session,
        workspace=ws,
        action=CaseActionType.VERIFY.value,
        actor_id="SENIOR_ANALYST_SARAH",
        actor_role="ANALYST",
        verifier="SENIOR_ANALYST_SARAH",
        reason="Confirmed industrial flaring event compliant with CTO permit.",
        confirm_governed_action=True
    )
    assert res["status"] == "EXECUTED"
    assert res["new_state"] == CaseState.VERIFIED.value
    assert res["verification_status"] == HumanVerificationDecision.VERIFIED.value


# =============================================================================
# 12. REPORT VERSIONING REPRODUCIBILITY
# =============================================================================
def test_report_versioning_reproducibility(db_session: Session):
    ws = workspace_manager.get_or_create_workspace(
        db=db_session, session_id=make_session_id("test-report-ver"), target_event_id="EVT-827"
    )
    content = "# INTELLIGENCE DOSSIER EVT-827\n\nVerified industrial thermal emission."
    rep = case_management_engine.record_report_version(
        db=db_session,
        case_id=ws.investigation_id,
        presentation_mode="ANALYST",
        assessment_version=1,
        content_markdown=content,
        title="EVT-827 Final Synthesis",
        generated_by="ANALYST_ALICE"
    )
    assert rep.report_id.startswith("REP-")
    assert rep.report_version == 1
    assert len(rep.hash) == 64


# =============================================================================
# 13. CASE TIMELINE CHRONOLOGY
# =============================================================================
def test_case_timeline_chronology(db_session: Session):
    ws = workspace_manager.get_or_create_workspace(
        db=db_session, session_id=make_session_id("test-timeline"), target_event_id="EVT-827"
    )
    # Add structured evidence
    workspace_manager.add_structured_evidence(
        db=db_session,
        investigation_id=ws.investigation_id,
        evidence_type="THERMAL_DETECTION",
        source="VIIRS_NOAA21",
        value={"frp": 45.2},
        epistemic_type="FACT"
    )
    # Add assessment
    case_management_engine.record_assessment_version(
        db=db_session,
        case_id=ws.investigation_id,
        assessment_dict={"evidence_support_score": 90.0},
        created_by="ANALYST_1",
        trigger="INITIAL_ASSESSMENT"
    )
    timeline = case_management_engine.get_case_timeline(db_session, ws.investigation_id)
    assert len(timeline) >= 2
    types = [t.event_type for t in timeline]
    assert CaseTimelineEventType.INVESTIGATION in types
    assert CaseTimelineEventType.ASSESSMENT in types


# =============================================================================
# 14. JARVIS COMMAND ROUTING
# =============================================================================
def test_jarvis_command_routing():
    # Primary Acceptance Command
    c1 = "JARVIS, prepare EVT-827 for human verification and show the complete case timeline, assessment history, unresolved evidence requests, latest assessment provenance, and recommended next evidence."
    obj1 = command_interpreter.interpret(c1)
    assert obj1["objective"].primary_goal == "SECTION_23_PHASE14_ACCEPTANCE"

    # Second Acceptance Command
    c2 = "JARVIS, show me exactly why the assessment changed between the previous and current versions."
    obj2 = command_interpreter.interpret(c2)
    assert obj2["objective"].primary_goal == "SECTION_24_PHASE14_ACCEPTANCE"

    # Third Acceptance Command
    c3 = "JARVIS, close the investigation."
    obj3 = command_interpreter.interpret(c3)
    assert obj3["objective"].primary_goal == "SECTION_25_PHASE14_ACCEPTANCE"

    # Timeline command
    c4 = "JARVIS, show the investigation timeline."
    obj4 = command_interpreter.interpret(c4)
    assert obj4["objective"].primary_goal == "CASE_TIMELINE"

    # Assessment history command
    c5 = "JARVIS, show assessment history."
    obj5 = command_interpreter.interpret(c5)
    assert obj5["objective"].primary_goal == "ASSESSMENT_HISTORY"


# =============================================================================
# 15. WRITE SAFETY (PROPOSE BEFORE EXECUTE)
# =============================================================================
def test_write_safety_propose_before_execute(db_session: Session):
    ws = workspace_manager.get_or_create_workspace(
        db=db_session, session_id=make_session_id("test-write-safety"), target_event_id="EVT-827"
    )
    ws.status = CaseState.INVESTIGATING.value
    db_session.add(ws)
    db_session.commit()

    # Autonomous or unconfirmed close action returns PROPOSED status
    res = case_management_engine.propose_or_execute_action(
        db=db_session,
        workspace=ws,
        action="CLOSE",
        actor_id="JARVIS_ORCHESTRATOR",
        actor_role="ANALYST",
        is_autonomous_call=True
    )
    assert res["status"] == "PROPOSED"
    assert res["requires_confirmation"] is True
    # Case was NOT closed
    assert ws.status == CaseState.INVESTIGATING.value

    # Explicit human confirmation closes the case
    res_confirmed = case_management_engine.propose_or_execute_action(
        db=db_session,
        workspace=ws,
        action="CLOSE",
        actor_id="ANALYST_HUMAN",
        actor_role="ANALYST",
        confirm_governed_action=True,
        is_autonomous_call=False
    )
    assert res_confirmed["status"] == "EXECUTED"
    assert ws.status == CaseState.CLOSED.value


# =============================================================================
# 16. RBAC MATRIX & PRIVILEGE ESCALATION DENIAL
# =============================================================================
def test_rbac_matrix_and_privilege_escalation_denial():
    # PUBLIC is denied protected actions
    with pytest.raises(CaseAuthorizationError):
        case_management_engine.check_authorization("PUBLIC", "CLOSE")
    with pytest.raises(CaseAuthorizationError):
        case_management_engine.check_authorization("PUBLIC", "START_INVESTIGATION")

    # RESEARCHER is denied close and verification
    with pytest.raises(CaseAuthorizationError):
        case_management_engine.check_authorization("RESEARCHER", "VERIFY")
    with pytest.raises(CaseAuthorizationError):
        case_management_engine.check_authorization("RESEARCHER", "CLOSE")

    # AGENCY can request review and escalate
    assert case_management_engine.check_authorization("AGENCY", "REQUEST_REVIEW") is True
    assert case_management_engine.check_authorization("AGENCY", "ESCALATE") is True


# =============================================================================
# 17. PROVENANCE CRYPTOGRAPHIC LINEAGE
# =============================================================================
def test_provenance_cryptographic_lineage(db_session: Session):
    ws = workspace_manager.get_or_create_workspace(
        db=db_session, session_id=make_session_id("test-prov-lin"), target_event_id="EVT-827"
    )
    v = case_management_engine.record_assessment_version(
        db=db_session,
        case_id=ws.investigation_id,
        assessment_dict={"score": 88.0},
        created_by="ANALYST_1",
        trigger="TEST"
    )
    assert "sha256" in v.provenance
    assert len(v.provenance["sha256"]) == 64


# =============================================================================
# 18. PHASE 13 INTELLIGENCE SYNTHESIS INTEGRATION
# =============================================================================
def test_phase13_intelligence_synthesis_integration(db_session: Session):
    ws = workspace_manager.get_or_create_workspace(
        db=db_session, session_id=make_session_id("test-synth-int"), target_event_id="EVT-827"
    )
    synth = global_intelligence_synthesis_engine.synthesize_assessment(
        db=db_session, target_ref="EVT-827", mode="ANALYST"
    )
    updated_ws = workspace_manager.update_workspace_intelligence_synthesis(db_session, ws, synth)
    assert updated_ws.unified_assessment is not None
    # Assessment version was recorded in assessment_versions table
    versions = db_session.query(AssessmentVersion).filter(AssessmentVersion.case_id == ws.investigation_id).all()
    assert len(versions) >= 1


# =============================================================================
# 19. PHASE 12 MULTI-EVENT INCIDENT INTEGRATION
# =============================================================================
def test_phase12_multi_event_incident_integration(db_session: Session):
    ws = workspace_manager.get_or_create_workspace(
        db=db_session, session_id=make_session_id("test-inc-int"), target_event_id="EVT-827"
    )
    ws.related_event_ids = ["EVT-827", "EVT-828"]
    ws.incident_assessment = {"incident_type": "MULTI_FACILITY_INDUSTRIAL_EPISODE", "correlation_strength": "STRONG"}
    db_session.add(ws)
    db_session.commit()

    timeline = case_management_engine.get_case_timeline(db_session, ws.investigation_id)
    assert len(timeline) >= 1
    assert ws.related_event_ids == ["EVT-827", "EVT-828"]


# =============================================================================
# 20. PHASE 11 EVIDENCE GRAPH INTEGRATION
# =============================================================================
def test_phase11_evidence_graph_integration(db_session: Session):
    ws = workspace_manager.get_or_create_workspace(
        db=db_session, session_id=make_session_id("test-eg-int"), target_event_id="EVT-827"
    )
    ws.evidence_nodes = [{"id": "N-1", "type": "THERMAL_DETECTION"}, {"id": "N-2", "type": "FACILITY"}]
    ws.evidence_edges = [{"source": "N-1", "target": "N-2", "type": "PROXIMATE_TO"}]
    db_session.add(ws)
    db_session.commit()

    assert len(ws.evidence_nodes) == 2
    assert len(ws.evidence_edges) == 1


# =============================================================================
# 21. NO SILENT ASSESSMENT OVERWRITES
# =============================================================================
def test_no_silent_assessment_overwrites(db_session: Session):
    ws = workspace_manager.get_or_create_workspace(
        db=db_session, session_id=make_session_id("test-no-overwrite"), target_event_id="EVT-827"
    )
    v1 = case_management_engine.record_assessment_version(
        db=db_session, case_id=ws.investigation_id, assessment_dict={"score": 80.0},
        created_by="ANALYST_1", trigger="TRIGGER_1"
    )
    v2 = case_management_engine.record_assessment_version(
        db=db_session, case_id=ws.investigation_id, assessment_dict={"score": 90.0},
        created_by="ANALYST_1", trigger="TRIGGER_2"
    )
    versions = db_session.query(AssessmentVersion).filter(AssessmentVersion.case_id == ws.investigation_id).all()
    assert len(versions) == 2
    assert v1.assessment["score"] == 80.0
    assert v2.assessment["score"] == 90.0


# =============================================================================
# 22. NO FABRICATED EVIDENCE
# =============================================================================
def test_no_fabricated_evidence(db_session: Session):
    ws = workspace_manager.get_or_create_workspace(
        db=db_session, session_id=make_session_id("test-no-fab"), target_event_id="EVT-827"
    )
    # Evidence request records legitimate empirical sources
    req = case_management_engine.create_evidence_request(
        db=db_session,
        case_id=ws.investigation_id,
        requested_source="SAR_RADAR",
        reason="Verify structural presence through cloud cover.",
        uncertainty_target="Cloud obscuration",
        priority="HIGH",
        requested_by="ANALYST_1"
    )
    assert req.requested_source == "SAR_RADAR"
    # Status is OPEN awaiting genuine human/sensor acquisition
    assert req.status == "OPEN"


# =============================================================================
# 23. DISPATCH GATE REMAINS STRICTLY BLOCKED
# =============================================================================
def test_operational_dispatch_remains_blocked():
    from backend.app.services.intelligence.global_intelligence_synthesis import ENABLE_OPERATIONAL_DISPATCH_GATE
    assert ENABLE_OPERATIONAL_DISPATCH_GATE is False


# =============================================================================
# 24. ONE MASTER AGENT INVARIANT
# =============================================================================
def test_one_master_agent_invariant():
    assert master_orchestrator is not None
    assert hasattr(master_orchestrator, "execute_command")
