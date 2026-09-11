"""
AGNI-NETRA — JARVIS Phase 4 Intelligence Operations & Command Workflows Test Suite
Validates:
1. Continuous operational workflow across multi-turn sequences without repetitive event IDs
2. Single persistent InvestigationWorkspace continuity across all turns
3. Operational State: current_winner, winner_reason, completed/pending/blocked subtasks, action graph, stopping condition
4. Action Graph 10-stage lifecycle tracking (OBJECTIVE -> DISCOVERY -> CANDIDATE_SET -> INVESTIGATION -> COMPARISON -> SELECTION -> EVIDENCE -> ASSESSMENT -> HITL -> REPORT)
5. Operational Query Commands:
   - "JARVIS, what remains to be done?"
   - "JARVIS, why did you stop?"
   - "JARVIS, summarize what you know about this case."
   - "JARVIS, summarize this investigation."
   - "JARVIS, continue the investigation."
   - "JARVIS, inspect Candidate B." / "JARVIS, select Candidate B."
   - "Why did you select that one?" / "Explain why the first one wins."
   - "Take the top three and investigate them."
   - "Show me the evidence supporting that conclusion."
   - "Does it require human verification?"
6. Comparative Matrix markdown table formatting and deterministic scoring provenance (35% class + 25% risk + 15% prox + 15% base + 10% frp)
7. Operational Dispatch Gate invariant (ENABLE_OPERATIONAL_DISPATCH_GATE = False hardcoded as BLOCKED subtask)
"""

import pytest
import uuid
from typing import Any, Dict
from sqlalchemy.orm import Session
from backend.app.core.database import SessionLocal
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
# 1. Action Graph & Subtasks Reconciliation Unit Tests
# =========================================================================

def test_action_graph_initialization():
    """Verify that init_action_graph initializes the 10 standard stages."""
    graph = workspace_manager.init_action_graph()
    assert graph is not None
    assert graph["active_stage"] == "OBJECTIVE"
    stages = graph["stages"]
    assert len(stages) == 10
    stage_ids = [s["id"] for s in stages]
    assert stage_ids == [
        "OBJECTIVE", "DISCOVERY", "CANDIDATE_SET", "INVESTIGATION",
        "COMPARISON", "SELECTION", "EVIDENCE", "ASSESSMENT", "HITL", "REPORT"
    ]
    # OBJECTIVE should be COMPLETED initially
    assert stages[0]["status"] == "COMPLETED"
    assert stages[1]["status"] == "PENDING"


def test_action_graph_stage_update(db_session: Session):
    """Verify that stages can transition to IN_PROGRESS and COMPLETED."""
    session_id = f"test-graph-{uuid.uuid4().hex[:8]}"
    ws = workspace_manager.create_workspace(
        db=db_session,
        session_id=session_id,
        user_role="ANALYST",
        primary_objective="Test Action Graph Updates"
    )
    assert ws.action_graph is not None

    workspace_manager.update_action_graph(ws, "DISCOVERY", "COMPLETED", "step-1")
    assert ws.action_graph["active_stage"] == "DISCOVERY"
    disc_stage = next(s for s in ws.action_graph["stages"] if s["id"] == "DISCOVERY")
    assert disc_stage["status"] == "COMPLETED"
    assert disc_stage["step_ref"] == "step-1"


def test_subtasks_reconciliation_dispatch_gate_blocked(db_session: Session):
    """Verify that reconcile_subtasks always marks OPERATIONAL_DISPATCH_GATE as BLOCKED."""
    session_id = f"test-subtasks-{uuid.uuid4().hex[:8]}"
    ws = workspace_manager.create_workspace(
        db=db_session,
        session_id=session_id,
        user_role="ANALYST",
        primary_objective="Test Subtask Reconciliation"
    )
    workspace_manager.reconcile_subtasks(ws)
    assert ws.blocked_subtasks is not None
    blocked_ids = [b["id"] for b in ws.blocked_subtasks]
    assert any("dispatch" in b.lower() for b in blocked_ids)
    dispatch_sub = next(b for b in ws.blocked_subtasks if "dispatch" in b["id"].lower())
    assert "BLOCKED" in dispatch_sub.get("status", "") or "BLOCKED" in dispatch_sub.get("summary", "") or "BLOCKED" in dispatch_sub.get("reason", "")


def test_candidate_comparison_matrix_formatting():
    """Verify format_candidate_comparison_matrix generates Markdown table with ranks and winner."""
    comp_res = {
        "target_hypothesis": "Industrial Fire",
        "candidates": [
            {
                "event_code": "EV-TEST-1",
                "predicted_class": "Industrial Flare",
                "confidence": 0.92,
                "risk_score": 85.0,
                "risk_level": "HIGH",
                "baseline_ratio": 3.4,
                "facility_distance_m": 450.0,
                "composite_evidence_score": 88.5
            },
            {
                "event_code": "EV-TEST-2",
                "predicted_class": "Biomass Burning",
                "confidence": 0.65,
                "risk_score": 42.0,
                "risk_level": "MEDIUM",
                "baseline_ratio": 1.2,
                "facility_distance_m": 2200.0,
                "composite_evidence_score": 51.0
            }
        ],
        "strongest_candidate": {
            "event_code": "EV-TEST-1",
            "composite_evidence_score": 88.5
        },
        "selection_reason": "EV-TEST-1 exhibits highest composite evidence score."
    }
    matrix_md = workspace_manager.format_candidate_comparison_matrix(comp_res)
    assert "| Candidate | Event Code | Classification | Confidence |" in matrix_md
    assert "EV-TEST-1" in matrix_md
    assert "EV-TEST-2" in matrix_md
    assert "WINNER" in matrix_md
    assert "88.5/100" in matrix_md
    assert "35% classification match + 25% 5-factor risk" in matrix_md


# =========================================================================
# 2. End-to-End Primary Continuous Operations Workflow
# =========================================================================

def test_continuous_operations_primary_workflow(db_session: Session):
    """
    Validates Section 22 primary multi-turn command sequence operating on ONE continuous InvestigationWorkspace:
    Turn 1: "JARVIS, show highest priority thermal events"
    Turn 2: "Take the top three and investigate them."
    Turn 3: "Compare them and identify the strongest industrial-fire candidate"
    Turn 4: "Why did you select that one?"
    Turn 5: "Show me the evidence supporting that conclusion."
    Turn 6: "Does it require human verification?"
    Turn 7: "JARVIS, what remains to be done?"
    Turn 8: "JARVIS, why did you stop?"
    Turn 9: "JARVIS, summarize what you know about this case."
    Turn 10: "JARVIS, summarize this investigation."
    """
    session_id = f"ops-primary-{uuid.uuid4().hex[:8]}"

    # Turn 1: Discover high priority events
    req1 = JarvisCommandRequest(
        command="JARVIS, show highest priority thermal events",
        session_id=session_id
    )
    res1 = master_orchestrator.execute_command(db=db_session, request=req1, user_role="ANALYST")
    assert res1.state.value == "COMPLETED"
    ws1 = get_ws_dict(res1)
    assert ws1.get("investigation_id") is not None
    inv_id = ws1["investigation_id"]
    # Verify candidate cohort was assembled
    assert ws1.get("candidate_set") is not None
    assert len(ws1["candidate_set"]) >= 2
    # Verify action graph stages
    ag1 = ws1.get("action_graph") or {}
    stages1 = {s["id"]: s["status"] for s in ag1.get("stages", [])}
    assert stages1.get("DISCOVERY") == "COMPLETED"
    assert stages1.get("CANDIDATE_SET") == "COMPLETED"

    # Turn 2: Take the top three and investigate them
    req2 = JarvisCommandRequest(
        command="Take the top three and investigate them.",
        session_id=session_id,
        investigation_id=inv_id
    )
    res2 = master_orchestrator.execute_command(db=db_session, request=req2, user_role="ANALYST")
    assert res2.state.value == "COMPLETED"
    ws2 = get_ws_dict(res2)
    # MUST stay on the SAME workspace
    assert ws2.get("investigation_id") == inv_id
    assert len(ws2.get("candidate_set", [])) >= 3
    ag2 = ws2.get("action_graph") or {}
    stages2 = {s["id"]: s["status"] for s in ag2.get("stages", [])}
    assert stages2.get("INVESTIGATION") in ["IN_PROGRESS", "COMPLETED"]

    # Turn 3: Compare them and identify strongest candidate
    req3 = JarvisCommandRequest(
        command="Compare them and identify the strongest industrial-fire candidate",
        session_id=session_id,
        investigation_id=inv_id
    )
    res3 = master_orchestrator.execute_command(db=db_session, request=req3, user_role="ANALYST")
    assert res3.state.value == "COMPLETED"
    ws3 = get_ws_dict(res3)
    assert ws3.get("investigation_id") == inv_id
    assert ws3.get("current_winner") is not None
    winner = ws3["current_winner"]
    assert ws3.get("winner_reason") is not None
    assert "MULTI-CANDIDATE COMPARATIVE MATRIX" in res3.summary
    assert "| Candidate | Event Code |" in res3.summary
    ag3 = ws3.get("action_graph") or {}
    stages3 = {s["id"]: s["status"] for s in ag3.get("stages", [])}
    assert stages3.get("COMPARISON") == "COMPLETED"
    assert stages3.get("SELECTION") == "COMPLETED"

    # Turn 4: Why did you select that one?
    req4 = JarvisCommandRequest(
        command="Why did you select that one?",
        session_id=session_id,
        investigation_id=inv_id
    )
    res4 = master_orchestrator.execute_command(db=db_session, request=req4, user_role="ANALYST")
    assert res4.state.value == "COMPLETED"
    assert "SELECTION RATIONALE" in res4.summary
    assert winner in res4.summary or "Candidate" in res4.summary
    assert "Deterministic Provenance" in res4.summary
    ws4 = get_ws_dict(res4)
    assert ws4.get("investigation_id") == inv_id

    # Turn 5: Show me the evidence supporting that conclusion
    req5 = JarvisCommandRequest(
        command="Show me the evidence supporting that conclusion.",
        session_id=session_id,
        investigation_id=inv_id
    )
    res5 = master_orchestrator.execute_command(db=db_session, request=req5, user_role="ANALYST")
    assert res5.state.value == "COMPLETED"
    assert "EVIDENTIARY KNOWLEDGE SYNTHESIS" in res5.summary
    assert "CLASSIFICATION EVIDENCE" in res5.summary
    ws5 = get_ws_dict(res5)
    assert ws5.get("investigation_id") == inv_id

    # Turn 6: Does it require human verification?
    req6 = JarvisCommandRequest(
        command="Does it require human verification?",
        session_id=session_id,
        investigation_id=inv_id
    )
    res6 = master_orchestrator.execute_command(db=db_session, request=req6, user_role="ANALYST")
    assert res6.state.value == "COMPLETED"
    assert "HUMAN VERIFICATION" in res6.summary
    ws6 = get_ws_dict(res6)
    assert ws6.get("investigation_id") == inv_id
    ag6 = ws6.get("action_graph") or {}
    stages6 = {s["id"]: s["status"] for s in ag6.get("stages", [])}
    assert stages6.get("HITL") in ["IN_PROGRESS", "COMPLETED", "PENDING"]

    # Turn 7: What remains to be done?
    req7 = JarvisCommandRequest(
        command="JARVIS, what remains to be done?",
        session_id=session_id,
        investigation_id=inv_id
    )
    res7 = master_orchestrator.execute_command(db=db_session, request=req7, user_role="ANALYST")
    assert res7.state.value == "COMPLETED"
    assert "OPERATIONAL STATUS // WHAT REMAINS" in res7.summary
    assert "COMPLETED:" in res7.summary
    assert "BLOCKED:" in res7.summary
    assert "Operational Dispatch" in res7.summary
    ws7 = get_ws_dict(res7)
    assert ws7.get("investigation_id") == inv_id
    assert len(ws7.get("completed_subtasks", [])) >= 1
    assert len(ws7.get("blocked_subtasks", [])) >= 1

    # Turn 8: Why did you stop?
    req8 = JarvisCommandRequest(
        command="JARVIS, why did you stop?",
        session_id=session_id,
        investigation_id=inv_id
    )
    res8 = master_orchestrator.execute_command(db=db_session, request=req8, user_role="ANALYST")
    assert res8.state.value == "COMPLETED"
    assert "OPERATIONAL STOPPING TRACE" in res8.summary
    assert "Stopping condition:" in res8.summary
    assert "Evidence obtained:" in res8.summary
    ws8 = get_ws_dict(res8)
    assert ws8.get("investigation_id") == inv_id

    # Turn 9: Summarize what you know about this case
    req9 = JarvisCommandRequest(
        command="JARVIS, summarize what you know about this case.",
        session_id=session_id,
        investigation_id=inv_id
    )
    res9 = master_orchestrator.execute_command(db=db_session, request=req9, user_role="ANALYST")
    assert res9.state.value == "COMPLETED"
    assert "EVIDENTIARY KNOWLEDGE SYNTHESIS" in res9.summary
    assert "FACTS" in res9.summary
    ws9 = get_ws_dict(res9)
    assert ws9.get("investigation_id") == inv_id

    # Turn 10: Summarize this investigation (canonical 13 dimensions)
    req10 = JarvisCommandRequest(
        command="JARVIS, summarize this investigation.",
        session_id=session_id,
        investigation_id=inv_id
    )
    res10 = master_orchestrator.execute_command(db=db_session, request=req10, user_role="ANALYST")
    assert res10.state.value == "COMPLETED"
    assert "CANONICAL INVESTIGATION SUMMARY" in res10.summary
    assert "CASE:" in res10.summary
    assert "OBJECTIVE:" in res10.summary
    assert "CURRENT TARGET:" in res10.summary
    assert "CURRENT WINNER:" in res10.summary
    assert "CLASSIFICATION:" in res10.summary
    assert "RISK:" in res10.summary
    ws10 = get_ws_dict(res10)
    assert ws10.get("investigation_id") == inv_id


# =========================================================================
# 3. Candidate Focus Switch & Continuation Tests
# =========================================================================

def test_inspect_candidate_and_continue_investigation(db_session: Session):
    """
    Tests:
    - "JARVIS, inspect Candidate B." -> switches candidate focus to Candidate B
    - "JARVIS, continue the investigation." -> advances next pending subtask
    """
    session_id = f"ops-cand-b-{uuid.uuid4().hex[:8]}"

    # Setup cohort
    req1 = JarvisCommandRequest(
        command="Take the top three and investigate them.",
        session_id=session_id
    )
    res1 = master_orchestrator.execute_command(db=db_session, request=req1, user_role="ANALYST")
    ws1 = get_ws_dict(res1)
    inv_id = ws1["investigation_id"]
    candidates = ws1.get("candidate_set", [])
    assert len(candidates) >= 2
    cand_b_code = candidates[1].get("event_code") or candidates[1].get("event_id")

    # Inspect Candidate B
    req2 = JarvisCommandRequest(
        command="JARVIS, inspect Candidate B.",
        session_id=session_id,
        investigation_id=inv_id
    )
    res2 = master_orchestrator.execute_command(db=db_session, request=req2, user_role="ANALYST")
    assert res2.state.value == "COMPLETED"
    assert "Candidate B" in res2.summary or cand_b_code in res2.summary
    ws2 = get_ws_dict(res2)
    assert ws2.get("investigation_id") == inv_id
    assert ws2.get("selected_candidate") == cand_b_code

    # Continue the investigation
    req3 = JarvisCommandRequest(
        command="JARVIS, continue the investigation.",
        session_id=session_id,
        investigation_id=inv_id
    )
    res3 = master_orchestrator.execute_command(db=db_session, request=req3, user_role="ANALYST")
    assert res3.state.value == "COMPLETED"
    assert "Continuing investigation" in res3.summary or "COMPLETED" in res3.summary
    ws3 = get_ws_dict(res3)
    assert ws3.get("investigation_id") == inv_id
