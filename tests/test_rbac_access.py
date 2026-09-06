"""
AGNI-NETRA — Automated RBAC Security & Portal Access Test Suite
Validates role-based access control, coordinate privacy blurring, and model governance invariants.
"""

import pytest
from fastapi.testclient import TestClient
from fastapi import HTTPException, status
from backend.app.main import app
from backend.app.api.deps import (
    get_current_user,
    get_current_active_user,
    require_admin,
    require_analyst,
    require_agency,
    require_researcher,
    require_industry,
)
from backend.app.models.domain import User
from backend.app.core.config import settings

client = TestClient(app, raise_server_exceptions=False)

# Mock user instances for role testing
USER_ADMIN = User(id="usr-adm-001", email="admin@agninetra.gov.in", role="ADMIN", is_active=True)
USER_ANALYST = User(id="usr-ana-001", email="analyst@agninetra.gov.in", role="ANALYST", is_active=True)
USER_AGENCY = User(id="usr-age-001", email="agency@agninetra.gov.in", role="AGENCY", is_active=True)
USER_PUBLIC = User(id="usr-pub-001", email="citizen@public.in", role="PUBLIC", is_active=True)
USER_INACTIVE = User(id="usr-inact-001", email="inactive@agninetra.gov.in", role="ANALYST", is_active=False)


# =========================================================================
# 1. Dependency Role Checker Unit Tests
# =========================================================================

def test_require_admin_permissions():
    assert require_admin(USER_ADMIN) == USER_ADMIN

    for user in [USER_ANALYST, USER_AGENCY, USER_PUBLIC]:
        with pytest.raises(HTTPException) as exc:
            require_admin(user)
        assert exc.value.status_code == status.HTTP_403_FORBIDDEN


def test_require_analyst_permissions():
    assert require_analyst(USER_ADMIN) == USER_ADMIN
    assert require_analyst(USER_ANALYST) == USER_ANALYST

    for user in [USER_AGENCY, USER_PUBLIC]:
        with pytest.raises(HTTPException) as exc:
            require_analyst(user)
        assert exc.value.status_code == status.HTTP_403_FORBIDDEN


def test_require_agency_permissions():
    assert require_agency(USER_ADMIN) == USER_ADMIN
    assert require_agency(USER_ANALYST) == USER_ANALYST
    assert require_agency(USER_AGENCY) == USER_AGENCY

    with pytest.raises(HTTPException) as exc:
        require_agency(USER_PUBLIC)
    assert exc.value.status_code == status.HTTP_403_FORBIDDEN


# =========================================================================
# 2. Endpoint Protection Matrix (Anonymous vs Public vs Agency vs Analyst vs Admin)
# =========================================================================

def test_unauthenticated_requests_blocked_from_internal_endpoints():
    """Unauthenticated users receive 401 on protected endpoints."""
    app.dependency_overrides.clear()

    protected_urls = [
        "/api/v1/events",
        "/api/v1/alerts",
        "/api/v1/facilities",
        "/api/v1/candidates",
        "/api/v1/verification/queue",
        "/api/v1/ml/model-info",
        "/api/v1/admin/model-monitoring",
        "/api/v1/admin/system-stats",
    ]

    for url in protected_urls:
        response = client.get(url)
        assert response.status_code in [401, 403], f"Expected 401/403 for unauthenticated GET {url}, got {response.status_code}"


def test_public_user_blocked_from_internal_intelligence():
    """PUBLIC role receives 403 on internal intelligence endpoints."""
    app.dependency_overrides[get_current_user] = lambda: USER_PUBLIC
    app.dependency_overrides[get_current_active_user] = lambda: USER_PUBLIC

    try:
        forbidden_urls = [
            "/api/v1/events",
            "/api/v1/alerts",
            "/api/v1/facilities",
            "/api/v1/candidates",
            "/api/v1/verification/queue",
            "/api/v1/ml/model-info",
            "/api/v1/admin/model-monitoring",
            "/api/v1/admin/system-stats",
            "/api/v1/admin/users",
        ]

        for url in forbidden_urls:
            response = client.get(url)
            assert response.status_code == 403, f"Expected 403 for PUBLIC on {url}, got {response.status_code}"
    finally:
        app.dependency_overrides.clear()


def test_agency_user_permitted_on_operational_blocked_from_analytical_and_admin():
    """AGENCY role can view alerts and events, but cannot access facilities, candidates, ML registry, or admin."""
    app.dependency_overrides[get_current_user] = lambda: USER_AGENCY
    app.dependency_overrides[get_current_active_user] = lambda: USER_AGENCY

    try:
        # Permitted operational endpoints
        r_events = client.get("/api/v1/events?limit=5")
        assert r_events.status_code == 200, f"AGENCY should access /events, got {r_events.status_code}"

        r_alerts = client.get("/api/v1/alerts?limit=5")
        assert r_alerts.status_code == 200, f"AGENCY should access /alerts, got {r_alerts.status_code}"

        # Blocked analytical endpoints
        forbidden_urls = [
            "/api/v1/facilities",
            "/api/v1/candidates",
            "/api/v1/verification/queue",
            "/api/v1/ml/model-info",
            "/api/v1/admin/model-monitoring",
            "/api/v1/admin/system-stats",
            "/api/v1/admin/users",
        ]
        for url in forbidden_urls:
            response = client.get(url)
            assert response.status_code == 403, f"Expected 403 for AGENCY on {url}, got {response.status_code}"
    finally:
        app.dependency_overrides.clear()


def test_analyst_user_permitted_on_analytical_blocked_from_admin():
    """ANALYST role can access analytical workstations and facilities, but is blocked from admin."""
    app.dependency_overrides[get_current_user] = lambda: USER_ANALYST
    app.dependency_overrides[get_current_active_user] = lambda: USER_ANALYST

    try:
        # Permitted analytical endpoints
        r_events = client.get("/api/v1/events?limit=5")
        assert r_events.status_code == 200

        r_facilities = client.get("/api/v1/facilities?limit=5")
        assert r_facilities.status_code == 200

        r_candidates = client.get("/api/v1/candidates?limit=5")
        assert r_candidates.status_code == 200

        r_ml = client.get("/api/v1/ml/model-info")
        assert r_ml.status_code == 200

        # Blocked admin endpoints
        r_admin_audit = client.get("/api/v1/admin/model-monitoring")
        assert r_admin_audit.status_code == 403

        r_admin_stats = client.get("/api/v1/admin/system-stats")
        assert r_admin_stats.status_code == 403

        r_admin_users = client.get("/api/v1/admin/users")
        assert r_admin_users.status_code == 403
    finally:
        app.dependency_overrides.clear()


def test_admin_user_has_universal_access():
    """ADMIN role has access across analytical, operational, and system admin endpoints."""
    app.dependency_overrides[get_current_user] = lambda: USER_ADMIN
    app.dependency_overrides[get_current_active_user] = lambda: USER_ADMIN

    try:
        urls = [
            "/api/v1/events?limit=5",
            "/api/v1/alerts?limit=5",
            "/api/v1/facilities?limit=5",
            "/api/v1/candidates?limit=5",
            "/api/v1/ml/model-info",
            "/api/v1/admin/model-monitoring",
            "/api/v1/admin/system-stats",
        ]
        for url in urls:
            response = client.get(url)
            assert response.status_code == 200, f"ADMIN should access {url}, got {response.status_code}"
    finally:
        app.dependency_overrides.clear()


# =========================================================================
# 3. Public Hazard Map Endpoint & Privacy Blurring
# =========================================================================

def test_public_hazard_map_accessible_without_auth_and_privacy_blurred():
    """Public hazard map is accessible to all, with coordinates rounded to ~1.1km and sensitive fields stripped."""
    app.dependency_overrides.clear()

    response = client.get("/api/v1/portals/public/hazard-map?limit=20")
    assert response.status_code == 200
    data = response.json()

    assert "features" in data
    assert "events" in data
    assert data["type"] == "FeatureCollection"

    events = data["events"]
    for h in events:
        # Coordinates must be rounded to 2 decimal places
        lat_str = str(h["latitude"]).split(".")
        lon_str = str(h["longitude"]).split(".")
        if len(lat_str) > 1:
            assert len(lat_str[1]) <= 2, f"Latitude {h['latitude']} exceeds 2 decimal places"
        if len(lon_str) > 1:
            assert len(lon_str[1]) <= 2, f"Longitude {h['longitude']} exceeds 2 decimal places"

        # Check absence of sensitive internal attributes
        assert "features_vector" not in h
        assert "shap_values" not in h
        assert "internal_facility_id" not in h
        assert "owner_contact" not in h


# =========================================================================
# 4. Truthful System Invariants
# =========================================================================

def test_dispatch_gate_permanently_disabled():
    """Operational dispatch gate invariant: must remain False."""
    assert settings.ENABLE_OPERATIONAL_DISPATCH_GATE is False


def test_admin_model_monitoring_data_integrity():
    """Admin model monitoring endpoint returns authentic Phase 8 calibration and drift data."""
    app.dependency_overrides[get_current_user] = lambda: USER_ADMIN
    app.dependency_overrides[get_current_active_user] = lambda: USER_ADMIN

    try:
        response = client.get("/api/v1/admin/model-monitoring")
        assert response.status_code == 200
        data = response.json()

        assert "feature_drift" in data
        assert "calibration_metrics" in data
        assert data["feature_drift"]["status"] == "AVAILABLE"
        assert data["calibration_metrics"]["status"] == "AVAILABLE"

        # Verify key authentic metrics
        assert "mathematical_audit" in data["feature_drift"]
        assert "xgboost_raw" in data["calibration_metrics"]
        assert "xgboost_calibrated" in data["calibration_metrics"]
        assert data["model_invariants"]["classifier_state"] == "CANDIDATE / INACTIVE"
    finally:
        app.dependency_overrides.clear()
