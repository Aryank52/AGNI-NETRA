"""
Migration script for Phase 10: Environmental Intelligence & Cross-Modal Verification
Adds Phase 10 columns to investigation_workspaces table in PostgreSQL if not already present.
"""

from sqlalchemy import text
from backend.app.core.database import engine

def migrate():
    columns_to_add = [
        ("environmental_sources", "JSON DEFAULT '[]'::json"),
        ("environmental_provenance", "JSON DEFAULT '[]'::json"),
        ("environmental_observations", "JSON DEFAULT '{}'::json"),
        ("environmental_relationships", "JSON DEFAULT '[]'::json"),
        ("environmental_coverage", "JSON DEFAULT '{}'::json"),
        ("environmental_uncertainty", "JSON DEFAULT '{}'::json"),
        ("environmental_conflicts", "JSON DEFAULT '[]'::json"),
        ("cross_modal_sources", "JSON DEFAULT '[]'::json"),
        ("cross_modal_evidence", "JSON DEFAULT '{}'::json"),
        ("cross_modal_uncertainty", "JSON DEFAULT '{}'::json"),
        ("environmental_observation_count", "INTEGER DEFAULT 0"),
        ("cross_modal_observation_count", "INTEGER DEFAULT 0"),
    ]

    with engine.connect() as conn:
        for col_name, col_type in columns_to_add:
            sql = f"ALTER TABLE investigation_workspaces ADD COLUMN IF NOT EXISTS {col_name} {col_type};"
            conn.execute(text(sql))
            print(f"Executed: {sql}")
        conn.commit()
    print("Phase 10 migration complete.")

if __name__ == "__main__":
    migrate()
