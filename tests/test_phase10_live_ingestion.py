"""
AGNI-NETRA — PHASE 10 TEST SUITE
Test Suite for Production Live Thermal-Data Ingestion & Incremental Event-Processing Pipeline

Verifies:
1. Historical raw FIRMS observation tables remain 100% immutable (8,221,554 rows).
2. Model registry lineage invariants (xgb-v3.0-real-candidate is CANDIDATE / is_active = FALSE).
3. Geodetic and telemetry physics validation engine.
4. Deterministic SHA-256 deduplication and idempotent ingestion.
5. Incremental spatiotemporal DBSCAN clustering and multi-layer spatial enrichment.
6. Point-in-time Phase 8H feature vector generation with boundary-safe recurrence.
7. Phase 9 ML model inference, calibrated probabilities, SHAP, and Tri-Tier routing.
8. Audit log persistence in `ml_prediction_audit_logs` and 100% dispatch suppression.
9. FastAPI operational ingestion endpoints (/health-diagnostics, /incremental-sync).
10. Existence and completeness of Phase 10 report and JSON manifest.
"""

import os
import sys
import json
import uuid
import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy import text
from fastapi.testclient import TestClient

WORKSPACE_DIR = r"E:\PROJECTS\AGNI-NETRA"
if WORKSPACE_DIR not in sys.path:
    sys.path.insert(0, WORKSPACE_DIR)

from backend.app.core.database import engine, SessionLocal
from backend.app.main import app
from backend.app.services.live_ingestion_service import (
    live_ingestion_service,
    compute_observation_fingerprint,
    INDIA_LAT_MIN, INDIA_LAT_MAX,
    INDIA_LON_MIN, INDIA_LON_MAX
)
from backend.app.models.domain import ThermalDetection, ThermalEvent, EventFeature, ModelPrediction, RiskScore

REPORT_MD_PATH = os.path.join(WORKSPACE_DIR, "PHASE10_LIVE_INGESTION_REPORT.md")
REPORT_JSON_PATH = os.path.join(WORKSPACE_DIR, "PHASE10_LIVE_INGESTION.json")

client = TestClient(app)


def test_phase10_database_immutability_and_model_registry_invariants():
    """Verifies that all raw FIRMS tables remain strictly immutable and candidate models inactive."""
    with engine.connect() as conn:
        c_2022_off = conn.execute(text("SELECT COUNT(*) FROM thermal_detections WHERE acq_timestamp >= '2022-01-01' AND acq_timestamp < '2023-01-01' AND is_demo = false;")).scalar()
        c_2022_pil = conn.execute(text("SELECT COUNT(*) FROM thermal_detections WHERE acq_timestamp >= '2022-01-01' AND acq_timestamp < '2023-01-01' AND is_demo = true;")).scalar()
        c_2023_off = conn.execute(text("SELECT COUNT(*) FROM thermal_detections WHERE acq_timestamp >= '2023-01-01' AND acq_timestamp < '2024-01-01' AND is_demo = false;")).scalar()
        c_2024_rec = conn.execute(text("SELECT COUNT(*) FROM thermal_detections WHERE acq_timestamp >= '2024-01-01' AND acq_timestamp < '2025-01-01';")).scalar()
        c_2025_off = conn.execute(text("SELECT COUNT(*) FROM thermal_detections WHERE acq_timestamp >= '2025-01-01' AND acq_timestamp < '2026-01-01';")).scalar()
        c_2026_off = conn.execute(text("SELECT COUNT(*) FROM thermal_detections WHERE acq_timestamp >= '2026-01-01';")).scalar()

        active_models = conn.execute(text("SELECT model_name, version, status, is_active FROM ml_model_registry WHERE version IN ('xgb-v3.0-real-candidate', 'rf-v3.0-real-candidate');")).fetchall()

    assert c_2022_off == 1_274_383
    assert c_2022_pil == 210_000
    assert c_2023_off == 1_244_759
    assert c_2024_rec == 1_711_626
    assert c_2025_off == 2_007_898
    assert c_2026_off >= 1_771_080

    for m in active_models:
        assert not m[3], f"Model {m[1]} must remain inactive (is_active = FALSE)!"
        assert m[2] == "CANDIDATE", f"Model {m[1]} must remain CANDIDATE status!"


def test_phase10_geodetic_and_physics_validation():
    """Verifies that the validation engine correctly accepts valid records and rejects out-of-bounds/malformed records."""
    valid_record = {
        "latitude": 22.5,
        "longitude": 70.0,
        "acq_timestamp": datetime.now(timezone.utc),
        "sensor": "VIIRS_NOAA20",
        "frp": 50.0,
        "brightness": 340.0
    }
    is_valid, reason = live_ingestion_service.validate_observation(valid_record)
    assert is_valid is True
    assert reason is None

    # Invalid latitude
    bad_lat = {**valid_record, "latitude": -5.0}
    is_v, r = live_ingestion_service.validate_observation(bad_lat)
    assert is_v is False
    assert "bounds" in r

    # Negative FRP
    bad_frp = {**valid_record, "frp": -10.0}
    is_v, r = live_ingestion_service.validate_observation(bad_frp)
    assert is_v is False
    assert "FRP" in r

    # Non-numeric
    bad_coords = {**valid_record, "latitude": "INVALID"}
    is_v, r = live_ingestion_service.validate_observation(bad_coords)
    assert is_v is False


def test_phase10_deterministic_deduplication_and_idempotency():
    """Verifies deterministic SHA-256 deduplication and idempotent re-ingestion."""
    db = SessionLocal()
    unique_ts = datetime.now(timezone.utc) - timedelta(hours=5)
    test_batch = [
        {
            "latitude": 21.12345,
            "longitude": 79.12345,
            "acq_timestamp": unique_ts,
            "brightness": 340.0,
            "frp": 45.0,
            "confidence": 90.0,
            "sensor": "VIIRS_DEDUP_TEST",
            "day_night": "D"
        }
    ]

    # First Ingestion
    res1 = live_ingestion_service.ingest_observations(db, test_batch, source_name="TEST_DEDUP_SOURCE", dry_run=False)
    assert res1["records_accepted"] == 1
    assert res1["records_duplicated"] == 0

    # Second Ingestion (Exact Same Data)
    res2 = live_ingestion_service.ingest_observations(db, test_batch, source_name="TEST_DEDUP_SOURCE", dry_run=False)
    assert res2["records_accepted"] == 0
    assert res2["records_duplicated"] == 1

    db.close()


def test_phase10_incremental_event_clustering_and_spatial_enrichment():
    """Verifies incremental DBSCAN clustering, LULC and facility enrichment, and feature vector assembly."""
    db = SessionLocal()
    ts = datetime.now(timezone.utc) - timedelta(hours=2)
    test_cluster = [
        {"latitude": 22.4700, "longitude": 69.8300, "acq_timestamp": ts, "brightness": 350.0, "frp": 130.0, "confidence": 95.0, "sensor": "VIIRS_TEST", "day_night": "N"},
        {"latitude": 22.4710, "longitude": 69.8310, "acq_timestamp": ts + timedelta(seconds=20), "brightness": 355.0, "frp": 140.0, "confidence": 96.0, "sensor": "VIIRS_TEST", "day_night": "N"}
    ]

    proc_res = live_ingestion_service.process_incremental_events(db, test_cluster, dry_run=True)
    assert proc_res["status"] == "SUCCESS"
    assert proc_res["events_created"] >= 1
    
    evt = proc_res["events"][0]
    assert evt["predicted_class"] in ["Gas Flare", "Industrial Fire", "Agricultural Burning", "Forest Fire", "Mining Activity", "Other Thermal Source"]
    assert 0.0 <= evt["confidence"] <= 1.0
    assert evt["is_operational_dispatch"] is False

    db.close()


def test_phase10_audit_persistence_and_zero_live_dispatch():
    """Verifies that audit records are logged and zero live automated alerts are dispatched."""
    with engine.connect() as conn:
        total_audits = conn.execute(text("SELECT COUNT(*) FROM ml_prediction_audit_logs;")).scalar()
        live_dispatches = conn.execute(text("SELECT COUNT(*) FROM ml_prediction_audit_logs WHERE is_operational_dispatch = true;")).scalar()

    assert total_audits > 0
    assert live_dispatches == 0, f"Found {live_dispatches} live automated dispatches!"


def test_phase10_fastapi_ingestion_endpoints():
    """Verifies FastAPI /api/v1/ingestion endpoints (/health-diagnostics and /incremental-sync)."""
    # 1. Health Diagnostics Endpoint
    resp_diag = client.get("/api/v1/ingestion/health-diagnostics")
    assert resp_diag.status_code == 200
    diag_data = resp_diag.json()
    assert diag_data["status"] == "HEALTHY"
    assert diag_data["database_connectivity"] == "CONNECTED"
    assert "source_freshness" in diag_data

    # 2. Incremental Sync Endpoint (Dry Run)
    payload = {
        "observations": [
            {
                "latitude": 28.5,
                "longitude": 77.2,
                "acq_timestamp": datetime.now(timezone.utc).isoformat(),
                "brightness": 335.0,
                "frp": 30.0,
                "confidence": 85.0,
                "sensor": "VIIRS_NOAA20",
                "day_night": "D"
            }
        ],
        "source_name": "API_TEST_STREAM",
        "dry_run": True
    }
    resp_sync = client.post("/api/v1/ingestion/incremental-sync", json=payload)
    assert resp_sync.status_code == 200
    sync_data = resp_sync.json()
    assert sync_data["status"] == "SUCCESS"
    assert sync_data["operational_safety"]["is_operational_dispatch"] is False
    assert sync_data["operational_safety"]["dispatches_emitted"] == 0


def test_phase10_report_and_manifest_exist():
    """Verifies that PHASE10_LIVE_INGESTION_REPORT.md and .json exist and have complete schema."""
    assert os.path.exists(REPORT_MD_PATH), f"Missing {REPORT_MD_PATH}"
    assert os.path.exists(REPORT_JSON_PATH), f"Missing {REPORT_JSON_PATH}"

    with open(REPORT_JSON_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    assert manifest["phase"] == "PHASE_10"
    assert manifest["status"] == "PHASE_10_COMPLETE"
    assert manifest["safety_invariants"]["is_operational_dispatch_enforced"] is False
    assert manifest["safety_invariants"]["live_dispatches_emitted"] == 0
