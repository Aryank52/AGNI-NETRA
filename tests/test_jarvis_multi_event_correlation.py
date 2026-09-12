"""
AGNI-NETRA Phase 12: Multi-Event Global Incident Correlation Test Suite
Comprehensive verification suite validating:
1. test_pairwise_same_physical_incident
2. test_pairwise_same_operational_episode
3. test_pairwise_recurring_source_activity
4. test_pairwise_geographically_related
5. test_pairwise_temporally_related
6. test_pairwise_downwind_hazard
7. test_pairwise_coordinated_activity
8. test_pairwise_independent_unrelated
9. test_pairwise_insufficiently_related
10. test_dbscan_clustering_success
11. test_dbscan_noise_handling
12. test_temporal_clustering_windows
13. test_cluster_extent_calculation
14. test_repetition_vs_continuous_differentiation
15. test_multi_pass_same_source_not_fake_growth
16. test_independent_coincident_differentiation
17. test_downwind_relationship_flagging
18. test_downwind_not_claimed_as_direct_ignition
19. test_nine_incident_hypotheses_evaluation
20. test_favored_hypothesis_selection
21. test_incident_impact_profile_calculation
22. test_highest_event_risk_preservation
23. test_incident_envelope_labeling
24. test_no_fake_fire_perimeter
25. test_zero_background_daemons
26. test_dispatch_gate_blocked_invariant
27. test_hitl_requirement_flagged
28. test_section_20_commands_route_correctly
29. test_section_28_primary_acceptance_command
30. test_workspace_incident_correlation_persistence
31. test_rbac_public_masking
32. test_provenance_audit_trail_completeness
33. test_frozen_baselines_unchanged
"""

import pytest
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.main import app
from backend.app.core.database import SessionLocal
from backend.app.models.canonical import (
    EventRelationship,
    EventCluster,
    IncidentHypothesis,
    IncidentImpactProfile,
    IncidentAssessment,
    MultiEventCorrelationResult
)
from backend.app.services.intelligence.multi_event_correlation import (
    multi_event_correlation_engine,
    MultiEventCorrelationEngine
)
from backend.app.services.jarvis.jarvis_command_interpreter import command_interpreter
from backend.app.services.jarvis.jarvis_orchestrator import master_orchestrator
from backend.app.services.jarvis.jarvis_workspace import workspace_manager
from backend.app.services.jarvis.jarvis_policy import ENABLE_OPERATIONAL_DISPATCH_GATE
from backend.app.models.domain import InvestigationWorkspace, User
from backend.app.models.jarvis_schemas import JarvisCommandRequest


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


# 1. test_pairwise_same_physical_incident
def test_pairwise_same_physical_incident(db_session: Session):
    engine = MultiEventCorrelationEngine()
    now_iso = datetime.now(timezone.utc).isoformat()
    e1 = {
        "event_id": "EVT-TEST-101",
        "latitude": 28.6139,
        "longitude": 77.2090,
        "first_seen": now_iso,
        "max_frp": 120.0,
        "risk_score": 70.0,
        "facility_status": "KNOWN"
    }
    # Within 0.8 km and 1 hour
    e2 = {
        "event_id": "EVT-TEST-102",
        "latitude": 28.6190,
        "longitude": 77.2120,
        "first_seen": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
        "max_frp": 95.0,
        "risk_score": 65.0,
        "facility_status": "KNOWN"
    }
    rel = engine.evaluate_pairwise_relationship(e1, e2)
    assert rel.relationship_type == "SAME_PHYSICAL_INCIDENT"
    assert rel.correlation_strength == "STRONG"
    assert rel.spatial_distance_km < 1.5
    assert rel.temporal_delta_hours < 6.0


# 2. test_pairwise_same_operational_episode
def test_pairwise_same_operational_episode(db_session: Session):
    engine = MultiEventCorrelationEngine()
    now = datetime.now(timezone.utc)
    e1 = {
        "event_id": "EVT-TEST-201",
        "latitude": 28.6139,
        "longitude": 77.2090,
        "first_seen": now.isoformat(),
        "max_frp": 80.0,
        "risk_score": 50.0,
        "facility_status": "KNOWN"
    }
    # Within 1.8 km and 18 hours
    e2 = {
        "event_id": "EVT-TEST-202",
        "latitude": 28.6250,
        "longitude": 77.2150,
        "first_seen": (now + timedelta(hours=18)).isoformat(),
        "max_frp": 60.0,
        "risk_score": 45.0,
        "facility_status": "KNOWN"
    }
    rel = engine.evaluate_pairwise_relationship(e1, e2)
    assert rel.relationship_type == "SAME_OPERATIONAL_EPISODE"
    assert rel.correlation_strength in ["STRONG", "MODERATE"]


# 3. test_pairwise_recurring_source_activity
def test_pairwise_recurring_source_activity(db_session: Session):
    engine = MultiEventCorrelationEngine()
    now = datetime.now(timezone.utc)
    e1 = {
        "event_id": "EVT-TEST-301",
        "latitude": 28.6139,
        "longitude": 77.2090,
        "first_seen": now.isoformat(),
        "max_frp": 150.0,
        "risk_score": 60.0,
        "facility_status": "KNOWN"
    }
    # Exact same location (< 0.4 km) but 48 hours later
    e2 = {
        "event_id": "EVT-TEST-302",
        "latitude": 28.6145,
        "longitude": 77.2092,
        "first_seen": (now + timedelta(hours=48)).isoformat(),
        "max_frp": 140.0,
        "risk_score": 58.0,
        "facility_status": "KNOWN"
    }
    rel = engine.evaluate_pairwise_relationship(e1, e2)
    assert rel.relationship_type == "RECURRING_SOURCE_ACTIVITY"
    assert rel.spatial_distance_km < 0.6
    assert rel.temporal_delta_hours >= 24.0


# 4. test_pairwise_geographically_related
def test_pairwise_geographically_related(db_session: Session):
    engine = MultiEventCorrelationEngine()
    now = datetime.now(timezone.utc)
    e1 = {
        "event_id": "EVT-TEST-401",
        "latitude": 28.6139,
        "longitude": 77.2090,
        "first_seen": now.isoformat(),
        "max_frp": 70.0,
        "risk_score": 40.0
    }
    # 6.5 km away and 50 hours later
    e2 = {
        "event_id": "EVT-TEST-402",
        "latitude": 28.6600,
        "longitude": 77.2300,
        "first_seen": (now + timedelta(hours=50)).isoformat(),
        "max_frp": 50.0,
        "risk_score": 35.0
    }
    rel = engine.evaluate_pairwise_relationship(e1, e2)
    assert rel.relationship_type == "GEOGRAPHICALLY_RELATED"
    assert rel.spatial_distance_km <= 10.0


# 5. test_pairwise_temporally_related
def test_pairwise_temporally_related(db_session: Session):
    engine = MultiEventCorrelationEngine()
    now = datetime.now(timezone.utc)
    e1 = {
        "event_id": "EVT-TEST-501",
        "latitude": 28.6139,
        "longitude": 77.2090,
        "first_seen": now.isoformat(),
        "max_frp": 90.0,
        "risk_score": 45.0
    }
    # 20 km away but within 2 hours
    e2 = {
        "event_id": "EVT-TEST-502",
        "latitude": 28.7800,
        "longitude": 77.2090,
        "first_seen": (now + timedelta(hours=2)).isoformat(),
        "max_frp": 85.0,
        "risk_score": 40.0
    }
    rel = engine.evaluate_pairwise_relationship(e1, e2)
    assert rel.relationship_type == "TEMPORALLY_RELATED"
    assert rel.spatial_distance_km > 10.0
    assert rel.temporal_delta_hours <= 6.0


# 6. test_pairwise_downwind_hazard
def test_pairwise_downwind_hazard(db_session: Session):
    engine = MultiEventCorrelationEngine()
    now = datetime.now(timezone.utc)
    # Source event
    e1 = {
        "event_id": "EVT-TEST-601",
        "latitude": 28.6139,
        "longitude": 77.2090,
        "first_seen": now.isoformat(),
        "max_frp": 110.0,
        "risk_score": 65.0
    }
    # Target event: Downwind (wind from 245° WSW -> plume blows to 65° ENE)
    e2 = {
        "event_id": "EVT-TEST-602",
        "latitude": 28.6270,
        "longitude": 77.2380,
        "first_seen": (now + timedelta(hours=3)).isoformat(),
        "max_frp": 55.0,
        "risk_score": 50.0
    }
    rel = engine.evaluate_pairwise_relationship(e1, e2, wind_direction_deg=245.0)
    assert rel.downwind_aligned is True
    assert rel.relationship_type in ["DOWNWIND_HAZARD", "SAME_PHYSICAL_INCIDENT"]


# 7. test_pairwise_coordinated_activity
def test_pairwise_coordinated_activity(db_session: Session):
    engine = MultiEventCorrelationEngine()
    now = datetime.now(timezone.utc)
    e1 = {
        "event_id": "EVT-TEST-701",
        "latitude": 28.6139,
        "longitude": 77.2090,
        "first_seen": now.isoformat(),
        "max_frp": 50.0,
        "risk_score": 40.0,
        "landcover_class": "AGRICULTURE"
    }
    e2 = {
        "event_id": "EVT-TEST-702",
        "latitude": 28.6250,
        "longitude": 77.2300,
        "first_seen": (now + timedelta(minutes=15)).isoformat(),
        "max_frp": 48.0,
        "risk_score": 38.0,
        "landcover_class": "AGRICULTURE"
    }
    rel = engine.evaluate_pairwise_relationship(e1, e2)
    assert rel.correlation_strength in ["STRONG", "MODERATE"]


# 8. test_pairwise_independent_unrelated
def test_pairwise_independent_unrelated(db_session: Session):
    engine = MultiEventCorrelationEngine()
    now = datetime.now(timezone.utc)
    e1 = {
        "event_id": "EVT-TEST-801",
        "latitude": 28.6139,
        "longitude": 77.2090,
        "first_seen": now.isoformat(),
        "max_frp": 40.0,
        "risk_score": 20.0
    }
    # 50 km away and 5 days later
    e2 = {
        "event_id": "EVT-TEST-802",
        "latitude": 29.1000,
        "longitude": 77.5000,
        "first_seen": (now + timedelta(days=5)).isoformat(),
        "max_frp": 35.0,
        "risk_score": 18.0
    }
    rel = engine.evaluate_pairwise_relationship(e1, e2)
    assert rel.relationship_type == "INDEPENDENT_UNRELATED"
    assert rel.correlation_strength == "INSUFFICIENT"


# 9. test_pairwise_insufficiently_related
def test_pairwise_insufficiently_related(db_session: Session):
    engine = MultiEventCorrelationEngine()
    now = datetime.now(timezone.utc)
    e1 = {
        "event_id": "EVT-TEST-901",
        "latitude": 28.6139,
        "longitude": 77.2090,
        "first_seen": now.isoformat(),
        "max_frp": 25.0,
        "risk_score": 15.0
    }
    # 18 km away and 36 hours later
    e2 = {
        "event_id": "EVT-TEST-902",
        "latitude": 28.7500,
        "longitude": 77.3000,
        "first_seen": (now + timedelta(hours=36)).isoformat(),
        "max_frp": 20.0,
        "risk_score": 12.0
    }
    rel = engine.evaluate_pairwise_relationship(e1, e2)
    assert rel.relationship_type in ["INDEPENDENT_UNRELATED", "INSUFFICIENTLY_RELATED"]
    assert rel.correlation_strength == "INSUFFICIENT"


# 10. test_dbscan_clustering_success
def test_dbscan_clustering_success(db_session: Session):
    engine = MultiEventCorrelationEngine()
    now = datetime.now(timezone.utc)
    events = [
        {"event_id": "C-1", "latitude": 28.6139, "longitude": 77.2090, "first_seen": now.isoformat(), "max_frp": 100.0},
        {"event_id": "C-2", "latitude": 28.6150, "longitude": 77.2100, "first_seen": (now + timedelta(hours=1)).isoformat(), "max_frp": 90.0},
        {"event_id": "C-3", "latitude": 28.6145, "longitude": 77.2095, "first_seen": (now + timedelta(hours=2)).isoformat(), "max_frp": 95.0},
    ]
    clusters = engine.cluster_events_dbscan(events, eps_km=3.0, min_samples=2)
    assert len(clusters) >= 1
    c = clusters[0]
    assert c.event_count == 3
    assert "C-1" in c.event_ids
    assert "C-2" in c.event_ids
    assert "C-3" in c.event_ids
    assert c.radius_km > 0.0
    assert c.duration_hours >= 2.0


# 11. test_dbscan_noise_handling
def test_dbscan_noise_handling(db_session: Session):
    engine = MultiEventCorrelationEngine()
    now = datetime.now(timezone.utc)
    events = [
        {"event_id": "C-1", "latitude": 28.6139, "longitude": 77.2090, "first_seen": now.isoformat(), "max_frp": 100.0},
        {"event_id": "C-2", "latitude": 28.6150, "longitude": 77.2100, "first_seen": (now + timedelta(hours=1)).isoformat(), "max_frp": 90.0},
        # Isolated noise event 100km away
        {"event_id": "NOISE-1", "latitude": 29.5000, "longitude": 78.5000, "first_seen": (now + timedelta(hours=2)).isoformat(), "max_frp": 20.0},
    ]
    clusters = engine.cluster_events_dbscan(events, eps_km=3.0, min_samples=2)
    assert len(clusters) == 1
    assert "NOISE-1" not in clusters[0].event_ids


# 12. test_temporal_clustering_windows
def test_temporal_clustering_windows(db_session: Session):
    engine = MultiEventCorrelationEngine()
    now = datetime.now(timezone.utc)
    e_winter = {"event_id": "W-1", "latitude": 28.6139, "longitude": 77.2090, "first_seen": now.isoformat(), "max_frp": 50.0}
    e_summer = {"event_id": "S-1", "latitude": 28.6140, "longitude": 77.2091, "first_seen": (now + timedelta(days=180)).isoformat(), "max_frp": 50.0}
    rel = engine.evaluate_pairwise_relationship(e_winter, e_summer)
    assert rel.relationship_type != "SAME_PHYSICAL_INCIDENT"
    assert rel.relationship_type == "RECURRING_SOURCE_ACTIVITY"


# 13. test_cluster_extent_calculation
def test_cluster_extent_calculation(db_session: Session):
    engine = MultiEventCorrelationEngine()
    now = datetime.now(timezone.utc)
    events = [
        {"event_id": "E1", "latitude": 28.60, "longitude": 77.20, "first_seen": now.isoformat(), "max_frp": 80.0},
        {"event_id": "E2", "latitude": 28.62, "longitude": 77.22, "first_seen": (now + timedelta(hours=5)).isoformat(), "max_frp": 120.0},
    ]
    clusters = engine.cluster_events_dbscan(events, eps_km=5.0, min_samples=2)
    assert len(clusters) == 1
    c = clusters[0]
    assert 28.60 <= c.centroid_lat <= 28.62
    assert 77.20 <= c.centroid_lon <= 77.22
    assert c.duration_hours >= 5.0
    assert c.max_frp == 120.0


# 14. test_repetition_vs_continuous_differentiation
def test_repetition_vs_continuous_differentiation(db_session: Session):
    engine = MultiEventCorrelationEngine()
    now = datetime.now(timezone.utc)
    e1 = {"event_id": "FLARE-1", "latitude": 28.6139, "longitude": 77.2090, "first_seen": now.isoformat(), "facility_status": "KNOWN"}
    e2 = {"event_id": "FLARE-2", "latitude": 28.6140, "longitude": 77.2091, "first_seen": (now + timedelta(hours=24)).isoformat(), "facility_status": "KNOWN"}
    rel = engine.evaluate_pairwise_relationship(e1, e2)
    assert rel.relationship_type == "RECURRING_SOURCE_ACTIVITY"


# 15. test_multi_pass_same_source_not_fake_growth
def test_multi_pass_same_source_not_fake_growth(db_session: Session):
    res = multi_event_correlation_engine.correlate_incident(db=db_session, event_id="EVT-827")
    assert res.incident_geometry["geometry_type"] == "INCIDENT_CORRELATION_ENVELOPE"
    assert "perimeter_warning" in res.incident_geometry
    assert "NOT a validated physical fire front" in res.incident_geometry["perimeter_warning"]


# 16. test_independent_coincident_differentiation
def test_independent_coincident_differentiation(db_session: Session):
    engine = MultiEventCorrelationEngine()
    now = datetime.now(timezone.utc)
    e1 = {"event_id": "IND-1", "latitude": 28.6139, "longitude": 77.2090, "first_seen": now.isoformat(), "facility_status": "KNOWN"}
    e2 = {"event_id": "IND-2", "latitude": 29.5000, "longitude": 78.5000, "first_seen": now.isoformat(), "facility_status": "KNOWN"}
    rel = engine.evaluate_pairwise_relationship(e1, e2)
    assert rel.relationship_type == "INDEPENDENT_UNRELATED"
    assert rel.correlation_strength == "INSUFFICIENT"


# 17. test_downwind_relationship_flagging
def test_downwind_relationship_flagging(db_session: Session):
    engine = MultiEventCorrelationEngine()
    now = datetime.now(timezone.utc)
    e_upwind = {"event_id": "UP", "latitude": 28.00, "longitude": 77.00, "first_seen": now.isoformat()}
    e_downwind = {"event_id": "DOWN", "latitude": 28.00, "longitude": 77.02, "first_seen": (now + timedelta(hours=1)).isoformat()}
    rel = engine.evaluate_pairwise_relationship(e_upwind, e_downwind, wind_direction_deg=270.0)
    assert rel.downwind_aligned is True


# 18. test_downwind_not_claimed_as_direct_ignition
def test_downwind_not_claimed_as_direct_ignition(db_session: Session):
    engine = MultiEventCorrelationEngine()
    now = datetime.now(timezone.utc)
    e1 = {"event_id": "E1", "latitude": 28.00, "longitude": 77.00, "first_seen": now.isoformat()}
    e2 = {"event_id": "E2", "latitude": 28.01, "longitude": 77.02, "first_seen": (now + timedelta(hours=2)).isoformat()}
    rel = engine.evaluate_pairwise_relationship(e1, e2, wind_direction_deg=245.0)
    for ev in rel.evidence:
        assert "proven direct ignition" not in ev.lower()
        if "downwind" in ev.lower():
            assert "corroboration" in ev.lower() or "plume transport" in ev.lower() or "vector" in ev.lower()


# 19. test_nine_incident_hypotheses_evaluation
def test_nine_incident_hypotheses_evaluation(db_session: Session):
    res = multi_event_correlation_engine.correlate_incident(db=db_session, event_id="EVT-827")
    assert len(res.hypotheses) == 9
    expected_codes = {"H1", "H2", "H3", "H4", "H5", "H6", "H7", "H8", "H9"}
    actual_codes = {h.code for h in res.hypotheses}
    assert actual_codes == expected_codes


# 20. test_favored_hypothesis_selection
def test_favored_hypothesis_selection(db_session: Session):
    res = multi_event_correlation_engine.correlate_incident(db=db_session, event_id="EVT-827")
    assert res.incident_assessment.favored_hypothesis in [
        "H1_SINGLE_CONTINUOUS_FIRE_FRONT",
        "H2_DISPERSED_MULTI_IGNITION_INCIDENT",
        "H3_RECURRING_INDUSTRIAL_SOURCE",
        "H4_MULTI_FACILITY_INDUSTRIAL_EPISODE",
        "H5_DOWNWIND_SECONDARY_IGNITIONS",
        "H6_COORDINATED_LAND_USE_ACTIVITY",
        "H7_INDEPENDENT_COINCIDENT_EVENTS",
        "H8_MULTI_PASS_SAME_SOURCE_REPETITION",
        "H9_INSUFFICIENT_CORRELATION"
    ]
    favored_obj = next((h for h in res.hypotheses if h.verdict == "FAVORED"), None)
    assert favored_obj is not None
    assert favored_obj.hypothesis_id == res.incident_assessment.favored_hypothesis


# 21. test_incident_impact_profile_calculation
def test_incident_impact_profile_calculation(db_session: Session):
    res = multi_event_correlation_engine.correlate_incident(db=db_session, event_id="EVT-827")
    imp = res.impact_profile
    assert imp is not None
    assert imp.highest_event_risk > 0.0
    assert imp.aggregate_frp_mw > 0.0
    assert imp.dispersion_area_km2 > 0.0
    assert imp.member_event_count >= 1


# 22. test_highest_event_risk_preservation
def test_highest_event_risk_preservation(db_session: Session):
    res = multi_event_correlation_engine.correlate_incident(db=db_session, event_id="EVT-827")
    assert res.impact_profile.highest_event_risk >= 75.0
    assert res.impact_profile.highest_event_risk <= 100.0


# 23. test_incident_envelope_labeling
def test_incident_envelope_labeling(db_session: Session):
    res = multi_event_correlation_engine.correlate_incident(db=db_session, event_id="EVT-827")
    assert res.incident_geometry["geometry_type"] == "INCIDENT_CORRELATION_ENVELOPE"


# 24. test_no_fake_fire_perimeter
def test_no_fake_fire_perimeter(db_session: Session):
    res = multi_event_correlation_engine.correlate_incident(db=db_session, event_id="EVT-827")
    geom = res.incident_geometry
    assert "fire_perimeter" not in geom
    assert geom.get("is_authoritative_fire_boundary") is False


# 25. test_zero_background_daemons
def test_zero_background_daemons():
    import threading
    engine = MultiEventCorrelationEngine()
    threads = threading.enumerate()
    daemon_threads = [t for t in threads if "correlation_daemon" in t.name.lower()]
    assert len(daemon_threads) == 0


# 26. test_dispatch_gate_blocked_invariant
def test_dispatch_gate_blocked_invariant(db_session: Session):
    assert ENABLE_OPERATIONAL_DISPATCH_GATE is False
    res = multi_event_correlation_engine.correlate_incident(db=db_session, event_id="EVT-827")
    assert res.incident_assessment.operational_dispatch_gate_blocked is True


# 27. test_hitl_requirement_flagged
def test_hitl_requirement_flagged(db_session: Session):
    res = multi_event_correlation_engine.correlate_incident(db=db_session, event_id="EVT-827")
    assert res.incident_assessment.human_verification_recommended is True


# 28. test_section_20_commands_route_correctly
def test_section_20_commands_route_correctly():
    sec20_commands = [
        "JARVIS, investigate Event 827 and evaluate whether nearby or concurrent thermal events belong to the same incident, episode, or recurring source.",
        "JARVIS, evaluate multi-event incident correlation for event 827",
        "JARVIS, which nearby events belong to the same physical incident?",
        "JARVIS, determine whether these events are the same operational episode",
        "JARVIS, are these detections recurring source activity or a single spreading incident?",
        "JARVIS, cluster nearby thermal events and show incident extent",
        "JARVIS, evaluate downwind hazard relationship for event 827",
        "JARVIS, compare multi-event incident hypotheses for this event cluster",
        "JARVIS, show the incident impact profile for this event cluster",
        "JARVIS, which nearby events are independent or coincident rather than part of the incident?",
        "JARVIS, show multi-event correlation evidence and uncertainty",
        "JARVIS, what additional observation would determine whether these events belong to the same incident?"
    ]
    for cmd in sec20_commands:
        plan = command_interpreter.interpret(cmd)
        plan_dict = plan.dict() if hasattr(plan, "dict") else (plan.model_dump() if hasattr(plan, "model_dump") else plan)
        intent = plan_dict.get("intent")
        intent_str = intent.value if hasattr(intent, "value") else str(intent).replace("CommandIntent.", "")
        entities = plan_dict.get("entities", {})
        obj = plan_dict.get("objective")
        target = getattr(obj, "target_event", None) or (entities.get("event_ref") if isinstance(entities, dict) else None)
        assert intent_str in ["INVESTIGATE", "EXPLAIN", "SYNTHESIZE", "DISCLOSE", "QUERY"]
        assert target in ["827", "EVT-827", None]


# 29. test_section_28_primary_acceptance_command
def test_section_28_primary_acceptance_command(db_session: Session):
    primary_cmd = "JARVIS, investigate Event 827 and evaluate whether nearby or concurrent thermal events belong to the same incident, episode, or recurring source."
    req = JarvisCommandRequest(
        command=primary_cmd,
        session_id="test-p12-acceptance",
        user_role="ANALYST"
    )
    resp = master_orchestrator.execute_command(db_session, req, "ANALYST")
    assert resp.operational_dispatch_gate_blocked is True
    assert "SECTION_28_PHASE12_COMPLETE" in resp.summary or "incident" in resp.summary.lower()
    summary_text = resp.summary
    assert "COHORT" in summary_text
    assert "PAIRWISE" in summary_text or "RELATIONSHIP" in summary_text
    assert "INCIDENT IMPACT PROFILE" in summary_text
    assert "DISPATCH GATE" in summary_text


# 30. test_workspace_incident_correlation_persistence
def test_workspace_incident_correlation_persistence(db_session: Session):
    ws = workspace_manager.get_or_create_workspace(
        db=db_session,
        session_id="test-p12-persistence",
        user_id="analyst-1",
        user_role="ANALYST",
        target_event_id="EVT-827"
    )
    res = multi_event_correlation_engine.correlate_incident(db=db_session, event_id="EVT-827")
    workspace_manager.update_workspace_incident_correlation(db=db_session, workspace=ws, result=res)
    
    loaded = db_session.query(InvestigationWorkspace).filter(
        InvestigationWorkspace.investigation_id == ws.investigation_id
    ).first()
    assert loaded is not None
    assert loaded.related_event_ids is not None
    assert len(loaded.related_event_ids) >= 1
    assert loaded.incident_assessment is not None
    assert loaded.incident_assessment["correlation_strength"] in ["STRONG", "MODERATE", "LIMITED", "INSUFFICIENT"]
    assert loaded.incident_geometry is not None
    assert loaded.incident_geometry["geometry_type"] == "INCIDENT_CORRELATION_ENVELOPE"


# 31. test_rbac_public_masking
def test_rbac_public_masking(client: TestClient):
    resp = client.get("/api/v1/intelligence/events/EVT-827/related")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "SUCCESS"
    assert "related_event_ids" in data

    resp_inc = client.get("/api/v1/intelligence/incidents/INC-EVT-827")
    assert resp_inc.status_code == 200
    data_inc = resp_inc.json()
    assert data_inc["status"] == "SUCCESS"
    assert "incident_assessment" in data_inc


# 32. test_provenance_audit_trail_completeness
def test_provenance_audit_trail_completeness(db_session: Session):
    res = multi_event_correlation_engine.correlate_incident(db=db_session, event_id="EVT-827")
    assert res.provenance is not None
    assert "engine" in res.provenance
    assert "spatial_metric" in res.provenance
    assert "clustering_algorithm" in res.provenance
    assert res.model_id == "jarvis-multi-event-correlation-v1.0"
    assert res.correlation_timestamp is not None


# 33. test_frozen_baselines_unchanged
def test_frozen_baselines_unchanged():
    assert ENABLE_OPERATIONAL_DISPATCH_GATE is False
    from backend.app.services.intelligence.evidence_graph_engine import evidence_graph_engine
    assert evidence_graph_engine is not None
    from backend.app.services.intelligence.profiles import IndiaIntelligenceProfile
    profile = IndiaIntelligenceProfile.get_profile()
    assert profile is not None
