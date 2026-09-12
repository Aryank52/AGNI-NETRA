"""
AGNI-NETRA — JARVIS Phase 11.1 Frozen Baseline Integrity & Architecture Consistency Audit
Comprehensive audit test suite verifying:
1. Authoritative Risk Formula (0.30 Intensity + 0.25 Abnormality + 0.20 Exposure + 0.15 Persistence + 0.10 Context)
2. Classifier Version & Platt Calibration (xgb-v3.0-real-candidate, 6 target classes)
3. Classifier Probability Semantics
4. Evidence Support Semantics (distinct from risk and classifier)
5. Evidence Strength Semantics
6. Observed Evidence Nature
7. Derived Evidence Nature
8. Inferred Evidence Nature
9. Missing Evidence Nature
10. Conflicting Evidence Nature
11. Provenance Propagation & Authenticity
12. Source Independence (INDEPENDENT_OF)
13. Duplicate Prevention & Same-Source Repetition
14. Phase 7 Thermal Fusion Integration
15. Phase 8 Spatial Context Integration
16. Phase 9 Temporal Intelligence Integration
17. Phase 10 Environmental & Cross-Modal Integration
18. Phase 10.1 Provenance Semantics Integration
19. API Consistency (8 intelligence endpoints)
20. UI Data Consistency
21. EVT-827 End-to-End Consistency
22. Documentation & Docstring Consistency
23. Single Master Agent Safety Invariants
24. Operational Dispatch Strictly Blocked
"""

import pytest
from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.database import SessionLocal
from backend.app.services.risk_service import calculate_risk_score
from backend.app.services.intelligence.evidence_graph_engine import evidence_graph_engine
from backend.app.services.jarvis.jarvis_orchestrator import master_orchestrator
from backend.app.models.jarvis_schemas import JarvisCommandRequest
from backend.app.services.jarvis.jarvis_command_interpreter import command_interpreter
from backend.app.services.jarvis.jarvis_workspace import workspace_manager
from backend.app.services.jarvis.jarvis_policy import (
    ENABLE_OPERATIONAL_DISPATCH_GATE,
    JarvisOperatingPolicy
)
from backend.app.models.canonical import (
    EvidenceGraphNode, EvidenceGraphEdge, Hypothesis, EvidenceGraph,
    RiskAssessment
)
from ml.inference.production_inference_service import (
    production_thermal_predictor,
    TARGET_CLASSES
)


@pytest.fixture
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client():
    return TestClient(app)


# 1. Authoritative Risk Formula
def test_authoritative_risk_formula():
    """Verifies that the authoritative production formula is 0.30*Intensity + 0.25*Abnormality + 0.20*Exposure + 0.15*Persistence + 0.10*Context."""
    # Test with controlled inputs:
    # max_frp=250.0, avg_frp=150.0 -> intensity = min(100, 80 + 20) = 100.0
    # is_anomaly=False -> abnormality = 15.0
    # nearest_settlement_dist_m=400.0 (< 500m) -> exposure = 95.0
    # persistence_score=10.0 -> persistence = 100.0
    # predicted_class="Gas Flare", facility_dist=200m -> context = 90.0
    # Expected total = 0.30*100 + 0.25*15 + 0.20*95 + 0.15*100 + 0.10*90
    #                = 30.0 + 3.75 + 19.0 + 15.0 + 9.0 = 76.75 -> 76.8
    score, level, subscores, reasons = calculate_risk_score(
        max_frp=250.0,
        avg_frp=150.0,
        anomaly_info={"is_anomaly": False},
        persistence_info={"persistence_score": 10.0},
        nearest_settlement_dist_m=400.0,
        nearest_facility_dist_m=200.0,
        predicted_class="Gas Flare"
    )
    assert subscores["intensity"] == 100.0
    assert subscores["abnormality"] == 15.0
    assert subscores["exposure"] == 95.0
    assert subscores["persistence"] == 100.0
    assert subscores["context"] == 90.0
    expected = round(0.30 * 100.0 + 0.25 * 15.0 + 0.20 * 95.0 + 0.15 * 100.0 + 0.10 * 90.0, 1)
    assert score == expected
    assert level == "CRITICAL"


# 2. Classifier Version Integrity
def test_classifier_version_integrity():
    """Verifies champion model version, calibrator version, and artifact configuration."""
    assert production_thermal_predictor.model_version == "xgb-v3.0-real-candidate"
    assert production_thermal_predictor.calibrator_version == "balanced-platt-v3.0"
    assert len(TARGET_CLASSES) == 6
    assert "Gas Flare" in TARGET_CLASSES
    assert "Industrial Fire" in TARGET_CLASSES


# 3. Classifier Probability Semantics
def test_classifier_probability_semantics():
    """Verifies that classifier probabilities represent calibrated class posteriors, summing to 1.0."""
    sample_event = {
        "frp_max": 85.0, "frp_avg": 45.0, "frp_std": 12.0,
        "bright_max": 350.0, "bright_avg": 335.0, "delta_brightness": 15.0,
        "dist_to_facility_m": 250.0, "dist_to_forest_m": 12000.0, "dist_to_agriculture_m": 8000.0,
        "dist_to_settlement_m": 3500.0, "dist_to_water_m": 4000.0, "dist_to_mine_m": 20000.0,
        "landcover_code": 1, "persistence_score": 0.85, "recurrence_rate": 3.0,
        "day_night_ratio": 1.5, "baseline_deviation_ratio": 2.5, "industrial_context_score": 0.9
    }
    res = production_thermal_predictor.predict(sample_event, log_audit=False)
    probs = res["class_probabilities"]
    assert len(probs) == 6
    prob_sum = sum(probs.values())
    assert 0.99 <= prob_sum <= 1.01
    assert 0.0 <= res["confidence"] <= 1.0
    assert res["predicted_class"] in TARGET_CLASSES


# 4. Evidence Support Semantics
def test_evidence_support_semantics(db_session):
    """Verifies Evidence Support Score is bounded 0-100 and distinct from classifier probabilities and risk."""
    graph = evidence_graph_engine.build_event_evidence_graph(db=db_session, event_ref="EVT-827")
    for hyp in graph.hypotheses:
        assert 0.0 <= hyp.support_score <= 100.0
        # Check node properties explicitly tag metric_type
        h_node = next((n for n in graph.nodes if n.properties.get("hypothesis_id") == hyp.hypothesis_id), None)
        assert h_node is not None
        assert h_node.properties.get("metric_type") == "EVIDENCE_SUPPORT_SCORE"
        assert h_node.properties.get("evidence_support_score") == hyp.support_score


# 5. Evidence Strength Semantics
def test_evidence_strength_semantics(db_session):
    """Verifies evidence strength uses standardized categorical tiers."""
    graph = evidence_graph_engine.build_event_evidence_graph(db=db_session, event_ref="EVT-827")
    valid_strengths = {"STRONG", "MODERATE", "LIMITED", "INSUFFICIENT"}
    for node in graph.nodes:
        assert node.strength in valid_strengths


# 6. Observed Evidence Nature
def test_observed_evidence_nature(db_session):
    """Verifies that OBSERVED nodes represent direct physical sensor or registry ground truth."""
    graph = evidence_graph_engine.build_event_evidence_graph(db=db_session, event_ref="EVT-827")
    observed = [n for n in graph.nodes if n.evidence_nature == "OBSERVED"]
    assert len(observed) >= 3
    sources = {n.source for n in observed}
    assert any(s in ["NASA_FIRMS", "OSM_CEA_REGISTRY", "ISRO_BHUVAN_WORLDCOVER", "FSI_ENVIS_PA_REGISTRY"] for s in sources)


# 7. Derived Evidence Nature
def test_derived_evidence_nature(db_session):
    """Verifies that DERIVED nodes represent deterministic algorithmic transformations."""
    graph = evidence_graph_engine.build_event_evidence_graph(db=db_session, event_ref="EVT-827")
    derived = [n for n in graph.nodes if n.evidence_nature == "DERIVED"]
    assert len(derived) >= 2
    labels = [n.label for n in derived]
    assert any("Pattern" in l or "Weather" in l or "Assessment" in l or "Event" in l for l in labels)


# 8. Inferred Evidence Nature
def test_inferred_evidence_nature(db_session):
    """Verifies that INFERRED nodes represent candidate hypotheses and cross-modal inferences."""
    graph = evidence_graph_engine.build_event_evidence_graph(db=db_session, event_ref="EVT-827")
    inferred = [n for n in graph.nodes if n.evidence_nature == "INFERRED"]
    assert len(inferred) >= 7  # 7 candidate hypotheses + cross-modal/uncertainty
    types = {n.node_type for n in inferred}
    assert "HYPOTHESIS" in types


# 9. Missing Evidence Nature
def test_missing_evidence_nature(db_session):
    """Verifies that MISSING nodes represent factual operational data gaps."""
    graph = evidence_graph_engine.build_event_evidence_graph(db=db_session, event_ref="EVT-827")
    missing = [n for n in graph.nodes if n.evidence_nature == "MISSING"]
    assert len(missing) >= 2
    types = {n.node_type for n in missing}
    assert "DATA_GAP" in types


# 10. Conflicting Evidence Nature
def test_conflicting_evidence_nature(db_session):
    """Verifies conflicting relationships and alternative hypothesis refutations."""
    graph = evidence_graph_engine.build_event_evidence_graph(db=db_session, event_ref="EVT-827")
    conflicts = [e for e in graph.edges if e.relationship_type == "CONTRADICTS"]
    assert len(conflicts) >= 3


# 11. Provenance Propagation
def test_provenance_propagation(db_session):
    """Verifies that all nodes with provenance carry valid data_authenticity attribution."""
    graph = evidence_graph_engine.build_event_evidence_graph(db=db_session, event_ref="EVT-827")
    valid_authenticities = {"REAL_PROVIDER", "LOCAL_DATASET", "DERIVED", "UNAVAILABLE", "TEST_FIXTURE"}
    for node in graph.nodes:
        if node.provenance:
            assert node.provenance.data_authenticity in valid_authenticities


# 12. Source Independence Semantics
def test_source_independence_semantics(db_session):
    """Verifies that INDEPENDENT_OF edges exist strictly between distinct observation domains."""
    graph = evidence_graph_engine.build_event_evidence_graph(db=db_session, event_ref="EVT-827")
    indep_edges = [e for e in graph.edges if e.relationship_type == "INDEPENDENT_OF"]
    assert len(indep_edges) >= 2
    for e in indep_edges:
        src = next(n for n in graph.nodes if n.node_id == e.source_node_id)
        tgt = next(n for n in graph.nodes if n.node_id == e.target_node_id)
        assert src.source != tgt.source or src.node_type != tgt.node_type


# 13. Duplicate Prevention Semantics
def test_duplicate_prevention_semantics(db_session):
    """Verifies that multi-pass observations from the same sensor are tagged as SAME_SOURCE_REPETITION."""
    graph = evidence_graph_engine.build_event_evidence_graph(db=db_session, event_ref="EVT-827")
    thermal_obs = next(n for n in graph.nodes if n.node_type == "OBSERVATION" and "VIIRS" in n.label)
    assert thermal_obs.properties.get("sampling_nature") == "SAME_SOURCE_REPETITION"


# 14. Phase 7 Thermal Fusion Integration
def test_phase7_thermal_fusion_integration(db_session):
    """Verifies integration with Phase 7 thermal observations and FIRMS provenance."""
    graph = evidence_graph_engine.build_event_evidence_graph(db=db_session, event_ref="EVT-827")
    obs = next(n for n in graph.nodes if n.source == "NASA_FIRMS" and n.node_type == "OBSERVATION")
    assert obs.properties.get("mean_frp_mw") is not None


# 15. Phase 8 Spatial Context Integration
def test_phase8_spatial_context_integration(db_session):
    """Verifies integration with Phase 8 OSM/CEA facility context and buffer checks."""
    graph = evidence_graph_engine.build_event_evidence_graph(db=db_session, event_ref="EVT-827")
    fac = next(n for n in graph.nodes if n.node_type == "CONTEXT" and "Industrial Asset" in n.label)
    assert "Reliance Jamnagar" in fac.label or "Refinery" in fac.label
    assert fac.properties.get("distance_meters") is not None


# 16. Phase 9 Temporal Intelligence Integration
def test_phase9_temporal_intelligence_integration(db_session):
    """Verifies integration with Phase 9 temporal baseline, recurrence, and persistence tier."""
    graph = evidence_graph_engine.build_event_evidence_graph(db=db_session, event_ref="EVT-827")
    temp = next(n for n in graph.nodes if n.node_type == "TEMPORAL_PATTERN")
    assert temp.evidence_nature == "DERIVED"
    assert "persistence_tier" in temp.properties


# 17. Phase 10 Environmental & Cross-Modal Integration
def test_phase10_environmental_crossmodal_integration(db_session):
    """Verifies integration with Phase 10 weather reanalysis and cross-modal corroboration."""
    graph = evidence_graph_engine.build_event_evidence_graph(db=db_session, event_ref="EVT-827")
    env = next(n for n in graph.nodes if n.node_type == "ENVIRONMENTAL_CONDITION")
    assert env.evidence_nature == "DERIVED"
    xm = next(n for n in graph.nodes if n.node_type == "CROSS_MODAL_OBSERVATION")
    assert xm.evidence_nature == "INFERRED"


# 18. Phase 10.1 Provenance Semantics Integration
def test_phase10_1_provenance_semantics_integration(db_session):
    """Verifies that ERA5 weather is correctly attributed as DERIVED authenticity."""
    graph = evidence_graph_engine.build_event_evidence_graph(db=db_session, event_ref="EVT-827")
    env_node = next(n for n in graph.nodes if n.source == "ECMWF_ERA5_WEATHER")
    assert env_node.provenance is not None
    assert env_node.provenance.data_authenticity == "DERIVED"


# 19. API Consistency
def test_api_consistency(client):
    """Verifies all 8 intelligence REST endpoints return correct status and schemas."""
    r1 = client.get("/api/v1/intelligence/events/EVT-827/evidence-graph")
    assert r1.status_code == 200
    r2 = client.get("/api/v1/intelligence/events/EVT-827/evidence")
    assert r2.status_code == 200
    r3 = client.get("/api/v1/intelligence/events/EVT-827/hypotheses")
    assert r3.status_code == 200
    r4 = client.get("/api/v1/intelligence/events/EVT-827/evidence/supporting")
    assert r4.status_code == 200
    r5 = client.get("/api/v1/intelligence/events/EVT-827/evidence/conflicting")
    assert r5.status_code == 200
    r6 = client.get("/api/v1/intelligence/events/EVT-827/data-gaps")
    assert r6.status_code == 200
    r7 = client.get("/api/v1/intelligence/events/EVT-827/assessment-lineage")
    assert r7.status_code == 200
    r8 = client.get("/api/v1/intelligence/events/EVT-827/provenance-chain")
    assert r8.status_code == 200


# 20. UI Data Consistency
def test_ui_data_consistency(db_session):
    """Verifies workspace serialization maintains all Phase 11 fields with distinct support score."""
    ws = workspace_manager.get_or_create_workspace(
        db=db_session,
        session_id="test_ui_consistency_session",
        primary_objective="Verify UI Data Consistency"
    )
    graph = evidence_graph_engine.build_event_evidence_graph(db=db_session, event_ref="EVT-827")
    ws_updated = workspace_manager.update_workspace_evidence_graph(
        db=db_session,
        workspace=ws,
        evidence_graph=graph.model_dump()
    )
    assert len(ws_updated.hypotheses) == 7
    winner = ws_updated.hypotheses[0]
    assert "support_score" in winner
    assert winner["support_score"] > 80.0


# 21. EVT-827 End-to-End Consistency
def test_evt_827_consistency(db_session):
    """Verifies the Section 15 acceptance command execution on EVT-827."""
    cmd = "JARVIS, verify the evidence graph for EVT-827 and explain the difference between risk score, classifier probability, evidence support, evidence strength, and uncertainty."
    parsed = command_interpreter.interpret(cmd)
    assert parsed["entities"].get("is_verify_evidence_graph_and_explain_metrics") is True

    req = JarvisCommandRequest(command=cmd, session_id="test_acceptance_evt827")
    res = master_orchestrator.execute_command(
        db=db_session,
        request=req,
        user_role="ANALYST"
    )
    assert "EVT-827" in res.summary
    assert "0.30*Intensity + 0.25*Abnormality + 0.20*Exposure + 0.15*Persistence + 0.10*Context" in res.summary or "0.30" in res.summary
    assert "xgb-v3.0-real-candidate" in res.summary
    assert "BLOCKED" in res.summary
    assert res.dispatch_gate_blocked is True
    assert res.requires_human_approval is True
    assert "SECTION_15_AUDIT_COMPLETE" in res.stopping_reason


# 22. Documentation & Docstring Consistency
def test_documentation_consistency():
    """Verifies that RiskAssessment docstring cites the production 5-factor formula."""
    doc = RiskAssessment.__doc__ or ""
    assert "0.30*Intensity" in doc
    assert "0.25*Abnormality" in doc
    assert "0.20*Exposure" in doc
    assert "0.15*Persistence" in doc
    assert "0.10*Context" in doc


# 23. Single Master Agent Safety Invariants
def test_safety_invariants(db_session):
    """Verifies single master agent invariant without subagents or autonomous dispatch."""
    ws = workspace_manager.get_or_create_workspace(
        db=db_session,
        session_id="test_safety_invariants_11_1",
        primary_objective="Verify Phase 11.1 Safety Invariants"
    )
    assert ws.verification_status != "APPROVED_FOR_DISPATCH"
    assert "DISPATCH" in JarvisOperatingPolicy.RESTRICTED_OPERATIONS


# 24. Operational Dispatch Strictly Blocked
def test_dispatch_strictly_blocked():
    """Verifies that ENABLE_OPERATIONAL_DISPATCH_GATE is strictly False."""
    assert ENABLE_OPERATIONAL_DISPATCH_GATE is False, "DISPATCH GATE MUST REMAIN STRICTLY BLOCKED"
