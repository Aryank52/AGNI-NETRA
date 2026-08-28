from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.app.core.database import get_db
from backend.app.api.deps import require_analyst, get_current_active_user
from backend.app.models.domain import Alert, User, AuditLog
from backend.app.models.schemas import AlertOut, AlertUpdate
from backend.app.services.notification_service import notification_service

router = APIRouter()


class TestNotificationRequest(BaseModel):
    recipient_email: Optional[str] = None
    recipient_phone: Optional[str] = None
    subject: str = "Test Thermal Alert"
    message: str = "Test notification dispatch from AGNI-NETRA alert pipeline."


@router.get("", response_model=List[AlertOut])
def get_alerts(
    db: Session = Depends(get_db),
    alert_level: Optional[str] = None,
    status_filter: Optional[str] = None,
    limit: int = 50
):
    """
    Retrieves system alerts with status and level filtering.
    """
    query = db.query(Alert)
    if alert_level and alert_level != "ALL":
        query = query.filter(Alert.alert_level == alert_level)
    if status_filter and status_filter != "ALL":
        query = query.filter(Alert.status == status_filter)

    return query.order_by(Alert.created_at.desc()).limit(limit).all()


@router.patch("/{alert_id}", response_model=AlertOut)
def update_alert_status(
    alert_id: str,
    alert_update: AlertUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Updates alert status (e.g. NEW, ACKNOWLEDGED, UNDER REVIEW, VERIFIED, RESOLVED).
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
