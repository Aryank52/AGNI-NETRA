"""
AGNI-NETRA — Database Schema for IBM National Mineral Inventory 2020
Creates PostgreSQL staging and canonical tables for IBM NMI mineral-resource context.
"""

import sys
import os
from sqlalchemy import text

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend.app.core.database import engine


def create_ibm_nmi_tables():
    print("[AGNI-NETRA] Creating IBM National Mineral Inventory (NMI) Tables...", flush=True)
    with engine.begin() as conn:
        # 1. Create ibm_nmi_staging table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS ibm_nmi_staging (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                record_id VARCHAR(128) UNIQUE NOT NULL,
                sl_no INTEGER,
                commodity VARCHAR(255),
                mineral VARCHAR(255) NOT NULL,
                unit VARCHAR(100),
                reserves DOUBLE PRECISION,
                remaining_resources DOUBLE PRECISION,
                total_resources DOUBLE PRECISION,
                not_estimated BOOLEAN NOT NULL DEFAULT FALSE,
                reference_year INTEGER NOT NULL DEFAULT 2020,
                reference_date DATE NOT NULL DEFAULT '2020-04-01',
                source_document VARCHAR(255) NOT NULL,
                page_number INTEGER,
                table_number VARCHAR(50) NOT NULL DEFAULT 'Table 6',
                provisional_flag BOOLEAN NOT NULL DEFAULT TRUE,
                raw_metadata JSONB DEFAULT '{}'::jsonb,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() AT TIME ZONE 'UTC')
            );
        """))

        # 2. Create canonical ibm_mineral_resources table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS ibm_mineral_resources (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                record_id VARCHAR(128) UNIQUE NOT NULL,
                sl_no INTEGER,
                commodity VARCHAR(255),
                mineral VARCHAR(255) NOT NULL,
                unit VARCHAR(100),
                reserves DOUBLE PRECISION,
                remaining_resources DOUBLE PRECISION,
                total_resources DOUBLE PRECISION,
                not_estimated BOOLEAN NOT NULL DEFAULT FALSE,
                reference_year INTEGER NOT NULL DEFAULT 2020,
                reference_date DATE NOT NULL DEFAULT '2020-04-01',
                source VARCHAR(50) NOT NULL DEFAULT 'IBM',
                source_document VARCHAR(255) NOT NULL,
                page_number INTEGER,
                table_number VARCHAR(50) NOT NULL DEFAULT 'Table 6',
                provisional_flag BOOLEAN NOT NULL DEFAULT TRUE,
                raw_metadata JSONB DEFAULT '{}'::jsonb,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() AT TIME ZONE 'UTC'),
                last_updated TIMESTAMP WITH TIME ZONE DEFAULT (NOW() AT TIME ZONE 'UTC')
            );
        """))

        # 3. Create B-Tree Indexes on Mineral, Commodity, and Record ID
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_ibm_nmi_staging_mineral ON ibm_nmi_staging (mineral);
            CREATE INDEX IF NOT EXISTS idx_ibm_nmi_staging_commodity ON ibm_nmi_staging (commodity);
            CREATE INDEX IF NOT EXISTS idx_ibm_nmi_staging_rec_id ON ibm_nmi_staging (record_id);

            CREATE INDEX IF NOT EXISTS idx_ibm_min_res_mineral ON ibm_mineral_resources (mineral);
            CREATE INDEX IF NOT EXISTS idx_ibm_min_res_commodity ON ibm_mineral_resources (commodity);
            CREATE INDEX IF NOT EXISTS idx_ibm_min_res_rec_id ON ibm_mineral_resources (record_id);
            CREATE INDEX IF NOT EXISTS idx_ibm_min_res_ref_year ON ibm_mineral_resources (reference_year);
        """))

    print("[AGNI-NETRA] IBM National Mineral Inventory schema created successfully.", flush=True)


if __name__ == "__main__":
    create_ibm_nmi_tables()
