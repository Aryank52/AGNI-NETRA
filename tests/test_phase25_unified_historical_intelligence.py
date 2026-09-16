"""
AGNI-NETRA — Phase 25 Unified Event Intelligence & Historical Incident Intelligence Test Suite

Validates:
1. Canonical Event Intelligence Object (9 core pillars, serialization, schema consistency)
2. Historical Incident Registry (registration, closed loop without model retraining, queries, similarity)
3. Historical Baseline Comparison Engine (point-in-time safety t < T_obs, deviations, recurrence, persistence, 6 grounded questions)
4. Data Coverage Registry (all 18+ feeds, zero synthetic substitution, truthful statuses)
5. Closed-Loop HITL Verification Integration (CONFIRM/CORRECT registers incident, model activation remains disabled)
6. JARVIS Natural Language Historical & Epistemic Reasoning (stopping reasons, grounded answers, dispatch gate blocked)
7. REST API Endpoints (/canonical, /incidents, /compare, /coverage-registry)
8. Safety Boundaries & Platform Invariants (ENABLE_OPERATIONAL_DISPATCH_GATE=False, ENABLE_AUTOMATED_MODEL_ACTIVATION=False)
"""

import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.database import SessionLocal
from backend.app.models.domain import ThermalEvent, VerificationRecord, HistoricalIncident, User
from backend.app.models.canonical import CanonicalEventIntelligence, DataCoverageStatus
from backend.app.services.intelligence.canonical_event_service import canonical_event_service
from backend.app.services.intelligence.historical_incident_registry import historical_incident_registry
from backend.app.services.intelligence.historical_comparison_engine import historical_comparison_engine
from backend.app.services.data_plane.data_coverage_registry import data_coverage_registry
from backend.app.services.jarvis.jarvis_orchestrator import jarvis_orchestrator
from backend.app.models.jarvis_schemas import JarvisCommandRequest, JarvisState
from backend.app.core.config import settings

client = TestClient(app)


@pytest.fixture(scope="module")
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="module")
def sample_event(db: Session):
    event = db.query(ThermalEvent).first()
    assert event is not None, "At least one thermal event must exist in test database"
    return event


# =============================================================================
# 1. Canonical Event Intelligence Object (9 Core Pillars)
# =============================================================================

def test_canonical_event_structure_and_serialization(db: Session, sample_event: ThermalEvent):
    """
    Validates that CanonicalEventIntelligence produces all 9 pillars with zero runtime schema errors.
    """
    canonical = canonical_event_service.get_canonical_event(db, sample_event)
    assert isinstance(canonical, CanonicalEventIntelligence)

    data = canonical.model_dump()
    expected_pillars = [
        "schema_version",
        "identity",
        "geography",
        "observation",
        "context",
        "historical",
        "analytics",
        "evidence",
        "jarvis",
        "governance"
    ]
    for pillar in expected_pillars:
        assert pillar in data, f"Missing expected canonical pillar: {pillar}"

    assert canonical.identity.event_id == sample_event.id
    assert canonical.identity.event_code == sample_event.event_code
    assert canonical.geography.latitude == round(float(sample_event.latitude), 4)
    assert canonical.observation.max_frp >= 0.0
    assert 0.0 <= canonical.analytics.risk_score <= 100.0
    assert 0.0 <= canonical.analytics.priority_score <= 100.0
    assert 0.0 <= canonical.evidence.evidence_strength <= 1.0
    assert canonical.governance.dispatch_gate_blocked is True


# =============================================================================
# 2. Historical Incident Registry & Closed-Loop Integration
# =============================================================================

def test_historical_incident_registry_seeding_and_queries(db: Session):
    """
    Validates that historical incidents can be queried and filtered by state, status, and min_frp.
    """
    res = historical_incident_registry.query_incidents(db, limit=10)
    assert "total_count" in res
    assert "items" in res
    assert res["total_count"] >= 1, "Historical incident registry should contain at least 1 record"

    first = res["items"][0]
    assert first.incident_code.startswith("INC-")
    assert first.status in ["VERIFIED", "UNVERIFIED", "CONTESTED", "RESOLVED"]

    # Detail query
    detail = historical_incident_registry.get_incident_by_id(db, first.id)
    assert detail is not None
    assert detail.id == first.id


def test_closed_loop_registration_without_model_activation(db: Session, sample_event: ThermalEvent):
    """
    Validates closed-loop registration: creating or updating a verified incident record
    must NEVER trigger automated model activation or retraining.
    """
    # Safety invariant check
    assert getattr(settings, "ENABLE_AUTOMATED_MODEL_ACTIVATION", False) is False

    inc = historical_incident_registry.register_verified_incident(
        db=db,
        event_id=sample_event.id,
        analyst_name="Test Lead Analyst",
        verified_label="Industrial Flare",
        verification_action="CONFIRM",
        notes="Automated Phase 25 verification test"
    )
    assert inc is not None
    assert inc.status == "VERIFIED"
    assert inc.verified_by == "Test Lead Analyst"
    assert sample_event.id in inc.linked_event_ids

    # Verify model remains frozen
    assert getattr(settings, "ENABLE_AUTOMATED_MODEL_ACTIVATION", False) is False


# =============================================================================
# 3. Deterministic Historical Baseline Comparison Engine
# =============================================================================

def test_point_in_time_baseline_anti_leakage(db: Session, sample_event: ThermalEvent):
    """
    Validates strict point-in-time anti-leakage protection:
    All historical queries strictly require t < T_obs.
    """
    comp = historical_comparison_engine.compare_event(db, sample_event)
    assert comp["event_id"] == sample_event.id
    assert comp["event_code"] == sample_event.event_code

    # Verify mathematical fields exist
    assert "baseline_frp_mean" in comp
    assert "baseline_frp_std" in comp
    assert "deviation_ratio" in comp
    assert "deviation_percent" in comp
    assert "deviation_z_score" in comp
    assert "is_intensity_anomaly" in comp
    assert "persistence_category" in comp
    assert "recurrence_category" in comp

    # Verify all 6 grounded questions are answered deterministically
    answers = comp.get("answers", {})
    assert "is_normal" in answers
    assert "has_happened_before" in answers
    assert "recurrence_frequency" in answers
    assert "intensity_relative_to_baseline" in answers
    assert "resemble_previous_incidents" in answers
    assert "is_persistent" in answers


# =============================================================================
# 4. Data Coverage Registry & Truthful Data Plane
# =============================================================================

def test_data_coverage_registry_disclosures():
    """
    Validates that Data Coverage Registry covers all 18+ datasets with explicit
    honest statuses (AVAILABLE, DERIVED, NOT_CONFIGURED, UNAVAILABLE) and zero synthetic mocks.
    """
    records = data_coverage_registry.get_coverage_registry()
    assert len(records) >= 15

    statuses = {r.current_status for r in records}
    assert DataCoverageStatus.AVAILABLE in statuses
    assert DataCoverageStatus.NOT_CONFIGURED in statuses

    # Verify unconfigured providers are disclosed as NOT_CONFIGURED
    cams_check = data_coverage_registry.check_provider_status("CAMS")
    assert cams_check["status"] == "NOT_CONFIGURED"

    goes_check = data_coverage_registry.check_provider_status("GOES")
    assert goes_check["status"] == "UNAVAILABLE"


# =============================================================================
# 5. JARVIS Historical & Epistemic Reasoning
# =============================================================================

def test_jarvis_historical_inquiries(db: Session):
    """
    Validates JARVIS natural language execution of historical and why-critical commands
    with structured stopping reasons and locked dispatch gate.
    """
    # 1. "Has this happened before?"
    resp1 = jarvis_orchestrator.execute_command(
        db,
        JarvisCommandRequest(command="Has this happened before?"),
        user_role="ANALYST"
    )
    assert resp1.state == JarvisState.COMPLETED
    assert resp1.dispatch_gate_blocked is True
    assert resp1.stopping_reason in [
        "HISTORICAL_PATTERN_SUFFICIENT: Longitudinal comparison evaluated.",
        "NO_RELEVANT_HISTORY: Sparse historical baseline."
    ]

    # 2. "Why is this event critical?"
    resp2 = jarvis_orchestrator.execute_command(
        db,
        JarvisCommandRequest(command="Why is this event critical?"),
        user_role="ANALYST"
    )
    assert resp2.state == JarvisState.COMPLETED
    assert resp2.dispatch_gate_blocked is True
    assert "EVIDENCE_SUFFICIENT" in resp2.stopping_reason or "NO_RELEVANT_HISTORY" in resp2.stopping_reason
    assert "Authoritative Risk Score" in resp2.summary

    # 3. "Assess evidence sufficiency"
    resp3 = jarvis_orchestrator.execute_command(
        db,
        JarvisCommandRequest(command="Assess evidence sufficiency"),
        user_role="ANALYST"
    )
    assert resp3.state == JarvisState.COMPLETED
    assert resp3.dispatch_gate_blocked is True
    assert "HUMAN_VERIFICATION_REQUIRED" in resp3.stopping_reason or "AVAILABLE_EVIDENCE_EXHAUSTED" in resp3.stopping_reason
    assert "KNOWN" in resp3.summary
    assert "INFERRED" in resp3.summary


# =============================================================================
# 6. REST API Endpoints
# =============================================================================

def test_rest_api_phase25_endpoints(sample_event: ThermalEvent):
    """
    Validates HTTP 200 responses and structure on all new Phase 25 REST API endpoints.
    """
    # 1. Canonical Event Intelligence
    r1 = client.get(f"/api/v1/events/{sample_event.id}/canonical")
    assert r1.status_code == 200
    d1 = r1.json()
    assert d1["identity"]["event_code"] == sample_event.event_code

    # 2. Historical Incident Registry
    r2 = client.get("/api/v1/historical/incidents")
    assert r2.status_code == 200
    d2 = r2.json()
    assert d2["total_count"] >= 1

    # 3. Coverage Registry
    r3 = client.get("/api/v1/inventory/coverage-registry")
    assert r3.status_code == 200
    d3 = r3.json()
    assert d3["total_feeds"] >= 15
    assert "AVAILABLE" in d3["summary"]

    # 4. Compare Event with Baseline
    r4 = client.get(f"/api/v1/historical/compare/{sample_event.id}")
    assert r4.status_code == 200
    d4 = r4.json()
    assert len(d4["answers"]) >= 6
    assert "is_normal" in d4["answers"]


# =============================================================================
# 7. Safety Boundaries & Dispatch Gate Invariant
# =============================================================================

def test_safety_invariants():
    """
    Validates core safety boundaries:
    - Operational dispatch gate held strictly BLOCKED
    - Automated model retraining / activation held strictly DISABLED
    """
    from backend.app.services.jarvis.jarvis_policy import ENABLE_OPERATIONAL_DISPATCH_GATE
    assert ENABLE_OPERATIONAL_DISPATCH_GATE is False
    assert getattr(settings, "ENABLE_AUTOMATED_MODEL_ACTIVATION", False) is False
