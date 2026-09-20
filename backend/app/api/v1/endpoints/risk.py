from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import text

from backend.app.core.database import get_db
from backend.app.api.deps import require_agency
from backend.app.models.domain import ThermalEvent, RiskScore, User
from backend.app.models.schemas import ThermalEventOut, RiskScoreOut

router = APIRouter()


@router.get("/critical", response_model=List[ThermalEventOut])
def get_critical_risk_events(
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_agency)
):
    """
    Retrieves active thermal events flagged as CRITICAL risk with indexed PostGIS/SQL join.
    """
    events = (
        db.query(ThermalEvent)
        .join(RiskScore, ThermalEvent.id == RiskScore.event_id)
        .filter(RiskScore.risk_level == "CRITICAL")
        .options(
            joinedload(ThermalEvent.prediction),
            joinedload(ThermalEvent.risk),
            joinedload(ThermalEvent.features)
        )
        .order_by(ThermalEvent.created_at.desc())
        .limit(limit)
        .all()
    )

    return events


@router.get("/summary")
def get_risk_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_agency)
):
    """
    Aggregates risk score stats across the country with fast SQL execution.
    """
    row = db.execute(text("""
        SELECT 
            AVG(risk_score) as avg_score,
            COUNT(*) as total_count,
            COUNT(CASE WHEN risk_level = 'CRITICAL' THEN 1 END) as crit_cnt,
            COUNT(CASE WHEN risk_level = 'HIGH' THEN 1 END) as high_cnt,
            COUNT(CASE WHEN risk_level = 'MODERATE' THEN 1 END) as mod_cnt,
            COUNT(CASE WHEN risk_level = 'LOW' THEN 1 END) as low_cnt
        FROM risk_scores;
    """)).fetchone()

    if not row or not row[1]:
        return {"avg_risk_score": 0.0, "total_evaluated": 0, "critical_count": 0, "high_count": 0, "moderate_count": 0, "low_count": 0}

    return {
        "avg_risk_score": round(float(row[0] or 0.0), 1),
        "total_evaluated": int(row[1] or 0),
        "critical_count": int(row[2] or 0),
        "high_count": int(row[3] or 0),
        "moderate_count": int(row[4] or 0),
        "low_count": int(row[5] or 0)
    }
