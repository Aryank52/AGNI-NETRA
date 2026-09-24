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
)


class TestCoreMigrationRunnerUnit(unittest.TestCase):
    def setUp(self):
        self.runner = CoreMigrationRunner(
            local_url="postgresql://mock_local:5432/db",
            supabase_url="postgresql://mock_supa:5432/db",
            dry_run=True,
            reconcile=False
        )

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


if __name__ == "__main__":
    unittest.main()
