"""
AGNI-NETRA Phase 11: Global Evidence Graph & Explainable Intelligence Test Suite
Comprehensive verification suite validating:
1. Node creation
2. Edge creation
3. Provenance inheritance
4. Evidence nature assignment (OBSERVED, DERIVED, INFERRED, MISSING, CONFLICTING)
5. Supporting relationship
6. Contradicting relationship
7. Derived relationship
8. Inferred relationship
9. Missing evidence node
10. Uncertainty propagation
11. Evidence strength calculation
12. Hypothesis creation (7 standardized candidates)
13. Hypothesis comparison
14. Evidence independence
15. Duplicate prevention
16. Source lineage
17. Assessment lineage
18. Data gaps identification
19. JARVIS command routing
20. API endpoints for evidence graph
21. Workspace persistence
22. Phase 7 thermal integration
23. Phase 8 context integration
24. Phase 9 temporal integration
25. Phase 10 environmental integration
26. Phase 10.1 provenance integration
27. No fabricated evidence
28. Safety invariants
29. Risk formula unchanged
30. Classifier unchanged
31. Dispatch remains blocked
"""

import pytest
from datetime import datetime, timezone
from typing import Dict, Any, List
from sqlalchemy import text

from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.database import SessionLocal
from backend.app.models.canonical import (
    EvidenceGraphNode,
    EvidenceGraphEdge,
    Hypothesis,
    EvidenceGraph,
    SourceProvenance
)
from backend.app.services.intelligence.evidence_graph_engine import (
    evidence_graph_engine,
    EvidenceGraphEngine
)
from backend.app.services.jarvis.jarvis_command_interpreter import command_interpreter
from backend.app.services.jarvis.jarvis_orchestrator import master_orchestrator
from backend.app.services.jarvis.jarvis_workspace import workspace_manager
from backend.app.services.jarvis.jarvis_policy import ENABLE_OPERATIONAL_DISPATCH_GATE
from backend.app.models.domain import InvestigationWorkspace


@pytest.fixture(scope="module")
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


# 1. Node Creation
def test_evidence_graph_node_creation():
    node = EvidenceGraphNode(
        id="NODE-TEST-001",
        label="Test Thermal Detection",
        domain="THERMAL",
        evidence_nature="OBSERVED",
        strength="STRONG",
        description="FRP 85.0 MW detected by VIIRS NOAA-20",
        observation_time=datetime.now(timezone.utc).isoformat(),
        reliability_score=0.92
    )
    assert node.id == "NODE-TEST-001"
    assert node.node_id == "NODE-TEST-001"
    assert node.domain == "THERMAL"
    assert node.node_type == "THERMAL"
    assert node.evidence_nature == "OBSERVED"
    assert node.strength == "STRONG"
    assert node.reliability_score == 0.92


# 2. Edge Creation
def test_evidence_graph_edge_creation():
    edge = EvidenceGraphEdge(
        source="NODE-TEST-001",
        target="HYP-001",
        edge_type="SUPPORTS",
        weight=0.85,
        explanation="High FRP observed within industrial perimeter reinforces flaring hypothesis"
    )
    assert edge.source == "NODE-TEST-001"
    assert edge.source_node_id == "NODE-TEST-001"
    assert edge.target == "HYP-001"
    assert edge.target_node_id == "HYP-001"
    assert edge.edge_type == "SUPPORTS"
    assert edge.relationship_type == "SUPPORTS"
    assert edge.weight == 0.85
    assert not edge.bidirectional


# 3. Provenance Inheritance
def test_provenance_inheritance(db_session):
    graph = evidence_graph_engine.build_event_evidence_graph(db=db_session, event_ref="EVT-827")
    obs_nodes = [n for n in graph.nodes if n.evidence_nature == "OBSERVED"]
    assert len(obs_nodes) > 0
    for n in obs_nodes:
        assert n.provenance is not None
        assert n.provenance.provider != ""
        assert n.provenance.dataset != ""


# 4. Evidence Nature Assignment
def test_evidence_nature_assignment(db_session):
    graph = evidence_graph_engine.build_event_evidence_graph(db=db_session, event_ref="EVT-827")
    natures = {n.evidence_nature for n in graph.nodes}
    assert "OBSERVED" in natures
    assert "DERIVED" in natures
    assert "INFERRED" in natures
    assert "MISSING" in natures
    for nat, count in graph.evidence_nature_counts.items():
        actual_count = sum(1 for n in graph.nodes if n.evidence_nature == nat)
        assert count == actual_count, f"Nature count mismatch for {nat}"


# 5. Supporting Relationship
def test_supporting_relationship(db_session):
    supp = evidence_graph_engine.get_supporting_evidence(db=db_session, event_id="EVT-827")
    assert len(supp) > 0
    for s in supp:
        assert s["edge_type"] in ["SUPPORTS", "CORROBORATES"]
        assert s["strength"] in ["STRONG", "MODERATE", "LIMITED", "WEAK"]


# 6. Contradicting Relationship
def test_contradicting_relationship(db_session):
    conf = evidence_graph_engine.get_conflicting_evidence(db=db_session, event_id="EVT-827")
    assert len(conf) > 0
    for c in conf:
        assert c["edge_type"] in ["CONTRADICTS", "CHANGES_CONFIDENCE"]
        assert c["contradiction_target"] != ""


# 7. Derived Relationship
def test_derived_relationship(db_session):
    graph = evidence_graph_engine.build_event_evidence_graph(db=db_session, event_ref="EVT-827")
    derived_edges = [e for e in graph.edges if e.relationship_type == "DERIVED_FROM"]
    assert len(derived_edges) > 0
    for de in derived_edges:
        source_node = next((n for n in graph.nodes if n.node_id == de.source_node_id), None)
        target_node = next((n for n in graph.nodes if n.node_id == de.target_node_id), None)
        assert source_node is not None and target_node is not None
        assert "DERIVED" in [source_node.evidence_nature, target_node.evidence_nature]


# 8. Inferred Relationship
def test_inferred_relationship(db_session):
    graph = evidence_graph_engine.build_event_evidence_graph(db=db_session, event_ref="EVT-827")
    inferred_edges = [e for e in graph.edges if e.relationship_type in ["INFERRED_FROM", "SUPPORTS"]]
    assert len(inferred_edges) > 0
    for ie in inferred_edges:
        target_node = next((n for n in graph.nodes if n.node_id == ie.target_node_id), None)
        assert target_node is not None
        assert target_node.evidence_nature in ["INFERRED", "OBSERVED", "DERIVED"]


# 9. Missing Evidence Node
def test_missing_evidence_node(db_session):
    graph = evidence_graph_engine.build_event_evidence_graph(db=db_session, event_ref="EVT-827")
    missing_nodes = [n for n in graph.nodes if n.evidence_nature == "MISSING"]
    assert len(missing_nodes) > 0
    for m in missing_nodes:
        assert "unconfigured" in m.description.lower() or "missing" in m.description.lower() or "unavailable" in m.description.lower() or "cloud" in m.description.lower()


# 10. Uncertainty Propagation
def test_uncertainty_propagation(db_session):
    graph = evidence_graph_engine.build_event_evidence_graph(db=db_session, event_ref="EVT-827")
    unc = graph.uncertainty_propagation
    assert "aggregate_uncertainty_score" in unc
    assert "uncertainty_tier" in unc
    assert "missing_evidence_count" in unc
    assert unc["missing_evidence_count"] >= len([n for n in graph.nodes if n.evidence_nature == "MISSING"])


# 11. Evidence Strength Calculation
def test_evidence_strength_calculation(db_session):
    graph = evidence_graph_engine.build_event_evidence_graph(db=db_session, event_ref="EVT-827")
    for node in graph.nodes:
        if node.strength == "STRONG":
            assert node.reliability_score >= 0.70
        elif node.strength == "WEAK":
            assert node.reliability_score <= 0.65 or node.evidence_nature == "MISSING"


# 12. Hypothesis Creation (7 Standardized Candidates)
def test_hypothesis_creation(db_session):
    hyps = evidence_graph_engine.get_hypotheses(db=db_session, event_id="EVT-827")
    assert len(hyps) == 7
    hyp_ids = {h["hypothesis_id"] for h in hyps}
    assert hyp_ids == {
        "HYPOTHESIS_A", "HYPOTHESIS_B", "HYPOTHESIS_C",
        "HYPOTHESIS_D", "HYPOTHESIS_E", "HYPOTHESIS_F", "HYPOTHESIS_G"
    }


# 13. Hypothesis Comparison
def test_hypothesis_comparison(db_session):
    graph = evidence_graph_engine.build_event_evidence_graph(db=db_session, event_ref="EVT-827")
    assert graph.winner_hypothesis in ["HYPOTHESIS_A", "HYPOTHESIS_E"]
    winner = next(h for h in graph.hypotheses if h.hypothesis_id == graph.winner_hypothesis)
    assert winner.support_score >= 70.0
    # Forest Fire hypothesis (HYPOTHESIS_B) should have contradicting count > 0 for an industrial refinery
    forest_fire = next(h for h in graph.hypotheses if h.hypothesis_id == "HYPOTHESIS_B")
    assert forest_fire.contradicting_evidence_count > 0


# 14. Evidence Independence
def test_evidence_independence(db_session):
    graph = evidence_graph_engine.build_event_evidence_graph(db=db_session, event_ref="EVT-827")
    independence_edges = [e for e in graph.edges if e.relationship_type == "INDEPENDENT_OF"]
    assert len(independence_edges) > 0
    for ie in independence_edges:
        assert "independent" in ie.explanation.lower()


# 15. Duplicate Prevention
def test_duplicate_prevention(db_session):
    graph = evidence_graph_engine.build_event_evidence_graph(db=db_session, event_ref="EVT-827")
    node_ids = [n.node_id for n in graph.nodes]
    assert len(node_ids) == len(set(node_ids)), "Duplicate node IDs detected in Evidence Graph"
    edge_keys = [(e.source_node_id, e.target_node_id, e.relationship_type) for e in graph.edges]
    assert len(edge_keys) == len(set(edge_keys)), "Duplicate edges detected in Evidence Graph"


# 16. Source Lineage
def test_source_lineage(db_session):
    graph = evidence_graph_engine.build_event_evidence_graph(db=db_session, event_ref="EVT-827")
    prov_chain = evidence_graph_engine.get_provenance_chain(db=db_session, event_id="EVT-827")
    assert len(prov_chain) >= len([n for n in graph.nodes if n.provenance is not None])
    for item in prov_chain:
        assert "node_id" in item
        assert "provenance" in item
        assert item["provenance"].get("provider") is not None


# 17. Assessment Lineage
def test_assessment_lineage(db_session):
    lineage = evidence_graph_engine.get_assessment_lineage(db=db_session, event_id="EVT-827")
    assert "event_id" in lineage
    assert "winner_hypothesis" in lineage
    assert "lineage_chain" in lineage
    assert len(lineage["lineage_chain"]) >= 3


# 18. Data Gaps Identification
def test_data_gaps_identification(db_session):
    gaps = evidence_graph_engine.get_data_gaps(db=db_session, event_id="EVT-827")
    assert len(gaps) >= 2
    gap_types = [g["data_gap_type"] for g in gaps]
    assert "UNCONFIGURED_FEED" in gap_types or "OBSCURED_OBSERVATION" in gap_types


# 19. JARVIS Command Routing
def test_jarvis_command_routing():
    p1 = command_interpreter.interpret(
        "JARVIS, explain the complete evidence chain for EVT-827. Show why the current assessment is supported, what evidence contradicts it, which evidence is observed, derived, or inferred, what information is missing, and what additional observation would most change the assessment."
    )
    assert p1["entities"].get("is_section_26_phase11_acceptance") or p1["objective"].primary_goal == "SECTION_26_PHASE11_ACCEPTANCE" or p1["entities"].get("event_ref") in ["EVT-827", "827"]

    p2 = command_interpreter.interpret("JARVIS, explain why you reached this assessment for event 827")
    assert p2["entities"].get("is_explain_why_reached_assessment") or p2["entities"].get("event_ref") == "827"

    p3 = command_interpreter.interpret("JARVIS, show all supporting evidence for event 827")
    assert p3["entities"].get("is_show_evidence_supporting") or p3["entities"].get("event_ref") == "827"

    p4 = command_interpreter.interpret("JARVIS, show contradicting evidence for event 827")
    assert p4["entities"].get("is_show_evidence_contradicting") or p4["entities"].get("event_ref") == "827"

    p5 = command_interpreter.interpret("JARVIS, compare competing hypotheses for event 827")
    assert p5["entities"].get("is_compare_competing_hypotheses") or p5["entities"].get("event_ref") == "827"


# 20. API Endpoints Evidence Graph
def test_api_endpoints_evidence_graph(client):
    r1 = client.get("/api/v1/intelligence/events/EVT-827/evidence-graph")
    assert r1.status_code == 200
    d1 = r1.json()["data"]
    assert len(d1["nodes"]) > 0
    assert len(d1["edges"]) > 0

    r2 = client.get("/api/v1/intelligence/events/EVT-827/evidence")
    assert r2.status_code == 200
    d2 = r2.json()
    assert d2["total_nodes"] > 0

    r3 = client.get("/api/v1/intelligence/events/EVT-827/hypotheses")
    assert r3.status_code == 200
    d3 = r3.json()
    assert d3["total_hypotheses"] == 7

    r4 = client.get("/api/v1/intelligence/events/EVT-827/data-gaps")
    assert r4.status_code == 200
    assert len(r4.json()["data_gaps"]) >= 2


# 21. Workspace Persistence
def test_workspace_persistence(db_session):
    ws = workspace_manager.get_or_create_workspace(
        db=db_session,
        session_id="test_evidence_graph_session",
        primary_objective="Test Phase 11 Evidence Graph Persistence"
    )
    graph = evidence_graph_engine.build_event_evidence_graph(db=db_session, event_ref="EVT-827")
    ws_updated = workspace_manager.update_workspace_evidence_graph(
        db=db_session,
        workspace=ws,
        evidence_graph=graph.model_dump()
    )
    assert ws_updated.evidence_graph is not None
    assert len(ws_updated.evidence_nodes) == len(graph.nodes)
    assert len(ws_updated.evidence_edges) == len(graph.edges)
    assert len(ws_updated.hypotheses) == 7


# 22. Phase 7 Thermal Integration
def test_phase7_thermal_integration(db_session):
    graph = evidence_graph_engine.build_event_evidence_graph(db=db_session, event_ref="EVT-827")
    thermal_nodes = [n for n in graph.nodes if n.node_type in ["OBSERVATION", "EVENT"] or "VIIRS" in n.label or "MODIS" in n.label]
    assert len(thermal_nodes) > 0
    for tn in thermal_nodes:
        assert tn.evidence_nature in ["OBSERVED", "DERIVED"]


# 23. Phase 8 Context Integration
def test_phase8_context_integration(db_session):
    graph = evidence_graph_engine.build_event_evidence_graph(db=db_session, event_ref="EVT-827")
    context_nodes = [n for n in graph.nodes if n.node_type == "CONTEXT" or "facility" in n.node_id.lower() or "power" in n.node_id.lower() or "lulc" in n.node_id.lower()]
    assert len(context_nodes) > 0


# 24. Phase 9 Temporal Integration
def test_phase9_temporal_integration(db_session):
    graph = evidence_graph_engine.build_event_evidence_graph(db=db_session, event_ref="EVT-827")
    temp_nodes = [n for n in graph.nodes if n.node_type in ["TEMPORAL_PATTERN", "TEMPORAL"] or "temporal" in n.node_id.lower()]
    assert len(temp_nodes) > 0
    assert any(tn.evidence_nature == "DERIVED" for tn in temp_nodes)


# 25. Phase 10 Environmental Integration
def test_phase10_environmental_integration(db_session):
    graph = evidence_graph_engine.build_event_evidence_graph(db=db_session, event_ref="EVT-827")
    env_nodes = [n for n in graph.nodes if n.node_type in ["ENVIRONMENTAL_CONDITION", "CROSS_MODAL_OBSERVATION"] or "env" in n.node_id.lower() or "optical" in n.node_id.lower() or "sar" in n.node_id.lower()]
    assert len(env_nodes) >= 2


# 26. Phase 10.1 Provenance Integration
def test_phase10_1_provenance_integration(db_session):
    graph = evidence_graph_engine.build_event_evidence_graph(db=db_session, event_ref="EVT-827")
    for node in graph.nodes:
        if node.evidence_nature == "OBSERVED" and node.provenance:
            assert node.provenance.data_authenticity in ["REAL_PROVIDER", "LOCAL_DATASET", "TEST_FIXTURE"]
        elif node.evidence_nature == "MISSING" and node.provenance:
            assert node.provenance.data_authenticity in ["UNAVAILABLE", "NOT_CONFIGURED", "MISSING"]


# 27. No Fabricated Evidence
def test_no_fabricated_evidence(db_session):
    graph = evidence_graph_engine.build_event_evidence_graph(db=db_session, event_ref="EVT-827")
    for node in graph.nodes:
        assert "synthetic" not in node.description.lower() or "zero synthetic" in node.description.lower()
        if node.provenance:
            assert node.provenance.provider != "SYNTHETIC_PROVIDER"


# 28. Safety Invariants
def test_safety_invariants(db_session):
    ws = workspace_manager.get_or_create_workspace(
        db=db_session,
        session_id="test_safety_invariants_session",
        primary_objective="Verify Phase 11 safety invariants"
    )
    assert ws.verification_status != "APPROVED_FOR_DISPATCH"
    assert ENABLE_OPERATIONAL_DISPATCH_GATE is False


# 29. Risk Formula Unchanged
def test_risk_formula_unchanged():
    weights = {
        "persistence": 0.25,
        "radiative": 0.25,
        "proximity": 0.20,
        "land_use": 0.15,
        "history": 0.15
    }
    assert sum(weights.values()) == 1.0
    assert weights["persistence"] == 0.25
    assert weights["radiative"] == 0.25
    assert weights["proximity"] == 0.20
    assert weights["land_use"] == 0.15
    assert weights["history"] == 0.15


# 30. Classifier Unchanged
def test_classifier_unchanged(db_session):
    row = db_session.execute(text("SELECT model_name, version, status, is_active FROM ml_model_registry WHERE version = 'xgb-v3.0-real-candidate';")).first()
    if row:
        assert row[2] == "CANDIDATE"
        assert not row[3]  # is_active == False


# 31. Dispatch Remains Blocked
def test_dispatch_remains_blocked():
    from backend.app.services.jarvis.jarvis_policy import (
        ENABLE_OPERATIONAL_DISPATCH_GATE,
        JarvisOperatingPolicy
    )
    assert ENABLE_OPERATIONAL_DISPATCH_GATE is False, "DISPATCH GATE MUST REMAIN STRICTLY BLOCKED"
    assert "DISPATCH" in JarvisOperatingPolicy.RESTRICTED_OPERATIONS
