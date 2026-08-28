from typing import Dict, Any, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload

from backend.app.core.database import get_db
from backend.app.models.domain import (
    ThermalEvent, IndustrialFacility, CandidateFacility,
    Alert, VerificationRecord
)
from backend.app.models.schemas import DashboardKPIs

router = APIRouter()


@router.get("/kpis", response_model=DashboardKPIs)
def get_dashboard_kpis(db: Session = Depends(get_db)):
    """
    Computes top-level command center KPIs.
    """
    active_events = db.query(ThermalEvent).filter(ThermalEvent.status == "ACTIVE").count()
    candidate_facs = db.query(CandidateFacility).filter(CandidateFacility.status == "CANDIDATE").count()
    
    # Persistent sources (active days >= 4 or persistence score >= 3.0)
    events = db.query(ThermalEvent).options(joinedload(ThermalEvent.features), joinedload(ThermalEvent.risk)).all()
    persistent_count = sum(1 for e in events if e.features and e.features.persistence_score >= 3.0)
    
    # Abnormal events
    abnormal_count = sum(1 for e in events if e.features and e.features.baseline_deviation_ratio >= 1.8)
    
    # Critical / High alerts
    critical_alerts = db.query(Alert).filter(Alert.alert_level.in_(["CRITICAL", "HIGH"]), Alert.status == "NEW").count()
    
    # Verification queue items
    verif_queue_count = sum(1 for e in events if (e.prediction and e.prediction.predicted_class == "Uncertain") or e.facility_status == "CANDIDATE")

    return {
        "active_events_count": active_events,
        "industrial_candidates_count": candidate_facs,
        "persistent_sources_count": persistent_count,
        "abnormal_anomalies_count": abnormal_count,
        "critical_alerts_count": critical_alerts,
        "verification_queue_count": verif_queue_count
    }


@router.get("/class-distribution")
def get_class_distribution(db: Session = Depends(get_db)):
    """
    Computes classification distribution for charts.
    """
    events = db.query(ThermalEvent).options(joinedload(ThermalEvent.prediction)).all()
    counts = {}
    for e in events:
        c = e.prediction.predicted_class if e.prediction else "Uncertain"
        counts[c] = counts.get(c, 0) + 1

    total = max(1, len(events))
    res = []
    for k, v in counts.items():
        res.append({
            "label": k,
            "count": v,
            "percentage": round((v / total) * 100.0, 1)
        })
    return res


@router.get("/risk-distribution")
def get_risk_distribution(db: Session = Depends(get_db)):
    """
    Computes risk level breakdown for analytics charts.
    """
    events = db.query(ThermalEvent).options(joinedload(ThermalEvent.risk)).all()
    counts = {"CRITICAL": 0, "HIGH": 0, "MODERATE": 0, "LOW": 0}
    for e in events:
        lvl = e.risk.risk_level if e.risk else "LOW"
        if lvl in counts:
            counts[lvl] += 1

    color_map = {
        "CRITICAL": "#ef4444",
        "HIGH": "#f97316",
        "MODERATE": "#eab308",
        "LOW": "#10b981"
    }

    return [
        {"level": k, "count": v, "color": color_map[k]}
        for k, v in counts.items()
    ]


@router.get("/state-summary")
def get_state_summary(db: Session = Depends(get_db)):
    """
    Aggregates thermal events and average FRP per state.
    """
    events = db.query(ThermalEvent).options(joinedload(ThermalEvent.risk)).all()
    states_map = {}
    for e in events:
        st = e.state or "National / Other"
        if st not in states_map:
            states_map[st] = {"event_count": 0, "total_frp": 0.0, "high_risk_count": 0}
        states_map[st]["event_count"] += 1
        states_map[st]["total_frp"] += e.max_frp
        if e.risk and e.risk.risk_level in ["CRITICAL", "HIGH"]:
            states_map[st]["high_risk_count"] += 1

    result = []
    for st, data in states_map.items():
        result.append({
            "state": st,
            "event_count": data["event_count"],
            "avg_frp": round(data["total_frp"] / max(1, data["event_count"]), 1),
            "high_risk_count": data["high_risk_count"]
        })

    result.sort(key=lambda x: x["event_count"], reverse=True)
    return result
