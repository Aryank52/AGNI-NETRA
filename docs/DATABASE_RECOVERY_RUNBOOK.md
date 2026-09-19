# AGNI-NETRA — DATABASE BACKUP & RECOVERY RUNBOOK (WP8)
## Disaster Recovery, Point-in-Time Restoration & PostGIS Verification SOP

**Document Version:** 1.0.0  
**Effective Date:** September 19, 2026  
**Audience:** Database Administrators (DBA), Infrastructure Engineers, Incident Commanders  
**Target Environment:** PostgreSQL 16.15 / PostGIS 3.4.2 Enterprise Instance  
**Authority:** Sovereign Republic of India Geospatial Intelligence Standards  

---

## 1. Overview & Objective

This runbook establishes deterministic Standard Operating Procedures (SOP) for the backup, validation, and disaster recovery of the AGNI-NETRA geospatial intelligence database. 

The primary database maintains:
- **35,684 Total Industrial Facilities** (35,570 active geocoded facilities, 114 legacy staging variance)
- **502 Distinct CEA Power Stations** (1,633 generating units)
- **8.22M Historical Thermal Observations**
- **Incident Lifecycle Transitions & Investigation Workspaces**
- **Sovereign Administrative Boundaries (EPSG:4326)**

---

## 2. Backup Architecture & Policy

### 2.1 Backup Tiers
1. **Continuous WAL Archiving (Physical Backup)**:
   - Archive mode enabled with write-ahead logging sent to immutable offsite storage.
   - Enables Point-in-Time Recovery (PITR) to any sub-second timestamp in the preceding 30 days.
2. **Daily Logical Export (`pg_dump`)**:
   - Automated nightly export with custom compressed directory format (`-Fd`).
   - Captures schema definitions, table data, spatial indexes, and sequence states.

### 2.2 Canonical Logical Backup Command
```bash
pg_dump -h localhost -p 5432 -U postgres -d agni_netra \
  -Fd -j 4 -Z 9 \
  --blobs \
  -f "/var/backups/agni_netra/agni_netra_backup_$(date +%Y%m%d_%H%M%S).dump"
```

---

## 3. Disaster Recovery & Restoration SOP

### 3.1 Scenario A: Full Disaster Recovery (Fresh Instance Restore)

#### Step 1: Initialize Database & PostGIS Extensions
```sql
CREATE DATABASE agni_netra WITH ENCODING = 'UTF8' LC_COLLATE = 'English_United States.1252' LC_CTYPE = 'English_United States.1252';
\c agni_netra;
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
```

#### Step 2: Restore Logical Dump with Multi-Threaded Loader
```bash
pg_restore -h localhost -p 5432 -U postgres -d agni_netra \
  -j 4 --clean --if-exists --exit-on-error \
  "/var/backups/agni_netra/agni_netra_backup_LATEST.dump"
```

#### Step 3: Run Database Vacuum & Analyze
```sql
VACUUM (ANALYZE, VERBOSE);
```

---

### 3.2 Scenario B: Isolated Point-in-Time Staging Restore (Non-Destructive)

To test a recovery or investigate past historical state without modifying the active production database:

#### Step 1: Create Dedicated Sandbox Schema
```sql
CREATE SCHEMA staging_recovery_audit;
```

#### Step 2: Restore Selected Tables into Staging
```bash
pg_restore -h localhost -p 5432 -U postgres -d agni_netra \
  --schema=staging_recovery_audit \
  "/var/backups/agni_netra/agni_netra_backup_LATEST.dump"
```

---

## 4. Post-Recovery Validation Protocol

Following any restore event, the automated verification script **MUST** be executed:

```bash
python scripts/verify_backup_recovery.py
```

### 4.1 Acceptance Criteria Checklist

| Verification Check | Target Standard | Verification Query |
|:---|:---|:---|
| **PostGIS Extension** | `3.4.2` | `SELECT PostGIS_Full_Version();` |
| **Active Facilities Count** | Exactly `35,570` (35,684 Total) | `SELECT count(*) FROM industrial_facilities WHERE is_active = true;` |
| **CEA Generating Units** | Exactly `1,633` (502 Stations) | `SELECT count(*) FROM cea_power_stations_staging;` |
| **Spatial Reference System** | `EPSG:4326` (WGS 84) | `SELECT Find_SRID('public', 'industrial_facilities', 'geom');` |
| **Spatial Index Integrity** | Functional GIST Index | `SELECT count(*) FROM industrial_facilities WHERE ST_DWithin(geom, ST_SetSRID(ST_MakePoint(70.0, 22.0), 4326), 0.5);` |
| **Territorial Containment** | Latitude $[6^\circ, 38^\circ]$, Longitude $[68^\circ, 98^\circ]$ | `SELECT MIN(latitude), MAX(latitude), MIN(longitude), MAX(longitude) FROM thermal_events;` |
| **Model Governance Lineage** | Candidate: `xgb-v3.0-real-candidate`<br>Artifact: `c52b6369...`<br>Status: `CANDIDATE`<br>Active: `FALSE` | `SELECT version, status, is_active, artifact_sha256 FROM ml_model_registry WHERE version = 'xgb-v3.0-real-candidate';` |
| **Safety Gates** | `ENABLE_OPERATIONAL_DISPATCH_GATE = False`<br>`ENABLE_AUTOMATED_MODEL_ACTIVATION = False` | Verified via application configuration and backend unit tests |

---

## 5. Failure Scenarios & Troubleshooting Matrix

| Failure Symptom | Root Cause | Remediation Procedure |
|:---|:---|:---|
| **PostGIS function errors (`ST_DWithin` missing)** | PostGIS extension not initialized before restoring tables. | Execute `CREATE EXTENSION postgis;` in the target database before executing `pg_restore`. |
| **Geometry SRID mismatch (0 instead of 4326)** | Spatial column created without explicit SRID constraint. | Execute: `ALTER TABLE industrial_facilities ALTER COLUMN geom TYPE geometry(Point, 4326) USING ST_SetSRID(geom, 4326);` |
| **GIST index corruption** | Incomplete index build during multi-threaded restore. | Execute: `REINDEX TABLE industrial_facilities; REINDEX TABLE thermal_events;` |
| **Transaction aborted during restore** | Schema constraint violation or sequence sync mismatch. | Check logs for primary key collisions; ensure target schema is clean before restore. |

---

## 6. Escalation & Contact

- **Lead Database Administrator**: `dba@agni-netra.gov.in`
- **Geospatial Infrastructure Lead**: `gis-infra@agni-netra.gov.in`
- **Emergency Operations Desk**: Secure VoIP `AGNI-DBA-911`
