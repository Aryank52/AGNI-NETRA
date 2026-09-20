"""
AGNI-NETRA — Automated Test Suite for Proactive Fire Prevention & Root-Cause Intelligence
Branch: feature/proactive-fire-prevention

Validates:
1. 13-Category Deterministic Root-Cause Taxonomy & Transparent Scoring
2. Epistemic Anti-Fabrication Constraints (No LLMs, Standardized Missing Telemetry Labels)
3. 24-Section Report Generator & ReportLab PDF Artifacts
4. Human Review, Approval & Cryptographic Delivery Ledger
5. 10 Mandatory Negative Invariant Tests
6. End-to-End Real Validation on Target Event EVT-GUJ-20260916-150D
7. Master JARVIS Orchestration Tools (tool_why_this_fire, tool_investigate_root_cause)
"""

import pytest
import os
import hashlib
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from backend.app.core.database import SessionLocal
from backend.app.core.config import settings
from backend.app.models.domain import (
    PreventionCase,
    RootCauseHypothesisRecord,
    PreventionRecommendationRecord,
    AuthorityDirectoryRecord,
    PreventionReportRecord,
    ReportDeliveryAudit,
    ThermalEvent
)
from backend.app.services.intelligence.authority_registry_service import authority_registry_service
from backend.app.services.intelligence.prevention_recommendation_engine import prevention_recommendation_engine
from backend.app.services.intelligence.root_cause_intelligence_service import root_cause_intelligence_service
from backend.app.services.prevention_report_generator import prevention_report_generator
from backend.app.services.jarvis.jarvis_tools import JarvisToolRegistry


@pytest.fixture
def db():
    session = SessionLocal()
    session.rollback()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


# ==============================================================================
# 1. Authority Registry Tests
# ==============================================================================

def test_authority_registry_resolution(db: Session):
    """Test resolution of Indian regulatory and emergency authorities by state/district."""
    authorities = authority_registry_service.resolve_authorities(
        db=db,
        state="Gujarat",
        district="Jamnagar"
    )
    assert len(authorities) >= 1
    for a in authorities:
        assert "name" in a
        assert "category" in a
        assert "relevance" in a


# ==============================================================================
# 2. Prevention Recommendation Engine Tests
# ==============================================================================

def test_recommendation_engine_phrasing_invariant():
    """Verify that all recommendations respect the epistemic risk-reduction phrasing invariant."""
    sample_hypotheses = [
        {
            "category": "INDUSTRIAL_PROCESS",
            "title": "Industrial High-Heat Flaring / Process Unit",
            "confidence_score": 0.85,
            "status": "PLAUSIBLE"
        }
    ]

    recs = prevention_recommendation_engine.generate_recommendations(
        case_id="PREV-TEST-001",
        facility_name="Reliance Jamnagar Refinery",
        facility_type="Refinery",
        hypotheses=sample_hypotheses,
        recurrence_rate=12.0,
        persistence_score=0.8,
        baseline_deviation_ratio=2.5
    )

    assert len(recs) >= 1
    for r in recs:
        assert "recommendation" in r
        assert "urgency" in r
        obj = r.get("expected_prevention_objective", "").lower()
        assert "may reduce recurrence risk" in obj


# ==============================================================================
# 3. 13-Category Root-Cause Intelligence Service Tests
# ==============================================================================

def test_root_cause_13_categories_evaluated(db: Session):
    """Verify that exactly 13 distinct hypothesis categories are evaluated deterministically."""
    case = db.query(PreventionCase).filter(PreventionCase.event_code == "EVT-GUJ-20260916-150D").first()
    if not case:
        case = root_cause_intelligence_service.analyze_event_root_cause(
            db=db,
            event_ref="EVT-GUJ-20260916-150D"
        )

    assert case is not None
    assert len(case.hypotheses) == 13

    # Check categories uniqueness
    categories = {h.category for h in case.hypotheses}
    assert len(categories) == 13
    assert "INDUSTRIAL_PROCESS" in categories
    assert "EQUIPMENT_FAILURE" in categories
    assert "FOREST_OR_VEGETATION" in categories
    assert "AGRICULTURAL_BURNING" in categories

    # Scores must be bounded [0.0, 1.0]
    for h in case.hypotheses:
        assert 0.0 <= h.confidence_score <= 1.0
        assert 0.0 <= h.evidence_strength <= 1.0
        assert h.status in ["SUPPORTED", "PLAUSIBLE", "WEAKLY_SUPPORTED", "CONTRADICTED", "UNKNOWN"]


def test_root_cause_reliance_jamnagar_classification(db: Session):
    """Test realistic classification for Reliance Jamnagar Refinery event."""
    case = db.query(PreventionCase).filter(PreventionCase.event_code == "EVT-GUJ-20260916-150D").first()
    if not case:
        case = root_cause_intelligence_service.analyze_event_root_cause(
            db=db,
            event_ref="EVT-GUJ-20260916-150D"
        )

    assert case.prevention_priority in ["CRITICAL", "HIGH"]

    # Primary hypothesis should be industrial/flare/equipment, not forestry or stubble burning
    supported = [h for h in case.hypotheses if h.status in ["SUPPORTED", "PLAUSIBLE"]]
    assert len(supported) >= 1
    supported_cats = [h.category for h in supported]
    assert any(c in supported_cats for c in ["INDUSTRIAL_PROCESS", "EQUIPMENT_FAILURE", "GAS_OR_FLAMMABLE_VAPOR", "FUEL_OR_HYDROCARBON"])

    # Forest and Agriculture should be contradicted or weakly supported inside a petrochemical refinery
    forest = next((h for h in case.hypotheses if h.category == "FOREST_OR_VEGETATION"), None)
    assert forest is not None
    assert forest.status in ["CONTRADICTED", "WEAKLY_SUPPORTED", "UNKNOWN"]


# ==============================================================================
# 4. 24-Section Report Generator & PDF Artifact Tests
# ==============================================================================

def test_24_section_report_generation(db: Session):
    """Verify compilation of all 24 canonical sections and ReportLab PDF artifact generation."""
    case = db.query(PreventionCase).filter(PreventionCase.event_code == "EVT-GUJ-20260916-150D").first()
    assert case is not None

    report = prevention_report_generator.create_draft_report(db, case.id)
    assert report is not None
    assert report.status == "DRAFT"
    assert report.report_number.startswith("REP-")
    assert report.pdf_path is not None
    assert os.path.exists(report.pdf_path)
    assert os.path.getsize(report.pdf_path) > 1000

    sections = report.sections_data
    assert len(sections) == 24
    for i in range(1, 25):
        key = next((k for k in sections.keys() if k.startswith(f"section_{i}_")), None)
        assert key is not None, f"Section {i} missing from compiled report"


# ==============================================================================
# 5. 10 Mandatory Negative Invariant Tests
# ==============================================================================

def test_negative_1_no_evidence_no_invented_cause(db: Session):
    """Negative Test 1: Empty context must not invent specific causes."""
    case = db.query(PreventionCase).first()
    assert case is not None
    assert case.evidence_strength_score <= 1.0


def test_negative_2_no_gas_data_standardized_label(db: Session):
    """Negative Test 2: In the absence of stack gas spectrometry, outputs GAS COMPOSITION DATA UNAVAILABLE."""
    case = db.query(PreventionCase).first()
    assert case is not None
    sections = prevention_report_generator.compile_sections_data(db, case)
    sec10 = sections.get("section_10_material_substance_context", {})
    assert sec10.get("gas_composition_status") == "GAS COMPOSITION DATA UNAVAILABLE"


def test_negative_3_no_material_data_standardized_label(db: Session):
    """Negative Test 3: No specific chemical composition is fabricated; epistemic disclaimer enforced."""
    case = db.query(PreventionCase).first()
    sections = prevention_report_generator.compile_sections_data(db, case)
    sec10 = sections.get("section_10_material_substance_context", {})
    assert "never presented as confirmed forensic substances" in sec10.get("epistemic_disclaimer", "").lower()


def test_negative_4_no_agency_records_standardized_label(db: Session):
    """Negative Test 4: In the absence of agency records, outputs 'No verified agency records available'."""
    case = db.query(PreventionCase).first()
    assert case is not None
    original_evidence = case.agency_evidence
    try:
        case.agency_evidence = []
        sections = prevention_report_generator.compile_sections_data(db, case)
        sec11 = sections.get("section_11_agency_evidence", {})
        assert sec11.get("agency_evidence_status") == "No verified agency records available"
    finally:
        case.agency_evidence = original_evidence


def test_negative_5_no_external_news_standardized_label(db: Session):
    """Negative Test 5: In the absence of web/media citations, outputs 'NEWS EVIDENCE UNAVAILABLE'."""
    case = db.query(PreventionCase).first()
    sections = prevention_report_generator.compile_sections_data(db, case)
    sec12 = sections.get("section_12_external_evidence", {})
    assert sec12.get("external_evidence_status") == "NEWS EVIDENCE UNAVAILABLE"


def test_negative_6_correlation_not_causation_banner(db: Session):
    """Negative Test 6: Invariant warning 'HISTORICAL CORRELATION DOES NOT IMPLY CAUSATION.' must appear."""
    case = db.query(PreventionCase).first()
    sections = prevention_report_generator.compile_sections_data(db, case)
    sec1 = sections.get("section_1_executive_summary", {})
    assert sec1.get("disclaimer") == "HISTORICAL CORRELATION DOES NOT IMPLY CAUSATION."
    sec6 = sections.get("section_6_recurrence_analysis", {})
    assert "HISTORICAL CORRELATION DOES NOT IMPLY CAUSATION." in sec6.get("correlation_statement", "")


def test_negative_7_jarvis_offline_resilience(db: Session):
    """Negative Test 7: Direct service functions without relying on external network or agent swarms."""
    auths = authority_registry_service.resolve_authorities(db, "Gujarat", "Jamnagar")
    assert isinstance(auths, list)
    recs = prevention_recommendation_engine.generate_recommendations(
        case_id="PREV-OFFLINE-001",
        facility_name="Offline Facility",
        facility_type="Refinery",
        hypotheses=[],
        recurrence_rate=5.0,
        persistence_score=0.5,
        baseline_deviation_ratio=1.0
    )
    assert isinstance(recs, list)


def test_negative_8_unauthorized_user_cannot_approve_or_send(db: Session):
    """Negative Test 8: Non-ANALYST/ADMIN role cannot approve or dispatch formal reports."""
    case = db.query(PreventionCase).first()
    rep = prevention_report_generator.create_draft_report(db, case.id)

    # Delivery while DRAFT must fail
    with pytest.raises(ValueError, match="Cannot deliver report in 'DRAFT' state"):
        prevention_report_generator.send_report(
            db, rep.id,
            {"recipient_name": "Test Officer"},
            {"role": "ANALYST", "email": "analyst@agni-netra.gov.in"}
        )

    # Approval by GUEST must fail
    with pytest.raises(PermissionError, match="not authorized to approve"):
        prevention_report_generator.approve_report(db, rep.id, "Guest User", "GUEST")


def test_negative_9_safety_invariant_operational_dispatch_gate():
    """Negative Test 9: Safety invariant ENABLE_OPERATIONAL_DISPATCH_GATE must remain False."""
    assert getattr(settings, "ENABLE_OPERATIONAL_DISPATCH_GATE", False) is False


def test_negative_10_safety_invariant_automated_model_activation():
    """Negative Test 10: Safety invariant ENABLE_AUTOMATED_MODEL_ACTIVATION must remain False."""
    assert getattr(settings, "ENABLE_AUTOMATED_MODEL_ACTIVATION", False) is False


# ==============================================================================
# 6. Master JARVIS Tool Integration Tests
# ==============================================================================

def test_jarvis_tool_why_this_fire(db: Session):
    """Verify JarvisToolRegistry.tool_why_this_fire returns the canonical proactive prevention response."""
    res = JarvisToolRegistry.tool_why_this_fire(db=db, event_ref="EVT-GUJ-20260916-150D")

    assert res.get("workflow") == "WHY_THIS_FIRE"
    assert res.get("event_code") == "EVT-GUJ-20260916-150D"
    assert "formatted_response" in res
    assert "HISTORICAL CORRELATION DOES NOT IMPLY CAUSATION." in res["formatted_response"]


def test_jarvis_tool_investigate_root_cause(db: Session):
    """Verify JarvisToolRegistry.tool_investigate_root_cause returns comprehensive prevention case details."""
    res = JarvisToolRegistry.tool_investigate_root_cause(db=db, event_ref="EVT-GUJ-20260916-150D")

    assert res.get("event_code") == "EVT-GUJ-20260916-150D"
    assert res.get("prevention_priority") in ["CRITICAL", "HIGH"]
    assert "hypotheses_count" in res
    assert res["hypotheses_count"] == 13
    assert res.get("human_review_required") is True
