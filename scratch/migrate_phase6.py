import os
import psycopg2

def run_migration():
    db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/agni_netra")
    print(f"Connecting to database...")
    conn = psycopg2.connect(db_url)
    conn.autocommit = True
    cur = conn.cursor()

    statements = [
        # InvestigationWorkspace
        "ALTER TABLE investigation_workspaces ADD COLUMN IF NOT EXISTS sources_used JSON DEFAULT '[]'::json;",
        "ALTER TABLE investigation_workspaces ADD COLUMN IF NOT EXISTS coverage_profile VARCHAR(50) DEFAULT 'INDIA';",
        "ALTER TABLE investigation_workspaces ADD COLUMN IF NOT EXISTS missing_sources JSON DEFAULT '[]'::json;",
        "ALTER TABLE investigation_workspaces ADD COLUMN IF NOT EXISTS partial_sources JSON DEFAULT '[]'::json;",
        "ALTER TABLE investigation_workspaces ADD COLUMN IF NOT EXISTS provenance_records JSON DEFAULT '[]'::json;",
        "ALTER TABLE investigation_workspaces ADD COLUMN IF NOT EXISTS source_availability_matrix JSON DEFAULT '{}'::json;",
        "ALTER TABLE investigation_workspaces ADD COLUMN IF NOT EXISTS country VARCHAR(100) DEFAULT 'India';",
        "ALTER TABLE investigation_workspaces ADD COLUMN IF NOT EXISTS jurisdiction VARCHAR(100);",
        
        # ThermalEvent
        "ALTER TABLE thermal_events ADD COLUMN IF NOT EXISTS country VARCHAR(100) DEFAULT 'India';",
        "ALTER TABLE thermal_events ADD COLUMN IF NOT EXISTS jurisdiction VARCHAR(100);",
        
        # IndustrialFacility
        "ALTER TABLE industrial_facilities ADD COLUMN IF NOT EXISTS country VARCHAR(100) DEFAULT 'India';",
        "ALTER TABLE industrial_facilities ADD COLUMN IF NOT EXISTS jurisdiction VARCHAR(100);"
    ]

    for stmt in statements:
        print(f"Executing: {stmt}")
        cur.execute(stmt)

    print("Phase 6 database schema migration successfully completed.")
    cur.close()
    conn.close()

if __name__ == "__main__":
    run_migration()
