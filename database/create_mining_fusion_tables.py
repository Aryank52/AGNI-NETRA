"""
AGNI-NETRA — Database Schema for Mining Intelligence Fusion Layer
Creates tables for facility mining evidence, thermal associations, and PostGIS spatial indexing.
"""

import sys
import os
from sqlalchemy import text

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend.app.core.database import engine


def create_mining_fusion_tables():
    print("[AGNI-NETRA] Creating Mining Intelligence Fusion Tables & Indexes...", flush=True)
    with engine.begin() as conn:
        # 1. Create facility_mining_evidence table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS facility_mining_evidence (
                facility_id VARCHAR(36) PRIMARY KEY REFERENCES industrial_facilities(id) ON DELETE CASCADE,
                facility_name VARCHAR(255) NOT NULL,
                facility_type VARCHAR(50) NOT NULL,
                osm_object_id VARCHAR(100),
                osm_object_type VARCHAR(50),
                operator VARCHAR(255),
                mineral_commodity VARCHAR(255),
                state VARCHAR(100),
                district VARCHAR(100),
                administrative_source VARCHAR(100),
                latitude DOUBLE PRECISION NOT NULL,
                longitude DOUBLE PRECISION NOT NULL,
                
                -- IBM Mining Lease Bulletin Context
                ibm_lease_context_present BOOLEAN NOT NULL DEFAULT FALSE,
                ibm_district_lease_count INTEGER,
                ibm_district_lease_area_ha DOUBLE PRECISION,
                ibm_potential_tier VARCHAR(50),
                ibm_district_minerals JSONB DEFAULT '[]'::jsonb,
                
                -- IBM National Mineral Inventory Context
                nmi_resource_context_present BOOLEAN NOT NULL DEFAULT FALSE,
                nmi_commodity_reserves DOUBLE PRECISION,
                nmi_commodity_resources DOUBLE PRECISION,
                nmi_commodity_unit VARCHAR(100),
                
                -- NASA FIRMS Thermal Telemetry Associations
                firms_associated_500m INTEGER NOT NULL DEFAULT 0,
                firms_associated_1km INTEGER NOT NULL DEFAULT 0,
                firms_associated_2km INTEGER NOT NULL DEFAULT 0,
                first_thermal_seen TIMESTAMP WITHOUT TIME ZONE,
                last_thermal_seen TIMESTAMP WITHOUT TIME ZONE,
                active_days_count INTEGER NOT NULL DEFAULT 0,
                mean_frp DOUBLE PRECISION,
                median_frp DOUBLE PRECISION,
                p90_frp DOUBLE PRECISION,
                p99_frp DOUBLE PRECISION,
                max_frp DOUBLE PRECISION,
                
                -- Evidence & Classification
                mining_context_present BOOLEAN NOT NULL DEFAULT TRUE,
                mining_geometry_present BOOLEAN NOT NULL DEFAULT TRUE,
                thermal_activity_present BOOLEAN NOT NULL DEFAULT FALSE,
                thermal_persistence_category VARCHAR(50) NOT NULL DEFAULT 'NO_THERMAL_ACTIVITY',
                confidence_score DOUBLE PRECISION NOT NULL DEFAULT 0.5,
                scientific_attribution TEXT NOT NULL,
                evidence_summary JSONB DEFAULT '{}'::jsonb,
                
                created_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() AT TIME ZONE 'UTC'),
                last_updated TIMESTAMP WITH TIME ZONE DEFAULT (NOW() AT TIME ZONE 'UTC')
            );
        """))

        # 2. Create mining_thermal_associations table for detailed distance-band metrics
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS mining_thermal_associations (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                facility_id VARCHAR(36) NOT NULL REFERENCES industrial_facilities(id) ON DELETE CASCADE,
                distance_band VARCHAR(20) NOT NULL, -- '500m', '1km', '2km'
                detection_count INTEGER NOT NULL DEFAULT 0,
                first_seen TIMESTAMP WITHOUT TIME ZONE,
                last_seen TIMESTAMP WITHOUT TIME ZONE,
                active_days_count INTEGER NOT NULL DEFAULT 0,
                mean_frp DOUBLE PRECISION,
                median_frp DOUBLE PRECISION,
                p90_frp DOUBLE PRECISION,
                p99_frp DOUBLE PRECISION,
                max_frp DOUBLE PRECISION,
                mean_confidence DOUBLE PRECISION,
                day_detection_count INTEGER NOT NULL DEFAULT 0,
                night_detection_count INTEGER NOT NULL DEFAULT 0,
                recurrence_rate DOUBLE PRECISION,
                persistence_days DOUBLE PRECISION,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() AT TIME ZONE 'UTC')
            );
        """))

        # 3. Create spatial and B-Tree indexes for fast queries
        print("[AGNI-NETRA] Creating indexes on mining evidence and thermal detections...", flush=True)
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_mining_ev_state ON facility_mining_evidence (state);
            CREATE INDEX IF NOT EXISTS idx_mining_ev_district ON facility_mining_evidence (district);
            CREATE INDEX IF NOT EXISTS idx_mining_ev_tier ON facility_mining_evidence (ibm_potential_tier);
            CREATE INDEX IF NOT EXISTS idx_mining_ev_mineral ON facility_mining_evidence (mineral_commodity);
            CREATE INDEX IF NOT EXISTS idx_mining_ev_therm_cat ON facility_mining_evidence (thermal_persistence_category);
            
            CREATE INDEX IF NOT EXISTS idx_mta_fac_id ON mining_thermal_associations (facility_id);
            CREATE INDEX IF NOT EXISTS idx_mta_dist_band ON mining_thermal_associations (distance_band);
            
            -- Spatial indexes on thermal_detections and industrial_facilities
            CREATE INDEX IF NOT EXISTS idx_th_lat_lon ON thermal_detections (latitude, longitude);
            CREATE INDEX IF NOT EXISTS idx_th_acq_date ON thermal_detections (acq_timestamp);
        """))

        # 4. Create PostGIS functional geometry index on thermal_detections if not exists
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_th_geom ON thermal_detections 
            USING gist (ST_SetSRID(ST_MakePoint(longitude, latitude), 4326));
        """))

    print("[AGNI-NETRA] Mining Intelligence Fusion tables and indexes created successfully.", flush=True)


if __name__ == "__main__":
    create_mining_fusion_tables()
