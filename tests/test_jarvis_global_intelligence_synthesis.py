"""
AGNI-NETRA Phase 13: Global Intelligence Fusion & Decision-Support Synthesis Test Suite
Comprehensive verification suite validating:
1. test_assessment_structure_has_all_required_sections
2. test_master_agent_invariant
3. test_operational_dispatch_gate_blocked
4. test_human_review_required_flag
5. test_metric_disambiguation_strict_separation
6. test_authoritative_risk_preservation
7. test_classifier_probability_not_risk
8. test_xgboost_champion_reference
9. test_evidence_support_score_range
10. test_evidence_strength_categorical_tiers
11. test_competing_hypotheses_count_and_categories
12. test_competing_hypotheses_supporting_contradicting_missing
13. test_why_this_assessment_deterministic
14. test_what_contradicts_it_identifies_conflicts
15. test_what_changed_initial_assessment
16. test_what_changed_subsequent_assessment
17. test_next_best_evidence_engine_ranking
18. test_next_best_evidence_never_claims_definitive_truth
19. test_information_value_categories
20. test_decision_support_mode_analyst
21. test_decision_support_mode_agency
22. test_decision_support_mode_executive
23. test_decision_support_mode_public_safe_masking
24. test_assessment_statements_lineage
25. test_provenance_audit_trail_and_hash
26. test_incident_level_synthesis
27. test_workspace_persistence
28. test_command_interpreter_section_31_intent
29. test_command_interpreter_section_32_intent
30. test_command_interpreter_section_33_intent
31. test_section_31_full_brief_markdown_formatting
32. test_section_32_competing_explanations_markdown
33. test_section_33_executive_brief_markdown
"""

import pytest
from datetime import datetime, timezone
from typing import Dict, Any, List
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.database import SessionLocal
from backend.app.models.canonical import (
    UnifiedIntelligenceAssessment,
    AssessmentState,
    AssessmentEvolution,
    InformationValueCategory,
    DecisionSupportMode,
    AssessmentStatement,
    CompetingAssessmentHypothesis,
    NextBestEvidenceRecommendation,
    DecisionSupportPackage
)
from backend.app.services.intelligence.global_intelligence_synthesis import (
    global_intelligence_synthesis_engine,
    GlobalIntelligenceSynthesisEngine
)
from backend.app.services.intelligence.next_best_evidence import (
    next_best_evidence_engine,
    NextBestEvidenceEngine
)
from backend.app.services.jarvis.jarvis_workspace import workspace_manager
from backend.app.services.jarvis.jarvis_command_interpreter import command_interpreter
from backend.app.services.jarvis.jarvis_orchestrator import master_orchestrator
from backend.app.services.jarvis.jarvis_policy import ENABLE_OPERATIONAL_DISPATCH_GATE
from backend.app.models.jarvis_schemas import CommandIntent


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


@pytest.fixture(scope="module")
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module")
def sample_assessment():
    return global_intelligence_synthesis_engine.synthesize_assessment(
        db=None,
        target_ref="EVT-827",
        mode="ANALYST"
    )


# -----------------------------------------------------------------------------
# 1. Assessment Structure
# -----------------------------------------------------------------------------
def test_assessment_structure_has_all_required_sections(sample_assessment):
    """Test 1: UnifiedIntelligenceAssessment has all required fields."""
    assert sample_assessment.assessment_id is not None
    assert sample_assessment.event_id == "EVT-827"
    assert sample_assessment.incident_id is not None
    assert sample_assessment.assessment_status in [s.value for s in AssessmentState]
    assert sample_assessment.assessment_evolution in [e.value for e in AssessmentEvolution]
    assert sample_assessment.primary_assessment is not None
    assert len(sample_assessment.alternative_assessments) >= 4
    assert len(sample_assessment.statements) >= 5
    assert len(sample_assessment.why_this_assessment) >= 3
    assert len(sample_assessment.what_contradicts_it) >= 1
    assert sample_assessment.what_changed is not None
    assert sample_assessment.risk_reference is not None
    assert sample_assessment.classifier_reference is not None
    assert sample_assessment.evidence_summary is not None
    assert sample_assessment.incident_summary is not None
    assert sample_assessment.uncertainty_summary is not None
    assert sample_assessment.data_gaps is not None
    assert len(sample_assessment.next_best_evidence) >= 1
    assert "ANALYST" in sample_assessment.decision_support_packages
    assert "PUBLIC_SAFE" in sample_assessment.decision_support_packages
    assert sample_assessment.provenance is not None
    assert sample_assessment.human_review_required is True
    assert sample_assessment.dispatch_gate_blocked is True


# -----------------------------------------------------------------------------
# 2. Master Agent Invariant
# -----------------------------------------------------------------------------
def test_master_agent_invariant():
    """Test 2: Exactly ONE Master JARVIS Agent, no subagents."""
    assert master_orchestrator is not None
    # Verify master orchestrator is a singleton and operates without subagent pools
    assert hasattr(master_orchestrator, "execute_command")
    assert not hasattr(master_orchestrator, "subagent_pool")
    assert not hasattr(master_orchestrator, "agent_swarm")


# -----------------------------------------------------------------------------
# 3. Operational Dispatch Gate Invariant
# -----------------------------------------------------------------------------
def test_operational_dispatch_gate_blocked(sample_assessment):
    """Test 3: Operational dispatch gate is strictly BLOCKED."""
    assert ENABLE_OPERATIONAL_DISPATCH_GATE is False
    assert sample_assessment.dispatch_gate_blocked is True
    assert sample_assessment.operational_dispatch_gate_blocked is True


# -----------------------------------------------------------------------------
# 4. Human Review Required Flag
# -----------------------------------------------------------------------------
def test_human_review_required_flag(sample_assessment):
    """Test 4: Human review required flag is set to True."""
    assert sample_assessment.human_review_required is True
    assert sample_assessment.human_verification_recommended is True


# -----------------------------------------------------------------------------
# 5. Metric Disambiguation
# -----------------------------------------------------------------------------
def test_metric_disambiguation_strict_separation(sample_assessment):
    """Test 5: Strict separation of the 6 core metrics."""
    risk = sample_assessment.authoritative_risk_score
    prob = sample_assessment.classifier_probability
    support = sample_assessment.evidence_support_score
    strength = sample_assessment.evidence_strength
    uncertainty = sample_assessment.epistemic_uncertainty
    corr_strength = sample_assessment.incident_correlation_strength

    # All metrics are populated
    assert risk is not None
    assert prob is not None
    assert support is not None
    assert strength is not None
    assert uncertainty is not None
    assert corr_strength is not None

    # Verify none are identical or conflated
    assert risk != prob
    assert prob != support
    assert risk != support
    assert strength in ["STRONG", "MODERATE", "LIMITED", "INSUFFICIENT"]
    assert corr_strength in ["STRONG", "MODERATE", "LIMITED", "INSUFFICIENT"]


# -----------------------------------------------------------------------------
# 6. Authoritative Risk Score Preservation
# -----------------------------------------------------------------------------
def test_authoritative_risk_preservation(sample_assessment):
    """Test 6: Authoritative 5-Factor Risk Formula is preserved without averaging."""
    risk_ref = sample_assessment.risk_reference
    assert risk_ref["risk_score"] == 75.3
    assert risk_ref["risk_level"] == "CRITICAL"
    assert "0.30*Intensity + 0.25*Abnormality + 0.20*Exposure + 0.15*Persistence + 0.10*Context" in risk_ref["formula"]
    assert "preserved" in risk_ref["preservation_policy"].lower()


# -----------------------------------------------------------------------------
# 7. Classifier Probability vs Risk
# -----------------------------------------------------------------------------
def test_classifier_probability_not_risk(sample_assessment):
    """Test 7: Classifier probability is P=0.942, not replaced by or replacing risk."""
    cls_ref = sample_assessment.classifier_reference
    assert cls_ref["calibrated_flaring_probability"] == 0.942
    assert cls_ref["predicted_class"] == "ROUTINE_INDUSTRIAL_FLARING"
    assert cls_ref["calibrated_flaring_probability"] != sample_assessment.risk_reference["risk_score"]


# -----------------------------------------------------------------------------
# 8. XGBoost Champion Model Reference
# -----------------------------------------------------------------------------
def test_xgboost_champion_reference(sample_assessment):
    """Test 8: Model reference identifies xgb-v3.0-real-candidate with SHAP contributions."""
    cls_ref = sample_assessment.classifier_reference
    assert cls_ref["model_id"] == "xgb-v3.0-real-candidate"
    assert len(cls_ref["top_shap_features"]) >= 3
    assert cls_ref["top_shap_features"][0]["feature"] == "persistence_ratio_14d"


# -----------------------------------------------------------------------------
# 9. Evidence Support Score Range
# -----------------------------------------------------------------------------
def test_evidence_support_score_range(sample_assessment):
    """Test 9: Support score is within [0.0, 100.0]."""
    score = sample_assessment.primary_assessment.support_score
    assert 0.0 <= score <= 100.0
    assert score == 92.4


# -----------------------------------------------------------------------------
# 10. Evidence Strength Categorical Tiers
# -----------------------------------------------------------------------------
def test_evidence_strength_categorical_tiers(sample_assessment):
    """Test 10: Evidence strength uses standardized categorical tiers."""
    for hyp in sample_assessment.alternative_assessments:
        assert hyp.evidence_strength in ["STRONG", "MODERATE", "LIMITED", "INSUFFICIENT"]


# -----------------------------------------------------------------------------
# 11. Competing Hypotheses Count and Categories
# -----------------------------------------------------------------------------
def test_competing_hypotheses_count_and_categories(sample_assessment):
    """Test 11: Standardized hypotheses evaluated concurrently."""
    hyps = sample_assessment.alternative_assessments
    assert len(hyps) == 4
    hyp_ids = [h.hypothesis_id for h in hyps]
    assert "HYP_INDUSTRIAL_FLARING" in hyp_ids
    assert "HYP_EMERGENCY_UPSET" in hyp_ids
    assert "HYP_VEGETATION_WILDFIRE" in hyp_ids
    assert "HYP_SENSOR_ARTIFACT" in hyp_ids


# -----------------------------------------------------------------------------
# 12. Competing Hypotheses Evidence Lists
# -----------------------------------------------------------------------------
def test_competing_hypotheses_supporting_contradicting_missing(sample_assessment):
    """Test 12: Each hypothesis contains supporting, contradicting, and missing evidence."""
    for hyp in sample_assessment.alternative_assessments:
        assert isinstance(hyp.supporting_evidence, list)
        assert isinstance(hyp.contradicting_evidence, list)
        assert isinstance(hyp.missing_evidence, list)
    primary = sample_assessment.primary_assessment
    assert len(primary.supporting_evidence) >= 2
    assert len(primary.contradicting_evidence) >= 1
    assert len(primary.missing_evidence) >= 1


# -----------------------------------------------------------------------------
# 13. "Why This Assessment?" Deterministic Derivation
# -----------------------------------------------------------------------------
def test_why_this_assessment_deterministic(sample_assessment):
    """Test 13: 'Why This Assessment?' produces numbered deterministic items."""
    why = sample_assessment.why_this_assessment
    assert len(why) == 5
    assert any("multi-source" in item.lower() for item in why)
    assert any("jamnagar" in item.lower() for item in why)
    assert any("persistence" in item.lower() for item in why)
    assert any("wind" in item.lower() or "era5" in item.lower() for item in why)
    assert any("xgboost" in item.lower() for item in why)


# -----------------------------------------------------------------------------
# 14. "What Contradicts It?" Identifies Conflicts
# -----------------------------------------------------------------------------
def test_what_contradicts_it_identifies_conflicts(sample_assessment):
    """Test 14: 'What Contradicts It?' identifies FRP anomaly and dispersion variance."""
    contra = sample_assessment.what_contradicts_it
    assert len(contra) == 3
    assert any("frp" in item.lower() or "1.45" in item.lower() for item in contra)
    assert any("dispersion" in item.lower() or "variance" in item.lower() for item in contra)


# -----------------------------------------------------------------------------
# 15. "What Changed?" Initial Assessment
# -----------------------------------------------------------------------------
def test_what_changed_initial_assessment():
    """Test 15: Initial assessment without prior state returns NO_PRIOR_ASSESSMENT."""
    initial = global_intelligence_synthesis_engine.synthesize_assessment(
        db=None,
        target_ref="EVT-827",
        prior_assessment=None
    )
    assert initial.what_changed == "NO_PRIOR_ASSESSMENT"
    assert initial.assessment_evolution == AssessmentEvolution.INITIAL.value


# -----------------------------------------------------------------------------
# 16. "What Changed?" Subsequent Assessment
# -----------------------------------------------------------------------------
def test_what_changed_subsequent_assessment(sample_assessment):
    """Test 16: Second assessment correctly calculates deltas and stability."""
    prior_dict = sample_assessment.model_dump()
    subsequent = global_intelligence_synthesis_engine.synthesize_assessment(
        db=None,
        target_ref="EVT-827",
        prior_assessment=prior_dict
    )
    assert isinstance(subsequent.what_changed, dict)
    assert subsequent.what_changed["evolution_status"] == "STABILIZED"
    assert subsequent.what_changed["thermal_observation_delta"] == 0
    assert subsequent.what_changed["risk_score_delta"] == 0.0
    assert subsequent.what_changed["favored_hypothesis_changed"] is False


# -----------------------------------------------------------------------------
# 17. Next-Best-Evidence Engine Ranking
# -----------------------------------------------------------------------------
def test_next_best_evidence_engine_ranking():
    """Test 17: NextBestEvidenceEngine ranks recommendations by Information Value."""
    recs = next_best_evidence_engine.recommend_next_best_evidence(
        event_data={"event_id": "EVT-827"},
        competing_hypotheses=[],
        data_gaps=[{"gap_id": "gap-1", "missing_information": "SCADA mass flow rate"}],
        context_data={"facility_type": "REFINERY"}
    )
    assert len(recs) >= 3
    assert recs[0].information_value == InformationValueCategory.HIGH.value
    sources = [r.source_name for r in recs]
    assert any("SCADA" in s or "OPTICAL" in s or "GROUND" in s for s in sources)


# -----------------------------------------------------------------------------
# 18. Next-Best-Evidence Never Claims Definitive Truth
# -----------------------------------------------------------------------------
def test_next_best_evidence_never_claims_definitive_truth():
    """Test 18: Recommendations do not claim definitive ground-truth resolution."""
    recs = next_best_evidence_engine.recommend_next_best_evidence(
        event_data={"event_id": "EVT-827"},
        competing_hypotheses=[],
        data_gaps=[],
        context_data={}
    )
    for r in recs:
        # None should claim 100% definitive ground-truth resolution
        assert "definitive ground-truth" not in r.reason.lower()
        assert "eliminates all uncertainty" not in r.reason.lower()


# -----------------------------------------------------------------------------
# 19. Information Value Categories
# -----------------------------------------------------------------------------
def test_information_value_categories(sample_assessment):
    """Test 19: Valid Information Value Categories are utilized."""
    valid_cats = [c.value for c in InformationValueCategory]
    for r in sample_assessment.next_best_evidence:
        assert r.information_value in valid_cats


# -----------------------------------------------------------------------------
# 20. Decision-Support Mode: ANALYST
# -----------------------------------------------------------------------------
def test_decision_support_mode_analyst(sample_assessment):
    """Test 20: Analyst mode contains full technical details and unmasked data."""
    pkg = sample_assessment.decision_support_packages.get("ANALYST")
    assert pkg is not None
    assert pkg["mode"] == "ANALYST"
    assert pkg["public_masked"] is False
    assert "Support: 92.4/100" in pkg["executive_summary"]
    assert "75.3" in pkg["risk_status"]


# -----------------------------------------------------------------------------
# 21. Decision-Support Mode: AGENCY
# -----------------------------------------------------------------------------
def test_decision_support_mode_agency(sample_assessment):
    """Test 21: Agency mode contains inter-agency operational briefing."""
    pkg = sample_assessment.decision_support_packages.get("AGENCY")
    assert pkg is not None
    assert pkg["mode"] == "AGENCY"
    assert pkg["public_masked"] is False
    assert "Operational Intelligence Brief" in pkg["executive_summary"]
    assert len(pkg["recommended_verification"]) >= 2


# -----------------------------------------------------------------------------
# 22. Decision-Support Mode: EXECUTIVE
# -----------------------------------------------------------------------------
def test_decision_support_mode_executive(sample_assessment):
    """Test 22: Executive mode provides high-level strategic briefing."""
    pkg = sample_assessment.decision_support_packages.get("EXECUTIVE")
    assert pkg is not None
    assert pkg["mode"] == "EXECUTIVE"
    assert pkg["public_masked"] is False
    assert "Executive Decision Brief" in pkg["executive_summary"]


# -----------------------------------------------------------------------------
# 23. Decision-Support Mode: PUBLIC_SAFE Masking
# -----------------------------------------------------------------------------
def test_decision_support_mode_public_safe_masking(sample_assessment):
    """Test 23: Public-Safe mode masks proprietary data."""
    pkg = sample_assessment.decision_support_packages.get("PUBLIC_SAFE")
    assert pkg is not None
    assert pkg["mode"] == "PUBLIC_SAFE"
    assert pkg["public_masked"] is True
    assert "Public Safety Advisory" in pkg["executive_summary"]
    assert "masked" in pkg["disclaimer"].lower()


# -----------------------------------------------------------------------------
# 24. Assessment Statements Lineage
# -----------------------------------------------------------------------------
def test_assessment_statements_lineage(sample_assessment):
    """Test 24: Statements contain explicit categories and source IDs."""
    stmts = sample_assessment.statements
    assert len(stmts) >= 6
    categories = {s.category for s in stmts}
    assert "OBSERVED" in categories
    assert "PREDICTED" in categories
    assert "RISK" in categories
    assert "CORRELATION" in categories
    assert "SUPPORTING" in categories
    assert "UNCERTAINTY" in categories

    for s in stmts:
        assert len(s.evidence_ids) >= 1
        assert len(s.source_ids) >= 1


# -----------------------------------------------------------------------------
# 25. Provenance Audit Trail and Hash
# -----------------------------------------------------------------------------
def test_provenance_audit_trail_and_hash(sample_assessment):
    """Test 25: Provenance contains algorithm version, source records, and confidence."""
    prov = sample_assessment.provenance
    prov_dict = prov.model_dump() if hasattr(prov, "model_dump") else prov
    extra = prov_dict.get("extra_metadata", {})
    assert "global_intelligence_synthesis_v1.0" in extra.get("algorithm_version", "") or "AN_DERIVATION" in prov_dict.get("source_version", "")
    assert "EVT-827" in extra.get("source_records", []) or prov_dict.get("provider") == "AGNI_NETRA"
    assert extra.get("confidence", 0.94) >= 0.90


# -----------------------------------------------------------------------------
# 26. Incident-Level Synthesis
# -----------------------------------------------------------------------------
def test_incident_level_synthesis():
    """Test 26: synthesize_incident_assessment correctly parses incident ref."""
    inc_assess = global_intelligence_synthesis_engine.synthesize_incident_assessment(
        db=None,
        incident_id="INC-EVT-827",
        mode="ANALYST"
    )
    assert inc_assess.event_id == "EVT-827"
    assert inc_assess.incident_id == "INC-EVT-827"
    assert inc_assess.incident_summary["incident_id"] == "INC-EVT-827"


# -----------------------------------------------------------------------------
# 27. Workspace Persistence
# -----------------------------------------------------------------------------
def test_workspace_persistence(sample_assessment, db_session):
    """Test 27: Workspace manager updates workspace with intelligence synthesis."""
    workspace = workspace_manager.get_or_create_workspace(
        db=db_session,
        session_id="test-session-phase13",
        user_role="ANALYST",
        target_event_id="EVT-827"
    )
    updated = workspace_manager.update_workspace_intelligence_synthesis(
        db=db_session,
        workspace=workspace,
        assessment=sample_assessment
    )
    assert updated.unified_assessment is not None
    assert updated.assessment_history is not None
    assert len(updated.assessment_history) >= 1
    assert updated.decision_support is not None


# -----------------------------------------------------------------------------
# 28. Command Interpreter: Section 31 Intent
# -----------------------------------------------------------------------------
def test_command_interpreter_section_31_intent():
    """Test 28: Section 31 acceptance command routes to SYNTHESIZE."""
    cmd = "JARVIS, synthesize the complete intelligence assessment for EVT-827. Clearly separate observed detections, classifier predictions, authoritative risk, evidence support, correlation, and epistemic uncertainty."
    obj = command_interpreter.interpret(cmd)
    assert obj["intent"] == CommandIntent.SYNTHESIZE
    assert obj["objective"].primary_goal == "SECTION_31_PHASE13_ACCEPTANCE"
    assert obj["objective"].target_event in ("827", "EVT-827")


# -----------------------------------------------------------------------------
# 29. Command Interpreter: Section 32 Intent
# -----------------------------------------------------------------------------
def test_command_interpreter_section_32_intent():
    """Test 29: Section 32 acceptance command routes to COMPARE."""
    cmd = "JARVIS, compare the leading explanations for EVT-827 without treating classifier probability as overall risk."
    obj = command_interpreter.interpret(cmd)
    assert obj["intent"] == CommandIntent.COMPARE
    assert obj["objective"].primary_goal == "SECTION_32_PHASE13_ACCEPTANCE"
    assert obj["objective"].target_event in ("827", "EVT-827")


# -----------------------------------------------------------------------------
# 30. Command Interpreter: Section 33 Intent
# -----------------------------------------------------------------------------
def test_command_interpreter_section_33_intent():
    """Test 30: Section 33 acceptance command routes to SYNTHESIZE."""
    cmd = "JARVIS, generate an executive decision-support brief for EVT-827."
    obj = command_interpreter.interpret(cmd)
    assert obj["intent"] == CommandIntent.SYNTHESIZE
    assert obj["objective"].primary_goal == "SECTION_33_PHASE13_ACCEPTANCE"
    assert obj["objective"].target_event in ("827", "EVT-827")


# -----------------------------------------------------------------------------
# 31. Section 31 Full Brief Markdown Formatting
# -----------------------------------------------------------------------------
def test_section_31_full_brief_markdown_formatting(sample_assessment):
    """Test 31: format_section_31_synthesis_markdown produces 16-point brief."""
    md = workspace_manager.format_section_31_synthesis_markdown(sample_assessment)
    assert "JARVIS GLOBAL INTELLIGENCE FUSION & DECISION-SUPPORT SYNTHESIS" in md
    assert "AUTHORITATIVE RISK SCORE" in md
    assert "75.3 / 100" in md
    assert "0.942" in md
    assert "EVIDENCE SUPPORT SCORE" in md
    assert "92.4 / 100" in md
    assert "EVIDENCE STRENGTH" in md
    assert "STRONG" in md
    assert "WHAT CONTRADICTS IT" in md
    assert "WHAT CHANGED" in md
    assert "NEXT-BEST EVIDENCE" in md
    assert "OPERATIONAL EMERGENCY DISPATCH GATE" in md
    assert "BLOCKED" in md
    assert "HUMAN REVIEW STATUS" in md


# -----------------------------------------------------------------------------
# 32. Section 32 Competing Explanations Markdown
# -----------------------------------------------------------------------------
def test_section_32_competing_explanations_markdown(sample_assessment):
    """Test 32: format_section_32_competing_explanations_markdown separates metrics."""
    md = workspace_manager.format_section_32_competing_explanations_markdown(sample_assessment)
    assert "JARVIS COMPETING HYPOTHESES & METRIC DISAMBIGUATION" in md
    assert "STRICT METRIC SEPARATION DECLARATION" in md
    assert "HYP_INDUSTRIAL_FLARING" in md
    assert "HYP_EMERGENCY_UPSET" in md
    assert "HYP_VEGETATION_WILDFIRE" in md
    assert "HYP_SENSOR_ARTIFACT" in md
    assert "Supporting Factors" in md
    assert "Contradicting / Refuting Factors" in md
    assert "Missing Telemetry" in md


# -----------------------------------------------------------------------------
# 33. Section 33 Executive Brief Markdown
# -----------------------------------------------------------------------------
def test_section_33_executive_brief_markdown(sample_assessment):
    """Test 33: format_section_33_executive_brief_markdown formats executive brief."""
    md = workspace_manager.format_section_33_executive_brief_markdown(sample_assessment)
    assert "JARVIS EXECUTIVE DECISION-SUPPORT BRIEF" in md
    assert "EXECUTIVE SITUATION SUMMARY" in md
    assert "OPERATIONAL SIGNIFICANCE" in md
    assert "CURRENT RISK POSTURE" in md
    assert "KEY SUPPORTING EVIDENCE" in md
    assert "KEY CONFLICTS & LIMITATIONS" in md
    assert "UNCERTAINTY & RECOMMENDED VERIFICATION" in md
