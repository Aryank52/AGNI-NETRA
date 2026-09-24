#!/usr/bin/env python3
"""
AGNI-NETRA — Real PostgreSQL Backup and Isolated Restore Validation Script
Executes genuine pg_dump -> CREATE DATABASE -> pg_restore -> PostGIS Validation -> DROP DATABASE.
"""

import os
import sys
import time
import subprocess
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

PG_BIN_DIR = r"E:\postsql database\bin"
PG_DUMP = os.path.join(PG_BIN_DIR, "pg_dump.exe")
PG_RESTORE = os.path.join(PG_BIN_DIR, "pg_restore.exe")
PSQL = os.path.join(PG_BIN_DIR, "psql.exe")

HOST = os.getenv("POSTGRES_HOST", "localhost")
PORT = int(os.getenv("POSTGRES_PORT", "5432"))
USER = os.getenv("POSTGRES_USER", "postgres")
PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
SOURCE_DB = os.getenv("POSTGRES_DB", "agni_netra")
RECOVERY_DB = "agni_netra_isolated_restore_test"

BACKUP_ARTIFACT = r"E:\PROJECTS\AGNI-NETRA\database\backups\agni_netra_core_wp8.dump"

def run_backup_restore():
    os.makedirs(os.path.dirname(BACKUP_ARTIFACT), exist_ok=True)
    env = os.environ.copy()
    env["PGPASSWORD"] = PASSWORD

    results = {}

    print("================================================================================")
    print("AGNI-NETRA: REAL POSTGRESQL BACKUP & ISOLATED RESTORE VALIDATION")
    print("================================================================================")

    # --------------------------------------------------------------------------
    # STEP 1: Generate real pg_dump backup artifact
    # --------------------------------------------------------------------------
    print("\n[STEP 1] Generating real pg_dump backup artifact from live database...")
    dump_tables = [
        "-t", "industrial_facilities",
        "-t", "thermal_events",
        "-t", "incident_lifecycle_transitions",
        "-t", "ml_model_registry",
        "-t", "audit_logs",
        "-t", "facility_baselines",
        "-t", "ingestion_batches",
        "-t", "ingestion_quarantine"
    ]
    dump_cmd = [
        PG_DUMP,
        "-h", HOST,
        "-p", str(PORT),
        "-U", USER,
        "-F", "c", # Custom binary archive format
        "-b",      # Include large objects
        "-v",
        "-f", BACKUP_ARTIFACT,
        *dump_tables,
        SOURCE_DB
    ]

    t0 = time.time()
    res = subprocess.run(dump_cmd, env=env, capture_output=True, text=True)
    t_backup = time.time() - t0

    if res.returncode != 0:
        print(f"FAILED pg_dump: {res.stderr}")
        sys.exit(1)

    backup_size_bytes = os.path.getsize(BACKUP_ARTIFACT)
    backup_size_mb = backup_size_bytes / (1024 * 1024)
    print(f"  Backup Method  : pg_dump (custom archive format -Fc)")
    print(f"  Artifact Path  : {BACKUP_ARTIFACT}")
    print(f"  Artifact Size  : {backup_size_mb:.2f} MB ({backup_size_bytes} bytes)")
    print(f"  Backup Duration: {t_backup:.2f} seconds")
    results["backup_duration_sec"] = t_backup
    results["artifact_size_mb"] = backup_size_mb

    # --------------------------------------------------------------------------
    # STEP 2: Create Isolated Recovery Database
    # --------------------------------------------------------------------------
    print(f"\n[STEP 2] Creating isolated recovery database '{RECOVERY_DB}'...")
    conn = psycopg2.connect(host=HOST, port=PORT, user=USER, password=PASSWORD, dbname="postgres")
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()

    cur.execute(f"DROP DATABASE IF EXISTS {RECOVERY_DB};")
    cur.execute(f"CREATE DATABASE {RECOVERY_DB};")
    cur.close()
    conn.close()
    print(f"  Isolated database '{RECOVERY_DB}' successfully created.")

    # --------------------------------------------------------------------------
    # STEP 3: Initialize PostGIS in Isolated Database
    # --------------------------------------------------------------------------
    print(f"\n[STEP 3] Initializing PostGIS extension in '{RECOVERY_DB}'...")
    conn_rec = psycopg2.connect(host=HOST, port=PORT, user=USER, password=PASSWORD, dbname=RECOVERY_DB)
    conn_rec.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur_rec = conn_rec.cursor()
    cur_rec.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
    cur_rec.execute("SELECT PostGIS_Full_Version();")
    postgis_ver = cur_rec.fetchone()[0]
    print(f"  PostGIS initialized: {postgis_ver[:60]}...")
    cur_rec.close()
    conn_rec.close()

    # --------------------------------------------------------------------------
    # STEP 4: Restore Backup Artifact into Isolated Database
    # --------------------------------------------------------------------------
    print(f"\n[STEP 4] Restoring backup artifact via pg_restore into '{RECOVERY_DB}'...")
    restore_cmd = [
        PG_RESTORE,
        "-h", HOST,
        "-p", str(PORT),
        "-U", USER,
        "-d", RECOVERY_DB,
        "-v",
        "--no-owner",
        "--no-privileges",
        BACKUP_ARTIFACT
    ]

    t0 = time.time()
    res_restore = subprocess.run(restore_cmd, env=env, capture_output=True, text=True)
    t_restore = time.time() - t0

    print(f"  Restore Method  : pg_restore")
    print(f"  Restore Duration: {t_restore:.2f} seconds")
    results["restore_duration_sec"] = t_restore

    # --------------------------------------------------------------------------
    # STEP 5: Perform Comprehensive Validation Checks in Isolated Database
    # --------------------------------------------------------------------------
    print(f"\n[STEP 5] Executing comprehensive integrity verification on '{RECOVERY_DB}'...")
    conn_val = psycopg2.connect(host=HOST, port=PORT, user=USER, password=PASSWORD, dbname=RECOVERY_DB)
    cur_val = conn_val.cursor()

    # 5.1 Critical Tables Check
    cur_val.execute("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
        ORDER BY table_name;
    """)
    recovered_tables = [r[0] for r in cur_val.fetchall()]
    print(f"  Recovered Tables ({len(recovered_tables)}): {recovered_tables}")
    assert "industrial_facilities" in recovered_tables
    assert "thermal_events" in recovered_tables
    assert "incident_lifecycle_transitions" in recovered_tables
    assert "ml_model_registry" in recovered_tables

    # 5.2 Geometry Validity Check
    cur_val.execute("SELECT count(*) FROM industrial_facilities WHERE NOT ST_IsValid(geom);")
    invalid_geoms = cur_val.fetchone()[0]
    print(f"  Invalid Geometries in industrial_facilities: {invalid_geoms}")
    assert invalid_geoms == 0, "Geometry corruption detected in restored table"

    # 5.3 PostGIS Spatial Index & Spatial Query Execution
    cur_val.execute("""
        SELECT count(*) FROM industrial_facilities 
        WHERE ST_DWithin(geom, ST_SetSRID(ST_MakePoint(69.86, 22.35), 4326), 0.5);
    """)
    nearby_facs = cur_val.fetchone()[0]
    print(f"  Spatial KNN/ST_DWithin Query: Found {nearby_facs} facilities within 0.5 deg of Jamnagar.")
    assert nearby_facs > 0, "Spatial indexing query failed on restored database"

    # 5.4 Representative Record Counts
    cur_val.execute("SELECT count(*) FROM industrial_facilities;")
    total_facs = cur_val.fetchone()[0]
    print(f"  Total Facilities Count        : {total_facs} (Standard Reference Total: 35,684)")
    assert total_facs == 35684, f"Facility count mismatch: {total_facs} != 35684"

    cur_val.execute("SELECT count(*) FROM industrial_facilities WHERE latitude IS NOT NULL AND longitude IS NOT NULL;")
    geocoded_facs = cur_val.fetchone()[0]
    print(f"  Geolocated Facilities Count   : {geocoded_facs} (Preserved geocoded core)")
    assert geocoded_facs >= 35570, f"Insufficient geolocated facilities: {geocoded_facs} < 35570"

    cur_val.execute("SELECT count(*) FROM industrial_facilities WHERE latitude IS NULL OR longitude IS NULL;")
    staging_variance = cur_val.fetchone()[0]
    print(f"  Provisional Staging Variance  : {staging_variance} (Non-geolocated staging entries)")
    assert staging_variance <= 114, f"Staging variance exceeded: {staging_variance} > 114"

    # 5.5 Thermal Events Snapshot Check
    cur_val.execute("SELECT count(*) FROM thermal_events;")
    evts_count = cur_val.fetchone()[0]
    print(f"  Thermal Events Sample Count   : {evts_count} (Preserved benchmark snapshot)")
    assert evts_count == 264, f"Thermal events count mismatch: {evts_count} != 264"

    # 5.6 Lifecycle Transitions Check
    cur_val.execute("SELECT count(*) FROM incident_lifecycle_transitions;")
    trans_count = cur_val.fetchone()[0]
    print(f"  Lifecycle Transitions Count   : {trans_count}")
    assert trans_count >= 9, "Lifecycle transitions missing"

    # 5.7 Model Governance Registry Check
    cur_val.execute("""
        SELECT version, status, is_active, artifact_sha256, dataset_version 
        FROM ml_model_registry 
        WHERE version = 'xgb-v3.0-real-candidate';
    """)
    model_row = cur_val.fetchone()
    print(f"  Candidate Model Record        : {model_row}")
    assert model_row is not None
    assert model_row[0] == "xgb-v3.0-real-candidate"
    assert model_row[1] == "CANDIDATE"
    assert model_row[2] is False
    assert model_row[3] == "c52b6369da19d4e423652a3001e38c72737f7f66684e5bc27b9bb1c2a9c754d8"
    assert model_row[4] == "v3.2-real-final"

    # Verify no champion is active
    cur_val.execute("SELECT count(*) FROM ml_model_registry WHERE status = 'CHAMPION' AND is_active = True;")
    active_champions = cur_val.fetchone()[0]
    print(f"  Active Production Champions   : {active_champions} (In accordance with invariant)")
    assert active_champions == 0, "Unauthorized active champion detected in registry"

    cur_val.close()
    conn_val.close()

    # --------------------------------------------------------------------------
    # STEP 6: Clean Teardown of Isolated Recovery Database
    # --------------------------------------------------------------------------
    print(f"\n[STEP 6] Cleaning up isolated recovery database '{RECOVERY_DB}'...")
    conn_drop = psycopg2.connect(host=HOST, port=PORT, user=USER, password=PASSWORD, dbname="postgres")
    conn_drop.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur_drop = conn_drop.cursor()
    cur_drop.execute(f"DROP DATABASE IF EXISTS {RECOVERY_DB};")
    cur_drop.close()
    conn_drop.close()
    print(f"  Isolated database '{RECOVERY_DB}' dropped cleanly.")

    print("\n================================================================================")
    print("RESTORE VALIDATION SUMMARY: 100% PASS")
    print(f"Backup Time : {t_backup:.2f}s | Restore Time: {t_restore:.2f}s | Artifact: {backup_size_mb:.2f} MB")
    print("Zero live data mutated. All acceptance criteria verified.")
    print("================================================================================")

if __name__ == "__main__":
    run_backup_restore()
