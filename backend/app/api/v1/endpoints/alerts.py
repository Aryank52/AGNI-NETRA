from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from backend.app.core.database import get_db
from backend.app.api.deps import require_analyst, get_current_active_user
from backend.app.models.domain import Alert, User, AuditLog
from backend.app.models.schemas import AlertOut, AlertUpdate
from backend.app.services.alert_workflow_service import alert_workflow_service
from backend.app.services.notification_service import notification_service

router = APIRouter()


class ActionRequest(BaseModel):
    notes: Optional[str] = Field(default=None, description="Analyst justification notes")


class VerifyActionRequest(BaseModel):
    verification_outcome: str = Field(default="CONFIRM", description="Outcome: CONFIRM, CORRECT, MARK_UNCERTAIN, FALSE_ALARM")
    ground_truth_class: str = Field(default="Industrial Fire", description="Verified true classification")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Analyst verification confidence")
    notes: Optional[str] = Field(default=None, description="Supporting analyst notes")


class EscalateActionRequest(BaseModel):
    target_agency: str = Field(default="STATE_POLLUTION_CONTROL_BOARD", description="Target response authority")
    reason: str = Field(default="HIGH_RISK_INDUSTRIAL_ANOMALY", description="Escalation rationale")
    notes: Optional[str] = Field(default=None, description="Additional notes")


class DismissActionRequest(BaseModel):
    reason: str = Field(default="KNOWN_PERMITTED_FLARING", description="Dismissal rationale: FALSE_ALARM, PERMITTED_OPERATION, NEGLIGIBLE_INTENSITY")
    notes: Optional[str] = Field(default=None, description="Dismissal justification")


class TestNotificationRequest(BaseModel):
    recipient_email: Optional[str] = None
    recipient_phone: Optional[str] = None
    subject: str = "Test Thermal Alert"
    message: str = "Test notification dispatch from AGNI-NETRA alert pipeline."


@router.get("")
def list_operational_alerts(
    db: Session = Depends(get_db),
    tier: Optional[str] = Query(None, description="Routing tier filter (TIER_1_AUTO_DISPATCH_CANDIDATE, TIER_2_ANALYST_REVIEW_QUEUE, TIER_3_UNCERTAINTY_QUEUE)"),
    status_filter: Optional[str] = Query(None, alias="status", description="Lifecycle state (NEW, ACKNOWLEDGED, UNDER_INVESTIGATION, VERIFIED, ESCALATED, DISMISSED, CLOSED)"),
    min_risk: Optional[float] = Query(None, description="Minimum risk score threshold (0-100)"),
    state: Optional[str] = Query(None, description="State filter"),
    sort_by: str = Query("priority", description="Sorting criterion: priority, risk, recency"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0)
):
    """
    Retrieves operational alerts with multi-tier routing, state filtering,
    and priority queue ordering.
    """
    return alert_workflow_service.list_alerts(
        db=db,
        tier=tier,
        status=status_filter,
        min_risk=min_risk,
        state=state,
        sort_by=sort_by,
        limit=limit,
        offset=offset
    )


@router.get("/{alert_id}/dossier")
def get_alert_investigation_dossier(
    alert_id: str,
    db: Session = Depends(get_db)
):
    """
    Aggregates comprehensive multi-layer investigation evidence for an alert:
    FIRMS telemetry, industrial facilities, CEA power stations, IBM mining context,
    Bhuvan LULC, FSI forest zones, administrative geography, SHAP attributions,
    and complete audit trail history.
    """
    try:
        return alert_workflow_service.get_alert_investigation_dossier(db, alert_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{alert_id}/acknowledge")
def acknowledge_alert(
    alert_id: str,
    req: ActionRequest,
    db: Session = Depends(get_db)
):
    """
    Transitions alert from NEW to ACKNOWLEDGED.
    """
    try:
        return alert_workflow_service.execute_state_action(
            db=db,
            alert_id=alert_id,
            action="ACKNOWLEDGE",
            target_state="ACKNOWLEDGED",
            analyst_id="ANALYST-OPS-01",
            analyst_name="Duty Thermal Analyst",
            notes=req.notes
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{alert_id}/investigate")
def start_alert_investigation(
    alert_id: str,
    req: ActionRequest,
    db: Session = Depends(get_db)
):
    """
    Transitions alert from ACKNOWLEDGED to UNDER_INVESTIGATION.
    """
    try:
        return alert_workflow_service.execute_state_action(
            db=db,
            alert_id=alert_id,
            action="START_INVESTIGATION",
            target_state="UNDER_INVESTIGATION",
            analyst_id="ANALYST-OPS-01",
            analyst_name="Duty Thermal Analyst",
            notes=req.notes
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{alert_id}/verify")
def verify_alert_decision(
    alert_id: str,
    req: VerifyActionRequest,
    db: Session = Depends(get_db)
):
    """
    Transitions alert from UNDER_INVESTIGATION / ESCALATED to VERIFIED.
    Creates a formal VerificationRecord with ground truth label.
    """
    try:
        return alert_workflow_service.execute_state_action(
            db=db,
            alert_id=alert_id,
            action="VERIFY",
            target_state="VERIFIED",
            analyst_id="ANALYST-OPS-01",
            analyst_name="Duty Thermal Analyst",
            notes=req.notes,
            verification_outcome=req.verification_outcome,
            ground_truth_class=req.ground_truth_class
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{alert_id}/escalate")
def escalate_alert(
    alert_id: str,
    req: EscalateActionRequest,
    db: Session = Depends(get_db)
):
    """
    Transitions alert from UNDER_INVESTIGATION / VERIFIED to ESCALATED.
    """
    try:
        return alert_workflow_service.execute_state_action(
            db=db,
            alert_id=alert_id,
            action="ESCALATE",
            target_state="ESCALATED",
            analyst_id="ANALYST-OPS-01",
            analyst_name="Duty Thermal Analyst",
            notes=f"Escalated to {req.target_agency}. Reason: {req.reason}. Notes: {req.notes or 'None'}"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{alert_id}/dismiss")
def dismiss_alert(
    alert_id: str,
    req: DismissActionRequest,
    db: Session = Depends(get_db)
):
    """
    Transitions alert from NEW / ACKNOWLEDGED / UNDER_INVESTIGATION / ESCALATED to DISMISSED.
    """
    try:
        return alert_workflow_service.execute_state_action(
            db=db,
            alert_id=alert_id,
            action="DISMISS",
            target_state="DISMISSED",
            analyst_id="ANALYST-OPS-01",
            analyst_name="Duty Thermal Analyst",
            notes=f"Dismissed. Reason: {req.reason}. Notes: {req.notes or 'None'}"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{alert_id}/close")
def close_alert(
    alert_id: str,
    req: ActionRequest,
    db: Session = Depends(get_db)
):
    """
    Transitions alert from VERIFIED / ESCALATED / DISMISSED to CLOSED.
    """
    try:
        return alert_workflow_service.execute_state_action(
            db=db,
            alert_id=alert_id,
            action="CLOSE",
            target_state="CLOSED",
            analyst_id="ANALYST-OPS-01",
            analyst_name="Duty Thermal Analyst",
            notes=req.notes
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{alert_id}/audit-trail")
def get_alert_audit_trail(
    alert_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieves chronological audit trail of all actions and state transitions on this alert.
    """
    try:
        dossier = alert_workflow_service.get_alert_investigation_dossier(db, alert_id)
        return {
            "alert_id": alert_id,
            "total_audit_records": len(dossier["audit_trail"]),
            "audit_trail": dossier["audit_trail"]
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/{alert_id}", response_model=AlertOut)
def update_alert_status(
    alert_id: str,
    alert_update: AlertUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Legacy status update endpoint for backward compatibility.
    """
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.status = alert_update.status
    alert.acknowledged_by = current_user.id
    
    audit = AuditLog(
        user_id=current_user.id,
        action="UPDATE_ALERT",
        resource_type="Alert",
        resource_id=alert_id,
        details={"new_status": alert_update.status}
    )
    db.add(audit)
    db.commit()
    db.refresh(alert)
    return alert


@router.post("/test-notification")
def send_test_notification(
    req: TestNotificationRequest,
    current_user: User = Depends(require_analyst)
):
    """
    Dispatches a test notification through configured email and SMS providers.
    """
    results: Dict[str, Any] = {}
    if req.recipient_email:
        results["email"] = notification_service.send_alert_email(
            recipient_email=req.recipient_email,
            subject=req.subject,
            alert_details={"event_code": "TEST-EVT-001", "risk_level": "CRITICAL", "max_frp": 120.0, "facility_name": "Test Facility", "state": "Gujarat"}
        )
    if req.recipient_phone:
        results["sms"] = notification_service.send_sms_alert(
            phone_number=req.recipient_phone,
            message=req.message
        )
    return {
        "status": "PROCESSED",
        "results": results
    }
