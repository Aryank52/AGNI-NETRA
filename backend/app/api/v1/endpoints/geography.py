"""
AGNI-NETRA — National Administrative Geography API Endpoints (Phase 2A)
Provides hierarchical administrative navigation (State -> District -> Sub-District),
spatial reverse geocoding, and administrative context query endpoints.
"""

from typing import List, Optional, Any
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.app.core.database import get_db
from backend.app.models.schemas import (
    AdminBoundaryOut,
    StateSummaryOut,
    DistrictSummaryOut,
    FacilityAdministrativeContextOut,
    AdministrativeReverseLookupOut
)

router = APIRouter()


@router.get("/states", response_model=List[StateSummaryOut])
def list_states(
    db: Session = Depends(get_db)
) -> Any:
    """
    List all 36 canonical States and Union Territories of India with facility & observation counts.
    """
    query = text("""
        SELECT 
            b.state_code,
            b.normalized_name as state_name,
            COUNT(DISTINCT d.id) as district_count,
            COUNT(DISTINCT sub.id) as subdistrict_count,
            COALESCE(fac.fac_count, 0) as facility_count,
            COALESCE(obs.obs_count, 0) as thermal_observation_count
        FROM admin_boundaries b
        LEFT JOIN admin_boundaries d ON d.admin_level = 2 AND d.state_name = b.normalized_name
        LEFT JOIN admin_boundaries sub ON sub.admin_level = 3 AND sub.state_name = b.normalized_name
        LEFT JOIN (
            SELECT derived_state, COUNT(*) as fac_count 
            FROM facility_administrative_context 
            GROUP BY derived_state
        ) fac ON fac.derived_state = b.normalized_name
        LEFT JOIN (
            SELECT state_name, COUNT(*) as obs_count 
            FROM observation_administrative_context 
            GROUP BY state_name
        ) obs ON obs.state_name = b.normalized_name
        WHERE b.admin_level = 1
        GROUP BY b.state_code, b.normalized_name, fac.fac_count, obs.obs_count
        ORDER BY b.normalized_name ASC;
    """)
    rows = db.execute(query).fetchall()
    return [
        StateSummaryOut(
            state_code=r[0],
            state_name=r[1],
            district_count=r[2],
            subdistrict_count=r[3],
            facility_count=r[4],
            thermal_observation_count=r[5]
        )
        for r in rows
    ]


@router.get("/districts", response_model=List[DistrictSummaryOut])
def list_districts(
    state: Optional[str] = Query(None, description="Filter districts by State name (case-insensitive)"),
    db: Session = Depends(get_db)
) -> Any:
    """
    List official districts with sub-district counts, optionally filtered by state.
    """
    where_clause = "WHERE b.admin_level = 2"
    params = {}
    if state:
        where_clause += " AND LOWER(b.state_name) = LOWER(:state)"
        params["state"] = state

    query = text(f"""
        SELECT 
            b.district_code,
            b.normalized_name as district_name,
            b.state_name,
            COUNT(DISTINCT sub.id) as subdistrict_count,
            COALESCE(fac.fac_count, 0) as facility_count,
            COALESCE(obs.obs_count, 0) as thermal_observation_count
        FROM admin_boundaries b
        LEFT JOIN admin_boundaries sub ON sub.admin_level = 3 AND sub.district_name = b.normalized_name
        LEFT JOIN (
            SELECT derived_district, COUNT(*) as fac_count 
            FROM facility_administrative_context 
            GROUP BY derived_district
        ) fac ON fac.derived_district = b.normalized_name
        LEFT JOIN (
            SELECT district_name, COUNT(*) as obs_count 
            FROM observation_administrative_context 
            GROUP BY district_name
        ) obs ON obs.district_name = b.normalized_name
        {where_clause}
        GROUP BY b.district_code, b.normalized_name, b.state_name, fac.fac_count, obs.obs_count
        ORDER BY b.state_name ASC, b.normalized_name ASC;
    """)
    rows = db.execute(query, params).fetchall()
    return [
        DistrictSummaryOut(
            district_code=r[0],
            district_name=r[1],
            state_name=r[2],
            subdistrict_count=r[3],
            facility_count=r[4],
            thermal_observation_count=r[5]
        )
        for r in rows
    ]


@router.get("/subdistricts", response_model=List[AdminBoundaryOut])
def list_subdistricts(
    district: Optional[str] = Query(None, description="Filter by District name"),
    state: Optional[str] = Query(None, description="Filter by State name"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
) -> Any:
    """
    List sub-districts / tehsils / taluks with pagination and filtering.
    """
    where_parts = ["admin_level = 3"]
    params = {"limit": limit, "offset": offset}

    if district:
        where_parts.append("LOWER(district_name) = LOWER(:district)")
        params["district"] = district
    if state:
        where_parts.append("LOWER(state_name) = LOWER(:state)")
        params["state"] = state

    where_sql = " AND ".join(where_parts)
    query = text(f"""
        SELECT 
            id, admin_level, admin_level_name, admin_code, name, normalized_name,
            parent_code, parent_name, state_code, state_name,
            district_code, district_name, subdistrict_code,
            source, source_document, source_version, is_authoritative
        FROM admin_boundaries
        WHERE {where_sql}
        ORDER BY state_name ASC, district_name ASC, normalized_name ASC
        LIMIT :limit OFFSET :offset;
    """)
    rows = db.execute(query, params).fetchall()
    return [
        AdminBoundaryOut(
            id=str(r[0]),
            admin_level=r[1],
            admin_level_name=r[2],
            admin_code=r[3],
            name=r[4],
            normalized_name=r[5],
            parent_code=r[6],
            parent_name=r[7],
            state_code=r[8],
            state_name=r[9],
            district_code=r[10],
            district_name=r[11],
            subdistrict_code=r[12],
            source=r[13],
            source_document=r[14],
            source_version=r[15],
            is_authoritative=r[16]
        )
        for r in rows
    ]


@router.get("/lookup", response_model=AdministrativeReverseLookupOut)
def reverse_geocode(
    latitude: float = Query(..., ge=-90.0, le=90.0, description="Latitude in EPSG:4326"),
    longitude: float = Query(..., ge=-180.0, le=180.0, description="Longitude in EPSG:4326"),
    db: Session = Depends(get_db)
) -> Any:
    """
    Spatially resolve coordinates to India State -> District -> Sub-district hierarchy.
    """
    query = text("""
        WITH pt AS (
            SELECT ST_SetSRID(ST_MakePoint(:lon, :lat), 4326) as geom
        ),
        st AS (
            SELECT state_code, normalized_name as state_name
            FROM admin_boundaries, pt
            WHERE admin_level = 1 AND ST_Within(pt.geom, admin_boundaries.geom)
            LIMIT 1
        ),
        dt AS (
            SELECT district_code, normalized_name as district_name
            FROM admin_boundaries, pt
            WHERE admin_level = 2 AND ST_Within(pt.geom, admin_boundaries.geom)
            LIMIT 1
        ),
        sub AS (
            SELECT subdistrict_code, normalized_name as subdistrict_name
            FROM admin_boundaries, pt
            WHERE admin_level = 3 AND ST_Within(pt.geom, admin_boundaries.geom)
            LIMIT 1
        )
        SELECT 
            st.state_name, st.state_code,
            dt.district_name, dt.district_code,
            sub.subdistrict_name, sub.subdistrict_code
        FROM (SELECT 1) dummy
        LEFT JOIN st ON TRUE
        LEFT JOIN dt ON TRUE
        LEFT JOIN sub ON TRUE;
    """)
    row = db.execute(query, {"lat": latitude, "lon": longitude}).fetchone()
    if not row:
        return AdministrativeReverseLookupOut(
            latitude=latitude,
            longitude=longitude,
            boundary_source="geoBoundaries / Local Government Directory",
            match_method="POSTGIS_SPATIAL_JOIN"
        )

    return AdministrativeReverseLookupOut(
        latitude=latitude,
        longitude=longitude,
        state_name=row[0],
        state_code=row[1],
        district_name=row[2],
        district_code=row[3],
        subdistrict_name=row[4],
        subdistrict_code=row[5],
        boundary_source="geoBoundaries / Local Government Directory",
        match_method="POSTGIS_SPATIAL_JOIN"
    )


@router.get("/facilities/{facility_id}/administrative-context", response_model=FacilityAdministrativeContextOut)
def get_facility_administrative_context(
    facility_id: str,
    db: Session = Depends(get_db)
) -> Any:
    """
    Retrieve derived administrative context and source conflict status for a specific facility.
    """
    query = text("""
        SELECT 
            facility_id, original_state, original_district, original_city,
            derived_state, derived_district, derived_subdistrict,
            state_id, district_id, subdistrict_id,
            has_state_conflict, has_district_conflict,
            spatial_match_method, administrative_source, administrative_confidence
        FROM facility_administrative_context
        WHERE facility_id = :fac_id;
    """)
    row = db.execute(query, {"fac_id": facility_id}).fetchone()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Administrative context not found for facility {facility_id}"
        )

    return FacilityAdministrativeContextOut(
        facility_id=row[0],
        original_state=row[1],
        original_district=row[2],
        original_city=row[3],
        derived_state=row[4],
        derived_district=row[5],
        derived_subdistrict=row[6],
        state_id=str(row[7]) if row[7] else None,
        district_id=str(row[8]) if row[8] else None,
        subdistrict_id=str(row[9]) if row[9] else None,
        has_state_conflict=row[10],
        has_district_conflict=row[11],
        spatial_match_method=row[12],
        administrative_source=row[13],
        administrative_confidence=row[14]
    )
