"""
AGNI-NETRA — Database Schema for IBM Table 15 Auctioned Mineral Blocks
Creates staging and canonical tables for Successful Auctions 2024-25 (Table 15).
"""

import sys
import os
from sqlalchemy import text

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend.app.core.database import engine


def create_ibm_auction_tables():
    print("[AGNI-NETRA] Creating IBM Auctioned Mineral Blocks Tables & Indexes...", flush=True)
    with engine.begin() as conn:
        # 1. Staging Table: ibm_auctioned_blocks_staging
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS ibm_auctioned_blocks_staging (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                sl_no INTEGER NOT NULL,
                state VARCHAR(100),
                block_name VARCHAR(255) NOT NULL,
                mineral VARCHAR(255),
                preferred_bidder VARCHAR(255),
                auction_financial_year VARCHAR(50) DEFAULT '2024-25',
                source_document VARCHAR(255) NOT NULL,
                page_number INTEGER,
                table_number VARCHAR(50) DEFAULT 'Table 15',
                provisional_status BOOLEAN DEFAULT TRUE,
                raw_metadata JSONB DEFAULT '{}'::jsonb,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() AT TIME ZONE 'UTC')
            );
        """))

        # 2. Canonical Table: ibm_auctioned_blocks
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS ibm_auctioned_blocks (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                source_doc_id VARCHAR(100) UNIQUE NOT NULL,
                sl_no INTEGER NOT NULL,
                block_name VARCHAR(255) NOT NULL,
                state VARCHAR(100) NOT NULL,
                district VARCHAR(100),
                mineral VARCHAR(255) NOT NULL,
                preferred_bidder VARCHAR(255),
                auction_financial_year VARCHAR(50) NOT NULL DEFAULT '2024-25',
                
                -- Entity Resolution & Geometry Provenance
                matched_facility_id VARCHAR(36) REFERENCES industrial_facilities(id) ON DELETE SET NULL,
                match_confidence VARCHAR(20) NOT NULL DEFAULT 'UNMATCHED', -- HIGH, MEDIUM, LOW, UNMATCHED
                match_score DOUBLE PRECISION,
                match_method VARCHAR(100),
                geom geometry(Geometry, 4326),
                
                -- FIRMS Thermal Associations (for spatial matches)
                firms_count_500m INTEGER DEFAULT 0,
                firms_count_1km INTEGER DEFAULT 0,
                firms_count_2km INTEGER DEFAULT 0,
                
                -- Metadata
                source VARCHAR(50) NOT NULL DEFAULT 'IBM',
                source_document VARCHAR(255) NOT NULL,
                page_number INTEGER,
                table_number VARCHAR(50) NOT NULL DEFAULT 'Table 15',
                is_provisional BOOLEAN NOT NULL DEFAULT TRUE,
                raw_metadata JSONB DEFAULT '{}'::jsonb,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() AT TIME ZONE 'UTC'),
                last_updated TIMESTAMP WITH TIME ZONE DEFAULT (NOW() AT TIME ZONE 'UTC')
            );
        """))

        # 3. Indexes
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_ibm_auc_state ON ibm_auctioned_blocks (state);
            CREATE INDEX IF NOT EXISTS idx_ibm_auc_mineral ON ibm_auctioned_blocks (mineral);
            CREATE INDEX IF NOT EXISTS idx_ibm_auc_conf ON ibm_auctioned_blocks (match_confidence);
            CREATE INDEX IF NOT EXISTS idx_ibm_auc_matched_fac ON ibm_auctioned_blocks (matched_facility_id);
            CREATE INDEX IF NOT EXISTS idx_ibm_auc_geom ON ibm_auctioned_blocks USING gist (geom);
        """))

    print("[AGNI-NETRA] IBM Auctioned Mineral Blocks tables created successfully.", flush=True)


if __name__ == "__main__":
    create_ibm_auction_tables()
