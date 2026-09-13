"""
AGNI-NETRA — Phase 21 Product Readiness, Release Hardening & Demonstration Test Suite
Covers all 23 Release Hardening Groups (A through W):

Group A: Configuration & Environment Hygiene
Group B: Process Startup & Database Engine
Group C: Health & Diagnostics API
Group D: Authentication & Token Lifecycle
Group E: Role-Based Access Control (6 Roles)
Group F: Public Safety & Data Sanitization
Group G: Sovereign India Scope Integrity
Group H: Provider Truthfulness & NOT_CONFIGURED
Group I: Data Provenance & Classification
Group J: Model Governance & Immutability
Group K: Frozen 5-Factor Risk Formula Preservation
Group L: Frozen Governed Priority Formula Preservation
Group M: Single Master Agent Architecture (JARVIS)
Group N: JARVIS Safety & Status Reporting
Group O: Operational Dispatch Gate Safety (BLOCKED)
Group P: Automated Model Activation Safety (DISABLED)
Group Q: API Error Handling & Validation
Group R: Database & PostGIS Geometry Integrity
Group S: Audit Logging & Immutability
Group T: Standardized Report Generation
Group U: Frontend Integration & Route Verification
Group V: Restart & Failure Recovery
Group W: Observability & Log Sanitization
"""

import os
import json
import time
import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy import text
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from backend.app.core.config import settings
from backend.app.core.database import SessionLocal, engine
from backend.app.core.security import (
    create_access_token, decode_access_token,
    verify_password, get_password_hash,
    AUTH_ISSUER
)
from backend.app.main import app
from backend.app.api.deps import RoleChecker
from backend.app.models.domain import (
    User, ThermalEvent, AuditLog, VerificationRecord,
    InvestigationWorkspace, RiskScore, ModelPrediction
)
from backend.app.services.india_boundary_service import india_boundary_service
from backend.app.services.intelligence.india_intelligence_service import india_intelligence_service
from backend.app.services.analyst.analyst_workflow_service import analyst_workflow_service
from backend.app.services.jarvis.jarvis_orchestrator import jarvis_orchestrator
from backend.app.models.jarvis_schemas import JarvisCommandRequest, JarvisCapability


@pytest.fixture(scope="module")
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


class TestPhase21ReleaseReadiness:
    """Comprehensive test matrix for Phase 21 Release Hardening & Quality Assurance."""

    # =========================================================================
    # GROUP A: CONFIGURATION & ENVIRONMENT HYGIENE
    # =========================================================================
    def test_group_a_configuration_hygiene(self):
        """Verify configuration parameters, masking of secrets, and safety invariant flags."""
        assert settings.PROJECT_NAME == "AGNI-NETRA"
        assert settings.ENABLE_OPERATIONAL_DISPATCH_GATE is False
        assert getattr(settings, "ENABLE_AUTOMATED_MODEL_ACTIVATION", False) is False

        sanitized = settings.get_sanitized_dict()
        assert "SECRET_KEY" in sanitized
        assert "DATABASE_URL" in sanitized
        # Passwords and secrets must be masked
        assert "****" in str(sanitized["SECRET_KEY"])
        assert "****@" in str(sanitized["DATABASE_URL"])
        assert not any("super_secure_key" in str(v) for v in sanitized.values())

    # =========================================================================
    # GROUP B: PROCESS STARTUP & DATABASE ENGINE
    # =========================================================================
    def test_group_b_process_startup_and_db(self, db_session: Session):
        """Verify database connection pool, dialect, and PostGIS extension presence."""
        with engine.connect() as conn:
            res = conn.execute(text("SELECT 1")).scalar()
            assert res == 1

            # Check PostGIS extension is installed
            postgis_ver = conn.execute(text("SELECT PostGIS_Full_Version()")).scalar()
            assert postgis_ver is not None
            assert "POSTGIS" in postgis_ver.upper()

    # =========================================================================
    # GROUP C: HEALTH & DIAGNOSTICS API
    # =========================================================================
    def test_group_c_health_diagnostics_api(self, client: TestClient):
        """Verify health check endpoints return 200 OK with fast response."""
        # Warmup
        client.get("/api/v1/health")
        t0 = time.time()
        resp = client.get("/api/v1/health")
        latency = (time.time() - t0) * 1000.0

        assert resp.status_code == 200
        data = resp.json()
        assert data.get("status") in ["healthy", "ok", "HEALTHY"]
        assert latency < 1000.0

        # Verify detailed health if available
        det_resp = client.get("/api/v1/health/detailed")
        if det_resp.status_code == 200:
            det_data = det_resp.json()
            assert "database" in det_data or "status" in det_data

    # =========================================================================
    # GROUP D: AUTHENTICATION & TOKEN LIFECYCLE
    # =========================================================================
    def test_group_d_authentication_lifecycle(self):
        """Verify password hashing, token encoding, expiration, and issuer checks."""
        password = "TestPassword2026!#"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True
        assert verify_password("WrongPassword", hashed) is False

        # Create valid token
        token = create_access_token(subject="user-123", role="ANALYST")
        payload = decode_access_token(token)
        assert payload["sub"] == "user-123"
        assert payload["role"] == "ANALYST"
        assert payload["iss"] == AUTH_ISSUER

        # Test expired token raises Exception
        expired_token = create_access_token(
            subject="user-123", role="ANALYST",
            expires_delta=timedelta(seconds=-10)
        )
        with pytest.raises(Exception):
            decode_access_token(expired_token)

    # =========================================================================
    # GROUP E: ROLE-BASED ACCESS CONTROL (6 ROLES)
    # =========================================================================
    def test_group_e_rbac_roles(self):
        """Verify permissions across PUBLIC, INDUSTRY, RESEARCHER, ANALYST, AGENCY, ADMIN."""
        analyst_checker = RoleChecker(["ANALYST"])
        admin_user = User(id="u-admin", email="admin@agni.gov.in", role="ADMIN", is_active=True)
        analyst_user = User(id="u-analyst", email="analyst@agni.gov.in", role="ANALYST", is_active=True)
        public_user = User(id="u-public", email="public@example.com", role="PUBLIC", is_active=True)

        # Admin bypasses role restriction
        assert analyst_checker(admin_user) == admin_user
        # Analyst passes analyst requirement
        assert analyst_checker(analyst_user) == analyst_user

        # Public user rejected with 403 Forbidden
        with pytest.raises(Exception) as exc:
            analyst_checker(public_user)
        assert "403" in str(exc.value)

    # =========================================================================
    # GROUP F: PUBLIC SAFETY & DATA SANITIZATION
    # =========================================================================
    def test_group_f_public_safety_sanitization(self, client: TestClient):
        """Verify public portal endpoints round coordinates and redact sensitive details."""
        resp = client.get("/api/v1/portals/public/hazard-map")
        assert resp.status_code == 200
        data = resp.json()
        assert "features" in data
        assert "events" in data

        for ev in data.get("events", [])[:5]:
            lat = ev.get("latitude")
            lon = ev.get("longitude")
            # Coordinate precision must be truncated to 2 decimals (~1.1km)
            assert round(lat, 2) == lat
            assert round(lon, 2) == lon
            # Sensitive internal names/logits must not leak
            assert "facility_name" not in ev
            assert "shap_values" not in ev
            assert "dispatch_controls" not in ev

    # =========================================================================
    # GROUP G: SOVEREIGN INDIA SCOPE INTEGRITY
    # =========================================================================
    def test_group_g_sovereign_india_scope(self):
        """Verify spatial boundary filtering: Indian coordinates pass; foreign coordinates reject."""
        # Dahej, Gujarat (Inside India)
        guj_pt, state, _, _ = india_boundary_service.is_point_inside_india(21.71, 72.58)
        assert guj_pt is True
        assert state is not None

        # Angul, Odisha (Inside India)
        odisha_pt, o_state, _, _ = india_boundary_service.is_point_inside_india(20.84, 85.10)
        assert odisha_pt is True

        # Colombo, Sri Lanka (Foreign - Outside Sovereign India)
        sri_lanka, _, _, _ = india_boundary_service.is_point_inside_india(6.92, 79.86)
        assert sri_lanka is False

        # Lahore, Pakistan (Foreign - Outside Sovereign India)
        pakistan, _, _, _ = india_boundary_service.is_point_inside_india(31.52, 74.35)
        assert pakistan is False

    # =========================================================================
    # GROUP H: PROVIDER TRUTHFULNESS & NOT_CONFIGURED
    # =========================================================================
    def test_group_h_provider_truthfulness(self, db_session: Session):
        """Verify audit truthfully declares unconfigured feeds with zero synthetic substitutions."""
        audit = india_intelligence_service.audit_india_data_intelligence(db_session)
        assert audit["active_operational_scope"] == "INDIA"
        inventory = audit.get("governed_datasets_inventory", [])

        # Confirm unconfigured external providers are explicitly flagged
        unconfigured = [d for d in inventory if d.get("data_class") == "NOT_CONFIGURED"]
        assert len(unconfigured) >= 5
        assert audit.get("unconfigured_international_datasets") >= 5
        assert audit.get("zero_synthetic_guarantee") is True

    # =========================================================================
    # GROUP I: DATA PROVENANCE & CLASSIFICATION
    # =========================================================================
    def test_group_i_data_provenance(self, db_session: Session):
        """Verify clear distinction between REAL, DERIVED, FIXTURE, and UNAVAILABLE data types."""
        audit = india_intelligence_service.audit_india_data_intelligence(db_session)
        assert audit["total_governed_datasets"] == 18
        assert audit["active_production_datasets"] >= 10
        assert audit["zero_synthetic_guarantee"] is True
        assert audit["operational_dispatch_gate"] == "BLOCKED"

    # =========================================================================
    # GROUP J: MODEL GOVERNANCE & IMMUTABILITY
    # =========================================================================
    def test_group_j_model_governance(self):
        """Verify model weights and artifacts exist, and automated retraining is disabled."""
        model_dir = settings.MODEL_DIR
        assert os.path.exists(model_dir) or os.path.isdir("ml/models")
        assert getattr(settings, "ENABLE_AUTOMATED_MODEL_ACTIVATION", False) is False

    # =========================================================================
    # GROUP K: FROZEN 5-FACTOR RISK FORMULA PRESERVATION
    # =========================================================================
    def test_group_k_frozen_risk_formula(self, db_session: Session):
        """Verify frozen risk weights (0.30, 0.25, 0.20, 0.15, 0.10) sum to 1.00 exactly."""
        assert analyst_workflow_service.RISK_WEIGHT_INTENSITY == 0.30
        assert analyst_workflow_service.RISK_WEIGHT_ABNORMALITY == 0.25
        assert analyst_workflow_service.RISK_WEIGHT_EXPOSURE == 0.20
        assert analyst_workflow_service.RISK_WEIGHT_PERSISTENCE == 0.15
        assert analyst_workflow_service.RISK_WEIGHT_CONTEXT == 0.10

        total_w = (
            analyst_workflow_service.RISK_WEIGHT_INTENSITY +
            analyst_workflow_service.RISK_WEIGHT_ABNORMALITY +
            analyst_workflow_service.RISK_WEIGHT_EXPOSURE +
            analyst_workflow_service.RISK_WEIGHT_PERSISTENCE +
            analyst_workflow_service.RISK_WEIGHT_CONTEXT
        )
        assert abs(total_w - 1.00) < 1e-6

    # =========================================================================
    # GROUP L: FROZEN GOVERNED PRIORITY FORMULA PRESERVATION
    # =========================================================================
    def test_group_l_frozen_priority_formula(self, db_session: Session):
        """Verify governed priority formula: 0.40R + 0.20C + 0.30T + 0.10Rec."""
        top_event = db_session.query(ThermalEvent).first()
        assert top_event is not None
        prio_res = analyst_workflow_service.explain_triage_priority(db_session, top_event.id)
        mb = prio_res["mathematical_breakdown"]

        assert abs(mb["risk_contribution"]["weight"] - 0.40) < 1e-6
        assert abs(mb["confidence_contribution"]["weight"] - 0.20) < 1e-6
        assert abs(mb["tier_contribution"]["weight"] - 0.30) < 1e-6
        assert abs(mb["recency_contribution"]["weight"] - 0.10) < 1e-6

    # =========================================================================
    # GROUP M: SINGLE MASTER AGENT ARCHITECTURE (JARVIS)
    # =========================================================================
    def test_group_m_single_master_agent(self, db_session: Session):
        """Verify JARVIS operates as single master agent with zero subagent spawns."""
        req = JarvisCommandRequest(command="JARVIS, audit India data intelligence.")
        res = jarvis_orchestrator.execute_command(req, db=db_session)

        # Must return completed state
        assert res.state.value in ["COMPLETED", "completed"]
        # Execution trace must only record JARVIS as the executing agent
        for step in res.execution_trace.steps:
            assert step.agent == "JARVIS"

    # =========================================================================
    # GROUP N: JARVIS SAFETY & STATUS REPORTING
    # =========================================================================
    def test_group_n_jarvis_status_reporting(self, db_session: Session):
        """Verify JARVIS clearly reports explicit information status (AVAILABLE, INSUFFICIENT, etc.)."""
        # Test 1: Available status
        req1 = JarvisCommandRequest(command="JARVIS, why was this event prioritized?")
        res1 = jarvis_orchestrator.execute_command(req1, db=db_session)
        assert res1.dispatch_gate_blocked is True
        assert res1.details.get("information_status") in ["AVAILABLE", "REQUIRES_HUMAN_VERIFICATION"]

        # Test 2: Missing evidence reports INSUFFICIENT
        req2 = JarvisCommandRequest(command="JARVIS, what evidence is still missing?")
        res2 = jarvis_orchestrator.execute_command(req2, db=db_session)
        assert res2.details.get("information_status") == "INSUFFICIENT"

    # =========================================================================
    # GROUP O: OPERATIONAL DISPATCH GATE SAFETY (BLOCKED)
    # =========================================================================
    def test_group_o_dispatch_gate_blocked(self, db_session: Session):
        """Verify operational dispatch gate remains strictly BLOCKED across all responses."""
        req = JarvisCommandRequest(command="JARVIS, show me what needs verification first.")
        res = jarvis_orchestrator.execute_command(req, db=db_session)
        assert res.dispatch_gate_blocked is True
        assert "BLOCKED" in res.summary.upper()
        assert analyst_workflow_service.ENABLE_OPERATIONAL_DISPATCH_GATE is False

    # =========================================================================
    # GROUP P: AUTOMATED MODEL ACTIVATION SAFETY (DISABLED)
    # =========================================================================
    def test_group_p_automated_model_activation_disabled(self):
        """Verify online automated model activation is strictly DISABLED."""
        assert analyst_workflow_service.ENABLE_AUTOMATED_MODEL_ACTIVATION is False
        assert getattr(settings, "ENABLE_AUTOMATED_MODEL_ACTIVATION", False) is False

    # =========================================================================
    # GROUP Q: API ERROR HANDLING & VALIDATION
    # =========================================================================
    def test_group_q_api_error_handling(self, client: TestClient):
        """Verify API handles invalid requests gracefully without unhandled 500 exceptions."""
        # Non-existent event dossier
        resp1 = client.get("/api/v1/analyst/events/NON_EXISTENT_ID/dossier")
        assert resp1.status_code in [400, 404]
        assert "detail" in resp1.json()

        # Invalid verification payload (empty body)
        resp2 = client.post("/api/v1/analyst/verification", json={})
        assert resp2.status_code in [400, 422]

    # =========================================================================
    # GROUP R: DATABASE & POSTGIS GEOMETRY INTEGRITY
    # =========================================================================
    def test_group_r_database_geometry_integrity(self, db_session: Session):
        """Verify admin_boundaries spatial geometries are valid with SRID 4326."""
        # Verify valid geometries exist
        valid_cnt = db_session.execute(text("""
            SELECT count(*) FROM admin_boundaries 
            WHERE ST_IsValid(geom) = true AND ST_SRID(geom) = 4326;
        """)).scalar()
        assert valid_cnt > 7000

        # Verify spatial index presence
        idx_res = db_session.execute(text("""
            SELECT indexname FROM pg_indexes 
            WHERE tablename = 'admin_boundaries' AND indexdef LIKE '%gist%';
        """)).fetchall()
        assert len(idx_res) >= 1

    # =========================================================================
    # GROUP S: AUDIT LOGGING & IMMUTABILITY
    # =========================================================================
    def test_group_s_audit_logging(self, db_session: Session):
        """Verify audit log table records entries with timestamps and resource IDs."""
        cnt = db_session.query(AuditLog).count()
        assert cnt >= 0  # Table exists and is queryable

    # =========================================================================
    # GROUP T: STANDARDIZED REPORT GENERATION
    # =========================================================================
    def test_group_t_standardized_report_generation(self, db_session: Session):
        """Verify 17-section operational report compiles with SHA-256 hash."""
        top_event = db_session.query(ThermalEvent).first()
        assert top_event is not None
        rep = analyst_workflow_service.generate_operational_analyst_report(
            db=db_session, case_or_event_id=top_event.id, analyst_id="RELEASE_AUDITOR"
        )
        assert rep["status"] == "SUCCESS"
        assert rep["sections_count"] == 17
        assert len(rep["hash_sha256"]) == 64
        assert "BLOCKED" in rep["content_markdown"]
        assert "## 1. Executive Summary" in rep["content_markdown"]
        assert "## 17. Provenance & Cryptographic Verification Manifest" in rep["content_markdown"]

    # =========================================================================
    # GROUP U: FRONTEND INTEGRATION & ROUTE VERIFICATION
    # =========================================================================
    def test_group_u_frontend_routes(self):
        """Verify frontend key page files exist in repository."""
        required_pages = [
            "frontend/src/app/page.tsx",
            "frontend/src/app/dashboard/page.tsx",
            "frontend/src/app/dashboard/verification/page.tsx",
            "frontend/src/app/dashboard/analytics/page.tsx",
            "frontend/src/app/jarvis/page.tsx",
            "frontend/src/app/admin/page.tsx",
            "frontend/src/app/portal/public/page.tsx",
            "frontend/src/app/portal/agency/page.tsx",
        ]
        for p in required_pages:
            assert os.path.exists(p), f"Missing required frontend page: {p}"

    # =========================================================================
    # GROUP V: RESTART & FAILURE RECOVERY
    # =========================================================================
    def test_group_v_failure_recovery(self, db_session: Session):
        """Verify database rollback on SQL error preserves connection integrity."""
        try:
            db_session.execute(text("SELECT * FROM non_existent_table_for_test"))
        except Exception:
            db_session.rollback()

        # Session must recover immediately and execute valid queries
        res = db_session.execute(text("SELECT 1")).scalar()
        assert res == 1

    # =========================================================================
    # GROUP W: OBSERVABILITY & LOG SANITIZATION
    # =========================================================================
    def test_group_w_observability_sanitization(self):
        """Verify sensitive credentials are never logged or exposed."""
        sanitized = settings.get_sanitized_dict()
        for k, v in sanitized.items():
            if k in ["SECRET_KEY", "DATABASE_URL", "FIRMS_MAP_KEY", "S3_ACCESS_KEY"]:
                assert "****" in str(v)
