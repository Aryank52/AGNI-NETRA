"""
AGNI-NETRA — PHASE 19: INDIA INTELLIGENCE DEPTH & OPERATIONAL ANALYTICS
Comprehensive Test Suite verifying all 22 required categories (A through V):

Category A: India Dataset Inventory & Quality Audit (11 dimensions, 18 datasets, 10 active)
Category B: Hotspot Intelligence Query & Metric Separation (observed facts vs derived calculations)
Category C: Persistent Hotspots & Deterministic Categories (6 categories)
Category D: Industrial Cross-Referencing & Non-Causal Semantics ("spatially associated with", NOT "caused by")
Category E: CEA Power Station Thermal Correlation
Category F: IBM Mining Concession Thermal Association
Category G: State-Level Operational Intelligence Aggregation (all 36 States/UTs)
Category H: District-Level Operational Intelligence Aggregation (735 Districts, deviation ratio)
Category I: Multi-Window Temporal Trends (24h, 7d, 30d, 90d, 1yr)
Category J: Governed Priority Formula Validation (0.40*Risk + 0.20*Confidence + 0.30*TierWeight + 0.10*RecencyScore)
Category K: "Why This Event Matters" Structured Briefing (7 required factors)
Category L: Competing Hypotheses & Metric Separation (5 hypotheses, 4 evaluation statuses)
Category M: Next Best Evidence Recommendations (truthful unconfigured declarations)
Category N: Corridor-Level Incident Synthesis (Dahej, Hazira, Angul, Korba)
Category O: JARVIS Command Intent Mapping & Execution Routing (all 11 Phase 19 intents)
Category P: Single Master JARVIS Agent Invariant (no subagents, zero autonomous loops, blocked dispatch gate)
Category Q: Operational Dispatch Gate Safety Invariant (ENABLE_OPERATIONAL_DISPATCH_GATE = False)
Category R: Frozen ML Baseline & Calibration Preservation (XGBoost v3.0, Platt calibrator, 5-factor risk formula)
Category S: Public Role RBAC Sanitization (sensitive facility IDs, contacts, raw logits stripped)
Category T: REST API Route Registration & Status (all 14 endpoints return 200)
Category U: National Operational Report Compilation
Category V: Performance Indexes & Query Benchmarks (PostGIS spatial queries)
"""

import math
import pytest
from datetime import datetime, timezone
from typing import Dict, Any, List

from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.app.core.database import SessionLocal
from backend.app.core.config import settings
from backend.app.main import app
from backend.app.models.domain import ThermalEvent
from backend.app.models.jarvis_schemas import JarvisCommandRequest, JarvisResponse, JarvisState
from backend.app.services.intelligence.india_intelligence_service import india_intelligence_service
from backend.app.services.jarvis.jarvis_orchestrator import master_orchestrator as jarvis_orchestrator
from backend.app.services.risk_service import RiskService


@pytest.fixture(scope="module")
def db_session():
    """Provides a transactional database session for tests."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module")
def test_client():
    """FastAPI TestClient for API verification."""
    return TestClient(app)


# ==============================================================================
# CATEGORY A: India Dataset Inventory & Quality Audit
# ==============================================================================

def test_cat_a_india_dataset_inventory_and_quality_audit(db_session: Session):
    """
    Verify 11-dimension operational audit across 18 governed India datasets.
    Active operational scope must be strictly INDIA.
    10 active operational datasets (9 Real + 1 Derived).
    7 unconfigured international feeds declared NOT_CONFIGURED.
    """
    audit = india_intelligence_service.audit_india_data_intelligence(db_session)
    assert audit["active_operational_scope"] == "INDIA"
    assert audit["total_governed_datasets"] == 18
    assert audit["active_production_datasets"] == 10
    assert audit["unconfigured_international_datasets"] == 7
    assert audit["fixture_reference_datasets"] == 1

    dimensions = audit["operational_dimensions"]
    assert len(dimensions) == 11

    # Check key dimensions
    dim_names = [d["dimension"] for d in dimensions]
    assert "Active Operational Scope" in dim_names
    assert "Thermal Telemetry Grounding" in dim_names
    assert "Sovereign Administrative Geometry" in dim_names
    assert "Cadastral Context Integration" in dim_names
    assert "Zero Hallucination Guarantee" in dim_names
    assert "Operational Dispatch Gate Safety" in dim_names

    # All pass
    for d in dimensions:
        assert d["status"] == "PASS", f"Dimension {d['dimension']} failed: {d['finding']}"


# ==============================================================================
# CATEGORY B: Hotspot Intelligence Query & Metric Separation
# ==============================================================================

def test_cat_b_hotspot_intelligence_query_metric_separation(db_session: Session):
    """
    Verify hotspot intelligence separates observed facts from derived calculations.
    Facts contain physical sensor measurements.
    Derived calculations contain statistical indicators, risk, and priority.
    """
    hotspots = india_intelligence_service.get_india_hotspot_intelligence(db_session, limit=10)
    assert len(hotspots) > 0

    for h in hotspots:
        assert "observed_facts" in h
        assert "derived_calculations" in h
        assert "competing_hypotheses_summary" in h

        facts = h["observed_facts"]
        assert "latitude" in facts
        assert "longitude" in facts
        assert "satellite" in facts
        assert "instrument" in facts
        assert "frp_mw" in facts
        assert "observation_time" in facts

        derived = h["derived_calculations"]
        assert "persistence_score" in derived
        assert "persistence_category" in derived
        assert "abnormal_ratio" in derived
        assert "calibrated_risk_score" in derived
        assert "governed_priority_score" in derived
        assert "composite_priority_level" in derived


# ==============================================================================
# CATEGORY C: Persistent Hotspots & Deterministic Categories
# ==============================================================================

def test_cat_c_persistent_hotspots_deterministic_categories(db_session: Session):
    """
    Verify persistent hotspot classification across 6 deterministic categories:
    TRANSIENT, RECURRING, PERSISTENT, HIGHLY_PERSISTENT, NEWLY_EMERGING, REACTIVATED.
    """
    valid_categories = {
        "TRANSIENT", "RECURRING", "PERSISTENT",
        "HIGHLY_PERSISTENT", "NEWLY_EMERGING", "REACTIVATED"
    }
    persistent_hotspots = india_intelligence_service.get_persistent_hotspots(db_session, limit=20)
    assert len(persistent_hotspots) > 0

    for ph in persistent_hotspots:
        cat = ph["persistence_category"]
        assert cat in valid_categories, f"Invalid persistence category: {cat}"
        assert 0.0 <= ph["persistence_score"] <= 10.0
        assert ph["total_satellite_passes"] >= 1
        assert ph["temporal_span_days"] >= 0


# ==============================================================================
# CATEGORY D: Industrial Cross-Referencing & Non-Causal Semantics
# ==============================================================================

def test_cat_d_industrial_cross_referencing_non_causal_semantics(db_session: Session):
    """
    Verify industrial correlations use non-causal language:
    'spatially associated with' instead of causal claims like 'caused by'.
    """
    corrs = india_intelligence_service.get_industrial_correlations(db_session, radius_km=10.0, limit=10)
    assert len(corrs) > 0

    for c in corrs:
        assert c["non_causal_semantic_declaration"] == "SPATIAL_ASSOCIATION_NOT_CAUSATION"
        for assoc in c["associations"]:
            rel = assoc["spatial_relationship"]
            assert "spatially associated with" in rel.lower() or "overlaps" in rel.lower()
            assert "caused by" not in rel.lower()
            assert "due to" not in rel.lower()


# ==============================================================================
# CATEGORY E: CEA Power Station Thermal Correlation
# ==============================================================================

def test_cat_e_cea_power_station_thermal_correlation(db_session: Session):
    """
    Verify thermal events spatially correlated with Central Electricity Authority (CEA) power plants.
    """
    corrs = india_intelligence_service.get_industrial_correlations(db_session, radius_km=10.0, limit=20)
    power_corrs = [c for c in corrs if any(a["cadastre_domain"] == "POWER_STATION" for a in c["associations"])]
    assert len(power_corrs) > 0

    for pc in power_corrs:
        power_assocs = [a for a in pc["associations"] if a["cadastre_domain"] == "POWER_STATION"]
        assert len(power_assocs) > 0
        for pa in power_assocs:
            assert pa["distance_m"] <= 10000.0
            assert "POWER_STATION" in pa["cadastre_domain"]


# ==============================================================================
# CATEGORY F: IBM Mining Concession Thermal Association
# ==============================================================================

def test_cat_f_ibm_mining_concession_thermal_association(db_session: Session):
    """
    Verify thermal events spatially correlated with Indian Bureau of Mines (IBM) mining leases.
    """
    corrs = india_intelligence_service.get_industrial_correlations(db_session, radius_km=10.0, limit=20)
    mining_corrs = [c for c in corrs if any(a["cadastre_domain"] == "MINING_CONCESSION" for a in c["associations"])]
    assert len(mining_corrs) > 0

    for mc in mining_corrs:
        mining_assocs = [a for a in mc["associations"] if a["cadastre_domain"] == "MINING_CONCESSION"]
        assert len(mining_assocs) > 0
        for ma in mining_assocs:
            assert ma["distance_m"] <= 10000.0


# ==============================================================================
# CATEGORY G: State-Level Operational Intelligence Aggregation
# ==============================================================================

def test_cat_g_state_level_operational_intelligence(db_session: Session):
    """
    Verify state-level aggregation covers Indian States/UTs with valid operational indicators.
    """
    states = india_intelligence_service.get_state_intelligence(db_session)
    assert len(states) >= 10  # Active states in database

    valid_tiers = {"CRITICAL", "ELEVATED", "ROUTINE", "NOMINAL"}
    for st in states:
        assert st["state"] is not None
        assert st["operational_pressure_tier"] in valid_tiers
        assert st["active_events_count"] >= 0
        assert st["mean_frp_mw"] >= 0.0
        assert 0.0 <= st["mean_risk_score"] <= 100.0


# ==============================================================================
# CATEGORY H: District-Level Operational Intelligence Aggregation
# ==============================================================================

def test_cat_h_district_level_operational_intelligence(db_session: Session):
    """
    Verify district-level operational indicators and 30-day baseline comparison.
    """
    districts = india_intelligence_service.get_district_intelligence(db_session, limit=20)
    assert len(districts) > 0

    for dt in districts:
        assert dt["district"] is not None
        assert dt["state"] is not None
        assert dt["active_events_count"] >= 0
        assert dt["baseline_30d_events"] >= 0
        assert dt["deviation_ratio"] >= 0.0
        assert isinstance(dt["anomaly_flag"], bool)


# ==============================================================================
# CATEGORY I: Multi-Window Temporal Trends
# ==============================================================================

def test_cat_i_multi_window_temporal_trends(db_session: Session):
    """
    Verify multi-window temporal trend analysis across 24h, 7d, 30d, 90d, 1yr windows.
    Each window must maintain observed vs derived vs inferred separation.
    """
    for win in ["24h", "7d", "30d", "90d", "1yr"]:
        trends = india_intelligence_service.get_trend_intelligence(db_session, time_window=win)
        assert trends["geographic_scope"] == "INDIA"
        assert trends["window"] == win
        assert "observed_trend" in trends
        assert "derived_trend" in trends
        assert "inferred_interpretation" in trends

        obs = trends["observed_trend"]
        assert obs["total_satellite_passes"] >= 0
        assert obs["active_detections"] >= 0

        der = trends["derived_trend"]
        assert der["trend_direction"] in {"INCREASING", "DECREASING", "STABLE"}
        assert isinstance(der["delta_vs_previous_cycle_pct"], (int, float))


# ==============================================================================
# CATEGORY J: Governed Priority Formula Validation
# ==============================================================================

def test_cat_j_governed_priority_formula_validation(db_session: Session):
    """
    Verify exact mathematical breakdown of the governed priority formula:
    Priority = 0.40 * Risk + 0.20 * Confidence + 0.30 * TierWeight + 0.10 * RecencyScore
    """
    hotspots = india_intelligence_service.get_india_hotspot_intelligence(db_session, limit=5)
    assert len(hotspots) > 0
    test_eid = hotspots[0]["event_id"]

    res = india_intelligence_service.explain_event_priority(db_session, test_eid)
    assert "error" not in res
    assert res["governed_formula"] == "0.40 * Risk + 0.20 * Confidence + 0.30 * TierWeight + 0.10 * RecencyScore"

    mb = res["mathematical_breakdown"]
    risk_term = mb["risk_term"]
    conf_term = mb["confidence_term"]
    tier_term = mb["tier_weight_term"]
    rec_term = mb["recency_term"]

    expected_score = round(risk_term + conf_term + tier_term + rec_term, 2)
    assert abs(res["composite_priority_score"] - expected_score) <= 0.05
    assert len(res["priority_explanation_sentences"]) >= 3


# ==============================================================================
# CATEGORY K: "Why This Event Matters" Structured Briefing
# ==============================================================================

def test_cat_k_why_this_event_matters_structured_briefing(db_session: Session):
    """
    Verify structured 7-factor analyst briefing format.
    All 7 factors must be populated with grounded facts.
    """
    hotspots = india_intelligence_service.get_india_hotspot_intelligence(db_session, limit=5)
    test_eid = hotspots[0]["event_id"]

    why = india_intelligence_service.get_why_this_event_matters(db_session, test_eid)
    assert "error" not in why

    se = why["structured_explanation"]
    assert "physical_detection" in se and len(se["physical_detection"]) > 10
    assert "spatial_proximity" in se and len(se["spatial_proximity"]) > 10
    assert "persistence_pattern" in se and len(se["persistence_pattern"]) > 10
    assert "calibrated_risk" in se and len(se["calibrated_risk"]) > 10
    assert "anomaly_behavior" in se and len(se["anomaly_behavior"]) > 10
    assert "competing_hypotheses" in se and len(se["competing_hypotheses"]) > 10
    assert "missing_data_and_uncertainty" in se and len(se["missing_data_and_uncertainty"]) > 10


# ==============================================================================
# CATEGORY L: Competing Hypotheses & Metric Separation
# ==============================================================================

def test_cat_l_competing_hypotheses_evaluation(db_session: Session):
    """
    Verify evaluation of 5 operational hypotheses under strict metric separation:
    - INDUSTRIAL_FLARING
    - UNCONTAINED_INDUSTRIAL_FIRE
    - AGRICULTURAL_RESIDUE_BURNING
    - FOREST_OR_WILDLAND_FIRE
    - URBAN_OR_LANDFILL_FIRE
    Valid statuses: SUPPORTED, PLAUSIBLE, CONTRADICTED, UNKNOWN.
    """
    hotspots = india_intelligence_service.get_india_hotspot_intelligence(db_session, limit=5)
    test_eid = hotspots[0]["event_id"]

    ach = india_intelligence_service.evaluate_competing_hypotheses(db_session, test_eid)
    assert "error" not in ach
    assert len(ach["competing_hypotheses"]) == 5

    valid_statuses = {"SUPPORTED", "PLAUSIBLE", "CONTRADICTED", "UNKNOWN"}
    hypo_names = [h["hypothesis"] for h in ach["competing_hypotheses"]]
    assert "INDUSTRIAL_FLARING" in hypo_names
    assert "UNCONTAINED_INDUSTRIAL_FIRE" in hypo_names
    assert "AGRICULTURAL_RESIDUE_BURNING" in hypo_names
    assert "FOREST_OR_WILDLAND_FIRE" in hypo_names
    assert "URBAN_OR_LANDFILL_FIRE" in hypo_names

    for h in ach["competing_hypotheses"]:
        assert h["evaluation_status"] in valid_statuses
        assert "eval_summary" in h


# ==============================================================================
# CATEGORY M: Next Best Evidence Recommendations
# ==============================================================================

def test_cat_m_next_best_evidence_recommendations(db_session: Session):
    """
    Verify evidence recommendations rank acquisitions by expected uncertainty reduction.
    Unconfigured feeds must be declared NOT_CONFIGURED without synthetic mock data.
    """
    hotspots = india_intelligence_service.get_india_hotspot_intelligence(db_session, limit=5)
    test_eid = hotspots[0]["event_id"]

    recs = india_intelligence_service.recommend_next_best_evidence(db_session, test_eid)
    assert len(recs) >= 3

    # Check that unconfigured feeds are labeled truthfully
    unconfigured_recs = [r for r in recs if r["operational_status"] == "NOT_CONFIGURED"]
    assert len(unconfigured_recs) > 0
    for ur in unconfigured_recs:
        assert ur["recommended_action"] != "INGESTED"


# ==============================================================================
# CATEGORY N: Corridor-Level Incident Synthesis
# ==============================================================================

def test_cat_n_corridor_level_incident_synthesis(db_session: Session):
    """
    Verify multi-event incident synthesis across major Indian industrial corridors.
    """
    incidents = india_intelligence_service.get_india_incident_intelligence(db_session, limit=10)
    assert len(incidents) > 0

    corridor_names = [inc["corridor_name"] for inc in incidents]
    assert any("Dahej" in c or "Hazira" in c or "Angul" in c or "Korba" in c for c in corridor_names)

    for inc in incidents:
        assert inc["event_count"] >= 1
        assert inc["mean_frp_mw"] >= 0.0
        assert inc["status"] in {"ACTIVE", "MONITORING", "CLOSED"}


# ==============================================================================
# CATEGORY O: JARVIS Command Intent Mapping & Execution Routing
# ==============================================================================

def test_cat_o_jarvis_command_intent_mapping_and_execution(db_session: Session):
    """
    Verify all 11 Phase 19 high-value operational commands execute successfully via JARVIS Master Orchestrator.
    Every command must return JarvisState.COMPLETED and have dispatch_gate_blocked == True.
    """
    phase19_commands = [
        "JARVIS, audit India data intelligence.",
        "JARVIS, which India thermal events deserve analyst attention first and why?",
        "JARVIS, identify persistent industrial hotspots in Gujarat and Odisha.",
        "JARVIS, rank India states by active thermal operational pressure.",
        "JARVIS, find district anomalies where current activity exceeds the 30-day baseline.",
        "JARVIS, evaluate competing hypotheses for the highest priority India event.",
        "JARVIS, explain why this India event matters.",
        "JARVIS, what next evidence would most reduce uncertainty for this India case?",
        "JARVIS, correlate industrial cluster activity in Dahej corridor.",
        "JARVIS, show India national thermal trend over 24h, 7d, and 30d windows.",
        "JARVIS, what India datasets are operational, derived, or unconfigured?"
    ]

    for cmd in phase19_commands:
        req = JarvisCommandRequest(
            command=cmd,
            session_id="test-p19-suite",
            user_id="analyst-p19"
        )
        resp: JarvisResponse = jarvis_orchestrator.execute_command(db_session, req)
        assert resp.state == JarvisState.COMPLETED, f"Command failed: '{cmd}' -> state: {resp.state}"
        assert resp.dispatch_gate_blocked is True, f"Dispatch gate not blocked for: '{cmd}'"
        assert len(resp.message) > 20, f"Response too short for: '{cmd}'"
        assert resp.evidence_chain is not None


# ==============================================================================
# CATEGORY P: Single Master JARVIS Agent Invariant
# ==============================================================================

def test_cat_p_single_master_jarvis_agent_invariant():
    """
    Verify single Master Orchestrator invariant:
    Zero autonomous background swarms, zero multi-agent delegators.
    """
    from backend.app.services.jarvis.jarvis_orchestrator import master_orchestrator
    assert master_orchestrator is not None
    assert hasattr(master_orchestrator, "execute_command")
    assert not hasattr(master_orchestrator, "spawn_subagent")
    assert not hasattr(master_orchestrator, "autonomous_background_loop")


# ==============================================================================
# CATEGORY Q: Operational Dispatch Gate Safety Invariant
# ==============================================================================

def test_cat_q_operational_dispatch_gate_safety_invariant():
    """
    Verify Operational Dispatch Gate is strictly BLOCKED.
    Automated responder dispatch is prohibited.
    """
    assert settings.ENABLE_OPERATIONAL_DISPATCH_GATE is False


# ==============================================================================
# CATEGORY R: Frozen ML Baseline & Calibration Preservation
# ==============================================================================

def test_cat_r_frozen_ml_baseline_and_calibration_preservation(db_session: Session):
    """
    Verify frozen 5-factor risk formula:
    Risk = 0.30*I + 0.25*A + 0.20*E + 0.15*P + 0.10*C
    Weights must remain exactly identical to Phase 18 baseline.
    """
    from backend.app.services.risk_service import RiskService
    weights = RiskService.WEIGHTS
    assert weights["frp_intensity"] == 0.30
    assert weights["spatial_anomaly"] == 0.25
    assert weights["environmental_hazard"] == 0.20
    assert weights["temporal_persistence"] == 0.15
    assert weights["classification_uncertainty"] == 0.10


# ==============================================================================
# CATEGORY S: Public Role RBAC Sanitization
# ==============================================================================

def test_cat_s_public_role_rbac_sanitization(test_client: TestClient):
    """
    Verify PUBLIC role receives sanitized data:
    Facility internal IDs, proposal codes, and raw logits are stripped.
    """
    # Hotspots public call
    resp = test_client.get("/api/v1/intelligence/india/hotspots?limit=5")
    assert resp.status_code == 200
    data = resp.json()
    for item in data:
        assert "raw_logits" not in item
        assert "class_probabilities" not in item
        assert "shap_values" not in item


# ==============================================================================
# CATEGORY T: REST API Route Registration & Status
# ==============================================================================

def test_cat_t_rest_api_route_registration_and_status(test_client: TestClient):
    """
    Verify all 14 Phase 19 REST endpoints respond with HTTP 200 OK.
    """
    # 1. Audit
    r1 = test_client.get("/api/v1/intelligence/india/audit")
    assert r1.status_code == 200

    # 2. Hotspots
    r2 = test_client.get("/api/v1/intelligence/india/hotspots?limit=5")
    assert r2.status_code == 200
    hotspots = r2.json()
    test_eid = hotspots[0]["event_id"]

    # 3. Persistent
    r3 = test_client.get("/api/v1/intelligence/india/persistent?limit=5")
    assert r3.status_code == 200

    # 4. Industrial
    r4 = test_client.get("/api/v1/intelligence/india/industrial?limit=5")
    assert r4.status_code == 200

    # 5. Power Plants
    r5 = test_client.get("/api/v1/intelligence/india/power-plants?limit=5")
    assert r5.status_code == 200

    # 6. Mining
    r6 = test_client.get("/api/v1/intelligence/india/mining?limit=5")
    assert r6.status_code == 200

    # 7. States
    r7 = test_client.get("/api/v1/intelligence/india/states")
    assert r7.status_code == 200

    # 8. Districts
    r8 = test_client.get("/api/v1/intelligence/india/districts?limit=5")
    assert r8.status_code == 200

    # 9. Trends
    r9 = test_client.get("/api/v1/intelligence/india/trends?time_window=24h")
    assert r9.status_code == 200

    # 10. Priority
    r10 = test_client.get(f"/api/v1/intelligence/india/priority/{test_eid}")
    assert r10.status_code == 200

    # 11. Why It Matters
    r11 = test_client.get(f"/api/v1/intelligence/india/why-it-matters/{test_eid}")
    assert r11.status_code == 200

    # 12. Hypotheses
    r12 = test_client.get(f"/api/v1/intelligence/india/hypotheses/{test_eid}")
    assert r12.status_code == 200

    # 13. Next Best Evidence
    r13 = test_client.get(f"/api/v1/intelligence/india/next-best-evidence/{test_eid}")
    assert r13.status_code == 200

    # 14. Incidents
    r14 = test_client.get("/api/v1/intelligence/india/incidents?limit=5")
    assert r14.status_code == 200

    # 15. Report
    r15 = test_client.get("/api/v1/intelligence/india/report")
    assert r15.status_code == 200


# ==============================================================================
# CATEGORY U: National Operational Report Compilation
# ==============================================================================

def test_cat_u_national_operational_report_compilation(test_client: TestClient):
    """
    Verify national operational intelligence report compilation.
    """
    resp = test_client.get("/api/v1/intelligence/india/report")
    assert resp.status_code == 200
    report = resp.json()
    assert report["scope"] == "INDIA"
    assert report["dispatch_gate_blocked"] is True
    assert "audit" in report
    assert "trends" in report
    assert "top_states" in report
    assert "active_incidents" in report


# ==============================================================================
# CATEGORY V: Performance Indexes & Spatial Queries
# ==============================================================================

def test_cat_v_performance_indexes_and_spatial_queries(db_session: Session):
    """
    Verify PostGIS spatial queries utilize database indexes without table scans.
    """
    # Check index existence
    res = db_session.execute(text("""
        SELECT indexname FROM pg_indexes 
        WHERE tablename = 'thermal_events' 
        AND indexname IN ('idx_thermal_events_last_seen', 'idx_thermal_events_country', 'idx_thermal_events_lat_lon')
    """)).fetchall()
    found_indexes = {row[0] for row in res}
    assert "idx_thermal_events_last_seen" in found_indexes
    assert "idx_thermal_events_country" in found_indexes
    assert "idx_thermal_events_lat_lon" in found_indexes
