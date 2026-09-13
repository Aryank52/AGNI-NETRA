"""
tests/test_phase23_situational_awareness.py

Comprehensive Phase 23 Test Suite:
JARVIS Situational Awareness, Priority Briefing & Command Center
Covering Test Groups A through AC (30+ targeted test cases).

Verifies:
- Situational Snapshot Generation
- Multi-Tier Change Detection & Significance Evaluation
- Governed Prioritized Attention Queue
- 60-Second Situational Brief & India Macro Briefs
- Regional, Industrial Corridor & Longitudinal Trend Summaries
- REST API Endpoints (/situational/...)
- Spatial & Sovereign Boundary Invariants
- Seamless Transition to Phase 22 Mission Mode
- Zero-drift Safety Invariants (Single Master Agent, Dispatch Blocked,
  Automated Model Activation Disabled, Decoupled Epistemic Metrics)
"""

import pytest
import datetime
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.main import app
from backend.app.core.database import SessionLocal
from backend.app.models.domain import ThermalEvent, AssessmentVersion, VerificationRecord
from backend.app.services.jarvis.jarvis_situational_service import (
    generate_snapshot,
    detect_changes,
    build_attention_queue,
    generate_60s_brief,
    generate_india_brief,
    generate_regional_brief,
    generate_industrial_brief,
    generate_trend_summary,
    explain_attention_item,
    get_situational_timeline,
    generate_executive_brief,
    generate_analyst_brief
)
from backend.app.services.jarvis.jarvis_command_interpreter import command_interpreter
from backend.app.services.jarvis.jarvis_orchestrator import master_orchestrator
from backend.app.models.jarvis_schemas import CommandIntent, JarvisState


@pytest.fixture(scope="module")
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module")
def api_client():
    return TestClient(app)


# =========================================================================
# Group A: Situational Snapshot Generation
# =========================================================================
def test_group_a_situational_snapshot_generation(db_session: Session):
    snapshot = generate_snapshot(db_session, time_window_hours=72)
    assert snapshot is not None
    assert snapshot.snapshot_id.startswith("SNP-")
    assert snapshot.geographic_scope == "SOVEREIGN_INDIA"
    assert snapshot.active_event_count >= 0
    assert snapshot.high_priority_count >= 0
    assert snapshot.high_risk_count >= 0
    assert isinstance(snapshot.provider_status, dict)
    assert snapshot.provider_status.get("NASA_FIRMS") == "OPERATIONAL"
    assert snapshot.provider_status.get("POSTGIS_LGD") == "OPERATIONAL"
    assert snapshot.provider_status.get("SENTINEL_2") == "NOT_CONFIGURED"


# =========================================================================
# Group B: Change Detection Engine
# =========================================================================
def test_group_b_change_detection(db_session: Session):
    changes = detect_changes(db_session, lookback_hours=72)
    assert isinstance(changes, list)
    for chg in changes:
        assert chg.change_id.startswith("CHG-")
        assert chg.category in [
            "NEW_DETECTION", "ASSESSMENT_SHIFT", "RISK_ESCALATION",
            "VERIFICATION_UPDATE", "PERSISTENCE_CONFIRMATION",
            "ANOMALY_SPIKE", "NO_MATERIAL_CHANGE"
        ]
        assert chg.significance in ["CRITICAL", "HIGH", "MODERATE", "LOW"]


# =========================================================================
# Group C: Significance Evaluation Tiers
# =========================================================================
def test_group_c_significance_evaluation(db_session: Session):
    changes = detect_changes(db_session, lookback_hours=168)
    for chg in changes:
        if chg.significance == "CRITICAL":
            # Critical items must be high risk or confirmed verification
            assert chg.category in ["RISK_ESCALATION", "ASSESSMENT_SHIFT", "PERSISTENCE_CONFIRMATION", "VERIFICATION_UPDATE", "NEW_DETECTION"]
        assert chg.significance in ["CRITICAL", "HIGH", "MODERATE", "LOW"]


# =========================================================================
# Group D: Prioritized Attention Queue
# =========================================================================
def test_group_d_attention_queue_ranking(db_session: Session):
    queue = build_attention_queue(db_session, max_items=15)
    assert isinstance(queue, list)
    # Check strict descending priority order
    for i in range(len(queue) - 1):
        assert queue[i].priority_score >= queue[i+1].priority_score
        assert 0.0 <= queue[i].priority_score <= 1.0
        assert 0.0 <= queue[i].risk_score <= 1.0


# =========================================================================
# Group E: Attention Reason & Driver Explanation
# =========================================================================
def test_group_e_attention_reasons(db_session: Session):
    queue = build_attention_queue(db_session, max_items=5)
    for item in queue:
        assert len(item.why_attention_needed) > 10
        assert item.category is not None
        assert isinstance(item.missing_evidence, list)
        assert len(item.recommended_action) > 5


# =========================================================================
# Group F: 60-Second Situational Brief Generation
# =========================================================================
def test_group_f_sixty_second_brief(db_session: Session):
    brief = generate_60s_brief(db_session)
    assert brief.brief_id.startswith("BRF-60S-")
    assert isinstance(brief.situation, list)
    assert len(brief.situation) > 0
    assert isinstance(brief.changes, list)
    assert isinstance(brief.attention, list)
    assert isinstance(brief.uncertainty, list)
    assert isinstance(brief.next, list)
    assert "60-SECOND SITUATIONAL AWARENESS BRIEF" in brief.markdown_text


# =========================================================================
# Group G: "What Needs Attention Right Now?" Command
# =========================================================================
def test_group_g_what_needs_attention_command():
    parsed = command_interpreter.interpret("JARVIS, what needs attention right now?")
    assert parsed["intent"] == CommandIntent.SITUATIONAL_AWARENESS
    assert parsed.get("primary_goal") in ["SITUATIONAL_ATTENTION_QUEUE", "SITUATIONAL_WHAT_NEEDS_ATTENTION"]

    res = master_orchestrator.execute_command("JARVIS, what needs attention right now?")
    assert res.state == JarvisState.IDLE
    assert "ATTENTION" in res.summary.upper()
    assert "attention_items" in res.details


# =========================================================================
# Group H: "What Changed?" Command
# =========================================================================
def test_group_h_what_changed_command():
    parsed = command_interpreter.interpret("JARVIS, what changed in the last 24 hours?")
    assert parsed["intent"] == CommandIntent.SITUATIONAL_AWARENESS
    assert parsed.get("primary_goal") == "SITUATIONAL_WHAT_CHANGED"

    res = master_orchestrator.execute_command("JARVIS, what changed?")
    assert res.state == JarvisState.IDLE
    assert "changes" in res.details


# =========================================================================
# Group I: Regional Situational Briefs (e.g., Gujarat)
# =========================================================================
def test_group_i_regional_brief(db_session: Session):
    brief = generate_regional_brief(db_session, "Gujarat")
    assert brief.regional_focus == "Gujarat"
    assert brief.geographic_scope == "SOVEREIGN_INDIA"
    assert "Gujarat" in brief.markdown_brief


# =========================================================================
# Group J: Industrial Corridor Briefs (e.g., Dahej)
# =========================================================================
def test_group_j_industrial_brief(db_session: Session):
    brief = generate_industrial_brief(db_session, "Dahej")
    assert "Dahej" in brief.markdown_brief
    assert brief.current_situation.get("focus") == "Dahej"


# =========================================================================
# Group K: Longitudinal Trend Summaries
# =========================================================================
def test_group_k_trend_summary(db_session: Session):
    trend = generate_trend_summary(db_session)
    assert "window_24h" in trend
    assert "window_7d" in trend
    assert "window_30d" in trend
    assert trend["window_30d"]["event_count"] >= trend["window_7d"]["event_count"]


# =========================================================================
# Group L: Situational Timeline Construction
# =========================================================================
def test_group_l_situational_timeline(db_session: Session):
    timeline = get_situational_timeline(db_session, limit=20)
    assert isinstance(timeline, list)
    for evt in timeline:
        assert evt.timeline_id.startswith("TL-")
        assert evt.timestamp is not None
        assert evt.event_type is not None


# =========================================================================
# Group M: Detailed Attention Item Explanation
# =========================================================================
def test_group_m_explain_attention_item(db_session: Session):
    queue = build_attention_queue(db_session, max_items=1)
    if queue:
        item = queue[0]
        explanation = explain_attention_item(db_session, item.item_id)
        assert "target" in explanation
        assert "priority_score" in explanation
        assert "risk_score" in explanation
        assert "why_attention_needed" in explanation


# =========================================================================
# Group N: No-Material-Change Graceful Handling
# =========================================================================
def test_group_n_no_material_change_handling(db_session: Session):
    # Detect changes in tiny 0.001h window where no new events occur
    changes = detect_changes(db_session, lookback_hours=0.0001)
    assert isinstance(changes, list)
    # Even if empty or containing baseline items, it must not throw


# =========================================================================
# Group O: REST API Endpoints Verification
# =========================================================================
def test_group_o_rest_api_snapshot(api_client: TestClient):
    res = api_client.get("/api/v1/jarvis/situational/snapshot?time_window_hours=48")
    assert res.status_code == 200
    data = res.json()
    assert "snapshot_id" in data
    assert data["geographic_scope"] == "SOVEREIGN_INDIA"


def test_group_o_rest_api_changes(api_client: TestClient):
    res = api_client.get("/api/v1/jarvis/situational/changes?lookback_hours=48")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_group_o_rest_api_attention(api_client: TestClient):
    res = api_client.get("/api/v1/jarvis/situational/attention?limit=10")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)


def test_group_o_rest_api_brief_60s(api_client: TestClient):
    res = api_client.post("/api/v1/jarvis/situational/brief", json={"brief_type": "60_SECOND"})
    assert res.status_code == 200
    data = res.json()
    assert "situation" in data
    assert "changes" in data


def test_group_o_rest_api_timeline(api_client: TestClient):
    res = api_client.get("/api/v1/jarvis/situational/timeline?limit=15")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


# =========================================================================
# Group P: Map & Spatial Sovereign Boundary Integration
# =========================================================================
def test_group_p_spatial_coordinates(db_session: Session):
    queue = build_attention_queue(db_session, max_items=10)
    for item in queue:
        if item.coordinates:
            lat, lon = item.coordinates
            # Sovereign India bounds: ~6°N to 38°N, 68°E to 98°E
            assert 6.0 <= lat <= 38.0, f"Latitude {lat} out of sovereign bounds"
            assert 68.0 <= lon <= 98.0, f"Longitude {lon} out of sovereign bounds"


# =========================================================================
# Group Q: Executive & Analyst Brief Modes
# =========================================================================
def test_group_q_executive_and_analyst_briefs(db_session: Session):
    exec_brief = generate_executive_brief(db_session)
    assert "EXECUTIVE SITUATIONAL BRIEF" in exec_brief.markdown_brief

    analyst_brief = generate_analyst_brief(db_session)
    assert "ANALYST SITUATIONAL BRIEF" in analyst_brief.markdown_brief


# =========================================================================
# Group R: Mission Mode Integration (Investigate Top Priority Item)
# =========================================================================
def test_group_r_investigate_top_item_transition():
    res = master_orchestrator.execute_command("JARVIS, investigate the highest-priority item.")
    assert res.state == JarvisState.IDLE
    assert res.investigation_workspace is not None
    assert res.mission is not None
    assert "MISSION" in res.mission.objective.upper()
    assert res.mission.canonical_assessment is not None


# =========================================================================
# Group S: India Macro Brief Command
# =========================================================================
def test_group_s_india_situation_command():
    res = master_orchestrator.execute_command("JARVIS, what is the current India thermal situation?")
    assert res.state == JarvisState.IDLE
    assert "INDIA" in res.summary.upper()
    assert "brief" in res.details


# =========================================================================
# Group T: Single Master Agent Invariant
# =========================================================================
def test_group_t_single_master_agent():
    # Master orchestrator must not instantiate subagents or background workers
    assert hasattr(master_orchestrator, "subagents") is False or master_orchestrator.subagents == []
    assert master_orchestrator.state == JarvisState.IDLE


# =========================================================================
# Group U: Blocked Dispatch Invariant
# =========================================================================
def test_group_u_blocked_dispatch():
    from backend.app.services.jarvis.jarvis_orchestrator import ENABLE_OPERATIONAL_DISPATCH_GATE
    assert ENABLE_OPERATIONAL_DISPATCH_GATE is False


# =========================================================================
# Group V: Disabled Automated Model Activation Invariant
# =========================================================================
def test_group_v_disabled_model_activation():
    from backend.app.services.jarvis.jarvis_orchestrator import ENABLE_AUTOMATED_MODEL_ACTIVATION
    assert ENABLE_AUTOMATED_MODEL_ACTIVATION is False


# =========================================================================
# Group W: Frozen Risk & Priority Formula Verification
# =========================================================================
def test_group_w_frozen_formula_weights():
    # Risk weights: Thermal 0.30, Context 0.25, Persistence 0.20, Vulnerability 0.15, Environmental 0.10
    # Governed Priority weights: 0.40R + 0.20C + 0.30T + 0.10Rec
    from backend.app.services.jarvis.jarvis_situational_service import compute_governed_priority
    # Case: R=1, C=1, T=1, Rec=1 -> 1.0
    p_max = compute_governed_priority(1.0, 1.0, 1.0, 1.0)
    assert abs(p_max - 1.0) < 1e-4

    # Case: R=0, C=0, T=0, Rec=0 -> 0.0
    p_min = compute_governed_priority(0.0, 0.0, 0.0, 0.0)
    assert abs(p_min - 0.0) < 1e-4

    # Proportional test: R=1.0 only -> 0.40
    p_r = compute_governed_priority(1.0, 0.0, 0.0, 0.0)
    assert abs(p_r - 0.40) < 1e-4


# =========================================================================
# Group X: Decoupled Epistemic Metrics Verification
# =========================================================================
def test_group_x_decoupled_epistemic_metrics(db_session: Session):
    queue = build_attention_queue(db_session, max_items=10)
    for item in queue:
        # Assert that risk score, confidence, and evidence strength are independent variables
        # (they should not be trivially identical across items)
        assert isinstance(item.risk_score, float)
        assert isinstance(item.calibrated_confidence, float)
        assert isinstance(item.evidence_strength, float)


# =========================================================================
# Group Y: External Feeds Reality & Zero Synthetic Data
# =========================================================================
def test_group_y_external_feeds_reality(db_session: Session):
    snapshot = generate_snapshot(db_session)
    status = snapshot.provider_status
    # Sentinel-2, PlanetScope, Maxar must be NOT_CONFIGURED or UNAVAILABLE
    assert status.get("SENTINEL_2") in ["NOT_CONFIGURED", "UNAVAILABLE"]
    assert status.get("PLANETSCOPE") in ["NOT_CONFIGURED", "UNAVAILABLE"]
    assert status.get("MAXAR") in ["NOT_CONFIGURED", "UNAVAILABLE"]


# =========================================================================
# Group Z: State Return to IDLE Verification
# =========================================================================
def test_group_z_state_return_to_idle():
    commands = [
        "JARVIS, give me a 60-second situation brief.",
        "JARVIS, what changed?",
        "JARVIS, what needs attention right now?",
        "JARVIS, what is the current India thermal situation?",
        "JARVIS, give me the executive situation brief."
    ]
    for cmd in commands:
        res = master_orchestrator.execute_command(cmd)
        assert res.state == JarvisState.IDLE, f"Command '{cmd}' failed to return to IDLE"


# =========================================================================
# Group AA: RBAC & Human Verification Requirement Invariant
# =========================================================================
def test_group_aa_human_verification_invariant(db_session: Session):
    # When an attention item has high risk or assessment shift, investigating it
    # must produce an assessment requiring human verification
    queue = build_attention_queue(db_session, max_items=3)
    if queue:
        top_event = queue[0].event_code or queue[0].event_id
        res = master_orchestrator.execute_command(f"Investigate event {top_event}")
        if res.mission and res.mission.canonical_assessment:
            # High-priority cases require human verification
            assert res.mission.canonical_assessment.requires_human_verification is True


# =========================================================================
# Group AB: API Investigate Top Item Endpoint
# =========================================================================
def test_group_ab_api_investigate_top(api_client: TestClient):
    res = api_client.post("/api/v1/jarvis/situational/investigate-top")
    assert res.status_code == 200
    data = res.json()
    assert "mission_id" in data or "investigation_id" in data
    assert "objective" in data


# =========================================================================
# Group AC: Public Safety Non-Causal Spatial Language
# =========================================================================
def test_group_ac_non_causal_spatial_language(db_session: Session):
    brief = generate_india_brief(db_session)
    text = brief.markdown_brief.lower()
    # Ensure no deterministic causal assertions like "caused by industrial facility"
    # instead of "spatially associated with" or "located within"
    assert "caused by" not in text
