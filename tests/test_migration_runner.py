import unittest
import os
import sys
import json
import uuid
import struct
import datetime
import psycopg2
from unittest.mock import MagicMock, patch

WORKSPACE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if WORKSPACE_DIR not in sys.path:
    sys.path.insert(0, WORKSPACE_DIR)

from scripts.migrate_core_to_supabase import (
    CoreMigrationRunner,
    APPROVED_CORE_TABLES,
    EXCLUDED_TABLES,
    TABLE_BATCH_SIZES,
    EXPECTED_TABLE_BATCHES,
    HardConflictError,
    ScopeViolationError,
    PreFlightCheckError,
    DataIntegrityError,
    MigrationError,
    normalize_value,
    values_are_equal,
    compute_canonical_row_hash,
    validate_spatial_ewkb,
    adapt_row_for_insertion,
    DATE_SEMANTIC_COLUMNS,
)


class TestCoreMigrationRunnerUnit(unittest.TestCase):
    def setUp(self):
        self.runner = CoreMigrationRunner(
            local_url="postgresql://mock_local:5432/db",
            supabase_url="postgresql://mock_supa:5432/db",
            dry_run=True,
            reconcile=False
        )
        self.runner.checkpoint = {"completed_tables": [], "tables": {}, "in_progress": None}

    # --- TEST 1: Destination empty -> row inserts successfully ---
    def test_01_destination_empty_inserts_successfully(self):
        meta = {
            "table_name": "data_sources",
            "pks": ["id"],
            "projected_columns": ["id", "source_name", "category"],
            "dst_cols": {"id": {}, "source_name": {}, "category": {}},
            "spatial_columns": []
        }
        batch_rows = [
            {"id": "src-1", "source_name": "FIRMS", "category": "THERMAL"},
            {"id": "src-2", "source_name": "OSM", "category": "FACILITY"}
        ]
        mock_d_conn = MagicMock()
        mock_cur = MagicMock()
        mock_d_conn.cursor.return_value.__enter__.return_value = mock_cur
        mock_cur.fetchall.return_value = []

        ins, ver = self.runner.process_batch(meta, batch_rows, mock_d_conn)
        self.assertEqual(ins, 2)
        self.assertEqual(ver, 0)

    # --- TEST 2: Destination contains identical PK + identical content -> VERIFIED_EXISTING ---
    def test_02_destination_identical_verified_existing(self):
        meta = {
            "table_name": "data_sources",
            "pks": ["id"],
            "projected_columns": ["id", "source_name", "category"],
            "dst_cols": {"id": {}, "source_name": {}, "category": {}},
            "spatial_columns": []
        }
        batch_rows = [
            {"id": "src-1", "source_name": "FIRMS", "category": "THERMAL"}
        ]
        mock_d_conn = MagicMock()
        mock_cur = MagicMock()
        mock_d_conn.cursor.return_value.__enter__.return_value = mock_cur
        mock_cur.fetchall.return_value = [("src-1", "FIRMS", "THERMAL")]

        ins, ver = self.runner.process_batch(meta, batch_rows, mock_d_conn)
        self.assertEqual(ins, 0)
        self.assertEqual(ver, 1)

    # --- TEST 3: Destination contains identical PK + different content -> HARD_CONFLICT_ERROR ---
    def test_03_destination_conflict_raises_hard_conflict_error(self):
        meta = {
            "table_name": "data_sources",
            "pks": ["id"],
            "projected_columns": ["id", "source_name", "category"],
            "dst_cols": {"id": {}, "source_name": {}, "category": {}},
            "spatial_columns": []
        }
        batch_rows = [
            {"id": "src-1", "source_name": "FIRMS", "category": "THERMAL_HOTSPOTS"}
        ]
        mock_d_conn = MagicMock()
        mock_cur = MagicMock()
        mock_d_conn.cursor.return_value.__enter__.return_value = mock_cur
        mock_cur.fetchall.return_value = [("src-1", "FIRMS", "DIFFERENT_CATEGORY")]

        with self.assertRaises(HardConflictError) as ctx:
            self.runner.process_batch(meta, batch_rows, mock_d_conn)
        self.assertIn("HARD DATA CONFLICT", str(ctx.exception))

    # --- TEST 4: Batch fails halfway -> transaction rolls back -> checkpoint does not advance ---
    def test_04_batch_failure_rolls_back_and_preserves_checkpoint(self):
        mock_d_conn = MagicMock()
        mock_s_conn = MagicMock()

        meta = {
            "table_name": "authority_directory",
            "pks": ["id"],
            "projected_columns": ["id", "name"],
            "src_cols": {"id": {}, "name": {}},
            "dst_cols": {"id": {}, "name": {}},
            "spatial_columns": []
        }

        self.runner.get_table_metadata = MagicMock(return_value=meta)
        
        s_cur = MagicMock()
        s_cur.fetchone.return_value = [2]
        s_cur.fetchmany.side_effect = [[("1", "Auth 1"), ("2", "Auth 2")], []]
        mock_s_conn.cursor.return_value.__enter__.return_value = s_cur

        self.runner.process_batch = MagicMock(side_effect=psycopg2.OperationalError("Simulated network crash"))
        self.runner._save_checkpoint = MagicMock()
        self.runner.dry_run = False

        with self.assertRaises(psycopg2.OperationalError):
            self.runner.migrate_table("authority_directory", mock_s_conn, mock_d_conn)

        mock_d_conn.rollback.assert_called_once()
        self.runner._save_checkpoint.assert_not_called()

    # --- TEST 5: Database commit succeeds but checkpoint write interrupted -> rerun reconciles ---
    def test_05_checkpoint_interrupted_rerun_reconciles(self):
        meta = {
            "table_name": "users",
            "pks": ["id"],
            "projected_columns": ["id", "email"],
            "dst_cols": {"id": {}, "email": {}},
            "spatial_columns": []
        }
        batch_rows = [
            {"id": "usr-1", "email": "analyst@agni.gov.in"}
        ]
        mock_d_conn = MagicMock()
        mock_cur = MagicMock()
        mock_d_conn.cursor.return_value.__enter__.return_value = mock_cur
        mock_cur.fetchall.return_value = [("usr-1", "analyst@agni.gov.in")]

        ins, ver = self.runner.process_batch(meta, batch_rows, mock_d_conn)
        self.assertEqual(ins, 0)
        self.assertEqual(ver, 1)

    # --- TEST 6: Unexpected table appears in manifest -> runner refuses to execute ---
    def test_06_unexpected_table_raises_scope_violation(self):
        mock_conn = MagicMock()
        with self.assertRaises(ScopeViolationError):
            self.runner.get_table_metadata("unapproved_table_xyz", mock_conn, mock_conn)

        with self.assertRaises(ScopeViolationError):
            self.runner.get_table_metadata("thermal_detections", mock_conn, mock_conn)

    # --- TEST 7: ibm_mining_lease_context contains raw_metadata -> explicit projection excludes it ---
    def test_07_explicit_projection_excludes_raw_metadata(self):
        s_conn = MagicMock()
        d_conn = MagicMock()
        s_cur = MagicMock()
        d_cur = MagicMock()
        s_conn.cursor.return_value.__enter__.return_value = s_cur
        d_conn.cursor.return_value.__enter__.return_value = d_cur

        s_cur.fetchall.return_value = [
            ("id", "uuid", 36),
            ("state", "varchar", 100),
            ("raw_metadata", "jsonb", None)
        ]
        d_cur.fetchall.side_effect = [
            [("id", "varchar", 36, "NO", None), ("state", "varchar", 100, "YES", None)],
            [("id",)],
            []
        ]

        meta = self.runner.get_table_metadata("ibm_mining_lease_context", s_conn, d_conn)
        self.assertNotIn("raw_metadata", meta["projected_columns"])
        self.assertEqual(meta["projected_columns"], ["id", "state"])

    # --- TEST 8: String exceeds varchar limit -> migration stops -> safe whitespace normalization for city ---
    def test_08_varchar_capacity_overflow_stops_migration(self):
        meta = {
            "table_name": "data_sources",
            "pks": ["id"],
            "projected_columns": ["id", "source_name"],
            "dst_cols": {
                "id": {"type": "varchar", "max_len": 36},
                "source_name": {"type": "varchar", "max_len": 10}
            },
            "spatial_columns": []
        }
        # String of length 20 exceeds max_len 10 and cannot be normalized
        batch_rows = [
            {"id": "src-1", "source_name": "A" * 20}
        ]
        mock_d_conn = MagicMock()
        with self.assertRaises(DataIntegrityError) as ctx:
            self.runner.process_batch(meta, batch_rows, mock_d_conn)
        self.assertIn("Varchar capacity overflow", str(ctx.exception))

        # Exact regression test: industrial_facilities.city 'Payal forgins'
        # Raw value is 105 chars with tabs/spaces; normalizes to 97 chars which fits varchar(100)
        raw_city = "Survey No. 236,  \tPlot No. 17,  \tB/H Vikas Stove,  \tAt: Vereval (Shapar)  \tDist: Rajkot (Gujarat - INDIA)"
        payal_meta = {
            "table_name": "industrial_facilities",
            "pks": ["id"],
            "projected_columns": ["id", "city"],
            "dst_cols": {
                "id": {"type": "varchar", "max_len": 36},
                "city": {"type": "varchar", "max_len": 100}
            },
            "spatial_columns": []
        }
        payal_batch = [{"id": "b184d1c5-648f-410e-b55e-b0c2f2e012e7", "city": raw_city}]
        mock_d_conn_2 = MagicMock()
        mock_cur_2 = MagicMock()
        mock_d_conn_2.cursor.return_value.__enter__.return_value = mock_cur_2
        mock_cur_2.fetchall.return_value = []

        ins, ver = self.runner.process_batch(payal_meta, payal_batch, mock_d_conn_2)
        self.assertEqual(ins, 1)
        self.assertEqual(ver, 0)
        # Verify write path mutation: payal_batch was updated with clean_val before insertion
        expected_clean = "Survey No. 236, Plot No. 17, B/H Vikas Stove, At: Vereval (Shapar) Dist: Rajkot (Gujarat - INDIA)"
        self.assertEqual(payal_batch[0]["city"], expected_clean)
        self.assertEqual(len(payal_batch[0]["city"]), 97)
        self.assertLessEqual(len(payal_batch[0]["city"]), 100)

    # --- TEST 9: Invalid geometry -> migration stops ---
    def test_09_invalid_geometry_stops_migration(self):
        # Corrupted short binary (< 9 bytes)
        corrupted_geom = b"\x01\x02\x03"
        with self.assertRaises(DataIntegrityError) as ctx:
            validate_spatial_ewkb(corrupted_geom, "geom", "admin_boundaries")
        self.assertIn("Corrupted EWKB binary", str(ctx.exception))

    # --- TEST 10: Wrong SRID -> migration stops ---
    def test_10_wrong_srid_stops_migration(self):
        # Create EWKB with SRID 3857 (Web Mercator) instead of 4326 (WGS84)
        endian = b"\x01"  # Little endian
        geom_type = struct.pack("<I", 1 | 0x20000000)  # Point with SRID flag
        srid_3857 = struct.pack("<I", 3857)
        point_data = struct.pack("<dd", 77.0, 28.0)
        ewkb_3857 = endian + geom_type + srid_3857 + point_data

        with self.assertRaises(DataIntegrityError) as ctx:
            validate_spatial_ewkb(ewkb_3857, "geom", "admin_boundaries")
        self.assertIn("Expected SRID 4326", str(ctx.exception))

    # --- TEST 11: Content Hash covers ALL columns & detects same PK + different data post-commit ---
    def test_11_content_hash_detects_data_drift_on_same_pk(self):
        meta = {
            "table_name": "risk_scores",
            "pks": ["id"],
            "projected_columns": ["id", "score", "confidence"],
            "spatial_columns": []
        }
        source_batch = [
            {"id": "r-1", "score": 75, "confidence": 0.95}
        ]
        # Same PK 'r-1', but score is 20 in destination
        mock_d_conn = MagicMock()
        mock_cur = MagicMock()
        mock_d_conn.cursor.return_value.__enter__.return_value = mock_cur
        mock_cur.fetchall.return_value = [("r-1", 20, 0.95)]

        with self.assertRaises(HardConflictError) as ctx:
            self.runner.verify_committed_destination_batch(meta, source_batch, mock_d_conn)
        self.assertIn("Post-commit content verification failed", str(ctx.exception))

    # --- TEST 12: Strict COMMIT -> VERIFY -> CHECKPOINT execution order ---
    def test_12_commit_verify_checkpoint_ordering(self):
        meta = {
            "table_name": "authority_directory",
            "pks": ["id"],
            "projected_columns": ["id", "name"],
            "src_cols": {"id": {}, "name": {}},
            "dst_cols": {"id": {}, "name": {}},
            "spatial_columns": []
        }
        mock_s_conn = MagicMock()
        mock_d_conn = MagicMock()

        self.runner.get_table_metadata = MagicMock(return_value=meta)
        s_cur = MagicMock()
        s_cur.fetchone.return_value = [1]
        s_cur.fetchmany.side_effect = [[("1", "Auth 1")], []]
        mock_s_conn.cursor.return_value.__enter__.return_value = s_cur

        # Process batch succeeds
        self.runner.process_batch = MagicMock(return_value=(1, 0))
        # Post-commit verification fails
        self.runner.verify_committed_destination_batch = MagicMock(
            side_effect=HardConflictError("Post-commit hash mismatch")
        )
        self.runner._save_checkpoint = MagicMock()
        self.runner.dry_run = False

        with self.assertRaises(HardConflictError):
            self.runner.migrate_table("authority_directory", mock_s_conn, mock_d_conn)

        # Confirm commit was attempted before verification, but checkpoint was NOT saved
        mock_d_conn.commit.assert_called_once()
        self.runner._save_checkpoint.assert_not_called()

    # --- TEST 13: REPEATABLE READ snapshot isolation configuration ---
    def test_13_repeatable_read_snapshot_configuration(self):
        with patch("psycopg2.connect") as mock_connect:
            mock_conn = MagicMock()
            mock_connect.return_value = mock_conn

            conn = self.runner.get_source_connection()
            mock_conn.set_session.assert_called_once_with(
                isolation_level=psycopg2.extensions.ISOLATION_LEVEL_REPEATABLE_READ,
                readonly=True,
                autocommit=False
            )

    # --- TEST 14: Strict explicit column validation rejects unapproved missing columns ---
    def test_14_strict_column_validation_rejects_arbitrary_missing_columns(self):
        s_conn = MagicMock()
        d_conn = MagicMock()
        s_cur = MagicMock()
        d_cur = MagicMock()
        s_conn.cursor.return_value.__enter__.return_value = s_cur
        d_conn.cursor.return_value.__enter__.return_value = d_cur

        # Source has an unexpected extra column not in ALLOWED_SOURCE_EXCLUSIONS
        s_cur.fetchall.return_value = [
            ("id", "uuid", 36),
            ("unexpected_column", "text", None)
        ]
        d_cur.fetchall.side_effect = [
            [("id", "varchar", 36, "NO", None)],
            [("id",)],
            []
        ]

        with self.assertRaises(DataIntegrityError) as ctx:
            self.runner.get_table_metadata("users", s_conn, d_conn)
        self.assertIn("Unapproved source column 'unexpected_column'", str(ctx.exception))

    # --- TEST 15: Exact 86-batch manifest across all 47 tables ---
    def test_15_batch_manifest_86_batches(self):
        total_batches = sum(EXPECTED_TABLE_BATCHES.values())
        self.assertEqual(len(APPROVED_CORE_TABLES), 47)
        self.assertEqual(len(EXPECTED_TABLE_BATCHES), 47)
        self.assertEqual(total_batches, 86)
        # Check explicit batch sizes
        self.assertEqual(TABLE_BATCH_SIZES["admin_boundaries"], 500)
        self.assertEqual(TABLE_BATCH_SIZES["industrial_facilities"], 5000)
        self.assertEqual(TABLE_BATCH_SIZES["facility_administrative_context"], 5000)
        self.assertEqual(TABLE_BATCH_SIZES["facility_baselines"], 5000)
        self.assertEqual(TABLE_BATCH_SIZES["audit_logs"], 1000)

    # --- TEST 16: Real driver psycopg2 parameter adaptation (TASK 4 regression test) ---
    def test_16_psycopg2_parameter_adaptation_real_driver(self):
        """
        Regression test exercising actual psycopg2 driver parameter adaptation path.
        Fails before fix (can't adapt type 'dict') and passes after type-aware adaptation.
        Tests:
        - JSONB dict (representative raw_metadata from admin_boundaries)
        - JSONB list
        - NULL JSON
        - ordinary scalar (int, str)
        - UUID
        - timestamp (UTC naive & aware)
        - geometry EWKB binary
        """
        import psycopg2
        import uuid
        import datetime

        # Sample representative record modeled directly on admin_boundaries
        representative_row = {
            "id": "522c0f31-24a7-4182-8803-6a6f37a64fc5",
            "admin_level": 1,
            "name": "Puducherry",
            "raw_metadata": {
                "shapeID": "1811400B81659894240990",
                "shapeISO": "IN-PY",
                "shapeName": "Puducherry",
                "shapeGroup": "IND"
            },
            "boundary_tags": ["union_territory", "coastal", "southern_zone"],
            "empty_metadata": None,
            "reference_date": datetime.datetime(2026, 8, 31, 2, 44, 15, tzinfo=datetime.timezone.utc),
            "geom": b"\x01\x01\x00\x00 \xe6\x10\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00",
            "uuid_obj": uuid.UUID("522c0f31-24a7-4182-8803-6a6f37a64fc5")
        }
        cols = [
            "id", "admin_level", "name", "raw_metadata",
            "boundary_tags", "empty_metadata", "reference_date", "geom", "uuid_obj"
        ]
        json_cols = {"raw_metadata", "boundary_tags", "empty_metadata"}

        insert_sql = """
            INSERT INTO admin_boundaries (
                "id", "admin_level", "name", "raw_metadata",
                "boundary_tags", "empty_metadata", "reference_date", "geom", "uuid_obj"
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, ST_GeomFromEWKB(%s), %s);
        """

        # Connect to configured PostgreSQL database for real psycopg2 driver cursor
        from backend.app.core.config import settings
        db_url = os.getenv("LOCAL_DATABASE_URL") or os.getenv("DATABASE_URL") or settings.DATABASE_URL
        if "+psycopg2" in db_url:
            db_url = db_url.replace("+psycopg2", "")
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()

        try:
            # 1. VERIFY FAILURE BEFORE FIX:
            # Raw parameter list with unadapted dict/list causes psycopg2 ProgrammingError
            unadapted_params = [representative_row[c] for c in cols]
            with self.assertRaises(psycopg2.ProgrammingError) as ctx:
                cur.mogrify(insert_sql, unadapted_params)
            self.assertIn("can't adapt type 'dict'", str(ctx.exception))

            # 2. VERIFY SUCCESS AFTER FIX:
            # Type-aware parameter adaptation wraps JSON dict/list and canonicalizes UUID/scalar
            adapted_params = adapt_row_for_insertion(representative_row, cols, json_cols)
            mogrified_bytes = cur.mogrify(insert_sql, adapted_params)

            # Assert SQL is successfully generated and formatted
            self.assertIsInstance(mogrified_bytes, bytes)
            self.assertIn(b"1811400B81659894240990", mogrified_bytes)
            self.assertIn(b"union_territory", mogrified_bytes)
            self.assertIn(b"NULL", mogrified_bytes)
            self.assertIn(b"Puducherry", mogrified_bytes)
            self.assertIn(b"522c0f31-24a7-4182-8803-6a6f37a64fc5", mogrified_bytes)
            self.assertIn(b"ST_GeomFromEWKB", mogrified_bytes)

            # 3. REGRESSION TEST FOR JSON SCALAR VALUES (TASK 5 & 6):
            # Tests exact failed case from investigation_workspaces (INV-20260911-8EA9DA)
            # where scalar string 'KNOWN' previously caused 'invalid input syntax for type json'
            ws_row = {
                "investigation_id": "INV-20260911-8EA9DA",
                "uncertainty": "KNOWN",
                "assessment_changes": "NO_PRIOR_ASSESSMENT",
                "is_active": True,
                "observation_count": 123,
                "empty_meta": None,
                "dict_data": {"level": "HIGH"},
                "list_data": ["sensor_a", "sensor_b"]
            }
            ws_cols = list(ws_row.keys())
            ws_json_cols = {
                "uncertainty", "assessment_changes", "is_active",
                "observation_count", "empty_meta", "dict_data", "list_data"
            }
            ws_insert_sql = f'INSERT INTO investigation_workspaces ({", ".join(f"{c}" for c in ws_cols)}) VALUES ({", ".join(["%s"]*len(ws_cols))});'

            ws_adapted = adapt_row_for_insertion(ws_row, ws_cols, ws_json_cols)
            ws_mogrified = cur.mogrify(ws_insert_sql, ws_adapted)

            self.assertIsInstance(ws_mogrified, bytes)
            # Verify Python "KNOWN" is adapted to JSON string '"KNOWN"' rather than unquoted token KNOWN
            self.assertIn(b'"KNOWN"', ws_mogrified)
            self.assertIn(b'"NO_PRIOR_ASSESSMENT"', ws_mogrified)
            # Verify boolean, numeric, NULL, dict, list
            self.assertIn(b"'true'", ws_mogrified)
            self.assertIn(b"'123'", ws_mogrified)
            self.assertIn(b"NULL", ws_mogrified)
            self.assertIn(b'"HIGH"', ws_mogrified)
            self.assertIn(b'"sensor_a"', ws_mogrified)

        finally:
            cur.close()
            conn.close()

    # --- TEST 17: Checkpoint-Aware Pre-Flight Destination Verification ---
    def test_17_checkpoint_aware_preflight_destination_verification(self):
        """
        Verifies all pre-flight destination verification conditions:
        - TEST A: Clean initial migration (empty checkpoint, empty destination) -> PASS
        - TEST B: Valid checkpoint resume (7 completed tables non-empty, remaining empty) -> PASS
        - TEST C: Unsafe uncompleted data (uncompleted table non-empty) -> FAIL with PreFlightCheckError
        - TEST D: Checkpoint contains unapproved table -> FAIL with ScopeViolationError
        - TEST E: Populated destination without checkpoint -> FAIL without reconcile; PASS with reconcile
        - TEST F: Dry run with uncompleted destination data -> PASS
        """
        import re

        def run_mocked_preflight(completed_tables, dest_counts, dry_run=False, reconcile=False):
            runner = CoreMigrationRunner(
                local_url="postgresql://mock_local:5432/db",
                supabase_url="postgresql://mock_supa:5432/db",
                dry_run=dry_run,
                reconcile=reconcile
            )
            runner.checkpoint = {
                "completed_tables": list(completed_tables),
                "tables": {t: {"status": "COMPLETED"} for t in completed_tables},
                "in_progress": None
            }

            s_conn = MagicMock()
            s_conn.__enter__.return_value = s_conn
            d_conn = MagicMock()
            d_conn.__enter__.return_value = d_conn

            s_cur = MagicMock()
            s_cur.__enter__.return_value = s_cur
            d_cur = MagicMock()
            d_cur.__enter__.return_value = d_cur

            s_conn.cursor.return_value = s_cur
            d_conn.cursor.return_value = d_cur

            s_cur.fetchone.return_value = ("agni_netra", "PostgreSQL 16.15")

            all_tables = [(t,) for t in APPROVED_CORE_TABLES]
            d_cur.fetchall.return_value = all_tables

            def dest_execute(query, *args, **kwargs):
                if "SELECT current_database()" in query:
                    d_cur.fetchone.return_value = ("postgres", "public", "PostgreSQL 17.6")
                elif "COUNT(*)" in query:
                    match = re.search(r'FROM\s+"([^"]+)"', query)
                    tbl = match.group(1) if match else "unknown"
                    cnt = dest_counts.get(tbl, 0)
                    d_cur.fetchone.return_value = (cnt,)

            d_cur.execute.side_effect = dest_execute

            with patch.object(runner, "get_source_connection", return_value=s_conn), \
                 patch.object(runner, "get_dest_connection", return_value=d_conn):
                return runner.run_preflight_checks()

        # TEST A: Clean initial migration
        res_a = run_mocked_preflight(completed_tables=[], dest_counts={})
        self.assertEqual(res_a, {"status": "SUCCESS"})

        # TEST B: Valid checkpoint resume (7 completed tables)
        completed_7 = [
            "admin_boundaries", "authority_directory", "fsi_sources", "lulc_sources",
            "industrial_facilities", "candidate_facilities", "incident_lifecycle_transitions"
        ]
        counts_7 = {t: 100 for t in completed_7}
        res_b = run_mocked_preflight(completed_tables=completed_7, dest_counts=counts_7)
        self.assertEqual(res_b, {"status": "SUCCESS"})

        # TEST C: Unsafe uncompleted data
        counts_c = dict(counts_7)
        counts_c["investigation_workspaces"] = 1
        with self.assertRaises(PreFlightCheckError) as ctx:
            run_mocked_preflight(completed_tables=completed_7, dest_counts=counts_c)
        self.assertIn("investigation_workspaces", str(ctx.exception))

        # TEST D: Unapproved checkpoint table
        with self.assertRaises(ScopeViolationError) as ctx:
            run_mocked_preflight(completed_tables=completed_7 + ["unapproved_bad_table"], dest_counts=counts_7)
        self.assertIn("unapproved_bad_table", str(ctx.exception))

        # TEST E: Populated destination without checkpoint
        with self.assertRaises(PreFlightCheckError):
            run_mocked_preflight(completed_tables=[], dest_counts={"admin_boundaries": 7595})

        # TEST E2: Populated destination with reconcile=True
        res_e2 = run_mocked_preflight(completed_tables=[], dest_counts={"admin_boundaries": 7595}, reconcile=True)
        self.assertEqual(res_e2, {"status": "SUCCESS"})

        # TEST F: Dry run allows uncompleted rows
        res_f = run_mocked_preflight(completed_tables=completed_7, dest_counts=counts_c, dry_run=True)
        self.assertEqual(res_f, {"status": "SUCCESS"})

    # --- TEST 18: Date/Timestamp Schema-Aware Canonical Hash Normalization ---
    def test_18_date_timestamp_canonical_hash_normalization(self):
        """
        Regression tests reproducing exact ibm_mineral_resources post-commit verification failure:
        - Source: datetime.date(2020, 4, 1)
        - Destination: datetime.datetime(2020, 4, 1, 0, 0)
        Verifies:
        1. Exact failure reproduction: canonical representation and SHA-256 hash are identical after fix.
        2. Genuine timestamps remain distinct (preserves timestamp precision, e.g. midnight vs 1 second later).
        3. Timezone-aware datetimes convert deterministically to UTC naive representation.
        4. values_are_equal semantic equivalence check.
        5. verify_committed_destination_batch passes on equivalent date/timestamp and rejects true conflicts.
        """
        src_date = datetime.date(2020, 4, 1)
        dst_dt = datetime.datetime(2020, 4, 1, 0, 0)

        # 1. Exact Failure Reproduction (Requirement 5):
        # A) With is_date_semantic=True, both produce exact canonical string "2020-04-01"
        self.assertEqual(normalize_value(src_date, is_date_semantic=True), "2020-04-01")
        self.assertEqual(normalize_value(dst_dt, is_date_semantic=True), "2020-04-01")

        # B) compute_canonical_row_hash produces IDENTICAL SHA-256 hash with date_cols
        src_row = {"id": "00228a23-1c23-4bcd-ad0b-0b91aac58975", "reference_date": src_date}
        dst_row = {"id": "00228a23-1c23-4bcd-ad0b-0b91aac58975", "reference_date": dst_dt}
        cols = ["id", "reference_date"]

        hash_src = compute_canonical_row_hash(src_row, cols, date_cols={"reference_date"})
        hash_dst = compute_canonical_row_hash(dst_row, cols, date_cols={"reference_date"})
        self.assertEqual(hash_src, hash_dst)

        # C) compute_canonical_row_hash with table_name="ibm_mineral_resources" produces IDENTICAL hash
        hash_src_tbl = compute_canonical_row_hash(src_row, cols, table_name="ibm_mineral_resources")
        hash_dst_tbl = compute_canonical_row_hash(dst_row, cols, table_name="ibm_mineral_resources")
        self.assertEqual(hash_src_tbl, hash_dst_tbl)
        self.assertEqual(hash_src_tbl, hash_src)

        # 2. Genuine Timestamps Remain Distinct (Requirement 6):
        # When not date_semantic, midnight timestamp preserves full ISO timestamp "2020-04-01T00:00:00"
        ts_midnight = datetime.datetime(2020, 4, 1, 0, 0, 0)
        ts_plus_1s = datetime.datetime(2020, 4, 1, 0, 0, 1)
        ts_subsecond = datetime.datetime(2020, 4, 1, 0, 0, 0, 500000)

        self.assertEqual(normalize_value(ts_midnight), "2020-04-01T00:00:00")
        self.assertEqual(normalize_value(ts_plus_1s), "2020-04-01T00:00:01")
        self.assertEqual(normalize_value(ts_subsecond), "2020-04-01T00:00:00.500000")

        # Distinct genuine timestamps produce distinct hashes
        hash_midnight = compute_canonical_row_hash({"created_at": ts_midnight}, ["created_at"])
        hash_plus_1s = compute_canonical_row_hash({"created_at": ts_plus_1s}, ["created_at"])
        self.assertNotEqual(hash_midnight, hash_plus_1s)

        # Even with is_date_semantic=True, non-zero time is not truncated into a date
        ts_afternoon = datetime.datetime(2020, 4, 1, 14, 30, 0)
        self.assertEqual(normalize_value(ts_afternoon, is_date_semantic=True), "2020-04-01T14:30:00")

        # 3. Timezone-Aware Datetimes (Requirement 7):
        ist_tz = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
        ts_ist = datetime.datetime(2020, 4, 1, 5, 30, 0, tzinfo=ist_tz)
        ts_utc = datetime.datetime(2020, 4, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)
        ts_utc_naive = datetime.datetime(2020, 4, 1, 0, 0, 0)

        self.assertEqual(normalize_value(ts_ist), "2020-04-01T00:00:00")
        self.assertEqual(normalize_value(ts_utc), "2020-04-01T00:00:00")
        self.assertEqual(normalize_value(ts_utc_naive), "2020-04-01T00:00:00")

        # Different instant in time with timezone remains distinct
        ts_ist_later = datetime.datetime(2020, 4, 1, 6, 30, 0, tzinfo=ist_tz)
        self.assertEqual(normalize_value(ts_ist_later), "2020-04-01T01:00:00")
        self.assertNotEqual(normalize_value(ts_ist), normalize_value(ts_ist_later))

        # 4. values_are_equal Semantic Equivalence:
        self.assertTrue(values_are_equal(src_date, dst_dt, is_date_semantic=True))
        self.assertTrue(values_are_equal(src_date, dst_dt))  # Automatic date vs midnight datetime detection
        self.assertFalse(values_are_equal(src_date, ts_plus_1s, is_date_semantic=True))
        self.assertFalse(values_are_equal(src_date, datetime.date(2020, 4, 2), is_date_semantic=True))

        # 5. verify_committed_destination_batch Integration:
        meta = {
            "table_name": "ibm_mineral_resources",
            "pks": ["id"],
            "projected_columns": ["id", "reference_date", "reserves"],
            "spatial_columns": [],
            "date_columns": {"reference_date"}
        }
        mock_d_conn = MagicMock()
        mock_cur = MagicMock()
        mock_d_conn.cursor.return_value.__enter__.return_value = mock_cur

        source_batch = [{
            "id": "00228a23-1c23-4bcd-ad0b-0b91aac58975",
            "reference_date": src_date,
            "reserves": 0.0
        }]
        # Destination returns timestamp representation
        mock_cur.fetchall.return_value = [(
            "00228a23-1c23-4bcd-ad0b-0b91aac58975",
            dst_dt,
            0.0
        )]

        # Must pass without raising HardConflictError
        self.runner.verify_committed_destination_batch(meta, source_batch, mock_d_conn)

        # But if destination has truly different date or reserves, must raise HardConflictError
        mock_cur.fetchall.return_value = [(
            "00228a23-1c23-4bcd-ad0b-0b91aac58975",
            datetime.datetime(2020, 4, 2, 0, 0),  # Differing date
            0.0
        )]
        with self.assertRaises(HardConflictError):
            self.runner.verify_committed_destination_batch(meta, source_batch, mock_d_conn)


if __name__ == "__main__":
    unittest.main()
