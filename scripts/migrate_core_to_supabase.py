#!/usr/bin/env python3
"""
AGNI-NETRA — Core Production Data Migration Runner
=================================================
Migrates the approved 47-table Core Production Dataset from local PostgreSQL 16.15 (agni_netra)
to Supabase PostgreSQL 17.6 (public schema).

Strict Invariants:
1. HARD ALLOWLIST: Exactly 47 core tables permitted. Rejects any table outside the allowlist.
2. EXPLICIT EXCLUSION LIST: Fails closed if any telemetry, simulation, staging, or legacy table is encountered.
3. CONFLICT-AWARE IDEMPOTENCY:
   - Case A: Destination PK does not exist -> INSERT
   - Case B: Destination PK exists AND all migrated columns match -> mark VERIFIED_EXISTING
   - Case C: Destination PK exists BUT columns differ -> HARD_CONFLICT_ERROR -> rollback -> halt
4. EXPLICIT COLUMN PROJECTION:
   - Never uses SELECT * or positional INSERT.
   - Explicitly omits unmapped source columns (e.g. raw_metadata on ibm_mining_lease_context, geom on industrial_facilities).
5. SOURCE SAFETY: Read-only session (conn.set_session(readonly=True)).
6. DESTINATION SAFETY:
   - Pre-flight checks verify Supabase target tables are empty before migration.
   - Zero credentials logged or leaked.
7. SPATIAL INTEGRITY: PostGIS EWKB format with strict EPSG:4326 preservation.
8. ATOMIC RESUMABLE CHECKPOINTING:
   - Checkpoint advances ONLY after Supabase COMMIT + verification succeed.
"""

import sys
import os
import json
import uuid
import math
import time
import datetime
import argparse
import logging
from collections import defaultdict, deque
from typing import Dict, List, Any, Tuple, Optional, Set

# Ensure workspace root in sys.path
WORKSPACE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if WORKSPACE_DIR not in sys.path:
    sys.path.insert(0, WORKSPACE_DIR)

import psycopg2
import psycopg2.extras
from backend.app.core.config import settings

# -----------------------------------------------------------------------------
# 1. HARD TABLE ALLOWLIST & EXCLUSIONS
# -----------------------------------------------------------------------------

APPROVED_CORE_TABLES: Tuple[str, ...] = (
    # Level 0 (Standalone Reference - 18)
    "admin_boundaries",
    "authority_directory",
    "fsi_sources",
    "lulc_sources",
    "industrial_facilities",
    "candidate_facilities",
    "incident_lifecycle_transitions",
    "investigation_workspaces",
    "data_sources",
    "dataset_registry",
    "governed_dataset_registry",
    "ml_model_registry",
    "analyst_feedback",
    "users",
    "ibm_mineral_resources",
    "ibm_mining_lease_context",
    "historical_baselines",
    "historical_incidents",
    # Level 1 (Primary Child References - 14)
    "mission_tasks",
    "audit_logs",
    "investigation_audit_log",
    "case_notes",
    "evidence_requests",
    "report_versions",
    "facility_administrative_context",
    "facility_baselines",
    "facility_mining_evidence",
    "ibm_auctioned_blocks",
    "fsi_isfr_district_forest_stats",
    "protected_areas",
    "lulc_classes",
    "lulc_raster_tiles",
    # Level 2 (Secondary References & Events - 3)
    "evidence_reviews",
    "facility_lulc_context",
    "thermal_events",
    # Level 3 (Event Derivatives & Context - 4)
    "assessment_versions",
    "prevention_cases",
    "facility_forest_context",
    "lulc_spatial_features",
    # Level 4 (Alerts, Predictions, & Verification - 8)
    "prevention_recommendations",
    "prevention_reports",
    "root_cause_hypotheses",
    "alerts",
    "event_features",
    "model_predictions",
    "risk_scores",
    "verification_records",
)

EXCLUDED_TABLES: Set[str] = {
    # Massive Telemetry Archive
    "thermal_detections",
    "thermal_history",
    "observation_administrative_context",
    "mining_thermal_associations",
    "observation_lulc_context",
    "observation_forest_context",
    # Synthetic Simulations
    "simulation_scenarios",
    # Empty Tables
    "evidence_records",
    "model_versions",
    "report_delivery_audits",
    "reports",
    "satellite_observations",
    # Legacy / Unmapped
    "alert_audit_logs",
    "ml_prediction_audit_logs",
    "shadow_predictions",
    # Staging & Raw Ingestion
    "osm_staging_facilities",
    "cea_power_stations_staging",
    "parivesh_projects_staging",
    "parivesh_administrative_context",
    "ingestion_records",
    "ibm_mining_lease_context_staging",
    "data_ingestion_jobs",
    "ingestion_batches",
    "ibm_auctioned_blocks_staging",
    "ingestion_quarantine",
    "satellite_telemetry_logs",
    "ibm_nmi_staging",
    "ingestion_checkpoints",
}

# Batch configuration by table
TABLE_BATCH_SIZES: Dict[str, int] = {
    "admin_boundaries": 500,
    "industrial_facilities": 5000,
    "facility_administrative_context": 5000,
    "facility_baselines": 5000,
    "audit_logs": 1000,
    "facility_lulc_context": 1000,
    "facility_forest_context": 1000,
    "investigation_workspaces": 1000,
}
DEFAULT_BATCH_SIZE: int = 1000

CHECKPOINT_PATH = os.path.join(WORKSPACE_DIR, "scratch", "migration_checkpoint.json")

# -----------------------------------------------------------------------------
# 2. LOGGING & SANITIZATION
# -----------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("agni_netra_migration")


def sanitize_message(msg: str) -> str:
    """Masks database passwords or URLs in log messages."""
    return re_sub_password(msg)


def re_sub_password(text: str) -> str:
    import re
    return re.sub(r":([^@/]+)@", r":****@", str(text))


# -----------------------------------------------------------------------------
# 3. CUSTOM EXCEPTIONS
# -----------------------------------------------------------------------------

class MigrationError(Exception):
    """Base exception for migration failures."""
    pass


class HardConflictError(MigrationError):
    """Raised when destination row exists with differing data content."""
    pass


class ScopeViolationError(MigrationError):
    """Raised when an unapproved or excluded table is encountered."""
    pass


class PreFlightCheckError(MigrationError):
    """Raised when pre-flight checks fail."""
    pass


# -----------------------------------------------------------------------------
# 4. NORMALIZATION & COMPARISON HELPERS
# -----------------------------------------------------------------------------

def normalize_value(val: Any) -> Any:
    """Normalizes database values for deterministic equality comparison."""
    if val is None:
        return None
    if isinstance(val, uuid.UUID):
        return str(val).lower()
    if isinstance(val, (datetime.datetime, datetime.date)):
        if isinstance(val, datetime.datetime):
            # Normalize to UTC naive representation for uniform matching
            if val.tzinfo is not None:
                val = val.astimezone(datetime.timezone.utc).replace(tzinfo=None)
            return val.isoformat()
        return val.isoformat()
    if isinstance(val, (dict, list)):
        return json.dumps(val, sort_keys=True)
    if isinstance(val, float):
        if math.isnan(val):
            return "NaN"
        return round(val, 7)
    if isinstance(val, memoryview):
        return val.tobytes().hex()
    if isinstance(val, bytes):
        return val.hex()
    return str(val)


def values_are_equal(src: Any, dst: Any) -> bool:
    """Strict semantic comparison of source and destination values."""
    if src is None and dst is None:
        return True
    if src is None or dst is None:
        return False
    return normalize_value(src) == normalize_value(dst)


# -----------------------------------------------------------------------------
# 5. MIGRATION RUNNER CLASS
# -----------------------------------------------------------------------------

class CoreMigrationRunner:
    def __init__(self, local_url: str, supabase_url: str, dry_run: bool = False, reconcile: bool = False):
        self.local_url = local_url
        self.supabase_url = supabase_url
        self.dry_run = dry_run
        self.reconcile = reconcile
        self.checkpoint = self._load_checkpoint()
        self.stats = {
            "tables_migrated": 0,
            "rows_inserted": 0,
            "rows_verified_existing": 0,
            "start_time": None,
            "end_time": None
        }

    # --- Checkpoint Management ---
    def _load_checkpoint(self) -> Dict[str, Any]:
        if os.path.exists(CHECKPOINT_PATH):
            try:
                with open(CHECKPOINT_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Could not read existing checkpoint: {e}. Starting fresh.")
        return {
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "completed_tables": [],
            "in_progress": None,
            "tables": {}
        }

    def _save_checkpoint(self, table_name: str, batch_num: int, total_batches: int,
                          rows_inserted: int, rows_verified: int, source_cnt: int, dest_cnt: int,
                          completed: bool = False) -> None:
        os.makedirs(os.path.dirname(CHECKPOINT_PATH), exist_ok=True)
        self.checkpoint["last_updated"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        
        table_state = self.checkpoint["tables"].setdefault(table_name, {})
        table_state.update({
            "status": "COMPLETED" if completed else "IN_PROGRESS",
            "last_batch": batch_num,
            "total_batches": total_batches,
            "rows_inserted": rows_inserted,
            "rows_verified_existing": rows_verified,
            "source_count": source_cnt,
            "destination_count": dest_cnt,
            "completed_at": datetime.datetime.now(datetime.timezone.utc).isoformat() if completed else None
        })

        if completed and table_name not in self.checkpoint["completed_tables"]:
            self.checkpoint["completed_tables"].append(table_name)
            self.checkpoint["in_progress"] = None
        elif not completed:
            self.checkpoint["in_progress"] = table_name

        # Atomic file write (tmp -> replace)
        tmp_path = CHECKPOINT_PATH + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(self.checkpoint, f, indent=2)
        os.replace(tmp_path, CHECKPOINT_PATH)

    # --- Database Connections ---
    def get_source_connection(self):
        """Creates a strictly READ-ONLY connection to the local database."""
        conn = psycopg2.connect(self.local_url)
        conn.set_session(readonly=True, autocommit=False)
        return conn

    def get_dest_connection(self):
        """Creates an authenticated connection to Supabase."""
        conn = psycopg2.connect(self.supabase_url)
        conn.set_session(readonly=False, autocommit=False)
        return conn

    # --- Pre-Flight Destination Verification ---
    def run_preflight_checks(self) -> Dict[str, Any]:
        logger.info("Executing Pre-Flight Migration Verification...")

        # 1. Verify Governance Flags
        if getattr(settings, "ENABLE_OPERATIONAL_DISPATCH_GATE", True):
            raise PreFlightCheckError("ENABLE_OPERATIONAL_DISPATCH_GATE is True. Must remain False.")
        if getattr(settings, "ENABLE_AUTOMATED_MODEL_ACTIVATION", True):
            raise PreFlightCheckError("ENABLE_AUTOMATED_MODEL_ACTIVATION is True. Must remain False.")

        # 2. Verify Table Allowlist
        if len(APPROVED_CORE_TABLES) != 47:
            raise ScopeViolationError(f"Allowlist must contain exactly 47 tables; found {len(APPROVED_CORE_TABLES)}")
        
        overlap = set(APPROVED_CORE_TABLES) & EXCLUDED_TABLES
        if overlap:
            raise ScopeViolationError(f"Excluded table(s) found in allowlist: {overlap}")

        # 3. Test Connections
        with self.get_source_connection() as s_conn:
            with s_conn.cursor() as cur:
                cur.execute("SELECT current_database(), version();")
                src_db, src_ver = cur.fetchone()
                logger.info(f"Source verified: Database='{src_db}', Version='{src_ver[:25]}...'")

        with self.get_dest_connection() as d_conn:
            with d_conn.cursor() as cur:
                cur.execute("SELECT current_database(), current_schema(), version();")
                dst_db, dst_schema, dst_ver = cur.fetchone()
                logger.info(f"Destination verified: Database='{dst_db}', Schema='{dst_schema}', Version='{dst_ver[:25]}...'")

                # 4. Verify all 47 tables exist on Supabase
                cur.execute("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_type = 'BASE TABLE';
                """)
                dest_tables = set(r[0] for r in cur.fetchall())
                missing_tables = set(APPROVED_CORE_TABLES) - dest_tables
                if missing_tables:
                    raise PreFlightCheckError(f"Missing core tables on destination: {missing_tables}")

                # 5. Check destination row count
                non_empty = {}
                for t in APPROVED_CORE_TABLES:
                    cur.execute(f'SELECT COUNT(*) FROM "{t}";')
                    cnt = cur.fetchone()[0]
                    if cnt > 0:
                        non_empty[t] = cnt

                if non_empty and not self.reconcile and not self.dry_run:
                    raise PreFlightCheckError(
                        f"Destination tables are not empty: {non_empty}. "
                        "Pre-flight requires a pristine target database or explicit --reconcile flag."
                    )

        logger.info("[OK] Pre-Flight Verification PASSED cleanly.")
        return {"status": "SUCCESS"}

    # --- Table Introspection & Column Projection ---
    def get_table_metadata(self, table_name: str, s_conn, d_conn) -> Dict[str, Any]:
        """Resolves explicit projected columns, primary keys, and spatial columns."""
        if table_name not in APPROVED_CORE_TABLES:
            raise ScopeViolationError(f"Table '{table_name}' rejected by HARD ALLOWLIST.")
        if table_name in EXCLUDED_TABLES:
            raise ScopeViolationError(f"Table '{table_name}' is in EXCLUDED_TABLES.")

        with s_conn.cursor() as s_cur, d_conn.cursor() as d_cur:
            # Source columns
            s_cur.execute("""
                SELECT column_name, data_type, character_maximum_length
                FROM information_schema.columns 
                WHERE table_schema = 'public' AND table_name = %s
                ORDER BY ordinal_position;
            """, (table_name,))
            src_cols = {r[0]: {"type": r[1], "max_len": r[2]} for r in s_cur.fetchall()}

            # Target columns
            d_cur.execute("""
                SELECT column_name, data_type, character_maximum_length, is_nullable
                FROM information_schema.columns 
                WHERE table_schema = 'public' AND table_name = %s
                ORDER BY ordinal_position;
            """, (table_name,))
            dst_cols = {r[0]: {"type": r[1], "max_len": r[2], "nullable": r[3] == "YES"} for r in d_cur.fetchall()}

            # Primary Key
            d_cur.execute("""
                SELECT kcu.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                  ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema
                WHERE tc.constraint_type = 'PRIMARY KEY' AND tc.table_schema = 'public' AND tc.table_name = %s
                ORDER BY kcu.ordinal_position;
            """, (table_name,))
            pks = [r[0] for r in d_cur.fetchall()]
            if not pks:
                raise MigrationError(f"No primary key found for table '{table_name}'.")

            # Spatial column in destination
            d_cur.execute("""
                SELECT f_geometry_column, srid, type
                FROM geometry_columns 
                WHERE f_table_schema = 'public' AND f_table_name = %s;
            """, (table_name,))
            spatial_cols = [r[0] for r in d_cur.fetchall()]

            # Determine projected columns:
            # All destination columns that exist in source
            projected = []
            for col in dst_cols.keys():
                if col in src_cols:
                    projected.append(col)
                elif not dst_cols[col]["nullable"]:
                    raise MigrationError(
                        f"Table '{table_name}' required destination column '{col}' is missing from source!"
                    )

            # Explicit exclusion verification (AUDIT-03)
            if table_name == "ibm_mining_lease_context":
                if "raw_metadata" in projected:
                    projected.remove("raw_metadata")
            if table_name == "industrial_facilities":
                if "geom" in src_cols and "geom" not in dst_cols:
                    if "geom" in projected:
                        projected.remove("geom")

            return {
                "table_name": table_name,
                "pks": pks,
                "projected_columns": projected,
                "src_cols": src_cols,
                "dst_cols": dst_cols,
                "spatial_columns": spatial_cols
            }

    # --- Conflict-Aware Reconciliation Batch Processing ---
    def process_batch(self, meta: Dict[str, Any], batch_rows: List[Dict[str, Any]], d_conn) -> Tuple[int, int]:
        """
        Executes Conflict-Aware Batch Reconciliation (AUDIT-02):
        - Case A: Destination PK does not exist -> INSERT
        - Case B: Destination PK exists AND content matches -> VERIFIED_EXISTING
        - Case C: Destination PK exists BUT content differs -> HARD_CONFLICT_ERROR
        """
        table = meta["table_name"]
        pks = meta["pks"]
        cols = meta["projected_columns"]
        spatial_cols = set(meta["spatial_columns"])

        if not batch_rows:
            return 0, 0

        with d_conn.cursor() as d_cur:
            # 1. Fetch existing destination records for this batch's PKs
            pk_lookup = {}
            if len(pks) == 1:
                pk_col = pks[0]
                batch_pk_values = [str(r[pk_col]) for r in batch_rows]
                # Format query with ::text cast for universal UUID/VARCHAR compatibility
                d_cur.execute(f"""
                    SELECT {', '.join(f'"{c}"' for c in cols)}
                    FROM "{table}"
                    WHERE "{pk_col}"::text = ANY(%s::text[]);
                """, (batch_pk_values,))
                for row in d_cur.fetchall():
                    row_dict = dict(zip(cols, row))
                    pk_lookup[normalize_value(row_dict[pk_col])] = row_dict
            else:
                # Composite primary key handling
                conditions = " OR ".join(f"({ ' AND '.join(f'\"{k}\"::text = %s::text' for k in pks) })" for _ in batch_rows)
                params = [str(r[k]) for r in batch_rows for k in pks]
                d_cur.execute(f"SELECT {', '.join(f'\"{c}\"' for c in cols)} FROM \"{table}\" WHERE {conditions};", params)
                for row in d_cur.fetchall():
                    row_dict = dict(zip(cols, row))
                    key = tuple(normalize_value(row_dict[k]) for k in pks)
                    pk_lookup[key] = row_dict

            to_insert = []
            rows_verified_existing = 0

            # 2. Reconcile each row
            for src_row in batch_rows:
                key = normalize_value(src_row[pks[0]]) if len(pks) == 1 else tuple(normalize_value(src_row[k]) for k in pks)
                
                if key not in pk_lookup:
                    # Case A: Missing in destination -> Prepare for INSERT
                    to_insert.append(src_row)
                else:
                    # Case B & C: Exists in destination -> Compare all columns
                    existing_row = pk_lookup[key]
                    mismatched_columns = []
                    for c in cols:
                        if not values_are_equal(src_row[c], existing_row[c]):
                            mismatched_columns.append({
                                "column": c,
                                "source": normalize_value(src_row[c]),
                                "dest": normalize_value(existing_row[c])
                            })

                    if mismatched_columns:
                        # Case C: HARD CONFLICT
                        raise HardConflictError(
                            f"HARD DATA CONFLICT in table '{table}' for PK {key}! "
                            f"Mismatched attributes: {mismatched_columns[:3]}"
                        )
                    else:
                        # Case B: Identical existing row
                        rows_verified_existing += 1

            # 3. Execute INSERT for non-existent records
            rows_inserted = 0
            if to_insert and not self.dry_run:
                # Build SQL with proper geometry casting
                val_placeholders = []
                for c in cols:
                    if c in spatial_cols:
                        val_placeholders.append("ST_GeomFromEWKB(%s)")
                    else:
                        val_placeholders.append("%s")

                insert_sql = f"""
                    INSERT INTO "{table}" ({', '.join(f'"{c}"' for c in cols)})
                    VALUES ({', '.join(val_placeholders)});
                """

                # Prepare tuples
                params_list = []
                for r in to_insert:
                    params_list.append([r[c] for c in cols])

                psycopg2.extras.execute_batch(d_cur, insert_sql, params_list, page_size=len(params_list))
                rows_inserted = len(to_insert)
            elif to_insert and self.dry_run:
                rows_inserted = len(to_insert)

            return rows_inserted, rows_verified_existing

    # --- Migration Execution for a Single Table ---
    def migrate_table(self, table_name: str, s_conn, d_conn) -> Dict[str, Any]:
        meta = self.get_table_metadata(table_name, s_conn, d_conn)
        cols = meta["projected_columns"]
        pks = meta["pks"]
        spatial_cols = set(meta["spatial_columns"])
        batch_size = TABLE_BATCH_SIZES.get(table_name, DEFAULT_BATCH_SIZE)

        # Total source count
        with s_conn.cursor() as s_cur:
            s_cur.execute(f'SELECT COUNT(*) FROM "{table_name}";')
            total_rows = s_cur.fetchone()[0]

        total_batches = (total_rows + batch_size - 1) // batch_size if total_rows > 0 else 1
        logger.info(f"[{table_name}] Starting migration: {total_rows} rows across ~{total_batches} batches (batch_size={batch_size})")

        # Check if already marked completed in checkpoint
        if table_name in self.checkpoint.get("completed_tables", []) and not self.reconcile and not self.dry_run:
            logger.info(f"[{table_name}] Already completed according to checkpoint. Skipping.")
            return {"status": "SKIPPED_CHECKPOINT", "table": table_name}

        # Build SELECT clause: use ST_AsEWKB for spatial columns
        select_expressions = []
        for c in cols:
            if c in spatial_cols:
                select_expressions.append(f'ST_AsEWKB("{c}") AS "{c}"')
            else:
                select_expressions.append(f'"{c}"')

        # Streaming query with deterministic PK ordering
        order_clause = f"ORDER BY {', '.join(f'\"{k}\" ASC' for k in pks)}"
        query_sql = f'SELECT {", ".join(select_expressions)} FROM "{table_name}" {order_clause};'

        rows_inserted_total = 0
        rows_verified_total = 0
        batch_num = 0

        # Named server-side cursor for constant memory streaming
        cursor_name = f"cur_{table_name}_{int(time.time())}"
        with s_conn.cursor(name=cursor_name) as s_cur:
            s_cur.itersize = batch_size
            s_cur.execute(query_sql)

            while True:
                batch = s_cur.fetchmany(batch_size)
                if not batch:
                    break

                batch_num += 1
                batch_dicts = [dict(zip(cols, row)) for row in batch]

                try:
                    # Process & Reconcile Batch
                    ins, ver = self.process_batch(meta, batch_dicts, d_conn)
                    
                    if not self.dry_run:
                        d_conn.commit()

                    rows_inserted_total += ins
                    rows_verified_total += ver

                    # Update Checkpoint atomically after commit
                    if not self.dry_run:
                        self._save_checkpoint(
                            table_name=table_name,
                            batch_num=batch_num,
                            total_batches=total_batches,
                            rows_inserted=rows_inserted_total,
                            rows_verified=rows_verified_total,
                            source_cnt=total_rows,
                            dest_cnt=rows_inserted_total + rows_verified_total,
                            completed=False
                        )

                    logger.info(f"  [{table_name}] Batch {batch_num}/{total_batches}: +{ins} inserted, {ver} verified existing.")

                except Exception as e:
                    if not self.dry_run:
                        d_conn.rollback()
                    logger.error(f"  [{table_name}] Error in batch {batch_num}: {e}. Transaction rolled back.")
                    raise

        # Final table verification
        if not self.dry_run:
            with d_conn.cursor() as d_cur:
                d_cur.execute(f'SELECT COUNT(*) FROM "{table_name}";')
                final_dest_cnt = d_cur.fetchone()[0]

            if final_dest_cnt != total_rows:
                raise MigrationError(
                    f"Count mismatch on '{table_name}'! Source={total_rows}, Dest={final_dest_cnt}"
                )

            self._save_checkpoint(
                table_name=table_name,
                batch_num=total_batches,
                total_batches=total_batches,
                rows_inserted=rows_inserted_total,
                rows_verified=rows_verified_total,
                source_cnt=total_rows,
                dest_cnt=final_dest_cnt,
                completed=True
            )

        logger.info(f"[OK] [{table_name}] Successfully completed: {total_rows} rows accounted for.")
        return {
            "table": table_name,
            "status": "SUCCESS",
            "source_count": total_rows,
            "rows_inserted": rows_inserted_total,
            "rows_verified": rows_verified_total
        }

    # --- Full Sequence Orchestration ---
    def run_migration(self):
        self.stats["start_time"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        logger.info("=============================================================")
        logger.info(f"AGNI-NETRA Core Migration Runner (Dry-Run={self.dry_run})")
        logger.info("=============================================================")

        # 1. Pre-flight Checks
        self.run_preflight_checks()

        # 2. Sequence Execution in strict Topological Order
        s_conn = self.get_source_connection()
        d_conn = self.get_dest_connection()

        try:
            for idx, table_name in enumerate(APPROVED_CORE_TABLES, 1):
                logger.info(f"\nStep {idx}/47: Processing '{table_name}'...")
                res = self.migrate_table(table_name, s_conn, d_conn)
                self.stats["tables_migrated"] += 1
                self.stats["rows_inserted"] += res.get("rows_inserted", 0)
                self.stats["rows_verified_existing"] += res.get("rows_verified", 0)

            logger.info("\n=============================================================")
            logger.info("[SUCCESS] CORE MIGRATION RUNNER FINISHED CLEANLY")
            logger.info(f"Tables Completed: {self.stats['tables_migrated']}/47")
            logger.info(f"Total Rows Inserted: {self.stats['rows_inserted']}")
            logger.info(f"Total Rows Verified Existing: {self.stats['rows_verified_existing']}")
            logger.info("=============================================================")

        finally:
            s_conn.close()
            d_conn.close()
            self.stats["end_time"] = datetime.datetime.now(datetime.timezone.utc).isoformat()


# -----------------------------------------------------------------------------
# 6. CLI ENTRY POINT
# -----------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="AGNI-NETRA Controlled Core Data Migration Runner")
    parser.add_argument("--dry-run", action="store_true", help="Perform pre-flight and dry-run validation without writing to Supabase.")
    parser.add_argument("--reconcile", action="store_true", help="Allow running reconciliation against partially migrated tables.")
    args = parser.parse_args()

    local_url = os.getenv("LOCAL_DATABASE_URL", "postgresql://postgres:projectdatabase_2026@127.0.0.1:5432/agni_netra")
    supabase_url = settings.DATABASE_URL.replace("+psycopg2", "") if "+psycopg2" in settings.DATABASE_URL else settings.DATABASE_URL

    runner = CoreMigrationRunner(
        local_url=local_url,
        supabase_url=supabase_url,
        dry_run=args.dry_run,
        reconcile=args.reconcile
    )

    if args.dry_run:
        logger.info("[MODE: DRY RUN] No rows will be written to Supabase.")
        runner.run_migration()
    else:
        logger.warning("ACTUAL PRODUCTION EXECUTION REQUESTED.")
        confirm = input("Are you sure you want to run the real core migration to Supabase? (type 'MIGRATE'): ")
        if confirm == "MIGRATE":
            runner.run_migration()
        else:
            logger.info("Migration aborted by user.")


if __name__ == "__main__":
    main()
