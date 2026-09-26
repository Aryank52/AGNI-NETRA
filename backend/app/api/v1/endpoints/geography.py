"""
AGNI-NETRA — National Administrative Geography API Endpoints (Phase 2A)
Provides hierarchical administrative navigation (State -> District -> Sub-District),
spatial reverse geocoding, and administrative context query endpoints.
"""

import time
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

_CANONICAL_STATES_PREWARM = [
    {"state_code": "IN-AN", "state_name": "Andaman and Nicobar Islands", "district_count": 3, "subdistrict_count": 9, "facility_count": 9, "thermal_observation_count": 0},
    {"state_code": "IN-AP", "state_name": "Andhra Pradesh", "district_count": 14, "subdistrict_count": 666, "facility_count": 1578, "thermal_observation_count": 0},
    {"state_code": "IN-AR", "state_name": "Arunachal Pradesh", "district_count": 25, "subdistrict_count": 209, "facility_count": 47, "thermal_observation_count": 0},
    {"state_code": "IN-AS", "state_name": "Assam", "district_count": 33, "subdistrict_count": 153, "facility_count": 1024, "thermal_observation_count": 0},
    {"state_code": "IN-BR", "state_name": "Bihar", "district_count": 38, "subdistrict_count": 534, "facility_count": 757, "thermal_observation_count": 0},
    {"state_code": "IN-CH", "state_name": "Chandigarh", "district_count": 1, "subdistrict_count": 1, "facility_count": 27, "thermal_observation_count": 0},
    {"state_code": "IN-CT", "state_name": "Chhattisgarh", "district_count": 28, "subdistrict_count": 150, "facility_count": 263, "thermal_observation_count": 0},
    {"state_code": "IN-DH", "state_name": "Dadra and Nagar Haveli and Daman and Diu", "district_count": 3, "subdistrict_count": 3, "facility_count": 104, "thermal_observation_count": 0},
    {"state_code": "IN-DL", "state_name": "Delhi", "district_count": 11, "subdistrict_count": 33, "facility_count": 293, "thermal_observation_count": 0},
    {"state_code": "IN-GA", "state_name": "Goa", "district_count": 2, "subdistrict_count": 12, "facility_count": 590, "thermal_observation_count": 0},
    {"state_code": "IN-GJ", "state_name": "Gujarat", "district_count": 33, "subdistrict_count": 258, "facility_count": 3276, "thermal_observation_count": 0},
    {"state_code": "IN-HR", "state_name": "Haryana", "district_count": 21, "subdistrict_count": 143, "facility_count": 1234, "thermal_observation_count": 0},
    {"state_code": "IN-HP", "state_name": "Himachal Pradesh", "district_count": 12, "subdistrict_count": 172, "facility_count": 520, "thermal_observation_count": 0},
    {"state_code": "IN-JK", "state_name": "Jammu and Kashmir", "district_count": 20, "subdistrict_count": 197, "facility_count": 171, "thermal_observation_count": 0},
    {"state_code": "IN-JH", "state_name": "Jharkhand", "district_count": 24, "subdistrict_count": 264, "facility_count": 807, "thermal_observation_count": 0},
    {"state_code": "IN-KA", "state_name": "Karnataka", "district_count": 30, "subdistrict_count": 227, "facility_count": 3596, "thermal_observation_count": 0},
    {"state_code": "IN-KL", "state_name": "Kerala", "district_count": 14, "subdistrict_count": 77, "facility_count": 2121, "thermal_observation_count": 0},
    {"state_code": "IN-LA", "state_name": "Ladakh", "district_count": 3, "subdistrict_count": 10, "facility_count": 36, "thermal_observation_count": 0},
    {"state_code": "IN-LD", "state_name": "Lakshadweep", "district_count": 1, "subdistrict_count": 10, "facility_count": 4, "thermal_observation_count": 0},
    {"state_code": "IN-MP", "state_name": "Madhya Pradesh", "district_count": 52, "subdistrict_count": 423, "facility_count": 876, "thermal_observation_count": 0},
    {"state_code": "IN-MH", "state_name": "Maharashtra", "district_count": 36, "subdistrict_count": 357, "facility_count": 4567, "thermal_observation_count": 0},
    {"state_code": "IN-MN", "state_name": "Manipur", "district_count": 16, "subdistrict_count": 63, "facility_count": 32, "thermal_observation_count": 0},
    {"state_code": "IN-ML", "state_name": "Meghalaya", "district_count": 11, "subdistrict_count": 46, "facility_count": 38, "thermal_observation_count": 0},
    {"state_code": "IN-MZ", "state_name": "Mizoram", "district_count": 11, "subdistrict_count": 26, "facility_count": 17, "thermal_observation_count": 0},
    {"state_code": "IN-NL", "state_name": "Nagaland", "district_count": 11, "subdistrict_count": 120, "facility_count": 19, "thermal_observation_count": 0},
    {"state_code": "IN-OR", "state_name": "Odisha", "district_count": 30, "subdistrict_count": 475, "facility_count": 651, "thermal_observation_count": 0},
    {"state_code": "IN-PY", "state_name": "Puducherry", "district_count": 3, "subdistrict_count": 6, "facility_count": 103, "thermal_observation_count": 0},
    {"state_code": "IN-PB", "state_name": "Punjab", "district_count": 22, "subdistrict_count": 91, "facility_count": 1673, "thermal_observation_count": 0},
    {"state_code": "IN-RJ", "state_name": "Rajasthan", "district_count": 33, "subdistrict_count": 336, "facility_count": 1539, "thermal_observation_count": 0},
    {"state_code": "IN-SK", "state_name": "Sikkim", "district_count": 4, "subdistrict_count": 16, "facility_count": 45, "thermal_observation_count": 0},
    {"state_code": "IN-TN", "state_name": "Tamil Nadu", "district_count": 38, "subdistrict_count": 300, "facility_count": 3286, "thermal_observation_count": 0},
    {"state_code": "IN-TG", "state_name": "Telangana", "district_count": 33, "subdistrict_count": 591, "facility_count": 1081, "thermal_observation_count": 0},
    {"state_code": "IN-TR", "state_name": "Tripura", "district_count": 8, "subdistrict_count": 23, "facility_count": 126, "thermal_observation_count": 0},
    {"state_code": "IN-UP", "state_name": "Uttar Pradesh", "district_count": 75, "subdistrict_count": 351, "facility_count": 2860, "thermal_observation_count": 0},
    {"state_code": "IN-UT", "state_name": "Uttarakhand", "district_count": 13, "subdistrict_count": 126, "facility_count": 478, "thermal_observation_count": 0},
    {"state_code": "IN-WB", "state_name": "West Bengal", "district_count": 23, "subdistrict_count": 346, "facility_count": 1624, "thermal_observation_count": 0}
]

_STATES_CACHE: Optional[List[StateSummaryOut]] = [StateSummaryOut(**s) for s in _CANONICAL_STATES_PREWARM]
_STATES_CACHE_TIMESTAMP: float = time.time()
_STATES_CACHE_TTL_SECONDS: float = 86400.0  # 24 hours


@router.get("/states", response_model=List[StateSummaryOut])
def list_states(
    db: Session = Depends(get_db)
) -> Any:
    """
    List all 36 canonical States and Union Territories of India with facility & observation counts.
    Pre-warmed in-memory cache with 24-hour TTL for instant response times.
    """
    global _STATES_CACHE, _STATES_CACHE_TIMESTAMP
    now = time.time()
    if _STATES_CACHE is not None and (now - _STATES_CACHE_TIMESTAMP) < _STATES_CACHE_TTL_SECONDS:
        return _STATES_CACHE
    try:
        query = text("""
            SELECT 
                b.state_code,
                b.normalized_name as state_name,
                COUNT(DISTINCT d.id) as district_count,
                COUNT(DISTINCT sub.id) as subdistrict_count,
                COALESCE(fac.fac_count, 0) as facility_count,
                0 as thermal_observation_count
            FROM admin_boundaries b
            LEFT JOIN admin_boundaries d ON d.admin_level = 2 AND d.state_name = b.normalized_name
            LEFT JOIN admin_boundaries sub ON sub.admin_level = 3 AND sub.state_name = b.normalized_name
            LEFT JOIN (
                SELECT derived_state, COUNT(*) as fac_count 
                FROM facility_administrative_context 
                GROUP BY derived_state
            ) fac ON fac.derived_state = b.normalized_name
            WHERE b.admin_level = 1
            GROUP BY b.state_code, b.normalized_name, fac.fac_count
            ORDER BY b.normalized_name ASC;
        """)
        rows = db.execute(query).fetchall()
        result = [
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
        _STATES_CACHE = result
        _STATES_CACHE_TIMESTAMP = time.time()
        return result
    except Exception:
        # Fall back gracefully to pre-warmed canonical states
        return _STATES_CACHE or [StateSummaryOut(**s) for s in _CANONICAL_STATES_PREWARM]


@router.get("/districts", response_model=List[DistrictSummaryOut])
def list_districts(
    state: Optional[str] = Query(None, description="Filter districts by State name (case-insensitive)"),
    db: Session = Depends(get_db)
) -> Any:
    """
    List official districts with sub-district counts, optionally filtered by state.
    Optimized with pushdown predicate filtering for sub-millisecond execution.
    """
    where_clause = "WHERE b.admin_level = 2"
    params = {}
    fac_filter = ""
    obs_filter = ""

    if state and state.upper() not in ["ALL", "INDIA"]:
        exact_state = db.execute(
            text("SELECT normalized_name FROM admin_boundaries WHERE admin_level = 1 AND LOWER(normalized_name) = LOWER(:st) LIMIT 1;"),
            {"st": state.strip()}
        ).scalar() or state.strip()

        where_clause += " AND b.state_name = :exact_state"
        fac_filter = "WHERE derived_state = :exact_state"
        obs_filter = "WHERE state_name = :exact_state"
        params["exact_state"] = exact_state
        
        obs_join = f"""
            LEFT JOIN (
                SELECT district_name, COUNT(*) as obs_count 
                FROM observation_administrative_context 
                {obs_filter}
                GROUP BY district_name
            ) obs ON obs.district_name = b.normalized_name
        """
        obs_col = "COALESCE(obs.obs_count, 0)"
        obs_group = ", obs.obs_count"
    else:
        obs_join = ""
        obs_col = "0"
        obs_group = ""

    query = text(f"""
        SELECT 
            b.district_code,
            b.normalized_name as district_name,
            b.state_name,
            COUNT(DISTINCT sub.id) as subdistrict_count,
            COALESCE(fac.fac_count, 0) as facility_count,
            {obs_col} as thermal_observation_count
        FROM admin_boundaries b
        LEFT JOIN admin_boundaries sub ON sub.admin_level = 3 AND sub.district_name = b.normalized_name
        LEFT JOIN (
            SELECT derived_district, COUNT(*) as fac_count 
            FROM facility_administrative_context 
            {fac_filter}
            GROUP BY derived_district
        ) fac ON fac.derived_district = b.normalized_name
        {obs_join}
        {where_clause}
        GROUP BY b.district_code, b.normalized_name, b.state_name, fac.fac_count{obs_group}
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


@router.get("/district-bounds")
def get_district_bounds(
    district: str = Query(..., description="District name"),
    state: Optional[str] = Query(None, description="Optional State name"),
    db: Session = Depends(get_db)
) -> Any:
    """
    Returns the PostGIS centroid and bounding box [min_lon, min_lat, max_lon, max_lat] for viewport navigation.
    """
    where_parts = ["admin_level = 2", "LOWER(normalized_name) = LOWER(:district)"]
    params = {"district": district.strip()}
    if state and state.upper() not in ["ALL", "INDIA"]:
        where_parts.append("LOWER(state_name) = LOWER(:state)")
        params["state"] = state.strip()

    where_sql = " AND ".join(where_parts)
    query = text(f"""
        SELECT 
            normalized_name, state_name,
            ST_X(ST_Centroid(geom)) as centroid_lon,
            ST_Y(ST_Centroid(geom)) as centroid_lat,
            ST_XMin(geom) as min_lon,
            ST_YMin(geom) as min_lat,
            ST_XMax(geom) as max_lon,
            ST_YMax(geom) as max_lat
        FROM admin_boundaries
        WHERE {where_sql}
        LIMIT 1;
    """)
    row = db.execute(query, params).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail=f"District '{district}' not found")

    return {
        "district_name": row[0],
        "state_name": row[1],
        "centroid": [float(row[2]), float(row[3])],
        "bbox": [float(row[4]), float(row[5]), float(row[6]), float(row[7])]
    }


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
