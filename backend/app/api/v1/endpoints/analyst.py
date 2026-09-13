"""
AGNI-NETRA — Analyst Workflow, Operational Validation & Decision Effectiveness REST API Endpoints
Phase 20: Sovereign Territory of India Operating Scope

Provides 16 typed, governed endpoints under /api/v1/analyst/*:
1. GET  /api/v1/analyst/triage
2. GET  /api/v1/analyst/events/{event_id}/dossier
3. GET  /api/v1/analyst/events/{event_id}/triage-explanation
4. GET  /api/v1/analyst/investigations/{case_id}/workflow-state
5. POST /api/v1/analyst/investigations/{case_id}/step-transition
6. GET  /api/v1/analyst/investigations/{case_id}/evidence-review
7. POST /api/v1/analyst/investigations/{case_id}/evidence-decision
8. GET  /api/v1/analyst/investigations/{case_id}/hypotheses
9. POST /api/v1/analyst/investigations/{case_id}/hypotheses/assess
10. POST /api/v1/analyst/investigations/{case_id}/confidence
11. POST /api/v1/analyst/verification
12. GET  /api/v1/analyst/investigations/{case_id}/lifecycle
13. GET  /api/v1/analyst/metrics/decision-effectiveness
14. GET  /api/v1/analyst/metrics/triage-effectiveness
15. POST /api/v1/analyst/feedback
16. GET  /api/v1/analyst/feedback
17. GET  /api/v1/analyst/events/{event_id}/report
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.api.deps import get_optional_current_user
from backend.app.models.domain import User
from backend.app.models.canonical import (
    EvidenceDecisionRequest,
    HypothesisAssessmentRequest,
    AnalystConfidenceSubmission,
    HumanVerificationSubmission,
    AnalystFeedbackSubmission,
    InvestigationWorkflowState,
    DecisionEffectivenessMetrics,
    TriageEffectivenessMetrics,
)
from backend.app.services.analyst.analyst_workflow_service import analyst_workflow_service
from backend.app.services.governance.case_management import (
    case_management_engine,
    CaseStateTransitionError,
    CaseAuthorizationError,
)

router = APIRouter()


# =============================================================================
# 1. TRIAGE QUEUE
# =============================================================================
@router.get("/triage")
@router.get("/triage-queue")
def get_triage_queue(
    state: Optional[str] = Query(None, description="Filter by Indian State/UT"),
    district: Optional[str] = Query(None, description="Filter by District"),
    min_priority: Optional[float] = Query(None, description="Minimum Governed Priority Score"),
    min_risk: Optional[float] = Query(None, description="Minimum 5-Factor Risk Score"),
    facility_type: Optional[str] = Query(None, description="Filter by industrial facility type"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
) -> Dict[str, Any]:
    """
    Retrieves the prioritized operational triage queue categorized into prioritized lists.
    Applies public role data sanitization if accessed without an authenticated analyst role.
    """
    filters = {
        "state": state,
        "district": district,
        "min_priority": min_priority,
        "min_risk": min_risk,
        "facility_type": facility_type,
    }
    # Clean None values
    filters = {k: v for k, v in filters.items() if v is not None}

    queue_data = analyst_workflow_service.get_triage_queue(db, filters=filters, limit=limit)

    # Public role sanitization
    user_role = (current_user.role if current_user else "PUBLIC").upper()
    if user_role == "PUBLIC":
        # Redact exact internal routing and detailed risk breakdowns
        sanitized_queues = {}
        for q_name, items in queue_data.get("operational_queues", {}).items():
            sanitized_items = []
            for item in items:
                if isinstance(item, dict):
                    sanitized_items.append({
                        "event_code": item.get("event_code"),
                        "state": item.get("state"),
                        "district": item.get("district"),
                        "first_seen": item.get("first_seen"),
                        "last_seen": item.get("last_seen"),
                        "risk_level": item.get("risk_level"),
                        "predicted_class": item.get("predicted_class"),
                        "verification_status": item.get("verification_status"),
                    })
            sanitized_queues[q_name] = sanitized_items
        queue_data["operational_queues"] = sanitized_queues
        queue_data["role_sanitization"] = "PUBLIC (Detailed operational priority scores redacted)"

    return queue_data


# =============================================================================
# 2. STANDARDIZED EVENT DOSSIER
# =============================================================================
@router.get("/events/{event_id}/dossier")
def get_event_dossier(
    event_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
) -> Dict[str, Any]:
    """
    Assembles standardized 7-dimension operational dossier for an event.
    """
    try:
        return analyst_workflow_service.get_standardized_event_dossier(db, event_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# =============================================================================
# 3. TRIAGE EXPLANATION
# =============================================================================
@router.get("/events/{event_id}/triage-explanation")
def get_triage_explanation(
    event_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
) -> Dict[str, Any]:
    """
    Provides mathematical breakdown of the governed priority formula.
    """
    try:
        return analyst_workflow_service.explain_triage_priority(db, event_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# =============================================================================
# 4. GUIDED INVESTIGATION WORKFLOW STATE
# =============================================================================
@router.get("/investigations/{case_id}/workflow-state")
def get_workflow_state(
    case_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
) -> Dict[str, Any]:
    """
    Retrieves current 8-step guided investigation workflow state.
    """
    try:
        return analyst_workflow_service.get_investigation_workflow_state(db, case_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# =============================================================================
# 5. STEP TRANSITION
# =============================================================================
@router.post("/investigations/{case_id}/step-transition")
def transition_workflow_step(
    case_id: str,
    payload: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
) -> Dict[str, Any]:
    """
    Transitions to next step in the 8-step sequence with audit logging.
    """
    actor_id = (current_user.id if current_user else payload.get("actor_id", "ANALYST"))
    actor_role = (current_user.role if current_user else payload.get("actor_role", "ANALYST")).upper()

    target_step = payload.get("target_step")
    if not target_step:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="'target_step' is required.")

    try:
        return analyst_workflow_service.transition_investigation_step(
            db=db,
            case_id=case_id,
            target_step=target_step,
            actor_id=actor_id,
            actor_role=actor_role,
            notes=payload.get("notes"),
        )
    except CaseStateTransitionError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except CaseAuthorizationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# =============================================================================
# 6. EVIDENCE REVIEW WORKSPACE
# =============================================================================
@router.get("/investigations/{case_id}/evidence-review")
def get_evidence_review_workspace(
    case_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
) -> Dict[str, Any]:
    """
    Retrieves evidence review items with review statuses and immutability guarantee.
    """
    try:
        return analyst_workflow_service.get_evidence_review_workspace(db, case_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# =============================================================================
# 7. EVIDENCE DECISION
# =============================================================================
@router.post("/investigations/{case_id}/evidence-decision")
def record_evidence_decision(
    case_id: str,
    req: EvidenceDecisionRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
) -> Dict[str, Any]:
    """
    Records an analyst decision on an evidence item without altering raw observations.
    """
    analyst_id = (current_user.id if current_user else req.analyst_id)
    analyst_role = (current_user.role if current_user else req.analyst_role).upper()

    try:
        return analyst_workflow_service.record_evidence_decision(
            db=db,
            case_id=case_id,
            evidence_id=req.evidence_id,
            decision=req.decision.value,
            analyst_id=analyst_id,
            analyst_role=analyst_role,
            notes=req.notes,
        )
    except CaseAuthorizationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# =============================================================================
# 8. COMPETING HYPOTHESES WORKSPACE
# =============================================================================
@router.get("/investigations/{case_id}/hypotheses")
def get_competing_hypotheses(
    case_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
) -> Dict[str, Any]:
    """
    Retrieves competing hypotheses evaluation matrix.
    """
    try:
        return analyst_workflow_service.get_competing_hypotheses_review(db, case_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# =============================================================================
# 9. ASSESS HYPOTHESIS
# =============================================================================
@router.post("/investigations/{case_id}/hypotheses/assess")
def assess_hypothesis(
    case_id: str,
    req: HypothesisAssessmentRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
) -> Dict[str, Any]:
    """
    Records analyst assessment on a competing hypothesis with mandatory rationale.
    """
    analyst_id = (current_user.id if current_user else req.analyst_id)
    analyst_role = (current_user.role if current_user else req.analyst_role).upper()

    try:
        return analyst_workflow_service.assess_hypothesis(
            db=db,
            case_or_event_id=case_id,
            hypothesis_id=req.hypothesis_id,
            status=req.status.value,
            analyst_id=analyst_id,
            analyst_role=analyst_role,
            rationale=req.rationale,
            supporting_evidence_ids=req.supporting_evidence_ids,
            contradicting_evidence_ids=req.contradicting_evidence_ids,
        )
    except CaseAuthorizationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# =============================================================================
# 10. RECORD ANALYST CONFIDENCE
# =============================================================================
@router.post("/investigations/{case_id}/confidence")
def record_analyst_confidence(
    case_id: str,
    req: AnalystConfidenceSubmission,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
) -> Dict[str, Any]:
    """
    Records analyst confidence score and justification strictly decoupled from model confidence.
    """
    analyst_id = (current_user.id if current_user else req.analyst_id)
    analyst_role = (current_user.role if current_user else req.analyst_role).upper()

    try:
        return analyst_workflow_service.record_analyst_confidence(
            db=db,
            case_id=case_id,
            analyst_id=analyst_id,
            analyst_role=analyst_role,
            confidence=req.analyst_confidence,
            confidence_scale_1_to_5=req.confidence_scale_1_to_5,
            rationale=req.rationale,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# =============================================================================
# 11. HUMAN VERIFICATION SUBMISSION
# =============================================================================
@router.post("/verification")
def submit_human_verification(
    req: HumanVerificationSubmission,
    event_id: Optional[str] = Query(None, description="Event ID if not verifying by case"),
    case_id: Optional[str] = Query(None, description="Case ID"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
) -> Dict[str, Any]:
    """
    Submits human verification decision with immutable cryptographic audit record.
    Rejects autonomous or non-human callers.
    """
    target = case_id or event_id
    if not target:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Either 'case_id' or 'event_id' is required.")

    verifier_id = (current_user.id if current_user else req.verifier_id)
    verifier_role = (current_user.role if current_user else req.verifier_role).upper()

    try:
        return analyst_workflow_service.submit_human_verification(
            db=db,
            case_or_event_id=target,
            verifier_id=verifier_id,
            verifier_role=verifier_role,
            action=req.action.value,
            verified_label=req.verified_label,
            notes=req.notes,
            analyst_confidence=req.analyst_confidence,
            evidence_reviewed=req.evidence_reviewed,
        )
    except CaseAuthorizationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# =============================================================================
# 12. CASE LIFECYCLE VALIDATOR
# =============================================================================
@router.get("/investigations/{case_id}/lifecycle")
def get_case_lifecycle(
    case_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
) -> Dict[str, Any]:
    """
    Returns valid state transitions and audit integrity for a case.
    """
    ws, err = analyst_workflow_service.get_investigation_workflow_state(db, case_id)
    integrity = case_management_engine.verify_case_audit_integrity(db, case_id)
    return {
        "case_id": case_id,
        "workflow_state": ws,
        "audit_integrity": integrity,
        "allowed_transitions": case_management_engine.ALLOWED_TRANSITIONS.get(ws.get("current_step", "SELECT"), []),
    }


# =============================================================================
# 13. DECISION EFFECTIVENESS METRICS
# =============================================================================
@router.get("/metrics/decision-effectiveness", response_model=DecisionEffectivenessMetrics)
def get_decision_effectiveness_metrics(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
) -> Dict[str, Any]:
    """
    Computes real empirical decision effectiveness metrics from database verifications.
    Explicitly returns INSUFFICIENT_DATA if sample size is zero (zero fabricated metrics).
    """
    return analyst_workflow_service.compute_decision_effectiveness_metrics(db)


# =============================================================================
# 14. TRIAGE EFFECTIVENESS METRICS
# =============================================================================
@router.get("/metrics/triage-effectiveness", response_model=TriageEffectivenessMetrics)
def get_triage_effectiveness_metrics(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
) -> Dict[str, Any]:
    """
    Computes real operational triage performance metrics and queue latency.
    """
    return analyst_workflow_service.compute_triage_effectiveness_metrics(db)


# =============================================================================
# 15. ANALYST FEEDBACK
# =============================================================================
@router.post("/feedback")
def submit_analyst_feedback(
    req: AnalystFeedbackSubmission,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
) -> Dict[str, Any]:
    """
    Submits structured operational analyst feedback.
    """
    analyst_id = (current_user.id if current_user else req.analyst_id)
    analyst_role = (current_user.role if current_user else req.analyst_role).upper()

    data = req.model_dump()
    data["analyst_id"] = analyst_id
    data["analyst_role"] = analyst_role

    return analyst_workflow_service.record_analyst_feedback(db, data)


@router.get("/feedback")
def get_analyst_feedback(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
) -> List[Dict[str, Any]]:
    """
    Retrieves operational feedback history.
    """
    return analyst_workflow_service.get_analyst_feedback(db, limit=limit)


# =============================================================================
# 16. OPERATIONAL REPORT
# =============================================================================
@router.get("/events/{event_id}/report")
def generate_operational_report(
    event_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
) -> Dict[str, Any]:
    """
    Generates standardized 17-section operational analyst report.
    """
    analyst_id = (current_user.id if current_user else "ANALYST")
    try:
        return analyst_workflow_service.generate_operational_analyst_report(
            db=db,
            case_or_event_id=event_id,
            analyst_id=analyst_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
