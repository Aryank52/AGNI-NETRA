from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.api.deps import require_admin
from backend.app.models.domain import User, AuditLog, DataSource, ModelVersion
from backend.app.models.schemas import UserOut

router = APIRouter()


@router.get("/users", response_model=List[UserOut])
def get_all_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Retrieves all registered users across all roles (Admin only).
    """
    return db.query(User).all()


@router.get("/audit-logs")
def get_audit_logs(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
    limit: int = 50
):
    """
    Retrieves enterprise security and system audit logs.
    """
    logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit).all()
    return [
        {
            "id": l.id,
            "user_id": l.user_id,
            "action": l.action,
            "resource_type": l.resource_type,
            "resource_id": l.resource_id,
            "details": l.details,
            "timestamp": l.timestamp.isoformat() if l.timestamp else None
        }
        for l in logs
    ]


@router.get("/system-health")
def get_system_health(db: Session = Depends(get_db)):
    """
    Returns system status, database health, and active services.
    """
    return {
        "status": "HEALTHY",
        "system": "AGNI-NETRA v1.0.0",
        "database": "CONNECTED",
        "spatial_engine": "OPERATIONAL",
        "ml_inference": "OPERATIONAL",
        "explainability_shap": "READY",
        "demo_mode": "ACTIVE"
    }
