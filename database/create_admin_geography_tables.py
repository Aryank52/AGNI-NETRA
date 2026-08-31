"""
AGNI-NETRA — Database Schema for National Administrative Geography Layer (Phase 2A)
Creates canonical admin_boundaries reference table and spatial administrative association tables.
"""

import sys
import os
from sqlalchemy import text

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend.app.core.database import engine


def create_admin_geography_tables():
    print("[AGNI-NETRA] Creating National Administrative Geography Tables & Indexes...", flush=True)
    with engine.begin() as conn:
        # 1. Canonical Administrative Boundaries Reference Table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS admin_boundaries (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                admin_level INTEGER NOT NULL, -- 1: State/UT, 2: District, 3: Sub-District/Tehsil
                admin_level_name VARCHAR(50) NOT NULL, -- STATE_UT, DISTRICT, SUBDISTRICT
                admin_code VARCHAR(100) NOT NULL,
                name VARCHAR(255) NOT NULL,
                normalized_name VARCHAR(255) NOT NULL,
                parent_code VARCHAR(100),
                parent_name VARCHAR(255),
                state_code VARCHAR(100),
                state_name VARCHAR(255),
                district_code VARCHAR(100),
                district_name VARCHAR(255),
                subdistrict_code VARCHAR(100),
                geom geometry(Geometry, 4326) NOT NULL,
                
                -- Provenance & Metadata
                source VARCHAR(100) NOT NULL DEFAULT 'geoBoundaries / Local Government Directory (lgdirectory.gov.in) / DataMeet',
                source_document VARCHAR(255) NOT NULL,
                source_url TEXT,
                reference_date TIMESTAMP WITH TIME ZONE DEFAULT (NOW() AT TIME ZONE 'UTC'),
                source_version VARCHAR(50) DEFAULT '2024',
                crs VARCHAR(50) DEFAULT 'EPSG:4326',
                srid INTEGER DEFAULT 4326,
                is_authoritative BOOLEAN DEFAULT TRUE,
                is_active BOOLEAN DEFAULT TRUE,
                raw_metadata JSONB DEFAULT '{}'::jsonb,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() AT TIME ZONE 'UTC')
            );
        """))

        # Indexes for admin_boundaries
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_admin_bound_geom ON admin_boundaries USING gist (geom);
            CREATE INDEX IF NOT EXISTS idx_admin_bound_level ON admin_boundaries (admin_level);
            CREATE INDEX IF NOT EXISTS idx_admin_bound_code ON admin_boundaries (admin_code);
            CREATE INDEX IF NOT EXISTS idx_admin_bound_state_name ON admin_boundaries (state_name);
            CREATE INDEX IF NOT EXISTS idx_admin_bound_dist_name ON admin_boundaries (district_name);
            CREATE INDEX IF NOT EXISTS idx_admin_bound_norm_name ON admin_boundaries (normalized_name);
        """))

        # 2. Facility Administrative Association Table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS facility_administrative_context (
                facility_id VARCHAR(36) PRIMARY KEY REFERENCES industrial_facilities(id) ON DELETE CASCADE,
                original_state VARCHAR(255),
                original_district VARCHAR(255),
                original_city VARCHAR(255),
                derived_state VARCHAR(255),
                derived_district VARCHAR(255),
                derived_subdistrict VARCHAR(255),
                state_id UUID REFERENCES admin_boundaries(id) ON DELETE SET NULL,
                district_id UUID REFERENCES admin_boundaries(id) ON DELETE SET NULL,
                subdistrict_id UUID REFERENCES admin_boundaries(id) ON DELETE SET NULL,
                has_state_conflict BOOLEAN DEFAULT FALSE,
                has_district_conflict BOOLEAN DEFAULT FALSE,
                spatial_match_method VARCHAR(100) DEFAULT 'POSTGIS_SPATIAL_JOIN',
                administrative_source VARCHAR(100) DEFAULT 'geoBoundaries / Local Government Directory',
                administrative_confidence VARCHAR(20) DEFAULT 'HIGH',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() AT TIME ZONE 'UTC'),
                last_updated TIMESTAMP WITH TIME ZONE DEFAULT (NOW() AT TIME ZONE 'UTC')
            );
        """))

        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_fac_admin_state_id ON facility_administrative_context (state_id);
            CREATE INDEX IF NOT EXISTS idx_fac_admin_dist_id ON facility_administrative_context (district_id);
            CREATE INDEX IF NOT EXISTS idx_fac_admin_subdist_id ON facility_administrative_context (subdistrict_id);
            CREATE INDEX IF NOT EXISTS idx_fac_admin_conflict ON facility_administrative_context (has_state_conflict, has_district_conflict);
        """))

        # 3. Observation Administrative Association Table (for 1.77M+ FIRMS observations)
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS observation_administrative_context (
                detection_id VARCHAR(50) PRIMARY KEY,
                state_id UUID REFERENCES admin_boundaries(id) ON DELETE SET NULL,
                state_name VARCHAR(255),
                district_id UUID REFERENCES admin_boundaries(id) ON DELETE SET NULL,
                district_name VARCHAR(255),
                subdistrict_id UUID REFERENCES admin_boundaries(id) ON DELETE SET NULL,
                subdistrict_name VARCHAR(255),
                spatial_match_method VARCHAR(100) DEFAULT 'POSTGIS_SPATIAL_JOIN',
                boundary_source VARCHAR(100) DEFAULT 'geoBoundaries / Local Government Directory',
                administrative_confidence VARCHAR(20) DEFAULT 'HIGH',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() AT TIME ZONE 'UTC')
            );
        """))

        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_obs_admin_state_id ON observation_administrative_context (state_id);
            CREATE INDEX IF NOT EXISTS idx_obs_admin_dist_id ON observation_administrative_context (district_id);
            CREATE INDEX IF NOT EXISTS idx_obs_admin_subdist_id ON observation_administrative_context (subdistrict_id);
            CREATE INDEX IF NOT EXISTS idx_obs_admin_state_name ON observation_administrative_context (state_name);
            CREATE INDEX IF NOT EXISTS idx_obs_admin_dist_name ON observation_administrative_context (district_name);
        """))

        # 4. PARIVESH Administrative Association Table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS parivesh_administrative_context (
                proposal_id VARCHAR(100) PRIMARY KEY,
                original_state VARCHAR(255),
                original_district VARCHAR(255),
                derived_state VARCHAR(255),
                derived_district VARCHAR(255),
                derived_subdistrict VARCHAR(255),
                state_id UUID REFERENCES admin_boundaries(id) ON DELETE SET NULL,
                district_id UUID REFERENCES admin_boundaries(id) ON DELETE SET NULL,
                subdistrict_id UUID REFERENCES admin_boundaries(id) ON DELETE SET NULL,
                has_state_conflict BOOLEAN DEFAULT FALSE,
                has_district_conflict BOOLEAN DEFAULT FALSE,
                administrative_method VARCHAR(100) DEFAULT 'POSTGIS_SPATIAL_JOIN',
                administrative_confidence VARCHAR(20) DEFAULT 'HIGH',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() AT TIME ZONE 'UTC')
            );
        """))

    print("[AGNI-NETRA] National Administrative Geography tables created successfully.", flush=True)


if __name__ == "__main__":
    create_admin_geography_tables()
