"""
AGNI-NETRA — PHASE 11 TEST SUITE
Comprehensive test suite for Operational Alert Generation, Analyst Investigation,
Verification, and Decision Workflow.

Verifies:
1. Historical raw FIRMS observation tables remain 100% immutable (8,221,554 rows).
2. Model registry lineage invariants (xgb-v3.0-real-candidate is CANDIDATE / is_active = FALSE).
3. Automatic alert creation and Tri-Tier routing from newly processed events.
4. Deterministic duplicate-alert suppression and idempotency.
5. Lifecycle state machine transitions (NEW -> ACKNOWLEDGED -> UNDER_INVESTIGATION -> VERIFIED / ESCALATED / DISMISSED -> CLOSED).
6. Invalid state transition rejection and guard enforcement.
7. Investigation evidence dossier aggregation (FIRMS telemetry, facilities, LULC, mining, admin, forests, SHAP).
8. Audit log persistence in `alert_audit_logs` and 100% dispatch suppression.
9. FastAPI operational alert endpoints (dossier, acknowledge, investigate, verify, escalate, dismiss, close, audit trail).
10. Existence and schema validity of Phase 11 report and JSON manifest.
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
from backend.app.models.domain import (
    Alert, ThermalEvent, ThermalDetection, ModelPrediction, RiskScore,
    EventFeature, IndustrialFacility, VerificationRecord
)
from backend.app.services.alert_workflow_service import alert_workflow_service, ensure_alert_schema
from backend.app.services.live_ingestion_service import live_ingestion_service

REPORT_MD_PATH = os.path.join(WORKSPACE_DIR, "PHASE11_ALERT_WORKFLOW_REPORT.md")
REPORT_JSON_PATH = os.path.join(WORKSPACE_DIR, "PHASE11_ALERT_WORKFLOW.json")

client = TestClient(app)


def test_phase11_database_immutability_and_model_invariants():
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
        assert not m[3], f"Model candidate {m[1]} must remain inactive (is_active = FALSE)!"
        assert m[2] == "CANDIDATE", f"Model candidate {m[1]} must remain CANDIDATE status!"


def test_phase11_automatic_alert_creation_and_tier_routing():
    """Verifies automatic alert creation from an operational event and Tri-Tier routing."""
    db = SessionLocal()
    event_id = str(uuid.uuid4())
    event_code = f"EVT-TEST-{event_id[:6].upper()}"

    # Create dummy event and predictions
    evt = ThermalEvent(
        id=event_id,
        event_code=event_code,
        latitude=22.4700,
        longitude=69.8300,
        first_seen=datetime.now(timezone.utc),
        last_seen=datetime.now(timezone.utc),
        detection_count=3,
        avg_frp=120.0,
        max_frp=150.0,
        min_frp=90.0,
        avg_brightness=350.0,
        state="Gujarat",
        district="Jamnagar",
        landcover_class="Industrial",
        status="ACTIVE",
        is_demo=False
    )
    pred = ModelPrediction(
        id=str(uuid.uuid4()),
        event_id=event_id,
        predicted_class="Gas Flare",
        confidence=0.92,
        class_probabilities={"Gas Flare": 0.92, "Industrial Fire": 0.05, "Other": 0.03},
        shap_values={"dist_to_facility_m": -0.85, "frp_max": 0.45}
    )
    risk = RiskScore(
        id=str(uuid.uuid4()),
        event_id=event_id,
        risk_score=78.5,
        risk_level="CRITICAL",
        intensity_subscore=35.0,
        exposure_subscore=25.0,
        context_subscore=18.5
    )
    feat = EventFeature(
        id=str(uuid.uuid4()),
        event_id=event_id,
        dist_to_facility_m=120.0,
        persistence_score=0.85,
        recurrence_rate=2.45
    )

    db.add(evt)
    db.add(pred)
    db.add(risk)
    db.add(feat)
    db.commit()

    alert_res = alert_workflow_service.create_or_update_alert_from_event(db, event_id, dry_run=False)
    assert alert_res["status"] == "ALERT_CREATED"
    assert alert_res["routing_tier"] == "TIER_1_AUTO_DISPATCH_CANDIDATE"
    assert alert_res["alert_level"] == "CRITICAL"
    assert alert_res["priority_score"] >= 70.0
    assert alert_res["lifecycle_state"] == "NEW"
    assert alert_res["is_operational_dispatch"] is False

    db.close()


def test_phase11_duplicate_alert_suppression():
    """Verifies that re-running alert creation on an existing event updates the alert without creating duplicates."""
    db = SessionLocal()
    # Query latest alert
    latest_alert = db.query(Alert).order_by(Alert.created_at.desc()).first()
    assert latest_alert is not None

    dup_res = alert_workflow_service.create_or_update_alert_from_event(db, latest_alert.event_id, dry_run=False)
    assert dup_res["status"] == "ALERT_UPDATED"
    assert dup_res["is_duplicate_suppressed"] is True
    assert dup_res["alert_id"] == latest_alert.id

    db.close()


def test_phase11_state_machine_valid_transitions():
    """Verifies complete valid lifecycle state transitions."""
    db = SessionLocal()
    
    # Create fresh alert
    event_id = str(uuid.uuid4())
    evt = ThermalEvent(
        id=event_id,
        event_code=f"EVT-SM-{event_id[:6].upper()}",
        latitude=30.9000,
        longitude=75.8500,
        first_seen=datetime.now(timezone.utc),
        last_seen=datetime.now(timezone.utc),
        detection_count=2,
        state="Punjab",
        district="Ludhiana",
        status="ACTIVE"
    )
    db.add(evt)
    db.commit()

    alert_res = alert_workflow_service.create_or_update_alert_from_event(db, event_id)
    aid = alert_res["alert_id"]

    # 1. NEW -> ACKNOWLEDGED
    r1 = alert_workflow_service.execute_state_action(db, aid, "ACKNOWLEDGE", "ACKNOWLEDGED", notes="Reviewed")
    assert r1["new_state"] == "ACKNOWLEDGED"

    # 2. ACKNOWLEDGED -> UNDER_INVESTIGATION
    r2 = alert_workflow_service.execute_state_action(db, aid, "START_INVESTIGATION", "UNDER_INVESTIGATION", notes="Investigating")
    assert r2["new_state"] == "UNDER_INVESTIGATION"

    # 3. UNDER_INVESTIGATION -> VERIFIED
    r3 = alert_workflow_service.execute_state_action(
        db, aid, "VERIFY", "VERIFIED", notes="Verified",
        ground_truth_class="Agricultural Burning", verification_outcome="CONFIRM_STUBBLE_BURNING"
    )
    assert r3["new_state"] == "VERIFIED"

    # 4. VERIFIED -> CLOSED
    r4 = alert_workflow_service.execute_state_action(db, aid, "CLOSE", "CLOSED", notes="Closed")
    assert r4["new_state"] == "CLOSED"

    db.close()


def test_phase11_state_machine_invalid_transitions():
    """Verifies that illegal transitions are strictly rejected by the state machine."""
    db = SessionLocal()
    
    # Create fresh alert in NEW state
    event_id = str(uuid.uuid4())
    evt = ThermalEvent(
        id=event_id,
        event_code=f"EVT-INV-{event_id[:6].upper()}",
        latitude=21.6500,
        longitude=86.3500,
        first_seen=datetime.now(timezone.utc),
        last_seen=datetime.now(timezone.utc),
        state="Odisha",
        district="Mayurbhanj",
        status="ACTIVE"
    )
    db.add(evt)
    db.commit()

    alert_res = alert_workflow_service.create_or_update_alert_from_event(db, event_id)
    aid = alert_res["alert_id"]

    # Illegal transition: NEW -> CLOSED directly
    with pytest.raises(ValueError, match="Illegal state transition"):
        alert_workflow_service.execute_state_action(db, aid, "CLOSE", "CLOSED")

    # Illegal transition: NEW -> VERIFIED directly
    with pytest.raises(ValueError, match="Illegal state transition"):
        alert_workflow_service.execute_state_action(db, aid, "VERIFY", "VERIFIED")

    db.close()


def test_phase11_investigation_dossier_aggregation():
    """Verifies that the investigation dossier contains comprehensive authentic multi-layer evidence."""
    db = SessionLocal()
    latest_alert = db.query(Alert).order_by(Alert.created_at.desc()).first()
    assert latest_alert is not None

    dossier = alert_workflow_service.get_alert_investigation_dossier(db, latest_alert.id)
    assert "alert_metadata" in dossier
    assert "thermal_event" in dossier
    assert "firms_observations" in dossier
    assert "ml_inference" in dossier
    assert "risk_assessment" in dossier
    assert "evidence_sources" in dossier
    assert "audit_trail" in dossier
    assert dossier["safety_invariants"]["is_operational_dispatch"] is False
    assert dossier["evidence_sources"]["provenance_guarantee"] == "AUTHENTIC_GEO_TELEMETRY_NO_FABRICATION"

    db.close()


def test_phase11_zero_live_dispatch_and_audit_logging():
    """Verifies that live dispatch is 100% disabled across all alerts and audit logs."""
    with engine.connect() as conn:
        dispatched_alerts = conn.execute(text("SELECT COUNT(*) FROM alerts WHERE is_operational_dispatch = true;")).scalar()
        dispatched_audits = conn.execute(text("SELECT COUNT(*) FROM alert_audit_logs WHERE is_operational_dispatch = true;")).scalar()

    assert dispatched_alerts == 0, f"Found {dispatched_alerts} live dispatched alerts!"
    assert dispatched_audits == 0, f"Found {dispatched_audits} live dispatched audit logs!"


def test_phase11_fastapi_alert_endpoints():
    """Verifies FastAPI /api/v1/alerts operational endpoints."""
    # 1. List Alerts
    resp_list = client.get("/api/v1/alerts?sort_by=priority&limit=10")
    assert resp_list.status_code == 200
    list_data = resp_list.json()
    assert "total_alerts" in list_data
    assert len(list_data["alerts"]) > 0

    target_aid = list_data["alerts"][0]["alert_id"]

    # 2. Get Dossier
    resp_dossier = client.get(f"/api/v1/alerts/{target_aid}/dossier")
    assert resp_dossier.status_code == 200
    dossier_data = resp_dossier.json()
    assert dossier_data["alert_metadata"]["alert_id"] == target_aid

    # 3. Get Audit Trail
    resp_trail = client.get(f"/api/v1/alerts/{target_aid}/audit-trail")
    assert resp_trail.status_code == 200
    trail_data = resp_trail.json()
    assert "audit_trail" in trail_data


def test_phase11_report_and_manifest_exist():
    """Verifies that PHASE11_ALERT_WORKFLOW_REPORT.md and .json exist and are well-formed."""
    assert os.path.exists(REPORT_MD_PATH), f"Missing {REPORT_MD_PATH}"
    assert os.path.exists(REPORT_JSON_PATH), f"Missing {REPORT_JSON_PATH}"

    with open(REPORT_JSON_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    assert manifest["phase"] == "PHASE_11"
    assert manifest["status"] == "PHASE_11_COMPLETE"
    assert manifest["safety_invariants"]["is_operational_dispatch_enforced"] is False
    assert manifest["safety_invariants"]["live_dispatches_emitted"] == 0
