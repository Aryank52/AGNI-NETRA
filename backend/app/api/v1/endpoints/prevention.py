"""
AGNI-NETRA — Proactive Fire Prevention & Root-Cause Intelligence REST API Router
Endpoints for case discovery, evidence correlation, hypothesis exploration,
prevention recommendations, authority routing, and governed report review/approval.
"""

import os
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc

from backend.app.core.database import get_db
from backend.app.api.deps import get_current_active_user, get_optional_current_user
from backend.app.models.domain import (
    User,
    PreventionCase,
    RootCauseHypothesisRecord,
    PreventionRecommendationRecord,
    AuthorityDirectoryRecord,
    PreventionReportRecord,
    ReportDeliveryAudit,
    ThermalEvent
)
from backend.app.models.schemas import (
    PreventionCaseOut,
    PreventionCaseListOut,
    PreventionAnalysisRequest,
    RootCauseHypothesisOut,
    PreventionRecommendationOut,
    AuthorityDirectoryOut,
    PreventionReportOut,
    PreventionReportCreateRequest,
    PreventionReportApproveRequest,
    PreventionReportSendRequest,
    ReportDeliveryAuditOut
)
from backend.app.services.intelligence.root_cause_intelligence_service import root_cause_intelligence_service
from backend.app.services.intelligence.authority_registry_service import authority_registry_service
from backend.app.services.intelligence.historical_comparison_engine import HistoricalComparisonEngine
from backend.app.services.prevention_report_generator import prevention_report_generator

router = APIRouter()


@router.post("/analyze", response_model=PreventionCaseOut, status_code=status.HTTP_201_CREATED)
def analyze_event_root_cause(
    req: PreventionAnalysisRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """
    Executes comprehensive point-in-time safe root-cause and prevention analysis for a target thermal event.
    Synthesizes 13 deterministic hypothesis categories, evidence matrices, and actionable recommendations.
    """
    creator = current_user.full_name if current_user else "JARVIS Master Intelligence"
    try:
        case = root_cause_intelligence_service.analyze_event_root_cause(
            db=db,
            event_ref=req.event_ref,
            radius_km=req.radius_km,
            creator=creator
        )
        return case
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Root-cause analysis failed: {str(e)}")


@router.get("/cases", response_model=PreventionCaseListOut)
def list_prevention_cases(
    state: Optional[str] = Query(None, description="Filter by Indian State/UT"),
    district: Optional[str] = Query(None, description="Filter by District"),
    priority: Optional[str] = Query(None, description="Filter by Prevention Priority (CRITICAL, HIGH, ELEVATED, STANDARD)"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by Case Status"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Lists registered prevention cases with filtering and pagination.
    """
    query = db.query(PreventionCase).options(
        joinedload(PreventionCase.hypotheses),
        joinedload(PreventionCase.recommendations)
    )

    if state and state.upper() != "ALL":
        query = query.filter(PreventionCase.state.ilike(f"%{state}%"))
    if district and district.upper() != "ALL":
        query = query.filter(PreventionCase.district.ilike(f"%{district}%"))
    if priority and priority.upper() != "ALL":
        query = query.filter(PreventionCase.prevention_priority == priority.upper())
    if status_filter and status_filter.upper() != "ALL":
        query = query.filter(PreventionCase.status == status_filter.upper())

    total = query.count()
    items = query.order_by(desc(PreventionCase.created_at)).offset((page - 1) * limit).limit(limit).all()

    return {
        "total_count": total,
        "page": page,
        "limit": limit,
        "total_pages": (total + limit - 1) // limit if limit > 0 else 1,
        "items": items
    }


@router.get("/cases/{case_id}", response_model=PreventionCaseOut)
def get_prevention_case(
    case_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieves full details of a PreventionCase by UUID or case number.
    """
    case = db.query(PreventionCase).options(
        joinedload(PreventionCase.hypotheses),
        joinedload(PreventionCase.recommendations)
    ).filter(
        (PreventionCase.id == case_id) | (PreventionCase.case_number == case_id)
    ).first()

    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Prevention case '{case_id}' not found.")
    return case


@router.get("/cases/{case_id}/history")
def get_case_historical_profile(
    case_id: str,
    db: Session = Depends(get_db)
):
    """
    Returns longitudinal historical intelligence, seasonality profile, and baseline deviation for the case.
    """
    case = db.query(PreventionCase).filter(
        (PreventionCase.id == case_id) | (PreventionCase.case_number == case_id)
    ).first()
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Case '{case_id}' not found.")

    return {
        "case_id": case.id,
        "case_number": case.case_number,
        "event_code": case.event_code,
        "recurrence_rate": case.recurrence_score,
        "persistence_score": case.persistence_score,
        "baseline_deviation_ratio": case.baseline_deviation_ratio,
        "temporal_statement": "HISTORICAL CORRELATION DOES NOT IMPLY CAUSATION.",
        "verified_ground_truth_count": len(case.agency_evidence or [])
    }


@router.get("/cases/{case_id}/evidence")
def get_case_evidence_matrix(
    case_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieves supporting evidence, contradicting evidence, unknowns, missing data, and conflicting sources.
    """
    case = db.query(PreventionCase).filter(
        (PreventionCase.id == case_id) | (PreventionCase.case_number == case_id)
    ).first()
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Case '{case_id}' not found.")

    supporting = []
    contradicting = []
    for h in case.hypotheses:
        if h.supporting_evidence:
            for item in h.supporting_evidence:
                supporting.append({"hypothesis": h.title, "evidence": item})
        if h.contradicting_evidence:
            for item in h.contradicting_evidence:
                contradicting.append({"hypothesis": h.title, "contra_indication": item})

    return {
        "case_id": case.id,
        "case_number": case.case_number,
        "evidence_strength_score": case.evidence_strength_score,
        "supporting_evidence": supporting,
        "contradicting_evidence": contradicting,
        "environmental_context": case.environmental_context,
        "material_context": case.material_context,
        "agency_evidence": case.agency_evidence,
        "external_evidence": case.external_evidence,
        "unknowns": case.unknowns,
        "missing_data": case.missing_data,
        "conflicting_sources": case.conflicting_sources
    }


@router.get("/cases/{case_id}/hypotheses", response_model=List[RootCauseHypothesisOut])
def get_case_hypotheses(
    case_id: str,
    db: Session = Depends(get_db)
):
    """
    Returns the 13 structured root-cause hypotheses with confidence and evidence status.
    """
    case = db.query(PreventionCase).filter(
        (PreventionCase.id == case_id) | (PreventionCase.case_number == case_id)
    ).first()
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Case '{case_id}' not found.")
    return case.hypotheses


@router.get("/cases/{case_id}/recommendations", response_model=List[PreventionRecommendationOut])
def get_case_recommendations(
    case_id: str,
    db: Session = Depends(get_db)
):
    """
    Returns evidence-linked preventive recommendations ('MAY REDUCE RECURRENCE RISK').
    """
    case = db.query(PreventionCase).filter(
        (PreventionCase.id == case_id) | (PreventionCase.case_number == case_id)
    ).first()
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Case '{case_id}' not found.")
    return case.recommendations


@router.get("/cases/{case_id}/authorities", response_model=List[AuthorityDirectoryOut])
def get_case_authorities(
    case_id: str,
    db: Session = Depends(get_db)
):
    """
    Resolves verified responsible authorities matching case jurisdiction.
    """
    case = db.query(PreventionCase).filter(
        (PreventionCase.id == case_id) | (PreventionCase.case_number == case_id)
    ).first()
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Case '{case_id}' not found.")

    auths = authority_registry_service.resolve_authorities(
        db=db,
        state=case.state,
        district=case.district,
        facility=case.facility
    )
    return auths


@router.post("/cases/{case_id}/report", response_model=PreventionReportOut, status_code=status.HTTP_201_CREATED)
def create_case_report(
    case_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """
    Compiles formal 24-section Root-Cause & Fire Prevention Intelligence Report in DRAFT state.
    """
    creator = current_user.full_name if current_user else "JARVIS Intelligence Layer"
    try:
        report = prevention_report_generator.create_draft_report(db, case_id, creator_name=creator)
        return report
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Report generation failed: {str(e)}")


@router.get("/cases/{case_id}/reports", response_model=List[PreventionReportOut])
def list_case_reports(
    case_id: str,
    db: Session = Depends(get_db)
):
    """
    Lists all reports compiled for a prevention case.
    """
    case = db.query(PreventionCase).filter(
        (PreventionCase.id == case_id) | (PreventionCase.case_number == case_id)
    ).first()
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Case '{case_id}' not found.")

    reports = db.query(PreventionReportRecord).options(
        joinedload(PreventionReportRecord.deliveries)
    ).filter(
        PreventionReportRecord.case_id == case.id
    ).order_by(desc(PreventionReportRecord.created_at)).all()
    return reports


@router.post("/reports/{report_id}/approve", response_model=PreventionReportOut)
def approve_report(
    report_id: str,
    req: PreventionReportApproveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Human analyst formal approval gate (DRAFT/UNDER_REVIEW -> APPROVED).
    Strictly requires authenticated user with ANALYST or ADMIN role.
    """
    if current_user.role not in ["ANALYST", "ADMIN", "AGENCY"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access Denied: Role '{current_user.role}' is not authorized to approve prevention intelligence reports."
        )

    try:
        report = prevention_report_generator.approve_report(
            db=db,
            report_id=report_id,
            approver_name=current_user.full_name,
            approver_role=current_user.role,
            review_notes=req.review_notes
        )
        return report
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.post("/reports/{report_id}/send", response_model=ReportDeliveryAuditOut)
def send_report(
    report_id: str,
    req: PreventionReportSendRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Executes formal governed report delivery to authorized authority.
    Mandatory safety invariant: Report MUST be APPROVED. User MUST be authenticated with ANALYST or ADMIN role.
    """
    if current_user.role not in ["ANALYST", "ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access Denied: Role '{current_user.role}' is not authorized to dispatch formal reports."
        )

    recipient_data = {
        "recipient_authority_id": req.recipient_authority_id,
        "recipient_name": req.recipient_name,
        "recipient_role": req.recipient_role,
        "recipient_organization": req.recipient_organization,
        "delivery_channel": req.delivery_channel,
        "notes": req.notes
    }
    dispatched_by = {
        "id": current_user.id,
        "email": current_user.email,
        "role": current_user.role
    }

    try:
        audit = prevention_report_generator.send_report(
            db=db,
            report_id=report_id,
            recipient_data=recipient_data,
            dispatched_by=dispatched_by
        )
        return audit
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.get("/reports/{report_id}/download")
@router.get("/reports/{report_id}/pdf")
def download_prevention_report_pdf(
    report_id: str,
    db: Session = Depends(get_db)
):
    """
    Downloads the compiled PDF artifact for a prevention report.
    """
    report = db.query(PreventionReportRecord).filter(
        (PreventionReportRecord.id == report_id) | (PreventionReportRecord.report_number == report_id)
    ).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Report '{report_id}' not found.")

    if not report.pdf_path or not os.path.exists(report.pdf_path):
        # Regenerate PDF if file missing
        os.makedirs("artifacts/prevention_reports", exist_ok=True)
        pdf_path = f"artifacts/prevention_reports/{report.report_number}.pdf"
        prevention_report_generator.generate_pdf(report.sections_data, output_filepath=pdf_path)
        report.pdf_path = pdf_path
        db.commit()

    return FileResponse(
        path=report.pdf_path,
        filename=f"{report.report_number}.pdf",
        media_type="application/pdf"
    )
