"""
AGNI-NETRA — Land Use / Land Cover (LULC) REST API Endpoints
Provides:
- GET /api/v1/lulc/classes
- GET /api/v1/lulc/lookup?latitude=...&longitude=...
- GET /api/v1/lulc/stats
- GET /api/v1/lulc/sources
- GET /api/v1/lulc/features
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text

from backend.app.core.database import get_db
from backend.app.models.domain import LULCSource, LULCClass, LULCSpatialFeature
from backend.app.models.schemas import (
    LULCClassOut, LULCSourceOut, LULCLookupOut, LULCStatsOut
)

router = APIRouter()


@router.get("/sources", response_model=List[LULCSourceOut])
def get_lulc_sources(db: Session = Depends(get_db)):
    """
    Retrieves all registered authoritative LULC data sources (e.g. ISRO Bhuvan 1:50,000).
    """
    sources = db.query(LULCSource).all()
    return sources


@router.get("/classes", response_model=List[LULCClassOut])
def get_lulc_classes(
    source_id: Optional[str] = Query(None, description="Filter by LULC source ID"),
    canonical_class: Optional[str] = Query(None, description="Filter by canonical class"),
    db: Session = Depends(get_db)
):
    """
    Retrieves the canonical LULC class catalog with NRSC Bhuvan Level-II crosswalk.
    """
    query = db.query(LULCClass)
    if source_id:
        query = query.filter(LULCClass.source_id == source_id)
    if canonical_class:
        query = query.filter(LULCClass.canonical_class == canonical_class)
    return query.order_by(LULCClass.source_class_code).all()


@router.get("/lookup", response_model=LULCLookupOut)
def lookup_lulc_coordinate(
    latitude: float = Query(..., ge=-90.0, le=90.0, description="Latitude (EPSG:4326)"),
    longitude: float = Query(..., ge=-180.0, le=180.0, description="Longitude (EPSG:4326)"),
    db: Session = Depends(get_db)
):
    """
    Executes real-time PostGIS multi-source LULC classification with strict deterministic precedence:
    1. REAL_BHUVAN (ISRO / NRSC 1:50,000 Level-II Point-in-Polygon)
    2. REAL_WORLDCOVER (ESA WorldCover 10m National Complementary Raster Grid)
    3. NO_COVERAGE (Points outside Indian territory)
    """
    from backend.app.services.lulc_service import lookup_unified_lulc
    return lookup_unified_lulc(latitude=latitude, longitude=longitude, db=db)


@router.get("/stats", response_model=LULCStatsOut)
def get_lulc_stats(db: Session = Depends(get_db)):
    """
    Returns high-level statistics of configured LULC sources, classes, and PostGIS features.
    """
    sources = db.query(LULCSource).all()
    class_count = db.query(LULCClass).count()
    feature_count = db.query(LULCSpatialFeature).count()

    # Canonical breakdown
    class_dist_rows = db.execute(text("""
        SELECT canonical_class, COUNT(*) as cnt
        FROM lulc_spatial_features
        GROUP BY canonical_class;
    """)).fetchall()
    class_dist = {r.canonical_class: r.cnt for r in class_dist_rows}

    return LULCStatsOut(
        total_sources=len(sources),
        total_classes=class_count,
        total_features=feature_count,
        sources=sources,
        canonical_class_distribution=class_dist
    )
