import os
import sys
import pytest
from fastapi.testclient import TestClient

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.database import SessionLocal
from backend.app.main import app
from backend.app.models.domain import User, ThermalEvent, IndustrialFacility, Alert
from backend.app.core.security import create_access_token

client = TestClient(app)


def test_baseline_grid_cells_endpoint():
    """Verify GET /api/v1/baselines/grid-cells computes industrial cluster cells"""
    resp = client.get("/api/v1/baselines/grid-cells")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 5
    cell = data[0]
    assert "grid_id" in cell
    assert "mean_frp" in cell
    assert "deviation_ratio" in cell
    assert "status" in cell


def test_research_portal_endpoints():
    """Verify research overview and GeoJSON export"""
    # 1. Overview
    resp_ov = client.get("/api/v1/portals/research/overview")
    assert resp_ov.status_code == 200
    ov = resp_ov.json()
    assert ov["feature_dimensions"] == 18
    assert len(ov["classes"]) == 7
    assert "model_architecture" in ov

    # 2. GeoJSON Export
    resp_geo = client.get("/api/v1/portals/research/geojson-export")
    assert resp_geo.status_code == 200
    geo = resp_geo.json()
    assert geo["type"] == "FeatureCollection"
    assert "features" in geo


def test_industry_portal_endpoints():
    """Verify industry plant roster and emission declaration"""
    # 1. Facilities
    resp_fac = client.get("/api/v1/portals/industry/facilities")
    assert resp_fac.status_code == 200
    facs = resp_fac.json()
    assert isinstance(facs, list)

    # 2. Emission Declaration
    resp_decl = client.post("/api/v1/portals/industry/declare-emission", json={
        "facility_name": "Reliance Jamnagar Refinery",
        "facility_type": "PETROCHEMICAL",
        "state": "Gujarat",
        "planned_operation": "Maintenance Flaring",
        "flare_stack_id": "FLARE-01",
        "expected_duration_hours": 6,
        "declarer_contact": "compliance@ril.com",
        "notes": "Pytest automated declaration"
    })
    assert resp_decl.status_code == 200
    res = resp_decl.json()
    assert res["status"] == "APPROVED"
    assert "reference_number" in res


def test_public_portal_advisories():
    """Verify public citizen advisory feed"""
    resp = client.get("/api/v1/portals/public/advisories")
    assert resp.status_code == 200
    data = resp.json()
    assert "national_status" in data
    assert "public_advisories" in data


def test_csv_report_export():
    """Verify CSV export format and headers"""
    resp = client.get("/api/v1/reports/export/csv")
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]
    assert "Event_Code,State" in resp.text


def test_admin_user_management_and_audit():
    """Verify admin role modification, system stats, and health"""
    db = SessionLocal()
    try:
        admin_user = db.query(User).filter(User.role == "ADMIN").first()
        if not admin_user:
            admin_user = db.query(User).first()

        token = create_access_token(subject=str(admin_user.id), role="ADMIN")
        headers = {"Authorization": f"Bearer {token}"}

        # 1. Get users
        resp_u = client.get("/api/v1/admin/users", headers=headers)
        assert resp_u.status_code == 200

        # 2. System Stats
        resp_s = client.get("/api/v1/admin/system-stats", headers=headers)
        assert resp_s.status_code == 200
        stats = resp_s.json()
        assert "events_count" in stats
        assert "facilities_count" in stats

        # 3. System Health
        resp_h = client.get("/api/v1/admin/system-health")
        assert resp_h.status_code == 200
        health = resp_h.json()
        assert health["status"] == "HEALTHY"
    finally:
        db.close()
