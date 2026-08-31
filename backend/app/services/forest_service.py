"""
AGNI-NETRA — Forest Intelligence Service
Executes multi-source forest context lookups and computes geodesic distances to Protected Areas
and Bhuvan forest canopies.
"""

from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text

from backend.app.models.schemas import ForestLookupOut


def lookup_forest_context(
    latitude: float,
    longitude: float,
    db: Session
) -> ForestLookupOut:
    """
    Evaluates geographic coordinate against official Indian Protected Areas and ISFR canopy density statistics.
    Rules:
    - HIGH: Inside Protected Area OR inside forest polygon (dist_forest == 0) OR dist_pa <= 500m
    - MEDIUM: dist_pa <= 5000m OR dist_forest <= 1000m
    - LOW: dist_pa <= 10000m OR dist_forest <= 3000m
    - NONE: dist_forest > 3000m AND dist_pa > 10000m
    """
    # 1. Check Protected Area Containment
    pa_match = db.execute(text("""
        SELECT id, pa_name, pa_type, state, district, area_sqkm, legal_status
        FROM protected_areas
        WHERE ST_Contains(geom, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326))
        LIMIT 1;
    """), {"lat": latitude, "lon": longitude}).fetchone()

    # 2. Compute Geodesic Distance to nearest Protected Area
    dist_pa_row = db.execute(text("""
        SELECT MIN(ST_Distance(ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, geom::geography)) as dist_pa
        FROM protected_areas;
    """), {"lat": latitude, "lon": longitude}).fetchone()
    dist_pa = round(float(dist_pa_row.dist_pa if dist_pa_row and dist_pa_row.dist_pa is not None else 999999.0), 1)

    # 3. Compute Geodesic Distance to nearest Bhuvan Forest Feature
    dist_for_row = db.execute(text("""
        SELECT MIN(ST_Distance(ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, geom::geography)) as dist_for
        FROM lulc_spatial_features
        WHERE canonical_class = 'FOREST';
    """), {"lat": latitude, "lon": longitude}).fetchone()
    dist_forest = round(float(dist_for_row.dist_for if dist_for_row and dist_for_row.dist_for is not None else 999999.0), 1)

    # 4. Check District ISFR Statistics
    isfr_row = db.execute(text("""
        SELECT s.district, s.percent_of_geo_area, s.total_forest_sqkm, s.very_dense_forest_sqkm
        FROM admin_boundaries a
        JOIN fsi_isfr_district_forest_stats s ON a.id = s.admin_boundary_id
        WHERE a.admin_level = 2
          AND ST_Contains(a.geom, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326))
        LIMIT 1;
    """), {"lat": latitude, "lon": longitude}).fetchone()

    district_name = isfr_row.district if isfr_row else None
    forest_pct = float(isfr_row.percent_of_geo_area) if isfr_row else None

    # Determine explicit rule-based Forest Context Level
    if pa_match or dist_forest == 0.0 or dist_pa <= 500.0:
        context_level = "HIGH"
        density_class = "VDF" if pa_match else "MDF"
        confidence = 0.98 if pa_match else 0.95
        primary_source = "WII_NATIONAL_WILDLIFE_DATABASE" if pa_match else "ISRO_BHUVAN_50K"
        match_method = "POSTGIS_PROTECTED_AREA_POINT_IN_POLYGON" if pa_match else "POSTGIS_FOREST_POINT_IN_POLYGON"
        ref_year = 2024 if pa_match else 2025
    elif dist_pa <= 5000.0 or dist_forest <= 1000.0:
        context_level = "MEDIUM"
        density_class = "OF"
        confidence = 0.90
        primary_source = "FSI_ISFR_2021"
        match_method = "POSTGIS_GEODESIC_BUFFER_PROXIMITY"
        ref_year = 2021
    elif dist_pa <= 10000.0 or dist_forest <= 3000.0:
        context_level = "LOW"
        density_class = "SCRUB"
        confidence = 0.85
        primary_source = "FSI_ISFR_2021"
        match_method = "POSTGIS_GEODESIC_BUFFER_PROXIMITY"
        ref_year = 2021
    else:
        context_level = "NONE"
        density_class = "NON_FOREST"
        confidence = 0.95
        primary_source = "FSI_ISFR_2021"
        match_method = "NO_FOREST_INTERSECT"
        ref_year = 2021

    return ForestLookupOut(
        latitude=latitude,
        longitude=longitude,
        forest_context_level=context_level,
        is_inside_forest=(dist_forest == 0.0 or bool(pa_match)),
        forest_density_class=density_class,
        is_inside_protected_area=bool(pa_match),
        protected_area_id=pa_match.id if pa_match else None,
        protected_area_name=pa_match.pa_name if pa_match else None,
        protected_area_type=pa_match.pa_type if pa_match else None,
        distance_to_forest_m=dist_forest,
        distance_to_protected_area_m=dist_pa,
        is_within_10km_esz_buffer=(dist_pa <= 10000.0),
        nearest_isfr_district=district_name,
        district_forest_cover_pct=forest_pct,
        primary_source=primary_source,
        reference_year=ref_year,
        confidence=confidence,
        spatial_match_method=match_method
    )
