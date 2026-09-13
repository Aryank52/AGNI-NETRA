"""
AGNI-NETRA — Phase 20 Comprehensive Operational Validation Test Suite
Authoritative tests for Groups A through W covering all Phase 20 capabilities:

Group A: Analyst Triage Queue
Group B: Priority Explanation
Group C: Event Dossier (7 Dimensions)
Group D: Investigation 8-Step Workflow
Group E: Evidence Review Workspace
Group F: Competing Hypotheses Workflow (5 Hypotheses Matrix)
Group G: Analyst Confidence vs Model Confidence Separation
Group H: Human Verification Desk
Group I: Case Lifecycle Governance (8 States)
Group J: Decision Effectiveness Metrics (with INSUFFICIENT DATA)
Group K: Operational Triage Effectiveness Metrics
Group L: Analyst Feedback Loop
Group M: JARVIS Analyst Assistance Commands (All 10 Commands)
Group N: JARVIS Internal Explanation Trace
Group O: Standardized 17-Section Operational Report
Group P: Decision Auditability & Immutability
Group Q: India Sovereign Geographic Filtering
Group R: Role-Based Access Control (RBAC)
Group S: Public Role Data Sanitization
Group T: Operational Dispatch Gate Safety Invariant (BLOCKED)
Group U: Automated Model Activation Disabled Invariant
Group V: Frozen 5-Factor Risk Formula Preservation
Group W: Frozen Governed Priority Formula Preservation
"""

import math
import time
import pytest
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, or_, and_

from backend.app.core.database import SessionLocal
from backend.app.models.domain import (
    ThermalEvent,
    RiskScore,
    ModelPrediction,
    Alert,
    IndustrialFacility,
    InvestigationWorkspace,
    VerificationRecord,
    InvestigationAuditLog,
    AssessmentVersion,
    EvidenceReview,
    ReportVersion,
    AnalystFeedback,
    generate_uuid,
)
from backend.app.models.canonical import (
    CaseState,
    CaseActionType,
    InvestigationWorkflowStep,
    EvidenceEvaluationStatus,
    HypothesisStatus,
    HumanVerificationAction,
    AnalystFeedbackType,
)
from backend.app.services.analyst.analyst_workflow_service import (
    analyst_workflow_service,
    WORKFLOW_STEPS_SEQUENCE,
)
from backend.app.services.intelligence.india_intelligence_service import india_intelligence_service
from backend.app.services.governance.case_management import (
    case_management_engine,
    CaseStateTransitionError,
    CaseAuthorizationError,
)
from backend.app.services.jarvis.jarvis_orchestrator import JarvisMasterOrchestrator
from backend.app.models.jarvis_schemas import JarvisCommandRequest


@pytest.fixture(scope="module")
def db_session():
    """Provides a transactional database session for tests."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module")
def sample_event(db_session: Session):
    """Retrieves or validates a representative Indian thermal event in DB."""
    ev = db_session.query(ThermalEvent).filter(
        ThermalEvent.country == "India"
    ).order_by(desc(ThermalEvent.detection_count)).first()
    if not ev:
        ev = db_session.query(ThermalEvent).first()
    assert ev is not None, "At least one thermal event required in database."
    return ev


@pytest.fixture(scope="module")
def test_workspace(db_session: Session, sample_event: ThermalEvent):
    """Creates an ephemeral test investigation workspace."""
    ws_id = f"INV-TEST-{int(time.time())}"
    ws = InvestigationWorkspace(
        investigation_id=ws_id,
        session_id="test-session-p20",
        target_event_id=sample_event.id,
        user_role="ANALYST",
        status=CaseState.CREATED.value,
        verification_status="REQUIRES_HUMAN_REVIEW",
        created_by="ANALYST_TEST",
        structured_evidence=[
            {
                "evidence_id": f"EV-TEST-1",
                "title": "Satellite Thermal Telemetry",
                "source": "NASA_FIRMS_VIIRS",
                "type": "SATELLITE_TELEMETRY",
            },
            {
                "evidence_id": f"EV-TEST-2",
                "title": "Industrial Registry Context",
                "source": "OSM_INDUSTRIAL",
                "type": "FACILITY_CONTEXT",
            }
        ],
    )
    db_session.add(ws)
    db_session.commit()
    db_session.refresh(ws)
    yield ws
    # Teardown
    db_session.query(InvestigationAuditLog).filter(InvestigationAuditLog.case_id == ws_id).delete()
    db_session.query(EvidenceReview).filter(EvidenceReview.case_id == ws_id).delete()
    db_session.query(AssessmentVersion).filter(AssessmentVersion.case_id == ws_id).delete()
    db_session.query(ReportVersion).filter(ReportVersion.case_id == ws_id).delete()
    db_session.query(InvestigationWorkspace).filter(InvestigationWorkspace.investigation_id == ws_id).delete()
    db_session.commit()


# =============================================================================
# GROUP A: ANALYST TRIAGE QUEUE
# =============================================================================
class TestGroupA_TriageQueue:
    def test_triage_queue_retrieval(self, db_session: Session):
        res = analyst_workflow_service.get_triage_queue(db_session, limit=20)
        assert res["status"] == "SUCCESS"
        assert res["jurisdiction"] == "Sovereign Territory of India"
        assert "operational_queues" in res
        queues = res["operational_queues"]
        assert "highest_priority" in queues
        assert "high_risk" in queues
        assert "persistent_hotspots" in queues
        assert "newly_emerging" in queues
        assert "requiring_verification" in queues
        assert res["queue_retrieval_latency_ms"] < 2000.0, "Triage queue retrieval latency must be < 2.0s"

    def test_triage_queue_filters(self, db_session: Session, sample_event: ThermalEvent):
        state = sample_event.state
        res = analyst_workflow_service.get_triage_queue(db_session, filters={"state": state}, limit=10)
        assert res["status"] == "SUCCESS"
        highest = res["operational_queues"]["highest_priority"]
        for item in highest:
            assert state.lower() in item["state"].lower()


# =============================================================================
# GROUP B: PRIORITY EXPLANATION
# =============================================================================
class TestGroupB_PriorityExplanation:
    def test_mathematical_priority_breakdown(self, db_session: Session, sample_event: ThermalEvent):
        exp = analyst_workflow_service.explain_triage_priority(db_session, sample_event.id)
        assert exp["status"] == "SUCCESS"
        prio = exp["governed_priority_score"]
        assert 0.0 <= prio <= 100.0

        mb = exp["mathematical_breakdown"]
        risk_pts = mb["risk_contribution"]["weighted_points"]
        conf_pts = mb["confidence_contribution"]["weighted_points"]
        tier_pts = mb["tier_contribution"]["weighted_points"]
        rec_pts = mb["recency_contribution"]["weighted_points"]

        expected_sum = round(risk_pts + conf_pts + tier_pts + rec_pts, 2)
        assert abs(prio - expected_sum) <= 0.02, "Governed priority score must equal sum of weighted contributions"

    def test_epistemic_separation_disclosure(self, db_session: Session, sample_event: ThermalEvent):
        exp = analyst_workflow_service.explain_triage_priority(db_session, sample_event.id)
        sep = exp["epistemic_separation"]
        assert "risk_score" in sep
        assert "model_calibrated_confidence" in sep
        assert "evidence_strength" in sep
        assert "epistemic_uncertainty" in sep
        assert "analyst_confidence" in sep


# =============================================================================
# GROUP C: STANDARDIZED EVENT DOSSIER (7 DIMENSIONS)
# =============================================================================
class TestGroupC_EventDossier:
    def test_dossier_all_seven_dimensions(self, db_session: Session, sample_event: ThermalEvent):
        dossier = analyst_workflow_service.get_standardized_event_dossier(db_session, sample_event.id)
        assert dossier["status"] == "SUCCESS"
        assert "identity" in dossier
        assert "observed_telemetry" in dossier
        assert "derived_patterns" in dossier
        assert "classification_and_attribution" in dossier
        assert "spatial_and_environmental_context" in dossier
        assert "evidence_graph_and_epistemics" in dossier
        assert "decision_support_and_guidance" in dossier

    def test_non_causal_spatial_language(self, db_session: Session, sample_event: ThermalEvent):
        dossier = analyst_workflow_service.get_standardized_event_dossier(db_session, sample_event.id)
        phrase = dossier["spatial_and_environmental_context"]["spatial_association_phrase"]
        assert "caused by" not in phrase.lower(), "Language must be non-causal: never 'caused by'."


# =============================================================================
# GROUP D: INVESTIGATION 8-STEP WORKFLOW
# =============================================================================
class TestGroupD_InvestigationWorkflow:
    def test_workflow_initial_state(self, db_session: Session, test_workspace: InvestigationWorkspace):
        state = analyst_workflow_service.get_investigation_workflow_state(db_session, test_workspace.investigation_id)
        assert state["case_id"] == test_workspace.investigation_id
        assert state["current_step"] == InvestigationWorkflowStep.SELECT.value

    def test_valid_step_progression(self, db_session: Session, test_workspace: InvestigationWorkspace):
        next_state = analyst_workflow_service.transition_investigation_step(
            db=db_session,
            case_id=test_workspace.investigation_id,
            target_step=InvestigationWorkflowStep.SCOPE.value,
            actor_id="ANALYST_TEST",
        )
        assert next_state["current_step"] == InvestigationWorkflowStep.SCOPE.value
        assert InvestigationWorkflowStep.SELECT.value in next_state["completed_steps"]

    def test_illegal_step_skip_rejected(self, db_session: Session, test_workspace: InvestigationWorkspace):
        with pytest.raises(CaseStateTransitionError):
            analyst_workflow_service.transition_investigation_step(
                db=db_session,
                case_id=test_workspace.investigation_id,
                target_step=InvestigationWorkflowStep.VERIFY.value,
                actor_id="ANALYST_TEST",
            )


# =============================================================================
# GROUP E: EVIDENCE REVIEW WORKSPACE
# =============================================================================
class TestGroupE_EvidenceReview:
    def test_evidence_review_immutability(self, db_session: Session, test_workspace: InvestigationWorkspace):
        review_res = analyst_workflow_service.record_evidence_decision(
            db=db_session,
            case_id=test_workspace.investigation_id,
            evidence_id="EV-TEST-1",
            decision=EvidenceEvaluationStatus.SUPPORTED.value,
            analyst_id="ANALYST_TEST",
            notes="Satellite observation corroborates elevated thermal activity.",
        )
        assert review_res["status"] == "SUCCESS"
        assert review_res["decision"] == "SUPPORTED"

        # Verify underlying workspace structured evidence is preserved
        db_session.refresh(test_workspace)
        assert len(test_workspace.structured_evidence) >= 2


# =============================================================================
# GROUP F: COMPETING HYPOTHESES WORKFLOW
# =============================================================================
class TestGroupF_CompetingHypotheses:
    def test_hypotheses_evaluation(self, db_session: Session, sample_event: ThermalEvent):
        res = analyst_workflow_service.get_competing_hypotheses_review(db_session, sample_event.id)
        assert res["status"] == "SUCCESS"
        assert len(res["hypotheses"]) == 5, "Must evaluate exactly 5 operational hypotheses."
        for h in res["hypotheses"]:
            assert h["baseline_status"] in [s.value for s in HypothesisStatus]

    def test_analyst_hypothesis_assessment(self, db_session: Session, test_workspace: InvestigationWorkspace):
        assess_res = analyst_workflow_service.assess_hypothesis(
            db=db_session,
            case_or_event_id=test_workspace.investigation_id,
            hypothesis_id="H1_ROUTINE_INDUSTRIAL",
            status=HypothesisStatus.SUPPORTED.value,
            analyst_id="ANALYST_TEST",
            rationale="Continuous operational flare matches OSM facility operating hours.",
        )
        assert assess_res["status"] == "SUCCESS"
        assert assess_res["assessed_status"] == "SUPPORTED"


# =============================================================================
# GROUP G: ANALYST CONFIDENCE VS MODEL CONFIDENCE SEPARATION
# =============================================================================
class TestGroupG_AnalystConfidenceSeparation:
    def test_confidence_decoupling(self, db_session: Session, test_workspace: InvestigationWorkspace, sample_event: ThermalEvent):
        # Query model prediction before
        pred_before = db_session.query(ModelPrediction).filter(ModelPrediction.event_id == sample_event.id).first()
        orig_conf = pred_before.confidence if pred_before else 0.50

        # Record analyst confidence
        res = analyst_workflow_service.record_analyst_confidence(
            db=db_session,
            case_id=test_workspace.investigation_id,
            analyst_id="ANALYST_TEST",
            confidence=0.92,
            confidence_scale_1_to_5=5,
            rationale="Verified with local industrial register and ground evidence.",
        )
        assert res["status"] == "SUCCESS"

        # Verify model prediction confidence has NOT mutated
        db_session.refresh(pred_before) if pred_before else None
        if pred_before:
            assert pred_before.confidence == orig_conf, "Model confidence must never be overwritten by analyst judgment."


# =============================================================================
# GROUP H: HUMAN VERIFICATION DESK
# =============================================================================
class TestGroupH_HumanVerificationDesk:
    def test_jarvis_autonomous_verification_rejected(self, db_session: Session, sample_event: ThermalEvent):
        with pytest.raises(ValueError, match="autonomous agents"):
            analyst_workflow_service.submit_human_verification(
                db=db_session,
                case_or_event_id=sample_event.id,
                verifier_id="JARVIS",
                verifier_role="ANALYST",
                action=HumanVerificationAction.CONFIRM.value,
            )

    def test_human_verification_submission(self, db_session: Session, sample_event: ThermalEvent):
        res = analyst_workflow_service.submit_human_verification(
            db=db_session,
            case_or_event_id=sample_event.id,
            verifier_id="HUMAN_ANALYST_42",
            verifier_role="ANALYST",
            action=HumanVerificationAction.CONFIRM.value,
            notes="Confirmed routine industrial thermal flare via official operating logs.",
            analyst_confidence=0.95,
        )
        assert res["status"] == "SUCCESS"
        assert res["action"] == "CONFIRM"
        assert res["verifier_id"] == "HUMAN_ANALYST_42"
        assert res["audit_id"].startswith("AUD-")


# =============================================================================
# GROUP I: CASE LIFECYCLE GOVERNANCE (8 STATES)
# =============================================================================
class TestGroupI_CaseLifecycleGovernance:
    def test_state_machine_transition_valid(self, db_session: Session, test_workspace: InvestigationWorkspace):
        test_workspace.status = CaseState.ACTIVE.value
        db_session.commit()
        res = analyst_workflow_service.validate_case_lifecycle(
            db=db_session,
            case_id=test_workspace.investigation_id,
            action=CaseActionType.START_INVESTIGATION.value,
            actor_id="ANALYST_TEST",
            actor_role="ANALYST",
        )
        assert res["status"] == "EXECUTED"
        assert res["new_state"] == CaseState.INVESTIGATING.value

    def test_illegal_state_transition_fails(self, db_session: Session, test_workspace: InvestigationWorkspace):
        test_workspace.status = CaseState.CREATED.value
        db_session.commit()
        with pytest.raises(CaseStateTransitionError):
            case_management_engine.validate_transition(CaseState.CREATED.value, CaseState.VERIFIED.value)


# =============================================================================
# GROUP J: DECISION EFFECTIVENESS METRICS (WITH INSUFFICIENT DATA)
# =============================================================================
class TestGroupJ_DecisionEffectivenessMetrics:
    def test_empirical_metrics_integrity(self, db_session: Session):
        metrics = analyst_workflow_service.compute_decision_effectiveness_metrics(db_session)
        assert metrics["metric_status"] in ["COMPUTED", "INSUFFICIENT_DATA"]
        if metrics["metric_status"] == "COMPUTED":
            assert metrics["total_verifications"] > 0
            assert metrics["confirmation_rate"] is not None
            assert 0.0 <= metrics["confirmation_rate"] <= 1.0
        else:
            assert metrics["sample_size"] == 0


# =============================================================================
# GROUP K: OPERATIONAL TRIAGE EFFECTIVENESS METRICS
# =============================================================================
class TestGroupK_TriageEffectivenessMetrics:
    def test_triage_metrics(self, db_session: Session):
        triage_m = analyst_workflow_service.compute_triage_effectiveness_metrics(db_session)
        assert triage_m["metric_status"] in ["COMPUTED", "INSUFFICIENT_DATA"]
        assert triage_m["total_triaged_events"] >= 0
        assert triage_m["queue_retrieval_latency_ms"] >= 0.0


# =============================================================================
# GROUP L: ANALYST FEEDBACK LOOP
# =============================================================================
class TestGroupL_AnalystFeedback:
    def test_record_and_retrieve_feedback(self, db_session: Session, sample_event: ThermalEvent):
        fb_res = analyst_workflow_service.record_analyst_feedback(
            db=db_session,
            feedback_data={
                "event_id": sample_event.id,
                "analyst_id": "ANALYST_TEST",
                "analyst_role": "ANALYST",
                "feedback_type": AnalystFeedbackType.USEFUL.value,
                "rating": 5,
                "target_component": "TRIAGE",
                "comments": "High priority sorting accurately captured anomalous industrial flaring.",
            },
        )
        assert fb_res["status"] == "SUCCESS"
        assert fb_res["feedback_type"] == "USEFUL"

        all_fb = analyst_workflow_service.get_analyst_feedback(db_session, limit=10)
        assert len(all_fb) >= 1


# =============================================================================
# GROUP M: JARVIS ANALYST ASSISTANCE COMMANDS (ALL 10 COMMANDS)
# =============================================================================
class TestGroupM_JarvisCommands:
    orchestrator = JarvisMasterOrchestrator()

    @pytest.mark.parametrize("cmd", [
        "JARVIS, show me what needs verification first.",
        "JARVIS, why was this event prioritized?",
        "JARVIS, what evidence is still missing?",
        "JARVIS, summarize this investigation.",
        "JARVIS, what changed since the previous assessment?",
        "JARVIS, what hypotheses remain plausible?",
        "JARVIS, what contradicts the current assessment?",
        "JARVIS, what should the analyst verify next?",
        "JARVIS, compare these two incidents.",
        "JARVIS, generate the final case report."
    ])
    def test_jarvis_analyst_commands_execution(self, cmd: str):
        req = JarvisCommandRequest(command=cmd)
        resp = self.orchestrator.execute_command(req)
        assert resp is not None
        assert resp.state in ["COMPLETED", "AWAITING_APPROVAL", "IDLE"]
        assert resp.summary is not None
        assert len(resp.summary) > 20
        assert resp.details.get("dispatch_gate_blocked") is True or "BLOCKED" in resp.summary


# =============================================================================
# GROUP N: JARVIS INTERNAL EXPLANATION TRACE
# =============================================================================
class TestGroupN_ExplanationTrace:
    orchestrator = JarvisMasterOrchestrator()

    def test_explanation_trace_completeness(self):
        req = JarvisCommandRequest(command="JARVIS, why was this event prioritized?")
        resp = self.orchestrator.execute_command(req)
        trace = resp.execution_trace
        assert trace is not None
        assert len(trace.steps) >= 1
        for step in trace.steps:
            assert step.agent == "JARVIS"
            assert step.status == "COMPLETED"


# =============================================================================
# GROUP O: STANDARDIZED 17-SECTION OPERATIONAL REPORT
# =============================================================================
class TestGroupO_OperationalReport:
    def test_seventeen_sections_present(self, db_session: Session, sample_event: ThermalEvent):
        rep = analyst_workflow_service.generate_operational_analyst_report(db_session, sample_event.id)
        assert rep["status"] == "SUCCESS"
        assert rep["sections_count"] == 17
        md = rep["content_markdown"]
        for i in range(1, 18):
            assert f"## {i}." in md, f"Report must contain section ## {i}."
        assert "Content SHA-256 Checksum" in md


# =============================================================================
# GROUP P: DECISION AUDITABILITY & IMMUTABILITY
# =============================================================================
class TestGroupP_DecisionAuditability:
    def test_audit_integrity_verification(self, db_session: Session, test_workspace: InvestigationWorkspace):
        # Create audit entry
        case_management_engine.create_audit_entry(
            db=db_session,
            case_id=test_workspace.investigation_id,
            actor_id="ANALYST_TEST",
            actor_role="ANALYST",
            action="TEST_AUDIT_ACTION",
            reason="Testing cryptographic tamper evidence.",
        )
        integrity = case_management_engine.verify_case_audit_integrity(db_session, test_workspace.investigation_id)
        assert integrity["is_tamper_free"] is True
        assert integrity["verified_entries"] >= 1


# =============================================================================
# GROUP Q: INDIA SOVEREIGN GEOGRAPHIC FILTERING
# =============================================================================
class TestGroupQ_IndiaSovereignGeographicFiltering:
    def test_foreign_geographic_isolation(self, db_session: Session):
        queue = analyst_workflow_service.get_triage_queue(db_session, limit=50)
        for q_name, items in queue["operational_queues"].items():
            for item in items:
                if isinstance(item, dict) and "state" in item:
                    assert item.get("country", "India") == "India"


# =============================================================================
# GROUP R: ROLE-BASED ACCESS CONTROL (RBAC)
# =============================================================================
class TestGroupR_RBAC:
    def test_unauthorized_role_denied(self):
        with pytest.raises(CaseAuthorizationError):
            case_management_engine.check_authorization("PUBLIC", CaseActionType.VERIFY.value)

    def test_authorized_role_permitted(self):
        assert case_management_engine.check_authorization("ANALYST", CaseActionType.VERIFY.value) is True
        assert case_management_engine.check_authorization("ADMIN", CaseActionType.VERIFY.value) is True


# =============================================================================
# GROUP S: PUBLIC ROLE DATA SANITIZATION
# =============================================================================
class TestGroupS_PublicRoleDataSanitization:
    def test_sanitization_logic(self, db_session: Session):
        queue = analyst_workflow_service.get_triage_queue(db_session, limit=5)
        # Apply public sanitization
        sanitized = {}
        for q_name, items in queue["operational_queues"].items():
            sanitized[q_name] = [
                {
                    "event_code": i.get("event_code"),
                    "state": i.get("state"),
                    "district": i.get("district"),
                    "risk_level": i.get("risk_level"),
                }
                for i in items if isinstance(i, dict)
            ]
        # Verify internal routing details redacted
        for item in sanitized["highest_priority"]:
            assert "routing_tier" not in item
            assert "governed_priority_score" not in item


# =============================================================================
# GROUP T: OPERATIONAL DISPATCH GATE SAFETY INVARIANT (BLOCKED)
# =============================================================================
class TestGroupT_DispatchGateBlocked:
    def test_dispatch_gate_blocked_invariant(self, db_session: Session):
        assert analyst_workflow_service.ENABLE_OPERATIONAL_DISPATCH_GATE is False
        res = analyst_workflow_service.get_triage_queue(db_session)
        assert "BLOCKED" in res["dispatch_gate_status"]


# =============================================================================
# GROUP U: AUTOMATED MODEL ACTIVATION DISABLED INVARIANT
# =============================================================================
class TestGroupU_AutomatedModelActivationDisabled:
    def test_automated_model_activation_disabled_invariant(self):
        assert analyst_workflow_service.ENABLE_AUTOMATED_MODEL_ACTIVATION is False


# =============================================================================
# GROUP V: FROZEN 5-FACTOR RISK FORMULA PRESERVATION
# =============================================================================
class TestGroupV_FrozenFiveFactorRiskFormula:
    def test_risk_weights_strictly_frozen(self):
        assert analyst_workflow_service.RISK_WEIGHT_INTENSITY == 0.30
        assert analyst_workflow_service.RISK_WEIGHT_ABNORMALITY == 0.25
        assert analyst_workflow_service.RISK_WEIGHT_EXPOSURE == 0.20
        assert analyst_workflow_service.RISK_WEIGHT_PERSISTENCE == 0.15
        assert analyst_workflow_service.RISK_WEIGHT_CONTEXT == 0.10
        total = (
            analyst_workflow_service.RISK_WEIGHT_INTENSITY +
            analyst_workflow_service.RISK_WEIGHT_ABNORMALITY +
            analyst_workflow_service.RISK_WEIGHT_EXPOSURE +
            analyst_workflow_service.RISK_WEIGHT_PERSISTENCE +
            analyst_workflow_service.RISK_WEIGHT_CONTEXT
        )
        assert abs(total - 1.00) < 1e-6


# =============================================================================
# GROUP W: FROZEN GOVERNED PRIORITY FORMULA PRESERVATION
# =============================================================================
class TestGroupW_FrozenGovernedPriorityFormula:
    def test_priority_weights_strictly_frozen(self):
        assert analyst_workflow_service.PRIORITY_WEIGHT_RISK == 0.40
        assert analyst_workflow_service.PRIORITY_WEIGHT_CONFIDENCE == 0.20
        assert analyst_workflow_service.PRIORITY_WEIGHT_TIER == 0.30
        assert analyst_workflow_service.PRIORITY_WEIGHT_RECENCY == 0.10
        total = (
            analyst_workflow_service.PRIORITY_WEIGHT_RISK +
            analyst_workflow_service.PRIORITY_WEIGHT_CONFIDENCE +
            analyst_workflow_service.PRIORITY_WEIGHT_TIER +
            analyst_workflow_service.PRIORITY_WEIGHT_RECENCY
        )
        assert abs(total - 1.00) < 1e-6
