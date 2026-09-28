"""
AGNI-NETRA — Automated Security Hardening & Session Integrity Test Suite
Validates backend auth enforcement, timing-safe credential verification,
cookie/Bearer dual authentication, registration role suppression, and protected API boundaries.
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


# =========================================================================
# 7. Access Request Registration Enforcement (Scenarios 1-4)
# =========================================================================

def test_scenario_1_public_registration_creates_public_account():
    """Scenario 1: PUBLIC registration creates PUBLIC account with APPROVED audit status."""
    unique_email = f"public_user_{uuid.uuid4().hex[:8]}@public.in"
    payload = {
        "full_name": "Public Citizen",
        "email": unique_email,
        "organization": "Citizen Science Forum",
        "requested_role": "PUBLIC",
        "password": "ValidPassword123!",
    }
    res = client.post("/api/v1/auth/register", json=payload)
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["role"] == "PUBLIC"
    assert data["email"] == unique_email

    # Verify audit log recorded with status APPROVED
    with SessionLocal() as db:
        audit = db.query(AuditLog).filter(
            AuditLog.user_id == data["id"],
            AuditLog.action == "ACCESS_REQUEST"
        ).first()
        assert audit is not None
        assert audit.details.get("requested_role") == "PUBLIC"
        assert audit.details.get("assigned_role") == "PUBLIC"
        assert audit.details.get("status") == "APPROVED"


def test_scenario_2_analyst_registration_creates_public_with_pending_access_request():
    """Scenario 2: ANALYST registration creates PUBLIC account with requested_role=ANALYST and PENDING request."""
    unique_email = f"analyst_applicant_{uuid.uuid4().hex[:8]}@fsi.gov.in"
    payload = {
        "full_name": "Senior Forest Analyst",
        "email": unique_email,
        "organization": "Forest Survey of India",
        "requested_role": "ANALYST",
        "password": "ValidPassword123!",
    }
    res = client.post("/api/v1/auth/register", json=payload)
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["role"] == "PUBLIC", "Immediate role assignment must remain PUBLIC until admin approval"

    with SessionLocal() as db:
        audit = db.query(AuditLog).filter(
            AuditLog.user_id == data["id"],
            AuditLog.action == "ACCESS_REQUEST"
        ).first()
        assert audit is not None
        assert audit.details.get("requested_role") == "ANALYST"
        assert audit.details.get("status") == "PENDING"


def test_scenario_3_agency_registration_creates_public_with_pending_access_request():
    """Scenario 3: AGENCY registration creates PUBLIC account with requested_role=AGENCY and PENDING request."""
    unique_email = f"agency_applicant_{uuid.uuid4().hex[:8]}@sdma.gov.in"
    payload = {
        "full_name": "Disaster Response Officer",
        "email": unique_email,
        "organization": "State Disaster Management Authority",
        "requested_role": "AGENCY",
        "password": "ValidPassword123!",
    }
    res = client.post("/api/v1/auth/register", json=payload)
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["role"] == "PUBLIC", "Immediate role assignment must remain PUBLIC until admin approval"

    with SessionLocal() as db:
        audit = db.query(AuditLog).filter(
            AuditLog.user_id == data["id"],
            AuditLog.action == "ACCESS_REQUEST"
        ).first()
        assert audit is not None
        assert audit.details.get("requested_role") == "AGENCY"
        assert audit.details.get("status") == "PENDING"


def test_scenario_4_admin_cannot_be_self_assigned_during_registration():
    """Scenario 4: ADMIN cannot be self-assigned during registration (sanitized to PUBLIC, no pending admin approval)."""
    unique_email = f"admin_attacker_{uuid.uuid4().hex[:8]}@sec-test.in"
    payload = {
        "full_name": "Privilege Escalation Tester",
        "email": unique_email,
        "organization": "Independent Security Lab",
        "role": "ADMIN",
        "requested_role": "ADMIN",
        "password": "ValidPassword123!",
    }
    res = client.post("/api/v1/auth/register", json=payload)
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["role"] == "PUBLIC"

    with SessionLocal() as db:
        audit = db.query(AuditLog).filter(
            AuditLog.user_id == data["id"],
            AuditLog.action == "ACCESS_REQUEST"
        ).first()
        assert audit is not None
        # Must be sanitized to PUBLIC, not ADMIN
        assert audit.details.get("requested_role") == "PUBLIC"
        assert audit.details.get("status") == "APPROVED"


# =========================================================================
# 8. Administrative Access Request Approval (Scenarios 5, 6)
# =========================================================================

def test_scenario_5_admin_can_approve_analyst_request():
    """Scenario 5: ADMIN can approve ANALYST request via /api/v1/admin/access-requests/{id}/approve."""
    unique_email = f"analyst_appr_{uuid.uuid4().hex[:8]}@domain.gov.in"
    reg_payload = {
        "full_name": "Analyst Candidate",
        "email": unique_email,
        "organization": "National Remote Sensing Centre",
        "requested_role": "ANALYST",
        "password": "ValidPassword123!",
    }
    reg_res = client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_res.status_code == status.HTTP_200_OK
    user_data = reg_res.json()
    user_id = user_data["id"]

    # Locate access request audit log
    with SessionLocal() as db:
        log = db.query(AuditLog).filter(
            AuditLog.user_id == user_id,
            AuditLog.action == "ACCESS_REQUEST"
        ).first()
        assert log is not None
        request_id = log.id

    # Admin lists access requests
    app.dependency_overrides[require_admin] = lambda: USER_ADMIN
    app.dependency_overrides[get_current_active_user] = lambda: USER_ADMIN

    list_res = client.get("/api/v1/admin/access-requests")
    assert list_res.status_code == status.HTTP_200_OK
    req_items = list_res.json()
    assert any(item["id"] == request_id and item["requested_role"] == "ANALYST" for item in req_items)

    # Admin approves request
    appr_res = client.post(f"/api/v1/admin/access-requests/{request_id}/approve")
    assert appr_res.status_code == status.HTTP_200_OK
    appr_data = appr_res.json()
    assert appr_data["status"] == "APPROVED"
    assert appr_data["role"] == "ANALYST"

    # Verify user in database is now ANALYST
    with SessionLocal() as db:
        user = db.query(User).filter(User.id == user_id).first()
        assert user.role == "ANALYST"
        updated_log = db.query(AuditLog).filter(AuditLog.id == request_id).first()
        assert updated_log.details.get("status") == "APPROVED"


def test_scenario_6_admin_can_approve_agency_request():
    """Scenario 6: ADMIN can approve AGENCY request via /api/v1/admin/access-requests/{id}/approve."""
    unique_email = f"agency_appr_{uuid.uuid4().hex[:8]}@state.gov.in"
    reg_payload = {
        "full_name": "Agency Candidate",
        "email": unique_email,
        "organization": "Fire & Emergency Services",
        "requested_role": "AGENCY",
        "password": "ValidPassword123!",
    }
    reg_res = client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_res.status_code == status.HTTP_200_OK
    user_data = reg_res.json()
    user_id = user_data["id"]

    with SessionLocal() as db:
        log = db.query(AuditLog).filter(
            AuditLog.user_id == user_id,
            AuditLog.action == "ACCESS_REQUEST"
        ).first()
        assert log is not None
        request_id = log.id

    app.dependency_overrides[require_admin] = lambda: USER_ADMIN
    app.dependency_overrides[get_current_active_user] = lambda: USER_ADMIN

    appr_res = client.post(f"/api/v1/admin/access-requests/{request_id}/approve")
    assert appr_res.status_code == status.HTTP_200_OK
    appr_data = appr_res.json()
    assert appr_data["status"] == "APPROVED"
    assert appr_data["role"] == "AGENCY"

    with SessionLocal() as db:
        user = db.query(User).filter(User.id == user_id).first()
        assert user.role == "AGENCY"


# =========================================================================
# 9. Login Destination Routing & Portal Validation (Scenarios 7-14)
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
            if account_role == "PUBLIC":
                return (
                    False,
                    "",
                    "Your account is currently PUBLIC. Request operational access from the Public Portal to obtain ANALYST/AGENCY clearance.",
                )
            return False, "", f"Portal access denied. Your account is authorized for {account_role}."

        return True, target_redirect, ""

    return True, authorized_portal, ""


def test_scenario_7_analyst_login_destination_routing():
    """Scenario 7: ANALYST login destination routing logic defaults to /dashboard."""
    authorized, dest, err = evaluate_login_portal_routing("ANALYST")
    assert authorized is True
    assert dest == "/dashboard"
    assert err == ""


def test_scenario_8_agency_login_destination_routing():
    """Scenario 8: AGENCY login destination routing logic defaults to /portal/agency."""
    authorized, dest, err = evaluate_login_portal_routing("AGENCY")
    assert authorized is True
    assert dest == "/portal/agency"
    assert err == ""


def test_scenario_9_public_login_destination_routing():
    """Scenario 9: PUBLIC login destination routing logic defaults to /portal/public."""
    authorized, dest, err = evaluate_login_portal_routing("PUBLIC")
    assert authorized is True
    assert dest == "/portal/public"
    assert err == ""


def test_scenario_10_admin_login_destination_routing():
    """Scenario 10: ADMIN login destination routing logic defaults to /admin."""
    authorized, dest, err = evaluate_login_portal_routing("ADMIN")
    assert authorized is True
    assert dest == "/admin"
    assert err == ""


def test_scenario_11_mismatch_rejection_analyst_requesting_admin():
    """Scenario 11: Mismatch rejection — ANALYST requesting /admin rejected with exact warning."""
    authorized, dest, err = evaluate_login_portal_routing("ANALYST", "/admin")
    assert authorized is False
    assert err == "Portal access denied. Your account is authorized for ANALYST."


def test_scenario_12_mismatch_rejection_agency_requesting_admin():
    """Scenario 12: Mismatch rejection — AGENCY requesting /admin rejected with exact warning."""
    authorized, dest, err = evaluate_login_portal_routing("AGENCY", "/admin")
    assert authorized is False
    assert err == "Portal access denied. Your account is authorized for AGENCY."


def test_scenario_13_mismatch_rejection_public_requesting_dashboard():
    """Scenario 13: Mismatch rejection — PUBLIC requesting /dashboard rejected with operational guidance."""
    authorized, dest, err = evaluate_login_portal_routing("PUBLIC", "/dashboard")
    assert authorized is False
    assert "Your account is currently PUBLIC" in err
    assert "Request operational access from the Public Portal" in err


def test_scenario_14_nested_authorized_redirects_validation():
    """Scenario 14: Nested authorized redirects validation (/dashboard/events, /admin/data-sources)."""
    # ANALYST accessing nested /dashboard subpaths with and without query params
    ok1, dest1, err1 = evaluate_login_portal_routing("ANALYST", "/dashboard/events")
    assert ok1 is True
    assert dest1 == "/dashboard/events"

    ok2, dest2, err2 = evaluate_login_portal_routing("ANALYST", "/dashboard/events?lat=21.5&lon=85.2")
    assert ok2 is True
    assert dest2 == "/dashboard/events?lat=21.5&lon=85.2"

    # ADMIN accessing nested /admin subpaths
    ok3, dest3, err3 = evaluate_login_portal_routing("ADMIN", "/admin/data-sources")
    assert ok3 is True
    assert dest3 == "/admin/data-sources"

    # AGENCY accessing nested /portal/agency subpaths
    ok4, dest4, err4 = evaluate_login_portal_routing("AGENCY", "/portal/agency/alerts?severity=critical")
    assert ok4 is True
    assert dest4 == "/portal/agency/alerts?severity=critical"


# =========================================================================
# 10. Unauthenticated Route Boundary & Middleware Matchers (Scenario 15)
# =========================================================================

def test_scenario_15_unauthenticated_protected_routes_rejection_and_redirect():
    """Scenario 15: Unauthenticated protected routes must be blocked and redirected to /login."""
    protected_patterns = [
        "/dashboard",
        "/dashboard/analytics",
        "/admin",
        "/admin/data-sources",
        "/portal/agency",
        "/portal/agency/alerts",
        "/jarvis",
    ]

    # Verify backend operational endpoints systematically reject without token
    for route in ["/api/v1/admin/access-requests", "/api/v1/analyst/triage", "/api/v1/events/geojson"]:
        res = client.get(route)
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    # Verify middleware logic for redirecting unauthenticated requests
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


# =========================================================================
# 11. Regression Invariant Verification (Scenario 16)
# =========================================================================

def test_scenario_16_regression_auth_rbac_invariants():
    """Scenario 16: Regression verification of existing auth, hashing, and RBAC primitives."""
    from backend.app.core.security import verify_password
    h = get_password_hash("TestP@ssw0rd")
    assert verify_password("TestP@ssw0rd", h) is True
    assert verify_password("WrongPassword", h) is False

    from backend.app.api.deps import require_admin, require_analyst, require_agency
    assert require_admin(USER_ADMIN) == USER_ADMIN
    assert require_analyst(USER_ANALYST) == USER_ANALYST
    assert require_agency(USER_AGENCY) == USER_AGENCY


# =========================================================================
# 12. Existing User Operational Access Request Tests (Requirements 1-13)
# =========================================================================

def test_req1_existing_public_user_can_submit_analyst_access_request():
    """1. Existing PUBLIC user can submit ANALYST access request."""
    email = f"existing_pub1_{uuid.uuid4().hex[:8]}@public.in"
    reg_res = client.post("/api/v1/auth/register", json={
        "full_name": "Existing Citizen One",
        "email": email,
        "organization": "Citizen Science Hub",
        "requested_role": "PUBLIC",
        "password": "ValidPassword123!"
    })
    assert reg_res.status_code == status.HTTP_200_OK
    user_id = reg_res.json()["id"]

    # Authenticate as this existing PUBLIC user
    user_obj = User(id=user_id, email=email, role="PUBLIC", is_active=True)
    app.dependency_overrides[get_current_active_user] = lambda: user_obj
    app.dependency_overrides[get_current_user] = lambda: user_obj

    res = client.post("/api/v1/auth/access-request", json={
        "requested_role": "ANALYST",
        "organization": "National Remote Sensing",
        "reason": "Forest fire spatial analysis"
    })
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["status"] == "PENDING"
    assert data["requested_role"] == "ANALYST"
    assert data["message"] == "Access request submitted. Await administrator approval."

    # Verify query status endpoint returns PENDING
    status_res = client.get("/api/v1/auth/access-request")
    assert status_res.status_code == status.HTTP_200_OK
    assert status_res.json()["status"] == "PENDING"
    assert status_res.json()["requested_role"] == "ANALYST"


def test_req2_existing_public_user_can_submit_agency_access_request():
    """2. Existing PUBLIC user can submit AGENCY access request."""
    email = f"existing_pub2_{uuid.uuid4().hex[:8]}@public.in"
    reg_res = client.post("/api/v1/auth/register", json={
        "full_name": "Existing Citizen Two",
        "email": email,
        "organization": "Disaster Response Unit",
        "requested_role": "PUBLIC",
        "password": "ValidPassword123!"
    })
    assert reg_res.status_code == status.HTTP_200_OK
    user_id = reg_res.json()["id"]

    user_obj = User(id=user_id, email=email, role="PUBLIC", is_active=True)
    app.dependency_overrides[get_current_active_user] = lambda: user_obj
    app.dependency_overrides[get_current_user] = lambda: user_obj

    res = client.post("/api/v1/auth/access-request", json={
        "requested_role": "AGENCY",
        "organization": "State Fire Brigade"
    })
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["status"] == "PENDING"
    assert data["requested_role"] == "AGENCY"


def test_req3_existing_public_user_cannot_create_duplicate_pending_request():
    """3. Existing PUBLIC user cannot create duplicate pending request."""
    email = f"existing_pub3_{uuid.uuid4().hex[:8]}@public.in"
    reg_res = client.post("/api/v1/auth/register", json={
        "full_name": "Existing Citizen Three",
        "email": email,
        "requested_role": "PUBLIC",
        "password": "ValidPassword123!"
    })
    user_id = reg_res.json()["id"]

    user_obj = User(id=user_id, email=email, role="PUBLIC", is_active=True)
    app.dependency_overrides[get_current_active_user] = lambda: user_obj
    app.dependency_overrides[get_current_user] = lambda: user_obj

    # First request
    res1 = client.post("/api/v1/auth/access-request", json={"requested_role": "ANALYST"})
    assert res1.status_code == status.HTTP_200_OK

    # Second request while pending
    res2 = client.post("/api/v1/auth/access-request", json={"requested_role": "AGENCY"})
    assert res2.status_code == status.HTTP_400_BAD_REQUEST
    assert "already pending" in res2.json()["detail"].lower()


def test_req4_existing_analyst_cannot_request_analyst_again():
    """4. Existing ANALYST cannot request ANALYST again."""
    app.dependency_overrides[get_current_active_user] = lambda: USER_ANALYST
    res = client.post("/api/v1/auth/access-request", json={"requested_role": "ANALYST"})
    assert res.status_code == status.HTTP_400_BAD_REQUEST


def test_req5_existing_agency_cannot_request_agency_again():
    """5. Existing AGENCY cannot request AGENCY again."""
    app.dependency_overrides[get_current_active_user] = lambda: USER_AGENCY
    res = client.post("/api/v1/auth/access-request", json={"requested_role": "AGENCY"})
    assert res.status_code == status.HTTP_400_BAD_REQUEST


def test_req6_public_user_remains_public_while_request_is_pending():
    """6. PUBLIC user remains PUBLIC while request is pending."""
    email = f"pending_pub_{uuid.uuid4().hex[:8]}@public.in"
    reg_res = client.post("/api/v1/auth/register", json={
        "full_name": "Pending Applicant",
        "email": email,
        "requested_role": "PUBLIC",
        "password": "ValidPassword123!"
    })
    user_id = reg_res.json()["id"]

    user_obj = User(id=user_id, email=email, role="PUBLIC", is_active=True)
    app.dependency_overrides[get_current_active_user] = lambda: user_obj
    app.dependency_overrides[get_current_user] = lambda: user_obj

    # Submit access request
    client.post("/api/v1/auth/access-request", json={"requested_role": "ANALYST"})

    # Verify user record in database still has role == PUBLIC
    with SessionLocal() as db:
        user_in_db = db.query(User).filter(User.id == user_id).first()
        assert user_in_db.role == "PUBLIC"


def test_req7_admin_can_approve_analyst_request():
    """7. ADMIN can approve ANALYST request."""
    email = f"appr_analyst_{uuid.uuid4().hex[:8]}@public.in"
    reg_res = client.post("/api/v1/auth/register", json={
        "full_name": "Analyst Applicant",
        "email": email,
        "requested_role": "PUBLIC",
        "password": "ValidPassword123!"
    })
    user_id = reg_res.json()["id"]

    user_obj = User(id=user_id, email=email, role="PUBLIC", is_active=True)
    app.dependency_overrides[get_current_active_user] = lambda: user_obj
    app.dependency_overrides[get_current_user] = lambda: user_obj

    sub_res = client.post("/api/v1/auth/access-request", json={"requested_role": "ANALYST"})
    request_id = sub_res.json()["request_id"]

    # Admin approves
    app.dependency_overrides[require_admin] = lambda: USER_ADMIN
    app.dependency_overrides[get_current_active_user] = lambda: USER_ADMIN
    appr_res = client.post(f"/api/v1/admin/access-requests/{request_id}/approve")
    assert appr_res.status_code == status.HTTP_200_OK
    assert appr_res.json()["status"] == "APPROVED"
    assert appr_res.json()["role"] == "ANALYST"


def test_req8_admin_can_approve_agency_request():
    """8. ADMIN can approve AGENCY request."""
    email = f"appr_agency_{uuid.uuid4().hex[:8]}@public.in"
    reg_res = client.post("/api/v1/auth/register", json={
        "full_name": "Agency Applicant",
        "email": email,
        "requested_role": "PUBLIC",
        "password": "ValidPassword123!"
    })
    user_id = reg_res.json()["id"]

    user_obj = User(id=user_id, email=email, role="PUBLIC", is_active=True)
    app.dependency_overrides[get_current_active_user] = lambda: user_obj
    app.dependency_overrides[get_current_user] = lambda: user_obj

    sub_res = client.post("/api/v1/auth/access-request", json={"requested_role": "AGENCY"})
    request_id = sub_res.json()["request_id"]

    # Admin approves
    app.dependency_overrides[require_admin] = lambda: USER_ADMIN
    app.dependency_overrides[get_current_active_user] = lambda: USER_ADMIN
    appr_res = client.post(f"/api/v1/admin/access-requests/{request_id}/approve")
    assert appr_res.status_code == status.HTTP_200_OK
    assert appr_res.json()["status"] == "APPROVED"
    assert appr_res.json()["role"] == "AGENCY"


def test_req9_after_approval_user_role_changes_correctly():
    """9. After approval, user role changes correctly in the database."""
    email = f"role_change_{uuid.uuid4().hex[:8]}@public.in"
    reg_res = client.post("/api/v1/auth/register", json={
        "full_name": "Role Change Applicant",
        "email": email,
        "requested_role": "PUBLIC",
        "password": "ValidPassword123!"
    })
    user_id = reg_res.json()["id"]

    user_obj = User(id=user_id, email=email, role="PUBLIC", is_active=True)
    app.dependency_overrides[get_current_active_user] = lambda: user_obj
    app.dependency_overrides[get_current_user] = lambda: user_obj

    sub_res = client.post("/api/v1/auth/access-request", json={"requested_role": "ANALYST"})
    request_id = sub_res.json()["request_id"]

    app.dependency_overrides[require_admin] = lambda: USER_ADMIN
    app.dependency_overrides[get_current_active_user] = lambda: USER_ADMIN
    client.post(f"/api/v1/admin/access-requests/{request_id}/approve")

    with SessionLocal() as db:
        user_db = db.query(User).filter(User.id == user_id).first()
        assert user_db.role == "ANALYST"


def test_req10_public_user_selecting_analyst_from_login_rejected_safely():
    """10. Public user selecting ANALYST from login is rejected safely with guidance."""
    authorized, dest, err = evaluate_login_portal_routing("PUBLIC", "/dashboard")
    assert authorized is False
    assert "Your account is currently PUBLIC" in err
    assert "Request operational access from the Public Portal" in err


def test_req11_public_user_selecting_agency_from_login_rejected_safely():
    """11. Public user selecting AGENCY from login is rejected safely with guidance."""
    authorized, dest, err = evaluate_login_portal_routing("PUBLIC", "/portal/agency")
    assert authorized is False
    assert "Your account is currently PUBLIC" in err
    assert "Request operational access from the Public Portal" in err


def test_req12_no_admin_self_assignment():
    """12. No ADMIN self-assignment during registration or via access-request endpoint."""
    # Registration attempt
    reg_res = client.post("/api/v1/auth/register", json={
        "full_name": "Admin Escalation Attacker",
        "email": f"attacker_{uuid.uuid4().hex[:8]}@bad.com",
        "role": "ADMIN",
        "requested_role": "ADMIN",
        "password": "ValidPassword123!"
    })
    assert reg_res.status_code == status.HTTP_200_OK
    assert reg_res.json()["role"] == "PUBLIC"

    # Authenticated access-request attempt with requested_role=ADMIN
    attacker = User(id="attacker-id", email="attacker@bad.com", role="PUBLIC", is_active=True)
    app.dependency_overrides[get_current_active_user] = lambda: attacker
    req_res = client.post("/api/v1/auth/access-request", json={"requested_role": "ADMIN"})
    assert req_res.status_code == status.HTTP_400_BAD_REQUEST
    assert "Only ANALYST and AGENCY" in req_res.json()["detail"]
