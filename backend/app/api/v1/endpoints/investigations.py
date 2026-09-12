"""
Investigation Case Management & Audit Governance REST API Endpoints (JARVIS Phase 14)
Implements:
- GET /api/v1/investigations/{id}
- GET /api/v1/investigations/{id}/timeline
- GET /api/v1/investigations/{id}/audit
- GET /api/v1/investigations/{id}/assessments
- GET /api/v1/investigations/{id}/evidence-reviews
- GET /api/v1/investigations/{id}/evidence-requests
- GET /api/v1/investigations/{id}/reports
- POST /api/v1/investigations/{id}/actions
- POST /api/v1/investigations/{id}/notes
- POST /api/v1/investigations/{id}/evidence-reviews
- POST /api/v1/investigations/{id}/evidence-requests
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.api.deps import get_optional_current_user
from backend.app.models.domain import (
    User,
    InvestigationWorkspace,
    InvestigationAuditLog,
    AssessmentVersion,
    EvidenceReview,
    EvidenceRequest,
    CaseNote,
    ReportVersion,
)
from backend.app.models.jarvis_schemas import (
    InvestigationWorkspaceSchema,
    CaseActionExecutionRequest,
    CaseNoteCreateRequest,
    EvidenceReviewUpdateRequest,
    EvidenceRequestCreateRequest,
)
from backend.app.models.canonical import (
    CaseTimelineItem,
    AssessmentVersionRecord,
    EvidenceReviewRecord,
    EvidenceRequestRecord,
    CaseNoteRecord,
    ReportVersionRecord,
    InvestigationAuditRecord,
)
from backend.app.services.jarvis.jarvis_workspace import workspace_manager
from backend.app.services.governance.case_management import (
    case_management_engine,
    CaseStateTransitionError,
    CaseAuthorizationError,
)

router = APIRouter()


@router.get("/{investigation_id}", response_model=InvestigationWorkspaceSchema)
def get_investigation_case(
    investigation_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> InvestigationWorkspace:
    """
    Retrieves investigation workspace case details with strict RBAC enforcement.
    """
    user_role = current_user.role if current_user else "ANALYST"
    user_id = current_user.id if current_user else None

    ws, err = workspace_manager.get_workspace(db, investigation_id, user_role=user_role, user_id=user_id)
    if not ws:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=err or "Investigation workspace not found.")
    return ws


@router.get("/{investigation_id}/timeline", response_model=List[CaseTimelineItem])
def get_investigation_timeline(
    investigation_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> List[CaseTimelineItem]:
    """
    Returns deterministic chronological case timeline across all operational milestones.
    """
    user_role = current_user.role if current_user else "ANALYST"
    user_id = current_user.id if current_user else None

    ws, err = workspace_manager.get_workspace(db, investigation_id, user_role=user_role, user_id=user_id)
    if not ws:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=err or "Investigation not found.")

    return case_management_engine.get_case_timeline(db, investigation_id)


@router.get("/{investigation_id}/audit", response_model=List[InvestigationAuditRecord])
def get_investigation_audit_trail(
    investigation_id: str,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> List[InvestigationAuditLog]:
    """
    Returns immutable append-only audit trail records for this investigation.
    """
    user_role = current_user.role if current_user else "ANALYST"
    if user_role == "PUBLIC":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Role 'PUBLIC' is not authorized to access internal audit logs.")

    logs = (
        db.query(InvestigationAuditLog)
        .filter(InvestigationAuditLog.case_id == investigation_id)
        .order_by(InvestigationAuditLog.timestamp.desc())
        .limit(limit)
        .all()
    )
    return logs


@router.get("/{investigation_id}/assessments", response_model=List[AssessmentVersionRecord])
def get_assessment_versions(
    investigation_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> List[AssessmentVersion]:
    """
    Returns versioned assessment history with evidence and uncertainty deltas.
    """
    user_role = current_user.role if current_user else "ANALYST"
    if user_role == "PUBLIC":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Role 'PUBLIC' cannot view detailed assessment version lineage.")

    versions = (
        db.query(AssessmentVersion)
        .filter(AssessmentVersion.case_id == investigation_id)
        .order_by(AssessmentVersion.version_number.asc())
        .all()
    )
    return versions


@router.get("/{investigation_id}/evidence-reviews", response_model=List[EvidenceReviewRecord])
def get_evidence_reviews(
    investigation_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> List[EvidenceReview]:
    """
    Returns analyst review decisions across individual evidence items.
    """
    user_role = current_user.role if current_user else "ANALYST"
    if user_role == "PUBLIC":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Role 'PUBLIC' cannot view internal evidence reviews.")

    return db.query(EvidenceReview).filter(EvidenceReview.case_id == investigation_id).all()


@router.get("/{investigation_id}/evidence-requests", response_model=List[EvidenceRequestRecord])
def get_evidence_requests(
    investigation_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> List[EvidenceRequest]:
    """
    Returns open and resolved formal evidence requests for this case.
    """
    user_role = current_user.role if current_user else "ANALYST"
    if user_role == "PUBLIC":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Role 'PUBLIC' cannot view evidence requests.")

    return db.query(EvidenceRequest).filter(EvidenceRequest.case_id == investigation_id).all()


@router.get("/{investigation_id}/reports", response_model=List[ReportVersionRecord])
def get_report_versions(
    investigation_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> List[ReportVersion]:
    """
    Returns versioned reproducible reports generated for this investigation.
    """
    user_role = current_user.role if current_user else "ANALYST"
    reports = db.query(ReportVersion).filter(ReportVersion.case_id == investigation_id).order_by(ReportVersion.report_version.desc()).all()
    if user_role == "PUBLIC":
        # Mask non-public-safe reports
        return [r for r in reports if r.presentation_mode == "PUBLIC_SAFE"]
    return reports


@router.post("/{investigation_id}/actions")
def execute_case_action(
    investigation_id: str,
    req: CaseActionExecutionRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Dict[str, Any]:
    """
    Executes or proposes a governed case action with strict RBAC and write safety validation.
    """
    user_role = current_user.role if current_user else "ANALYST"
    user_id = current_user.id if current_user else "ANALYST_HUMAN"

    ws, err = workspace_manager.get_workspace(db, investigation_id, user_role=user_role, user_id=user_id)
    if not ws:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=err or "Investigation not found.")

    try:
        res = case_management_engine.propose_or_execute_action(
            db=db,
            workspace=ws,
            action=req.action,
            actor_id=user_id,
            actor_role=user_role,
            reason=req.reason,
            evidence_ids=req.evidence_ids,
            supporting_evidence=req.supporting_evidence,
            verifier=req.verifier or user_id,
            confirm_governed_action=req.confirm_governed_action,
            is_autonomous_call=False
        )
        return res
    except CaseAuthorizationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except CaseStateTransitionError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{investigation_id}/notes", response_model=CaseNoteRecord)
def add_case_note(
    investigation_id: str,
    req: CaseNoteCreateRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> CaseNote:
    """
    Adds a structured analyst note. Prohibits JARVIS autonomous impersonation.
    """
    user_role = current_user.role if current_user else "ANALYST"
    user_id = current_user.id if current_user else "ANALYST_HUMAN"

    ws, err = workspace_manager.get_workspace(db, investigation_id, user_role=user_role, user_id=user_id)
    if not ws:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=err or "Investigation not found.")

    try:
        note = case_management_engine.add_case_note(
            db=db,
            case_id=investigation_id,
            author=user_id,
            author_role=user_role,
            content=req.content,
            case_version=req.case_version or 1
        )
        return note
    except CaseAuthorizationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{investigation_id}/evidence-reviews", response_model=EvidenceReviewRecord)
def review_evidence_item(
    investigation_id: str,
    req: EvidenceReviewUpdateRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> EvidenceReview:
    """
    Records an analyst review decision for an evidence item.
    """
    user_role = current_user.role if current_user else "ANALYST"
    user_id = current_user.id if current_user else "ANALYST_HUMAN"

    ws, err = workspace_manager.get_workspace(db, investigation_id, user_role=user_role, user_id=user_id)
    if not ws:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=err or "Investigation not found.")

    try:
        rev = case_management_engine.review_evidence_item(
            db=db,
            case_id=investigation_id,
            evidence_id=req.evidence_id,
            status=req.status,
            reviewer_id=user_id,
            reviewer_role=user_role,
            notes=req.notes
        )
        return rev
    except CaseAuthorizationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{investigation_id}/evidence-requests", response_model=EvidenceRequestRecord)
def create_evidence_request(
    investigation_id: str,
    req: EvidenceRequestCreateRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> EvidenceRequest:
    """
    Creates a formal evidence request for additional sensor or external data.
    """
    user_role = current_user.role if current_user else "ANALYST"
    user_id = current_user.id if current_user else "ANALYST_HUMAN"

    ws, err = workspace_manager.get_workspace(db, investigation_id, user_role=user_role, user_id=user_id)
    if not ws:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=err or "Investigation not found.")

    try:
        ev_req = case_management_engine.create_evidence_request(
            db=db,
            case_id=investigation_id,
            requested_source=req.requested_source,
            reason=req.reason,
            uncertainty_target=req.uncertainty_target,
            priority=req.priority or "MEDIUM",
            requested_by=user_id,
            actor_role=user_role
        )
        return ev_req
    except CaseAuthorizationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
