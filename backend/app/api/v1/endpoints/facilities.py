from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from backend.app.core.database import get_db
from backend.app.models.domain import IndustrialFacility, HistoricalBaseline, FacilityBaseline, ThermalEvent
from backend.app.models.schemas import IndustrialFacilityOut, ThermalEventOut, FacilityBaselineOut
from backend.app.services.baseline_service import generate_thermal_fingerprint, calculate_facility_baseline

router = APIRouter()


@router.get("", response_model=List[IndustrialFacilityOut])
def get_industrial_facilities(
    db: Session = Depends(get_db),
    facility_type: Optional[str] = None,
    state: Optional[str] = None,
    status_filter: Optional[str] = "KNOWN"
):
    """
    Retrieves registered known and verified industrial facilities.
    """
    query = db.query(IndustrialFacility).options(
        joinedload(IndustrialFacility.baselines),
        joinedload(IndustrialFacility.facility_baseline)
    )
    
    if facility_type and facility_type != "ALL":
        query = query.filter(IndustrialFacility.facility_type == facility_type)
    if state and state != "ALL":
        query = query.filter(IndustrialFacility.state.ilike(f"%{state}%"))
    if status_filter and status_filter != "ALL":
        query = query.filter(IndustrialFacility.status == status_filter)

    return query.all()


@router.get("/{facility_id}", response_model=IndustrialFacilityOut)
def get_facility_detail(facility_id: str, db: Session = Depends(get_db)):
    """
    Retrieves full details and baseline metrics for a facility.
    """
    fac = db.query(IndustrialFacility).options(
        joinedload(IndustrialFacility.baselines),
        joinedload(IndustrialFacility.facility_baseline)
    ).filter(IndustrialFacility.id == facility_id).first()
    
    if not fac:
        raise HTTPException(status_code=404, detail="Industrial facility not found")
    return fac


@router.get("/{facility_id}/baseline")
def get_facility_baseline_profile(facility_id: str, db: Session = Depends(get_db)):
    """
    Retrieves empirical facility-specific thermal baseline (mean, median, variance, FRP distribution, status band).
    """
    try:
        baseline = calculate_facility_baseline(db, facility_id)
        return baseline
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{facility_id}/fingerprint")
def get_facility_thermal_fingerprint(facility_id: str, db: Session = Depends(get_db)):
    """
    Computes analytical Thermal Fingerprint Profile for an industrial facility.
    """
    fac = db.query(IndustrialFacility).filter(IndustrialFacility.id == facility_id).first()
    if not fac:
        raise HTTPException(status_code=404, detail="Facility not found")

    events = db.query(ThermalEvent).filter(ThermalEvent.facility_id == facility_id).all()
    event_dicts = [{"avg_frp": e.avg_frp, "max_frp": e.max_frp, "detection_count": e.detection_count} for e in events]
    
    fingerprint = generate_thermal_fingerprint(event_dicts)
    fingerprint["facility_name"] = fac.name
    fingerprint["facility_type"] = fac.facility_type
    fingerprint["state"] = fac.state

    return fingerprint
