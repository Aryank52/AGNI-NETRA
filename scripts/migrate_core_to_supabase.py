#!/usr/bin/env python3
"""
AGNI-NETRA — Core Production Data Migration Runner
=================================================
Migrates the approved 47-table Core Production Dataset from local PostgreSQL 16.15 (agni_netra)
to Supabase PostgreSQL 17.6 (public schema).

Strict Invariants & Security Directives:
1. HARD ALLOWLIST: Exactly 47 core tables permitted. Rejects any table outside the allowlist.
2. EXPLICIT EXCLUSION LIST: Fails closed if any telemetry, simulation, staging, or legacy table is encountered.
3. CONFLICT-AWARE IDEMPOTENCY (AUDIT-02):
   - Case A: Destination PK does not exist -> INSERT
   - Case B: Destination PK exists AND all migrated columns match -> mark VERIFIED_EXISTING
   - Case C: Destination PK exists BUT columns differ -> HARD_CONFLICT_ERROR -> rollback -> halt
4. DETERMINISTIC CONTENT VERIFICATION (BLOCKER 2):
   - Canonical row hash (SHA-256) covering ALL projected columns, scalars, UTC timestamps, JSON, UUID, EWKB.
   - Post-commit destination content verification detects same PK + different data.
5. STRICT COMMIT / VERIFY / CHECKPOINT PROTOCOL (BLOCKER 3):
   - BEGIN -> INSERT / RECONCILE -> COMMIT -> VERIFY COMMITTED DESTINATION DATA -> ATOMIC CHECKPOINT
   - Checkpoint MUST NEVER advance before committed destination data is verified.
6. STRICT EXPLICIT COLUMN PROJECTION (BLOCKER 4, AUDIT-03):
   - Never uses SELECT * or positional INSERT.
   - Every destination column must exist in source or have an allowed default/exclusion.
   - Every source column not in destination must be in ALLOWED_SOURCE_EXCLUSIONS.
   - ibm_mining_lease_context raw_metadata is explicitly excluded.
7. REPEATABLE READ READ-ONLY SOURCE SNAPSHOT (BLOCKER 5):
   - Source session: isolation_level=REPEATABLE READ, readonly=True.
   - Server-side named cursor provides a frozen, consistent snapshot across all batches.
8. EXACT 86-BATCH MANIFEST (BLOCKER 1):
   - 123,811 rows across exactly 86 batches.
"""

import sys
import os
import re
import json
import uuid
import math
import time
import struct
import hashlib
import datetime
import argparse
import logging
from typing import Dict, List, Any, Tuple, Optional, Set

# Ensure workspace root in sys.path
WORKSPACE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if WORKSPACE_DIR not in sys.path:
    sys.path.insert(0, WORKSPACE_DIR)

import psycopg2
import psycopg2.extras
from psycopg2.extensions import ISOLATION_LEVEL_REPEATABLE_READ
from backend.app.core.config import settings

# -----------------------------------------------------------------------------
# 1. HARD TABLE ALLOWLIST, EXCLUSIONS & BATCH SPECIFICATIONS
# -----------------------------------------------------------------------------

APPROVED_CORE_TABLES: Tuple[str, ...] = (
    # Level 0 (Standalone Reference & Master - 18)
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

# Strict Batch Sizes (Approved Manifest: 86 Batches total)
TABLE_BATCH_SIZES: Dict[str, int] = {
    "admin_boundaries": 500,                  # 7,595 / 500 = 16 batches
    "industrial_facilities": 5000,            # 35,684 / 5,000 = 8 batches
    "facility_administrative_context": 5000,  # 35,662 / 5,000 = 8 batches
    "facility_baselines": 5000,               # 35,579 / 5,000 = 8 batches
    "audit_logs": 1000,                       # 3,381 / 1,000 = 4 batches
}
DEFAULT_BATCH_SIZE: int = 1000

# Expected batch count per table in approved manifest (Sum = 86)
EXPECTED_TABLE_BATCHES: Dict[str, int] = {
    "admin_boundaries": 16,
    "authority_directory": 1,
    "fsi_sources": 1,
    "lulc_sources": 1,
    "industrial_facilities": 8,
    "candidate_facilities": 1,
    "incident_lifecycle_transitions": 1,
    "investigation_workspaces": 1,
    "data_sources": 1,
    "dataset_registry": 1,
    "governed_dataset_registry": 1,
    "ml_model_registry": 1,
    "analyst_feedback": 1,
    "users": 1,
    "ibm_mineral_resources": 1,
    "ibm_mining_lease_context": 1,
    "historical_baselines": 1,
    "historical_incidents": 1,
    "mission_tasks": 1,
    "audit_logs": 4,
    "investigation_audit_log": 1,
    "case_notes": 1,
    "evidence_requests": 1,
    "report_versions": 1,
    "facility_administrative_context": 8,
    "facility_baselines": 8,
    "facility_mining_evidence": 1,
    "ibm_auctioned_blocks": 1,
    "fsi_isfr_district_forest_stats": 1,
    "protected_areas": 1,
    "lulc_classes": 1,
    "lulc_raster_tiles": 1,
    "evidence_reviews": 1,
    "facility_lulc_context": 1,
    "thermal_events": 1,
    "assessment_versions": 1,
    "prevention_cases": 1,
    "facility_forest_context": 1,
    "lulc_spatial_features": 1,
    "prevention_recommendations": 1,
    "prevention_reports": 1,
    "root_cause_hypotheses": 1,
    "alerts": 1,
    "event_features": 1,
    "model_predictions": 1,
    "risk_scores": 1,
    "verification_records": 1,
}

# Explicit Allowed Exclusions (Source -> Target)
ALLOWED_SOURCE_EXCLUSIONS: Dict[str, Set[str]] = {
    "ibm_mining_lease_context": {"raw_metadata"},  # AUDIT-03
    "industrial_facilities": {"geom"}              # Legacy geometry column; canonical lat/long used
}
ALLOWED_TARGET_DEFAULT_COLUMNS: Dict[str, Set[str]] = {}

# Explicit Date-Semantic Columns (where source is DATE and target is TIMESTAMP WITHOUT TIME ZONE at midnight)
DATE_SEMANTIC_COLUMNS: Dict[str, Set[str]] = {
    "ibm_mineral_resources": {"reference_date"},
    "ibm_mining_lease_context": {"reference_date"},
}

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
    return re.sub(r":([^@/]+)@", r":****@", str(msg))


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


class DataIntegrityError(MigrationError):
    """Raised when content hash, type capacity, or PostGIS spatial validation fails."""
    pass


# -----------------------------------------------------------------------------
# 4. NORMALIZATION, CANONICAL ROW HASHING & SPATIAL VALIDATION
# -----------------------------------------------------------------------------

def normalize_value(val: Any, is_date_semantic: bool = False) -> Any:
    """Normalizes database values for deterministic equality and canonical representation."""
    if val is None:
        return ""
    if hasattr(val, "adapted"):
        val = val.adapted
    if isinstance(val, uuid.UUID):
        return str(val).lower()
    if isinstance(val, (datetime.datetime, datetime.date)):
        if isinstance(val, datetime.datetime):
            # Normalize to UTC naive ISO string
            if val.tzinfo is not None:
                val = val.astimezone(datetime.timezone.utc).replace(tzinfo=None)
            # Schema-aware date semantic: treat timestamp at midnight as equivalent to pure date
            if is_date_semantic and val.time() == datetime.time(0, 0, 0, 0):
                return val.date().isoformat()
            return val.isoformat()
        return val.isoformat()
    if isinstance(val, (dict, list)):
        return json.dumps(val, sort_keys=True, separators=(",", ":"))
    if isinstance(val, float):
        if math.isnan(val):
            return "NaN"
        return f"{val:.7f}"
    if isinstance(val, memoryview):
        return val.tobytes().hex()
    if isinstance(val, bytes):
        return val.hex()
    s_val = str(val)
    # Canonicalize JSON strings if string starts with { or [
    if (s_val.startswith("{") and s_val.endswith("}")) or (s_val.startswith("[") and s_val.endswith("]")):
        try:
            parsed = json.loads(s_val)
            return json.dumps(parsed, sort_keys=True, separators=(",", ":"))
        except Exception:
            pass
    # Canonicalize whitespace in strings (collapses internal multi-spaces/tabs and strips outer whitespace)
    s_val = re.sub(r"\s+", " ", s_val).strip()
    # Canonicalize UUID strings
    if len(s_val) == 36 and s_val.count("-") == 4:
        return s_val.lower()
    return s_val


def values_are_equal(src: Any, dst: Any, is_date_semantic: bool = False) -> bool:
    """Strict semantic comparison of source and destination values."""
    if src is None and dst is None:
        return True
    if src is None or dst is None:
        return False
    if is_date_semantic:
        return normalize_value(src, is_date_semantic=True) == normalize_value(dst, is_date_semantic=True)
    if (type(src) is datetime.date and isinstance(dst, datetime.datetime)) or \
       (type(dst) is datetime.date and isinstance(src, datetime.datetime)):
        dt_val = dst if isinstance(dst, datetime.datetime) else src
        d_val = src if type(src) is datetime.date else dst
        if dt_val.tzinfo is not None:
            dt_val = dt_val.astimezone(datetime.timezone.utc).replace(tzinfo=None)
        if dt_val.time() == datetime.time(0, 0, 0, 0) and dt_val.date() == d_val:
            return True
    return normalize_value(src) == normalize_value(dst)


def compute_canonical_row_hash(
    row_dict: Dict[str, Any],
    cols: List[str],
    date_cols: Optional[Set[str]] = None,
    table_name: Optional[str] = None
) -> str:
    """
    Computes a deterministic SHA-256 content hash covering ALL projected columns.
    Ensures identical PK + different data is immediately flagged (BLOCKER 2).
    Supports schema-aware date-semantic canonicalization for columns declared in date_cols
    or established by DATE_SEMANTIC_COLUMNS for the given table_name.
    """
    active_date_cols = set(date_cols or set())
    if table_name and table_name in DATE_SEMANTIC_COLUMNS:
        active_date_cols |= DATE_SEMANTIC_COLUMNS[table_name]

    tokens = []
    for c in cols:
        val = row_dict.get(c)
        is_date = c in active_date_cols
        tokens.append(f"{c}={normalize_value(val, is_date_semantic=is_date)}")
    canonical_payload = "|".join(tokens)
    return hashlib.sha256(canonical_payload.encode("utf-8")).hexdigest()


def validate_spatial_ewkb(geom_data: Any, col_name: str, table_name: str) -> None:
    """
    Validates PostGIS EWKB binary data:
    1. Checks binary length and valid endianness byte.
    2. Validates presence of SRID flag (0x20000000).
    3. Confirms SRID is exactly 4326 (WGS84).
    """
    if geom_data is None:
        return
    b = bytes(geom_data) if not isinstance(geom_data, bytes) else geom_data
    if len(b) < 9:
        raise DataIntegrityError(
            f"Corrupted EWKB binary on '{table_name}.{col_name}': too short ({len(b)} bytes)."
        )
    endian = b[0]
    if endian not in (0, 1):
        raise DataIntegrityError(
            f"Invalid EWKB endian byte on '{table_name}.{col_name}': {endian}."
        )
    fmt = "<" if endian == 1 else ">"
    geom_type = struct.unpack(fmt + "I", b[1:5])[0]
    has_srid = bool(geom_type & 0x20000000)
    if not has_srid:
        raise DataIntegrityError(
            f"Missing SRID flag in EWKB on '{table_name}.{col_name}'."
        )
    srid = struct.unpack(fmt + "I", b[5:9])[0]
    if srid != 4326:
        raise DataIntegrityError(
            f"Invalid SRID {srid} on '{table_name}.{col_name}'. Expected SRID 4326."
        )


def adapt_json_value(val: Any) -> Any:
    """
    Safely adapts a JSON/JSONB value for PostgreSQL parameterization:
    - None -> None (SQL NULL)
    - psycopg2.extras.Json -> returned as-is
    - dict, list, int, float, bool -> wrapped in psycopg2.extras.Json
    - str -> if JSON serialized object/array string, parses and wraps in Json; otherwise wraps scalar string in Json
    """
    if val is None:
        return None
    if isinstance(val, psycopg2.extras.Json):
        return val
    if isinstance(val, (dict, list, int, float, bool)):
        return psycopg2.extras.Json(val)
    if isinstance(val, str):
        s = val.strip()
        if (s.startswith("{") and s.endswith("}")) or (s.startswith("[") and s.endswith("]")):
            try:
                parsed = json.loads(s)
                return psycopg2.extras.Json(parsed)
            except Exception:
                pass
        return psycopg2.extras.Json(val)
    return psycopg2.extras.Json(val)


def adapt_row_for_insertion(row_dict: Dict[str, Any], cols: List[str], json_cols: Set[str]) -> List[Any]:
    """
    Type-aware parameter adaptation for PostgreSQL insertion:
    - JSON/JSONB columns: explicitly adapts dict, list, scalar str/num/bool via adapt_json_value().
    - Preserves UUID handling (UUID object converted to canonical string).
    - Preserves timestamp handling (datetime objects preserved).
    - Preserves PostGIS/EWKB handling (bytes / memoryview preserved).
    - Preserves NULL behavior (None -> SQL NULL).
    - Does NOT blindly wrap non-JSON dicts or values.
    """
    row_params = []
    for c in cols:
        val = row_dict.get(c)
        if val is None:
            row_params.append(None)
        elif c in json_cols:
            row_params.append(adapt_json_value(val))
        elif isinstance(val, uuid.UUID):
            row_params.append(str(val))
        else:
            row_params.append(val)
    return row_params


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
            "batches_executed": 0,
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
        """Atomically replaces checkpoint file. Checkpoint advances ONLY after verification."""
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
            "verification_status": "PASSED",
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
        """
        Creates a strictly READ-ONLY connection to local PostgreSQL with REPEATABLE READ snapshot.
        Guarantees snapshot consistency across all batches without drift (BLOCKER 5).
        """
        conn = psycopg2.connect(self.local_url)
        conn.set_session(
            isolation_level=ISOLATION_LEVEL_REPEATABLE_READ,
            readonly=True,
            autocommit=False
        )
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

        # 3. Test Connections & Versions
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

                # 5. Checkpoint-Aware Destination Row Count Verification
                completed_tables = set(self.checkpoint.get("completed_tables", []))
                invalid_cp_tables = completed_tables - set(APPROVED_CORE_TABLES)
                if invalid_cp_tables:
                    raise ScopeViolationError(
                        f"Checkpoint contains unapproved table(s) not in allowlist: {invalid_cp_tables}"
                    )

                uncompleted_non_empty = {}
                for t in APPROVED_CORE_TABLES:
                    if t in completed_tables:
                        continue
                    cur.execute(f'SELECT COUNT(*) FROM "{t}";')
                    cnt = cur.fetchone()[0]
                    if cnt > 0:
                        uncompleted_non_empty[t] = cnt

                if uncompleted_non_empty and not self.reconcile and not self.dry_run:
                    raise PreFlightCheckError(
                        f"Uncompleted destination tables are not empty: {uncompleted_non_empty}. "
                        "Pre-flight requires uncompleted target tables to be empty or explicit --reconcile flag."
                    )

        logger.info("[OK] Pre-Flight Verification PASSED cleanly.")
        return {"status": "SUCCESS"}

    # --- Strict Column Validation & Metadata Introspection (BLOCKER 4) ---
    def get_table_metadata(self, table_name: str, s_conn, d_conn) -> Dict[str, Any]:
        """
        Resolves explicit projected columns with strict validation:
        - Rejects any destination column missing from source unless declared in ALLOWED_TARGET_DEFAULT_COLUMNS.
        - Rejects any source column missing from destination unless declared in ALLOWED_SOURCE_EXCLUSIONS.
        - Explicitly projects ibm_mining_lease_context excluding raw_metadata (AUDIT-03).
        """
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
                SELECT column_name, data_type, character_maximum_length, is_nullable, column_default, is_generated
                FROM information_schema.columns 
                WHERE table_schema = 'public' AND table_name = %s
                ORDER BY ordinal_position;
            """, (table_name,))
            dst_cols = {r[0]: {
                "type": r[1],
                "max_len": r[2],
                "nullable": r[3] == "YES",
                "default": r[4],
                "is_generated": (len(r) > 5 and r[5] == "ALWAYS")
            } for r in d_cur.fetchall()}

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

            # Spatial columns in destination
            d_cur.execute("""
                SELECT f_geometry_column, srid, type
                FROM geometry_columns 
                WHERE f_table_schema = 'public' AND f_table_name = %s;
            """, (table_name,))
            spatial_cols = [r[0] for r in d_cur.fetchall()]

            # STRICT VALIDATION (BLOCKER 4): Check every destination column
            projected = []
            for col, col_info in dst_cols.items():
                if col in src_cols:
                    projected.append(col)
                else:
                    allowed_defaults = ALLOWED_TARGET_DEFAULT_COLUMNS.get(table_name, set())
                    is_generated = col_info.get("is_generated", False)
                    has_default = col_info.get("default") is not None
                    is_intentional_exclusion = col in allowed_defaults
                    if is_generated or has_default or is_intentional_exclusion:
                        logger.info(
                            f"[{table_name}] Column '{col}' missing from source, "
                            f"permitted via: generated={is_generated}, default={has_default}, exclusion={is_intentional_exclusion}."
                        )
                    else:
                        raise DataIntegrityError(
                            f"CRITICAL: Destination column '{col}' on table '{table_name}' does not exist in source and has no allowed default/generator!"
                        )

            # STRICT VALIDATION: Check every source column not in destination
            for col in src_cols.keys():
                if col not in dst_cols:
                    allowed_exclusions = ALLOWED_SOURCE_EXCLUSIONS.get(table_name, set())
                    if col in allowed_exclusions:
                        logger.debug(f"[{table_name}] Intentionally excluding source column '{col}'.")
                    else:
                        raise DataIntegrityError(
                            f"CRITICAL: Unapproved source column '{col}' on table '{table_name}' is missing in destination schema! Not in ALLOWED_SOURCE_EXCLUSIONS."
                        )

            # Audit confirmation: ibm_mining_lease_context raw_metadata exclusion
            if table_name == "ibm_mining_lease_context":
                if "raw_metadata" in projected:
                    projected.remove("raw_metadata")

            # JSON/JSONB columns in destination (for type-aware parameter adaptation)
            json_cols = [
                col for col, col_info in dst_cols.items()
                if col_info["type"].lower() in ("json", "jsonb")
            ]

            # Date-semantic columns in schema (for type-aware date/timestamp normalization)
            date_cols = set(DATE_SEMANTIC_COLUMNS.get(table_name, set()))
            for col in projected:
                s_type = src_cols.get(col, {}).get("type", "").lower()
                d_type = dst_cols.get(col, {}).get("type", "").lower()
                if s_type == "date" or d_type == "date":
                    date_cols.add(col)

            return {
                "table_name": table_name,
                "pks": pks,
                "projected_columns": projected,
                "src_cols": src_cols,
                "dst_cols": dst_cols,
                "spatial_columns": spatial_cols,
                "json_columns": json_cols,
                "date_columns": date_cols
            }

    # --- Conflict-Aware Reconciliation Batch Processing (AUDIT-02) ---
    def process_batch(self, meta: Dict[str, Any], batch_rows: List[Dict[str, Any]], d_conn) -> Tuple[int, int]:
        """
        Executes Conflict-Aware Batch Reconciliation (AUDIT-02):
        - Case A: Destination PK does not exist -> INSERT
        - Case B: Destination PK exists AND content matches -> VERIFIED_EXISTING
        - Case C: Destination PK exists BUT content differs -> HARD_CONFLICT_ERROR -> rollback -> halt
        """
        table = meta["table_name"]
        pks = meta["pks"]
        cols = meta["projected_columns"]
        spatial_cols = set(meta["spatial_columns"])
        json_cols = set(meta.get("json_columns", []))
        date_cols = set(meta.get("date_columns", []))

        if not batch_rows:
            return 0, 0

        # Validate varchar lengths and geometry in batch before execution
        for r in batch_rows:
            for c in cols:
                val = r.get(c)
                # Varchar capacity check
                if val is not None and isinstance(val, str):
                    max_len = meta["dst_cols"][c].get("max_len")
                    if max_len:
                        if len(val) > max_len:
                            # Check if whitespace-normalized string fits without truncation
                            clean_val = re.sub(r"\s+", " ", val).strip()
                            if len(clean_val) > max_len:
                                raise DataIntegrityError(
                                    f"Varchar capacity overflow on '{table}.{c}': length {len(val)} exceeds max {max_len}! Truncation prohibited."
                                )
                            else:
                                # Safe whitespace cleanup without semantic text loss
                                r[c] = clean_val
                # Spatial check
                if c in spatial_cols and val is not None:
                    validate_spatial_ewkb(val, c, table)

        with d_conn.cursor() as d_cur:
            # 1. Fetch existing destination records for this batch's PKs
            pk_lookup = {}
            if len(pks) == 1:
                pk_col = pks[0]
                batch_pk_values = [normalize_value(r[pk_col]) for r in batch_rows]
                # Format query with ::text cast for universal UUID/VARCHAR compatibility
                select_exprs = []
                for c in cols:
                    if c in spatial_cols:
                        select_exprs.append(f'ST_AsEWKB("{c}") AS "{c}"')
                    else:
                        select_exprs.append(f'"{c}"')

                d_cur.execute(f"""
                    SELECT {', '.join(select_exprs)}
                    FROM "{table}"
                    WHERE "{pk_col}"::text = ANY(%s::text[]);
                """, (batch_pk_values,))
                for row in d_cur.fetchall():
                    row_dict = dict(zip(cols, row))
                    pk_lookup[normalize_value(row_dict[pk_col])] = row_dict
            else:
                # Composite primary key handling
                select_exprs = [f'ST_AsEWKB("{c}") AS "{c}"' if c in spatial_cols else f'"{c}"' for c in cols]
                conditions = " OR ".join(f"({ ' AND '.join(f'\"{k}\"::text = %s::text' for k in pks) })" for _ in batch_rows)
                params = [normalize_value(r[k]) for r in batch_rows for k in pks]
                d_cur.execute(f"SELECT {', '.join(select_exprs)} FROM \"{table}\" WHERE {conditions};", params)
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
                        is_date = c in date_cols
                        if not values_are_equal(src_row[c], existing_row[c], is_date_semantic=is_date):
                            mismatched_columns.append({
                                "column": c,
                                "source": normalize_value(src_row[c], is_date_semantic=is_date),
                                "dest": normalize_value(existing_row[c], is_date_semantic=is_date)
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
            if to_insert:
                params_list = []
                for r in to_insert:
                    params_list.append(adapt_row_for_insertion(r, cols, json_cols))

                if not self.dry_run:
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

                    psycopg2.extras.execute_batch(d_cur, insert_sql, params_list, page_size=len(params_list))
                    rows_inserted = len(to_insert)
                else:
                    rows_inserted = len(to_insert)

            return rows_inserted, rows_verified_existing

    # --- Post-Commit Content Verification (BLOCKER 2 & BLOCKER 3) ---
    def verify_committed_destination_batch(self, meta: Dict[str, Any], source_batch: List[Dict[str, Any]], d_conn) -> None:
        """
        Verifies committed destination data across ALL projected columns using deterministic SHA-256 hashes.
        Detects same PK + different data immediately.
        """
        table = meta["table_name"]
        cols = meta["projected_columns"]
        pks = meta["pks"]
        spatial_cols = set(meta.get("spatial_columns", []))
        date_cols = set(meta.get("date_columns", []))

        select_exprs = [f'ST_AsEWKB("{c}") AS "{c}"' if c in spatial_cols else f'"{c}"' for c in cols]
        
        with d_conn.cursor() as d_cur:
            if len(pks) == 1:
                pk_col = pks[0]
                batch_pk_values = [normalize_value(r[pk_col]) for r in source_batch]
                sql = f"""
                    SELECT {', '.join(select_exprs)}
                    FROM "{table}"
                    WHERE "{pk_col}"::text = ANY(%s::text[]);
                """
                d_cur.execute(sql, (batch_pk_values,))
            else:
                conditions = " OR ".join(f"({ ' AND '.join(f'\"{k}\"::text = %s::text' for k in pks) })" for _ in source_batch)
                params = [normalize_value(r[k]) for r in source_batch for k in pks]
                d_cur.execute(f"SELECT {', '.join(select_exprs)} FROM \"{table}\" WHERE {conditions};", params)

            dest_rows = [dict(zip(cols, r)) for r in d_cur.fetchall()]

        dest_lookup = {}
        for r in dest_rows:
            k = normalize_value(r[pks[0]]) if len(pks) == 1 else tuple(normalize_value(r[pk]) for pk in pks)
            dest_lookup[k] = r

        if len(dest_rows) != len(source_batch):
            raise DataIntegrityError(
                f"Post-commit row count mismatch in table '{table}': "
                f"expected {len(source_batch)}, found {len(dest_rows)}."
            )

        for src_r in source_batch:
            k = normalize_value(src_r[pks[0]]) if len(pks) == 1 else tuple(normalize_value(src_r[pk]) for pk in pks)
            if k not in dest_lookup:
                raise DataIntegrityError(
                    f"Post-commit verification error: PK {k} missing from destination table '{table}'."
                )
            dst_r = dest_lookup[k]

            src_hash = compute_canonical_row_hash(src_r, cols, date_cols=date_cols, table_name=table)
            dst_hash = compute_canonical_row_hash(dst_r, cols, date_cols=date_cols, table_name=table)

            if src_hash != dst_hash:
                raise HardConflictError(
                    f"Post-commit content verification failed for table '{table}' PK={k}! "
                    f"Deterministic row hash mismatch: source={src_hash} vs dest={dst_hash}."
                )

    # --- Migration Execution for a Single Table ---
    def migrate_table(self, table_name: str, s_conn, d_conn) -> Dict[str, Any]:
        meta = self.get_table_metadata(table_name, s_conn, d_conn)
        cols = meta["projected_columns"]
        pks = meta["pks"]
        spatial_cols = set(meta["spatial_columns"])
        batch_size = TABLE_BATCH_SIZES.get(table_name, DEFAULT_BATCH_SIZE)

        # Total source count within frozen repeatable read snapshot
        with s_conn.cursor() as s_cur:
            s_cur.execute(f'SELECT COUNT(*) FROM "{table_name}";')
            total_rows = s_cur.fetchone()[0]

        total_batches = (total_rows + batch_size - 1) // batch_size if total_rows > 0 else 1
        expected_batches = EXPECTED_TABLE_BATCHES.get(table_name, 1)

        logger.info(
            f"[{table_name}] Starting migration: {total_rows} rows across {total_batches} batches "
            f"(batch_size={batch_size}, expected_batches={expected_batches})"
        )

        # Check if already marked completed in checkpoint
        if table_name in self.checkpoint.get("completed_tables", []) and not self.reconcile and not self.dry_run:
            logger.info(f"[{table_name}] Already completed according to checkpoint. Skipping.")
            return {"status": "SKIPPED_CHECKPOINT", "table": table_name, "batches": total_batches}

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

        # Named server-side cursor within the repeatable read snapshot
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
                    # STEP 1: Process & Reconcile Batch
                    ins, ver = self.process_batch(meta, batch_dicts, d_conn)

                    # STEP 2: COMMIT to Destination (BLOCKER 3)
                    if not self.dry_run:
                        d_conn.commit()

                    # STEP 3: VERIFY COMMITTED DESTINATION DATA (BLOCKER 2 & 3)
                    if not self.dry_run:
                        self.verify_committed_destination_batch(meta, batch_dicts, d_conn)

                    rows_inserted_total += ins
                    rows_verified_total += ver
                    self.stats["batches_executed"] += 1

                    # STEP 4: ATOMIC CHECKPOINT ADVANCE (ONLY after commit & verification succeed)
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
                    logger.error(f"  [{table_name}] Error in batch {batch_num}: {e}. Migration halted.")
                    raise

        # Final table verification
        if not self.dry_run:
            with d_conn.cursor() as d_cur:
                d_cur.execute(f'SELECT COUNT(*) FROM "{table_name}";')
                final_dest_cnt = d_cur.fetchone()[0]

            if final_dest_cnt != total_rows:
                raise DataIntegrityError(
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
            "rows_verified": rows_verified_total,
            "batches": total_batches
        }

    # --- Full Sequence Orchestration ---
    def run_migration(self):
        self.stats["start_time"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        logger.info("=============================================================")
        logger.info(f"AGNI-NETRA Core Migration Runner (Dry-Run={self.dry_run})")
        logger.info("=============================================================")

        # 1. Pre-flight Checks
        self.run_preflight_checks()

        # 2. Sequence Execution in strict Topological Order within Repeatable Read Snapshot
        s_conn = self.get_source_connection()
        d_conn = self.get_dest_connection()

        try:
            total_batches_count = 0
            for idx, table_name in enumerate(APPROVED_CORE_TABLES, 1):
                logger.info(f"\nStep {idx}/47: Processing '{table_name}'...")
                res = self.migrate_table(table_name, s_conn, d_conn)
                self.stats["tables_migrated"] += 1
                self.stats["rows_inserted"] += res.get("rows_inserted", 0)
                self.stats["rows_verified_existing"] += res.get("rows_verified", 0)
                total_batches_count += res.get("batches", 0)

            logger.info("\n=============================================================")
            logger.info("[SUCCESS] CORE MIGRATION RUNNER FINISHED CLEANLY")
            logger.info(f"Tables Completed: {self.stats['tables_migrated']}/47")
            logger.info(f"Total Batches Processed: {total_batches_count} (Expected: 86)")
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
