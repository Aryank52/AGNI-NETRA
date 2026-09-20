#!/usr/bin/env python3
"""
AGNI-NETRA — WP5: Model Registry Governance Migration
Adds strict governance columns to ml_model_registry and populates cryptographic hashes.
"""

import os
import sys
import hashlib
from datetime import datetime, timezone
from sqlalchemy import text

WORKSPACE_DIR = r"E:\PROJECTS\AGNI-NETRA"
if WORKSPACE_DIR not in sys.path:
    sys.path.insert(0, WORKSPACE_DIR)

from backend.app.core.database import engine as default_engine, DATABASE_MODE
from sqlalchemy import create_engine

PG_URL = "postgresql+psycopg2://postgres:projectdatabase_2026@localhost:5432/agni_netra"

ARTIFACT_HASHES = {
    "xgb_v3_real_candidate.joblib": "c52b6369da19d4e423652a3001e38c72737f7f66684e5bc27b9bb1c2a9c754d8",
    "rf_v3_real_candidate.joblib": "4a89367317ce4f30e8e253956fb9e27270959b3aa051718bfce13a8b37aa1d40",
    "xgb_v2_real_candidate.joblib": "55c2b5df638fe1bd9c6b98b09cd1c40d16fa5b234cbad26738b2b64de1b8a503",
    "rf_v2_real_candidate.joblib": "bb14f061093a9bfdfc026f5b34829e25cbc536b284b4ca3d1675fc8cfadcb4ec",
    "isolation_forest_v1.joblib": "4215ae0609e3d0c13aa0cb1214a5bc92d3f1039a691baddca99fd0f53b2940c0",
    "rf_classifier_v1.joblib": "b5b5d8807bec20f7506f0ddf313e6a489031fc103f87ba48047714ad0f528798",
    "xgboost_classifier_v1.joblib": "6b484b89c41ebfc05a9fcbc65930989bf4a2e104d8d52f1e1e0c68c03b49f794"
}


def migrate_engine(eng, mode_name):
    print(f"[WP5 MIGRATION] Hardening ml_model_registry on {mode_name}...")
    new_cols = [
        ("model_family", "VARCHAR(50)"),
        ("training_period", "VARCHAR(100)"),
        ("feature_schema_version", "VARCHAR(50) DEFAULT 'v3.2'"),
        ("taxonomy_version", "VARCHAR(50) DEFAULT '7-class-v1'"),
        ("calibration_version", "VARCHAR(50)"),
        ("artifact_sha256", "VARCHAR(64)"),
        ("created_by", "VARCHAR(100) DEFAULT 'SYSTEM_PIPELINE'"),
        ("approval_timestamp", "TIMESTAMP WITH TIME ZONE" if "POSTGRES" in mode_name else "TIMESTAMP")
    ]

    with eng.begin() as conn:
        for col_name, col_type in new_cols:
            try:
                if "POSTGRES" in mode_name:
                    conn.execute(text(f"ALTER TABLE ml_model_registry ADD COLUMN IF NOT EXISTS {col_name} {col_type};"))
                else:
                    conn.execute(text(f"ALTER TABLE ml_model_registry ADD COLUMN {col_name} {col_type};"))
                print(f"  Added column: {col_name}")
            except Exception as e:
                if "already exists" in str(e).lower() or "duplicate column" in str(e).lower():
                    print(f"  Column already exists: {col_name}")
                else:
                    print(f"  Notice on {col_name}: {e}")

        conn.execute(text("""
            UPDATE ml_model_registry
            SET model_family = 'XGBoost',
                training_period = '2022-01-01 to 2024-12-31',
                feature_schema_version = 'v3.2',
                taxonomy_version = '7-class-v1',
                calibration_version = 'balanced-platt-v3.0',
                artifact_sha256 = 'c52b6369da19d4e423652a3001e38c72737f7f66684e5bc27b9bb1c2a9c754d8',
                status = 'CANDIDATE',
                is_active = FALSE
            WHERE version = 'xgb-v3.0-real-candidate';
        """))

        conn.execute(text("""
            UPDATE ml_model_registry
            SET model_family = 'RandomForest',
                training_period = '2022-01-01 to 2024-12-31',
                feature_schema_version = 'v3.2',
                taxonomy_version = '7-class-v1',
                calibration_version = 'none',
                artifact_sha256 = '4a89367317ce4f30e8e253956fb9e27270959b3aa051718bfce13a8b37aa1d40',
                status = 'CANDIDATE',
                is_active = FALSE
            WHERE version = 'rf-v3.0-real-candidate';
        """))

        conn.execute(text("""
            UPDATE ml_model_registry
            SET model_family = 'RandomForest',
                training_period = '2022-01-01 to 2023-12-31',
                feature_schema_version = 'v3.0',
                taxonomy_version = '6-class-v1',
                artifact_sha256 = 'bb14f061093a9bfdfc026f5b34829e25cbc536b284b4ca3d1675fc8cfadcb4ec',
                status = 'RETIRED',
                is_active = FALSE
            WHERE version = 'rf-v2.0-real-candidate';
        """))

        conn.execute(text("""
            UPDATE ml_model_registry
            SET model_family = 'IsolationForest',
                feature_schema_version = 'v1.0',
                taxonomy_version = 'anomaly-v1',
                artifact_sha256 = '4215ae0609e3d0c13aa0cb1214a5bc92d3f1039a691baddca99fd0f53b2940c0'
            WHERE version = 'iso-v1.0-anomaly';
        """))

    print(f"[WP5 MIGRATION] Completed hardening on {mode_name}.")


def migrate_registry():
    migrate_engine(default_engine, DATABASE_MODE)
    try:
        pg_engine = create_engine(PG_URL)
        migrate_engine(pg_engine, "POSTGRESQL")
    except Exception as e:
        print(f"[WP5 MIGRATION] PostgreSQL not reachable: {e}")



if __name__ == "__main__":
    migrate_registry()
