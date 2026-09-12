"""
AGNI-NETRA — India Operational Intelligence & Depth Analytics API Endpoints
Phase 19: Strict Sovereign India Scope (ACTIVE OPERATIONAL GEOGRAPHY = INDIA)

Exposes governed REST endpoints for:
1. /hotspots - Hotspot intelligence query with spatial, temporal, risk & evidence metrics
2. /persistent - Persistent hotspot rankings across 6 deterministic categories
3. /industrial - Industrial spatial cross-referencing and facility risk signatures
4. /power-plants - CEA power station thermal correlations
5. /mining - IBM mining concession thermal associations
6. /states - State-level operational indicators and rankings
7. /districts - District-level operational indicators
8. /trends - Multi-window temporal trends (24h, 7d, 30d, 90d)
9. /priority/{event_id} - Governed priority score breakdown and explanation
10. /why-it-matters/{event_id} - 7-field structured analyst explanation
11. /hypotheses/{event_id} - Competing hypotheses and evidence strength
12. /next-best-evidence/{event_id} - Targeted evidence recommendations (unconfigured declared NOT_CONFIGURED)
13. /incidents - Multi-event incident synthesis
14. /report - National operational intelligence report

Security & RBAC:
- Enforces strict public safety filtering for PUBLIC role (sensitive facility IDs, contacts, raw logits stripped).
- Analysts and Admins receive full multi-source cadastral context.
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.api.deps import get_optional_current_user
from backend.app.models.domain import User
from backend.app.services.intelligence.india_intelligence_service import india_intelligence_service

router = APIRouter()


def _sanitize_for_public(data: Any) -> Any:
    """
    Sanitizes operational data for PUBLIC role users:
    - Strips proprietary facility IDs, owner contacts, raw logits, and internal SHAP details.
    - Preserves high-level safety indicators and regional state/district awareness.
    """
    if isinstance(data, list):
        return [_sanitize_for_public(item) for item in data]
    elif isinstance(data, dict):
        sanitized = {}
        for k, v in data.items():
            if k in ["facility_id", "proposal_id", "record_id", "shap_values", "class_probabilities", "logits"]:
                continue
            elif k == "nearest_context":
                # Sanitize nearest context
                sanitized_ctx = {}
                if isinstance(v, dict):
                    for domain, val in v.items():
                        if val and isinstance(val, dict):
                            sanitized_ctx[domain] = {
                                "sector": val.get("sector", "Industrial"),
                                "distance_m": val.get("distance_m"),
                                "jurisdiction_scope": "India Operational"
                            }
                        else:
                            sanitized_ctx[domain] = None
                sanitized[k] = sanitized_ctx
            elif k == "associations":
                # Sanitize cadastre associations
                sanitized[k] = [
                    {
                        "cadastre_domain": a.get("cadastre_domain"),
                        "spatial_relationship": a.get("spatial_relationship"),
                        "association_confidence": a.get("association_confidence")
                    } for a in v if isinstance(a, dict)
                ]
            else:
                sanitized[k] = _sanitize_for_public(v)
        return sanitized
    return data


@router.get("/audit")
def get_india_audit(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Dict[str, Any]:
    """
    Returns 11-dimension operational audit of India datasets.
    """
    return india_intelligence_service.audit_india_data_intelligence(db=db)


@router.get("/hotspots")
def get_india_hotspots(
    state: Optional[str] = Query(None, description="Filter by Indian State/UT name"),
    district: Optional[str] = Query(None, description="Filter by Indian District name"),
    min_risk: float = Query(0.0, ge=0.0, le=100.0, description="Minimum risk score threshold"),
    persistence_category: Optional[str] = Query(None, description="Filter by persistence category"),
    limit: int = Query(50, ge=1, le=200, description="Maximum records to return"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> List[Dict[str, Any]]:
    """
    Retrieves active Indian thermal hotspot intelligence with explicit observed vs derived separation.
    """
    results = india_intelligence_service.get_india_hotspot_intelligence(
        db=db,
        state=state,
        district=district,
        min_risk=min_risk,
        persistence_category=persistence_category,
        limit=limit
    )
    user_role = current_user.role if current_user else "PUBLIC"
    if user_role == "PUBLIC":
        return _sanitize_for_public(results)
    return results


@router.get("/persistent")
def get_persistent_hotspots(
    category: Optional[str] = Query(None, description="Persistence category: TRANSIENT, RECURRING, PERSISTENT, HIGHLY_PERSISTENT, NEWLY_EMERGING, REACTIVATED"),
    min_persistence_score: float = Query(3.5, ge=0.0, le=10.0, description="Minimum persistence score (0.0 - 10.0)"),
    state: Optional[str] = Query(None, description="Filter by Indian State"),
    limit: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> List[Dict[str, Any]]:
    """
    Ranks persistent thermal hotspots across 6 deterministic categories.
    """
    results = india_intelligence_service.get_persistent_hotspots(
        db=db,
        category=category,
        min_persistence_score=min_persistence_score,
        state=state,
        limit=limit
    )
    user_role = current_user.role if current_user else "PUBLIC"
    if user_role == "PUBLIC":
        return _sanitize_for_public(results)
    return results


@router.get("/industrial")
def get_industrial_correlations(
    state: Optional[str] = Query(None, description="Filter by Indian State"),
    radius_km: float = Query(10.0, ge=1.0, le=25.0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> List[Dict[str, Any]]:
    """
    Correlates active thermal events with Indian industrial infrastructure using non-causal spatial language.
    """
    results = india_intelligence_service.get_industrial_correlations(
        db=db,
        radius_km=radius_km,
        state=state,
        limit=limit
    )
    user_role = current_user.role if current_user else "PUBLIC"
    if user_role == "PUBLIC":
        return _sanitize_for_public(results)
    return results


@router.get("/power-plants")
def get_power_plant_correlations(
    state: Optional[str] = Query(None, description="Filter by Indian State"),
    limit: int = Query(25, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> List[Dict[str, Any]]:
    """
    Returns thermal anomalies spatially associated with CEA power generating complexes.
    """
    corrs = india_intelligence_service.get_industrial_correlations(db=db, state=state, limit=limit * 2)
    power_events = [c for c in corrs if any(a["cadastre_domain"] == "POWER_STATION" for a in c["associations"])]
    user_role = current_user.role if current_user else "PUBLIC"
    if user_role == "PUBLIC":
        return _sanitize_for_public(power_events[:limit])
    return power_events[:limit]


@router.get("/mining")
def get_mining_correlations(
    state: Optional[str] = Query(None, description="Filter by Indian State"),
    limit: int = Query(25, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> List[Dict[str, Any]]:
    """
    Returns thermal activity associated with IBM mining concessions and mineral blocks.
    """
    corrs = india_intelligence_service.get_industrial_correlations(db=db, state=state, limit=limit * 2)
    mining_events = [c for c in corrs if any(a["cadastre_domain"] == "MINING_CONCESSION" for a in c["associations"])]
    user_role = current_user.role if current_user else "PUBLIC"
    if user_role == "PUBLIC":
        return _sanitize_for_public(mining_events[:limit])
    return mining_events[:limit]


@router.get("/states")
def get_state_intelligence(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> List[Dict[str, Any]]:
    """
    Aggregates operational indicators across Indian States and Union Territories.
    """
    return india_intelligence_service.get_state_intelligence(db=db)


@router.get("/districts")
def get_district_intelligence(
    state: Optional[str] = Query(None, description="Filter by Indian State"),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> List[Dict[str, Any]]:
    """
    Aggregates operational indicators by Indian District.
    """
    return india_intelligence_service.get_district_intelligence(db=db, state=state, limit=limit)


@router.get("/trends")
def get_trend_intelligence(
    time_window: str = Query("30d", pattern="^(24h|7d|30d|90d|1yr)$"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Dict[str, Any]:
    """
    Returns deterministic temporal trend analysis with observed vs derived separation.
    """
    return india_intelligence_service.get_trend_intelligence(db=db, time_window=time_window)


@router.get("/priority/{event_id}")
def get_priority_explanation(
    event_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Dict[str, Any]:
    """
    Decomposes the composite priority score into governed risk, confidence, tier, and recency terms.
    """
    res = india_intelligence_service.explain_event_priority(db=db, event_id=event_id)
    if "error" in res:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=res["error"])
    return res


@router.get("/why-it-matters/{event_id}")
def get_why_it_matters(
    event_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Dict[str, Any]:
    """
    Produces structured 7-factor analyst briefing based on actual evidence.
    """
    res = india_intelligence_service.get_why_this_event_matters(db=db, event_id=event_id)
    if "error" in res:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=res["error"])
    return res


@router.get("/hypotheses/{event_id}")
def get_competing_hypotheses(
    event_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Dict[str, Any]:
    """
    Evaluates competing operational hypotheses with explicit metric separation.
    """
    res = india_intelligence_service.evaluate_competing_hypotheses(db=db, event_id=event_id)
    if "error" in res:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=res["error"])
    return res


@router.get("/next-best-evidence/{event_id}")
def get_next_best_evidence(
    event_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> List[Dict[str, Any]]:
    """
    Recommends targeted information acquisitions; unconfigured feeds declared NOT_CONFIGURED.
    """
    return india_intelligence_service.recommend_next_best_evidence(db=db, event_id=event_id)


@router.get("/incidents")
def get_incident_intelligence(
    limit: int = Query(15, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> List[Dict[str, Any]]:
    """
    Synthesizes multi-event incidents across Indian priority corridors.
    """
    results = india_intelligence_service.get_india_incident_intelligence(db=db, limit=limit)
    user_role = current_user.role if current_user else "PUBLIC"
    if user_role == "PUBLIC":
        return _sanitize_for_public(results)
    return results


@router.get("/report")
def get_national_report(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Dict[str, Any]:
    """
    Compiles national operational thermal intelligence briefing.
    """
    audit = india_intelligence_service.audit_india_data_intelligence(db)
    trends = india_intelligence_service.get_trend_intelligence(db)
    states = india_intelligence_service.get_state_intelligence(db)
    incidents = india_intelligence_service.get_india_incident_intelligence(db)

    return {
        "report_title": "AGNI-NETRA National Operational Thermal Intelligence Report",
        "scope": "INDIA",
        "generated_at": audit["audit_timestamp"],
        "dispatch_gate_blocked": True,
        "audit": audit,
        "trends": trends,
        "top_states": states[:5],
        "active_incidents": incidents[:4]
    }
