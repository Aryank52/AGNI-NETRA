from datetime import datetime
from typing import List, Optional, Any, Dict
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from backend.app.core.database import get_db
from backend.app.models.domain import ThermalEvent, ThermalDetection, IndustrialFacility, CandidateFacility
from backend.app.models.schemas import ThermalEventOut, ThermalDetectionOut

router = APIRouter()


@router.get("", response_model=List[ThermalEventOut])
def get_thermal_events(
    db: Session = Depends(get_db),
    state: Optional[str] = None,
    risk_level: Optional[str] = None,
    facility_status: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    min_frp: Optional[float] = None,
    limit: int = 100,
    offset: int = 0
):
    """
    Retrieves list of clustered thermal events with multi-criteria filtering.
    """
    query = db.query(ThermalEvent).options(
        joinedload(ThermalEvent.prediction),
        joinedload(ThermalEvent.risk),
        joinedload(ThermalEvent.features)
    )

    if state and state != "ALL" and state != "India":
        query = query.filter(ThermalEvent.state.ilike(f"%{state}%"))
    if facility_status and facility_status != "ALL":
        query = query.filter(ThermalEvent.facility_status == facility_status)
    if status_filter:
        query = query.filter(ThermalEvent.status == status_filter)
    if min_frp is not None:
        query = query.filter(ThermalEvent.max_frp >= min_frp)

    events = query.order_by(ThermalEvent.last_seen.desc()).offset(offset).limit(limit).all()

    if risk_level and risk_level != "ALL":
        events = [e for e in events if e.risk and e.risk.risk_level == risk_level]

    return events


@router.get("/geojson")
def get_thermal_events_geojson(
    db: Session = Depends(get_db),
    state: Optional[str] = None,
    risk_level: Optional[str] = None,
    time_window_days: Optional[int] = 30
):
    """
    Optimized GeoJSON FeatureCollection endpoint for MapLibre GL JS layers.
    Includes rich properties for interactive clustering, filtering, and styling.
    """
    query = db.query(ThermalEvent).options(
        joinedload(ThermalEvent.prediction),
        joinedload(ThermalEvent.risk)
    )

    if state and state != "ALL" and state != "India":
        query = query.filter(ThermalEvent.state.ilike(f"%{state}%"))

    events = query.all()
    features = []

    for e in events:
        r_level = e.risk.risk_level if e.risk else "LOW"
        r_score = e.risk.risk_score if e.risk else 0.0
        p_class = e.prediction.predicted_class if e.prediction else "Uncertain"
        p_conf = e.prediction.confidence if e.prediction else 0.0

        if risk_level and risk_level != "ALL" and r_level != risk_level:
            continue

        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [e.longitude, e.latitude]
            },
            "properties": {
                "id": e.id,
                "event_code": e.event_code,
                "state": e.state,
                "district": e.district,
                "max_frp": e.max_frp,
                "avg_frp": e.avg_frp,
                "detection_count": e.detection_count,
                "facility_status": e.facility_status,
                "landcover_class": e.landcover_class,
                "predicted_class": p_class,
                "confidence": p_conf,
                "risk_level": r_level,
                "risk_score": r_score,
                "first_seen": e.first_seen.isoformat() if e.first_seen else None,
                "last_seen": e.last_seen.isoformat() if e.last_seen else None,
                "status": e.status,
                "is_demo": e.is_demo
            }
        }
        features.append(feature)

    return {
        "type": "FeatureCollection",
        "features": features
    }


@router.get("/{event_id}", response_model=ThermalEventOut)
def get_event_detail(event_id: str, db: Session = Depends(get_db)):
    """
    Retrieves granular intelligence for a single thermal event.
    """
    event = db.query(ThermalEvent).options(
        joinedload(ThermalEvent.prediction),
        joinedload(ThermalEvent.risk),
        joinedload(ThermalEvent.features),
        joinedload(ThermalEvent.facility),
        joinedload(ThermalEvent.candidate_facility)
    ).filter(ThermalEvent.id == event_id).first()

    if not event:
        raise HTTPException(status_code=404, detail="Thermal event not found")

    return event


@router.get("/{event_id}/detections", response_model=List[ThermalDetectionOut])
def get_event_detections(event_id: str, db: Session = Depends(get_db)):
    """
    Retrieves the raw satellite thermal observations constituting this event.
    """
    detections = db.query(ThermalDetection).filter(ThermalDetection.event_id == event_id).order_by(ThermalDetection.acq_timestamp.desc()).all()
    return detections
