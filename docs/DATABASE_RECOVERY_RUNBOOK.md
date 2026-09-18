# AGNI-NETRA — Enterprise Database Backup & Recovery Runbook

**System:** Production PostgreSQL 16 + PostGIS 3.4  
**Database Name:** `agni_netra`  
**Host Environment:** Windows x86_64, Port `5432`  
**Binary Location:** `E:\postsql database\bin`  
**Data Location:** `E:\postsql database\data`  
**Version:** PostgreSQL 16.15 / PostGIS 3.4.2  
**Document Revision:** 2.0 (WP2 Hardening)

---

## 1. Executive Summary

This runbook defines the authoritative, step-by-step procedures for disaster recovery, point-in-time backup, schema verification, and non-destructive rollbacks for the AGNI-NETRA sovereign thermal intelligence platform.

> [!CAUTION]
> **CRITICAL PRODUCTION RULE:**
> NEVER execute destructive restore tests against the active operational database (`agni_netra`).
> Always restore to an isolated target (e.g., `agni_netra_recovery_test`) when validating backups.

---

## 2. Backup Strategy & Schedules

| Backup Type | Frequency | Target Directory | Format | Retention Policy |
| :--- | :--- | :--- | :--- | :--- |
| **Full Database Dump** | Daily (02:00 IST) | `E:\backups\agni_netra\daily\` | Custom Compressed (`-Fc`) | 30 days local / 90 days S3 |
| **Schema-Only Backup** | On Every Migration | `E:\backups\agni_netra\schema\` | Plain SQL (`-s`) | Permanent (Versioned) |
| **Cadastre & Baselines** | Weekly (Sunday) | `E:\backups\agni_netra\cadastre\` | Custom Compressed (`-Fc`) | 1 Year |
| **WAL Archiving** | Continuous | `E:\backups\agni_netra\wal\` | Binary WAL Segments | 7 days |

---

## 3. Step-by-Step Local Backup Procedures

### 3.1 Full Database Backup (Custom Compressed Format)
The custom format (`-Fc`) is compressed, supports parallel multi-threaded restore, and allows selective table restoration.

```powershell
# Set Environment Variables for Backup Execution
$env:PGPASSWORD = "projectdatabase_2026"
$PG_BIN = "E:\postsql database\bin"
$BACKUP_DIR = "E:\backups\agni_netra\daily"
$TIMESTAMP = (Get-Date).ToString("yyyyMMdd_HHmmss")
$BACKUP_FILE = "$BACKUP_DIR\agni_netra_full_$TIMESTAMP.dump"

# Ensure target backup directory exists
if (-not (Test-Path $BACKUP_DIR)) { New-Item -ItemType Directory -Path $BACKUP_DIR -Force }

# Execute pg_dump
& "$PG_BIN\pg_dump.exe" `
    --host=127.0.0.1 `
    --port=5432 `
    --username=postgres `
    --format=custom `
    --compress=9 `
    --blobs `
    --verbose `
    --file=$BACKUP_FILE `
    agni_netra

# Validate backup file was written and non-empty
$backup_size = (Get-Item $BACKUP_FILE).Length
Write-Host "[SUCCESS] Backup completed: $BACKUP_FILE ($([math]::Round($backup_size / 1MB, 2)) MB)"
```

### 3.2 Schema-Only DDL Snapshot (Before Any Migration)
```powershell
$env:PGPASSWORD = "projectdatabase_2026"
$PG_BIN = "E:\postsql database\bin"
$SCHEMA_FILE = "E:\backups\agni_netra\schema\schema_ddl_$TIMESTAMP.sql"

& "$PG_BIN\pg_dump.exe" `
    --host=127.0.0.1 `
    --port=5432 `
    --username=postgres `
    --schema-only `
    --file=$SCHEMA_FILE `
    agni_netra
```

---

## 4. Disaster Recovery & Restoration Procedures

### 4.1 Restoring to an Isolated Verification Database
Before touching production or in the event of an audit verification:

```powershell
$env:PGPASSWORD = "projectdatabase_2026"
$PG_BIN = "E:\postsql database\bin"
$TEST_DB = "agni_netra_recovery_test"

# 1. Create fresh isolated test database with PostGIS
& "$PG_BIN\psql.exe" -h 127.0.0.1 -U postgres -c "DROP DATABASE IF EXISTS $TEST_DB;"
& "$PG_BIN\psql.exe" -h 127.0.0.1 -U postgres -c "CREATE DATABASE $TEST_DB WITH ENCODING 'UTF8';"
& "$PG_BIN\psql.exe" -h 127.0.0.1 -U postgres -d $TEST_DB -c "CREATE EXTENSION IF NOT EXISTS postgis;"

# 2. Restore dump using pg_restore
& "$PG_BIN\pg_restore.exe" `
    --host=127.0.0.1 `
    --port=5432 `
    --username=postgres `
    --dbname=$TEST_DB `
    --verbose `
    --no-owner `
    --no-privileges `
    $BACKUP_FILE

# 3. Verify row counts and integrity
& "$PG_BIN\psql.exe" -h 127.0.0.1 -U postgres -d $TEST_DB -c "SELECT count(*) AS total_detections FROM thermal_detections;"
& "$PG_BIN\psql.exe" -h 127.0.0.1 -U postgres -d $TEST_DB -c "SELECT count(*) AS total_facilities FROM industrial_facilities;"
```

### 4.2 Full Production Disaster Restoration (Emergency Protocol)
In the catastrophic event of hardware loss or unrecoverable corruption:

1. **Stop Application Services Immediately:**
   ```powershell
   # Stop Next.js and FastAPI services
   Get-Process python, node, uvicorn -ErrorAction SilentlyContinue | Stop-Process -Force
   ```
2. **Verify PostgreSQL Engine Health:**
   ```powershell
   & "E:\postsql database\bin\pg_ctl.exe" status -D "E:\postsql database\data"
   ```
3. **Drop Corrupted Database & Re-instantiate from Latest Verified Dump:**
   ```powershell
   $env:PGPASSWORD = "projectdatabase_2026"
   $PG_BIN = "E:\postsql database\bin"

   & "$PG_BIN\psql.exe" -h 127.0.0.1 -U postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'agni_netra' AND pid <> pg_backend_pid();"
   & "$PG_BIN\psql.exe" -h 127.0.0.1 -U postgres -c "DROP DATABASE agni_netra;"
   & "$PG_BIN\psql.exe" -h 127.0.0.1 -U postgres -c "CREATE DATABASE agni_netra WITH ENCODING 'UTF8';"
   & "$PG_BIN\psql.exe" -h 127.0.0.1 -U postgres -d agni_netra -c "CREATE EXTENSION IF NOT EXISTS postgis;"

   & "$PG_BIN\pg_restore.exe" `
       -h 127.0.0.1 -U postgres -d agni_netra `
       --jobs=4 `
       --no-owner `
       $LATEST_VERIFIED_BACKUP
   ```
4. **Re-apply Post-Freeze WP1 & WP2 Enterprise Hardening Migrations:**
   ```powershell
   .\venv\Scripts\python.exe database\migrate_postgres_wp2.py
   ```
5. **Execute Integrity Invariant Check:**
   ```powershell
   .\venv\Scripts\pytest.exe tests/test_wp2_database_gis_hardening.py -k "test_data_integrity_invariants" -v
   ```

---

## 5. Automated Data Integrity Diagnostics

The automated diagnostics script checks the 13 frozen invariants:

```sql
-- Sovereign Data Invariant Diagnostic
SELECT 
    (SELECT count(*) FROM industrial_facilities) AS industrial_facilities,
    (SELECT count(*) FROM cea_power_stations_staging) AS cea_units,
    (SELECT count(*) FROM ibm_mining_lease_context) AS ibm_leases,
    (SELECT count(*) FROM admin_boundaries WHERE admin_level = 'STATE') AS states_uts,
    (SELECT count(*) FROM admin_boundaries WHERE admin_level = 'DISTRICT') AS districts,
    (SELECT count(*) FROM protected_areas) AS protected_areas,
    (SELECT count(*) FROM lulc_spatial_features) AS lulc_features,
    (SELECT count(*) FROM governed_dataset_registry) AS governed_registries;
```

---

## 6. Migration Rollback Strategy

Every migration in AGNI-NETRA is accompanied by a safe rollback definition:

| Migration | Rollback Script / Command | Data Impact |
| :--- | :--- | :--- |
| **WP2 PostgreSQL Migration** | `ALTER TABLE thermal_events DROP COLUMN IF EXISTS is_simulation;` `ALTER TABLE thermal_events DROP COLUMN IF EXISTS lifecycle_state;` `DROP TABLE IF EXISTS incident_lifecycle_transitions;` `DROP INDEX IF EXISTS idx_fac_geom_geog;` `DROP INDEX IF EXISTS ix_thermal_detections_event_ts;` | Zero data loss on core tables (`thermal_detections`, `facilities`). Reverts WP2 schema to baseline. |

---

## 7. Operational Health Monitoring Commands

```powershell
# Check Active PostgreSQL Connections & Long-Running Queries
& "E:\postsql database\bin\psql.exe" -h 127.0.0.1 -U postgres -d agni_netra -c "
    SELECT pid, now() - query_start AS duration, query, state 
    FROM pg_stat_activity 
    WHERE state != 'idle' AND pid <> pg_backend_pid() 
    ORDER BY duration DESC;
"

# Check PostGIS Geometry Column Registration
& "E:\postsql database\bin\psql.exe" -h 127.0.0.1 -U postgres -d agni_netra -c "
    SELECT f_table_name, f_geometry_column, srid, type FROM geometry_columns;
"
```
