"""
Migration script for Phase 13: Global Intelligence Fusion & Decision-Support Synthesis
Adds Phase 13 synthesis columns to investigation_workspaces table in PostgreSQL and SQLite if not already present.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from backend.app.core.database import engine, IS_SQLITE_TEST

def migrate():
    columns_to_add = [
        ("unified_assessment", "JSON DEFAULT '{}'::json", "JSON DEFAULT '{}'"),
        ("assessment_history", "JSON DEFAULT '[]'::json", "JSON DEFAULT '[]'"),
        ("assessment_changes", "JSON DEFAULT '{}'::json", "JSON DEFAULT '{}'"),
        ("decision_support", "JSON DEFAULT '{}'::json", "JSON DEFAULT '{}'"),
        ("recommended_verification", "JSON DEFAULT '[]'::json", "JSON DEFAULT '[]'"),
        ("assessment_provenance", "JSON DEFAULT '{}'::json", "JSON DEFAULT '{}'"),
        ("assessment_evidence_ids", "JSON DEFAULT '[]'::json", "JSON DEFAULT '[]'"),
        ("assessment_uncertainty", "JSON DEFAULT '{}'::json", "JSON DEFAULT '{}'"),
        ("assessment_mode", "VARCHAR(50) DEFAULT 'ANALYST'", "VARCHAR(50) DEFAULT 'ANALYST'"),
    ]

    with engine.connect() as conn:
        for col_name, pg_type, sqlite_type in columns_to_add:
            col_type = sqlite_type if IS_SQLITE_TEST else pg_type
            if IS_SQLITE_TEST:
                sql = f"ALTER TABLE investigation_workspaces ADD COLUMN {col_name} {col_type};"
            else:
                sql = f"ALTER TABLE investigation_workspaces ADD COLUMN IF NOT EXISTS {col_name} {col_type};"
            try:
                conn.execute(text(sql))
                print(f"Executed: {sql}")
            except Exception as e:
                if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                    print(f"Column {col_name} already exists.")
                else:
                    print(f"Notice on {col_name}: {e}")
        conn.commit()
    print("Phase 13 migration complete.")

if __name__ == "__main__":
    migrate()
