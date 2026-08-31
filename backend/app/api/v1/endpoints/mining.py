"""
AGNI-NETRA — Mining Intelligence Fusion API Endpoints
Exposes fused OSM mining geometries, IBM lease context, IBM mineral resources, and multi-distance NASA FIRMS thermal telemetry.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import text, func
from typing import List, Optional, Dict, Any

from backend.app.core.database import get_db
from backend.app.models.domain import (
    FacilityMiningEvidence, MiningThermalAssociation, CandidateFacility,
    IndustrialFacility, IbmAuctionedBlock
)
from backend.app.models.schemas import (
    FacilityMiningEvidenceOut, MiningThermalAssociationOut, MiningContextSummaryOut,
    IbmAuctionedBlockOut
)

router = APIRouter()


@router.get("/facilities", response_model=List[FacilityMiningEvidenceOut])
def get_mining_facilities(
    state: Optional[str] = Query(None, description="Filter by Indian State"),
    district: Optional[str] = Query(None, description="Filter by District"),
    potential_tier: Optional[str] = Query(None, description="Filter by IBM Potential Tier: HIGH, MEDIUM, LOW"),
    mineral: Optional[str] = Query(None, description="Filter by Mineral Commodity (e.g., Coal, Iron Ore, Limestone)"),
    thermal_only: Optional[bool] = Query(False, description="Filter only facilities with active FIRMS thermal detections"),
    persistence_category: Optional[str] = Query(None, description="Filter by persistence: HIGH_PERSISTENCE, MODERATE_PERSISTENCE, etc."),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Retrieve fused mining facilities enriched with IBM lease statistics and NASA FIRMS thermal metrics.
    """
    query = db.query(FacilityMiningEvidence).options(joinedload(FacilityMiningEvidence.associations))

    if state:
        query = query.filter(func.lower(FacilityMiningEvidence.state) == state.strip().lower())
    if district:
        query = query.filter(func.lower(FacilityMiningEvidence.district) == district.strip().lower())
    if potential_tier:
        query = query.filter(func.upper(FacilityMiningEvidence.ibm_potential_tier) == potential_tier.strip().upper())
    if mineral:
        query = query.filter(func.lower(FacilityMiningEvidence.mineral_commodity).like(f"%{mineral.strip().lower()}%"))
    if thermal_only:
        query = query.filter(FacilityMiningEvidence.thermal_activity_present == True)
    if persistence_category:
        query = query.filter(FacilityMiningEvidence.thermal_persistence_category == persistence_category.strip())

    return query.order_by(FacilityMiningEvidence.firms_associated_2km.desc()).offset(offset).limit(limit).all()


@router.get("/facilities/{facility_id}", response_model=FacilityMiningEvidenceOut)
def get_mining_facility_detail(
    facility_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieve single mining facility evidence by facility_id.
    """
    record = db.query(FacilityMiningEvidence).options(joinedload(FacilityMiningEvidence.associations)).filter(
        FacilityMiningEvidence.facility_id == facility_id
    ).first()

    if not record:
        raise HTTPException(status_code=404, detail="Mining evidence record not found for facility_id")
    return record


@router.get("/context", response_model=List[MiningContextSummaryOut])
def get_mining_context_summary(
    state: Optional[str] = Query(None, description="Filter by Indian State"),
    potential_tier: Optional[str] = Query(None, description="Filter by Potential Tier: HIGH, MEDIUM, LOW"),
    db: Session = Depends(get_db)
):
    """
    Retrieve aggregate mining lease context across states and districts with active OSM facility counts.
    """
    raw_query = """
        SELECT 
            e.state,
            e.district,
            e.ibm_potential_tier as potential_tier,
            e.ibm_district_lease_count as total_leases,
            e.ibm_district_lease_area_ha as total_area_ha,
            e.ibm_district_minerals as top_minerals,
            COUNT(e.facility_id) as facility_count
        FROM facility_mining_evidence e
        WHERE e.state IS NOT NULL
    """
    params = {}
    if state:
        raw_query += " AND lower(e.state) = :state"
        params["state"] = state.strip().lower()
    if potential_tier:
        raw_query += " AND upper(e.ibm_potential_tier) = :potential_tier"
        params["potential_tier"] = potential_tier.strip().upper()

    raw_query += """
        GROUP BY e.state, e.district, e.ibm_potential_tier, e.ibm_district_lease_count, e.ibm_district_lease_area_ha, e.ibm_district_minerals
        ORDER BY facility_count DESC, e.state ASC;
    """

    rows = db.execute(text(raw_query), params).fetchall()
    results = []
    for r in rows:
        results.append(MiningContextSummaryOut(
            state=r[0],
            district=r[1],
            potential_tier=r[2],
            total_leases=r[3],
            total_area_ha=r[4],
            top_minerals=r[5] if r[5] else [],
            facility_count=r[6]
        ))
    return results


@router.get("/thermal-associations", response_model=List[MiningThermalAssociationOut])
def get_mining_thermal_associations(
    facility_id: Optional[str] = Query(None, description="Filter by facility ID"),
    distance_band: Optional[str] = Query(None, description="Filter by band: 500m, 1km, 2km"),
    min_detections: int = Query(1, ge=1),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Retrieve detailed multi-distance concentric FIRMS thermal association telemetry.
    """
    query = db.query(MiningThermalAssociation).filter(MiningThermalAssociation.detection_count >= min_detections)

    if facility_id:
        query = query.filter(MiningThermalAssociation.facility_id == facility_id)
    if distance_band:
        query = query.filter(MiningThermalAssociation.distance_band == distance_band.strip())

    return query.order_by(MiningThermalAssociation.detection_count.desc()).offset(offset).limit(limit).all()


@router.get("/candidate-sources")
def get_mining_candidate_sources(
    state: Optional[str] = Query(None, description="Filter by state"),
    min_detections: int = Query(3, ge=1),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """
    Retrieve candidate mining thermal sources detected from NASA FIRMS clustering near mining geometry.
    """
    query = db.query(CandidateFacility).filter(
        CandidateFacility.status == "CANDIDATE",
        CandidateFacility.detection_count >= min_detections
    )

    if state:
        query = query.filter(func.lower(CandidateFacility.state) == state.strip().lower())

    candidates = query.order_by(CandidateFacility.detection_count.desc()).limit(limit).all()

    return [{
        "id": c.id,
        "name_label": c.name_label,
        "status": c.status,
        "state": c.state,
        "district": c.district,
        "latitude": c.latitude,
        "longitude": c.longitude,
        "detection_count": c.detection_count,
        "persistence_days": c.persistence_days,
        "industrial_context_score": c.industrial_context_score,
        "first_detected_at": c.first_detected_at,
        "last_detected_at": c.last_detected_at,
        "evidence_summary": c.evidence_summary
    } for c in candidates]


@router.get("/auctioned-blocks", response_model=List[IbmAuctionedBlockOut])
def get_auctioned_mineral_blocks(
    state: Optional[str] = Query(None, description="Filter by Indian State"),
    mineral: Optional[str] = Query(None, description="Filter by Mineral"),
    match_confidence: Optional[str] = Query(None, description="Filter by match confidence: HIGH, MEDIUM, LOW, UNMATCHED"),
    preferred_bidder: Optional[str] = Query(None, description="Filter by preferred bidder"),
    has_geometry: Optional[bool] = Query(None, description="Filter only blocks with inherited geometry"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Retrieve IBM Table 15 Successful Mineral Block Auctions (2024-25).
    """
    query = db.query(IbmAuctionedBlock)

    if state and state != "ALL":
        query = query.filter(func.lower(IbmAuctionedBlock.state).like(f"%{state.strip().lower()}%"))
    if mineral and mineral != "ALL":
        query = query.filter(func.lower(IbmAuctionedBlock.mineral).like(f"%{mineral.strip().lower()}%"))
    if match_confidence and match_confidence != "ALL":
        query = query.filter(func.upper(IbmAuctionedBlock.match_confidence) == match_confidence.strip().upper())
    if preferred_bidder and preferred_bidder != "ALL":
        query = query.filter(func.lower(IbmAuctionedBlock.preferred_bidder).like(f"%{preferred_bidder.strip().lower()}%"))
    if has_geometry is not None:
        if has_geometry:
            query = query.filter(IbmAuctionedBlock.geom.isnot(None))
        else:
            query = query.filter(IbmAuctionedBlock.geom.is_(None))

    return query.order_by(IbmAuctionedBlock.sl_no.asc()).offset(offset).limit(limit).all()

