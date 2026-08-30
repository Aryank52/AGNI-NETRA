"""
AGNI-NETRA — Database Setup for CEA Power Stations Staging Layer & Enrichment
Creates table `cea_power_stations_staging` and adds indexes for fast entity resolution.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.database import engine
from sqlalchemy import text


def setup_cea_tables():
    print("[AGNI-NETRA] Initializing CEA Power Stations Database Schema...")
    with engine.begin() as conn:
        # 1. Create cea_power_stations_staging table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS cea_power_stations_staging (
                id VARCHAR(64) PRIMARY KEY,
                cea_record_id TEXT UNIQUE NOT NULL,
                source_document TEXT NOT NULL,
                source_date TEXT NOT NULL,
                page_number INTEGER NOT NULL,
                s_no TEXT,
                region TEXT,
                state TEXT,
                sector TEXT,
                organisation TEXT,
                project_name TEXT NOT NULL,
                prime_mover TEXT,
                unit_no TEXT,
                installed_capacity_mw DOUBLE PRECISION,
                year_of_commissioning INTEGER,
                raw_row_text TEXT,
                created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'UTC')
            );
        """))

        # 2. Create indexes for fast lookup and entity resolution
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_cea_staging_project ON cea_power_stations_staging (project_name);
            CREATE INDEX IF NOT EXISTS idx_cea_staging_state ON cea_power_stations_staging (state);
            CREATE INDEX IF NOT EXISTS idx_cea_staging_org ON cea_power_stations_staging (organisation);
            CREATE INDEX IF NOT EXISTS idx_cea_staging_prime_mover ON cea_power_stations_staging (prime_mover);
        """))

        # 3. Enhance industrial_facilities with CEA-specific canonical attributes if not present
        cea_columns = [
            ("prime_mover", "TEXT"),
            ("unit_count", "INTEGER"),
            ("commissioning_year_min", "INTEGER"),
            ("commissioning_year_max", "INTEGER"),
            ("cea_project_name", "TEXT"),
            ("cea_organisation", "TEXT"),
            ("firms_detections_500m", "INTEGER DEFAULT 0"),
            ("firms_detections_1km", "INTEGER DEFAULT 0"),
            ("firms_detections_2km", "INTEGER DEFAULT 0"),
            ("thermal_activity_status", "TEXT")
        ]

        for col_name, col_type in cea_columns:
            conn.execute(text(f"ALTER TABLE industrial_facilities ADD COLUMN IF NOT EXISTS {col_name} {col_type};"))

        print("[AGNI-NETRA] CEA Schema & Table extensions initialized successfully.")


if __name__ == "__main__":
    setup_cea_tables()
