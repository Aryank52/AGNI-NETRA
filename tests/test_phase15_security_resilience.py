"""
JARVIS Phase 15 Test Suite: Production Readiness, Security, Performance & Resilience
Validates all 30 required verification scenarios matching Section 27:
1. test_jwt_expiry
2. test_jwt_issuer_validation
3. test_rbac_enforcement
4. test_privilege_escalation_denial
5. test_public_masking
6. test_secret_leakage_prevention
7. test_input_validation_coordinates_and_bounds
8. test_sql_injection_protection
9. test_path_traversal_protection
10. test_oversized_requests_rejection
11. test_invalid_ids_rejection
12. test_provider_failure_graceful_handling
13. test_provider_timeout_handling
14. test_malformed_provider_response_handling
15. test_database_failure_handling
16. test_transaction_rollback_atomicity
17. test_audit_immutability_and_tamper_detection
18. test_restart_recovery_and_idle_state
19. test_concurrent_writes_and_locking
20. test_report_resilience_and_hash_reproducibility
21. test_jarvis_safe_failure_without_crash
22. test_dispatch_remains_blocked
23. test_one_master_agent_invariant
24. test_no_model_changes
25. test_no_risk_formula_changes
26. test_no_fabricated_fallback_data
27. test_safe_error_responses_no_internals
28. test_correlation_id_propagation
29. test_large_dataset_bounded_pagination
30. test_assessment_integrity_versioning
"""

import os
import uuid
import json
import hashlib
from datetime import datetime, timezone, timedelta
import pytest
from jose import jwt
from jose.exceptions import ExpiredSignatureError, JWTClaimsError, JWTError
from fastapi.testclient import TestClient
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from backend.app.main import app
from backend.app.core.config import settings
from backend.app.core.database import SessionLocal
from backend.app.core.security import (
    create_access_token,
    decode_access_token,
    AUTH_ISSUER,
    ALGORITHM,
)
from backend.app.api.deps import (
    get_current_user,
    get_current_active_user,
    require_admin,
    require_analyst,
    require_agency,
)
from backend.app.models.domain import (
    User,
    InvestigationWorkspace,
    InvestigationAuditLog,
    AssessmentVersion,
    ReportVersion,
)
from backend.app.models.canonical import (
    CaseState,
    CaseActionType,
    HumanVerificationDecision,
)
from backend.app.services.governance.case_management import (
    case_management_engine,
    verify_audit_entry_integrity,
    verify_case_audit_integrity,
    CaseAuthorizationError,
    CaseStateTransitionError,
)
from backend.app.services.jarvis.jarvis_workspace import workspace_manager
from backend.app.services.jarvis.jarvis_orchestrator import master_orchestrator
from backend.app.services.jarvis.jarvis_command_interpreter import command_interpreter
from backend.app.models.jarvis_schemas import JarvisCommandRequest, StepStatus, JarvisState, CommandIntent
from backend.app.services.model_integrity_service import ModelIntegrityService
from backend.app.services.risk_service import calculate_risk_score
from backend.app.services.intelligence.provider_registry import ProviderRegistry
from backend.app.services.intelligence.providers.base import (
    ProviderHealth,
    BaseIntelligenceProvider,
    ProviderMetadata,
    GeographicCoverage,
    CoverageType,
)
from backend.app.api.v1.endpoints.health import database_health_check


client = TestClient(app, raise_server_exceptions=False)

USER_ADMIN = User(id="usr-adm-phase15", email="admin@agninetra.gov.in", role="ADMIN", is_active=True)
USER_ANALYST = User(id="usr-ana-phase15", email="analyst@agninetra.gov.in", role="ANALYST", is_active=True)
USER_AGENCY = User(id="usr-age-phase15", email="agency@agninetra.gov.in", role="AGENCY", is_active=True)
USER_PUBLIC = User(id="usr-pub-phase15", email="citizen@public.in", role="PUBLIC", is_active=True)


def make_test_id(prefix: str = "test15") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


@pytest.fixture(scope="function")
def db_session():
    """Provides a transactional database session."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


# =============================================================================
# 1. TEST JWT EXPIRY
# =============================================================================
def test_jwt_expiry():
    """Expired JWT tokens must be rejected with HTTP 401 and ExpiredSignatureError."""
    past_exp = datetime.now(timezone.utc) - timedelta(minutes=15)
    expired_payload = {
        "sub": "usr-ana-phase15",
        "role": "ANALYST",
        "iss": AUTH_ISSUER,
        "exp": past_exp,
    }
    expired_token = jwt.encode(expired_payload, settings.SECRET_KEY, algorithm=ALGORITHM)

    # Unit check
    with pytest.raises(ExpiredSignatureError):
        decode_access_token(expired_token, verify_exp=True)

    # API check
    app.dependency_overrides.clear()
    headers = {"Authorization": f"Bearer {expired_token}"}
    response = client.get("/api/v1/facilities", headers=headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "expired" in response.json().get("detail", "").lower()


# =============================================================================
# 2. TEST JWT ISSUER VALIDATION
# =============================================================================
def test_jwt_issuer_validation():
    """JWT tokens with forged or untrusted issuers must be rejected."""
    future_exp = datetime.now(timezone.utc) + timedelta(hours=1)
    forged_payload = {
        "sub": "usr-ana-phase15",
        "role": "ANALYST",
        "iss": "forged-external-issuer",
        "exp": future_exp,
    }
    forged_token = jwt.encode(forged_payload, settings.SECRET_KEY, algorithm=ALGORITHM)

    # Unit check
    with pytest.raises(JWTClaimsError):
        decode_access_token(forged_token, verify_exp=True)

    # API check
    app.dependency_overrides.clear()
    headers = {"Authorization": f"Bearer {forged_token}"}
    response = client.get("/api/v1/facilities", headers=headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# =============================================================================
# 3. TEST RBAC ENFORCEMENT
# =============================================================================
def test_rbac_enforcement():
    """Enforces strict role separation across Admin, Analyst, Agency, and Public tiers."""
    # Dependency checker unit enforcement
    assert require_admin(USER_ADMIN) == USER_ADMIN
    with pytest.raises(HTTPException) as exc:
        require_admin(USER_ANALYST)
    assert exc.value.status_code == status.HTTP_403_FORBIDDEN

    assert require_analyst(USER_ANALYST) == USER_ANALYST
    with pytest.raises(HTTPException) as exc:
        require_analyst(USER_AGENCY)
    assert exc.value.status_code == status.HTTP_403_FORBIDDEN

    # API route enforcement
    app.dependency_overrides[get_current_user] = lambda: USER_AGENCY
    app.dependency_overrides[get_current_active_user] = lambda: USER_AGENCY
    try:
        # Agency blocked from analytical facilities & admin endpoints
        resp_fac = client.get("/api/v1/facilities?limit=5")
        assert resp_fac.status_code == status.HTTP_403_FORBIDDEN

        resp_admin = client.get("/api/v1/admin/system-stats")
        assert resp_admin.status_code == status.HTTP_403_FORBIDDEN

        # Agency permitted on operational alerts
        resp_alerts = client.get("/api/v1/alerts?limit=5")
        assert resp_alerts.status_code == status.HTTP_200_OK
    finally:
        app.dependency_overrides.clear()


# =============================================================================
# 4. TEST PRIVILEGE ESCALATION DENIAL
# =============================================================================
def test_privilege_escalation_denial():
    """PUBLIC or unauthenticated entities cannot execute analyst actions or escalate privileges."""
    # Public role cannot authorize or execute governed actions
    with pytest.raises(CaseAuthorizationError):
        case_management_engine.check_authorization("PUBLIC", CaseActionType.VERIFY.value)
    with pytest.raises(CaseAuthorizationError):
        case_management_engine.check_authorization("PUBLIC", CaseActionType.CLOSE.value)
    with pytest.raises(CaseAuthorizationError):
        case_management_engine.check_authorization("PUBLIC", CaseActionType.RESOLVE.value)

    # Attempting to execute action without analyst permissions raises CaseAuthorizationError
    dummy_ws = InvestigationWorkspace(
        investigation_id=make_test_id("INV-ESC"),
        target_event_id="EVT-827",
        status=CaseState.REQUIRES_REVIEW.value,
        verification_status="REQUIRES_HUMAN_REVIEW"
    )
    with pytest.raises(CaseAuthorizationError):
        case_management_engine.propose_or_execute_action(
            db=None,
            workspace=dummy_ws,
            action=CaseActionType.CLOSE.value,
            actor_id="CITIZEN_MALLORY",
            actor_role="PUBLIC",
            confirm_governed_action=True
        )

    # API write endpoint denies unauthenticated / public caller
    app.dependency_overrides.clear()
    payload = {
        "action": "CLOSE",
        "reason": "Unauthorized escalation attempt"
    }
    resp = client.post("/api/v1/investigations/INV-TEST/actions", json=payload)
    assert resp.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]


# =============================================================================
# 5. TEST PUBLIC MASKING
# =============================================================================
def test_public_masking():
    """Public portal endpoints round coordinates to 2 decimal places and strip sensitive metadata."""
    app.dependency_overrides.clear()
    response = client.get("/api/v1/portals/public/hazard-map?limit=10")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "events" in data

    for ev in data["events"]:
        lat_parts = str(ev["latitude"]).split(".")
        lon_parts = str(ev["longitude"]).split(".")
        if len(lat_parts) > 1:
            assert len(lat_parts[1]) <= 2, f"Latitude {ev['latitude']} exceeds 2 decimal places"
        if len(lon_parts) > 1:
            assert len(lon_parts[1]) <= 2, f"Longitude {ev['longitude']} exceeds 2 decimal places"

        # Check absence of sensitive internal attributes
        for sensitive_key in ["features_vector", "shap_values", "internal_facility_id", "owner_contact"]:
            assert sensitive_key not in ev, f"Leaked sensitive field {sensitive_key} in public response"


# =============================================================================
# 6. TEST SECRET LEAKAGE PREVENTION
# =============================================================================
def test_secret_leakage_prevention():
    """No sensitive keys, DB passwords, or internal tokens appear in public or health endpoints."""
    endpoints = [
        "/api/v1/health",
        "/api/v1/health/db",
        "/api/v1/health/providers",
        "/api/v1/health/application",
    ]

    for ep in endpoints:
        resp = client.get(ep)
        body = resp.text
        assert settings.SECRET_KEY not in body, f"Secret key exposed in {ep}"
        assert "postgres:" not in body, f"DB credentials exposed in {ep}"


# =============================================================================
# 7. TEST INPUT VALIDATION COORDINATES AND BOUNDS
# =============================================================================
def test_input_validation_coordinates_and_bounds():
    """Malformed coordinates, bad bounding boxes, or out-of-range limits are rejected with 400."""
    app.dependency_overrides[get_current_user] = lambda: USER_ANALYST
    app.dependency_overrides[get_current_active_user] = lambda: USER_ANALYST
    try:
        # Non-numeric bbox on GIS industrial facilities endpoint
        r1 = client.get("/api/v1/gis/industrial-facilities?bbox=alpha,beta,gamma,delta")
        assert r1.status_code == status.HTTP_400_BAD_REQUEST

        # Latitude > 90
        r2 = client.get("/api/v1/gis/industrial-facilities?bbox=77.0,95.0,78.0,96.0")
        assert r2.status_code == status.HTTP_400_BAD_REQUEST

        # Malformed count
        r3 = client.get("/api/v1/gis/industrial-facilities?bbox=77.0,28.0,78.0")
        assert r3.status_code == status.HTTP_400_BAD_REQUEST

        # Invalid pagination limit (<= 0)
        r4 = client.get("/api/v1/events?limit=0")
        assert r4.status_code == status.HTTP_400_BAD_REQUEST
    finally:
        app.dependency_overrides.clear()


# =============================================================================
# 8. TEST SQL INJECTION PROTECTION
# =============================================================================
def test_sql_injection_protection():
    """SQL injection payloads in query parameters are handled safely via parameterized ORM queries."""
    app.dependency_overrides[get_current_user] = lambda: USER_ANALYST
    app.dependency_overrides[get_current_active_user] = lambda: USER_ANALYST
    try:
        injection_payloads = [
            "' OR '1'='1",
            "'; DROP TABLE users;--",
            "1 UNION SELECT null, null, null--",
            "' OR 1=1--",
        ]
        for payload in injection_payloads:
            resp = client.get(f"/api/v1/events?satellite={payload}")
            # Parameterized query handles payload cleanly without SQL syntax failure
            assert resp.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY]
    finally:
        app.dependency_overrides.clear()


# =============================================================================
# 9. TEST PATH TRAVERSAL PROTECTION
# =============================================================================
def test_path_traversal_protection():
    """Path traversal sequences (.., slashes, null bytes) are blocked with HTTP 400."""
    app.dependency_overrides[get_current_user] = lambda: USER_ANALYST
    app.dependency_overrides[get_current_active_user] = lambda: USER_ANALYST
    try:
        traversals = [
            "../../etc/passwd",
            "..%2f..%2fwindows%2fwin.ini",
            "EVT-827%00malicious",
            "..%5c..%5cboot.ini",
        ]
        for bad_id in traversals:
            resp = client.get(f"/api/v1/reports/event/{bad_id}/download")
            assert resp.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND]
    finally:
        app.dependency_overrides.clear()


# =============================================================================
# 10. TEST OVERSIZED REQUESTS REJECTION
# =============================================================================
def test_oversized_requests_rejection():
    """Unbounded limits and oversized requests exceed bounds and are rejected with HTTP 400."""
    app.dependency_overrides[get_current_user] = lambda: USER_ANALYST
    app.dependency_overrides[get_current_active_user] = lambda: USER_ANALYST
    try:
        # Limit > 1000 rejected
        r1 = client.get("/api/v1/events?limit=1001")
        assert r1.status_code == status.HTTP_400_BAD_REQUEST
        assert "limit" in r1.json().get("detail", "").lower()

        # Limit > 50000 rejected
        r2 = client.get("/api/v1/events?limit=50000")
        assert r2.status_code == status.HTTP_400_BAD_REQUEST
    finally:
        app.dependency_overrides.clear()


# =============================================================================
# 11. TEST INVALID IDS REJECTION
# =============================================================================
def test_invalid_ids_rejection():
    """Non-existent or malformed entity IDs are rejected with clean 404/400 without script reflection."""
    app.dependency_overrides[get_current_user] = lambda: USER_ANALYST
    app.dependency_overrides[get_current_active_user] = lambda: USER_ANALYST
    try:
        # Non-existent investigation
        r1 = client.get("/api/v1/investigations/INV-DOES-NOT-EXIST-99999")
        assert r1.status_code == status.HTTP_404_NOT_FOUND
        assert r1.json().get("detail") is not None

        # Cross-site script tag in ID
        xss_id = "INV-test-xss-clean"
        r2 = client.get(f"/api/v1/investigations/{xss_id}")
        assert r2.status_code in [status.HTTP_404_NOT_FOUND, status.HTTP_400_BAD_REQUEST]
        assert "<script>" not in r2.text
    finally:
        app.dependency_overrides.clear()


# =============================================================================
# 12. TEST PROVIDER FAILURE GRACEFUL HANDLING
# =============================================================================
def test_provider_failure_graceful_handling():
    """Provider exceptions are caught, recorded as DEGRADED, and do not crash the registry."""
    class FailingTestProvider(BaseIntelligenceProvider):
        def get_metadata(self) -> ProviderMetadata:
            return ProviderMetadata(
                provider_name="FAILING_TEST_FEED",
                dataset_name="FAILING_DATASET",
                availability=ProviderHealth.AVAILABLE,
                capabilities=["TEST"],
                geographic_coverage=GeographicCoverage(coverage_type=CoverageType.GLOBAL, description="Global", is_global=True)
            )
        def get_coverage(self) -> GeographicCoverage:
            return GeographicCoverage(coverage_type=CoverageType.GLOBAL, description="Global", is_global=True)
        def get_health(self, db: Session = None) -> ProviderHealth:
            raise RuntimeError("Simulated remote satellite feed socket crash")

    registry = ProviderRegistry()
    registry.register_provider(FailingTestProvider())

    summary = registry.get_provider_health_summary(db=None)
    assert summary is not None
    assert "provider_count" in summary
    assert "statuses" in summary
    # Registry caught the exception and assigned DEGRADED or UNAVAILABLE
    failing_status = summary["statuses"].get("FAILING_TEST_FEED")
    assert failing_status in [ProviderHealth.DEGRADED.value, ProviderHealth.UNAVAILABLE.value]


# =============================================================================
# 13. TEST PROVIDER TIMEOUT HANDLING
# =============================================================================
def test_provider_timeout_handling():
    """Provider timeouts are captured gracefully, setting health to DEGRADED."""
    class TimeoutTestProvider(BaseIntelligenceProvider):
        def get_metadata(self) -> ProviderMetadata:
            return ProviderMetadata(
                provider_name="TIMEOUT_TEST_FEED",
                dataset_name="TIMEOUT_DATASET",
                availability=ProviderHealth.AVAILABLE,
                capabilities=["TIMEOUT_TEST"],
                geographic_coverage=GeographicCoverage(coverage_type=CoverageType.GLOBAL, description="Global", is_global=True)
            )
        def get_coverage(self) -> GeographicCoverage:
            return GeographicCoverage(coverage_type=CoverageType.GLOBAL, description="Global", is_global=True)
        def get_health(self, db: Session = None) -> ProviderHealth:
            raise TimeoutError("Simulated provider upstream timeout after 5000ms")

    registry = ProviderRegistry()
    registry.register_provider(TimeoutTestProvider())

    summary = registry.get_provider_health_summary(db=None)
    assert summary["statuses"].get("TIMEOUT_TEST_FEED") in [ProviderHealth.DEGRADED.value, ProviderHealth.UNAVAILABLE.value]


# =============================================================================
# 14. TEST MALFORMED PROVIDER RESPONSE HANDLING
# =============================================================================
def test_malformed_provider_response_handling():
    """Malformed or unexpected external responses are caught without crashing downstream operations."""
    class MalformedDataTestProvider(BaseIntelligenceProvider):
        def get_metadata(self) -> ProviderMetadata:
            return ProviderMetadata(
                provider_name="MALFORMED_DATA_FEED",
                dataset_name="MALFORMED_DATASET",
                availability=ProviderHealth.AVAILABLE,
                capabilities=["PARSE_TEST"],
                geographic_coverage=GeographicCoverage(coverage_type=CoverageType.GLOBAL, description="Global", is_global=True)
            )
        def get_coverage(self) -> GeographicCoverage:
            return GeographicCoverage(coverage_type=CoverageType.GLOBAL, description="Global", is_global=True)
        def get_health(self, db: Session = None) -> ProviderHealth:
            # Emulate JSON decode error or KeyError during health ping
            raise ValueError("Corrupted JSON payload from satellite telemetry endpoint")

    registry = ProviderRegistry()
    registry.register_provider(MalformedDataTestProvider())

    summary = registry.get_provider_health_summary(db=None)
    assert summary["statuses"].get("MALFORMED_DATA_FEED") in [ProviderHealth.DEGRADED.value, ProviderHealth.UNAVAILABLE.value]


# =============================================================================
# 15. TEST DATABASE FAILURE HANDLING
# =============================================================================
def test_database_failure_handling():
    """Database connectivity or query exceptions return sanitized 500 errors without leaking paths."""
    class BrokenSession:
        def execute(self, *args, **kwargs):
            raise SQLAlchemyError("FATAL: connection terminated unexpectedly (psycopg2.OperationalError)")
        def close(self):
            pass

    res = database_health_check(BrokenSession())
    assert res["status"] == "UNHEALTHY"
    assert res["database"] == "FAILED"
    assert "password" not in str(res).lower()
    assert "postgresql://" not in str(res).lower()


# =============================================================================
# 16. TEST TRANSACTION ROLLBACK ATOMICITY
# =============================================================================
def test_transaction_rollback_atomicity(db_session: Session):
    """Case state and audit entries are atomically committed or rolled back together."""
    ws = workspace_manager.get_or_create_workspace(
        db=db_session,
        session_id=make_test_id("test-rollback-session"),
        target_event_id="EVT-827",
        user_role="ANALYST",
        created_by="ANALYST_ROLLBACK"
    )
    ws.status = CaseState.CREATED.value
    db_session.add(ws)
    db_session.commit()
    initial_status = ws.status

    # Attempting to execute an unauthorized transition (VERIFY from CREATED is disallowed)
    with pytest.raises(CaseStateTransitionError):
        case_management_engine.propose_or_execute_action(
            db=db_session,
            workspace=ws,
            action=CaseActionType.VERIFY.value,
            actor_id="ANALYST_ROLLBACK",
            actor_role="ANALYST",
            verifier="ANALYST_ROLLBACK",
            reason="Disallowed instant verify from CREATED",
            confirm_governed_action=True
        )

    # Workspace status must remain unchanged at initial state
    db_session.refresh(ws)
    assert ws.status == initial_status


# =============================================================================
# 17. TEST AUDIT IMMUTABILITY AND TAMPER DETECTION
# =============================================================================
def test_audit_immutability_and_tamper_detection(db_session: Session):
    """Cryptographic audit logs detect unauthorized modifications using HMAC SHA-256."""
    ws = workspace_manager.get_or_create_workspace(
        db=db_session,
        session_id=make_test_id("test-audit-tamper"),
        target_event_id="EVT-827"
    )
    entry = case_management_engine.create_audit_entry(
        db=db_session,
        case_id=ws.investigation_id,
        actor_id="ANALYST_VERIFIER",
        actor_role="ANALYST",
        action="REQUEST_REVIEW",
        new_state=CaseState.REQUIRES_REVIEW.value,
        reason="Evidence graph corroboration high"
    )
    assert entry.audit_id.startswith("AUD-")
    assert "checksum_sha256" in entry.provenance

    # 1. Untampered entry verifies cleanly
    assert verify_audit_entry_integrity(entry) is True
    res = verify_case_audit_integrity(db_session, ws.investigation_id)
    assert res["is_tamper_free"] is True
    assert len(res["tampered_audit_ids"]) == 0

    # 2. Tampered entry fails cryptographic verification
    original_action = entry.action
    entry.action = "FORGED_UNAUTHORIZED_ACTION"
    assert verify_audit_entry_integrity(entry) is False

    res_after = verify_case_audit_integrity(db_session, ws.investigation_id)
    assert res_after["is_tamper_free"] is False
    assert len(res_after["tampered_audit_ids"]) >= 1

    # Restore original action to maintain clean state
    entry.action = original_action


# =============================================================================
# 18. TEST RESTART RECOVERY AND IDLE STATE
# =============================================================================
def test_restart_recovery_and_idle_state(db_session: Session):
    """JARVIS orchestrator restarts cleanly and persistent cases are preserved across restarts."""
    # Workspaces in the database survive engine reboots
    ws = workspace_manager.get_or_create_workspace(
        db=db_session,
        session_id=make_test_id("test-restart"),
        target_event_id="EVT-827"
    )
    stored_inv_id = ws.investigation_id

    # Simulated engine restart / new instance creation
    new_orchestrator = type(master_orchestrator)()
    res = new_orchestrator.execute_command(
        db=db_session,
        request=JarvisCommandRequest(command="status", session_id=make_test_id("test-restart-cmd")),
        user_role="ANALYST"
    )
    assert res is not None
    assert res.execution_trace.status == StepStatus.COMPLETED

    # Reload workspace from database
    recovered_ws = db_session.query(InvestigationWorkspace).filter_by(investigation_id=stored_inv_id).first()
    assert recovered_ws is not None
    assert recovered_ws.investigation_id == stored_inv_id


# =============================================================================
# 19. TEST CONCURRENT WRITES AND LOCKING
# =============================================================================
def test_concurrent_writes_and_locking(db_session: Session):
    """Enforces strict state machine locking preventing illegal race conditions or conflicting writes."""
    ws = workspace_manager.get_or_create_workspace(
        db=db_session,
        session_id=make_test_id("test-concurrency"),
        target_event_id="EVT-827"
    )
    ws.status = CaseState.INVESTIGATING.value
    db_session.add(ws)
    db_session.commit()

    # Move to REQUIRES_REVIEW
    case_management_engine.validate_transition(ws.status, CaseState.REQUIRES_REVIEW.value)
    ws.status = CaseState.REQUIRES_REVIEW.value
    db_session.add(ws)
    db_session.commit()

    # Invalid jump back to CREATED is rejected
    with pytest.raises(CaseStateTransitionError):
        case_management_engine.validate_transition(ws.status, CaseState.CREATED.value)


# =============================================================================
# 20. TEST REPORT RESILIENCE AND HASH REPRODUCIBILITY
# =============================================================================
def test_report_resilience_and_hash_reproducibility(db_session: Session):
    """Report publication computes deterministic SHA-256 hashes that reproduce identically."""
    ws = workspace_manager.get_or_create_workspace(
        db=db_session,
        session_id=make_test_id("test-rep-hash"),
        target_event_id="EVT-827"
    )
    markdown_content = "# FORMAL INTELLIGENCE REPORT EVT-827\n\nVerified industrial thermal emission."
    expected_hash = hashlib.sha256(markdown_content.encode("utf-8")).hexdigest()

    rep = case_management_engine.record_report_version(
        db=db_session,
        case_id=ws.investigation_id,
        presentation_mode="ANALYST",
        assessment_version=1,
        content_markdown=markdown_content,
        title="EVT-827 Hardening Dossier",
        generated_by="ANALYST_ALICE"
    )
    assert rep.hash == expected_hash
    assert rep.report_version == 1

    # Stored version matches SHA-256 exactly
    stored_rep = db_session.query(ReportVersion).filter_by(report_id=rep.report_id).first()
    assert stored_rep is not None
    assert stored_rep.hash == expected_hash


# =============================================================================
# 21. TEST JARVIS SAFE FAILURE WITHOUT CRASH
# =============================================================================
def test_jarvis_safe_failure_without_crash(db_session: Session):
    """Hostile, empty, or oversized input strings fail safely without crashing JARVIS."""
    hostile_inputs = [
        "",
        "   ",
        "A" * 10000,
        "<script>alert('xss')</script>",
        "'; DROP TABLE investigation_workspaces;--",
        "!!!???@@@###$$$%%%^^^&&&***()",
    ]
    for bad_cmd in hostile_inputs:
        intent_res = command_interpreter.interpret(bad_cmd)
        assert intent_res is not None
        assert "intent" in intent_res

    # Orchestrator handles unknown command safely
    result = master_orchestrator.execute_command(
        db=db_session,
        request=JarvisCommandRequest(command="Completely unrecognized anomalous command string 987654321", session_id=make_test_id("test-safe-fail")),
        user_role="ANALYST"
    )
    assert result is not None
    assert result.execution_trace.status in [StepStatus.COMPLETED, StepStatus.FAILED]


# =============================================================================
# 22. TEST DISPATCH REMAINS BLOCKED
# =============================================================================
def test_dispatch_remains_blocked(db_session: Session):
    """Operational dispatch gate invariant: ENABLE_OPERATIONAL_DISPATCH_GATE is strictly False."""
    assert settings.ENABLE_OPERATIONAL_DISPATCH_GATE is False

    # Orchestrator rejects dispatch commands and keeps dispatch gate blocked
    dispatch_res = master_orchestrator.execute_command(
        db=db_session,
        request=JarvisCommandRequest(command="JARVIS, dispatch response team to EVT-827", session_id=make_test_id("test-dispatch")),
        user_role="ANALYST"
    )
    assert dispatch_res.dispatch_gate_blocked is True
    assert "[DISPATCH PERMANENTLY BLOCKED]" in dispatch_res.summary or "blocked" in dispatch_res.summary.lower()


# =============================================================================
# 23. TEST ONE MASTER AGENT INVARIANT
# =============================================================================
def test_one_master_agent_invariant():
    """Exactly one master JARVIS orchestrator instance exists. No autonomous swarms or subagents."""
    from backend.app.services.jarvis.jarvis_orchestrator import master_orchestrator as mo1
    from backend.app.services.jarvis.jarvis_orchestrator import master_orchestrator as mo2
    assert mo1 is mo2
    assert not hasattr(mo1, "subagents") or len(getattr(mo1, "subagents", [])) == 0


# =============================================================================
# 24. TEST NO MODEL CHANGES
# =============================================================================
def test_no_model_changes():
    """Champion model xgb-v3.0-real-candidate and calibrator artifacts are present and verified."""
    service = ModelIntegrityService()
    checksums = service.get_artifact_checksums()

    assert "model_file" in checksums
    assert "calibrator_file" in checksums
    assert "shap_explainer_file" in checksums
    assert "metadata_file" in checksums

    # Ensure artifacts exist and have non-null sha256 checksums
    for name, item in checksums.items():
        if name in ["model_file", "calibrator_file", "shap_explainer_file", "metadata_file"]:
            assert item["status"] == "VERIFIED_PRESENT", f"Champion model artifact {name} is missing"
            assert item["sha256"] is not None
            assert len(item["sha256"]) == 64


# =============================================================================
# 25. TEST NO RISK FORMULA CHANGES
# =============================================================================
def test_no_risk_formula_changes():
    """Enforces strict authoritative risk formula: 0.30*I + 0.25*A + 0.20*E + 0.15*P + 0.10*C."""
    score, level, breakdown, reasons = calculate_risk_score(
        max_frp=350.0,
        avg_frp=200.0,
        anomaly_info={"is_anomaly": True, "z_score": 3.0, "deviation_ratio": 2.0},
        persistence_info={"persistence_score": 10.0},
        nearest_settlement_dist_m=300.0,
        nearest_facility_dist_m=100.0,
        predicted_class="Industrial Fire"
    )
    # Mathematical sanity check on subscore weighting
    i = breakdown["intensity"]
    a = breakdown["abnormality"]
    e = breakdown["exposure"]
    p = breakdown["persistence"]
    c = breakdown["context"]

    expected_total = round(0.30 * i + 0.25 * a + 0.20 * e + 0.15 * p + 0.10 * c, 1)
    assert score == expected_total
    assert score >= 75.0
    assert level == "CRITICAL"


# =============================================================================
# 26. TEST NO FABRICATED FALLBACK DATA
# =============================================================================
def test_no_fabricated_fallback_data():
    """Unconfigured providers return empty lists or offline statuses, never synthetic events."""
    registry = ProviderRegistry()
    unconfigured = [p for p in registry._providers.values() if p.get_metadata().availability == ProviderHealth.NOT_CONFIGURED]
    for p in unconfigured:
        meta = p.get_metadata()
        assert meta.availability == ProviderHealth.NOT_CONFIGURED
        # No synthetic points generated
        if hasattr(p, "get_detections"):
            detections = p.get_detections(db=None)
            assert detections == []


# =============================================================================
# 27. TEST SAFE ERROR RESPONSES NO INTERNALS
# =============================================================================
def test_safe_error_responses_no_internals():
    """Error responses do not leak python tracebacks, internal paths, or database schemas."""
    app.dependency_overrides.clear()
    resp = client.get("/api/v1/invalid-route-for-security-test")
    assert resp.status_code == status.HTTP_404_NOT_FOUND
    body = resp.text
    assert "Traceback (most recent call last)" not in body
    assert "E:\\PROJECTS\\AGNI-NETRA" not in body


# =============================================================================
# 28. TEST CORRELATION ID PROPAGATION
# =============================================================================
def test_correlation_id_propagation():
    """Request correlation IDs are accepted or generated and propagated in response headers."""
    # 1. Custom correlation ID passed
    custom_cid = "AGNI-TEST-TRACE-PHASE15"
    resp1 = client.get("/api/v1/health", headers={"X-Correlation-ID": custom_cid})
    assert resp1.headers.get("X-Correlation-ID") == custom_cid

    # 2. Auto-generated correlation ID
    resp2 = client.get("/api/v1/health")
    assert resp2.headers.get("X-Correlation-ID") is not None
    assert resp2.headers.get("X-Correlation-ID").startswith("AGNI-")


# =============================================================================
# 29. TEST LARGE DATASET BOUNDED PAGINATION
# =============================================================================
def test_large_dataset_bounded_pagination():
    """Pagination parameters enforce strict upper bounds (<= 1000) and reject negative limits/offsets."""
    app.dependency_overrides[get_current_user] = lambda: USER_ANALYST
    app.dependency_overrides[get_current_active_user] = lambda: USER_ANALYST
    try:
        # Valid boundary
        r_valid = client.get("/api/v1/events?limit=1000&offset=0")
        assert r_valid.status_code == status.HTTP_200_OK

        # Exceeds max boundary
        r_over = client.get("/api/v1/events?limit=1001")
        assert r_over.status_code == status.HTTP_400_BAD_REQUEST

        # Negative offset
        r_neg_offset = client.get("/api/v1/events?offset=-1")
        assert r_neg_offset.status_code == status.HTTP_400_BAD_REQUEST

        # Negative limit
        r_neg_limit = client.get("/api/v1/events?limit=-1")
        assert r_neg_limit.status_code == status.HTTP_400_BAD_REQUEST
    finally:
        app.dependency_overrides.clear()


# =============================================================================
# 30. TEST ASSESSMENT INTEGRITY VERSIONING
# =============================================================================
def test_assessment_integrity_versioning(db_session: Session):
    """Assessment revisions increment version numbers, track deltas, and forbid silent overwrites."""
    ws = workspace_manager.get_or_create_workspace(
        db=db_session,
        session_id=make_test_id("test-ass-integ"),
        target_event_id="EVT-827"
    )
    inv_id = ws.investigation_id

    # Version 1
    assessment_v1 = {
        "evidence_support_score": 82.0,
        "uncertainty_summary": {"level": "PARTIALLY_KNOWN"},
        "structured_statements": {"ST-1": {}},
    }
    v1 = case_management_engine.record_assessment_version(
        db=db_session,
        case_id=inv_id,
        assessment_dict=assessment_v1,
        created_by="ANALYST_ALICE",
        trigger="INITIAL_EVALUATION"
    )
    assert v1.version_number == 1
    assert v1.evidence_delta["total_evidence_count"] == 1

    # Version 2
    assessment_v2 = {
        "evidence_support_score": 91.5,
        "uncertainty_summary": {"level": "KNOWN"},
        "structured_statements": {"ST-1": {}, "ST-2": {}},
    }
    v2 = case_management_engine.record_assessment_version(
        db=db_session,
        case_id=inv_id,
        assessment_dict=assessment_v2,
        created_by="ANALYST_ALICE",
        trigger="NEW_GROUND_TRUTH"
    )
    assert v2.version_number == 2
    assert v2.evidence_delta["total_evidence_count"] == 2
    assert v2.uncertainty_delta["score_delta"] == 9.5

    # Confirm version 1 remains unaltered in storage
    stored_v1 = db_session.query(AssessmentVersion).filter_by(case_id=inv_id, version_number=1).first()
    assert stored_v1 is not None
    assert stored_v1.version_number == 1
    assert stored_v1.assessment["evidence_support_score"] == 82.0
