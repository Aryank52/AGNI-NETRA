"""
AGNI-NETRA — JARVIS Investigation Workspace & Persistent Intelligence State Test Suite
Validates:
1. Investigation Workspace Model & Manager CRUD
2. State Machine Transitions (CREATED -> ACTIVE -> REQUIRES_HUMAN_REVIEW -> CLOSED)
3. Structured Epistemic Evidence Ingestion & Freshness Tracking
4. Primary 7-Step Acceptance Scenario (continuous multi-turn investigation flow)
5. Secondary Gujarat 3-Event Scenario (Cohort comparison & Candidate targeting)
6. Ambiguous Reference Clarification Guarding
7. Evidence Reuse & Safe Force-Refresh
8. Safe Closure Audit Warnings
9. RBAC & Cross-User Isolation
10. REST API Workspace Endpoints
"""

import pytest
import uuid
from typing import Any, Dict
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from backend.app.core.database import SessionLocal
from backend.app.main import app
from backend.app.models.domain import InvestigationWorkspace, ThermalEvent
from backend.app.models.jarvis_schemas import (
    CommandIntent, JarvisCommandRequest, StepStatus, InvestigationStatus, EpistemicType
)
from backend.app.services.jarvis.jarvis_workspace import workspace_manager
from backend.app.services.jarvis.jarvis_orchestrator import master_orchestrator
from backend.app.services.jarvis.jarvis_command_interpreter import command_interpreter


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()


@pytest.fixture(scope="module")
def api_client():
    return TestClient(app)


def get_ws_dict(res: Any) -> Dict[str, Any]:
    """Helper to access workspace dictionary regardless of dict or Pydantic model representation."""
    if not res or res.investigation_workspace is None:
        return {}
    if isinstance(res.investigation_workspace, dict):
        return res.investigation_workspace
    if hasattr(res.investigation_workspace, "model_dump"):
        return res.investigation_workspace.model_dump()
    return vars(res.investigation_workspace)


# =========================================================================
# 1. Workspace Service & State Machine Unit Tests
# =========================================================================

class TestJarvisWorkspaceManager:
    """Validates core workspace CRUD, state machine transitions, and evidence storage."""

    def test_create_and_retrieve_workspace(self, db_session: Session):
        session_id = "test-ws-unit-01"
        ws = workspace_manager.get_or_create_workspace(
            db_session,
            session_id=session_id,
            target_event_id="827",
            primary_objective="Test unit investigation",
            user_id="analyst-1",
            user_role="ANALYST"
        )
        assert ws is not None
        assert ws.investigation_id.startswith("INV-")
        assert ws.session_id == session_id
        assert ws.target_event_id == "827"
        assert ws.status in [InvestigationStatus.CREATED.value, InvestigationStatus.ACTIVE.value, "CREATED", "ACTIVE"]

        # Retrieve
        fetched, err = workspace_manager.get_workspace(db_session, ws.investigation_id)
        assert fetched is not None
        assert fetched.investigation_id == ws.investigation_id

    def test_state_transitions(self, db_session: Session):
        ws = workspace_manager.get_or_create_workspace(
            db_session,
            session_id="test-ws-transitions",
            target_event_id="827"
        )
        inv_id = ws.investigation_id

        # ACTIVE
        updated = workspace_manager.update_status(db_session, inv_id, InvestigationStatus.ACTIVE)
        assert updated.status == InvestigationStatus.ACTIVE.value

        # ANALYZING
        updated = workspace_manager.update_status(db_session, inv_id, InvestigationStatus.ANALYZING)
        assert updated.status == InvestigationStatus.ANALYZING.value

        # REQUIRES_HUMAN_REVIEW
        updated = workspace_manager.update_status(
            db_session, inv_id, InvestigationStatus.REQUIRES_HUMAN_REVIEW, note="Risk exceeds threshold"
        )
        assert updated.status == InvestigationStatus.REQUIRES_HUMAN_REVIEW.value

        # COMPLETED
        updated = workspace_manager.update_status(db_session, inv_id, InvestigationStatus.COMPLETED)
        assert updated.status == InvestigationStatus.COMPLETED.value

    def test_epistemic_evidence_ingestion(self, db_session: Session):
        ws = workspace_manager.get_or_create_workspace(
            db_session,
            session_id="test-ws-evidence",
            target_event_id="827"
        )
        inv_id = ws.investigation_id

        # Add Fact
        workspace_manager.add_structured_evidence(
            db_session, inv_id,
            evidence_type="PEAK_FRP",
            source="NASA_FIRMS_VIIRS",
            value=145.2,
            epistemic_type=EpistemicType.FACT,
            confidence=0.95
        )

        # Add Model Output
        workspace_manager.add_structured_evidence(
            db_session, inv_id,
            evidence_type="PREDICTED_CLASS",
            source="XGBOOST_V3",
            value="INDUSTRIAL_FLARING",
            epistemic_type=EpistemicType.MODEL_OUTPUT,
            confidence=0.91
        )

        # Add Derived Analysis
        workspace_manager.add_structured_evidence(
            db_session, inv_id,
            evidence_type="SHAP_IMPORTANCE",
            source="TREE_SHAP",
            value={"top_driver": "facility_distance_m", "attribution": 0.42},
            epistemic_type=EpistemicType.DERIVED_ANALYSIS
        )

        # Add Recommendation
        workspace_manager.add_structured_evidence(
            db_session, inv_id,
            evidence_type="HITL_RECOMMENDATION",
            source="JARVIS_POLICY_ENGINE",
            value="HUMAN_VERIFICATION_REQUIRED",
            epistemic_type=EpistemicType.RECOMMENDATION
        )

        # Verify evidence store
        evidence_list = workspace_manager.get_evidence_store(db_session, inv_id)
        assert len(evidence_list) >= 4
        epistemic_types = {e["epistemic_type"] for e in evidence_list}
        assert "FACT" in epistemic_types
        assert "MODEL_OUTPUT" in epistemic_types
        assert "DERIVED_ANALYSIS" in epistemic_types
        assert "RECOMMENDATION" in epistemic_types

    def test_evidence_freshness_and_staleness(self, db_session: Session):
        ws = workspace_manager.get_or_create_workspace(
            db_session,
            session_id=f"test-ws-freshness-{uuid.uuid4().hex[:8]}",
            target_event_id="827"
        )
        inv_id = ws.investigation_id

        # Fresh initially
        assert workspace_manager.is_evidence_fresh(ws, max_age_seconds=300) is True

        # Ingest item
        workspace_manager.add_structured_evidence(
            db_session, inv_id,
            evidence_type="TEST_METRIC",
            source="TEST",
            value=42,
            epistemic_type=EpistemicType.FACT
        )

        # Mark stale
        workspace_manager.mark_evidence_stale(db_session, inv_id)
        stale_ws, _ = workspace_manager.get_workspace(db_session, inv_id)
        for item in stale_ws.structured_evidence:
            assert item.get("freshness_status") == "STALE"

    def test_safe_closure_audit_warnings(self, db_session: Session):
        ws = workspace_manager.get_or_create_workspace(
            db_session,
            session_id="test-ws-closure-warning",
            target_event_id="827"
        )
        inv_id = ws.investigation_id

        # Set high risk and pending verification
        workspace_manager.update_intelligence_dimension(
            db_session, inv_id,
            risk_summary={"total_risk_score": 85, "risk_level": "CRITICAL"},
            verification_status="PENDING_VERIFICATION",
            open_questions=[{"question": "Confirm containment status with site manager"}]
        )

        # Close workspace
        closed_ws, err, warnings = workspace_manager.close_workspace(db_session, inv_id, user_role="ANALYST")
        assert closed_ws.status == InvestigationStatus.CLOSED.value
        assert len(closed_ws.warnings) >= 2
        warning_str = " ".join(closed_ws.warnings).lower()
        assert "verification" in warning_str or "unverified" in warning_str
        assert "open question" in warning_str or "unresolved question" in warning_str

    def test_rbac_cross_user_denial(self, db_session: Session):
        sess_id = f"test-ws-rbac-{uuid.uuid4().hex[:6]}"
        ws = workspace_manager.get_or_create_workspace(
            db_session,
            session_id=sess_id,
            target_event_id="827",
            user_id="analyst-alpha",
            user_role="ANALYST"
        )

        # Analyst Alpha can access
        assert workspace_manager.check_access(ws, user_id="analyst-alpha", user_role="ANALYST") is True

        # Analyst Beta (different user, non-admin) cannot access
        assert workspace_manager.check_access(ws, user_id="analyst-beta", user_role="ANALYST") is False

        # Commander or Admin can access (governance role override)
        assert workspace_manager.check_access(ws, user_id="admin-1", user_role="ADMIN") is True
        assert workspace_manager.check_access(ws, user_id="cmdr-1", user_role="COMMANDER") is True


# =========================================================================
# 2. Primary 7-Step Continuous Investigation Flow
# =========================================================================

class TestJarvisPrimary7StepAcceptance:
    """
    Validates the primary 7-step continuous investigation scenario:
    1. 'JARVIS, investigate Event 827.'
    2. 'JARVIS, explain why Event 827 has high risk.'
    3. 'JARVIS, compare Event 827 with similar events.'
    4. 'JARVIS, which case is strongest?'
    5. 'JARVIS, show the strongest evidence for that conclusion.'
    6. 'JARVIS, does it require verification?'
    7. 'JARVIS, generate an investigation dossier.'
    """

    def test_primary_7_step_continuous_flow(self, db_session: Session):
        session_id = "test-primary-7step-session"

        # -------------------------------------------------------------
        # Step 1: Investigate Event 827
        # -------------------------------------------------------------
        r1 = master_orchestrator.execute_command(
            db_session,
            JarvisCommandRequest(command="JARVIS, investigate Event 827.", session_id=session_id),
            user_role="ANALYST"
        )
        assert r1.execution_trace.status == StepStatus.COMPLETED
        assert r1.execution_trace.target_event in ["827", "EVT-827"]
        assert r1.investigation_id is not None
        assert r1.investigation_workspace is not None
        ws1 = get_ws_dict(r1)
        assert ws1.get("target_event_id") in ["827", "EVT-827"]
        assert ws1.get("status") in [
            InvestigationStatus.ACTIVE.value, InvestigationStatus.ANALYZING.value,
            InvestigationStatus.REQUIRES_HUMAN_REVIEW.value, "ACTIVE", "ANALYZING", "REQUIRES_HUMAN_REVIEW"
        ]
        inv_id = r1.investigation_id

        # Verify structured evidence was populated
        assert len(ws1.get("structured_evidence", [])) > 0

        # -------------------------------------------------------------
        # Step 2: Explain why Event 827 has high risk (Evidence Reuse)
        # -------------------------------------------------------------
        r2 = master_orchestrator.execute_command(
            db_session,
            JarvisCommandRequest(
                command="JARVIS, explain why Event 827 has high risk.",
                session_id=session_id,
                investigation_id=inv_id
            ),
            user_role="ANALYST"
        )
        assert r2.execution_trace.status == StepStatus.COMPLETED
        assert r2.investigation_id == inv_id
        assert "risk_decomposition" in r2.details
        assert r2.fused_evidence.risk is not None

        # Evidence reuse check: Tool calls shouldn't re-run full database scans
        tools_run_2 = [s.tool for s in r2.execution_trace.steps if s.tool]
        assert "tool_generate_investigation_dossier" not in tools_run_2

        # -------------------------------------------------------------
        # Step 3: Compare Event 827 with similar events
        # -------------------------------------------------------------
        r3 = master_orchestrator.execute_command(
            db_session,
            JarvisCommandRequest(
                command="JARVIS, compare Event 827 with similar events.",
                session_id=session_id,
                investigation_id=inv_id
            ),
            user_role="ANALYST"
        )
        assert r3.execution_trace.status == StepStatus.COMPLETED
        assert r3.investigation_id == inv_id
        assert "comparison" in r3.details
        matrix = r3.details["comparison"].get("comparison_matrix", [])
        assert len(matrix) >= 2

        # Verify candidate set is populated in workspace
        ws3 = get_ws_dict(r3)
        assert ws3.get("candidate_set") is not None
        assert len(ws3.get("candidate_set", [])) >= 2
        candidate_codes = [c.get("candidate_code") for c in ws3.get("candidate_set", [])]
        assert "Candidate A" in candidate_codes
        assert "Candidate B" in candidate_codes

        # -------------------------------------------------------------
        # Step 4: Which case is strongest?
        # -------------------------------------------------------------
        r4 = master_orchestrator.execute_command(
            db_session,
            JarvisCommandRequest(
                command="JARVIS, which case is strongest?",
                session_id=session_id,
                investigation_id=inv_id
            ),
            user_role="ANALYST"
        )
        assert r4.execution_trace.status == StepStatus.COMPLETED
        assert r4.investigation_id == inv_id
        assert "comparison" in r4.details
        winner = r4.details["comparison"].get("winner")
        assert winner is not None
        ws4 = get_ws_dict(r4)
        assert ws4.get("selected_candidate") is not None

        # -------------------------------------------------------------
        # Step 5: Show the strongest evidence for that conclusion
        # -------------------------------------------------------------
        r5 = master_orchestrator.execute_command(
            db_session,
            JarvisCommandRequest(
                command="JARVIS, show the strongest evidence for that conclusion.",
                session_id=session_id,
                investigation_id=inv_id
            ),
            user_role="ANALYST"
        )
        assert r5.execution_trace.status == StepStatus.COMPLETED
        assert r5.investigation_id == inv_id
        assert r5.objective.resolved_from_context is True
        assert r5.fused_evidence is not None

        # -------------------------------------------------------------
        # Step 6: Does it require verification?
        # -------------------------------------------------------------
        r6 = master_orchestrator.execute_command(
            db_session,
            JarvisCommandRequest(
                command="JARVIS, does it require verification?",
                session_id=session_id,
                investigation_id=inv_id
            ),
            user_role="ANALYST"
        )
        assert r6.execution_trace.status == StepStatus.COMPLETED
        assert r6.investigation_id == inv_id
        assert "verification_assessment" in r6.details
        assessment = r6.details["verification_assessment"]
        assert "verification_required" in assessment
        ws6 = get_ws_dict(r6)
        assert ws6.get("verification_status") is not None

        # If risk >= 60, status must transition to REQUIRES_HUMAN_REVIEW
        if assessment["verification_required"]:
            assert ws6.get("status") in [InvestigationStatus.REQUIRES_HUMAN_REVIEW.value, "REQUIRES_HUMAN_REVIEW"]

        # -------------------------------------------------------------
        # Step 7: Generate an investigation dossier
        # -------------------------------------------------------------
        r7 = master_orchestrator.execute_command(
            db_session,
            JarvisCommandRequest(
                command="JARVIS, generate an investigation dossier.",
                session_id=session_id,
                investigation_id=inv_id
            ),
            user_role="ANALYST"
        )
        assert r7.execution_trace.status == StepStatus.COMPLETED
        assert r7.investigation_id == inv_id
        assert "pdf_export" in r7.details
        assert r7.details["pdf_export"].get("is_valid_pdf") is True
        ws7 = get_ws_dict(r7)
        assert ws7.get("report_status") in ["READY", "GENERATED"]
        assert ws7.get("report_file_path") is not None


# =========================================================================
# 3. Secondary Multi-Event Scenario: Gujarat Cohort Analysis
# =========================================================================

class TestJarvisGujaratCohortScenario:
    """
    Validates multi-event cohort evaluation in Gujarat near industrial facilities:
    1. Find/compare events in Gujarat near facilities.
    2. 'Which candidate is most severe?' -> Identifies winner.
    3. 'Generate a dossier for Candidate B.' -> Resolves Candidate B directly.
    """

    def test_gujarat_cohort_and_candidate_targeting(self, db_session: Session):
        session_id = "test-gujarat-cohort-session"

        # Step 1: Compare thermal events in Gujarat
        r1 = master_orchestrator.execute_command(
            db_session,
            JarvisCommandRequest(
                command="JARVIS, compare the critical thermal events in Gujarat near industrial facilities.",
                session_id=session_id
            ),
            user_role="ANALYST"
        )
        assert r1.execution_trace.status == StepStatus.COMPLETED
        assert r1.investigation_id is not None
        inv_id = r1.investigation_id
        ws1 = get_ws_dict(r1)
        assert ws1.get("candidate_set") is not None
        assert len(ws1.get("candidate_set", [])) >= 2

        # Step 2: Which candidate is most severe?
        r2 = master_orchestrator.execute_command(
            db_session,
            JarvisCommandRequest(
                command="JARVIS, which candidate is most severe?",
                session_id=session_id,
                investigation_id=inv_id
            ),
            user_role="ANALYST"
        )
        assert r2.execution_trace.status == StepStatus.COMPLETED
        assert r2.investigation_id == inv_id
        assert r2.details.get("comparison", {}).get("winner") is not None

        # Step 3: Generate a dossier for Candidate B specifically
        r3 = master_orchestrator.execute_command(
            db_session,
            JarvisCommandRequest(
                command="JARVIS, generate a dossier for Candidate B.",
                session_id=session_id,
                investigation_id=inv_id
            ),
            user_role="ANALYST"
        )
        assert r3.execution_trace.status == StepStatus.COMPLETED
        assert r3.investigation_id == inv_id
        assert "pdf_export" in r3.details
        assert r3.details["pdf_export"].get("is_valid_pdf") is True


# =========================================================================
# 4. Ambiguous Candidate Clarification Guarding
# =========================================================================

class TestJarvisCandidateClarificationGuard:
    """Validates safe handling of ambiguous cohort references without premature hallucination."""

    def test_unselected_candidate_clarification(self, db_session: Session):
        session_id = "test-ambiguous-candidate-session"

        # Step 1: Setup comparison with candidates
        r1 = master_orchestrator.execute_command(
            db_session,
            JarvisCommandRequest(
                command="JARVIS, compare the critical thermal events in Gujarat.",
                session_id=session_id
            ),
            user_role="ANALYST"
        )
        inv_id = r1.investigation_id

        # Step 2: If user asks for 'that candidate' without selecting or ranking one:
        req_clarify = JarvisCommandRequest(
            command="JARVIS, show evidence for that case.",
            session_id=session_id,
            investigation_id=inv_id
        )
        res = master_orchestrator.execute_command(db_session, req_clarify, user_role="ANALYST")
        
        # If ambiguous, prompt must present options or resolve to target safely
        assert res.execution_trace.status in [StepStatus.COMPLETED, StepStatus.BLOCKED]
        if "CLARIFICATION REQUIRED" in res.summary:
            assert "Candidate" in res.summary


# =========================================================================
# 5. Workspace Force-Refresh & Safe Closure Commands
# =========================================================================

class TestJarvisWorkspaceLifecycleCommands:
    """Validates operational lifecycle commands: refresh and close."""

    def test_refresh_evidence_command(self, db_session: Session):
        session_id = "test-refresh-session"

        # Step 1: Initialize
        r1 = master_orchestrator.execute_command(
            db_session,
            JarvisCommandRequest(command="JARVIS, investigate Event 827.", session_id=session_id),
            user_role="ANALYST"
        )
        inv_id = r1.investigation_id

        # Step 2: Force refresh
        r2 = master_orchestrator.execute_command(
            db_session,
            JarvisCommandRequest(
                command="JARVIS, refresh the evidence for this investigation.",
                session_id=session_id,
                investigation_id=inv_id
            ),
            user_role="ANALYST"
        )
        assert r2.execution_trace.status == StepStatus.COMPLETED
        assert "REFRESHED" in r2.summary.upper() or "REFRESH" in r2.summary.upper()
        assert r2.investigation_id == inv_id

    def test_close_investigation_command(self, db_session: Session):
        session_id = "test-close-session"

        # Step 1: Initialize
        r1 = master_orchestrator.execute_command(
            db_session,
            JarvisCommandRequest(command="JARVIS, investigate Event 827.", session_id=session_id),
            user_role="ANALYST"
        )
        inv_id = r1.investigation_id

        # Step 2: Close
        r2 = master_orchestrator.execute_command(
            db_session,
            JarvisCommandRequest(
                command="JARVIS, close this investigation.",
                session_id=session_id,
                investigation_id=inv_id
            ),
            user_role="ANALYST"
        )
        assert r2.execution_trace.status == StepStatus.COMPLETED
        ws2 = get_ws_dict(r2)
        assert ws2.get("status") in [InvestigationStatus.CLOSED.value, "CLOSED"]
        assert "CLOSED" in r2.summary.upper()


# =========================================================================
# 6. REST API Endpoints Integration Tests
# =========================================================================

class TestJarvisWorkspaceRestApi:
    """Validates HTTP REST endpoints for investigation workspaces."""

    def test_list_and_get_investigations(self, api_client: TestClient, db_session: Session):
        # Create an investigation via orchestrator
        r = master_orchestrator.execute_command(
            db_session,
            JarvisCommandRequest(command="JARVIS, investigate Event 827.", session_id="test-api-session"),
            user_role="ANALYST"
        )
        inv_id = r.investigation_id

        # GET /api/v1/jarvis/investigations
        resp = api_client.get("/api/v1/jarvis/investigations")
        assert resp.status_code == 200
        items = resp.json()
        assert isinstance(items, list)
        assert any(item["investigation_id"] == inv_id for item in items)

        # GET /api/v1/jarvis/investigations/{id}
        resp_single = api_client.get(f"/api/v1/jarvis/investigations/{inv_id}")
        assert resp_single.status_code == 200
        single_data = resp_single.json()
        assert single_data["investigation_id"] == inv_id

        # GET /api/v1/jarvis/investigations/{id}/evidence
        resp_ev = api_client.get(f"/api/v1/jarvis/investigations/{inv_id}/evidence")
        assert resp_ev.status_code == 200
        ev_data = resp_ev.json()
        assert isinstance(ev_data, dict)
        assert "structured_evidence" in ev_data
        assert isinstance(ev_data["structured_evidence"], list)
        assert len(ev_data["structured_evidence"]) > 0

        # POST /api/v1/jarvis/investigations/{id}/close
        resp_close = api_client.post(f"/api/v1/jarvis/investigations/{inv_id}/close")
        assert resp_close.status_code == 200
        close_data = resp_close.json()
        assert close_data["status"] == "CLOSED"
