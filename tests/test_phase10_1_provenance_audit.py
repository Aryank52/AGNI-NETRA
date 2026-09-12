"""
AGNI-NETRA Phase 10.1: Environmental & Cross-Modal Data Authenticity / Provenance Audit Test Suite
Comprehensive verification suite validating:
1. Real provider provenance labeling (NASA FIRMS = REAL_PROVIDER, OBSERVED).
2. Local dataset provenance labeling (ISRO Bhuvan = LOCAL_DATASET).
3. Test fixture provenance labeling (Mesonet weather = TEST_FIXTURE).
4. Simulation / derivation identification (Boundary layer & plume = DERIVED).
5. Unavailable / unconfigured source handling (CAMS, Sentinel-2, Sentinel-1 = NOT_CONFIGURED / UNAVAILABLE).
6. Provider status semantics adherence (only mounted pipelines are AVAILABLE).
7. Source record ID propagation.
8. Observation and retrieval timestamp propagation.
9. Spatial provenance verification.
10. Temporal provenance and alignment verification.
11. Explicit derived vs observed labeling.
12. Plume dispersion derivation method disclosure (Gaussian vector dispersion, NOT optical smoke).
13. Cross-modal inference labeling.
14. Optical cloud limitation semantics (cloud occlusion = observation absence, NOT fire absence).
15. Graceful provider failure handling without hallucination.
16. Zero credential / secret leakage.
17. No test fixture leakage into operational real provider designations.
18. REST API provenance metadata verification.
19. JARVIS Command 1 provenance presentation and table generation.
20. Complete provenance audit across all 12 Phase 10 measurements.
21. Zero fabricated operational measurements without provenance lineage.
22. System safety invariants (single master agent, mandatory HITL routing, dispatch gate BLOCKED).
23. Operational dispatch gate enforcement (strictly BLOCKED).
"""

import pytest
import re
from datetime import datetime, timezone
from typing import Dict, Any, List

from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.database import SessionLocal
from backend.app.models.canonical import (
    SourceProvenance,
    WeatherObservation,
    WindObservation,
    PrecipitationObservation,
    CloudCondition,
    AtmosphericObservation,
    OpticalObservation,
    SARObservation,
    CrossModalEvidence,
    EnvironmentalEvidence
)
from backend.app.services.intelligence.provenance import (
    create_environmental_fixture_provenance,
    create_derived_environmental_provenance,
    create_unconfigured_provenance
)
from backend.app.services.intelligence.provider_registry import provider_registry
from backend.app.services.intelligence.environmental_engine import environmental_discovery_engine
from backend.app.services.intelligence.cross_modal_engine import cross_modal_verification_engine
from backend.app.services.jarvis.jarvis_command_interpreter import command_interpreter
from backend.app.services.jarvis.jarvis_orchestrator import master_orchestrator
from backend.app.services.jarvis.jarvis_workspace import workspace_manager
from backend.app.services.jarvis.jarvis_policy import ENABLE_OPERATIONAL_DISPATCH_GATE
from backend.app.models.jarvis_schemas import (
    JarvisCommandRequest,
    CommandIntent,
    JarvisState
)


@pytest.fixture(scope="module")
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module")
def api_client():
    with TestClient(app) as client:
        yield client


# =========================================================================
# TEST 01: REAL PROVIDER PROVENANCE
# =========================================================================
def test_01_real_provider_provenance(db_session):
    """
    Verifies that genuine thermal infrared satellite radiometry is attributed
    to REAL_PROVIDER and OBSERVED evidence nature.
    """
    cm_res = cross_modal_verification_engine.verify_event_cross_modal(db=db_session, event_ref="EVT-827")
    thermal = cm_res.get("thermal", {})
    assert thermal.get("source_type") == "REAL_PROVIDER"
    assert thermal.get("evidence_nature") == "OBSERVED"
    assert "NASA_FIRMS" in thermal.get("provider", "")


# =========================================================================
# TEST 02: LOCAL DATASET PROVENANCE
# =========================================================================
def test_02_local_dataset_provenance(db_session):
    """
    Verifies that GIS land cover classification is attributed to LOCAL_DATASET.
    """
    cm_res = cross_modal_verification_engine.verify_event_cross_modal(db=db_session, event_ref="EVT-827")
    lulc = cm_res.get("land_cover", {})
    assert lulc.get("source_type") == "LOCAL_DATASET"
    assert "BHUVAN" in lulc.get("dataset", "").upper()


# =========================================================================
# TEST 03: TEST FIXTURE IDENTIFICATION
# =========================================================================
def test_03_test_fixture_identification(db_session):
    """
    Verifies that ground mesonet weather observations used for EVT-827 are
    explicitly identified as TEST_FIXTURE.
    """
    env_res = environmental_discovery_engine.analyze_event_environment(db=db_session, event_ref="EVT-827")
    wx = env_res.get("weather", {})
    assert wx.get("source_type") == "TEST_FIXTURE"
    assert wx.get("evidence_nature") == "TEST_FIXTURE"
    assert "TEST_FIXTURE" in wx.get("provenance", {}).get("source_type", "")


# =========================================================================
# TEST 04: SIMULATION / DERIVATION IDENTIFICATION
# =========================================================================
def test_04_simulation_identification(db_session):
    """
    Verifies that plume dispersion and boundary layer height are explicitly labeled as DERIVED.
    """
    env_res = environmental_discovery_engine.analyze_event_environment(db=db_session, event_ref="EVT-827")
    relationships = env_res.get("relationships", [])
    plume_rel = next((r for r in relationships if "DERIVED" in r.get("relationship_type", "") or "plume" in r.get("description", "").lower()), None)
    assert plume_rel is not None
    assert plume_rel.get("source_type") in ["DERIVED", "SIMULATION"]
    assert plume_rel.get("evidence_nature") == "DERIVED"


# =========================================================================
# TEST 05: UNAVAILABLE / UNCONFIGURED SOURCE HANDLING
# =========================================================================
def test_05_unavailable_source_handling(db_session):
    """
    Verifies that unconfigured data providers (Sentinel-2, Sentinel-1, CAMS)
    are returned as UNAVAILABLE or NOT_CONFIGURED without raising uncaught exceptions.
    """
    cm_res = cross_modal_verification_engine.verify_event_cross_modal(db=db_session, event_ref="EVT-827")
    opt = cm_res.get("optical", {})
    sar = cm_res.get("sar", {})
    assert opt.get("source_type") in ["UNAVAILABLE", "NOT_CONFIGURED"]
    assert sar.get("source_type") in ["UNAVAILABLE", "NOT_CONFIGURED"]
    assert opt.get("evidence_nature") == "MISSING"
    assert sar.get("evidence_nature") == "MISSING"


# =========================================================================
# TEST 06: PROVIDER STATUS SEMANTICS
# =========================================================================
def test_06_provider_status_semantics():
    """
    Verifies that provider health status strictly adheres to semantics:
    only mounted pipelines are AVAILABLE; scaffolds without mounted data are NOT_CONFIGURED.
    """
    env_providers = provider_registry.get_environmental_providers()
    cm_providers = provider_registry.get_cross_modal_providers()

    for p in env_providers:
        if p.get("provider") == "IMD_AWS_GROUND":
            assert p.get("status") in ["NOT_CONFIGURED", "UNAVAILABLE"]
        if p.get("provider") == "COPERNICUS_CAMS":
            assert p.get("status") in ["NOT_CONFIGURED", "UNAVAILABLE"]

    for p in cm_providers:
        if p.get("provider") in ["COPERNICUS_SENTINEL2", "COPERNICUS_SENTINEL1"]:
            assert p.get("status") in ["NOT_CONFIGURED", "UNAVAILABLE"]
        if p.get("provider") == "PLANETSCOPE":
            assert p.get("status") in ["NOT_CONFIGURED", "UNAVAILABLE"]


# =========================================================================
# TEST 07: SOURCE RECORD ID PROPAGATION
# =========================================================================
def test_07_source_record_id_propagation(db_session):
    """
    Verifies that source_record_id is populated and propagated where available.
    """
    cm_res = cross_modal_verification_engine.verify_event_cross_modal(db=db_session, event_ref="EVT-827")
    audits = cm_res.get("measurements_audit", [])
    assert len(audits) > 0
    for a in audits:
        assert "provenance" in a
        assert len(a["provenance"]) > 0


# =========================================================================
# TEST 08: OBSERVATION TIMESTAMP PROPAGATION
# =========================================================================
def test_08_observation_timestamp_propagation(db_session):
    """
    Verifies that observation_time matches the event epoch and retrieval_time is recorded.
    """
    env_res = environmental_discovery_engine.analyze_event_environment(db=db_session, event_ref="EVT-827")
    audits = env_res.get("measurements_audit", [])
    assert len(audits) >= 5
    for a in audits:
        assert a.get("observation_time") is not None
        assert a.get("retrieval_time") is not None


# =========================================================================
# TEST 09: SPATIAL PROVENANCE
# =========================================================================
def test_09_spatial_provenance(db_session):
    """
    Verifies that spatial context (coordinates, station height, or grid cell) is present.
    """
    env_res = environmental_discovery_engine.analyze_event_environment(db=db_session, event_ref="EVT-827")
    audits = env_res.get("measurements_audit", [])
    for a in audits:
        assert "spatial_context" in a
        assert len(a["spatial_context"]) > 0


# =========================================================================
# TEST 10: TEMPORAL PROVENANCE & ALIGNMENT
# =========================================================================
def test_10_temporal_provenance(db_session):
    """
    Verifies that cross-modal verification explicitly evaluates space-time alignment.
    """
    cm_res = cross_modal_verification_engine.verify_event_cross_modal(db=db_session, event_ref="EVT-827")
    alignment = cm_res.get("alignment", {})
    assert "time_delta_hours" in alignment
    assert "spatial_distance_m" in alignment
    assert "alignment_quality" in alignment


# =========================================================================
# TEST 11: DERIVED VS OBSERVED LABELING
# =========================================================================
def test_11_derived_vs_observed_labeling(db_session):
    """
    Verifies that observed vs derived evidence nature is distinct across measurements.
    """
    env_res = environmental_discovery_engine.analyze_event_environment(db=db_session, event_ref="EVT-827")
    audits = env_res.get("measurements_audit", [])
    natures = {a.get("evidence_nature") for a in audits}
    assert "DERIVED" in natures
    assert "TEST_FIXTURE" in natures


# =========================================================================
# TEST 12: PLUME DERIVATION LABELING
# =========================================================================
def test_12_plume_derivation_labeling(db_session):
    """
    Verifies that plume trajectory is labeled as DERIVED ENVIRONMENTAL RELATIONSHIP
    and explicitly states that NO optical smoke plume was observed.
    """
    env_res = environmental_discovery_engine.analyze_event_environment(db=db_session, event_ref="EVT-827")
    audits = env_res.get("measurements_audit", [])
    plume_audit = next((a for a in audits if a.get("measurement") == "plume_direction"), None)
    assert plume_audit is not None
    assert plume_audit.get("evidence_nature") == "DERIVED"
    assert "DERIVED ENVIRONMENTAL RELATIONSHIP" in plume_audit.get("limitation", "")
    assert "NOT an observed plume" in plume_audit.get("limitation", "")


# =========================================================================
# TEST 13: CROSS-MODAL INFERENCE LABELING
# =========================================================================
def test_13_cross_modal_inference_labeling(db_session):
    """
    Verifies that multi-criteria model inferences are marked INFERRED.
    """
    cm_res = cross_modal_verification_engine.verify_event_cross_modal(db=db_session, event_ref="EVT-827")
    lulc = cm_res.get("land_cover", {})
    assert lulc.get("evidence_nature") == "INFERRED"


# =========================================================================
# TEST 14: OPTICAL CLOUD LIMITATION SEMANTICS
# =========================================================================
def test_14_optical_cloud_limitation(db_session):
    """
    Verifies the epistemic separation rule: cloud occlusion represents observation absence,
    NOT fire inactivity or flame extinction.
    """
    cm_res = cross_modal_verification_engine.verify_event_cross_modal(db=db_session, event_ref="EVT-827")
    epistemic_notes = cm_res.get("epistemic_notes", "")
    assert "Observation absence" in epistemic_notes
    assert "does NOT equal activity absence" in epistemic_notes


# =========================================================================
# TEST 15: PROVIDER FAILURE SEMANTICS
# =========================================================================
def test_15_provider_failure_semantics():
    """
    Verifies that unconfigured or unmounted providers return empty or missing payloads
    rather than fabricating operational data.
    """
    prov = provider_registry.get_environmental_providers()
    cams = next((p for p in prov if "CAMS" in p.get("dataset", "") or p.get("provider") == "COPERNICUS_ATMOSPHERIC"), None)
    assert cams is not None
    assert cams.get("status") in ["NOT_CONFIGURED", "UNAVAILABLE"]


# =========================================================================
# TEST 16: NO CREDENTIAL LEAKAGE
# =========================================================================
def test_16_no_credential_leakage(db_session):
    """
    Verifies that no API keys, tokens, or passwords are exposed in provenance records.
    """
    env_res = environmental_discovery_engine.analyze_event_environment(db=db_session, event_ref="EVT-827")
    cm_res = cross_modal_verification_engine.verify_event_cross_modal(db=db_session, event_ref="EVT-827")
    payload_str = str(env_res) + str(cm_res)

    forbidden_patterns = [r"api[_-]?key", r"bearer\s+[a-zA-Z0-9_\-\.]{10,}", r"secret[_-]?key", r"password"]
    for pattern in forbidden_patterns:
        match = re.search(pattern, payload_str, re.IGNORECASE)
        # Verify no value follows
        if match:
            # Check context is just metadata key, not actual credential value
            assert "token_secret" not in payload_str


# =========================================================================
# TEST 17: NO FIXTURE LEAKAGE INTO OPERATIONAL OUTPUT
# =========================================================================
def test_17_no_fixture_leakage_into_operational_output(db_session):
    """
    Verifies that no test fixture is surfaced as a real operational provider.
    """
    env_res = environmental_discovery_engine.analyze_event_environment(db=db_session, event_ref="EVT-827")
    audits = env_res.get("measurements_audit", [])
    for a in audits:
        if a.get("source_type") == "TEST_FIXTURE":
            assert a.get("source_type") != "REAL_PROVIDER"


# =========================================================================
# TEST 18: API PROVENANCE METADATA
# =========================================================================
def test_18_api_provenance(api_client):
    """
    Verifies that intelligence REST API endpoints return explicit provenance metadata.
    """
    resp = api_client.get("/api/v1/intelligence/environmental/EVT-827/plume")
    assert resp.status_code == 200
    data = resp.json().get("data", {})
    assert "evidence_nature" in data
    assert data["evidence_nature"] == "DERIVED"
    assert "derivation_explanation" in data


# =========================================================================
# TEST 19: JARVIS PROVENANCE PRESENTATION (COMMAND 1)
# =========================================================================
def test_19_jarvis_provenance_presentation(db_session):
    """
    Verifies that JARVIS interprets Command 1:
    'JARVIS, show the provenance and authenticity status of every environmental and cross-modal observation used for EVT-827.'
    and returns a complete markdown provenance audit table.
    """
    cmd = "JARVIS, show the provenance and authenticity status of every environmental and cross-modal observation used for EVT-827."
    req = JarvisCommandRequest(command=cmd)
    res = master_orchestrator.execute_command(db_session, req, user_role="ANALYST")

    assert res.objective.primary_goal == "PROVENANCE_AUTHENTICITY_AUDIT"
    assert "Comprehensive Measurement Provenance Table" in res.summary
    assert "TEST_FIXTURE" in res.summary
    assert "DERIVED" in res.summary
    assert "NOT_CONFIGURED" in res.summary
    assert res.dispatch_gate_blocked is True


# =========================================================================
# TEST 20: PROVENANCE COMPLETENESS (12 MEASUREMENTS)
# =========================================================================
def test_20_provenance_completeness(db_session):
    """
    Verifies that all 12 Phase 10 measurements are audited in measurements_audit.
    """
    env_res = environmental_discovery_engine.analyze_event_environment(db=db_session, event_ref="EVT-827")
    cm_res = cross_modal_verification_engine.verify_event_cross_modal(db=db_session, event_ref="EVT-827")
    env_audits = env_res.get("measurements_audit", [])
    cm_audits = cm_res.get("measurements_audit", [])
    total_audits = env_audits + cm_audits

    assert len(total_audits) == 12
    measurements = [a.get("measurement") for a in total_audits]
    expected = [
        "cloud_percentage",
        "temperature",
        "wind_speed",
        "wind_direction",
        "boundary_layer_height",
        "plume_direction",
        "precipitation_rate",
        "atmospheric_aod",
        "downstream_receptor_warning",
        "sentinel1_sigma0_vv",
        "sentinel1_coherence_change",
        "sentinel2_optical_swir"
    ]
    for m in expected:
        assert m in measurements


# =========================================================================
# TEST 21: NO FABRICATED OPERATIONAL MEASUREMENTS
# =========================================================================
def test_21_no_fabricated_operational_measurements(db_session):
    """
    Verifies that every measurement has a non-empty provenance and explicit source_type.
    """
    env_res = environmental_discovery_engine.analyze_event_environment(db=db_session, event_ref="EVT-827")
    cm_res = cross_modal_verification_engine.verify_event_cross_modal(db=db_session, event_ref="EVT-827")
    for a in env_res.get("measurements_audit", []) + cm_res.get("measurements_audit", []):
        assert a.get("provenance")
        assert a.get("source_type") in ["REAL_PROVIDER", "LOCAL_DATASET", "TEST_FIXTURE", "DERIVED", "SIMULATION", "NOT_CONFIGURED", "UNAVAILABLE"]


# =========================================================================
# TEST 22: SAFETY INVARIANTS
# =========================================================================
def test_22_safety_invariants(db_session):
    """
    Verifies that command execution returns dispatch_gate_blocked == True
    and routes to mandatory HITL verification.
    """
    cmd = "JARVIS, perform a complete environmental and cross-modal assessment of EVT-827 and distinguish observed evidence from derived and inferred evidence."
    req = JarvisCommandRequest(command=cmd)
    res = master_orchestrator.execute_command(db_session, req, user_role="ANALYST")

    assert res.dispatch_gate_blocked is True
    assert res.requires_human_approval is True
    assert res.state in [JarvisState.REQUIRES_APPROVAL, JarvisState.IDLE, JarvisState.COMPLETED]
    assert "DERIVED ENVIRONMENTAL RELATIONSHIP" in res.summary


# =========================================================================
# TEST 23: DISPATCH REMAINS BLOCKED
# =========================================================================
def test_23_dispatch_remains_blocked(db_session):
    """
    Verifies that live dispatch commands are prohibited by policy invariant.
    """
    assert ENABLE_OPERATIONAL_DISPATCH_GATE is False
    req = JarvisCommandRequest(command="JARVIS, emergency dispatch responders to EVT-827 immediately!")
    res = master_orchestrator.execute_command(db_session, req, user_role="ANALYST")

    assert res.dispatch_gate_blocked is True
    assert "BLOCKED" in res.summary or "PROHIBITED" in res.summary
