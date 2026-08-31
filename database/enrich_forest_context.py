"""
AGNI-NETRA — Phase 4B: Forest Intelligence Context Enrichment Script
Enriches:
1. facility_forest_context for industrial facilities (nearest PA, geodesic distance, 10km ESZ flag)
2. observation_forest_context for a controlled sample of thermal detections
"""

import os
import sys
import logging
from sqlalchemy import text

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.app.core.database import engine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ForestEnrich")


def enrich_facilities(limit: int = 1000):
    logger.info(f"Enriching facility_forest_context for up to {limit} industrial facilities...")
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO facility_forest_context (
                id, facility_id, nearest_protected_area_id, nearest_protected_area_name,
                nearest_protected_area_type, distance_to_protected_area_m, distance_to_forest_m,
                is_inside_esz_10km, esz_evaluation_status, forest_context_level,
                source_id, reference_year, confidence_score, created_at
            )
            SELECT
                'FAC_FOR_' || f.id as id,
                f.id as facility_id,
                pa.id as nearest_protected_area_id,
                pa.pa_name as nearest_protected_area_name,
                pa.pa_type as nearest_protected_area_type,
                ROUND(pa.dist_pa::numeric, 1) as distance_to_protected_area_m,
                ROUND(COALESCE(for_feat.dist_for, 999999.0)::numeric, 1) as distance_to_forest_m,
                (pa.dist_pa <= 10000.0) as is_inside_esz_10km,
                CASE WHEN pa.dist_pa <= 10000.0 THEN 'DISTANCE_WITHIN_10KM' ELSE 'OUTSIDE_10KM_BUFFER' END as esz_evaluation_status,
                CASE
                    WHEN pa.dist_pa <= 500.0 OR COALESCE(for_feat.dist_for, 999999.0) = 0.0 THEN 'HIGH'
                    WHEN pa.dist_pa <= 5000.0 OR COALESCE(for_feat.dist_for, 999999.0) <= 1000.0 THEN 'MEDIUM'
                    WHEN pa.dist_pa <= 10000.0 OR COALESCE(for_feat.dist_for, 999999.0) <= 3000.0 THEN 'LOW'
                    ELSE 'NONE'
                END as forest_context_level,
                'WII_PA_REGISTRY' as source_id,
                2024 as reference_year,
                0.95 as confidence_score,
                CURRENT_TIMESTAMP as created_at
            FROM (
                SELECT id, geom
                FROM industrial_facilities
                LIMIT :lim
            ) f
            CROSS JOIN LATERAL (
                SELECT p.id, p.pa_name, p.pa_type,
                       ST_Distance(f.geom::geography, p.geom::geography) as dist_pa
                FROM protected_areas p
                ORDER BY f.geom <-> p.geom
                LIMIT 1
            ) pa
            LEFT JOIN LATERAL (
                SELECT ST_Distance(f.geom::geography, l.geom::geography) as dist_for
                FROM lulc_spatial_features l
                WHERE l.canonical_class = 'FOREST'
                ORDER BY f.geom <-> l.geom
                LIMIT 1
            ) for_feat ON TRUE
            ON CONFLICT (facility_id) DO UPDATE SET
                nearest_protected_area_id = EXCLUDED.nearest_protected_area_id,
                nearest_protected_area_name = EXCLUDED.nearest_protected_area_name,
                nearest_protected_area_type = EXCLUDED.nearest_protected_area_type,
                distance_to_protected_area_m = EXCLUDED.distance_to_protected_area_m,
                distance_to_forest_m = EXCLUDED.distance_to_forest_m,
                is_inside_esz_10km = EXCLUDED.is_inside_esz_10km,
                esz_evaluation_status = EXCLUDED.esz_evaluation_status,
                forest_context_level = EXCLUDED.forest_context_level;
        """), {"lim": limit})

        count = conn.execute(text("SELECT COUNT(*) FROM facility_forest_context;")).scalar()
        logger.info(f"facility_forest_context now has {count} enriched records.")


def enrich_observations(limit: int = 1000):
    logger.info(f"Enriching observation_forest_context for a controlled sample of {limit} thermal detections...")
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO observation_forest_context (
                id, detection_id, is_inside_forest, forest_density_class,
                is_inside_recorded_forest, is_inside_protected_area,
                protected_area_id, protected_area_type, protected_area_name,
                distance_to_protected_area_m, distance_to_forest_m,
                forest_context_level, forest_fire_evidence,
                source_id, reference_year, confidence_score, spatial_match_method,
                created_at
            )
            SELECT
                'OBS_FOR_' || d.id as id,
                d.id as detection_id,
                (COALESCE(for_feat.dist_for, 999999.0) = 0.0 OR pa.is_inside) as is_inside_forest,
                CASE
                    WHEN pa.is_inside THEN 'VDF'
                    WHEN COALESCE(for_feat.dist_for, 999999.0) = 0.0 THEN 'MDF'
                    WHEN pa.dist_pa <= 5000.0 OR COALESCE(for_feat.dist_for, 999999.0) <= 1000.0 THEN 'OF'
                    WHEN pa.dist_pa <= 10000.0 OR COALESCE(for_feat.dist_for, 999999.0) <= 3000.0 THEN 'SCRUB'
                    ELSE 'NON_FOREST'
                END as forest_density_class,
                (COALESCE(for_feat.dist_for, 999999.0) = 0.0 OR pa.is_inside) as is_inside_recorded_forest,
                pa.is_inside as is_inside_protected_area,
                pa.id as protected_area_id,
                pa.pa_type as protected_area_type,
                pa.pa_name as protected_area_name,
                ROUND(pa.dist_pa::numeric, 1) as distance_to_protected_area_m,
                ROUND(COALESCE(for_feat.dist_for, 999999.0)::numeric, 1) as distance_to_forest_m,
                CASE
                    WHEN pa.is_inside OR COALESCE(for_feat.dist_for, 999999.0) = 0.0 OR pa.dist_pa <= 500.0 THEN 'HIGH'
                    WHEN pa.dist_pa <= 5000.0 OR COALESCE(for_feat.dist_for, 999999.0) <= 1000.0 THEN 'MEDIUM'
                    WHEN pa.dist_pa <= 10000.0 OR COALESCE(for_feat.dist_for, 999999.0) <= 3000.0 THEN 'LOW'
                    ELSE 'NONE'
                END as forest_context_level,
                CASE
                    WHEN pa.is_inside OR COALESCE(for_feat.dist_for, 999999.0) = 0.0 THEN 'INSIDE_CANOPY_HIGH_FOREST_FIRE_PROBABILITY'
                    WHEN pa.dist_pa <= 5000.0 THEN 'PROXIMATE_TO_PROTECTED_AREA'
                    ELSE 'NO_DIRECT_FIRE_EVIDENCE'
                END as forest_fire_evidence,
                CASE WHEN pa.is_inside THEN 'WII_PA_REGISTRY' ELSE 'FSI_ISFR_2021' END as source_id,
                CASE WHEN pa.is_inside THEN 2024 ELSE 2021 END as reference_year,
                CASE WHEN pa.is_inside THEN 0.98 ELSE 0.90 END as confidence_score,
                CASE
                    WHEN pa.is_inside THEN 'POSTGIS_PROTECTED_AREA_POINT_IN_POLYGON'
                    WHEN COALESCE(for_feat.dist_for, 999999.0) = 0.0 THEN 'POSTGIS_BHUVAN_FOREST_POINT_IN_POLYGON'
                    ELSE 'POSTGIS_GEODESIC_BUFFER_PROXIMITY'
                END as spatial_match_method,
                CURRENT_TIMESTAMP as created_at
            FROM (
                SELECT id, ST_SetSRID(ST_MakePoint(longitude, latitude), 4326) as geom
                FROM thermal_detections
                LIMIT :lim
            ) d
            CROSS JOIN LATERAL (
                SELECT p.id, p.pa_name, p.pa_type,
                       ST_Contains(p.geom, d.geom) as is_inside,
                       ST_Distance(d.geom::geography, p.geom::geography) as dist_pa
                FROM protected_areas p
                ORDER BY d.geom <-> p.geom
                LIMIT 1
            ) pa
            LEFT JOIN LATERAL (
                SELECT ST_Distance(d.geom::geography, l.geom::geography) as dist_for
                FROM lulc_spatial_features l
                WHERE l.canonical_class = 'FOREST'
                ORDER BY d.geom <-> l.geom
                LIMIT 1
            ) for_feat ON TRUE
            ON CONFLICT (detection_id) DO UPDATE SET
                is_inside_forest = EXCLUDED.is_inside_forest,
                forest_density_class = EXCLUDED.forest_density_class,
                is_inside_recorded_forest = EXCLUDED.is_inside_recorded_forest,
                is_inside_protected_area = EXCLUDED.is_inside_protected_area,
                protected_area_id = EXCLUDED.protected_area_id,
                protected_area_type = EXCLUDED.protected_area_type,
                protected_area_name = EXCLUDED.protected_area_name,
                distance_to_protected_area_m = EXCLUDED.distance_to_protected_area_m,
                distance_to_forest_m = EXCLUDED.distance_to_forest_m,
                forest_context_level = EXCLUDED.forest_context_level,
                forest_fire_evidence = EXCLUDED.forest_fire_evidence;
        """), {"lim": limit})

        count = conn.execute(text("SELECT COUNT(*) FROM observation_forest_context;")).scalar()
        logger.info(f"observation_forest_context now has {count} enriched records.")


if __name__ == "__main__":
    enrich_facilities(limit=1000)
    enrich_observations(limit=1000)
