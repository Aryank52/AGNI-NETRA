from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload

from backend.app.core.database import get_db
from backend.app.models.domain import ThermalEvent, RiskScore
from backend.app.models.schemas import ThermalEventOut, RiskScoreOut

router = APIRouter()


@router.get("/critical", response_model=List[ThermalEventOut])
def get_critical_risk_events(db: Session = Depends(get_db)):
    """
    Retrieves all active thermal events flagged as CRITICAL risk.
    """
    events = db.query(ThermalEvent).options(
        joinedload(ThermalEvent.prediction),
        joinedload(ThermalEvent.risk),
        joinedload(ThermalEvent.features)
    ).all()

    return [e for e in events if e.risk and e.risk.risk_level == "CRITICAL"]


@router.get("/summary")
def get_risk_summary(db: Session = Depends(get_db)):
    """
    Aggregates risk score stats across the country.
    """
    scores = db.query(RiskScore).all()
    if not scores:
        return {"avg_risk_score": 0.0, "critical_count": 0, "high_count": 0, "moderate_count": 0, "low_count": 0}

    total_score = sum(s.risk_score for s in scores)
    critical_cnt = sum(1 for s in scores if s.risk_level == "CRITICAL")
    high_cnt = sum(1 for s in scores if s.risk_level == "HIGH")
    mod_cnt = sum(1 for s in scores if s.risk_level == "MODERATE")
    low_cnt = sum(1 for s in scores if s.risk_level == "LOW")

    return {
        "avg_risk_score": round(total_score / len(scores), 1),
        "total_evaluated": len(scores),
        "critical_count": critical_cnt,
        "high_count": high_cnt,
        "moderate_count": mod_cnt,
        "low_count": low_cnt
    }
