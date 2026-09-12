"""
Migration script for Phase 11: Global Evidence Graph & Explainable Intelligence
Adds Phase 11 evidence graph columns to investigation_workspaces table in PostgreSQL and SQLite if not already present.
"""

from sqlalchemy import text
from backend.app.core.database import engine, IS_SQLITE_TEST

def migrate():
    columns_to_add = [
        ("evidence_graph", "JSON DEFAULT '{}'::json", "JSON DEFAULT '{}'"),
        ("evidence_nodes", "JSON DEFAULT '[]'::json", "JSON DEFAULT '[]'"),
        ("evidence_edges", "JSON DEFAULT '[]'::json", "JSON DEFAULT '[]'"),
        ("hypotheses", "JSON DEFAULT '[]'::json", "JSON DEFAULT '[]'"),
        ("hypothesis_support", "JSON DEFAULT '{}'::json", "JSON DEFAULT '{}'"),
        ("hypothesis_conflicts", "JSON DEFAULT '[]'::json", "JSON DEFAULT '[]'"),
        ("evidence_lineage", "JSON DEFAULT '{}'::json", "JSON DEFAULT '{}'"),
        ("evidence_uncertainty", "JSON DEFAULT '{}'::json", "JSON DEFAULT '{}'"),
        ("assessment_lineage", "JSON DEFAULT '{}'::json", "JSON DEFAULT '{}'"),
        ("data_gaps", "JSON DEFAULT '[]'::json", "JSON DEFAULT '[]'"),
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
    print("Phase 11 migration complete.")

if __name__ == "__main__":
    migrate()
