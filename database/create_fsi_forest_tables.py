"""
AGNI-NETRA — Phase 4B: Forest Intelligence & FSI / Protected Areas PostGIS Table DDL
Creates:
1. fsi_sources
2. fsi_isfr_district_forest_stats
3. protected_areas
4. observation_forest_context
5. facility_forest_context
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
logger = logging.getLogger("FSISchema")


def create_fsi_tables():
    logger.info("Initializing Forest Intelligence & Protected Area Tables in PostgreSQL/PostGIS...")
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))

        # 1. Source Registry
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS fsi_sources (
                id VARCHAR(64) PRIMARY KEY,
                source_name VARCHAR(100) UNIQUE NOT NULL,
                organization VARCHAR(255) NOT NULL,
                dataset_name VARCHAR(255) NOT NULL,
                reference_year INTEGER NOT NULL,
                product_version VARCHAR(50) NOT NULL,
                access_method VARCHAR(100) NOT NULL,
                source_url VARCHAR(500) NOT NULL,
                license VARCHAR(150) NOT NULL,
                metadata_info JSONB DEFAULT '{}'::jsonb,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """))

        # 2. Official ISFR District Forest Cover Statistics
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS fsi_isfr_district_forest_stats (
                id VARCHAR(64) PRIMARY KEY,
                state VARCHAR(100) NOT NULL,
                district VARCHAR(100) NOT NULL,
                admin_boundary_id UUID REFERENCES admin_boundaries(id) ON DELETE SET NULL,
                geographical_area_sqkm FLOAT NOT NULL,
                very_dense_forest_sqkm FLOAT NOT NULL DEFAULT 0.0,
                moderately_dense_forest_sqkm FLOAT NOT NULL DEFAULT 0.0,
                open_forest_sqkm FLOAT NOT NULL DEFAULT 0.0,
                total_forest_sqkm FLOAT NOT NULL DEFAULT 0.0,
                percent_of_geo_area FLOAT NOT NULL DEFAULT 0.0,
                scrub_sqkm FLOAT NOT NULL DEFAULT 0.0,
                reference_year INTEGER DEFAULT 2021,
                source_id VARCHAR(64) REFERENCES fsi_sources(id) ON DELETE CASCADE,
                source_document VARCHAR(255) NOT NULL,
                page_table_reference VARCHAR(150),
                provisional_flag BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT uq_isfr_state_district_year UNIQUE (state, district, reference_year)
            );
            CREATE INDEX IF NOT EXISTS idx_fsi_isfr_state_district ON fsi_isfr_district_forest_stats(state, district);
            CREATE INDEX IF NOT EXISTS idx_fsi_isfr_admin_boundary ON fsi_isfr_district_forest_stats(admin_boundary_id);
        """))

        # 3. Protected Areas Spatial Registry
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS protected_areas (
                id VARCHAR(64) PRIMARY KEY,
                pa_name VARCHAR(255) NOT NULL,
                pa_type VARCHAR(50) NOT NULL, -- NATIONAL_PARK, WILDLIFE_SANCTUARY, TIGER_RESERVE, BIOSPHERE_RESERVE, CONSERVATION_RESERVE
                state VARCHAR(100) NOT NULL,
                district VARCHAR(100),
                established_year INTEGER,
                area_sqkm FLOAT,
                geom GEOMETRY(MultiPolygon, 4326) NOT NULL,
                legal_status VARCHAR(100),
                source_id VARCHAR(64) REFERENCES fsi_sources(id) ON DELETE CASCADE,
                source_record_id VARCHAR(100),
                reference_date VARCHAR(50),
                metadata_info JSONB DEFAULT '{}'::jsonb,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_protected_areas_geom ON protected_areas USING GIST (geom);
            CREATE INDEX IF NOT EXISTS idx_protected_areas_type ON protected_areas(pa_type);
            CREATE INDEX IF NOT EXISTS idx_protected_areas_state ON protected_areas(state);
        """))

        # 4. Observation Forest & Protected Area Context
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS observation_forest_context (
                id VARCHAR(64) PRIMARY KEY,
                detection_id VARCHAR(36) UNIQUE NOT NULL REFERENCES thermal_detections(id) ON DELETE CASCADE,
                is_inside_forest BOOLEAN DEFAULT FALSE,
                forest_density_class VARCHAR(50) DEFAULT 'NON_FOREST', -- VDF, MDF, OF, SCRUB, NON_FOREST
                is_inside_recorded_forest BOOLEAN DEFAULT FALSE,
                is_inside_protected_area BOOLEAN DEFAULT FALSE,
                protected_area_id VARCHAR(64) REFERENCES protected_areas(id) ON DELETE SET NULL,
                protected_area_type VARCHAR(50),
                protected_area_name VARCHAR(255),
                distance_to_protected_area_m FLOAT,
                distance_to_forest_m FLOAT,
                forest_context_level VARCHAR(20) DEFAULT 'NONE', -- HIGH, MEDIUM, LOW, NONE
                forest_fire_evidence VARCHAR(100) DEFAULT 'NO_DIRECT_FIRE_EVIDENCE',
                source_id VARCHAR(64) REFERENCES fsi_sources(id) ON DELETE SET NULL,
                reference_year INTEGER DEFAULT 2021,
                confidence_score FLOAT DEFAULT 0.90,
                spatial_match_method VARCHAR(50) NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_obs_forest_detection_id ON observation_forest_context(detection_id);
            CREATE INDEX IF NOT EXISTS idx_obs_forest_pa_id ON observation_forest_context(protected_area_id);
            CREATE INDEX IF NOT EXISTS idx_obs_forest_context_level ON observation_forest_context(forest_context_level);
        """))

        # 5. Facility Forest Context
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS facility_forest_context (
                id VARCHAR(64) PRIMARY KEY,
                facility_id VARCHAR(36) UNIQUE NOT NULL REFERENCES industrial_facilities(id) ON DELETE CASCADE,
                nearest_protected_area_id VARCHAR(64) REFERENCES protected_areas(id) ON DELETE SET NULL,
                nearest_protected_area_name VARCHAR(255),
                nearest_protected_area_type VARCHAR(50),
                distance_to_protected_area_m FLOAT,
                distance_to_forest_m FLOAT,
                is_inside_esz_10km BOOLEAN DEFAULT FALSE,
                esz_evaluation_status VARCHAR(50) DEFAULT 'DISTANCE_WITHIN_10KM',
                forest_context_level VARCHAR(20) DEFAULT 'NONE',
                source_id VARCHAR(64) REFERENCES fsi_sources(id) ON DELETE SET NULL,
                reference_year INTEGER DEFAULT 2021,
                confidence_score FLOAT DEFAULT 0.95,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_fac_forest_facility_id ON facility_forest_context(facility_id);
            CREATE INDEX IF NOT EXISTS idx_fac_forest_nearest_pa ON facility_forest_context(nearest_protected_area_id);
        """))

        logger.info("Successfully created all Forest Intelligence and Protected Area PostGIS tables.")


if __name__ == "__main__":
    create_fsi_tables()
