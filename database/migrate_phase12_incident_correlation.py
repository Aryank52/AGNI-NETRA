"""
Migration script for Phase 12: Multi-Event Global Incident Correlation
Adds Phase 12 multi-event correlation columns to investigation_workspaces table in PostgreSQL and SQLite if not already present.
"""

from sqlalchemy import text
from backend.app.core.database import engine, IS_SQLITE_TEST

def migrate():
    columns_to_add = [
        ("related_event_ids", "JSON DEFAULT '[]'::json", "JSON DEFAULT '[]'"),
        ("event_relationships", "JSON DEFAULT '[]'::json", "JSON DEFAULT '[]'"),
        ("event_clusters", "JSON DEFAULT '[]'::json", "JSON DEFAULT '[]'"),
        ("incident_hypotheses", "JSON DEFAULT '[]'::json", "JSON DEFAULT '[]'"),
        ("incident_assessment", "JSON DEFAULT '{}'::json", "JSON DEFAULT '{}'"),
        ("incident_geometry", "JSON DEFAULT '{}'::json", "JSON DEFAULT '{}'"),
        ("incident_evidence", "JSON DEFAULT '{}'::json", "JSON DEFAULT '{}'"),
        ("incident_uncertainty", "JSON DEFAULT '{}'::json", "JSON DEFAULT '{}'"),
        ("incident_data_gaps", "JSON DEFAULT '[]'::json", "JSON DEFAULT '[]'"),
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
    print("Phase 12 migration complete.")

if __name__ == "__main__":
    migrate()
