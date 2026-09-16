"""
AGNI-NETRA — Phase 25.2 Integration Repair & Cross-System Validation Test Suite

Validates:
1. /api/v1/alerts?event_id={event_id} returns HTTP 200 without SQLite/PostGIS error.
2. /api/v1/alerts without event_id returns HTTP 200 with all operational alerts.
3. /api/v1/events/{id}/buffer-assets supports both UUID and event_code.
4. /api/v1/events/{id}/buffer-assets returns valid GeoJSON coordinates [longitude, latitude].
5. /api/v1/events/{id} and /detections and /trace dual lookup by UUID or event_code.
6. /api/v1/gis/layers catalog includes authentic counts for facilities, mining, power stations, protected areas.
7. JARVIS demonstrative resolution binds selected_event_id from context.
8. /api/v1/reports/event/{id}/download generates valid PDF report.
9. Strict safety invariant gates:
   - ENABLE_OPERATIONAL_DISPATCH_GATE = False
   - ENABLE_AUTOMATED_MODEL_ACTIVATION = False
"""

import pytest
from datetime import datetime, timezone
from sqlalchemy import text
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.database import SessionLocal, haversine_distance_meters
from backend.app.models.domain import ThermalEvent, Alert, User
from backend.app.core.config import settings

client = TestClient(app)


@pytest.fixture(scope="module")
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="module")
def sample_event(db: Session):
    event = db.query(ThermalEvent).first()
    assert event is not None, "At least one thermal event must exist in database"
    return event


@pytest.fixture(scope="module")
def auth_headers():
    login_res = client.post(
        "/api/v1/auth/login",
        data={"username": "admin@agninetra.gov.in", "password": "AgniNetra@2026"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert login_res.status_code == 200, f"Login failed: {login_res.text}"
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# =============================================================================
# 1. Alert Endpoint & Filtering Repair
# =============================================================================

def test_alerts_endpoint_with_event_id(auth_headers, sample_event):
    """
    Verifies /api/v1/alerts?event_id={event_id} returns HTTP 200 and matches the event.
    """
    response = client.get(f"/api/v1/alerts?event_id={sample_event.id}", headers=auth_headers)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    assert "alerts" in data
    assert len(data["alerts"]) >= 1
    for alert in data["alerts"]:
        assert alert["event_id"] == sample_event.id
        assert "alert_id" in alert
        assert "routing_tier" in alert
        assert "priority_score" in alert
        assert alert["is_operational_dispatch"] is False


def test_alerts_endpoint_without_event_id(auth_headers):
    """
    Verifies /api/v1/alerts returns HTTP 200 and lists all alerts across events.
    """
    response = client.get("/api/v1/alerts", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "alerts" in data
    assert data["total_alerts"] >= 80


# =============================================================================
# 2. Buffer Assets Dual Lookup & Spatial Repair
# =============================================================================

def test_buffer_assets_by_uuid(auth_headers, sample_event):
    """
    Verifies /api/v1/events/{id}/buffer-assets returns HTTP 200 with spatial context.
    """
    response = client.get(f"/api/v1/events/{sample_event.id}/buffer-assets?radius_m=5000", headers=auth_headers)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    assert "event_id" in data
    assert data["event_id"] == sample_event.id
    assert "summary" in data
    assert "facilities" in data
    assert "protected_areas" in data
    assert "mining_context" in data

    # Verify GeoJSON coordinates format [lon, lat]
    for fac in data["facilities"]:
        if fac.get("geometry"):
            coords = fac["geometry"]["coordinates"]
            assert len(coords) == 2
            assert -180.0 <= coords[0] <= 180.0  # longitude
            assert -90.0 <= coords[1] <= 90.0   # latitude


def test_buffer_assets_by_event_code(auth_headers, sample_event):
    """
    Verifies /api/v1/events/{event_code}/buffer-assets resolves seamlessly.
    """
    response = client.get(f"/api/v1/events/{sample_event.event_code}/buffer-assets?radius_m=5000", headers=auth_headers)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    assert data["event_id"] == sample_event.id


# =============================================================================
# 3. Dual Identifier Resolution Across All Event Endpoints
# =============================================================================

def test_event_detail_dual_identifier(auth_headers, sample_event):
    res_uuid = client.get(f"/api/v1/events/{sample_event.id}", headers=auth_headers)
    assert res_uuid.status_code == 200
    res_code = client.get(f"/api/v1/events/{sample_event.event_code}", headers=auth_headers)
    assert res_code.status_code == 200
    assert res_uuid.json()["id"] == res_code.json()["id"]


def test_event_detections_dual_identifier(auth_headers, sample_event):
    res_uuid = client.get(f"/api/v1/events/{sample_event.id}/detections", headers=auth_headers)
    assert res_uuid.status_code == 200
    res_code = client.get(f"/api/v1/events/{sample_event.event_code}/detections", headers=auth_headers)
    assert res_code.status_code == 200


def test_event_trace_dual_identifier(auth_headers, sample_event):
    res_uuid = client.get(f"/api/v1/events/{sample_event.id}/trace", headers=auth_headers)
    assert res_uuid.status_code == 200
    res_code = client.get(f"/api/v1/events/{sample_event.event_code}/trace", headers=auth_headers)
    assert res_code.status_code == 200
    assert "stages" in res_uuid.json()


# =============================================================================
# 4. GIS Layers Catalog Count Accuracy
# =============================================================================

def test_gis_layers_catalog():
    """
    Verifies /api/v1/gis/layers catalog returns authentic counts for all 9 layers.
    """
    response = client.get("/api/v1/gis/layers")
    assert response.status_code == 200
    data = response.json()
    assert "layers" in data
    layer_map = {l["id"]: l for l in data["layers"]}

    assert "industrial_facilities" in layer_map
    assert layer_map["industrial_facilities"]["record_count"] >= 20

    assert "power_stations" in layer_map
    assert layer_map["power_stations"]["record_count"] >= 5

    assert "mining" in layer_map
    assert layer_map["mining"]["record_count"] >= 2

    assert "protected_areas" in layer_map
    assert layer_map["protected_areas"]["record_count"] >= 10


# =============================================================================
# 5. JARVIS Demonstrative Binding
# =============================================================================

def test_jarvis_selected_event_context(auth_headers, sample_event):
    """
    Verifies JARVIS resolves 'investigate this event' using selected_event_id context.
    """
    payload = {
        "command": "Investigate this event and summarize risk",
        "context": {
            "selected_event_id": sample_event.id,
            "viewport": {"zoom": 12, "latitude": sample_event.latitude, "longitude": sample_event.longitude}
        }
    }
    response = client.post("/api/v1/jarvis/command", json=payload, headers=auth_headers)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    assert "summary" in data
    assert sample_event.event_code in data["summary"] or sample_event.id in data["summary"]


# =============================================================================
# 6. Report Generation
# =============================================================================

def test_event_pdf_report_download(auth_headers, sample_event):
    """
    Verifies /api/v1/reports/event/{id}/download generates valid PDF.
    """
    response = client.get(f"/api/v1/reports/event/{sample_event.id}/download", headers=auth_headers)
    assert response.status_code == 200
    assert response.headers.get("content-type") == "application/pdf"
    assert len(response.content) > 1000
    assert response.content[:4] == b"%PDF"


# =============================================================================
# 7. Operational Safety Gates Invariant
# =============================================================================

def test_operational_safety_gates():
    """
    CONFIRMS ABSOLUTE SAFETY LOCK:
    - Live automated dispatch is HARD-LOCKED FALSE.
    - Automated model activation is HARD-LOCKED FALSE.
    """
    assert settings.ENABLE_OPERATIONAL_DISPATCH_GATE is False
    assert settings.ENABLE_AUTOMATED_MODEL_ACTIVATION is False
