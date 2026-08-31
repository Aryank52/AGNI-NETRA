"""
AGNI-NETRA — Database Schema for IBM Mining Lease Context
Creates PostgreSQL staging and canonical context tables for IBM Mining Lease Bulletin.
"""

import sys
import os
from sqlalchemy import text

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend.app.core.database import engine


def create_ibm_tables():
    print("[AGNI-NETRA] Creating IBM Mining Lease Context Tables...", flush=True)
    with engine.begin() as conn:
        # 1. Create ibm_mining_lease_context_staging table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS ibm_mining_lease_context_staging (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                record_id VARCHAR(128) UNIQUE NOT NULL,
                state VARCHAR(100),
                district VARCHAR(100),
                mineral VARCHAR(100),
                lease_count INTEGER,
                lease_area_ha DOUBLE PRECISION,
                sector VARCHAR(50),
                potential_category VARCHAR(50),
                reference_year INTEGER NOT NULL DEFAULT 2024,
                reference_date DATE NOT NULL DEFAULT '2024-03-31',
                source_document VARCHAR(255) NOT NULL,
                page_number INTEGER,
                table_number VARCHAR(50) NOT NULL,
                provisional_flag BOOLEAN NOT NULL DEFAULT TRUE,
                raw_metadata JSONB DEFAULT '{}'::jsonb,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() AT TIME ZONE 'UTC')
            );
        """))

        # 2. Create canonical ibm_mining_lease_context table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS ibm_mining_lease_context (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                record_id VARCHAR(128) UNIQUE NOT NULL,
                state VARCHAR(100),
                district VARCHAR(100),
                mineral VARCHAR(100),
                lease_count INTEGER,
                lease_area_ha DOUBLE PRECISION,
                sector VARCHAR(50),
                potential_category VARCHAR(50),
                reference_year INTEGER NOT NULL DEFAULT 2024,
                reference_date DATE NOT NULL DEFAULT '2024-03-31',
                source_document VARCHAR(255) NOT NULL,
                table_number VARCHAR(50) NOT NULL,
                page_number INTEGER,
                provisional_flag BOOLEAN NOT NULL DEFAULT TRUE,
                source VARCHAR(50) NOT NULL DEFAULT 'IBM',
                aggregation_level VARCHAR(50) NOT NULL DEFAULT 'DISTRICT_MINERAL',
                raw_metadata JSONB DEFAULT '{}'::jsonb,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() AT TIME ZONE 'UTC'),
                last_updated TIMESTAMP WITH TIME ZONE DEFAULT (NOW() AT TIME ZONE 'UTC')
            );
        """))

        # 3. Create B-Tree Indexes on State, District, Mineral, and Potential Category
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_ibm_staging_state ON ibm_mining_lease_context_staging (state);
            CREATE INDEX IF NOT EXISTS idx_ibm_staging_district ON ibm_mining_lease_context_staging (district);
            CREATE INDEX IF NOT EXISTS idx_ibm_staging_mineral ON ibm_mining_lease_context_staging (mineral);
            CREATE INDEX IF NOT EXISTS idx_ibm_staging_table_num ON ibm_mining_lease_context_staging (table_number);

            CREATE INDEX IF NOT EXISTS idx_ibm_context_state ON ibm_mining_lease_context (state);
            CREATE INDEX IF NOT EXISTS idx_ibm_context_district ON ibm_mining_lease_context (district);
            CREATE INDEX IF NOT EXISTS idx_ibm_context_mineral ON ibm_mining_lease_context (mineral);
            CREATE INDEX IF NOT EXISTS idx_ibm_context_potential ON ibm_mining_lease_context (potential_category);
            CREATE INDEX IF NOT EXISTS idx_ibm_context_agg_level ON ibm_mining_lease_context (aggregation_level);
        """))

    print("[AGNI-NETRA] IBM Mining Lease Context schema created successfully.", flush=True)


if __name__ == "__main__":
    create_ibm_tables()
