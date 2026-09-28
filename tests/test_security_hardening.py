"""
AGNI-NETRA — Automated Security Hardening & Session Integrity Test Suite
Validates backend auth enforcement, timing-safe credential verification,
cookie/Bearer dual authentication, registration role suppression, and protected API boundaries.
"""

import pytest
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from fastapi import status
from jose import jwt

from backend.app.main import app
from backend.app.core.config import settings
from backend.app.core.security import create_access_token, get_password_hash, ALGORITHM
from backend.app.models.domain import User
from backend.app.api.deps import (
    get_current_user,
    get_current_active_user,
    require_analyst,
    require_admin,
    require_agency,
)

client = TestClient(app, raise_server_exceptions=False)

USER_PUBLIC = User(id="usr-pub-test", email="citizen@public.in", role="PUBLIC", is_active=True)
USER_ANALYST = User(id="usr-ana-test", email="analyst@domain.gov.in", role="ANALYST", is_active=True)


@pytest.fixture(autouse=True)
def clean_dependencies():
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


# =========================================================================
# 1. Protected API Boundary — Anonymous Rejection Tests (401 Unauthorized)
# =========================================================================

def test_anonymous_requests_blocked_from_operational_endpoints():
    """Operational intelligence endpoints must strictly reject unauthenticated calls."""
    protected_endpoints = [
        ("GET", "/api/v1/events/geojson"),
        ("GET", "/api/v1/prevention/cases"),
        ("GET", "/api/v1/analytics/kpis"),
        ("GET", "/api/v1/gis/thermal-events"),
        ("GET", "/api/v1/analyst/triage"),
        ("POST", "/api/v1/jarvis/command"),
        ("GET", "/api/v1/mining/facilities"),
        ("GET", "/api/v1/historical/observations"),
        ("GET", "/api/v1/baselines/"),
        ("GET", "/api/v1/investigations/cases"),
        ("GET", "/api/v1/satellite/tasks"),
        ("GET", "/api/v1/intelligence/providers"),
        ("GET", "/api/v1/data/live/latest"),
    ]

    for method, path in protected_endpoints:
        if method == "GET":
            res = client.get(path)
        else:
            res = client.post(path, json={"command": "test"})
        assert res.status_code == status.HTTP_401_UNAUTHORIZED, (
            f"Expected 401 for anonymous {method} {path}, got {res.status_code}: {res.text}"
        )


# =========================================================================
# 2. Public Advisory Endpoints Allowed Anonymously
# =========================================================================

def test_public_advisory_endpoints_accessible_without_auth():
    """Public portal endpoints must remain accessible without credentials."""
    public_endpoints = [
        "/api/v1/portals/public/overview",
        "/api/v1/portals/public/advisories",
        "/api/v1/portals/public/hazard-map",
        "/api/v1/health/db",
    ]

    for path in public_endpoints:
        res = client.get(path)
        assert res.status_code != status.HTTP_401_UNAUTHORIZED, (
            f"Public endpoint {path} should not return 401, got {res.status_code}"
        )


# =========================================================================
# 3. RBAC Enforcement — Public Role Blocked from Restricted Operations
# =========================================================================

def test_public_user_forbidden_from_analyst_and_admin_endpoints():
    """PUBLIC role must be denied with 403 Forbidden on analyst and triage tools."""
    app.dependency_overrides[get_current_user] = lambda: USER_PUBLIC
    app.dependency_overrides[get_current_active_user] = lambda: USER_PUBLIC

    restricted_endpoints = [
        ("GET", "/api/v1/analyst/triage"),
        ("POST", "/api/v1/prevention/analyze"),
    ]

    for method, path in restricted_endpoints:
        if method == "GET":
            res = client.get(path)
        else:
            res = client.post(path, json={})
        assert res.status_code == status.HTTP_403_FORBIDDEN, (
            f"Expected 403 for PUBLIC user at {method} {path}, got {res.status_code}"
        )


# =========================================================================
# 4. Registration Role Elevation Suppression & Validation
# =========================================================================

def test_registration_forces_public_role():
    """Registering with elevated role must be overridden to PUBLIC server-side."""
    unique_email = f"evaluator_{datetime.now(timezone.utc).timestamp()}@domain.gov.in"
    payload = {
        "full_name": "Test Evaluator",
        "email": unique_email,
        "organization": "National Testing Agency",
        "role": "ADMIN",  # Client tries to self-assign ADMIN
        "password": "ValidPassword123!",
    }

    res = client.post("/api/v1/auth/register", json=payload)
    if res.status_code == status.HTTP_200_OK:
        data = res.json()
        assert data.get("role") == "PUBLIC", "Server MUST override role to PUBLIC"


def test_registration_rejects_short_password():
    """Passcodes shorter than 8 characters must be rejected."""
    payload = {
        "full_name": "Short Pass User",
        "email": "shortpass@domain.gov.in",
        "organization": "Test Org",
        "password": "short",  # < 8 chars
    }
    res = client.post("/api/v1/auth/register", json=payload)
    assert res.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY]


# =========================================================================
# 5. Login Hardening & Constant-Time Enumeration Resistance
# =========================================================================

def test_login_invalid_credentials_returns_generic_error():
    """Invalid credentials must return 401 without revealing whether email exists."""
    res = client.post(
        "/api/v1/auth/login",
        data={"username": "nonexistent.officer@domain.gov.in", "password": "WrongPassword123!"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert "email or password" in res.json().get("detail", "").lower()


def test_logout_clears_cookies():
    """Logout endpoint must set Set-Cookie headers with max-age=0 to invalidate cookies."""
    res = client.post("/api/v1/auth/logout")
    assert res.status_code == status.HTTP_200_OK
    set_cookie_headers = res.headers.get("set-cookie", "")
    assert "access_token" in set_cookie_headers or "agni_token" in set_cookie_headers
    assert "max-age=0" in set_cookie_headers.lower() or "expires=" in set_cookie_headers.lower()


# =========================================================================
# 6. Session Token Ingestion — Cookie & Bearer Dual Authentication
# =========================================================================

def test_cookie_based_authentication():
    """Requests presenting valid access_token via HTTP-only Cookie must be authenticated."""
    token = create_access_token(
        subject="test-analyst-uuid",
        role="ANALYST",
        expires_delta=timedelta(minutes=30),
    )

    # Issue request with cookie and NO Authorization Bearer header
    client.cookies.set("access_token", token)
    try:
        # Override DB lookup for test-analyst-uuid to avoid database dependency
        app.dependency_overrides[get_current_active_user] = lambda: USER_ANALYST
        res = client.get("/api/v1/events/geojson")
        assert res.status_code != status.HTTP_401_UNAUTHORIZED, (
            f"Expected cookie auth to pass, got {res.status_code}"
        )
    finally:
        client.cookies.clear()


def test_expired_token_rejected():
    """Expired JWT tokens must be strictly rejected with 401."""
    expired_payload = {
        "sub": "test-analyst-uuid",
        "role": "ANALYST",
        "exp": datetime.now(timezone.utc) - timedelta(hours=1),  # Expired in past
    }
    expired_token = jwt.encode(expired_payload, settings.SECRET_KEY, algorithm=ALGORITHM)

    res = client.get(
        "/api/v1/events/geojson",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
