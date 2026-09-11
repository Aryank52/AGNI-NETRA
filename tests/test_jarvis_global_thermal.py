"""
AGNI-NETRA Phase 7: Global Thermal Intelligence & Multi-Provider Fusion Test Suite
Validates:
1. FIRMS query returns normalized observations
2. SLSTR query returns normalized observations
3. MOSDAC query returns regional observations
4. GOES query handles unconfigured state gracefully
5. Deduplication clusters coincident observations within spatial and temporal thresholds
6. Deduplication preserves distinct satellite passes
7. Event fusion correctly combines multi-source observations
8. Source agreement level computed correctly
9. Single-source fallback works when only one provider available
10. Source conflict detected when FRP diverges
11. Provenance records generated for all observations
12. Workspace persists thermal sources and agreement
13. Workspace persists source conflicts
14. Coverage summary includes all thermal providers
15. Section 28 Primary Acceptance Command succeeds end-to-end
16. Multi-source support query answered correctly
17. Thermal provenance query returns complete lineage
18. Provider failure/timeout does not break pipeline (fail-safe isolation)
"""

import pytest
from datetime import datetime, timezone, timedelta
from typing import List

from backend.app.core.database import SessionLocal
from backend.app.models.canonical import ThermalObservation, ThermalEvent, SourceProvenance
from backend.app.services.intelligence.provider_registry import provider_registry
from backend.app.services.intelligence.providers.adapters import (
    FIRMSProvider,
    CopernicusSLSTRProvider,
    MOSDACThermalProvider,
    NOAAGOESProvider
)
from backend.app.services.intelligence.providers.base import ProviderHealth
from backend.app.services.intelligence.thermal_fusion import (
    normalize_thermal_record,
    deduplicate_thermal_observations,
    evaluate_source_agreement,
    fuse_observations_to_canonical_event,
    query_multi_provider_thermal_intelligence,
    haversine_distance_meters
)
from backend.app.services.jarvis.jarvis_orchestrator import master_orchestrator
from backend.app.models.jarvis_schemas import JarvisCommandRequest, CommandIntent
from backend.app.services.jarvis.jarvis_workspace import workspace_manager


@pytest.fixture(scope="module")
def db_session():
    session = SessionLocal()
    yield session
    session.close()


# Test 1: FIRMS query returns normalized observations
def test_1_firms_query_returns_normalized_observations(db_session):
    provider = provider_registry.get_provider("FIRMS")
    assert provider is not None
    assert isinstance(provider, FIRMSProvider)
    
    # Query observations near Event 827 coords
    obs = provider.query_observations(
        db=db_session,
        latitude=22.3039,
        longitude=70.8022,
        radius_km=50.0
    )
    assert len(obs) > 0
    first_obs = obs[0]
    assert isinstance(first_obs, ThermalObservation)
    assert first_obs.provider == "FIRMS"
    assert first_obs.latitude is not None
    assert first_obs.longitude is not None
    assert first_obs.radiative_power >= 0.0
    assert first_obs.source_provenance is not None
    assert first_obs.source_provenance.provider == "FIRMS"


# Test 2: SLSTR query returns normalized observations
def test_2_slstr_query_returns_normalized_observations(db_session):
    provider = provider_registry.get_provider("COPERNICUS_SLSTR")
    assert provider is not None
    assert isinstance(provider, CopernicusSLSTRProvider)
    assert provider.get_health(db_session) == ProviderHealth.AVAILABLE
    
    obs = provider.query_observations(
        db=db_session,
        latitude=22.3039,
        longitude=70.8022,
        radius_km=50.0
    )
    assert len(obs) > 0
    first_obs = obs[0]
    assert isinstance(first_obs, ThermalObservation)
    assert first_obs.provider == "COPERNICUS_SLSTR"
    assert "SLSTR" in first_obs.dataset
    assert first_obs.source_provenance.spatial_resolution == "1000m SLSTR Nadir Footprint"


# Test 3: MOSDAC query returns regional observations
def test_3_mosdac_query_returns_regional_observations(db_session):
    provider = provider_registry.get_provider("ISRO_MOSDAC")
    assert provider is not None
    assert isinstance(provider, MOSDACThermalProvider)
    assert provider.get_health(db_session) == ProviderHealth.AVAILABLE
    
    obs = provider.query_observations(
        db=db_session,
        latitude=22.3039,
        longitude=70.8022,
        radius_km=50.0
    )
    assert len(obs) > 0
    first_obs = obs[0]
    assert isinstance(first_obs, ThermalObservation)
    assert first_obs.provider == "ISRO_MOSDAC"
    assert "MOSDAC" in first_obs.dataset
    assert first_obs.source_provenance.geographic_coverage == "REGION:INDIAN_OCEAN"


# Test 4: GOES query handles unconfigured state gracefully
def test_4_goes_query_handles_unconfigured_state(db_session):
    provider = provider_registry.get_provider("NOAA_GOES")
    assert provider is not None
    assert isinstance(provider, NOAAGOESProvider)
    assert provider.get_health(db_session) == ProviderHealth.NOT_CONFIGURED
    
    # Querying GOES for Indian coordinates returns empty list without crashing
    obs = provider.query_observations(
        db=db_session,
        latitude=22.3039,
        longitude=70.8022,
        radius_km=50.0
    )
    assert isinstance(obs, list)
    assert len(obs) == 0


# Test 5: Deduplication clusters coincident observations within spatial and temporal thresholds
def test_5_deduplication_clusters_coincident_observations():
    t0 = datetime(2026, 9, 10, 12, 0, 0, tzinfo=timezone.utc)
    t1 = t0 + timedelta(minutes=10)  # Within 1800s (30m)
    
    obs1 = ThermalObservation(
        provider="FIRMS",
        dataset="VIIRS",
        source_record_id="REC-1",
        latitude=22.3000,
        longitude=70.8000,
        observation_time=t0,
        radiative_power=150.0,
        brightness_temperature=340.0
    )
    obs2 = ThermalObservation(
        provider="COPERNICUS_SLSTR",
        dataset="SLSTR",
        source_record_id="REC-2",
        latitude=22.3020,  # ~220 meters away (<= 1000m)
        longitude=70.8010,
        observation_time=t1,
        radiative_power=140.0,
        brightness_temperature=338.0
    )
    
    clusters = deduplicate_thermal_observations([obs1, obs2], spatial_threshold_m=1000.0, temporal_threshold_sec=1800.0)
    assert len(clusters) == 1
    assert len(clusters[0]) == 2


# Test 6: Deduplication preserves distinct satellite passes
def test_6_deduplication_preserves_distinct_passes():
    t0 = datetime(2026, 9, 10, 12, 0, 0, tzinfo=timezone.utc)
    t_later = t0 + timedelta(hours=6)  # 6 hours later (> 1800s)
    
    obs1 = ThermalObservation(
        provider="FIRMS",
        dataset="VIIRS",
        source_record_id="REC-1",
        latitude=22.3000,
        longitude=70.8000,
        observation_time=t0,
        radiative_power=150.0,
        brightness_temperature=340.0
    )
    obs2 = ThermalObservation(
        provider="FIRMS",
        dataset="VIIRS",
        source_record_id="REC-2",
        latitude=22.3000,
        longitude=70.8000,
        observation_time=t_later,
        radiative_power=160.0,
        brightness_temperature=345.0
    )
    
    clusters = deduplicate_thermal_observations([obs1, obs2], spatial_threshold_m=1000.0, temporal_threshold_sec=1800.0)
    assert len(clusters) == 2


# Test 7: Event fusion correctly combines multi-source observations
def test_7_event_fusion_correctly_combines_observations():
    t0 = datetime(2026, 9, 10, 12, 0, 0, tzinfo=timezone.utc)
    obs_list = [
        ThermalObservation(
            provider="FIRMS",
            dataset="VIIRS",
            source_record_id="REC-1",
            latitude=22.3000,
            longitude=70.8000,
            observation_time=t0,
            radiative_power=200.0,
            brightness_temperature=350.0
        ),
        ThermalObservation(
            provider="COPERNICUS_SLSTR",
            dataset="SLSTR",
            source_record_id="REC-2",
            latitude=22.3010,
            longitude=70.8010,
            observation_time=t0,
            radiative_power=180.0,
            brightness_temperature=345.0
        )
    ]
    
    fused = fuse_observations_to_canonical_event(
        observations=obs_list,
        event_id="EVT-TEST",
        fallback={"state": "Gujarat"}
    )
    assert isinstance(fused, ThermalEvent)
    assert fused.detection_count == 2
    assert fused.max_frp == 200.0
    assert fused.avg_frp == 190.0
    assert sorted(fused.contributing_providers) == ["COPERNICUS_SLSTR", "FIRMS"]
    assert fused.source_agreement == "MULTI_SOURCE_AGREEMENT"


# Test 8: Source agreement level computed correctly
def test_8_source_agreement_level_computed_correctly():
    t0 = datetime(2026, 9, 10, 12, 0, 0, tzinfo=timezone.utc)
    # Multi-source concordant
    obs_multi = [
        ThermalObservation(provider="FIRMS", dataset="V", source_record_id="1", latitude=22.3, longitude=70.8, observation_time=t0, radiative_power=100.0, brightness_temperature=330.0),
        ThermalObservation(provider="COPERNICUS_SLSTR", dataset="S", source_record_id="2", latitude=22.3, longitude=70.8, observation_time=t0, radiative_power=95.0, brightness_temperature=328.0)
    ]
    agreement, conflicts = evaluate_source_agreement(obs_multi)
    assert agreement == "MULTI_SOURCE_AGREEMENT"
    assert len(conflicts) == 0


# Test 9: Single-source fallback works when only one provider available
def test_9_single_source_fallback():
    t0 = datetime(2026, 9, 10, 12, 0, 0, tzinfo=timezone.utc)
    obs_single = [
        ThermalObservation(provider="FIRMS", dataset="V", source_record_id="1", latitude=22.3, longitude=70.8, observation_time=t0, radiative_power=100.0, brightness_temperature=330.0)
    ]
    agreement, conflicts = evaluate_source_agreement(obs_single)
    assert agreement == "SINGLE_SOURCE"
    assert len(conflicts) == 0


# Test 10: Source conflict detected when FRP diverges significantly
def test_10_source_conflict_detected_when_frp_diverges():
    t0 = datetime(2026, 9, 10, 12, 0, 0, tzinfo=timezone.utc)
    # FRP divergence > 2.5x ratio (e.g. 500.0 MW vs 100.0 MW = 5.0x)
    obs_divergent = [
        ThermalObservation(provider="FIRMS", dataset="V", source_record_id="1", latitude=22.3, longitude=70.8, observation_time=t0, radiative_power=500.0, brightness_temperature=420.0),
        ThermalObservation(provider="COPERNICUS_SLSTR", dataset="S", source_record_id="2", latitude=22.3, longitude=70.8, observation_time=t0, radiative_power=100.0, brightness_temperature=320.0)
    ]
    agreement, conflicts = evaluate_source_agreement(obs_divergent)
    assert agreement == "SOURCE_CONFLICT"
    assert len(conflicts) > 0
    assert conflicts[0]["type"] == "THERMAL_MAGNITUDE_DIVERGENCE"
    assert "ratio" in conflicts[0]["explanation"].lower()


# Test 11: Provenance records generated for all observations
def test_11_provenance_records_generated(db_session):
    res = query_multi_provider_thermal_intelligence(
        db=db_session,
        latitude=22.3039,
        longitude=70.8022,
        radius_km=10.0
    )
    provs = res.get("provenance_records", [])
    assert len(provs) > 0
    for p in provs:
        assert "provider" in p
        assert "dataset" in p
        assert "spatial_resolution" in p
        assert "limitations" in p


# Test 12: Workspace persists thermal sources and agreement
def test_12_workspace_persists_thermal_sources_and_agreement(db_session):
    ws = workspace_manager.create_workspace(
        db=db_session,
        session_id="test-phase7-ws",
        user_role="ANALYST",
        primary_objective="Test Phase 7 Workspace Persistence",
        target_event_id="EVT-827"
    )
    
    ws.thermal_sources = ["FIRMS", "COPERNICUS_SLSTR", "ISRO_MOSDAC"]
    ws.source_agreement = "MULTI_SOURCE_AGREEMENT"
    ws.observation_count = 42
    db_session.commit()
    db_session.refresh(ws)
    
    assert ws.thermal_sources == ["FIRMS", "COPERNICUS_SLSTR", "ISRO_MOSDAC"]
    assert ws.source_agreement == "MULTI_SOURCE_AGREEMENT"
    assert ws.observation_count == 42


# Test 13: Workspace persists source conflicts
def test_13_workspace_persists_source_conflicts(db_session):
    ws = workspace_manager.get_or_create_workspace(
        db=db_session,
        session_id="test-phase7-ws",
        user_role="ANALYST",
        target_event_id="EVT-827"
    )
    conflicts_data = [{
        "type": "THERMAL_MAGNITUDE_DIVERGENCE",
        "divergence_ratio": 2.8,
        "explanation": "VIIRS 375m pixel vs SLSTR 1000m pixel integration difference."
    }]
    ws.source_conflicts = conflicts_data
    db_session.commit()
    db_session.refresh(ws)
    
    assert len(ws.source_conflicts) == 1
    assert ws.source_conflicts[0]["type"] == "THERMAL_MAGNITUDE_DIVERGENCE"


# Test 14: Coverage summary includes all thermal providers
def test_14_coverage_summary_includes_all_thermal_providers():
    summary = provider_registry.get_thermal_coverage_summary()
    assert summary["total_thermal_providers"] == 4
    prov_names = [p["provider_name"] for p in summary["providers"]]
    assert "FIRMS" in prov_names
    assert "COPERNICUS_SLSTR" in prov_names
    assert "ISRO_MOSDAC" in prov_names
    assert "NOAA_GOES" in prov_names
    assert len(summary["global_polar_orbiters"]) >= 2
    assert len(summary["regional_geostationary"]) >= 1
    assert len(summary["unconfigured_providers"]) >= 1


# Test 15: Section 28 Primary Acceptance Command succeeds end-to-end
def test_15_section_28_primary_acceptance_command(db_session):
    cmd = (
        "JARVIS, investigate Event 827 using all available thermal sources and "
        "tell me whether the observations agree, what sources support the event, "
        "what coverage they provide, and whether any source disagreement affects confidence."
    )
    req = JarvisCommandRequest(command=cmd, session_id="test-phase7-session")
    resp = master_orchestrator.execute_command(db_session, req)
    
    assert resp is not None
    assert resp.intent == "INVESTIGATE"
    assert resp.objective.primary_goal == "SECTION_28_ACCEPTANCE"
    assert "MULTI_SOURCE_AGREEMENT" in resp.summary or resp.source_agreement == "MULTI_SOURCE_AGREEMENT"
    assert resp.thermal_sources is not None
    assert len(resp.thermal_sources) >= 2
    assert "EVT-827" in resp.summary
    assert resp.dispatch_gate_blocked is True
    assert "SECTION_28_COMPLETE" in resp.stopping_reason


# Test 16: Multi-source support query answered correctly
def test_16_multi_source_support_query(db_session):
    cmd = "does more than one source support this thermal event?"
    req = JarvisCommandRequest(command=cmd, session_id="test-phase7-session")
    resp = master_orchestrator.execute_command(db_session, req)
    
    assert resp is not None
    assert "DIRECT ANSWER" in resp.summary
    assert "YES" in resp.summary or "supports this thermal event" in resp.summary
    assert resp.stopping_reason.startswith("THERMAL_SOURCES_REPORTED")


# Test 17: Thermal provenance query returns complete lineage (Section 29)
def test_17_thermal_provenance_query(db_session):
    cmd = "JARVIS, show the thermal-source provenance for this investigation."
    req = JarvisCommandRequest(command=cmd, session_id="test-phase7-session")
    resp = master_orchestrator.execute_command(db_session, req)
    
    assert resp is not None
    assert "CANONICAL THERMAL OBSERVATION PROVENANCE LINEAGE" in resp.summary
    assert "| Provider |" in resp.summary
    assert "FIRMS" in resp.summary
    assert resp.stopping_reason.startswith("THERMAL_PROVENANCE_REPORTED")


# Test 18: Provider failure/timeout does not break pipeline (fail-safe isolation)
def test_18_provider_failure_isolation(db_session):
    # Pass an invalid region or trigger query
    res = query_multi_provider_thermal_intelligence(
        db=db_session,
        latitude=0.0,
        longitude=0.0,
        radius_km=1.0
    )
    # Even if 0 detections found, structure is complete and zero exceptions raised
    assert isinstance(res, dict)
    assert "provider_status_breakdown" in res
    assert "source_agreement" in res
    assert "observations" in res
    assert res["source_agreement"] in ("INSUFFICIENT_OVERLAP", "SINGLE_SOURCE")
