from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import text

from backend.app.core.database import get_db
from backend.app.models.domain import (
    IndustrialFacility, HistoricalBaseline, FacilityBaseline, ThermalEvent,
    PariveshProjectStaging, IbmMiningLeaseContext, IbmMineralResource,
    FacilityMiningEvidence, MiningThermalAssociation, IbmAuctionedBlock
)
from backend.app.models.schemas import (
    IndustrialFacilityOut, ThermalEventOut, FacilityBaselineOut,
    PariveshProjectOut, IbmMiningLeaseContextOut, IbmMineralResourceOut,
    FacilityMiningEvidenceOut, MiningThermalAssociationOut, IbmAuctionedBlockOut
)
from backend.app.services.baseline_service import generate_thermal_fingerprint, calculate_facility_baseline

router = APIRouter()


@router.get("", response_model=List[IndustrialFacilityOut])
def get_industrial_facilities(
    db: Session = Depends(get_db),
    facility_type: Optional[str] = None,
    state: Optional[str] = None,
    district: Optional[str] = None,
    status_filter: Optional[str] = None,
    search: Optional[str] = None,
    sector: Optional[str] = None,
    nic_code: Optional[str] = None,
    has_clearance: Optional[bool] = None,
    clearance_status: Optional[str] = None,
    limit: int = 500,
    offset: int = 0
):
    """
    Retrieves registered known and verified industrial facilities with search, pagination,
    and environmental clearance filtering support.
    """
    query = db.query(IndustrialFacility).options(
        joinedload(IndustrialFacility.baselines),
        joinedload(IndustrialFacility.facility_baseline)
    )
    
    if facility_type and facility_type != "ALL":
        query = query.filter(IndustrialFacility.facility_type == facility_type)
    if state and state != "ALL":
        query = query.filter(IndustrialFacility.state.ilike(f"%{state}%"))
    if district and district != "ALL":
        query = query.filter(IndustrialFacility.district.ilike(f"%{district}%"))
    if sector and sector != "ALL":
        query = query.filter(IndustrialFacility.master_sector.ilike(f"%{sector}%"))
    if nic_code:
        query = query.filter(IndustrialFacility.nic_code == nic_code)
    if status_filter and status_filter != "ALL":
        query = query.filter(IndustrialFacility.status == status_filter)
    if has_clearance is not None:
        query = query.filter(IndustrialFacility.environmental_clearance_present == has_clearance)
    if clearance_status and clearance_status != "ALL":
        query = query.filter(IndustrialFacility.ec_clearance_status == clearance_status)
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (IndustrialFacility.name.ilike(search_term)) |
            (IndustrialFacility.industry_name.ilike(search_term)) |
            (IndustrialFacility.company_name.ilike(search_term)) |
            (IndustrialFacility.city.ilike(search_term)) |
            (IndustrialFacility.district.ilike(search_term)) |
            (IndustrialFacility.state.ilike(search_term))
        )

    return query.offset(offset).limit(min(limit, 5000)).all()


@router.get("/parivesh/projects", response_model=List[PariveshProjectOut])
def get_parivesh_projects(
    db: Session = Depends(get_db),
    state: Optional[str] = None,
    match_status: Optional[str] = None,
    clearance_status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    """
    Retrieves staged PARIVESH environmental clearance projects and their resolution status.
    """
    query = db.query(PariveshProjectStaging)
    if state and state != "ALL":
        query = query.filter(PariveshProjectStaging.state.ilike(f"%{state}%"))
    if match_status and match_status != "ALL":
        query = query.filter(PariveshProjectStaging.match_status == match_status)
    if clearance_status and clearance_status != "ALL":
        query = query.filter(PariveshProjectStaging.clearance_status == clearance_status)

    return query.offset(offset).limit(min(limit, 1000)).all()


@router.get("/ibm/mining-leases", response_model=List[IbmMiningLeaseContextOut])
def get_ibm_mining_lease_context(
    db: Session = Depends(get_db),
    state: Optional[str] = None,
    district: Optional[str] = None,
    mineral: Optional[str] = None,
    table_number: Optional[str] = None,
    potential_category: Optional[str] = None,
    aggregation_level: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    """
    Retrieves official IBM Mining Lease Bulletin contextual evidence records.
    """
    query = db.query(IbmMiningLeaseContext)
    if state and state != "ALL":
        query = query.filter(IbmMiningLeaseContext.state.ilike(f"%{state}%"))
    if district and district != "ALL":
        query = query.filter(IbmMiningLeaseContext.district.ilike(f"%{district}%"))
    if mineral and mineral != "ALL":
        query = query.filter(IbmMiningLeaseContext.mineral.ilike(f"%{mineral}%"))
    if table_number and table_number != "ALL":
        query = query.filter(IbmMiningLeaseContext.table_number == table_number)
    if potential_category and potential_category != "ALL":
        query = query.filter(IbmMiningLeaseContext.potential_category == potential_category)
    if aggregation_level and aggregation_level != "ALL":
        query = query.filter(IbmMiningLeaseContext.aggregation_level == aggregation_level)

    return query.offset(offset).limit(min(limit, 1000)).all()


@router.get("/ibm/mineral-resources", response_model=List[IbmMineralResourceOut])
def get_ibm_mineral_resources(
    db: Session = Depends(get_db),
    commodity: Optional[str] = None,
    mineral: Optional[str] = None,
    not_estimated: Optional[bool] = None,
    limit: int = 100,
    offset: int = 0
):
    """
    Retrieves official IBM National Mineral Inventory (NMI) resource records.
    """
    query = db.query(IbmMineralResource)
    if commodity and commodity != "ALL":
        query = query.filter(IbmMineralResource.commodity.ilike(f"%{commodity}%"))
    if mineral and mineral != "ALL":
        query = query.filter(IbmMineralResource.mineral.ilike(f"%{mineral}%"))
    if not_estimated is not None:
        query = query.filter(IbmMineralResource.not_estimated == not_estimated)

    return query.order_by(IbmMineralResource.sl_no.asc()).offset(offset).limit(min(limit, 1000)).all()


@router.get("/ibm/auctioned-blocks", response_model=List[IbmAuctionedBlockOut])
def get_ibm_auctioned_blocks(
    db: Session = Depends(get_db),
    state: Optional[str] = None,
    mineral: Optional[str] = None,
    match_confidence: Optional[str] = None,
    preferred_bidder: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    """
    Retrieves official IBM Table 15 Successful Auctioned Mineral Block records (2024-25).
    """
    query = db.query(IbmAuctionedBlock)
    if state and state != "ALL":
        query = query.filter(IbmAuctionedBlock.state.ilike(f"%{state}%"))
    if mineral and mineral != "ALL":
        query = query.filter(IbmAuctionedBlock.mineral.ilike(f"%{mineral}%"))
    if match_confidence and match_confidence != "ALL":
        query = query.filter(IbmAuctionedBlock.match_confidence == match_confidence.upper())
    if preferred_bidder and preferred_bidder != "ALL":
        query = query.filter(IbmAuctionedBlock.preferred_bidder.ilike(f"%{preferred_bidder}%"))

    return query.order_by(IbmAuctionedBlock.sl_no.asc()).offset(offset).limit(min(limit, 1000)).all()


@router.get("/{facility_id}", response_model=IndustrialFacilityOut)
def get_facility_detail(facility_id: str, db: Session = Depends(get_db)):
    """
    Retrieves full details, baseline metrics, and mining evidence for a facility.
    """
    fac = db.query(IndustrialFacility).options(
        joinedload(IndustrialFacility.baselines),
        joinedload(IndustrialFacility.facility_baseline),
        joinedload(IndustrialFacility.mining_evidence).joinedload(FacilityMiningEvidence.associations)
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


@router.get("/{facility_id}/intelligence")
def get_facility_deep_intelligence(facility_id: str, db: Session = Depends(get_db)):
    """
    Comprehensive Industrial Facility Thermal & Geospatial Intelligence Dossier:
    Returns facility identity, sector, coordinates, thermal baseline, nearby thermal events,
    multi-year historical activity, nearby power stations, IBM mining context, and ecological proximity.
    """
    fac = db.query(IndustrialFacility).options(
        joinedload(IndustrialFacility.facility_baseline)
    ).filter(IndustrialFacility.id == facility_id).first()

    if not fac:
        raise HTTPException(status_code=404, detail="Industrial facility not found")

    lat, lon = fac.latitude, fac.longitude

    # 1. Nearby active thermal events within 5km
    nearby_events = []
    if lat is not None and lon is not None:
        evt_rows = db.execute(text("""
            SELECT id, event_code, max_frp, avg_frp, detection_count,
                   state, district, status,
                   ROUND(ST_Distance(
                       ST_SetSRID(ST_Point(longitude, latitude), 4326)::geography,
                       ST_SetSRID(ST_Point(:lon, :lat), 4326)::geography
                   )::numeric, 1) as dist_m
            FROM thermal_events
            WHERE ST_DWithin(
                ST_SetSRID(ST_Point(longitude, latitude), 4326)::geography,
                ST_SetSRID(ST_Point(:lon, :lat), 4326)::geography,
                5000
            )
            ORDER BY dist_m ASC
            LIMIT 10;
        """), {"lon": lon, "lat": lat}).fetchall()

        nearby_events = [
            {
                "id": r[0],
                "event_code": r[1],
                "max_frp": float(r[2] or 0.0),
                "avg_frp": float(r[3] or 0.0),
                "detection_count": r[4],
                "state": r[5],
                "district": r[6],
                "status": r[7],
                "distance_m": float(r[8])
            }
            for r in evt_rows
        ]

    # 2. Nearby CEA Thermal Power Stations (within state/district)
    nearby_power = []
    if fac.district:
        p_rows = db.execute(text("""
            SELECT id, project_name, organisation, prime_mover, installed_capacity_mw
            FROM cea_power_stations_staging
            WHERE state ILIKE :st
            ORDER BY installed_capacity_mw DESC NULLS LAST
            LIMIT 5;
        """), {"st": f"%{fac.state or ''}%"}).fetchall()
        nearby_power = [
            {
                "id": str(r[0]),
                "project_name": r[1],
                "organisation": r[2],
                "prime_mover": r[3],
                "installed_capacity_mw": r[4]
            }
            for r in p_rows
        ]

    # 3. Nearby IBM Mining Leases in district
    nearby_mining = []
    if fac.district:
        m_rows = db.execute(text("""
            SELECT id, mineral, lease_count, lease_area_ha, sector
            FROM ibm_mining_lease_context
            WHERE district ILIKE :dist
            ORDER BY lease_area_ha DESC NULLS LAST
            LIMIT 5;
        """), {"dist": f"%{fac.district}%"}).fetchall()
        nearby_mining = [
            {
                "id": str(r[0]),
                "mineral": r[1],
                "lease_count": r[2],
                "lease_area_ha": r[3],
                "sector": r[4]
            }
            for r in m_rows
        ]

    # 4. Nearest Protected Wildlife Sanctuary
    nearest_protected = None
    if lat is not None and lon is not None:
        pa_row = db.execute(text("""
            SELECT id, pa_name, pa_type, area_sqkm,
                   ROUND(ST_Distance(geom, ST_SetSRID(ST_Point(:lon, :lat), 4326)::geography)::numeric, 1) as dist_m
            FROM protected_areas
            ORDER BY dist_m ASC
            LIMIT 1;
        """), {"lon": lon, "lat": lat}).fetchone()
        if pa_row:
            nearest_protected = {
                "id": pa_row[0],
                "name": pa_row[1],
                "type": pa_row[2],
                "area_sqkm": pa_row[3],
                "distance_m": float(pa_row[4])
            }

    base = fac.facility_baseline
    return {
        "facility": {
            "id": fac.id,
            "name": fac.name or fac.plant_name or "Industrial Facility",
            "facility_type": fac.facility_type,
            "master_sector": fac.master_sector,
            "industry_type": fac.industry_type,
            "company_name": fac.company_name,
            "latitude": fac.latitude,
            "longitude": fac.longitude,
            "state": fac.state,
            "district": fac.district,
            "city": fac.city,
            "operating_status": fac.operating_status or "OPERATIONAL",
            "environmental_clearance_present": fac.environmental_clearance_present,
            "ec_clearance_status": fac.ec_clearance_status,
            "ec_proposal_id": fac.ec_proposal_id,
            "energy_intensity": fac.energy_intensity,
            "plant_capacity": fac.plant_capacity
        },
        "baseline": {
            "mean_frp": base.mean_frp if base else 45.0,
            "max_historical_frp": base.max_historical_frp if base else (base.mean_frp * 1.8 if base else 90.0),
            "frequency_days": base.frequency_days if base else 15,
            "day_night_ratio": base.day_night_ratio if base else 1.0,
            "status_band": base.status_band if base else "NORMAL"
        },
        "historical_activity": {
            "firms_detections_500m": fac.firms_detections_500m or 0,
            "firms_detections_1km": fac.firms_detections_1km or 0,
            "firms_detections_2km": fac.firms_detections_2km or 0,
            "thermal_activity_status": fac.thermal_activity_status or "HISTORICALLY_ACTIVE"
        },
        "nearby_thermal_events": nearby_events,
        "nearby_power_stations": nearby_power,
        "nearby_mining_leases": nearby_mining,
        "ecological_context": {
            "nearest_protected_area": nearest_protected,
            "forest_related_flag": fac.forest_related_flag,
            "wildlife_related_flag": fac.wildlife_related_flag
        }
    }
