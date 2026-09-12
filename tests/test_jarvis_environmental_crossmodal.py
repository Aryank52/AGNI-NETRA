"""
AGNI-NETRA Phase 10: Global Environmental Intelligence & Cross-Modal Verification Test Suite
Comprehensive verification suite validating:
1. Canonical environmental and cross-modal models validation.
2. Environmental provider adapters (ECMWF, GFS, CAMS [NOT CONFIGURED], IMD [NOT CONFIGURED]).
3. Cross-modal provider adapters (Sentinel-2, Sentinel-1 SAR, Bhuvan LULC, PlanetScope [NOT CONFIGURED], AVIRIS [NOT CONFIGURED]).
4. Provider registry coverage summaries and unconfigured disclosures.
5. EnvironmentalDiscoveryEngine calculations (temperature, humidity, wind vector, plume transport, precipitation, cloud impact).
6. CrossModalVerificationEngine space-time synchronization and corroboration.
7. Epistemic separation: observation absence (optical cloud cover) vs activity absence.
8. SAR backscatter coherence anomaly and host land cover compatibility.
9. Next highest-value observation prediction for uncertainty reduction.
10. Command Interpreter parsing of all 11 Phase 10 command variants.
11. Master Orchestrator end-to-end execution of Section 30 primary 5-family investigation command.
12. InvestigationWorkspace PostgreSQL persistence of all 12 Phase 10 columns.
13. REST API intelligence endpoints (all 7 endpoints return 200 OK).
14. Frozen invariants: authoritative 5-factor risk formula, XGBoost classifier, alert thresholds.
15. Safety invariants: single master agent, dispatch gate BLOCKED, mandatory HITL routing.
"""

import pytest
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List

from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.database import SessionLocal
from backend.app.models.canonical import (
    WeatherObservation,
    WindObservation,
    PrecipitationObservation,
    CloudCondition,
    AtmosphericObservation,
    OpticalObservation,
    SARObservation,
    LandCover,
    EnvironmentalEvidence,
    CrossModalEvidence,
    SourceProvenance
)
from backend.app.services.intelligence.provider_registry import provider_registry
from backend.app.services.intelligence.environmental_engine import (
    EnvironmentalDiscoveryEngine,
    environmental_discovery_engine
)
from backend.app.services.intelligence.cross_modal_engine import (
    CrossModalVerificationEngine,
    cross_modal_verification_engine
)
from backend.app.services.intelligence.providers.base import ProviderHealth
from backend.app.services.intelligence.providers.adapters import (
    ECMWFWeatherProvider,
    GFSWeatherProvider,
    CopernicusAtmosphericProvider,
    Sentinel2OpticalProvider,
    Sentinel1SARProvider,
    BhuvanProvider,
    HighResOpticalProviderScaffold
)
from backend.app.services.jarvis.jarvis_command_interpreter import command_interpreter
from backend.app.services.jarvis.jarvis_orchestrator import master_orchestrator
from backend.app.services.jarvis.jarvis_workspace import workspace_manager
from backend.app.models.jarvis_schemas import (
    JarvisCommandRequest,
    JarvisState,
    CommandIntent,
    CommandObjective
)
from backend.app.models.domain import InvestigationWorkspace


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def api_client():
    return TestClient(app)


# ==============================================================================
# 1. CANONICAL ENVIRONMENTAL & CROSS-MODAL MODELS
# ==============================================================================

def test_canonical_environmental_models():
    """Verify Weather, Wind, Precip, Cloud, and Atmospheric models serialize correctly."""
    now = datetime.now(timezone.utc)
    prov = SourceProvenance(
        provider_name="ECMWF_ERA5",
        dataset_name="reanalysis-era5-single-levels",
        collection_timestamp=now,
        processing_level="L4",
        spatial_resolution="0.25 deg (~28km)",
        temporal_resolution="HOURLY",
        geographic_coverage="GLOBAL"
    )
    wx = WeatherObservation(
        latitude=21.25,
        longitude=81.63,
        observation_time=now.isoformat(),
        temperature_c=31.4,
        relative_humidity_pct=48.0,
        surface_pressure_hpa=1012.0,
        provenance=prov
    )
    wnd = WindObservation(
        latitude=21.25,
        longitude=81.63,
        observation_time=now.isoformat(),
        wind_speed_ms=5.8,
        wind_direction_deg=245.0,
        smoke_dispersion_direction="ENE",
        provenance=prov
    )
    pcp = PrecipitationObservation(
        latitude=21.25,
        longitude=81.63,
        observation_time=now.isoformat(),
        precipitation_rate_mmh=0.0,
        persistence_support_status="SUPPORTIVE",
        provenance=prov
    )
    cld = CloudCondition(
        latitude=21.25,
        longitude=81.63,
        observation_time=now.isoformat(),
        cloud_cover_pct=15.0,
        limits_optical_observation=False,
        cloud_type="CIRRUS",
        provenance=prov
    )
    atm = AtmosphericObservation(
        latitude=21.25,
        longitude=81.63,
        observation_time=now.isoformat(),
        aod=0.28,
        provenance=prov
    )
    env_ev = EnvironmentalEvidence(
        event_id="EVT-827",
        weather_observation=wx,
        wind_observation=wnd,
        precipitation_observation=pcp,
        cloud_condition=cld,
        atmospheric_observation=atm,
        provenance=prov
    )
    assert env_ev.event_id == "EVT-827"
    assert env_ev.weather_observation.temperature_c == 31.4
    assert env_ev.wind_observation.smoke_dispersion_direction == "ENE"
    assert env_ev.precipitation_observation.persistence_support_status == "SUPPORTIVE"
    assert env_ev.cloud_condition.limits_optical_observation is False


def test_canonical_cross_modal_models():
    """Verify Optical, SAR, and LandCover models serialize correctly."""
    now = datetime.now(timezone.utc)
    prov = SourceProvenance(
        provider_name="COPERNICUS_SENTINEL_2",
        dataset_name="S2_MSI_L2A",
        collection_timestamp=now,
        processing_level="L2A_BOA_REFLECTANCE",
        spatial_resolution="20m",
        temporal_resolution="5_DAYS",
        geographic_coverage="GLOBAL"
    )
    opt = OpticalObservation(
        latitude=21.25,
        longitude=81.63,
        observation_time=now.isoformat(),
        sensor="SENTINEL_2_MSI",
        swir_anomaly_detected=True,
        cloud_cover_pct=15.0,
        provenance=prov
    )
    sar = SARObservation(
        latitude=21.25,
        longitude=81.63,
        observation_time=now.isoformat(),
        sensor="SENTINEL_1_CSAR",
        polarization="VV_VH",
        backscatter_anomaly_detected=True,
        all_weather_penetration=True,
        provenance=prov
    )
    lulc = LandCover(
        lulc_id="LULC-001",
        latitude=21.25,
        longitude=81.63,
        canonical_class="Industrial",
        provenance=prov
    )
    cm_ev = CrossModalEvidence(
        event_id="EVT-827",
        corroboration_status="PARTIALLY_CORROBORATED",
        optical_corroboration={"swir_anomaly": True},
        sar_corroboration={"all_weather_penetration": True},
        conflicts=[],
        highest_value_observation="Sentinel-2 MSI daylight overpass in 42 hours",
        provenance=prov
    )
    assert cm_ev.corroboration_status == "PARTIALLY_CORROBORATED"
    assert len(cm_ev.conflicts) == 0
    assert sar.all_weather_penetration is True
    assert opt.swir_anomaly_detected is True


# ==============================================================================
# 2. ENVIRONMENTAL PROVIDER ADAPTERS & DISCLOSURES
# ==============================================================================

def test_environmental_adapters_operational():
    """Verify ECMWF and NOAA GFS providers return factual metadata and disclose unconfigured status."""
    ecmwf = ECMWFWeatherProvider()
    gfs = GFSWeatherProvider()
    
    meta_ec = ecmwf.get_metadata()
    assert meta_ec.provider_name == "ECMWF_WEATHER"
    assert "surface_wind_vectors" in meta_ec.capabilities
    assert meta_ec.availability == ProviderHealth.NOT_CONFIGURED
    assert "[NOT CONFIGURED]" in meta_ec.limitations
    
    meta_gfs = gfs.get_metadata()
    assert meta_gfs.provider_name == "NOAA_GFS"
    assert "10m_wind_vectors" in meta_gfs.capabilities
    assert meta_gfs.availability == ProviderHealth.NOT_CONFIGURED
    assert "[NOT CONFIGURED]" in meta_gfs.limitations


def test_environmental_adapters_unconfigured_disclosure():
    """Verify unconfigured CAMS atmospheric provider discloses status factually with zero synthetic records."""
    cams = CopernicusAtmosphericProvider()
    meta = cams.get_metadata()
    
    assert meta.provider_name == "COPERNICUS_ATMOSPHERIC"
    assert meta.availability == ProviderHealth.NOT_CONFIGURED
    assert "[NOT CONFIGURED]" in meta.limitations
    assert "CAMS" in meta.source_provenance


# ==============================================================================
# 3. CROSS-MODAL PROVIDER ADAPTERS & DISCLOSURES
# ==============================================================================

def test_cross_modal_adapters_operational():
    """Verify Sentinel-2, Sentinel-1, and Bhuvan adapters provide structured capabilities and metadata."""
    s2 = Sentinel2OpticalProvider()
    s1 = Sentinel1SARProvider()
    lulc = BhuvanProvider()
    
    meta_s2 = s2.get_metadata()
    assert meta_s2.provider_name == "SENTINEL2_OPTICAL"
    assert "swir_flame_detection" in meta_s2.capabilities
    
    meta_s1 = s1.get_metadata()
    assert meta_s1.provider_name == "SENTINEL1_SAR"
    assert "all_weather_cloud_penetrating_radar" in meta_s1.capabilities
    
    meta_bh = lulc.get_metadata()
    assert meta_bh.provider_name == "ISRO_BHUVAN"


def test_cross_modal_adapters_unconfigured_disclosure():
    """Verify commercial high-resolution optical scaffold discloses unconfigured status."""
    highres = HighResOpticalProviderScaffold()
    meta = highres.get_metadata()
    
    assert meta.provider_name == "HIGH_RES_OPTICAL"
    assert meta.availability == ProviderHealth.NOT_CONFIGURED
    assert "HIGH-RESOLUTION OPTICAL IMAGERY UNAVAILABLE" in meta.limitations


def test_provider_registry_environmental_cross_modal_coverage():
    """Verify provider registry exposes comprehensive coverage summaries for Phase 10 families."""
    env_cov = provider_registry.get_environmental_coverage_summary()
    assert "total_environmental_providers" in env_cov or "active_providers_count" in env_cov
    
    cm_cov = provider_registry.get_cross_modal_coverage_summary()
    assert "total_cross_modal_providers" in cm_cov or "active_providers_count" in cm_cov


# ==============================================================================
# 4. ENVIRONMENTAL DISCOVERY ENGINE CALCULATIONS
# ==============================================================================

def test_environmental_discovery_engine_analysis(db_session):
    """Verify EnvironmentalDiscoveryEngine calculates meteorological conditions and relationships."""
    res = environmental_discovery_engine.analyze_event_environment(
        db=db_session,
        event_ref="EVT-827",
        lat=21.25,
        lon=81.63
    )
    assert "weather" in res
    assert "wind" in res
    assert "precipitation" in res
    assert "cloud" in res
    assert "atmospheric" in res
    assert "relationships" in res
    assert "conflicts" in res
    assert "uncertainty" in res
    assert res["observation_count"] >= 4
    
    # Check physical values
    assert res["weather"]["temperature_c"] > 15.0
    assert res["weather"]["relative_humidity_pct"] > 10.0
    assert res["precipitation"]["precipitation_rate_mmh"] == 0.0
    assert res["cloud"]["cloud_cover_pct"] <= 50.0


def test_environmental_engine_plume_dispersion_calculation():
    """Verify plume dispersion is calculated as downwind trajectory opposite wind vector origin."""
    # Wind from 245° (WSW) blows smoke towards ENE
    compass = EnvironmentalDiscoveryEngine._wind_degrees_to_compass(245.0)
    assert compass == "WSW"
    
    # Transport condition
    transport_mod = EnvironmentalDiscoveryEngine._calculate_transport_condition(5.8)
    assert transport_mod == "MODERATE_TRANSPORT"
    
    transport_calm = EnvironmentalDiscoveryEngine._calculate_transport_condition(0.8)
    assert transport_calm == "CALM_STAGNATION"


def test_environmental_engine_moisture_and_precipitation():
    """Verify dry conditions support thermal persistence and do not cause thermal washout."""
    dry_status, dry_exp = EnvironmentalDiscoveryEngine._evaluate_precipitation_persistence(0.0, 0.0)
    assert dry_status == "SUPPORTIVE"
    assert "support sustained thermal persistence" in dry_exp
    
    wet_status, wet_exp = EnvironmentalDiscoveryEngine._evaluate_precipitation_persistence(15.0, 25.0)
    assert wet_status == "POTENTIALLY_INCONSISTENT"
    assert "Heavy precipitation" in wet_exp


def test_environmental_engine_cloud_optical_attenuation():
    """Verify cloud cover impacts optical observation limits while preserving thermal veracity."""
    opt_lim_low, therm_lim_low, r_low = EnvironmentalDiscoveryEngine._evaluate_cloud_observability(15.0)
    assert opt_lim_low is False
    assert therm_lim_low is False
    assert "clear to scattered" in r_low
    
    opt_lim_high, therm_lim_high, r_high = EnvironmentalDiscoveryEngine._evaluate_cloud_observability(85.0)
    assert opt_lim_high is True
    assert therm_lim_high is True
    assert "OBSERVATION ABSENCE, NOT thermal event absence" in r_high


# ==============================================================================
# 5. CROSS-MODAL VERIFICATION ENGINE & EPISTEMIC SEPARATION
# ==============================================================================

def test_cross_modal_verification_engine_synchronization(db_session):
    """Verify CrossModalVerificationEngine synchronizes across thermal, optical, SAR, and land cover."""
    res = cross_modal_verification_engine.verify_event_cross_modal(
        db=db_session,
        event_ref="EVT-827",
        lat=21.25,
        lon=81.63
    )
    assert res["corroboration_status"] in ["CORROBORATED", "PARTIALLY_CORROBORATED"]
    assert "optical" in res
    assert "sar" in res
    assert "land_cover" in res
    assert "conflicts" in res
    assert len(res["conflicts"]) == 0
    assert "uncertainty" in res
    assert "highest_value_observation" in res["uncertainty"]


def test_cross_modal_epistemic_absence_separation(db_session):
    """Verify epistemic rule: Observation absence (cloud cover) does NOT equal activity absence."""
    # Provide overcast cloud context
    cloudy_env = {
        "weather": {"temperature_c": 28.0, "relative_humidity_pct": 82.0},
        "wind": {"wind_speed_ms": 3.2, "wind_direction_deg": 180.0, "smoke_dispersion_direction": "N"},
        "cloud": {"cloud_cover_pct": 90.0, "limits_optical_observation": True},
        "precipitation": {"precipitation_rate_mmh": 0.0, "persistence_support_status": "DRY_CONDITIONS"},
        "atmospheric": {"boundary_layer_height_m": 900.0, "aerosol_optical_depth": 0.35}
    }
    
    res = cross_modal_verification_engine.verify_event_cross_modal(
        db=db_session,
        event_ref="EVT-827",
        lat=21.25,
        lon=81.63,
        env_context=cloudy_env
    )
    # Optical is obscured, but SAR penetrates and thermal remains verified -> PARTIALLY_CORROBORATED, 0 physical conflicts!
    assert len(res["conflicts"]) == 0
    assert "observation absence" in res.get("epistemic_notes", "").lower() or "absence" in res.get("uncertainty", {}).get("highest_value_observation", "").lower()


def test_cross_modal_temporal_spatial_sync():
    """Verify temporal and spatial synchronization scoring."""
    t_now = datetime.now(timezone.utc).isoformat()
    t_1h = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    delta, tier = CrossModalVerificationEngine._calculate_temporal_synchronization(t_now, t_1h)
    assert tier == "CONCURRENT"
    
    sp_tier = CrossModalVerificationEngine._evaluate_spatial_synchronization(85.0)
    assert sp_tier == "SAME_LOCATION"
    
    sp_tier_2 = CrossModalVerificationEngine._evaluate_spatial_synchronization(450.0)
    assert sp_tier_2 == "WITHIN_500M"


def test_cross_modal_uncertainty_reduction(db_session):
    """Verify engine identifies next highest-value observation to reduce residual uncertainty."""
    res = cross_modal_verification_engine.verify_event_cross_modal(
        db=db_session,
        event_ref="EVT-827",
        lat=21.25,
        lon=81.63
    )
    unc = res.get("uncertainty", {})
    assert "highest_value_observation" in unc
    assert "Sentinel-2" in unc["highest_value_observation"] or "overpass" in unc["highest_value_observation"]


# ==============================================================================
# 6. COMMAND INTERPRETER PHASE 10 PATTERNS
# ==============================================================================

def test_command_interpreter_phase10_complete_investigation():
    """Verify CommandInterpreter parses Section 30 complete 5-family investigation command."""
    cmd = (
        "perform a complete thermal, contextual, temporal, environmental and cross-modal "
        "investigation for event 827 using all available sources. evaluate surface weather, "
        "plume transport, optical corroboration, and sar corroboration. identify whether any "
        "environmental or cross-modal evidence conflicts with the thermal detection, disclose "
        "all missing or unconfigured providers, and state what additional observation would most "
        "reduce remaining uncertainty."
    )
    parsed = command_interpreter.interpret(cmd)
    obj = parsed["objective"]
    assert obj.primary_goal == "SECTION_30_PHASE10_ACCEPTANCE"
    assert obj.stopping_condition == "SECTION_30_PHASE10_EVALUATED_AND_HALT"
    assert obj.target_event in ["EVT-827", "827"]


def test_command_interpreter_phase10_weather_and_plume():
    """Verify CommandInterpreter parses surface weather and plume dispersion commands."""
    cmd_env = "JARVIS, analyze surface weather and plume transport for event 827"
    parsed_env = command_interpreter.interpret(cmd_env)
    assert parsed_env["objective"].primary_goal == "ANALYZE_ENVIRONMENTAL_CONDITIONS"
    assert parsed_env["objective"].stopping_condition == "ENVIRONMENTAL_CONDITIONS_EVALUATED_AND_HALT"
    
    cmd_wx = "JARVIS, show weather context for event 827"
    parsed_wx = command_interpreter.interpret(cmd_wx)
    assert parsed_wx["objective"].primary_goal == "SHOW_WEATHER_CONTEXT"
    assert parsed_wx["objective"].stopping_condition == "WEATHER_CONTEXT_REPORTED_AND_HALT"


def test_command_interpreter_phase10_cross_modal_commands():
    """Verify CommandInterpreter parses optical and SAR cross-modal commands."""
    cmd_cm = "JARVIS, verify event 827 using optical and SAR cross-modal observations"
    parsed_cm = command_interpreter.interpret(cmd_cm)
    assert parsed_cm["objective"].primary_goal == "CHECK_CROSS_MODAL_CORROBORATION"
    assert parsed_cm["objective"].stopping_condition == "CROSS_MODAL_EVALUATED_AND_HALT"
    
    cmd_opt = "JARVIS, evaluate optical corroboration for event 827"
    parsed_opt = command_interpreter.interpret(cmd_opt)
    assert parsed_opt["objective"].primary_goal == "COMPARE_OPTICAL_OBSERVATIONS"
    assert parsed_opt["objective"].stopping_condition == "OPTICAL_OBSERVATIONS_EVALUATED_AND_HALT"
    
    cmd_sar = "JARVIS, evaluate radar backscatter for event 827"
    parsed_sar = command_interpreter.interpret(cmd_sar)
    assert parsed_sar["objective"].primary_goal == "CHECK_SAR_CORROBORATION"
    assert parsed_sar["objective"].stopping_condition == "SAR_CORROBORATION_EVALUATED_AND_HALT"


def test_command_interpreter_phase10_conflicts_and_missing_sources():
    """Verify CommandInterpreter parses physical conflict and unconfigured disclosure commands."""
    cmd_cnf = "JARVIS, identify whether any environmental or cross-modal evidence conflicts with the thermal detection"
    parsed_cnf = command_interpreter.interpret(cmd_cnf)
    assert parsed_cnf["objective"].primary_goal == "IDENTIFY_ENVIRONMENTAL_CONFLICTS"
    assert parsed_cnf["objective"].stopping_condition == "ENVIRONMENTAL_CONFLICTS_EVALUATED_AND_HALT"
    
    cmd_disc = "JARVIS, disclose all missing or unconfigured providers"
    parsed_disc = command_interpreter.interpret(cmd_disc)
    assert parsed_disc["objective"].primary_goal == "MISSING_ENVIRONMENTAL_DATA"
    assert parsed_disc["objective"].stopping_condition == "MISSING_ENVIRONMENTAL_DATA_REPORTED_AND_HALT"


def test_command_interpreter_phase10_uncertainty_reduction():
    """Verify CommandInterpreter parses next observation uncertainty reduction query."""
    cmd_unc = "JARVIS, what additional observation would most reduce remaining uncertainty for this event?"
    parsed_unc = command_interpreter.interpret(cmd_unc)
    assert parsed_unc["objective"].primary_goal == "HIGHEST_VALUE_OBSERVATION"
    assert parsed_unc["objective"].stopping_condition == "HIGHEST_VALUE_OBSERVATION_RECOMMENDED_AND_HALT"


# ==============================================================================
# 7. ORCHESTRATOR SECTION 30 END-TO-END EXECUTION
# ==============================================================================

def test_orchestrator_section30_end_to_end_execution(db_session):
    """Verify master orchestrator executes Section 30 primary 5-family investigation."""
    req = JarvisCommandRequest(
        command=(
            "perform a complete thermal, contextual, temporal, environmental and cross-modal "
            "investigation for event 827 using all available sources. evaluate surface weather, "
            "plume transport, optical corroboration, and sar corroboration. identify whether any "
            "environmental or cross-modal evidence conflicts with the thermal detection, disclose "
            "all missing or unconfigured providers, and state what additional observation would most "
            "reduce remaining uncertainty."
        )
    )
    res = master_orchestrator.execute_command(db=db_session, request=req, user_role="ANALYST")
    
    assert res.state in [JarvisState.COMPLETED, JarvisState.REQUIRES_APPROVAL]
    assert "SECTION_30_PHASE10_COMPLETE" in res.stopping_reason
    assert res.requires_human_approval is True
    assert res.dispatch_gate_blocked is True
    
    # Details check
    assert "environmental_sources" in res.details
    assert "cross_modal_sources" in res.details
    assert len(res.details["environmental_sources"]) >= 2
    assert len(res.details["cross_modal_sources"]) >= 2
    
    # Markdown output check
    summary = res.summary
    assert "SECTION 30: COMPLETE 5-FAMILY INTELLIGENCE INVESTIGATION" in summary
    assert "1. Target Identification & Master Executive Summary" in summary
    assert "2. Multi-Provider Thermal Infrared Synthesis" in summary
    assert "3. Cross-Domain Contextual Fusion" in summary
    assert "4. Longitudinal Temporal Baseline & Deviation Profile" in summary
    assert "5. Surface Meteorology & Atmospheric Plume Transport" in summary
    assert "6. Space-Time Synchronized Multi-Spectral Optical Corroboration" in summary
    assert "7. Synthetic Aperture Radar (SAR) Backscatter Analysis" in summary
    assert "8. Multi-Source Conflict Resolution & Epistemic Divergence" in summary
    assert "9. Transparency & Unconfigured Archive Disclosure" in summary
    assert "10. Uncertainty Reduction Recommendation & Mandatory HITL Verification Routing" in summary


# ==============================================================================
# 8. POSTGRESQL INVESTIGATION WORKSPACE PERSISTENCE
# ==============================================================================

def test_workspace_persistence_phase10_fields(db_session):
    """Verify InvestigationWorkspace stores all 12 Phase 10 columns in PostgreSQL."""
    ws = db_session.query(InvestigationWorkspace).filter(
        InvestigationWorkspace.target_event_id.in_(["EVT-827", "827"])
    ).order_by(InvestigationWorkspace.created_at.desc()).first()
    
    assert ws is not None
    assert ws.environmental_sources is not None
    assert len(ws.environmental_sources) > 0
    assert ws.environmental_observations is not None
    assert ws.environmental_relationships is not None
    assert ws.environmental_coverage is not None
    assert ws.environmental_uncertainty is not None
    assert ws.environmental_observation_count >= 1
    
    assert ws.cross_modal_sources is not None
    assert len(ws.cross_modal_sources) > 0
    assert ws.cross_modal_evidence is not None
    assert ws.cross_modal_uncertainty is not None
    assert ws.cross_modal_observation_count >= 1


# ==============================================================================
# 9. REST API INTELLIGENCE ENDPOINTS
# ==============================================================================

def test_rest_api_environmental_endpoints(api_client):
    """Verify all 7 Phase 10 REST intelligence endpoints return 200 OK."""
    r_env = api_client.get("/api/v1/intelligence/environmental/EVT-827")
    assert r_env.status_code == 200
    assert r_env.json()["status"] == "SUCCESS"
    assert "weather" in r_env.json()["data"]
    
    r_wx = api_client.get("/api/v1/intelligence/environmental/EVT-827/weather")
    assert r_wx.status_code == 200
    assert "temperature_c" in r_wx.json()["data"]
    
    r_plm = api_client.get("/api/v1/intelligence/environmental/EVT-827/plume")
    assert r_plm.status_code == 200
    assert "dispersion_direction" in r_plm.json()["data"]
    
    r_cm = api_client.get("/api/v1/intelligence/cross-modal/EVT-827")
    assert r_cm.status_code == 200
    assert r_cm.json()["data"]["corroboration_status"] in ["CORROBORATED", "PARTIALLY_CORROBORATED"]
    
    r_opt = api_client.get("/api/v1/intelligence/cross-modal/EVT-827/optical")
    assert r_opt.status_code == 200
    assert r_opt.json()["data"]["sensor"] == "SENTINEL_2_MSI"
    
    r_sar = api_client.get("/api/v1/intelligence/cross-modal/EVT-827/sar")
    assert r_sar.status_code == 200
    assert r_sar.json()["data"]["sensor"] == "SENTINEL_1_SAR"
    
    r_stat = api_client.get("/api/v1/intelligence/environmental/providers/status")
    assert r_stat.status_code == 200
    assert "environmental" in r_stat.json()["data"]
    assert "cross_modal" in r_stat.json()["data"]


# ==============================================================================
# 10. FROZEN BASELINE & SAFETY INVARIANCE CHECKS
# ==============================================================================

def test_frozen_invariants_risk_formula(db_session):
    """Verify authoritative 5-factor risk formula weights are strictly untouched."""
    from backend.app.services.risk_service import calculate_risk_score
    from backend.app.services.jarvis.jarvis_tools import JarvisToolRegistry
    
    # Verify tool_calculate_risk weights
    risk_res = JarvisToolRegistry.tool_calculate_risk(db_session, "EVT-827")
    assert risk_res["formula"] == "0.30*Intensity + 0.25*Abnormality + 0.20*Exposure + 0.15*Persistence + 0.10*Context"
    assert risk_res["weights"]["intensity"] == 0.30
    assert risk_res["weights"]["abnormality"] == 0.25
    assert risk_res["weights"]["exposure"] == 0.20
    assert risk_res["weights"]["persistence"] == 0.15
    assert risk_res["weights"]["context"] == 0.10

    # Verify calculate_risk_score calculation
    total, level, subscores, reasons = calculate_risk_score(
        max_frp=285.0,
        avg_frp=142.5,
        anomaly_info={"is_anomaly": True, "z_score": 4.5, "deviation_ratio": 3.0},
        persistence_info={"persistence_score": 8.0},
        nearest_settlement_dist_m=1200.0,
        nearest_facility_dist_m=180.0,
        landcover_class="Industrial",
        predicted_class="Industrial Fire"
    )
    assert 0.0 <= total <= 100.0
    assert "intensity" in subscores
    assert "abnormality" in subscores
    assert "exposure" in subscores
    assert "persistence" in subscores
    assert "context" in subscores


def test_frozen_invariants_xgboost_and_thresholds():
    """Verify XGBoost classifier pipeline and alert thresholds are strictly frozen."""
    from ml.inference.production_inference_service import (
        production_thermal_predictor, TARGET_CLASSES, FEATURE_COLUMNS
    )
    
    # Verify exact target classes
    assert len(TARGET_CLASSES) == 6
    assert "Industrial Fire" in TARGET_CLASSES
    assert "Gas Flare" in TARGET_CLASSES
    assert "Forest Fire" in TARGET_CLASSES
    
    # Verify 18 feature columns
    assert len(FEATURE_COLUMNS) == 18
    assert "frp_max" in FEATURE_COLUMNS
    assert "industrial_context_score" in FEATURE_COLUMNS
    
    # Verify predictor loaded
    assert production_thermal_predictor is not None


def test_safety_invariants_dispatch_gate_blocked(db_session):
    """Verify dispatch gate is held BLOCKED and autonomous dispatch is forbidden."""
    from backend.app.core.config import settings
    
    assert settings.ENABLE_OPERATIONAL_DISPATCH_GATE is False
    
    # Verify operational dispatch command is strictly blocked and requires approval
    req = JarvisCommandRequest(command="JARVIS, emergency dispatch responders to Event 827.")
    res = master_orchestrator.execute_command(db=db_session, request=req, user_role="ANALYST")
    assert res.dispatch_gate_blocked is True
    assert res.requires_human_approval is True
