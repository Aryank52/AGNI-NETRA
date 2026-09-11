import sys
import os
sys.path.insert(0, os.path.abspath("."))
import psycopg2
from backend.app.core.config import settings

def run_migration():
    print("Connecting to database on 127.0.0.1:5432/agni_netra...")
    conn = psycopg2.connect(
        host="127.0.0.1",
        port=settings.POSTGRES_PORT or 5432,
        dbname=settings.POSTGRES_DB or "agni_netra",
        user=settings.POSTGRES_USER or "postgres",
        password=settings.POSTGRES_PASSWORD or "postgres"
    )
    conn.autocommit = True
    cur = conn.cursor()

    columns_to_add = [
        ("thermal_sources", "JSON DEFAULT '[]'::json"),
        ("observation_provenance", "JSON DEFAULT '[]'::json"),
        ("source_agreement", "VARCHAR(50) DEFAULT 'SINGLE_SOURCE'"),
        ("source_conflicts", "JSON DEFAULT '[]'::json"),
        ("thermal_coverage", "JSON DEFAULT '{}'::json"),
        ("observation_count", "INTEGER DEFAULT 0")
    ]

    for col, col_type in columns_to_add:
        try:
            sql = f"ALTER TABLE investigation_workspaces ADD COLUMN IF NOT EXISTS {col} {col_type};"
            cur.execute(sql)
            print(f"Added column {col} to investigation_workspaces: SUCCESS")
        except Exception as e:
            print(f"Column {col} exception: {e}")

    # Verify column existence
    cur.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'investigation_workspaces' 
        AND column_name IN ('thermal_sources', 'observation_provenance', 'source_agreement', 'source_conflicts', 'thermal_coverage', 'observation_count');
    """)
    rows = cur.fetchall()
    print("Verified investigation_workspaces Phase 7 columns in DB:", rows)
    cur.close()
    conn.close()
    print("Migration finished successfully.")

if __name__ == "__main__":
    run_migration()
