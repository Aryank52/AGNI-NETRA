"""
AGNI-NETRA — Post-Freeze Hardening WP1 Migration
Adds lifecycle_state and is_simulation columns to thermal_events.
Creates the incident_lifecycle_transitions audit ledger table.
Ensures indexes on thermal_detections.event_id and spatial-temporal coordinates.
Compatible with both PostgreSQL and SQLite.
"""

import sys
import os
from sqlalchemy import text, inspect

WORKSPACE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if WORKSPACE_DIR not in sys.path:
    sys.path.insert(0, WORKSPACE_DIR)

from backend.app.core.database import engine, Base, IS_POSTGRESQL
import backend.app.models.domain  # Ensure models are loaded into Base.metadata


def migrate_wp1():
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    # 1. Create incident_lifecycle_transitions table if missing
    if "incident_lifecycle_transitions" not in existing_tables:
        print("[MIGRATE WP1] Creating table 'incident_lifecycle_transitions'...")
        Base.metadata.tables["incident_lifecycle_transitions"].create(bind=engine, checkfirst=True)
        print("[MIGRATE WP1] Table 'incident_lifecycle_transitions' created successfully.")
    else:
        print("[MIGRATE WP1] Table 'incident_lifecycle_transitions' already exists.")

    # 2. Add lifecycle_state and is_simulation to thermal_events if missing
    if "thermal_events" in existing_tables:
        existing_cols = [c["name"] for c in inspector.get_columns("thermal_events")]
        with engine.connect() as conn:
            if "lifecycle_state" not in existing_cols:
                print("[MIGRATE WP1] Adding column 'lifecycle_state' to 'thermal_events'...")
                if IS_POSTGRESQL:
                    conn.execute(text("ALTER TABLE thermal_events ADD COLUMN IF NOT EXISTS lifecycle_state VARCHAR(50) DEFAULT 'OBSERVED';"))
                else:
                    conn.execute(text("ALTER TABLE thermal_events ADD COLUMN lifecycle_state VARCHAR(50) DEFAULT 'OBSERVED';"))
                print("[MIGRATE WP1] Added 'lifecycle_state'.")

            if "is_simulation" not in existing_cols:
                print("[MIGRATE WP1] Adding column 'is_simulation' to 'thermal_events'...")
                if IS_POSTGRESQL:
                    conn.execute(text("ALTER TABLE thermal_events ADD COLUMN IF NOT EXISTS is_simulation BOOLEAN DEFAULT FALSE;"))
                else:
                    conn.execute(text("ALTER TABLE thermal_events ADD COLUMN is_simulation BOOLEAN DEFAULT 0;"))
                print("[MIGRATE WP1] Added 'is_simulation'.")

            conn.commit()

    # 3. Create indexes on thermal_detections if needed
    if "thermal_detections" in existing_tables:
        existing_indexes = [idx["name"] for idx in inspector.get_indexes("thermal_detections")]
        with engine.connect() as conn:
            if "ix_thermal_detections_event_id" not in existing_indexes:
                print("[MIGRATE WP1] Creating index 'ix_thermal_detections_event_id'...")
                try:
                    conn.execute(text("CREATE INDEX ix_thermal_detections_event_id ON thermal_detections (event_id);"))
                    print("[MIGRATE WP1] Index 'ix_thermal_detections_event_id' created.")
                except Exception as e:
                    print(f"[MIGRATE WP1] Notice on ix_thermal_detections_event_id: {e}")

            if "ix_thermal_detections_lat_lon_ts" not in existing_indexes:
                print("[MIGRATE WP1] Creating composite index 'ix_thermal_detections_lat_lon_ts'...")
                try:
                    conn.execute(text("CREATE INDEX ix_thermal_detections_lat_lon_ts ON thermal_detections (latitude, longitude, acq_timestamp);"))
                    print("[MIGRATE WP1] Composite index 'ix_thermal_detections_lat_lon_ts' created.")
                except Exception as e:
                    print(f"[MIGRATE WP1] Notice on ix_thermal_detections_lat_lon_ts: {e}")

            conn.commit()

    print("[MIGRATE WP1] Migration complete.")


if __name__ == "__main__":
    migrate_wp1()
