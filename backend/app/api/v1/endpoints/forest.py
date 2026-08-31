"""
AGNI-NETRA — Forest Intelligence & Protected Areas API Endpoints
Provides access to:
- Official FSI / WII source registries
- ISFR district-level forest canopy density statistics
- Protected Areas Network spatial boundaries (National Parks, Tiger Reserves, Wildlife Sanctuaries, Biospheres)
- Real-time PostGIS forest context & 10km ESZ buffer evaluations
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text

from backend.app.api.deps import get_db
from backend.app.models.domain import FSISource, FSIISFRDistrictStats, ProtectedArea
from backend.app.models.schemas import (
    FSISourceOut, FSIISFRStatsOut, ProtectedAreaOut, ForestLookupOut, ForestStatsOut
)
from backend.app.services.forest_service import lookup_forest_context

router = APIRouter()


@router.get("/sources", response_model=List[FSISourceOut])
def get_forest_sources(db: Session = Depends(get_db)):
    """
    Retrieves the authoritative Forest Intelligence data source registry.
    """
    return db.query(FSISource).order_by(FSISource.reference_year.desc()).all()


@router.get("/stats", response_model=ForestStatsOut)
def get_forest_statistics(db: Session = Depends(get_db)):
    """
    Returns high-level statistics of Indian forest cover from ISFR and Protected Area distribution.
    """
    sources = db.query(FSISource).all()
    stat_count = db.query(FSIISFRDistrictStats).count()
    pa_count = db.query(ProtectedArea).count()

    # Protected Area breakdown by type
    pa_dist_rows = db.execute(text("""
        SELECT pa_type, COUNT(*) as cnt
        FROM protected_areas
        GROUP BY pa_type;
    """)).fetchall()
    pa_dist = {r.pa_type: r.cnt for r in pa_dist_rows}

    # Top forested districts from ISFR
    top_districts = db.query(FSIISFRDistrictStats).order_by(
        FSIISFRDistrictStats.percent_of_geo_area.desc()
    ).limit(10).all()

    return ForestStatsOut(
        total_sources=len(sources),
        total_district_records=stat_count,
        total_protected_areas=pa_count,
        sources=sources,
        protected_area_distribution=pa_dist,
        top_forested_districts=top_districts
    )


@router.get("/protected-areas", response_model=List[ProtectedAreaOut])
def list_protected_areas(
    state: Optional[str] = Query(None, description="Filter by State name"),
    pa_type: Optional[str] = Query(None, description="Filter by PA Type (NATIONAL_PARK, TIGER_RESERVE, WILDLIFE_SANCTUARY, BIOSPHERE_RESERVE)"),
    db: Session = Depends(get_db)
):
    """
    Lists officially notified Protected Areas with legal gazette details and established year.
    """
    query = db.query(ProtectedArea)
    if state:
        query = query.filter(ProtectedArea.state.ilike(f"%{state}%"))
    if pa_type:
        query = query.filter(ProtectedArea.pa_type == pa_type)
    return query.order_by(ProtectedArea.pa_name).all()


@router.get("/lookup", response_model=ForestLookupOut)
def lookup_forest_coordinate(
    latitude: float = Query(..., ge=-90.0, le=90.0, description="Latitude (EPSG:4326)"),
    longitude: float = Query(..., ge=-180.0, le=180.0, description="Longitude (EPSG:4326)"),
    db: Session = Depends(get_db)
):
    """
    Executes real-time PostGIS Point-in-Polygon containment and geodesic distance calculations
    against Indian Protected Areas and ISFR forest canopy density baselines.
    """
    return lookup_forest_context(latitude=latitude, longitude=longitude, db=db)
