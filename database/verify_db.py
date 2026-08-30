#!/usr/bin/env python3
"""
AGNI-NETRA — Database Configuration & PostGIS Spatial Diagnostic Tool
Verifies database engine, connection state, PostGIS availability, and Alembic migration status.
"""

import os
import sys
from typing import Dict, Any

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import text
from backend.app.core.config import settings
from backend.app.core.database import (
    engine, SessionLocal, get_database_mode, check_postgis_available,
    get_database_diagnostics, IS_POSTGRESQL, IS_SQLITE_TEST
)


def get_migration_status() -> str:
    """Checks whether the database schema is up-to-date with Alembic migrations."""
    try:
        from alembic.config import Config
        from alembic.script import ScriptDirectory
        from alembic.runtime.migration import MigrationContext

        alembic_cfg_path = os.path.join(os.path.dirname(__file__), "..", "alembic.ini")
        if not os.path.exists(alembic_cfg_path):
            return "ALEMBIC_INI_MISSING"

        alembic_cfg = Config(alembic_cfg_path)
        script = ScriptDirectory.from_config(alembic_cfg)
        head_rev = script.get_current_head()

        with engine.connect() as connection:
            context = MigrationContext.configure(connection)
            current_rev = context.get_current_revision()

        if current_rev == head_rev and head_rev is not None:
            return f"CURRENT ({current_rev})"
        elif current_rev is None and head_rev is not None:
            return f"INITIAL_SCHEMA / UNTRACKED (Head: {head_rev})"
        else:
            return f"OUTDATED (Current: {current_rev}, Head: {head_rev})"
    except Exception as e:
        return f"UNVERIFIED ({str(e)})"


def verify_postgis_spatial_query() -> Dict[str, Any]:
    """Tests an explicit PostGIS spatial query if connected to PostgreSQL."""
    if IS_SQLITE_TEST:
        return {
            "spatial_query_verified": False,
            "engine": "SQLite (Shapely R-Tree Fallback)",
            "details": "PostGIS spatial queries not applicable in SQLite TEST/DEMO mode."
        }

    try:
        with SessionLocal() as session:
            # Test ST_SetSRID, ST_MakePoint, ST_Distance
            query = text("""
                SELECT 
                    ST_Distance(
                        ST_SetSRID(ST_MakePoint(72.8777, 19.0760), 4326)::geography,
                        ST_SetSRID(ST_MakePoint(77.1025, 28.7041), 4326)::geography
                    ) as distance_meters,
                    ST_GeometryType(ST_SetSRID(ST_MakePoint(72.8777, 19.0760), 4326)) as geom_type;
            """)
            row = session.execute(query).first()
            if row:
                dist_km = round(row[0] / 1000.0, 2)
                return {
                    "spatial_query_verified": True,
                    "engine": "PostGIS 3.x",
                    "sample_distance_mumbai_delhi_km": dist_km,
                    "geometry_type": row[1],
                    "srid": 4326
                }
    except Exception as e:
        return {
            "spatial_query_verified": False,
            "engine": "PostgreSQL (PostGIS Error)",
            "error": str(e)
        }

    return {"spatial_query_verified": False, "error": "Unknown error executing spatial query"}


def run_diagnostics():
    diag = get_database_diagnostics()
    migration_status = get_migration_status()
    spatial_result = verify_postgis_spatial_query()

    print("=" * 70)
    print("  AGNI-NETRA -- DATABASE CONFIGURATION & HEALTH REPORT")
    print("=" * 70)
    print(f"  DATABASE_URL configured  : {'YES' if diag['database_url_configured'] else 'NO'}")
    print(f"  Database sanitized URL   : {diag['database_url_sanitized']}")
    print(f"  Database engine          : {diag['database_engine']}")
    print(f"  Database operational mode: {diag['database_mode']}")
    print(f"  Database name            : {diag['database_name']}")
    print(f"  Connection status        : {diag['status']}")
    if diag.get("database_version"):
        print(f"  Database version         : {diag['database_version']}")
    print(f"  PostGIS available        : {'YES' if diag['postgis_available'] else 'NO'}")
    if diag.get("postgis_version"):
        print(f"  PostGIS version          : {diag['postgis_version']}")
    print(f"  Migration state          : {migration_status}")
    print("-" * 70)
    print("  SPATIAL CAPABILITY STATUS:")
    if spatial_result.get("spatial_query_verified"):
        print(f"  [+] PostGIS Spatial Queries : VERIFIED (SRID 4326)")
        print(f"  [+] Sample Geodetic Dist    : Mumbai -> Delhi = {spatial_result.get('sample_distance_mumbai_delhi_km')} km")
    else:
        print(f"  [*] Spatial Engine           : {spatial_result.get('engine')}")
        if spatial_result.get("details"):
            print(f"  [*] Details                  : {spatial_result.get('details')}")
        if spatial_result.get("error"):
            print(f"  [-] Spatial Error            : {spatial_result.get('error')}")
    print("=" * 70)

    if diag["status"] == "CONNECTED":
        print("  [+] Database is operational.")
        return 0
    else:
        print(f"  [-] Database connection failed: {diag.get('connection_error')}")
        return 1


if __name__ == "__main__":
    exit_code = run_diagnostics()
    sys.exit(exit_code)
