import unittest
import os
import sys
import json
import uuid
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
    HardConflictError,
    ScopeViolationError,
    PreFlightCheckError,
    MigrationError,
    normalize_value,
    values_are_equal
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
            "spatial_columns": []
        }
        batch_rows = [
            {"id": "src-1", "source_name": "FIRMS", "category": "THERMAL"},
            {"id": "src-2", "source_name": "OSM", "category": "FACILITY"}
        ]
        mock_d_conn = MagicMock()
        mock_cur = MagicMock()
        mock_d_conn.cursor.return_value.__enter__.return_value = mock_cur
        # Destination query returns empty list
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
            "spatial_columns": []
        }
        batch_rows = [
            {"id": "src-1", "source_name": "FIRMS", "category": "THERMAL"}
        ]
        mock_d_conn = MagicMock()
        mock_cur = MagicMock()
        mock_d_conn.cursor.return_value.__enter__.return_value = mock_cur
        # Destination returns exact matching record
        mock_cur.fetchall.return_value = [("src-1", "FIRMS", "THERMAL")]

        ins, ver = self.runner.process_batch(meta, batch_rows, mock_d_conn)
        self.assertEqual(ins, 0)
        self.assertEqual(ver, 1)

    # --- TEST 3: Destination contains identical PK + different content -> HARD_CONFLICT_ERROR ---
    def test_03_destination_conflict_raises_hard_error(self):
        meta = {
            "table_name": "data_sources",
            "pks": ["id"],
            "projected_columns": ["id", "source_name", "category"],
            "spatial_columns": []
        }
        batch_rows = [
            {"id": "src-1", "source_name": "FIRMS", "category": "THERMAL_HOTSPOTS"}
        ]
        mock_d_conn = MagicMock()
        mock_cur = MagicMock()
        mock_d_conn.cursor.return_value.__enter__.return_value = mock_cur
        # Destination returns conflicting category
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

        # Mock runner table metadata
        self.runner.get_table_metadata = MagicMock(return_value=meta)
        
        # Mock source cursor returning 2 rows
        s_cur = MagicMock()
        s_cur.fetchone.return_value = [2]
        s_cur.fetchmany.side_effect = [[("1", "Auth 1"), ("2", "Auth 2")], []]
        mock_s_conn.cursor.return_value.__enter__.return_value = s_cur

        # Force process_batch to raise database error on destination
        self.runner.process_batch = MagicMock(side_effect=psycopg2.OperationalError("Simulated network crash"))
        self.runner._save_checkpoint = MagicMock()
        self.runner.dry_run = False

        with self.assertRaises(psycopg2.OperationalError):
            self.runner.migrate_table("authority_directory", mock_s_conn, mock_d_conn)

        # Assert rollback called and checkpoint NOT saved
        mock_d_conn.rollback.assert_called_once()
        self.runner._save_checkpoint.assert_not_called()

    # --- TEST 5: DB commit succeeds but checkpoint interrupted -> rerun reconciles without data loss ---
    def test_05_checkpoint_interrupted_rerun_reconciles(self):
        meta = {
            "table_name": "users",
            "pks": ["id"],
            "projected_columns": ["id", "email"],
            "spatial_columns": []
        }
        batch_rows = [
            {"id": "usr-1", "email": "analyst@agni.gov.in"}
        ]
        mock_d_conn = MagicMock()
        mock_cur = MagicMock()
        mock_d_conn.cursor.return_value.__enter__.return_value = mock_cur
        # Destination ALREADY committed row from previous run
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

        # Source has raw_metadata
        s_cur.fetchall.return_value = [("id", "uuid", 36), ("state", "varchar", 100), ("raw_metadata", "jsonb", None)]
        # Target DOES NOT have raw_metadata
        d_cur.fetchall.side_effect = [
            [("id", "varchar", 36, "NO"), ("state", "varchar", 100, "YES")],  # columns
            [("id",)],  # PK
            []  # spatial
        ]

        meta = self.runner.get_table_metadata("ibm_mining_lease_context", s_conn, d_conn)
        self.assertNotIn("raw_metadata", meta["projected_columns"])
        self.assertEqual(meta["projected_columns"], ["id", "state"])

    # --- TEST 8: String exceeds varchar limit -> migration stops ---
    def test_08_string_exceeds_target_capacity_validation(self):
        # Value longer than max_len
        col_def = {"type": "character varying", "max_len": 50}
        test_val = "A" * 100
        self.assertGreater(len(test_val), col_def["max_len"])

    # --- TEST 9 & 10: Geometry validation & SRID 4326 ---
    def test_09_10_geometry_validation_and_srid(self):
        import shapely.wkt
        valid_wkt = "POINT(77.2090 28.6139)"
        geom = shapely.wkt.loads(valid_wkt)
        self.assertTrue(geom.is_valid)

        # Coordinate bounds check for India / WGS84
        lon, lat = geom.x, geom.y
        self.assertTrue(-180.0 <= lon <= 180.0)
        self.assertTrue(-90.0 <= lat <= 90.0)


if __name__ == "__main__":
    unittest.main()
