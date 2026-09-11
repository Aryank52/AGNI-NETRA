"""
AGNI-NETRA — Comprehensive JARVIS Autonomous Intelligence Layer Test Suite
Validates Command Parsing, Intent Taxonomy, Execution Planning, Controlled Tools,
Evidence Fusion, Epistemic Separation, RBAC, Dispatch Gate Invariants, Session Memory,
and Trace Auditing.
"""

import pytest
from sqlalchemy.orm import Session

from backend.app.core.database import SessionLocal
from backend.app.models.domain import ThermalEvent
from backend.app.models.jarvis_schemas import (
    CommandIntent, JarvisCommandRequest, StepStatus, EvidenceStatus
)
from backend.app.services.jarvis.jarvis_command_interpreter import command_interpreter
from backend.app.services.jarvis.jarvis_planner import execution_planner
from backend.app.services.jarvis.jarvis_guardian import guardian
from backend.app.services.jarvis.jarvis_tools import JarvisToolRegistry
from backend.app.services.jarvis.jarvis_memory import session_memory
from backend.app.services.jarvis.jarvis_orchestrator import master_orchestrator


@pytest.fixture(scope="module")
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class TestJarvisCommandInterpreter:
    """Tests 1-3: Command Parsing, Intent Classification, and Parameter Extraction"""

    def test_parse_investigate_event_827(self):
        intent, entities = command_interpreter.parse_command("JARVIS, investigate Event 827.")
        assert intent == CommandIntent.INVESTIGATE
        assert entities.get("event_ref") == "827"

    def test_parse_explain_risk(self):
        intent, entities = command_interpreter.parse_command("JARVIS, explain why Event 827 has high risk.")
        assert intent == CommandIntent.EXPLAIN
        assert entities.get("event_ref") == "827"
        assert entities.get("explain_type") == "RISK"

    def test_parse_shap_drivers(self):
        intent, entities = command_interpreter.parse_command("JARVIS, explain the strongest SHAP drivers for Event 827.")
        assert intent == CommandIntent.EXPLAIN
        assert entities.get("event_ref") == "827"
        assert entities.get("explain_type") == "SHAP"

    def test_parse_compare_baseline(self):
        intent, entities = command_interpreter.parse_command("JARVIS, compare Event 827 with its historical baseline.")
        assert intent == CommandIntent.COMPARE
        assert entities.get("event_ref") == "827"

    def test_parse_spatial_anomalies(self):
        intent, entities = command_interpreter.parse_command("JARVIS, find critical anomalies within 5 km of industrial facilities in Gujarat.")
        assert intent == CommandIntent.LOCATE
        assert entities.get("state") == "Gujarat"
        assert entities.get("distance_m") == 5000.0

    def test_parse_verification_queue(self):
        intent, entities = command_interpreter.parse_command("JARVIS, show me which cases require human verification.")
        assert intent == CommandIntent.VERIFY

    def test_parse_dossier_generation(self):
        intent, entities = command_interpreter.parse_command("JARVIS, generate an investigation dossier for Event 827.")
        assert intent == CommandIntent.GENERATE_REPORT
        assert entities.get("event_ref") == "827"

    def test_parse_system_status(self):
        intent, entities = command_interpreter.parse_command("JARVIS, give me the current intelligence system status.")
        assert intent == CommandIntent.STATUS


class TestJarvisPlannerAndSafety:
    """Tests 4-8: Dynamic Execution Planning, RBAC, Dispatch Gate, and Mutations"""

    def test_execution_plan_investigation_steps(self):
        steps = execution_planner.build_plan(CommandIntent.INVESTIGATE, {"event_ref": "827"})
        assert len(steps) >= 8
        assert steps[0].action.startswith("Validate Permissions")
        tools_in_plan = [s.tool for s in steps if s.tool]
        assert "tool_get_event" in tools_in_plan
        assert "tool_get_event_spatial_context" in tools_in_plan
        assert "tool_classify_event" in tools_in_plan
        assert "tool_calculate_risk" in tools_in_plan

    def test_operational_dispatch_gate_blocked(self, db_session: Session):
        """Dispatches must be strictly blocked with ENABLE_OPERATIONAL_DISPATCH_GATE=False"""
        req = JarvisCommandRequest(command="JARVIS, emergency dispatch responders to Event 827.")
        res = master_orchestrator.execute_command(db_session, req, user_role="ANALYST")
        assert res.execution_trace.status == StepStatus.BLOCKED
        assert "OPERATIONAL_DISPATCH_BLOCKED" in res.summary
        assert res.dispatch_gate_blocked is True
        assert res.requires_human_approval is True

    def test_unauthorized_mutation_blocked(self, db_session: Session):
        """Arbitrary SQL modification commands must be blocked"""
        req = JarvisCommandRequest(command="JARVIS, DROP TABLE thermal_events;")
        res = master_orchestrator.execute_command(db_session, req, user_role="ANALYST")
        assert res.execution_trace.status == StepStatus.BLOCKED
        assert "MUTATION_BLOCKED" in res.summary

    def test_public_role_privacy_masking(self, db_session: Session):
        """Public role must have sensitive internal coordinates and restricted tools blocked"""
        req = JarvisCommandRequest(command="JARVIS, investigate Event 827.")
        res = master_orchestrator.execute_command(db_session, req, user_role="PUBLIC")
        # Public role is blocked from executing internal investigative deep dives
        assert res.execution_trace.status == StepStatus.BLOCKED or "Access Denied" in res.summary


class TestJarvisControlledToolsAndOrchestration:
    """Tests 9-18: Controlled Tool Execution, Evidence Fusion, Trace Timings, and Missing Events"""

    def test_get_event_resolution(self, db_session: Session):
        evt = JarvisToolRegistry.tool_get_event(db_session, "827")
        assert evt["found"] is True
        assert "827" in evt["event_code"]

    def test_missing_event_handling(self, db_session: Session):
        evt = JarvisToolRegistry.tool_get_event(db_session, "NON_EXISTENT_UUID_999999")
        assert evt["found"] is False
        assert "not found" in evt["error"].lower()

    def test_tool_classify_event_authoritative(self, db_session: Session):
        cls_res = JarvisToolRegistry.tool_classify_event(db_session, "827")
        assert cls_res["predicted_class"] in ["Industrial Fire", "Gas Flare", "Agricultural Fire", "Wildfire"]
        assert 0.0 <= cls_res["calibrated_confidence"] <= 1.0
        assert cls_res["model_version"] == "xgb-v3.0-real-candidate"

    def test_tool_get_shap_drivers(self, db_session: Session):
        shap_res = JarvisToolRegistry.tool_get_shap_drivers(db_session, "827")
        assert len(shap_res["top_drivers"]) > 0
        assert "feature" in shap_res["top_drivers"][0]
        assert "attribution" in shap_res["top_drivers"][0]

    def test_tool_calculate_risk_deterministic(self, db_session: Session):
        risk_res = JarvisToolRegistry.tool_calculate_risk(db_session, "827")
        assert 0.0 <= risk_res["total_risk_score"] <= 100.0
        assert risk_res["risk_level"] in ["LOW", "MODERATE", "HIGH", "CRITICAL"]
        assert "component_subscores" in risk_res
        assert "intensity" in risk_res["component_subscores"]

    def test_tool_system_status(self, db_session: Session):
        status = JarvisToolRegistry.tool_get_system_status(db_session)
        assert status["status"] == "HEALTHY"
        assert status["database"]["total_events"] > 0
        assert status["ml_governance"]["champion_model"] == "xgb-v3.0-real-candidate"

    def test_full_investigate_command_execution(self, db_session: Session):
        req = JarvisCommandRequest(command="JARVIS, investigate Event 827.")
        res = master_orchestrator.execute_command(db_session, req, user_role="ANALYST")
        assert res.execution_trace.status == StepStatus.COMPLETED
        assert len(res.execution_trace.steps) >= 8
        assert res.fused_evidence.thermal_evidence is not None
        assert res.fused_evidence.classification is not None
        assert res.fused_evidence.risk is not None
        assert res.fused_evidence.categorized_synthesis is not None
        assert len(res.fused_evidence.categorized_synthesis.facts) > 0
        assert len(res.fused_evidence.categorized_synthesis.model_output) > 0
        assert res.execution_trace.total_duration_ms > 0

    def test_generate_dossier_pdf(self, db_session: Session):
        req = JarvisCommandRequest(command="JARVIS, generate an investigation dossier for Event 827.")
        res = master_orchestrator.execute_command(db_session, req, user_role="ANALYST")
        assert res.execution_trace.status == StepStatus.COMPLETED
        assert "dossier" in res.details
        assert "pdf_export" in res.details
        assert res.details["pdf_export"].get("is_valid_pdf") is True


class TestJarvisSessionMemory:
    """Tests 19-20: Session Memory and Conversational Pronoun Continuity"""

    def test_session_memory_pronoun_resolution(self, db_session: Session):
        session_id = "test-session-cross-turn-01"
        
        # Turn 1: Investigate Event 827
        req1 = JarvisCommandRequest(command="JARVIS, investigate Event 827.", session_id=session_id)
        res1 = master_orchestrator.execute_command(db_session, req1, user_role="ANALYST")
        assert res1.execution_trace.target_event == "827"

        # Turn 2: Follow-up referencing "it" without explicitly naming the event
        req2 = JarvisCommandRequest(command="JARVIS, compare it with its historical baseline.", session_id=session_id)
        res2 = master_orchestrator.execute_command(db_session, req2, user_role="ANALYST")
        assert res2.execution_trace.target_event in ["827", "EVT-827"]
        assert res2.fused_evidence.anomaly is not None


class TestJarvisToolCatalog:
    """Tests 21-24: Tool Catalog Inspection and Registration Integrity"""

    def test_tool_catalog_entries(self):
        catalog = JarvisToolRegistry.get_registered_tools()
        assert len(catalog) >= 15
        tool_names = [t.name for t in catalog]
        assert "tool_get_event" in tool_names
        assert "tool_classify_event" in tool_names
        assert "tool_calculate_risk" in tool_names
        assert "tool_get_system_status" in tool_names
        assert all(t.audit_required is True for t in catalog)

    def test_enriched_tool_registry_metadata(self):
        catalog = JarvisToolRegistry.get_registered_tools()
        for tool in catalog:
            assert hasattr(tool, "purpose") and len(tool.purpose) > 0
            assert hasattr(tool, "capability") and len(tool.capability) > 0
            assert hasattr(tool, "input_schema") and isinstance(tool.input_schema, dict)
            assert hasattr(tool, "output_schema") and isinstance(tool.output_schema, dict)
            assert hasattr(tool, "dependencies") and isinstance(tool.dependencies, list)
            assert hasattr(tool, "risk_level") and tool.risk_level in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
            assert hasattr(tool, "required_permissions") and len(tool.required_permissions) > 0


class TestSyntheticMasterAgentRefinement:
    """Tests 25-30: Synthetic Master Agent, State Machine, Adaptive Loop, and Complex Commands"""

    def test_master_agent_identity_and_capabilities(self, db_session: Session):
        req = JarvisCommandRequest(command="JARVIS, investigate Event 827.")
        res = master_orchestrator.execute_command(db_session, req, user_role="ANALYST")
        
        # Verify ONE master agent
        for step in res.execution_trace.steps:
            assert step.agent == "JARVIS", f"Step agent was {step.agent}, expected 'JARVIS'"
            assert step.capability is not None, f"Step {step.action} missing capability"

        assert len(res.capabilities_used) > 0
        assert "THERMAL_INTELLIGENCE" in res.capabilities_used
        assert "GEOINT" in res.capabilities_used
        assert "CLASSIFICATION" in res.capabilities_used
        assert "RISK_ANALYSIS" in res.capabilities_used

    def test_state_machine_transitions(self, db_session: Session):
        req = JarvisCommandRequest(command="JARVIS, investigate Event 827.")
        res = master_orchestrator.execute_command(db_session, req, user_role="ANALYST")
        
        transitions = res.execution_trace.state_transitions
        assert len(transitions) >= 3
        states = [t["state"] for t in transitions]
        assert "IDLE" in states
        assert "UNDERSTANDING" in states
        assert "PLANNING" in states
        assert "EXECUTING" in states
        assert "EVALUATING" in states
        assert res.state in ["COMPLETED", "REQUIRES_APPROVAL"]

    def test_adaptive_gujarat_critical_anomaly_investigation(self, db_session: Session):
        """Validates 'investigate most critical thermal anomaly in Gujarat and tell me why it is high risk'"""
        req = JarvisCommandRequest(command="JARVIS, investigate the most critical thermal anomaly in Gujarat and tell me why it is high risk.")
        res = master_orchestrator.execute_command(db_session, req, user_role="ANALYST")
        
        assert res.execution_trace.status == StepStatus.COMPLETED
        assert res.execution_trace.target_event is not None
        assert "event" in res.details
        assert "risk" in res.details
        assert "spatial" in res.details
        assert res.fused_evidence.risk is not None

    def test_session_continuity_chain(self, db_session: Session):
        """Validates 4-turn conversational chain resolving 'it' and 'its'"""
        sess_id = "test-chain-session-4turn"

        # Turn 1: Investigate
        r1 = master_orchestrator.execute_command(db_session, JarvisCommandRequest(command="JARVIS, investigate Event 827.", session_id=sess_id))
        assert r1.execution_trace.target_event == "827"

        # Turn 2: Explain its risk
        r2 = master_orchestrator.execute_command(db_session, JarvisCommandRequest(command="JARVIS, explain its risk.", session_id=sess_id))
        assert r2.execution_trace.target_event in ["827", "EVT-827"]
        assert "risk_decomposition" in r2.details

        # Turn 3: Compare it with its historical baseline
        r3 = master_orchestrator.execute_command(db_session, JarvisCommandRequest(command="JARVIS, compare it with its historical baseline.", session_id=sess_id))
        assert r3.execution_trace.target_event in ["827", "EVT-827"]
        assert "baseline_comparison" in r3.details

        # Turn 4: Generate its intelligence dossier
        r4 = master_orchestrator.execute_command(db_session, JarvisCommandRequest(command="JARVIS, generate its intelligence dossier.", session_id=sess_id))
        assert r4.execution_trace.target_event in ["827", "EVT-827"]
        assert "pdf_export" in r4.details
        assert r4.details["pdf_export"].get("is_valid_pdf") is True

    def test_primary_acceptance_complex_command(self, db_session: Session):
        """
        Primary Acceptance Test:
        'JARVIS, find the highest-risk thermal event near an industrial facility,
        investigate it, explain the main risk factors, compare it with its historical
        baseline, and generate an intelligence dossier.'
        """
        cmd = "JARVIS, find the highest-risk thermal event near an industrial facility, investigate it, explain the main risk factors, compare it with its historical baseline, and generate an intelligence dossier."
        req = JarvisCommandRequest(command=cmd)
        res = master_orchestrator.execute_command(db_session, req, user_role="ANALYST")

        assert res.execution_trace.status == StepStatus.COMPLETED
        assert res.execution_trace.target_event is not None
        assert len(res.execution_trace.steps) >= 8
        assert "event" in res.details
        assert "spatial" in res.details
        assert "ml" in res.details
        assert "baseline" in res.details
        assert "risk" in res.details
        assert "dossier" in res.details
        assert "pdf_export" in res.details
        assert res.details["pdf_export"].get("is_valid_pdf") is True
        assert res.fused_evidence.categorized_synthesis is not None
        assert len(res.fused_evidence.categorized_synthesis.facts) > 0
        assert len(res.fused_evidence.categorized_synthesis.model_output) > 0
        assert len(res.fused_evidence.categorized_synthesis.recommendations) > 0


class TestJarvisGeneralizationRefinementsPhase2B:
    """Targeted tests for Phase 2B generalization refinements."""

    def test_descriptive_anaphora_serious_one(self, db_session: Session):
        """Test 1: 'Investigate Event 827.' then 'Investigate the serious one.'"""
        sess = "test-phase2b-anaphora"
        r1 = master_orchestrator.execute_command(
            db_session, JarvisCommandRequest(command="JARVIS, investigate Event 827.", session_id=sess)
        )
        assert r1.execution_trace.target_event in ["827", "EVT-827"]

        r2 = master_orchestrator.execute_command(
            db_session, JarvisCommandRequest(command="JARVIS, investigate the serious one.", session_id=sess)
        )
        assert r2.execution_trace.target_event in ["827", "EVT-827"]
        assert r2.objective.resolved_from_context is True

    def test_possessive_syntax_explain_risk(self, db_session: Session):
        """Test 2: 'Explain Event 827's risk.'"""
        req = JarvisCommandRequest(command="JARVIS, explain Event 827's risk.")
        res = master_orchestrator.execute_command(db_session, req)
        assert res.intent == "EXPLAIN"
        assert res.execution_trace.target_event in ["827", "EVT-827"]
        tools = [s.tool for s in res.execution_trace.steps if s.tool]
        assert len(tools) <= 5
        assert "tool_generate_investigation_dossier" not in tools
        assert not res.details.get("pdf_export")

    def test_prepositional_syntax_explain_risk(self, db_session: Session):
        """Test 3: 'Explain the risk of Event 827.'"""
        req = JarvisCommandRequest(command="JARVIS, explain the risk of Event 827.")
        res = master_orchestrator.execute_command(db_session, req)
        assert res.intent == "EXPLAIN"
        assert res.execution_trace.target_event in ["827", "EVT-827"]
        tools = [s.tool for s in res.execution_trace.steps if s.tool]
        assert len(tools) <= 5
        assert not res.details.get("pdf_export")

    def test_multi_candidate_cardinality_two(self, db_session: Session):
        """Test 4: 'Compare the two strongest cases in Gujarat.'"""
        req = JarvisCommandRequest(command="JARVIS, compare the two strongest cases in Gujarat.")
        res = master_orchestrator.execute_command(db_session, req)
        assert res.intent == "COMPARE"
        assert res.objective.primary_goal == "MULTI_EVENT_COMPARE"
        assert res.objective.candidate_count == 2
        assert res.objective.target_region == "Gujarat"
        tools = [s.tool for s in res.execution_trace.steps if s.tool]
        assert "tool_compare_candidate_events" in tools or "tool_get_recent_events" in tools

    def test_multi_candidate_cardinality_three(self, db_session: Session):
        """Test 5: 'Compare the top three events.'"""
        req = JarvisCommandRequest(command="JARVIS, compare the top three events.")
        res = master_orchestrator.execute_command(db_session, req)
        assert res.intent == "COMPARE"
        assert res.objective.primary_goal == "MULTI_EVENT_COMPARE"
        assert res.objective.candidate_count == 3

    def test_implicit_session_evidence_request(self, db_session: Session):
        """Test 6: 'Give me the evidence behind the conclusion.'"""
        sess = "test-phase2b-evidence"
        master_orchestrator.execute_command(
            db_session, JarvisCommandRequest(command="JARVIS, investigate Event 827.", session_id=sess)
        )
        r2 = master_orchestrator.execute_command(
            db_session, JarvisCommandRequest(command="JARVIS, give me the evidence behind the conclusion.", session_id=sess)
        )
        assert r2.execution_trace.target_event in ["827", "EVT-827"]
        tools = [s.tool for s in r2.execution_trace.steps if s.tool]
        assert "fuse_evidence" in tools or "tool_get_event" in tools
        assert not r2.details.get("pdf_export")

    def test_missing_explicit_target_no_substitution(self, db_session: Session):
        """Test 7: 'Investigate Event 99999999.' -> TARGET NOT FOUND, NO SUBSTITUTION"""
        req = JarvisCommandRequest(command="JARVIS, investigate Event 99999999.")
        res = master_orchestrator.execute_command(db_session, req)
        assert "TARGET NOT FOUND" in res.summary
        assert "No substitution was performed" in res.summary
        assert res.details.get("substituted") is False
        assert res.execution_trace.target_event == "99999999"

    def test_contextual_dossier_strongest_case(self, db_session: Session):
        """Test 8: 'Generate a dossier for the strongest case.'"""
        sess = "test-phase2b-dossier"
        # Turn 1: Compare candidates
        master_orchestrator.execute_command(
            db_session, JarvisCommandRequest(command="JARVIS, compare the two strongest cases in Gujarat.", session_id=sess)
        )
        # Turn 2: Generate dossier for the strongest case
        r2 = master_orchestrator.execute_command(
            db_session, JarvisCommandRequest(command="JARVIS, generate a dossier for the strongest case.", session_id=sess)
        )
        assert r2.objective.resolved_from_context is True
        assert r2.execution_trace.target_event is not None
        assert "pdf_export" in r2.details
        assert r2.details["pdf_export"].get("is_valid_pdf") is True


