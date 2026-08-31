from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

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
