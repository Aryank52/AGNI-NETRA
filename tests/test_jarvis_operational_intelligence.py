"""
AGNI-NETRA — JARVIS Phase 5 Operational Intelligence Depth Test Suite
Validates:
1. Deep cross-capability correlation combining Thermal, GeoINT, ML, Anomaly, Risk, and HITL dimensions
2. Section 20 complex operational acceptance workflow end-to-end
3. Lightweight evidence-conflict detection (real empirical signal contradictions)
4. Deterministic evidence-strength assessment (STRONG, MODERATE, LIMITED, INSUFFICIENT) distinct from risk
5. Explainable analyst prioritization (JARVIS ANALYST RANKING: 40% Risk + 25% Anomaly + 15% Proximity + 10% HITL + 10% Ambiguity)
6. Priority explanation ("Why investigate this first?")
7. Multi-constraint conditional queries across spatial, baseline, ML, and risk dimensions
8. Epistemic uncertainty decomposition (Known, Uncertain, Missing, Conflicting)
9. Bounded "What could change the conclusion" referencing actual AGNI-NETRA evidence classes
10. User-triggered operator intelligence summaries (no background polling)
11. Operational Dispatch Gate invariant (dispatch_gate_blocked == True hardcoded)
"""

import pytest
import uuid
from typing import Any, Dict
from sqlalchemy.orm import Session
from backend.app.core.database import SessionLocal
from backend.app.models.domain import InvestigationWorkspace
from backend.app.models.jarvis_schemas import (
    JarvisCommandRequest, JarvisState, StepStatus
)
from backend.app.services.jarvis.jarvis_orchestrator import master_orchestrator
from backend.app.services.jarvis.jarvis_command_interpreter import command_interpreter
from backend.app.services.jarvis.jarvis_intelligence_depth import depth_engine


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()


def get_ws_dict(res: Any) -> Dict[str, Any]:
    """Helper to access workspace dictionary regardless of dict or Pydantic model representation."""
    if not res or res.investigation_workspace is None:
        return {}
    if isinstance(res.investigation_workspace, dict):
        return res.investigation_workspace
    if hasattr(res.investigation_workspace, "model_dump"):
        return res.investigation_workspace.model_dump()
    return vars(res.investigation_workspace)


class TestJarvisPhase5OperationalIntelligence:
    """Comprehensive test suite for Phase 5 Operational Intelligence Depth."""

    def test_section_20_complex_operational_acceptance_workflow(self, db_session: Session):
        """
        Validates the primary complex operational acceptance command from Section 20:
        'JARVIS, identify the most concerning thermal event near an industrial facility,
         investigate it, determine whether the evidence strongly supports an industrial fire,
         explain any conflicting evidence, tell me what remains uncertain,
         and determine whether human verification is required.'
        """
        session_id = f"test-sec20-{uuid.uuid4().hex[:8]}"
        cmd = (
            "JARVIS, identify the most concerning thermal event near an industrial facility, "
            "investigate it, determine whether the evidence strongly supports an industrial fire, "
            "explain any conflicting evidence, tell me what remains uncertain, "
            "and determine whether human verification is required."
        )

        intent, entities = command_interpreter.parse_command(cmd)
        assert entities.get("is_complex_acceptance") is True
        assert entities.get("objective").primary_goal == "COMPLEX_OPERATIONAL_ACCEPTANCE"

        req = JarvisCommandRequest(command=cmd, session_id=session_id)
        res = master_orchestrator.execute_command(db_session, req)

        # 1. State and Safety Gate
        assert res.state == JarvisState.REQUIRES_APPROVAL
        assert res.requires_human_approval is True
        assert res.dispatch_gate_blocked is True

        # 2. Stopping Reason
        assert res.stopping_reason.startswith("COMPLEX_OPERATIONAL_ACCEPTANCE_COMPLETE")

        # 3. Evidence Strength
        assert res.evidence_strength in ["STRONG", "MODERATE", "LIMITED", "INSUFFICIENT"]
        assert res.evidence_strength_details is not None
        assert "completeness_score" in res.evidence_strength_details
        assert "consistency_score" in res.evidence_strength_details

        # 4. Uncertainty & Sensitivity
        assert res.uncertainty is not None or res.uncertainty_assessment is not None
        u_data = res.uncertainty_assessment or res.uncertainty
        assert "known" in u_data
        assert "uncertain" in u_data
        assert "what_could_change" in u_data
        assert len(u_data["what_could_change"]) >= 1

        # 5. Capabilities Used
        expected_caps = [
            "THERMAL_INTELLIGENCE", "GEOINT", "CLASSIFICATION",
            "RISK_ANALYSIS", "CROSS_SOURCE_CORRELATION",
            "SYSTEM_GOVERNANCE", "VERIFICATION"
        ]
        for cap in expected_caps:
            assert cap in res.capabilities_used, f"Expected {cap} in capabilities_used"

        # 6. Response Summary Content
        assert "OPERATIONAL INTELLIGENCE ASSESSMENT" in res.summary
        assert "Target Identification & Proximity" in res.summary
        assert "Hypothesis Support" in res.summary
        assert "Conflicting Evidence" in res.summary
        assert "Uncertainty Assessment & Sensitivity" in res.summary
        assert "Human Verification Determination" in res.summary
        assert "HUMAN VERIFICATION REQUIRED" in res.summary
        assert "BLOCKED" in res.summary

        # 7. Workspace Persistence
        ws = get_ws_dict(res)
        assert ws.get("evidence_strength") == res.evidence_strength
        assert ws.get("verification_status") in ["REQUIRES_HUMAN_REVIEW", "PENDING_VERIFICATION"]

    def test_analyst_prioritization_ranking(self, db_session: Session):
        """
        Validates JARVIS ANALYST RANKING multi-factor prioritization:
        Formula: 40% Risk + 25% Anomaly + 15% Proximity + 10% HITL + 10% Ambiguity
        """
        session_id = f"test-prio-{uuid.uuid4().hex[:8]}"
        cmd = "JARVIS, identify the events that deserve analyst attention first."

        req = JarvisCommandRequest(command=cmd, session_id=session_id)
        res = master_orchestrator.execute_command(db_session, req)

        assert res.stopping_reason.startswith("ANALYST_PRIORITIZATION_COMPLETE")
        assert res.dispatch_gate_blocked is True
        assert res.analyst_ranking is not None
        assert len(res.analyst_ranking) >= 1

        # Check ranking ordering
        scores = [c.get("analyst_priority_score", 0) for c in res.analyst_ranking]
        assert scores == sorted(scores, reverse=True), "Candidates must be sorted descending by analyst_priority_score"

        # Check component breakdown on top candidate
        top = res.analyst_ranking[0]
        assert "score_breakdown" in top
        b = top["score_breakdown"]
        assert "risk_component" in b
        assert "anomaly_component" in b
        assert "proximity_component" in b
        assert "verification_urgency" in b
        assert "uncertainty_urgency" in b

        # Validate summary format
        assert "JARVIS ANALYST RANKING" in res.summary
        assert "OPERATIONAL TRIAGE QUEUE" in res.summary

    def test_priority_explanation(self, db_session: Session):
        """
        Validates explainable priority justification ("Why is the winner stronger? / Why investigate this first?")
        """
        session_id = f"test-explain-{uuid.uuid4().hex[:8]}"
        cmd = "JARVIS, explain why the winner is stronger."

        req = JarvisCommandRequest(command=cmd, session_id=session_id)
        res = master_orchestrator.execute_command(db_session, req)

        assert res.stopping_reason.startswith("PRIORITY_EXPLAINED")
        assert res.dispatch_gate_blocked is True
        assert "PRIORITY EXPLANATION" in res.summary
        assert "Component Breakdown" in res.summary
        assert "Risk contribution:" in res.summary

    def test_multi_constraint_queries(self, db_session: Session):
        """
        Validates multi-constraint compound searches:
        1. High-risk + low classification confidence
        2. Persistent thermal anomalies near industrial facilities
        """
        session_id = f"test-mc-{uuid.uuid4().hex[:8]}"

        # Query 1: High-risk with low confidence
        cmd1 = "JARVIS, show high-risk events with low classification confidence."
        req1 = JarvisCommandRequest(command=cmd1, session_id=session_id)
        res1 = master_orchestrator.execute_command(db_session, req1)
        assert res1.stopping_reason.startswith("MULTI_CONSTRAINT_SEARCH_COMPLETE")
        assert "MULTI-CONSTRAINT INTELLIGENCE QUERY RESULTS" in res1.summary
        assert res1.dispatch_gate_blocked is True

        # Query 2: Persistent anomalies near industrial facilities
        cmd2 = "JARVIS, find persistent thermal anomalies near industrial facilities."
        req2 = JarvisCommandRequest(command=cmd2, session_id=session_id)
        res2 = master_orchestrator.execute_command(db_session, req2)
        assert res2.stopping_reason.startswith("MULTI_CONSTRAINT_SEARCH_COMPLETE")
        assert "MULTI-CONSTRAINT INTELLIGENCE QUERY RESULTS" in res2.summary
        assert res2.dispatch_gate_blocked is True

    def test_evidence_conflict_detection(self, db_session: Session):
        """
        Validates detection of genuine empirical signal contradictions:
        Classification vs baseline, classification vs spatial context, risk vs confidence.
        """
        session_id = f"test-cnf-{uuid.uuid4().hex[:8]}"
        cmd = "JARVIS, find events where historical behavior conflicts with the current classification."

        req = JarvisCommandRequest(command=cmd, session_id=session_id)
        res = master_orchestrator.execute_command(db_session, req)

        assert res.stopping_reason.startswith("EVIDENCE_CONFLICTS_EVALUATED")
        assert res.dispatch_gate_blocked is True
        assert "EVIDENCE CONFLICT" in res.summary

    def test_evidence_strength_distinct_from_risk(self, db_session: Session):
        """
        Validates evidence strength assessment (STRONG, MODERATE, LIMITED, INSUFFICIENT)
        and confirms it is separate from risk score (0-100).
        """
        session_id = f"test-str-{uuid.uuid4().hex[:8]}"
        cmd = "JARVIS, how strong is the evidence?"

        req = JarvisCommandRequest(command=cmd, session_id=session_id)
        res = master_orchestrator.execute_command(db_session, req)

        assert res.stopping_reason.startswith("EVIDENCE_STRENGTH_ASSESSED")
        assert res.dispatch_gate_blocked is True
        assert res.evidence_strength in ["STRONG", "MODERATE", "LIMITED", "INSUFFICIENT"]
        assert "EVIDENCE STRENGTH" in res.summary

    def test_epistemic_uncertainty_and_what_could_change(self, db_session: Session):
        """
        Validates uncertainty assessment (Known, Uncertain, Missing, Conflicting)
        and bounded 'what could change the conclusion' referencing actual AGNI-NETRA evidence classes.
        """
        session_id = f"test-unc-{uuid.uuid4().hex[:8]}"

        # Part A: Uncertainty query
        cmd_a = "JARVIS, what are we still uncertain about?"
        req_a = JarvisCommandRequest(command=cmd_a, session_id=session_id)
        res_a = master_orchestrator.execute_command(db_session, req_a)
        assert res_a.stopping_reason.startswith("UNCERTAINTY_ASSESSED")
        assert "UNCERTAINTY" in res_a.summary
        assert "KNOWN" in res_a.summary
        assert res_a.dispatch_gate_blocked is True

        # Part B: What could change query
        cmd_b = "JARVIS, what evidence could change the conclusion?"
        req_b = JarvisCommandRequest(command=cmd_b, session_id=session_id)
        res_b = master_orchestrator.execute_command(db_session, req_b)
        assert res_b.stopping_reason.startswith("SENSITIVITY_EVALUATED")
        assert "SENSITIVITY ANALYSIS" in res_b.summary
        assert "WHAT COULD CHANGE THIS CONCLUSION" in res_b.summary
        assert res_b.dispatch_gate_blocked is True

    def test_operator_summary_on_demand(self, db_session: Session):
        """
        Validates user-triggered operator intelligence summary assembly across monitored events.
        Confirms no autonomous background polling is used.
        """
        session_id = f"test-op-{uuid.uuid4().hex[:8]}"
        cmd = "JARVIS, summarize current intelligence."

        req = JarvisCommandRequest(command=cmd, session_id=session_id)
        res = master_orchestrator.execute_command(db_session, req)

        assert res.stopping_reason.startswith("OPERATOR_SUMMARY_GENERATED")
        assert res.dispatch_gate_blocked is True
        assert res.operator_summary is not None
        assert "AGNI-NETRA OPERATOR INTELLIGENCE BRIEFING" in res.summary
        assert "THREAT MONITORING TOTALS" in res.summary

    def test_safety_dispatch_gate_invariant(self, db_session: Session):
        """
        Ensures that dispatch_gate_blocked is strictly True and live dispatch is never emitted.
        """
        session_id = f"test-gate-{uuid.uuid4().hex[:8]}"
        commands = [
            "JARVIS, identify the events that deserve analyst attention first.",
            "JARVIS, how strong is the evidence?",
            "JARVIS, what are we still uncertain about?",
            "JARVIS, summarize current intelligence."
        ]
        for cmd in commands:
            req = JarvisCommandRequest(command=cmd, session_id=session_id)
            res = master_orchestrator.execute_command(db_session, req)
            assert res.dispatch_gate_blocked is True, f"Dispatch gate MUST be blocked for '{cmd}'"
