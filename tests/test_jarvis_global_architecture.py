"""
AGNI-NETRA — JARVIS Phase 6 Global Intelligence Architecture & Provider Abstraction Test Suite
Validates:
1. Provider Registry: Controlled registration, discovery, metadata, and factual capabilities.
2. Provider Metadata: Explicit attributes without fabricated claims.
3. Geographic Coverage: Explicit modeling (GLOBAL, COUNTRY, REGION, STATE, DISTRICT).
4. Provider Health: Lightweight status checks (AVAILABLE vs NOT_CONFIGURED).
5. India Intelligence Profile: Complete 8-provider operational stack.
6. Global Profile Scaffolding: Future extension points without unpopulated claims.
7. Source Provenance: Lineage metadata on canonical evidence objects.
8. Missing Provider Behavior: Graceful handling of unconfigured providers (Weather) without hallucinations.
9. Source-Aware JARVIS Commands: All 6 new user-triggered commands.
10. Workspace Source Persistence: Persistence in PostgreSQL database.
11. RBAC Governance: Role-governed catalog access.
12. Public Privacy Restrictions: Masking of internal diagnostic details for PUBLIC role.
13. Backward Compatibility: Authoritative algorithms and dispatch gate invariant preserved.
14. Section 24 Acceptance Scenario: End-to-end multi-source investigation and HITL evaluation.
"""

import pytest
import uuid
from typing import Any, Dict
from sqlalchemy.orm import Session
from backend.app.core.database import SessionLocal
from backend.app.models.domain import InvestigationWorkspace, ThermalEvent
from backend.app.models.jarvis_schemas import (
    JarvisCommandRequest, JarvisState, StepStatus
)
from backend.app.services.jarvis.jarvis_orchestrator import master_orchestrator
from backend.app.services.jarvis.jarvis_command_interpreter import command_interpreter
from backend.app.services.intelligence.provider_registry import provider_registry, ProviderRegistry
from backend.app.services.intelligence.profiles import IndiaIntelligenceProfile, GlobalIntelligenceProfile
from backend.app.services.intelligence.provenance import SourceProvenance, create_firms_provenance
from backend.app.services.intelligence.providers.base import ProviderHealth, CoverageType


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()


def get_ws_dict(res: Any) -> Dict[str, Any]:
    """Helper to access workspace dictionary regardless of dict or Pydantic model representation."""
    if not res or res.investigation_workspace is None:
        return {}
    if isinstance(res.investigation_workspace, dict):
        return res.investigation_workspace
    if hasattr(res.investigation_workspace, "model_dump"):
        return res.investigation_workspace.model_dump()
    return vars(res.investigation_workspace)


# ---------------------------------------------------------------------------------
# 1. Provider Registry Tests
# ---------------------------------------------------------------------------------

def test_provider_registry_initialization():
    """Verify registry initializes with all required AGNI-NETRA dataset adapters."""
    reg = provider_registry
    assert reg.get_provider("FIRMS") is not None
    assert reg.get_provider("OSM") is not None
    assert reg.get_provider("CEA") is not None
    assert reg.get_provider("PARIVESH") is not None
    assert reg.get_provider("IBM_MINING") is not None
    assert reg.get_provider("ISRO_BHUVAN") is not None
    assert reg.get_provider("FSI") is not None
    assert reg.get_provider("ADMIN_BOUNDARIES") is not None
    assert reg.get_provider("WEATHER_INTELLIGENCE") is not None
    assert reg.get_provider("HIGH_RES_OPTICAL") is not None


def test_provider_metadata_and_factual_claims():
    """Validate provider metadata is machine-readable and factual without false global claims."""
    firms = provider_registry.get_provider("FIRMS")
    assert firms is not None
    meta = firms.get_metadata()
    assert meta.provider_name == "FIRMS"
    assert meta.geographic_coverage.coverage_type == CoverageType.GLOBAL
    assert meta.geographic_coverage.is_global is True

    cea = provider_registry.get_provider("CEA")
    assert cea is not None
    cea_meta = cea.get_metadata()
    assert cea_meta.geographic_coverage.coverage_type == CoverageType.COUNTRY
    assert cea_meta.geographic_coverage.is_global is False
    assert "India" in cea_meta.geographic_coverage.countries


def test_provider_health_reporting(db_session: Session):
    """Verify lightweight health status accurately distinguishes operational from unconfigured providers."""
    health_summary = provider_registry.get_provider_health_summary(db_session)
    statuses = health_summary["statuses"]
    assert statuses.get("FIRMS") in ("AVAILABLE", "DEGRADED")
    assert statuses.get("OSM") in ("AVAILABLE", "DEGRADED")
    assert statuses.get("CEA") in ("AVAILABLE", "DEGRADED")
    assert statuses.get("WEATHER_INTELLIGENCE") == "NOT_CONFIGURED"
    assert statuses.get("HIGH_RES_OPTICAL") == "NOT_CONFIGURED"


# ---------------------------------------------------------------------------------
# 2. Intelligence Profiles Tests
# ---------------------------------------------------------------------------------

def test_india_intelligence_profile():
    """Validate IndiaIntelligenceProfile is the active operational stack."""
    prof = IndiaIntelligenceProfile.get_profile()
    assert prof.profile_id == "INDIA"
    assert prof.is_active_default is True
    assert "FIRMS" in prof.active_providers
    assert "OSM" in prof.active_providers
    assert "CEA" in prof.active_providers
    assert "PARIVESH" in prof.active_providers
    assert "ISRO_BHUVAN" in prof.active_providers
    assert "IBM_MINING" in prof.active_providers
    assert "FSI" in prof.active_providers
    assert "ADMIN_BOUNDARIES" in prof.active_providers


def test_global_profile_scaffolding():
    """Validate GlobalIntelligenceProfile contains extension points without claiming unpopulated datasets."""
    prof = GlobalIntelligenceProfile.get_profile()
    assert prof.profile_id == "GLOBAL"
    assert prof.is_active_default is False
    # Only globally-native layers are active
    assert set(prof.active_providers) == {"FIRMS", "OSM"}
    assert len(prof.extension_points) >= 4
    # Future global capabilities are explicitly documented
    assert any("Copernicus" in ep for ep in prof.extension_points)
    assert any("ECMWF" in ep for ep in prof.extension_points)


# ---------------------------------------------------------------------------------
# 3. Provenance and Evidence Availability Matrix Tests
# ---------------------------------------------------------------------------------

def test_source_provenance_model():
    """Ensure SourceProvenance records enforce strict factual audit fields."""
    prov = create_firms_provenance(record_id="DET-9876", sensor="VIIRS_NOAA21", confidence=95.0)
    assert prov.provider == "FIRMS"
    assert prov.dataset == "NASA_FIRMS_VIIRS_NOAA21"
    assert prov.geographic_coverage == "GLOBAL"
    assert prov.spatial_resolution == "375m"
    assert prov.limitations is not None
    assert prov.confidence_tier == "HIGH"


def test_evidence_availability_matrix():
    """Validate 5-state evidence availability matrix construction."""
    matrix = provider_registry.build_evidence_availability_matrix()
    assert matrix["THERMAL_HOTSPOTS"] == "AVAILABLE"
    assert matrix["INDUSTRIAL_FACILITIES"] == "AVAILABLE"
    assert matrix["ENVIRONMENTAL_CLEARANCES"] == "PARTIAL"
    assert matrix["WEATHER_METEOROLOGY"] == "MISSING"
    assert matrix["HIGH_RES_OPTICAL"] == "MISSING"


# ---------------------------------------------------------------------------------
# 4. Graceful Missing Provider Handling Tests
# ---------------------------------------------------------------------------------

def test_missing_provider_graceful_handling(db_session: Session):
    """
    When user requests 'Investigate this event with weather context',
    JARVIS must report 'WEATHER CONTEXT UNAVAILABLE' without hallucinating or crashing.
    """
    req = JarvisCommandRequest(
        command="JARVIS, investigate Event EVT-827 with weather context.",
        session_id=f"test-weather-{uuid.uuid4().hex[:6]}"
    )
    res = master_orchestrator.execute_command(db_session, req, user_role="ANALYST")
    assert res.state in [JarvisState.COMPLETED, JarvisState.REQUIRES_APPROVAL]
    assert "WEATHER CONTEXT UNAVAILABLE" in res.summary
    assert res.dispatch_gate_blocked is True
    # Investigation succeeds using available intelligence
    assert "EVT-827" in res.summary or "827" in res.summary


# ---------------------------------------------------------------------------------
# 5. Source-Aware JARVIS Commands Tests
# ---------------------------------------------------------------------------------

def test_command_what_sources_were_used(db_session: Session):
    """Command: 'JARVIS, what sources were used for this case?'"""
    req = JarvisCommandRequest(
        command="JARVIS, what sources were used for this case?",
        session_id=f"test-sources-{uuid.uuid4().hex[:6]}"
    )
    res = master_orchestrator.execute_command(db_session, req, user_role="ANALYST")
    assert res.state == JarvisState.COMPLETED
    assert "SOURCES USED IN THIS ASSESSMENT" in res.summary
    assert "NASA FIRMS" in res.summary
    assert "OpenStreetMap" in res.summary
    assert "INDIA" in res.summary


def test_command_geographic_coverage(db_session: Session):
    """Command: 'JARVIS, what geographic coverage is available here?'"""
    req = JarvisCommandRequest(
        command="JARVIS, what geographic coverage is available here?",
        session_id=f"test-cov-{uuid.uuid4().hex[:6]}"
    )
    res = master_orchestrator.execute_command(db_session, req, user_role="ANALYST")
    assert res.state == JarvisState.COMPLETED
    assert "GEOGRAPHIC INTELLIGENCE COVERAGE" in res.summary
    assert "GLOBAL-CAPABLE INTELLIGENCE LAYERS" in res.summary
    assert "INDIA-FOCUSED OPERATIONAL LAYERS" in res.summary


def test_command_missing_sources(db_session: Session):
    """Command: 'JARVIS, what data is missing from this investigation?'"""
    req = JarvisCommandRequest(
        command="JARVIS, what data is missing from this investigation?",
        session_id=f"test-gap-{uuid.uuid4().hex[:6]}"
    )
    res = master_orchestrator.execute_command(db_session, req, user_role="ANALYST")
    assert res.state == JarvisState.COMPLETED
    assert "INTELLIGENCE GAP ANALYSIS" in res.summary
    assert "WEATHER CONTEXT" in res.summary
    assert "HIGH-RESOLUTION OPTICAL" in res.summary


def test_command_coverage_sufficiency(db_session: Session):
    """Command: 'JARVIS, is this investigation sufficiently covered?'"""
    req = JarvisCommandRequest(
        command="JARVIS, is this investigation sufficiently covered?",
        session_id=f"test-suff-{uuid.uuid4().hex[:6]}"
    )
    res = master_orchestrator.execute_command(db_session, req, user_role="ANALYST")
    assert res.state == JarvisState.COMPLETED
    assert "SUFFICIENT FOR OPERATIONAL DISPOSITION" in res.summary


def test_command_source_provenance(db_session: Session):
    """Command: 'JARVIS, show me the source provenance.'"""
    req = JarvisCommandRequest(
        command="JARVIS, show me the source provenance.",
        session_id=f"test-prov-{uuid.uuid4().hex[:6]}"
    )
    res = master_orchestrator.execute_command(db_session, req, user_role="ANALYST")
    assert res.state == JarvisState.COMPLETED
    assert "SOURCE PROVENANCE AUDIT" in res.summary
    assert "FIRMS" in res.summary
    assert "OSM" in res.summary


# ---------------------------------------------------------------------------------
# 6. Workspace Persistence and RBAC / Public Restrictions
# ---------------------------------------------------------------------------------

def test_workspace_source_persistence(db_session: Session):
    """Verify source metadata columns persist in PostgreSQL database."""
    req = JarvisCommandRequest(
        command="JARVIS, investigate Event EVT-827",
        session_id=f"test-persist-{uuid.uuid4().hex[:6]}"
    )
    res = master_orchestrator.execute_command(db_session, req, user_role="ANALYST")
    assert res.investigation_id is not None

    ws_db = db_session.query(InvestigationWorkspace).filter(
        InvestigationWorkspace.investigation_id == res.investigation_id
    ).first()
    assert ws_db is not None
    assert ws_db.coverage_profile == "INDIA"
    assert isinstance(ws_db.sources_used, list)
    assert len(ws_db.sources_used) > 0
    assert "FIRMS" in ws_db.sources_used
    assert ws_db.source_availability_matrix is not None


def test_rbac_public_restrictions():
    """Verify PUBLIC role masks internal diagnostics while preserving high-level metadata."""
    public_catalog = provider_registry.list_providers(role="PUBLIC")
    analyst_catalog = provider_registry.list_providers(role="ANALYST")

    assert len(public_catalog) == len(analyst_catalog)
    # Check that public descriptions are sanitized
    firms_pub = next(p for p in public_catalog if p["provider_name"] == "FIRMS")
    assert firms_pub["source_provenance"] == "Authoritative Satellite / Official Public Catalog"


# ---------------------------------------------------------------------------------
# 7. Section 24 Final Acceptance Scenario
# ---------------------------------------------------------------------------------

def test_section_24_acceptance_scenario(db_session: Session):
    """
    Section 24 Acceptance Scenario:
    'JARVIS, investigate Event 827 and tell me which intelligence sources support the assessment,
    what geographic coverage they provide, what evidence is missing,
    and whether the evidence is sufficient for human verification.'
    """
    req = JarvisCommandRequest(
        command="JARVIS, investigate Event 827 and tell me which intelligence sources support the assessment, what geographic coverage they provide, what evidence is missing, and whether the evidence is sufficient for human verification.",
        session_id=f"test-sec24-{uuid.uuid4().hex[:6]}"
    )
    res = master_orchestrator.execute_command(db_session, req, user_role="ANALYST")

    assert res.state == JarvisState.COMPLETED
    assert res.dispatch_gate_blocked is True
    # 1. Sources identified
    assert "INTELLIGENCE SOURCES SUPPORTING ASSESSMENT" in res.summary
    assert "NASA FIRMS" in res.summary
    assert "OpenStreetMap" in res.summary
    assert "Central Electricity Authority" in res.summary
    # 2. Coverage identified
    assert "GEOGRAPHIC COVERAGE" in res.summary
    assert "INDIA" in res.summary
    # 3. Missing evidence identified
    assert "WEATHER CONTEXT UNAVAILABLE" in res.summary
    assert "HIGH-RES OPTICAL SCENE UNAVAILABLE" in res.summary
    # 4. Evidence sufficiency & HITL evaluated
    assert "EVIDENCE SUFFICIENCY" in res.summary
    assert "SUFFICIENT FOR ACTIONABLE DISPOSITION" in res.summary
    assert "Human-In-The-Loop (HITL)" in res.summary
    # 5. Workspace fields populated
    ws = get_ws_dict(res)
    assert ws.get("coverage_profile") == "INDIA"
    assert "FIRMS" in (ws.get("sources_used") or [])
