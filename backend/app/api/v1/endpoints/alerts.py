from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.api.deps import require_analyst, get_current_active_user
from backend.app.models.domain import Alert, User, AuditLog
from backend.app.models.schemas import AlertOut, AlertUpdate

router = APIRouter()


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
    Updates alert status (e.g. ACKNOWLEDGED, RESOLVED).
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
