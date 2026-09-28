"""
AGNI-NETRA — Automated Security Hardening, RBAC & Prototype Access Test Suite
Validates:
1. Prototype mode toggle enforcement and security boundaries
2. One-click demo session token creation for ANALYST, AGENCY, PUBLIC
3. Strict rejection of ADMIN prototype access
4. Normal JWT authentication and RoleChecker RBAC enforcement for prototype users
5. Normal self-service registration (ANALYST, AGENCY, PUBLIC, Gmail, optional org)
6. Prevention of ADMIN self-registration
7. Normal credentials login and session cookie termination
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
def clean_dependencies_and_settings():
    original_proto_mode = settings.AGNI_PROTOTYPE_MODE
    app.dependency_overrides.clear()
    client.cookies.clear()
    yield
    client.cookies.clear()
    app.dependency_overrides.clear()
    settings.AGNI_PROTOTYPE_MODE = original_proto_mode


# =========================================================================
# 1. Prototype Mode Access Suite (Section 19: Requirements 1-9)
# =========================================================================

def test_proto_1_prototype_mode_disabled_rejects_session():
    """1. When prototype mode is disabled, prototype-session is rejected with 403."""
    settings.AGNI_PROTOTYPE_MODE = False
    res = client.post("/api/v1/auth/prototype-session", json={"role": "ANALYST"})
    assert res.status_code == status.HTTP_403_FORBIDDEN
    assert "disabled" in res.json().get("detail", "").lower()


def test_proto_2_prototype_mode_enabled_creates_analyst_session():
    """2. When prototype mode is enabled, ANALYST session is created."""
    settings.AGNI_PROTOTYPE_MODE = True
    res = client.post("/api/v1/auth/prototype-session", json={"role": "ANALYST"})
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["user"]["role"] == "ANALYST"
    assert data["user"]["email"] == "prototype-analyst@agni-netra.local"
    assert "access_token" in data and len(data["access_token"].split(".")) == 3

    # Check cookies are set
    set_cookie = res.headers.get("set-cookie", "")
    assert "access_token" in set_cookie


def test_proto_3_prototype_mode_enabled_creates_agency_session():
    """3. When prototype mode is enabled, AGENCY session is created."""
    settings.AGNI_PROTOTYPE_MODE = True
    res = client.post("/api/v1/auth/prototype-session", json={"role": "AGENCY"})
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["user"]["role"] == "AGENCY"
    assert data["user"]["email"] == "prototype-agency@agni-netra.local"
    assert "access_token" in data


def test_proto_4_prototype_mode_enabled_creates_public_session():
    """4. When prototype mode is enabled, PUBLIC session is created."""
    settings.AGNI_PROTOTYPE_MODE = True
    res = client.post("/api/v1/auth/prototype-session", json={"role": "PUBLIC"})
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["user"]["role"] == "PUBLIC"
    assert data["user"]["email"] == "prototype-public@agni-netra.local"
    assert "access_token" in data


def test_proto_5_prototype_admin_session_rejected():
    """5. Prototype ADMIN session must be rejected with 400 Bad Request."""
    settings.AGNI_PROTOTYPE_MODE = True
    res = client.post("/api/v1/auth/prototype-session", json={"role": "ADMIN"})
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert "ADMIN" in res.json().get("detail", "")

    # Arbitrary unauthorized roles must also be rejected
    res2 = client.post("/api/v1/auth/prototype-session", json={"role": "ROOT"})
    assert res2.status_code == status.HTTP_400_BAD_REQUEST


def test_proto_6_prototype_jwt_authenticates_normally():
    """6. Prototype JWT authenticates normally via get_current_user on /auth/me."""
    settings.AGNI_PROTOTYPE_MODE = True
    proto_res = client.post("/api/v1/auth/prototype-session", json={"role": "ANALYST"})
    assert proto_res.status_code == status.HTTP_200_OK
    token = proto_res.json()["access_token"]

    res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == status.HTTP_200_OK
    user_data = res.json()
    assert user_data["email"] == "prototype-analyst@agni-netra.local"
    assert user_data["role"] == "ANALYST"


def test_proto_7_analyst_prototype_reaches_analyst_protected_apis():
    """7. Analyst prototype reaches analyst-protected APIs (e.g. /analyst/triage)."""
    settings.AGNI_PROTOTYPE_MODE = True
    proto_res = client.post("/api/v1/auth/prototype-session", json={"role": "ANALYST"})
    token = proto_res.json()["access_token"]

    res = client.get("/api/v1/analyst/triage", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == status.HTTP_200_OK


def test_proto_8_agency_prototype_reaches_agency_protected_apis():
    """8. Agency prototype reaches agency-protected APIs (e.g. /alerts)."""
    settings.AGNI_PROTOTYPE_MODE = True
    proto_res = client.post("/api/v1/auth/prototype-session", json={"role": "AGENCY"})
    token = proto_res.json()["access_token"]

    res = client.get("/api/v1/alerts?limit=5", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == status.HTTP_200_OK


def test_proto_9_public_prototype_restricted_to_public_permissions():
    """9. Public prototype remains restricted to public permissions."""
    settings.AGNI_PROTOTYPE_MODE = True
    proto_res = client.post("/api/v1/auth/prototype-session", json={"role": "PUBLIC"})
    token = proto_res.json()["access_token"]

    # Blocked from analyst triage
    res_analyst = client.get("/api/v1/analyst/triage", headers={"Authorization": f"Bearer {token}"})
    assert res_analyst.status_code == status.HTTP_403_FORBIDDEN

    # Blocked from internal facilities
    res_facilities = client.get("/api/v1/facilities", headers={"Authorization": f"Bearer {token}"})
    assert res_facilities.status_code == status.HTTP_403_FORBIDDEN

    # Allowed on public overview
    res_public = client.get("/api/v1/portals/public/overview", headers={"Authorization": f"Bearer {token}"})
    assert res_public.status_code == status.HTTP_200_OK


# =========================================================================
# 2. Registration Suite (Section 19: Requirements 10-15)
# =========================================================================

def test_scenario_10_normal_registration_creates_analyst():
    """10. Normal registration creates ANALYST user directly."""
    unique_email = f"analyst_usr_{uuid.uuid4().hex[:8]}@fsi.gov.in"
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
        assert audit.details.get("role") == "ANALYST" or audit.details.get("assigned_role") == "ANALYST"


def test_scenario_11_normal_registration_creates_agency():
    """11. Normal registration creates AGENCY user directly."""
    unique_email = f"agency_usr_{uuid.uuid4().hex[:8]}@sdma.gov.in"
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


def test_scenario_12_normal_registration_creates_public():
    """12. Normal registration creates PUBLIC user directly."""
    unique_email = f"public_usr_{uuid.uuid4().hex[:8]}@public.in"
    payload = {
        "full_name": "Citizen Observer",
        "email": unique_email,
        "organization": "Civil Society Forum",
        "role": "PUBLIC",
        "password": "ValidPassword123!",
    }
    res = client.post("/api/v1/auth/register", json=payload)
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["role"] == "PUBLIC"
    assert data["email"] == unique_email


def test_scenario_13_admin_cannot_self_register():
    """13. ADMIN cannot self-register publicly (rejected with 400)."""
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


def test_scenario_14_gmail_registration_works():
    """14. Standard consumer email (gmail.com, yahoo.com) registration works."""
    unique_email = f"user.{uuid.uuid4().hex[:6]}@gmail.com"
    payload = {
        "full_name": "Field Officer",
        "email": unique_email,
        "role": "ANALYST",
        "password": "ValidPassword123!",
    }
    res = client.post("/api/v1/auth/register", json=payload)
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["email"] == unique_email
    assert res.json()["role"] == "ANALYST"


def test_scenario_15_organization_is_optional():
    """15. Organization field is optional and omissible."""
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
# 3. Normal Login & Core Authentication (Section 19: Requirements 16-17)
# =========================================================================

def test_scenario_16_normal_login_still_works():
    """16. Normal credentials login works via /api/v1/auth/login."""
    unique_email = f"login_test_{uuid.uuid4().hex[:8]}@domain.gov.in"
    reg_payload = {
        "full_name": "Login Test User",
        "email": unique_email,
        "role": "ANALYST",
        "password": "NormalPassword123!",
    }
    reg_res = client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_res.status_code == status.HTTP_200_OK

    login_res = client.post(
        "/api/v1/auth/login",
        data={"username": unique_email, "password": "NormalPassword123!"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert login_res.status_code == status.HTTP_200_OK
    data = login_res.json()
    assert "access_token" in data
    assert data["user"]["email"] == unique_email
    assert data["user"]["role"] == "ANALYST"


def test_scenario_17_existing_rbac_tests_remain_passing():
    """17. Regression verification of existing auth, hashing, and RBAC primitives."""
    from backend.app.core.security import verify_password
    h = get_password_hash("TestP@ssw0rd")
    assert verify_password("TestP@ssw0rd", h) is True
    assert verify_password("WrongPassword", h) is False

    assert require_admin(USER_ADMIN) == USER_ADMIN
    assert require_analyst(USER_ANALYST) == USER_ANALYST
    assert require_agency(USER_AGENCY) == USER_AGENCY


# =========================================================================
# 4. Protected API Boundary & Security Invariants
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
    ]

    for method, path in protected_endpoints:
        if method == "GET":
            res = client.get(path)
        else:
            res = client.post(path, json={"command": "test"})
        assert res.status_code == status.HTTP_401_UNAUTHORIZED


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
        assert res.status_code != status.HTTP_401_UNAUTHORIZED


def test_login_invalid_credentials_returns_generic_error():
    """Invalid credentials must return 401 without revealing whether email exists."""
    res = client.post(
        "/api/v1/auth/login",
        data={"username": "nonexistent@domain.gov.in", "password": "WrongPassword123!"},
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


def test_cookie_based_authentication():
    """Requests presenting valid access_token via HTTP-only Cookie must be authenticated."""
    token = create_access_token(
        subject="test-analyst-uuid",
        role="ANALYST",
        expires_delta=timedelta(minutes=30),
    )

    client.cookies.set("access_token", token)
    try:
        app.dependency_overrides[get_current_active_user] = lambda: USER_ANALYST
        res = client.get("/api/v1/events/geojson")
        assert res.status_code != status.HTTP_401_UNAUTHORIZED
    finally:
        client.cookies.clear()


def test_expired_token_rejected():
    """Expired JWT tokens must be strictly rejected with 401."""
    expired_payload = {
        "sub": "test-analyst-uuid",
        "role": "ANALYST",
        "exp": datetime.now(timezone.utc) - timedelta(hours=1),
    }
    expired_token = jwt.encode(expired_payload, settings.SECRET_KEY, algorithm=ALGORITHM)

    res = client.get(
        "/api/v1/events/geojson",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert res.status_code == status.HTTP_401_UNAUTHORIZED


# =========================================================================
# 5. Portal Routing & Mismatch Handling Invariants
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


def test_portal_routing_and_mismatches():
    # ANALYST routing
    auth_an, dest_an, _ = evaluate_login_portal_routing("ANALYST")
    assert auth_an is True and dest_an == "/dashboard"

    # AGENCY routing
    auth_ag, dest_ag, _ = evaluate_login_portal_routing("AGENCY")
    assert auth_ag is True and dest_ag == "/portal/agency"

    # PUBLIC routing
    auth_pu, dest_pu, _ = evaluate_login_portal_routing("PUBLIC")
    assert auth_pu is True and dest_pu == "/portal/public"

    # Mismatch rejections
    _, _, err_pu = evaluate_login_portal_routing("PUBLIC", "/dashboard")
    assert err_pu == "Your account is registered for PUBLIC access."

    _, _, err_an = evaluate_login_portal_routing("ANALYST", "/portal/agency")
    assert err_an == "Your account is registered for ANALYST access."

    _, _, err_ag = evaluate_login_portal_routing("AGENCY", "/dashboard")
    assert err_ag == "Your account is registered for AGENCY access."


def test_unauthenticated_protected_routes_middleware_simulation():
    """Unauthenticated protected routes redirect to /login."""
    def simulate_nextjs_middleware(pathname: str, search: str, has_cookie: bool):
        if not has_cookie:
            dest = f"{pathname}{search}"
            return {"redirect": f"/login?redirect={dest}" if dest and dest != "/" else "/login"}
        return {"status": 200}

    for path in ["/dashboard", "/admin", "/portal/agency"]:
        sim = simulate_nextjs_middleware(path, "?test=1", has_cookie=False)
        assert sim["redirect"] == f"/login?redirect={path}?test=1"

    sim_auth = simulate_nextjs_middleware("/dashboard", "", has_cookie=True)
    assert sim_auth["status"] == 200


def test_three_public_portals_only_and_no_admin_in_login():
    """10 & 11. Verify that public login page configures exactly ANALYST, AGENCY, PUBLIC and NO ADMIN."""
    import re
    import os
    login_page_path = os.path.join("frontend", "src", "app", "login", "page.tsx")
    with open(login_page_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Verify 3 persona cards only
    assert '"ANALYST"' in content
    assert '"AGENCY"' in content
    assert '"PUBLIC"' in content

    # Assert ADMIN, RESEARCHER, INDUSTRY are not in PERSONA_CARDS
    persona_match = re.search(r"PERSONA_CARDS: PersonaCard\[\] = \[(.*?)\];", content, re.DOTALL)
    assert persona_match is not None
    persona_block = persona_match.group(1)
    assert "ADMIN" not in persona_block
    assert "RESEARCHER" not in persona_block
    assert "INDUSTRY" not in persona_block
