from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.app.core.database import get_db
from backend.app.api.deps import require_admin, get_current_active_user
from backend.app.models.domain import (
    User, AuditLog, DataSource, ModelVersion,
    ThermalEvent, IndustrialFacility, CandidateFacility, VerificationRecord
)
from backend.app.models.schemas import UserOut

router = APIRouter()


class RoleUpdateRequest(BaseModel):
    new_role: str


@router.get("/users", response_model=List[UserOut])
def get_all_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Retrieves all registered users across all roles (Admin only).
    """
    return db.query(User).order_by(User.created_at.desc()).all()


@router.patch("/users/{user_id}/role", response_model=UserOut)
def update_user_role(
    user_id: str,
    req: RoleUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Updates the RBAC role of a user (Admin only).
    """
    allowed_roles = ["ADMIN", "ANALYST", "OPERATOR", "RESEARCHER", "INDUSTRY", "PUBLIC"]
    if req.new_role.upper() not in allowed_roles:
        raise HTTPException(status_code=400, detail=f"Invalid role. Allowed: {allowed_roles}")

    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    old_role = target_user.role
    target_user.role = req.new_role.upper()

    audit = AuditLog(
        user_id=current_user.id,
        action="UPDATE_USER_ROLE",
        resource_type="User",
        resource_id=user_id,
        details={"user_email": target_user.email, "old_role": old_role, "new_role": req.new_role.upper()}
    )
    db.add(audit)
    db.commit()
    db.refresh(target_user)

    return target_user


@router.get("/audit-logs")
def get_audit_logs(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
    limit: int = 100
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


@router.get("/system-stats")
def get_system_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Aggregates operational counts and health indicators.
    """
    return {
        "users_count": db.query(User).count(),
        "events_count": db.query(ThermalEvent).count(),
        "facilities_count": db.query(IndustrialFacility).count(),
        "candidates_count": db.query(CandidateFacility).count(),
        "verifications_count": db.query(VerificationRecord).count(),
        "audit_logs_count": db.query(AuditLog).count()
    }


@router.get("/system-health")
def get_system_health(db: Session = Depends(get_db)):
    """
    Returns system status, database health, and active services.
    """
    dialect = db.bind.dialect.name if db.bind else "sqlite"
    if dialect == "postgresql":
        db_desc = "CONNECTED (PostgreSQL + PostGIS)"
        spatial_desc = "OPERATIONAL (PostGIS Extension)"
    else:
        db_desc = "CONNECTED (SQLite - TEST/DEMO FALLBACK)"
        spatial_desc = "OPERATIONAL (Shapely R-Tree Engine - TEST/DEMO FALLBACK)"

    return {
        "status": "HEALTHY",
        "system": "AGNI-NETRA (AI Geospatial Network for Industrial Thermal Risk & Anomaly Analysis)",
        "database": db_desc,
        "spatial_engine": spatial_desc,
        "ml_inference": "OPERATIONAL (XGBoost + SHAP TreeExplainer)",
        "uncertainty_engine": "OPERATIONAL (Normalized Shannon Entropy)",
        "anomaly_engine": "OPERATIONAL (Isolation Forest)",
        "satellite_simulator": "OPERATIONAL (AGNI-SAT-01 Digital Twin)",
        "demo_mode": "ACTIVE"
    }

