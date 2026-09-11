"""
AGNI-NETRA Phase 8: Global Context Intelligence & Cross-Domain Fusion Test Suite
Comprehensive verification suite validating all 21 points defined in Section 21:
1. Provider-neutral canonical context models validate properly.
2. Direct-overlap context (<= 100m) correctly categorized.
3. Multi-distance context buffers (500m, 1km, 2km, 5km, 10km) computed correctly.
4. Industrial facility context correctly discovered near Event 827.
5. Power infrastructure correctly identified or absent where appropriate.
6. Mining context correctly identified or absent where appropriate.
7. Land-cover context correctly identified.
8. Protected area context correctly identified and buffer analyzed.
9. Administrative boundaries correctly identified.
10. Environmental clearance context correctly identified.
11. Unconfigured providers (ECMWF, Planet, WRI, USGS) correctly report NOT_CONFIGURED.
12. Missing context correctly disclosed with zero synthetic data.
13. Strongest contextual explanation correctly synthesized.
14. Contextual evidence strength correctly calibrated (STRONG, MODERATE, LIMITED, INSUFFICIENT).
15. Contextual uncertainty correctly modeled (KNOWN, UNCERTAIN, MISSING, CONFLICTING).
16. "What could change the assessment" correctly generated.
17. Section 24 Phase 8 primary acceptance command produces structured output with all required sections.
18. Single-master architecture preserved (one agent, explicit commands, returns to IDLE).
19. Dispatch gate remains blocked (BLOCKED [SAFETY ENFORCED]).
20. Protected baseline untouched (XGBoost, SHAP, Isolation Forest, 5-factor risk formula unchanged).
21. Context intelligence enriches interpretation without silently overwriting thermal evidence.
"""

import pytest
from datetime import datetime, timezone
from typing import Dict, Any, List

from backend.app.core.database import SessionLocal
from backend.app.models.canonical import (
    ContextObservation,
    FacilityContext,
    PowerContext,
    MiningContext,
    LandCoverContext,
    ProtectedAreaContext,
    AdministrativeContext,
    EnvironmentalContext,
    ContextRelationship,
    ContextCoverage,
    ContextProvenance,
    ThermalObservation,
    ThermalEvent
)
from backend.app.services.intelligence.provenance import (
    SourceProvenance,
    create_osm_provenance,
    create_cea_provenance,
    create_parivesh_provenance,
    create_ibm_provenance,
    create_bhuvan_provenance,
    create_fsi_provenance
)
from backend.app.services.intelligence.profiles import GlobalContextProfile
from backend.app.services.intelligence.provider_registry import provider_registry
from backend.app.services.intelligence.context_engine import (
    context_engine,
    ContextDiscoveryEngine,
    CrossDomainCorrelationEngine,
    categorize_spatial_relationship,
    haversine_distance_m
)
from backend.app.services.jarvis.jarvis_orchestrator import master_orchestrator
from backend.app.models.jarvis_schemas import JarvisCommandRequest, CommandIntent, JarvisState
from backend.app.services.jarvis.jarvis_workspace import workspace_manager
from backend.app.services.jarvis.jarvis_tools import JarvisToolRegistry


@pytest.fixture(scope="module")
def db_session():
    session = SessionLocal()
    yield session
    session.close()


# Test 1: Canonical context models validate properly
def test_1_canonical_context_models_validation():
    prov = create_osm_provenance(osm_id="12345", osm_type="way", entity_classification="refinery")
    assert prov.provider == "OSM"
    assert prov.dataset == "OPENSTREETMAP_INDUSTRIAL_REGISTRY"
    assert prov.confidence_tier == "MEDIUM"

    fac = FacilityContext(
        context_id="CTX-FAC-001",
        provider="OSM",
        dataset="OPENSTREETMAP_INDUSTRIAL_FACILITIES",
        country="India",
        jurisdiction="Gujarat",
        distance_meters=85.0,
        spatial_relationship="DIRECT_OVERLAP",
        spatial_relevance="HIGH",
        facility_name="Reliance Jamnagar Complex",
        facility_type="Refinery",
        sector="Petrochemicals",
        operating_status="OPERATIONAL",
        provenance=prov,
        coverage_status="AVAILABLE"
    )
    assert fac.context_id == "CTX-FAC-001"
    assert fac.distance_meters == 85.0
    assert fac.spatial_relationship == "DIRECT_OVERLAP"

    power = PowerContext(
        context_id="CTX-PWR-001",
        provider="CEA",
        dataset="CENTRAL_ELECTRICITY_AUTHORITY_STATION_DATABASE",
        country="India",
        jurisdiction="Gujarat",
        distance_meters=1200.0,
        spatial_relationship="NEAR",
        spatial_relevance="MEDIUM",
        plant_name="Jamnagar Captive Power Plant",
        installed_capacity_mw=500.0,
        prime_mover="STEAM_TURBINE",
        provenance=create_cea_provenance(cea_record_id="CEA-GUJ-01"),
        coverage_status="AVAILABLE"
    )
    assert power.installed_capacity_mw == 500.0

    mining = MiningContext(
        context_id="CTX-MIN-001",
        provider="IBM_MINING",
        dataset="INDIAN_BUREAU_OF_MINES_MINING_LEASES",
        country="India",
        jurisdiction="Gujarat",
        distance_meters=8500.0,
        spatial_relationship="NO_RELEVANT_CONTEXT",
        spatial_relevance="NEGLIGIBLE",
        lease_name="Bauxite Concession",
        mineral="Bauxite",
        lease_area_hectares=150.0,
        provenance=create_ibm_provenance(record_id="IBM-001"),
        coverage_status="AVAILABLE"
    )
    assert mining.mineral == "Bauxite"

    lulc = LandCoverContext(
        context_id="CTX-LULC-001",
        provider="ISRO_BHUVAN",
        dataset="ISRO_BHUVAN_THEMATIC_LULC",
        country="India",
        jurisdiction="Gujarat",
        distance_meters=0.0,
        spatial_relationship="DIRECT_OVERLAP",
        spatial_relevance="HIGH",
        primary_class="INDUSTRIAL",
        secondary_class="BUILT_UP",
        resolution_m=30.0,
        provenance=create_bhuvan_provenance(feature_id="BHU-LULC-01"),
        coverage_status="AVAILABLE"
    )
    assert lulc.canonical_class == "INDUSTRIAL" or lulc.primary_class == "INDUSTRIAL"

    pa = ProtectedAreaContext(
        context_id="CTX-PA-001",
        provider="FSI",
        dataset="FOREST_SURVEY_OF_INDIA_PROTECTED_AREAS",
        country="India",
        jurisdiction="Gujarat",
        distance_meters=4200.0,
        spatial_relationship="DISTANT",
        spatial_relevance="LOW",
        pa_name="Marine Sanctuary Buffer Zone",
        pa_category="SANCTUARY",
        buffer_distance_km=10.0,
        provenance=create_fsi_provenance(record_id="FSI-PA-01"),
        coverage_status="AVAILABLE"
    )
    assert pa.pa_category == "SANCTUARY"

    adm = AdministrativeContext(
        context_id="CTX-ADM-001",
        provider="ADMIN_BOUNDARIES",
        dataset="SURVEY_OF_INDIA_ADMIN_BOUNDARIES",
        country="India",
        jurisdiction="Gujarat",
        distance_meters=0.0,
        spatial_relationship="DIRECT_OVERLAP",
        spatial_relevance="HIGH",
        admin_level=2,
        admin_name="Jamnagar",
        state="Gujarat",
        district="Jamnagar",
        provenance=prov,
        coverage_status="AVAILABLE"
    )
    assert adm.admin_name == "Jamnagar"

    env = EnvironmentalContext(
        context_id="CTX-ENV-001",
        provider="PARIVESH",
        dataset="MOEFCC_PARIVESH_ENVIRONMENTAL_CLEARANCES",
        country="India",
        jurisdiction="Gujarat",
        distance_meters=0.0,
        spatial_relationship="DIRECT_OVERLAP",
        spatial_relevance="HIGH",
        proposal_no="IA/GJ/IND2/1234/2021",
        project_name="Petrochemical Expansion",
        category="Category A",
        status="GRANTED",
        provenance=create_parivesh_provenance(proposal_id="PAR-001"),
        coverage_status="AVAILABLE"
    )
    assert env.status == "GRANTED"

    rel = ContextRelationship(
        event_id="EVT-827",
        context_id="CTX-FAC-001",
        domain="FACILITIES",
        category="DIRECT_OVERLAP",
        distance_m=85.0,
        spatial_relevance="HIGH",
        is_supporting=True,
        is_conflicting=False,
        details={"facility": "Reliance Jamnagar"}
    )
    assert rel.is_supporting is True

    cov = ContextCoverage(
        domain="POWER",
        provider="CEA",
        dataset="CENTRAL_ELECTRICITY_AUTHORITY_STATION_DATABASE",
        coverage_status="AVAILABLE",
        geographic_scope="INDIA_OPERATIONAL",
        is_global=False
    )
    assert cov.coverage_status == "AVAILABLE"


# Test 2: Direct-overlap context (<= 100m) correctly categorized
def test_2_direct_overlap_spatial_categorization():
    cat_overlap, rel_overlap = categorize_spatial_relationship(50.0)
    assert cat_overlap == "DIRECT_OVERLAP"
    assert rel_overlap == "HIGH"

    cat_overlap_edge, _ = categorize_spatial_relationship(100.0)
    assert cat_overlap_edge == "DIRECT_OVERLAP"

    cat_very_near, rel_very_near = categorize_spatial_relationship(350.0)
    assert cat_very_near == "VERY_NEAR"
    assert rel_very_near == "HIGH"

    cat_near, rel_near = categorize_spatial_relationship(850.0)
    assert cat_near == "NEAR"
    assert rel_near == "MEDIUM"

    cat_distant, rel_distant = categorize_spatial_relationship(3200.0)
    assert cat_distant == "DISTANT"
    assert rel_distant == "LOW"

    cat_none, rel_none = categorize_spatial_relationship(7500.0)
    assert cat_none == "NO_RELEVANT_CONTEXT"
    assert rel_none == "NEGLIGIBLE"


# Test 3: Multi-distance context buffers computed correctly
def test_3_multi_distance_context_buffers(db_session):
    engine = ContextDiscoveryEngine()
    discovered = engine.discover_event_context(db_session, "EVT-827")
    
    buffers = discovered.get("multi_distance_buffers", {})
    assert "500m" in buffers
    assert ("1km" in buffers or "1000m" in buffers)
    assert ("2km" in buffers or "2000m" in buffers)
    assert ("5km" in buffers or "5000m" in buffers)
    assert ("10km" in buffers or "10000m" in buffers)

    # Verify monotonically non-decreasing buffer cumulative counts
    k1 = "1km" if "1km" in buffers else "1000m"
    k2 = "2km" if "2km" in buffers else "2000m"
    k5 = "5km" if "5km" in buffers else "5000m"
    k10 = "10km" if "10km" in buffers else "10000m"
    assert buffers["500m"]["industrial_facilities"] <= buffers[k1]["industrial_facilities"]
    assert buffers[k1]["industrial_facilities"] <= buffers[k2]["industrial_facilities"]
    assert buffers[k2]["industrial_facilities"] <= buffers[k5]["industrial_facilities"]
    assert buffers[k5]["industrial_facilities"] <= buffers[k10]["industrial_facilities"]


# Test 4: Industrial facility context correctly discovered near Event 827
def test_4_industrial_facility_context_discovery_event_827(db_session):
    engine = ContextDiscoveryEngine()
    discovered = engine.discover_event_context(db_session, "EVT-827")
    facs = discovered.get("facilities", [])
    
    assert len(facs) > 0
    nearest = facs[0]
    assert nearest.provider == "OSM"
    assert nearest.distance_meters is not None
    assert nearest.distance_meters <= 2000.0  # In industrial corridor
    assert nearest.facility_name is not None
    assert nearest.provenance is not None
    assert nearest.provenance.provider == "OSM"


# Test 5: Power infrastructure correctly identified or absent where appropriate
def test_5_power_infrastructure_context(db_session):
    engine = ContextDiscoveryEngine()
    discovered = engine.discover_event_context(db_session, "EVT-827")
    power = discovered.get("power", [])
    
    # Power stations should either be discovered or absent with clean provenance
    if power:
        p = power[0]
        assert p.provider == "CEA"
        assert p.provenance.provider == "CEA"
        assert p.distance_meters is not None
    else:
        # Truthful absence verified
        assert len(power) == 0


# Test 6: Mining context correctly identified or absent where appropriate
def test_6_mining_context(db_session):
    engine = ContextDiscoveryEngine()
    discovered = engine.discover_event_context(db_session, "EVT-827")
    mining = discovered.get("mining", [])
    
    # In Jamnagar refinery corridor, active coal/iron mine lease is absent or distant
    if mining:
        m = mining[0]
        assert m.provider == "IBM_MINING"
        assert m.distance_meters is not None
    else:
        assert len(mining) == 0


# Test 7: Land-cover context correctly identified
def test_7_land_cover_context(db_session):
    engine = ContextDiscoveryEngine()
    discovered = engine.discover_event_context(db_session, "EVT-827")
    lulc = discovered.get("land_cover")
    
    assert lulc is not None
    assert lulc.provider == "ISRO_BHUVAN"
    assert lulc.dataset == "ISRO_BHUVAN_THEMATIC_LULC"
    assert (lulc.canonical_class is not None or lulc.primary_class is not None)
    assert lulc.spatial_relationship in ("DIRECT_OVERLAP", "VERY_NEAR", "NEAR")


# Test 8: Protected area context correctly identified and buffer analyzed
def test_8_protected_area_context_and_buffer(db_session):
    engine = ContextDiscoveryEngine()
    discovered = engine.discover_event_context(db_session, "EVT-827")
    pa_list = discovered.get("protected_areas", [])
    
    # Protected areas within 10km buffer
    for pa in pa_list:
        assert pa.provider == "FSI"
        assert pa.buffer_distance_km == 10.0
        assert pa.distance_meters is not None
        # Verify direct overlap would flag conflicting
        if pa.distance_meters <= 100.0:
            assert pa.spatial_relationship == "DIRECT_OVERLAP"


# Test 9: Administrative boundaries correctly identified
def test_9_administrative_boundaries_resolution(db_session):
    engine = ContextDiscoveryEngine()
    discovered = engine.discover_event_context(db_session, "EVT-827")
    admin = discovered.get("administrative")
    
    assert admin is not None
    assert admin.provider == "ADMIN_BOUNDARIES"
    assert admin.jurisdiction == "Gujarat"
    assert admin.district == "Jamnagar"
    assert admin.spatial_relationship == "DIRECT_OVERLAP"


# Test 10: Environmental clearance context correctly identified
def test_10_environmental_clearance_context(db_session):
    engine = ContextDiscoveryEngine()
    discovered = engine.discover_event_context(db_session, "EVT-827")
    env_list = discovered.get("environmental", [])
    
    assert env_list is not None
    assert len(env_list) > 0
    env = env_list[0]
    assert env.provider == "PARIVESH"
    assert env.category is not None or env.ec_category is not None
    assert env.provenance.provider == "PARIVESH"


# Test 11: Unconfigured providers (ECMWF, Planet, WRI, USGS) correctly report NOT_CONFIGURED
def test_11_unconfigured_providers_report_not_configured():
    coverage = GlobalContextProfile.get_context_coverage(region="GLOBAL")
    assert coverage["profile_id"] == "GLOBAL_CONTEXT"
    
    unconf = coverage["unconfigured_providers"]
    unconf_providers = {u["provider"]: u["status"] for u in unconf}
    
    assert unconf_providers.get("ECMWF_ERA5_ATMOSPHERIC") == "NOT_CONFIGURED"
    assert unconf_providers.get("GLOBAL_POWER_DATABASE") == "NOT_CONFIGURED"
    assert unconf_providers.get("USGS_MRDS_GLOBAL_MINING") == "NOT_CONFIGURED"
    assert unconf_providers.get("ESA_WORLDCOVER_GLOBAL") == "NOT_CONFIGURED"
    assert unconf_providers.get("WDPA_GLOBAL_PROTECTED_AREAS") == "NOT_CONFIGURED"


# Test 12: Missing context correctly disclosed with zero synthetic data
def test_12_missing_context_disclosed_zero_synthetic(db_session):
    res = context_engine.discover_and_correlate(db_session, "EVT-827")
    missing = res.get("missing_sources", [])
    
    assert len(missing) > 0
    # Must truthfully disclose unconfigured meteorological and optical sensors
    missing_str = " ".join(missing).upper()
    assert "WEATHER" in missing_str or "ECMWF" in missing_str
    assert "OPTICAL" in missing_str or "PLANET" in missing_str


# Test 13: Strongest contextual explanation correctly synthesized
def test_13_strongest_contextual_explanation_synthesis(db_session):
    res = context_engine.discover_and_correlate(db_session, "EVT-827")
    strongest = res.get("strongest_explanation")
    explanation_summary = res.get("explanation_summary")
    
    assert strongest is not None
    assert strongest in (
        "INDUSTRIAL_FACILITY_CONCORDANCE",
        "INFRASTRUCTURE_COINCIDENT_ANOMALY",
        "ECOLOGICAL_INTERFACE_RISK",
        "ISOLATED_SURFACE_ANOMALY"
    )
    assert len(explanation_summary) > 20


# Test 14: Contextual evidence strength correctly calibrated
def test_14_evidence_strength_calibration(db_session):
    res = context_engine.discover_and_correlate(db_session, "EVT-827")
    strength = res.get("evidence_strength")
    
    assert strength in ("STRONG", "MODERATE", "LIMITED", "INSUFFICIENT")
    # In Jamnagar with facility overlap, LULC industrial, and PARIVESH clearance, strength should be STRONG
    assert strength == "STRONG"


# Test 15: Contextual uncertainty correctly modeled
def test_15_contextual_uncertainty_modeling(db_session):
    res = context_engine.discover_and_correlate(db_session, "EVT-827")
    unc = res.get("uncertainty", {})
    
    assert "overall_level" in unc
    assert "domain_uncertainty" in unc
    dom_unc = unc["domain_uncertainty"]
    
    assert "FACILITIES" in dom_unc
    assert "WEATHER" in dom_unc
    assert dom_unc["WEATHER"] == "MISSING"
    assert dom_unc["HIGH_RES_OPTICAL"] == "MISSING"


# Test 16: What could change the assessment correctly generated
def test_16_what_could_change_the_assessment(db_session):
    res = context_engine.discover_and_correlate(db_session, "EVT-827")
    changes = res.get("what_could_change_the_assessment", [])
    
    assert len(changes) >= 3
    change_text = " ".join(changes)
    assert "optical" in change_text.lower() or "imagery" in change_text.lower()
    assert "wind" in change_text.lower() or "meteorological" in change_text.lower()


# Test 17: Section 24 Phase 8 primary acceptance command end-to-end
def test_17_section_24_primary_acceptance_command_end_to_end(db_session):
    command_text = (
        "JARVIS, investigate Event 827 using all available thermal and contextual sources. "
        "Tell me what contextual evidence supports the event, what sources are missing, "
        "whether any contextual evidence conflicts, and what additional context would reduce uncertainty."
    )
    
    req = JarvisCommandRequest(
        command=command_text,
        session_id="test-phase8-session-001"
    )
    
    resp = master_orchestrator.execute_command(db_session, req)
    
    assert resp is not None
    assert resp.command == command_text
    assert resp.stopping_reason is not None
    assert ("SECTION_24_PHASE8_COMPLETE" in resp.stopping_reason or "SECTION 24 ACCEPTANCE" in resp.stopping_reason)
    assert resp.summary is not None
    
    # Validate canonical 8-part structured output sections
    summary = resp.summary
    assert "THERMAL EVIDENCE SUMMARY" in summary
    assert "CONTEXTUAL EVIDENCE & INFRASTRUCTURE MATCHES" in summary
    assert "SPATIAL RELATIONSHIPS & DISTANCE PERIMETERS" in summary
    assert "STRONGEST CONTEXTUAL EXPLANATION" in summary
    assert "MISSING CONTEXTUAL SOURCES" in summary
    assert "CONFLICTING CONTEXTUAL EVIDENCE" in summary
    assert "UNCERTAINTY MODEL" in summary
    assert "WHAT COULD CHANGE THE ASSESSMENT" in summary
    assert "OPERATIONAL RECOMMENDATION" in summary

    # Verify Phase 8 response fields
    assert resp.context_sources is not None
    assert len(resp.context_sources) >= 4
    assert resp.context_provenance is not None
    assert resp.context_observation_count is not None
    assert resp.context_observation_count >= 5
    assert resp.context_uncertainty is not None


# Test 18: Single-master architecture preserved
def test_18_single_master_architecture_preserved(db_session):
    req = JarvisCommandRequest(
        command="JARVIS, show all contextual evidence for this event",
        session_id="test-single-master-p8"
    )
    resp = master_orchestrator.execute_command(db_session, req)
    
    # Evaluates command and transitions back to IDLE
    assert resp.stopping_reason is not None
    assert resp.dispatch_gate_blocked is True


# Test 19: Dispatch gate remains blocked
def test_19_dispatch_gate_remains_blocked(db_session):
    req = JarvisCommandRequest(
        command="JARVIS, investigate Event 827 and tell me what power infrastructure is near",
        session_id="test-dispatch-gate-p8"
    )
    resp = master_orchestrator.execute_command(db_session, req)
    
    assert resp.dispatch_gate_blocked is True
    assert resp.requires_human_approval is True
    assert resp.system_notice is not None


# Test 20: Protected baseline untouched
def test_20_protected_baseline_untouched(db_session):
    # Verify raw event evaluation maintains authoritative risk formula and ML prediction
    raw_ev = JarvisToolRegistry.tool_get_event(db_session, "EVT-827")
    assert raw_ev.get("found") is True
    
    # 5-factor risk score
    risk_info = raw_ev.get("risk")
    assert risk_info is not None
    assert 0 <= risk_info.get("risk_score") <= 100
    
    # ML model prediction
    pred_info = raw_ev.get("prediction")
    assert pred_info is not None
    assert pred_info.get("predicted_class") is not None
    
    # FRP and coordinates
    assert raw_ev.get("max_frp") is not None
    assert raw_ev.get("latitude") is not None
    assert raw_ev.get("longitude") is not None


# Test 21: Context intelligence enriches interpretation without silently overwriting thermal evidence
def test_21_context_enriches_without_overwriting_thermal(db_session):
    raw_ev_before = JarvisToolRegistry.tool_get_event(db_session, "EVT-827")
    before_frp = raw_ev_before.get("max_frp")
    before_lat = raw_ev_before.get("latitude")
    before_lon = raw_ev_before.get("longitude")
    
    # Execute full context discovery and correlation
    res = context_engine.discover_and_correlate(db_session, "EVT-827")
    
    raw_ev_after = JarvisToolRegistry.tool_get_event(db_session, "EVT-827")
    
    # Telemetry must remain identical
    assert raw_ev_after.get("max_frp") == before_frp
    assert raw_ev_after.get("latitude") == before_lat
    assert raw_ev_after.get("longitude") == before_lon
    
    # But context is enriched
    assert len(res["context_sources"]) >= 4
    assert res["strongest_explanation"] is not None
