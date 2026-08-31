"""
AGNI-NETRA — Database Setup for PARIVESH Environmental Clearance Staging Layer & Enrichment
Creates table `parivesh_projects_staging` and enhances `industrial_facilities` with clearance evidence fields.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.database import engine
from sqlalchemy import text


def setup_parivesh_tables():
    print("[AGNI-NETRA] Initializing PARIVESH Environmental Clearance Database Schema...")
    with engine.begin() as conn:
        # 1. Create parivesh_projects_staging table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS parivesh_projects_staging (
                id VARCHAR(64) PRIMARY KEY,
                proposal_id TEXT UNIQUE NOT NULL,
                project_name TEXT NOT NULL,
                project_type TEXT,
                proponent TEXT,
                state TEXT,
                district TEXT,
                category TEXT,
                sector TEXT,
                clearance_type TEXT,
                clearance_status TEXT,
                proposal_date TEXT,
                decision_date TEXT,
                forest_related_flag BOOLEAN DEFAULT FALSE,
                wildlife_related_flag BOOLEAN DEFAULT FALSE,
                crz_related_flag BOOLEAN DEFAULT FALSE,
                latitude DOUBLE PRECISION,
                longitude DOUBLE PRECISION,
                geom geometry(Point, 4326),
                source_url TEXT,
                source_file TEXT,
                source_date TEXT,
                raw_metadata JSONB,
                match_status TEXT DEFAULT 'UNMATCHED',
                matched_facility_id VARCHAR(36),
                match_confidence TEXT,
                match_score DOUBLE PRECISION,
                match_reasons JSONB,
                created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'UTC')
            );
        """))

        # 2. Create indexes for fast lookup and entity resolution
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_parivesh_staging_proposal ON parivesh_projects_staging (proposal_id);
            CREATE INDEX IF NOT EXISTS idx_parivesh_staging_proj_name ON parivesh_projects_staging (project_name);
            CREATE INDEX IF NOT EXISTS idx_parivesh_staging_state ON parivesh_projects_staging (state);
            CREATE INDEX IF NOT EXISTS idx_parivesh_staging_proponent ON parivesh_projects_staging (proponent);
            CREATE INDEX IF NOT EXISTS idx_parivesh_staging_sector ON parivesh_projects_staging (sector);
            CREATE INDEX IF NOT EXISTS idx_parivesh_staging_status ON parivesh_projects_staging (clearance_status);
            CREATE INDEX IF NOT EXISTS idx_parivesh_staging_match ON parivesh_projects_staging (match_status);
            CREATE INDEX IF NOT EXISTS idx_parivesh_staging_geom ON parivesh_projects_staging USING GIST (geom);
        """))

        # 3. Enhance industrial_facilities with PARIVESH environmental clearance fields
        parivesh_columns = [
            ("environmental_clearance_present", "BOOLEAN DEFAULT FALSE"),
            ("ec_proposal_id", "TEXT"),
            ("ec_clearance_type", "TEXT"),
            ("ec_clearance_status", "TEXT"),
            ("ec_category", "TEXT"),
            ("ec_decision_date", "TEXT"),
            ("forest_related_flag", "BOOLEAN DEFAULT FALSE"),
            ("wildlife_related_flag", "BOOLEAN DEFAULT FALSE"),
            ("crz_related_flag", "BOOLEAN DEFAULT FALSE")
        ]

        for col_name, col_type in parivesh_columns:
            conn.execute(text(f"ALTER TABLE industrial_facilities ADD COLUMN IF NOT EXISTS {col_name} {col_type};"))

        print("[AGNI-NETRA] PARIVESH Schema & Table extensions initialized successfully.")


if __name__ == "__main__":
    setup_parivesh_tables()
