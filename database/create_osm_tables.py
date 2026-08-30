"""
AGNI-NETRA — Database Setup for OSM Staging Layer & Canonical Facility Registry
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.database import engine
from sqlalchemy import text


def setup_facility_tables():
    print("[AGNI-NETRA] Initializing OSM Staging & Canonical Facility Database Schema...")
    with engine.connect() as conn:
        # 1. Create PostGIS extension if not exists
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))

        # 2. Create osm_staging_facilities table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS osm_staging_facilities (
                id VARCHAR(64) PRIMARY KEY,
                osm_type TEXT NOT NULL,
                osm_id BIGINT NOT NULL,
                name TEXT,
                operator TEXT,
                entity_classification TEXT NOT NULL,
                industrial_tag TEXT,
                landuse_tag TEXT,
                man_made_tag TEXT,
                power_tag TEXT,
                amenity_tag TEXT,
                plant_source TEXT,
                plant_output TEXT,
                plant_method TEXT,
                product TEXT,
                resource TEXT,
                nic_code TEXT,
                master_sector TEXT,
                sub_sector TEXT,
                industry_type TEXT,
                state TEXT,
                district TEXT,
                city TEXT,
                industrial_area TEXT,
                latitude DOUBLE PRECISION NOT NULL,
                longitude DOUBLE PRECISION NOT NULL,
                geom geometry(Geometry, 4326),
                geom_point geometry(Point, 4326) NOT NULL,
                confidence TEXT NOT NULL,
                verification_status TEXT NOT NULL,
                source TEXT DEFAULT 'OSM',
                source_record_id TEXT NOT NULL,
                source_file TEXT NOT NULL,
                source_metadata JSONB NOT NULL,
                created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'UTC')
            );
        """))

        # 3. Create spatial and lookup indexes on osm_staging_facilities
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_osm_staging_osm_ident ON osm_staging_facilities (osm_type, osm_id);
            CREATE INDEX IF NOT EXISTS idx_osm_staging_classification ON osm_staging_facilities (entity_classification);
            CREATE INDEX IF NOT EXISTS idx_osm_staging_state ON osm_staging_facilities (state);
            CREATE INDEX IF NOT EXISTS idx_osm_staging_district ON osm_staging_facilities (district);
            CREATE INDEX IF NOT EXISTS idx_osm_staging_nic ON osm_staging_facilities (nic_code);
            CREATE INDEX IF NOT EXISTS idx_osm_staging_geom ON osm_staging_facilities USING GIST (geom);
            CREATE INDEX IF NOT EXISTS idx_osm_staging_geom_point ON osm_staging_facilities USING GIST (geom_point);
        """))

        # 4. Enhance industrial_facilities table with all canonical fields
        canonical_columns = [
            ("industry_id", "TEXT"),
            ("industry_name", "TEXT"),
            ("nic_code", "TEXT"),
            ("master_sector", "TEXT"),
            ("sub_sector", "TEXT"),
            ("industry_type", "TEXT"),
            ("company_name", "TEXT"),
            ("facility_name", "TEXT"),
            ("plant_name", "TEXT"),
            ("city", "TEXT"),
            ("industrial_area", "TEXT"),
            ("geom", "geometry(Geometry, 4326)"),
            ("plant_capacity", "TEXT"),
            ("production_type", "TEXT"),
            ("energy_intensity", "TEXT"),
            ("electricity_consumption", "TEXT"),
            ("fuel_consumption", "TEXT"),
            ("water_consumption", "TEXT"),
            ("co2_emissions", "TEXT"),
            ("equipment_type", "TEXT"),
            ("major_machinery", "TEXT"),
            ("operating_status", "TEXT"),
            ("enterprise_size", "TEXT"),
            ("ownership_type", "TEXT"),
            ("data_source", "TEXT DEFAULT 'OSM'"),
            ("source_record_id", "TEXT"),
            ("source_url", "TEXT"),
            ("source_date", "TEXT"),
            ("source_file", "TEXT"),
            ("source_metadata", "JSONB"),
            ("verification_status", "TEXT"),
            ("confidence", "TEXT"),
            ("last_updated", "TIMESTAMP WITHOUT TIME ZONE")
        ]

        for col_name, col_type in canonical_columns:
            conn.execute(text(f"ALTER TABLE industrial_facilities ADD COLUMN IF NOT EXISTS {col_name} {col_type};"))

        # Spatial index on industrial_facilities geometry
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_fac_geom ON industrial_facilities USING GIST (geom);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_fac_nic ON industrial_facilities (nic_code);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_fac_sector ON industrial_facilities (master_sector);"))

        conn.commit()
        print("[AGNI-NETRA] Schema initialized successfully.")


if __name__ == "__main__":
    setup_facility_tables()
