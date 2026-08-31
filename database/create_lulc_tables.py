"""
AGNI-NETRA — Phase 3B: Canonical PostGIS LULC Database Schema Creation
Creates:
- lulc_sources
- lulc_classes
- lulc_spatial_features (with GiST index on geom)
- observation_lulc_context (1:1 with thermal_detections.id)
- facility_lulc_context (1:1 with industrial_facilities.id)
"""

import os
import sys
import logging

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from sqlalchemy import text
from backend.app.core.database import engine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("LULCSchema")


def create_lulc_tables():
    logger.info("Initializing Canonical LULC PostGIS Schema for AGNI-NETRA...")
    
    with engine.begin() as conn:
        # Enable PostGIS if not enabled
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))

        # 1. lulc_sources
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS lulc_sources (
                id VARCHAR(64) PRIMARY KEY,
                source_name VARCHAR(100) UNIQUE NOT NULL,
                organization VARCHAR(255) NOT NULL,
                dataset_name VARCHAR(255) NOT NULL,
                resolution_m FLOAT NOT NULL,
                reference_year INTEGER NOT NULL,
                product_version VARCHAR(50) NOT NULL,
                access_type VARCHAR(50) NOT NULL,
                license VARCHAR(150) NOT NULL,
                source_url VARCHAR(500) NOT NULL,
                metadata_info JSONB DEFAULT '{}'::jsonb,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """))
        logger.info("Created table lulc_sources.")

        # 2. lulc_classes
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS lulc_classes (
                id VARCHAR(64) PRIMARY KEY,
                source_id VARCHAR(64) REFERENCES lulc_sources(id) ON DELETE CASCADE,
                source_class_code VARCHAR(50) NOT NULL,
                source_class_name VARCHAR(150) NOT NULL,
                canonical_class VARCHAR(50) NOT NULL,
                is_industrial_compatible BOOLEAN DEFAULT FALSE,
                risk_weight FLOAT DEFAULT 0.5,
                description TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT uq_source_class UNIQUE (source_id, source_class_code)
            );
        """))
        logger.info("Created table lulc_classes.")

        # 3. lulc_spatial_features
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS lulc_spatial_features (
                id VARCHAR(64) PRIMARY KEY,
                source_id VARCHAR(64) REFERENCES lulc_sources(id) ON DELETE CASCADE,
                class_id VARCHAR(64) REFERENCES lulc_classes(id) ON DELETE CASCADE,
                canonical_class VARCHAR(50) NOT NULL,
                feature_name VARCHAR(255),
                state VARCHAR(100),
                district VARCHAR(100),
                geom GEOMETRY(MultiPolygon, 4326) NOT NULL,
                area_sqkm FLOAT,
                source_provenance JSONB DEFAULT '{}'::jsonb,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_lulc_spatial_features_geom ON lulc_spatial_features USING GIST (geom);
            CREATE INDEX IF NOT EXISTS idx_lulc_spatial_features_class ON lulc_spatial_features(canonical_class);
            CREATE INDEX IF NOT EXISTS idx_lulc_spatial_features_state ON lulc_spatial_features(state);
            CREATE INDEX IF NOT EXISTS idx_lulc_spatial_features_district ON lulc_spatial_features(district);
        """))
        logger.info("Created table lulc_spatial_features with GiST index.")

        # 4. observation_lulc_context (1:1 with thermal_detections)
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS observation_lulc_context (
                id VARCHAR(64) PRIMARY KEY,
                detection_id VARCHAR(36) UNIQUE NOT NULL REFERENCES thermal_detections(id) ON DELETE CASCADE,
                primary_lulc_class VARCHAR(50) NOT NULL,
                source_lulc_class VARCHAR(150) NOT NULL,
                is_industrial_zone BOOLEAN DEFAULT FALSE,
                is_mining_zone BOOLEAN DEFAULT FALSE,
                is_forest_zone BOOLEAN DEFAULT FALSE,
                is_agriculture_zone BOOLEAN DEFAULT FALSE,
                is_water_zone BOOLEAN DEFAULT FALSE,
                distance_to_forest_m FLOAT,
                distance_to_agriculture_m FLOAT,
                distance_to_water_m FLOAT,
                distance_to_industrial_m FLOAT,
                distance_to_mining_m FLOAT,
                spatial_match_method VARCHAR(50) NOT NULL,
                source_id VARCHAR(64) REFERENCES lulc_sources(id),
                confidence_score FLOAT DEFAULT 0.90,
                reference_date VARCHAR(50),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_obs_lulc_detection_id ON observation_lulc_context(detection_id);
            CREATE INDEX IF NOT EXISTS idx_obs_lulc_primary_class ON observation_lulc_context(primary_lulc_class);
            CREATE INDEX IF NOT EXISTS idx_obs_lulc_is_ind ON observation_lulc_context(is_industrial_zone);
            CREATE INDEX IF NOT EXISTS idx_obs_lulc_is_forest ON observation_lulc_context(is_forest_zone);
        """))
        logger.info("Created table observation_lulc_context.")

        # 5. facility_lulc_context (1:1 with industrial_facilities)
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS facility_lulc_context (
                id VARCHAR(64) PRIMARY KEY,
                facility_id VARCHAR(36) UNIQUE NOT NULL REFERENCES industrial_facilities(id) ON DELETE CASCADE,
                primary_lulc_class VARCHAR(50) NOT NULL,
                source_lulc_class VARCHAR(150) NOT NULL,
                industrial_compatibility VARCHAR(50) DEFAULT 'COMPATIBLE',
                distance_to_forest_m FLOAT,
                distance_to_agriculture_m FLOAT,
                distance_to_water_m FLOAT,
                distance_to_mining_m FLOAT,
                source_id VARCHAR(64) REFERENCES lulc_sources(id),
                confidence_score FLOAT DEFAULT 0.95,
                reference_date VARCHAR(50),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_fac_lulc_facility_id ON facility_lulc_context(facility_id);
            CREATE INDEX IF NOT EXISTS idx_fac_lulc_primary_class ON facility_lulc_context(primary_lulc_class);
            CREATE INDEX IF NOT EXISTS idx_fac_lulc_compat ON facility_lulc_context(industrial_compatibility);
        """))
        logger.info("Created table facility_lulc_context.")

    logger.info("All Canonical LULC PostGIS Tables Successfully Created!")


if __name__ == "__main__":
    create_lulc_tables()
