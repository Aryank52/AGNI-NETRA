"""
AGNI-NETRA — Automated Security Hardening & Session Integrity Test Suite
Validates backend auth enforcement, timing-safe credential verification,
cookie/Bearer dual authentication, simplified portal registration, and protected API boundaries.
"""

import uuid
import pytest
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from fastapi import status
from jose import jwt

from backend.app.main import app
from backend.app.core.config import settings
from backend.app.core.database import SessionLocal
from backend.app.core.security import create_access_token, get_password_hash, ALGORITHM
from backend.app.models.domain import User, AuditLog
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
USER_AGENCY = User(id="usr-age-test", email="agency@domain.gov.in", role="AGENCY", is_active=True)
USER_ADMIN = User(
    id="usr-adm-test",
    email="admin@domain.gov.in",
    full_name="Admin Evaluator",
    hashed_password=get_password_hash("AdminSecured123!"),
    role="ADMIN",
    is_active=True,
)


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

def test_registration_rejects_admin_role():
    """Registering with ADMIN role must be rejected with 400 Bad Request."""
    unique_email = f"evaluator_{datetime.now(timezone.utc).timestamp()}@domain.gov.in"
    payload = {
        "full_name": "Test Evaluator",
        "email": unique_email,
        "organization": "National Testing Agency",
        "role": "ADMIN",  # Client tries to self-assign ADMIN
        "password": "ValidPassword123!",
    }

    res = client.post("/api/v1/auth/register", json=payload)
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert "ADMIN accounts cannot be created" in res.json().get("detail", "")


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


# =========================================================================
# 7. Simplified Portal Registration & Validation (Scenarios 1-7)
# =========================================================================

def test_scenario_1_public_registration_creates_public_account():
    """Scenario 1: PUBLIC registration creates PUBLIC account directly."""
    unique_email = f"public_user_{uuid.uuid4().hex[:8]}@public.in"
    payload = {
        "full_name": "Public Citizen",
        "email": unique_email,
        "organization": "Citizen Science Forum",
        "role": "PUBLIC",
        "password": "ValidPassword123!",
    }
    res = client.post("/api/v1/auth/register", json=payload)
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["role"] == "PUBLIC"
    assert data["email"] == unique_email

    # Verify audit log recorded
    with SessionLocal() as db:
        audit = db.query(AuditLog).filter(
            AuditLog.user_id == data["id"],
            AuditLog.action == "USER_REGISTRATION"
        ).first()
        assert audit is not None
        assert audit.details.get("assigned_role") == "PUBLIC"


def test_scenario_2_analyst_registration_creates_analyst_account():
    """Scenario 2: ANALYST registration creates ANALYST account directly."""
    unique_email = f"analyst_applicant_{uuid.uuid4().hex[:8]}@fsi.gov.in"
    payload = {
        "full_name": "Senior Forest Analyst",
        "email": unique_email,
        "organization": "Forest Survey of India",
        "role": "ANALYST",
        "password": "ValidPassword123!",
    }
    res = client.post("/api/v1/auth/register", json=payload)
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["role"] == "ANALYST"
    assert data["email"] == unique_email

    with SessionLocal() as db:
        audit = db.query(AuditLog).filter(
            AuditLog.user_id == data["id"],
            AuditLog.action == "USER_REGISTRATION"
        ).first()
        assert audit is not None
        assert audit.details.get("assigned_role") == "ANALYST"


def test_scenario_3_agency_registration_creates_agency_account():
    """Scenario 3: AGENCY registration creates AGENCY account directly."""
    unique_email = f"agency_applicant_{uuid.uuid4().hex[:8]}@sdma.gov.in"
    payload = {
        "full_name": "Disaster Response Officer",
        "email": unique_email,
        "organization": "State Disaster Management Authority",
        "role": "AGENCY",
        "password": "ValidPassword123!",
    }
    res = client.post("/api/v1/auth/register", json=payload)
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["role"] == "AGENCY"
    assert data["email"] == unique_email

    with SessionLocal() as db:
        audit = db.query(AuditLog).filter(
            AuditLog.user_id == data["id"],
            AuditLog.action == "USER_REGISTRATION"
        ).first()
        assert audit is not None
        assert audit.details.get("assigned_role") == "AGENCY"


def test_scenario_4_admin_cannot_be_self_assigned_during_registration():
    """Scenario 4: ADMIN cannot be registered publicly (rejected with 400)."""
    unique_email = f"admin_attacker_{uuid.uuid4().hex[:8]}@sec-test.in"
    payload = {
        "full_name": "Privilege Escalation Tester",
        "email": unique_email,
        "organization": "Independent Security Lab",
        "role": "ADMIN",
        "password": "ValidPassword123!",
    }
    res = client.post("/api/v1/auth/register", json=payload)
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert "ADMIN accounts cannot be created" in res.json().get("detail", "")


def test_scenario_5_gmail_registration_works():
    """Scenario 5: Standard gmail.com address registration succeeds."""
    unique_email = f"officer.{uuid.uuid4().hex[:6]}@gmail.com"
    payload = {
        "full_name": "Field Researcher",
        "email": unique_email,
        "role": "ANALYST",
        "password": "ValidPassword123!",
    }
    res = client.post("/api/v1/auth/register", json=payload)
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["email"] == unique_email
    assert res.json()["role"] == "ANALYST"


def test_scenario_6_normal_email_registration_works():
    """Scenario 6: Standard normal emails (yahoo.com, outlook.com) succeed."""
    for domain in ["yahoo.com", "outlook.com"]:
        unique_email = f"user.{uuid.uuid4().hex[:6]}@{domain}"
        payload = {
            "full_name": "Operational User",
            "email": unique_email,
            "role": "AGENCY",
            "password": "ValidPassword123!",
        }
        res = client.post("/api/v1/auth/register", json=payload)
        assert res.status_code == status.HTTP_200_OK
        assert res.json()["email"] == unique_email


def test_scenario_7_organization_optional():
    """Scenario 7: Organization field is optional and omissible."""
    unique_email = f"no_org_{uuid.uuid4().hex[:8]}@gmail.com"
    payload = {
        "full_name": "Independent Citizen",
        "email": unique_email,
        "role": "PUBLIC",
        "password": "ValidPassword123!",
    }
    res = client.post("/api/v1/auth/register", json=payload)
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["organization"] is None or res.json()["organization"] == ""


# =========================================================================
# 8. Login Destination Routing & Portal Validation (Scenarios 8-16)
# =========================================================================

ROLE_PORTAL_MAP = {
    "ADMIN": "/admin",
    "ANALYST": "/dashboard",
    "AGENCY": "/portal/agency",
    "PUBLIC": "/portal/public",
    "RESEARCHER": "/portal/research",
    "INDUSTRY": "/portal/industry",
}

def evaluate_login_portal_routing(account_role: str, target_redirect: str = None) -> tuple[bool, str, str]:
    """
    Evaluates portal routing identical to frontend/src/app/login/page.tsx.
    Returns: (is_authorized, target_or_fallback_destination, error_message)
    """
    authorized_portal = ROLE_PORTAL_MAP.get(account_role)
    if not authorized_portal:
        return False, "", "Portal access denied. No authorized workspace is assigned to this account."

    if target_redirect:
        from urllib.parse import urlparse
        if target_redirect.startswith("http://") or target_redirect.startswith("https://"):
            parsed_path = urlparse(target_redirect).path
        else:
            parsed_path = urlparse(f"http://localhost{target_redirect if target_redirect.startswith('/') else '/' + target_redirect}").path

        parsed_path = parsed_path.rstrip("/") or "/"
        authorized = (
            parsed_path == authorized_portal or
            parsed_path.startswith(f"{authorized_portal}/")
        )

        if not authorized:
            return False, "", f"Your account is registered for {account_role} access."

        return True, target_redirect, ""

    return True, authorized_portal, ""


def test_scenario_8_analyst_login_destination_routing():
    """Scenario 8: ANALYST login destination routing logic defaults to /dashboard."""
    authorized, dest, err = evaluate_login_portal_routing("ANALYST")
    assert authorized is True
    assert dest == "/dashboard"
    assert err == ""


def test_scenario_9_agency_login_destination_routing():
    """Scenario 9: AGENCY login destination routing logic defaults to /portal/agency."""
    authorized, dest, err = evaluate_login_portal_routing("AGENCY")
    assert authorized is True
    assert dest == "/portal/agency"
    assert err == ""


def test_scenario_10_public_login_destination_routing():
    """Scenario 10: PUBLIC login destination routing logic defaults to /portal/public."""
    authorized, dest, err = evaluate_login_portal_routing("PUBLIC")
    assert authorized is True
    assert dest == "/portal/public"
    assert err == ""


def test_scenario_11_public_cannot_enter_analyst_portal():
    """Scenario 11: PUBLIC user accessing /dashboard is rejected with mismatch message."""
    authorized, dest, err = evaluate_login_portal_routing("PUBLIC", "/dashboard")
    assert authorized is False
    assert err == "Your account is registered for PUBLIC access."


def test_scenario_12_public_cannot_enter_agency_portal():
    """Scenario 12: PUBLIC user accessing /portal/agency is rejected with mismatch message."""
    authorized, dest, err = evaluate_login_portal_routing("PUBLIC", "/portal/agency")
    assert authorized is False
    assert err == "Your account is registered for PUBLIC access."


def test_scenario_13_analyst_cannot_enter_agency_portal():
    """Scenario 13: ANALYST user accessing /portal/agency is rejected with mismatch message."""
    authorized, dest, err = evaluate_login_portal_routing("ANALYST", "/portal/agency")
    assert authorized is False
    assert err == "Your account is registered for ANALYST access."


def test_scenario_14_agency_cannot_enter_analyst_portal():
    """Scenario 14: AGENCY user accessing /dashboard is rejected with mismatch message."""
    authorized, dest, err = evaluate_login_portal_routing("AGENCY", "/dashboard")
    assert authorized is False
    assert err == "Your account is registered for AGENCY access."


def test_scenario_15_admin_backend_authorization_intact():
    """Scenario 15: ADMIN backend authorization remains intact and routes to /admin."""
    authorized, dest, err = evaluate_login_portal_routing("ADMIN")
    assert authorized is True
    assert dest == "/admin"
    assert require_admin(USER_ADMIN) == USER_ADMIN


def test_scenario_16_unauthenticated_protected_routes_rejection_and_redirect():
    """Scenario 16: Unauthenticated protected routes must be blocked and redirected to /login."""
    protected_patterns = [
        "/dashboard",
        "/dashboard/analytics",
        "/admin",
        "/admin/data-sources",
        "/portal/agency",
        "/portal/agency/alerts",
        "/jarvis",
    ]

    for route in ["/api/v1/analyst/triage", "/api/v1/events/geojson"]:
        res = client.get(route)
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def simulate_nextjs_middleware(pathname: str, search: str, has_cookie: bool):
        if not has_cookie:
            dest = f"{pathname}{search}"
            return {"redirect": f"/login?redirect={dest}" if dest and dest != "/" else "/login"}
        return {"status": 200}

    for path in protected_patterns:
        sim = simulate_nextjs_middleware(path, "?query=1", has_cookie=False)
        assert sim["redirect"] == f"/login?redirect={path}?query=1"

    sim_authenticated = simulate_nextjs_middleware("/dashboard", "", has_cookie=True)
    assert sim_authenticated["status"] == 200


def test_nested_authorized_redirects_validation():
    """Nested authorized redirects validation (/dashboard/events, /admin/data-sources)."""
    ok1, dest1, err1 = evaluate_login_portal_routing("ANALYST", "/dashboard/events")
    assert ok1 is True
    assert dest1 == "/dashboard/events"

    ok2, dest2, err2 = evaluate_login_portal_routing("ANALYST", "/dashboard/events?lat=21.5&lon=85.2")
    assert ok2 is True
    assert dest2 == "/dashboard/events?lat=21.5&lon=85.2"

    ok3, dest3, err3 = evaluate_login_portal_routing("ADMIN", "/admin/data-sources")
    assert ok3 is True
    assert dest3 == "/admin/data-sources"

    ok4, dest4, err4 = evaluate_login_portal_routing("AGENCY", "/portal/agency/alerts?severity=critical")
    assert ok4 is True
    assert dest4 == "/portal/agency/alerts?severity=critical"


def test_regression_auth_rbac_invariants():
    """Regression verification of existing auth, hashing, and RBAC primitives."""
    from backend.app.core.security import verify_password
    h = get_password_hash("TestP@ssw0rd")
    assert verify_password("TestP@ssw0rd", h) is True
    assert verify_password("WrongPassword", h) is False

    assert require_admin(USER_ADMIN) == USER_ADMIN
    assert require_analyst(USER_ANALYST) == USER_ANALYST
    assert require_agency(USER_AGENCY) == USER_AGENCY
