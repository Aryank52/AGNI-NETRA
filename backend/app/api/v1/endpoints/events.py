import math
from datetime import datetime, timezone
from typing import List, Optional, Any, Dict, Union
from fastapi import APIRouter, Depends, HTTPException, Query, status, Response
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, and_

from backend.app.core.database import get_db
from backend.app.models.domain import ThermalEvent, ThermalDetection, IndustrialFacility, CandidateFacility, ModelPrediction, RiskScore, EventFeature
from backend.app.models.schemas import ThermalEventOut, ThermalDetectionOut, PaginatedEventsOut, EventTraceLineageOut
from backend.app.services.lineage_service import generate_event_trace_lineage

router = APIRouter()


@router.get("", response_model=Union[PaginatedEventsOut, List[ThermalEventOut]])
def get_thermal_events(
    response: Response,
    db: Session = Depends(get_db),
    state: Optional[str] = None,
    district: Optional[str] = None,
    risk_level: Optional[str] = None,
    event_type: Optional[str] = Query(None, alias="event_type", description="Classification class (e.g. Gas Flare, Industrial Fire)"),
    facility_status: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    min_frp: Optional[float] = None,
    min_persistence: Optional[float] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    is_demo: Optional[bool] = None,
    page: Optional[int] = None,
    limit: int = 100,
    offset: int = 0
):
    """
    Retrieves list of clustered thermal events with comprehensive multi-criteria filtering and server-side pagination.
    """
    # Sanitize against FastAPI Query defaults if called programmatically
    if state is not None and not isinstance(state, str):
        state = getattr(state, "default", None)
    if district is not None and not isinstance(district, str):
        district = getattr(district, "default", None)
    if risk_level is not None and not isinstance(risk_level, str):
        risk_level = getattr(risk_level, "default", None)
    if event_type is not None and not isinstance(event_type, str):
        event_type = getattr(event_type, "default", None)
    if facility_status is not None and not isinstance(facility_status, str):
        facility_status = getattr(facility_status, "default", None)
    if status_filter is not None and not isinstance(status_filter, str):
        status_filter = getattr(status_filter, "default", None)
    if min_frp is not None and not isinstance(min_frp, (int, float)):
        min_frp = getattr(min_frp, "default", None)
    if min_persistence is not None and not isinstance(min_persistence, (int, float)):
        min_persistence = getattr(min_persistence, "default", None)
    if start_date is not None and not isinstance(start_date, str):
        start_date = getattr(start_date, "default", None)
    if end_date is not None and not isinstance(end_date, str):
        end_date = getattr(end_date, "default", None)
    if is_demo is not None and not isinstance(is_demo, bool):
        is_demo = getattr(is_demo, "default", None)
    if page is not None and not isinstance(page, int):
        page = getattr(page, "default", None)
    if limit is not None and not isinstance(limit, int):
        limit = getattr(limit, "default", 100)
    if offset is not None and not isinstance(offset, int):
        offset = getattr(offset, "default", 0)

    query = db.query(ThermalEvent).options(
        joinedload(ThermalEvent.prediction),
        joinedload(ThermalEvent.risk),
        joinedload(ThermalEvent.features),
        joinedload(ThermalEvent.facility),
        joinedload(ThermalEvent.candidate_facility)
    )

    # 1. Geographic filtering
    if state and state.upper() not in ["ALL", "INDIA"]:
        query = query.filter(ThermalEvent.state.ilike(f"%{state}%"))
    if district and district.upper() not in ["ALL"]:
        query = query.filter(ThermalEvent.district.ilike(f"%{district}%"))

    # 2. Facility & Operational status
    if facility_status and facility_status.upper() not in ["ALL"]:
        query = query.filter(ThermalEvent.facility_status == facility_status)
    if status_filter and status_filter.upper() not in ["ALL"]:
        query = query.filter(ThermalEvent.status == status_filter)

    # 3. Radiative & Temporal metrics
    if min_frp is not None:
        query = query.filter(ThermalEvent.max_frp >= min_frp)

    if start_date:
        try:
            s_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            query = query.filter(ThermalEvent.last_seen >= s_dt)
        except Exception:
            pass

    if end_date:
        try:
            e_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            query = query.filter(ThermalEvent.first_seen <= e_dt)
        except Exception:
            pass

    # 4. Live vs Demo dataset provenance
    if is_demo is not None:
        query = query.filter(ThermalEvent.is_demo == is_demo)

    events = query.order_by(ThermalEvent.last_seen.desc()).all()

    # 5. Nested filter evaluations (Risk level, Classification class, Persistence score)
    filtered = []
    for e in events:
        if risk_level and risk_level.upper() not in ["ALL"]:
            if not e.risk or e.risk.risk_level != risk_level:
                continue

        if event_type and event_type.upper() not in ["ALL"]:
            if not e.prediction or event_type.lower() not in e.prediction.predicted_class.lower():
                continue

        if min_persistence is not None:
            p_score = e.features.persistence_score if e.features else 0.0
            if p_score < min_persistence:
                continue

        filtered.append(e)

    total_count = len(filtered)
    response.headers["X-Total-Count"] = str(total_count)

    if page is not None and page > 0:
        total_pages = max(1, math.ceil(total_count / limit))
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_items = filtered[start_idx:end_idx]
        return PaginatedEventsOut(
            total_count=total_count,
            page=page,
            limit=limit,
            total_pages=total_pages,
            items=paginated_items
        )

    return filtered[offset:offset + limit]


@router.get("/geojson")
def get_thermal_events_geojson(
    db: Session = Depends(get_db),
    state: Optional[str] = None,
    district: Optional[str] = None,
    risk_level: Optional[str] = None,
    event_type: Optional[str] = None,
    is_demo: Optional[bool] = None,
    min_frp: Optional[float] = None
):
    """
    Optimized GeoJSON FeatureCollection endpoint for MapLibre GL JS layers.
    Includes rich properties for interactive clustering, filtering, timestamp provenance, and styling.
    """
    if state is not None and not isinstance(state, str):
        state = getattr(state, "default", None)
    if district is not None and not isinstance(district, str):
        district = getattr(district, "default", None)
    if risk_level is not None and not isinstance(risk_level, str):
        risk_level = getattr(risk_level, "default", None)
    if event_type is not None and not isinstance(event_type, str):
        event_type = getattr(event_type, "default", None)
    if is_demo is not None and not isinstance(is_demo, bool):
        is_demo = getattr(is_demo, "default", None)
    if min_frp is not None and not isinstance(min_frp, (int, float)):
        min_frp = getattr(min_frp, "default", None)

    query = db.query(ThermalEvent).options(
        joinedload(ThermalEvent.prediction),
        joinedload(ThermalEvent.risk),
        joinedload(ThermalEvent.features)
    )

    if state and state.upper() not in ["ALL", "INDIA"]:
        query = query.filter(ThermalEvent.state.ilike(f"%{state}%"))
    if district and district.upper() not in ["ALL"]:
        query = query.filter(ThermalEvent.district.ilike(f"%{district}%"))
    if is_demo is not None:
        query = query.filter(ThermalEvent.is_demo == is_demo)
    if min_frp is not None:
        query = query.filter(ThermalEvent.max_frp >= min_frp)

    events = query.all()
    features = []

    for e in events:
        r_level = e.risk.risk_level if e.risk else "LOW"
        r_score = e.risk.risk_score if e.risk else 0.0
        p_class = e.prediction.predicted_class if e.prediction else "Uncertain"
        p_conf = e.prediction.confidence if e.prediction else 0.0
        p_score = e.features.persistence_score if e.features else 0.0
        dn_ratio = e.features.day_night_ratio if e.features else 1.0

        if risk_level and risk_level.upper() not in ["ALL"] and r_level != risk_level:
            continue
        if event_type and event_type.upper() not in ["ALL"] and event_type.lower() not in p_class.lower():
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
                "nearest_facility_distance_m": e.nearest_facility_distance_m,
                "landcover_class": e.landcover_class,
                "predicted_class": p_class,
                "confidence": p_conf,
                "risk_level": r_level,
                "risk_score": r_score,
                "persistence_score": p_score,
                "day_night_ratio": dn_ratio,
                "first_seen": e.first_seen.isoformat() if e.first_seen else None,
                "last_seen": e.last_seen.isoformat() if e.last_seen else None,
                "status": e.status,
                "is_demo": e.is_demo,
                "provenance": "LIVE_FIRMS_VIIRS" if not e.is_demo else "DEMO_HISTORICAL_FIRMS"
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
    Retrieves granular intelligence dossier for a single thermal event.
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
    detections = db.query(ThermalDetection).filter(
        ThermalDetection.event_id == event_id
    ).order_by(ThermalDetection.acq_timestamp.desc()).all()
    return detections


@router.get("/{event_id}/trace", response_model=EventTraceLineageOut)
def get_event_trace(event_id: str, db: Session = Depends(get_db)):
    """
    Trace Data API:
    Generates a complete 10-stage scientific data lineage from raw sensor telemetry
    to PostGIS enrichment, machine learning inference, explainability, and decision support.
    """
    try:
        lineage = generate_event_trace_lineage(db, event_id)
        return lineage
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
