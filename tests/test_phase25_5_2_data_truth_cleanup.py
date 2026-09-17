"""
AGNI-NETRA — Phase 25.5.2 Final Data Count, Entity Semantics, Provenance
& Authoritative Source Cleanup Test Suite

Validates:
1. Exact 35,570 Authoritative Physical Facilities (35,546 OSM + 11 seed hubs + 8 CEA + 5 candidates)
2. Exactly 0 Facilities with NULL Coordinates in the Active Database
3. 114-Record Delta Historical Non-Geocoded Staging Explanation Invariance
4. Power Semantics: 1,633 Generating Units across 502 Stations vs 4,125 Power Cadastre Facilities
5. Mining Semantics: 414 IBM Lease Records vs 206 Geolocated Mining Sites
6. Administrative Semantics: 36 Sovereign States/UTs + 735 Vector Polygon Districts
7. Thermal Hierarchy: 285 Raw Detections -> 88 Clustered Events -> 82 Active + 6 Verified Incidents
8. Analytics /command-center KPI Payload Authoritative Accuracy
9. GIS /layers Catalog Semantic Disambiguation & Layer Counts
10. JARVIS Natural Language Deterministic Understanding for All 7 Primary Entity Queries
11. Operational Safety Invariants Strictly Locked (Dispatch=False, Activation=False)
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.app.main import app
from backend.app.core.database import SessionLocal
from backend.app.models.domain import (
    IndustrialFacility, CEAPowerStationStaging, IbmMiningLeaseContext,
    AdminBoundary, ThermalEvent, ThermalDetection, Alert
)
from backend.app.core.config import settings

client = TestClient(app)


@pytest.fixture(scope="module")
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


# =============================================================================
# 1. INDUSTRIAL FACILITY EXACT COUNT & ZERO NULL COORDINATES
# =============================================================================

def test_industrial_facility_exact_count_and_zero_null_coords(db_session: Session):
    """Verify that industrial_facilities contains exactly 35,570 records with zero NULL coordinates."""
    total_count = db_session.query(IndustrialFacility).count()
    assert total_count == 35570, (
        f"Expected exactly 35,570 authoritative industrial facilities, got {total_count}"
    )

    # Invariant: ZERO null coordinates
    null_coords = db_session.execute(text("""
        SELECT COUNT(*) FROM industrial_facilities 
        WHERE latitude IS NULL OR longitude IS NULL;
    """)).scalar()
    assert null_coords == 0, f"Expected 0 facilities with NULL coordinates, found {null_coords}"

    # Invariant: Source breakdown
    osm_count = db_session.query(IndustrialFacility).filter(IndustrialFacility.source == "OSM").count()
    cea_count = db_session.query(IndustrialFacility).filter(IndustrialFacility.source == "CEA").count()
    cand_count = db_session.query(IndustrialFacility).filter(IndustrialFacility.source == "PROMOTED_CANDIDATE").count()

    assert osm_count == 35557, f"Expected 35,557 OSM facilities, got {osm_count}"
    assert cea_count == 8, f"Expected 8 geolocated CEA power stations, got {cea_count}"
    assert cand_count == 5, f"Expected 5 promoted candidate facilities, got {cand_count}"
    assert osm_count + cea_count + cand_count == 35570


# =============================================================================
# 2. 114-RECORD HISTORICAL STAGING DELTA INVARIANCE
# =============================================================================

def test_114_delta_historical_staging_invariance(db_session: Session):
    """Verify historical 35,684 catalog reference and exact 114 non-geocoded staging delta."""
    total_authoritative = db_session.query(IndustrialFacility).count()
    historical_catalog_reference = 35684
    delta = historical_catalog_reference - total_authoritative
    assert delta == 114, f"Expected delta of exactly 114, got {delta}"

    # Verify Data Truth endpoint documents this exact lineage
    resp = client.get("/api/v1/admin/data-truth")
    assert resp.status_code == 200
    data = resp.json()
    disc = [d for d in data.get("discrepancies_reconciled", []) if d["topic"] == "Industrial Facility Count"]
    assert len(disc) > 0
    item = disc[0]
    assert item["counts"]["authoritative_db"] == 35570
    assert item["counts"]["historical_catalog_reference"] == 35684
    assert item["counts"]["delta"] == 114
    assert "114 non-geolocated provisional project staging entries" in item["lineage"]


# =============================================================================
# 3. POWER SEMANTICS: GENERATING UNITS VS STATIONS VS CADASTRE
# =============================================================================

def test_power_semantics_generating_units_vs_stations_vs_cadastre(db_session: Session):
    """Verify CEA generating units (1,633), distinct stations (502), and power cadastre (4,125)."""
    units_count = db_session.query(CEAPowerStationStaging).count()
    assert units_count == 1633, f"Expected 1,633 CEA generating units, got {units_count}"

    stations_count = db_session.execute(
        text("SELECT COUNT(DISTINCT project_name) FROM cea_power_stations_staging;")
    ).scalar()
    assert stations_count == 502, f"Expected 502 distinct power station projects, got {stations_count}"

    power_cadastre_count = db_session.execute(text("""
        SELECT COUNT(*) FROM industrial_facilities 
        WHERE cea_project_name IS NOT NULL OR LOWER(facility_type) LIKE '%power%' OR LOWER(master_sector) LIKE '%power%';
    """)).scalar()
    assert power_cadastre_count == 4125, f"Expected 4,125 power cadastre facilities, got {power_cadastre_count}"


# =============================================================================
# 4. MINING SEMANTICS: LEASES VS SITES
# =============================================================================

def test_mining_semantics_leases_vs_sites(db_session: Session):
    """Verify IBM extraction lease context records (414) vs geolocated mining sites (206)."""
    ibm_lease_count = db_session.query(IbmMiningLeaseContext).count()
    assert ibm_lease_count == 414, f"Expected 414 IBM mineral lease context records, got {ibm_lease_count}"

    mining_sites_count = db_session.execute(text("""
        SELECT COUNT(*) FROM industrial_facilities 
        WHERE facility_type = 'MINING' OR LOWER(name) LIKE '%mine%' OR LOWER(master_sector) LIKE '%mining%';
    """)).scalar()
    assert mining_sites_count == 206, f"Expected 206 geolocated mining sites, got {mining_sites_count}"


# =============================================================================
# 5. ADMINISTRATIVE BOUNDARIES: 36 STATES + 735 DISTRICTS
# =============================================================================

def test_admin_boundaries_36_states_735_districts(db_session: Session):
    """Verify 36 States/UTs (admin_level=1) and 735 sovereign district vector polygons (admin_level=2)."""
    states_count = db_session.query(AdminBoundary).filter(AdminBoundary.admin_level == 1).count()
    assert states_count == 36, f"Expected 36 sovereign States/UTs, got {states_count}"

    districts_count = db_session.query(AdminBoundary).filter(AdminBoundary.admin_level == 2).count()
    assert districts_count == 735, f"Expected 735 sovereign district boundaries, got {districts_count}"


# =============================================================================
# 6. THERMAL TELEMETRY HIERARCHY: DETECTIONS -> EVENTS -> INCIDENTS
# =============================================================================

def test_thermal_telemetry_hierarchy(db_session: Session):
    """Verify 285 raw detections, 88 clustered events (82 active + 6 verified incidents), 88 alerts."""
    raw_detections = db_session.query(ThermalDetection).count()
    assert raw_detections == 285, f"Expected 285 raw pixel detections, got {raw_detections}"

    total_events = db_session.query(ThermalEvent).count()
    assert total_events == 88, f"Expected 88 clustered pipeline events, got {total_events}"

    active_events = db_session.query(ThermalEvent).filter(ThermalEvent.status == "ACTIVE").count()
    assert active_events == 82, f"Expected 82 active monitored hotspots, got {active_events}"

    verified_events = db_session.query(ThermalEvent).filter(ThermalEvent.status == "VERIFIED").count()
    assert verified_events == 6, f"Expected 6 analyst-verified incidents, got {verified_events}"
    assert active_events + verified_events == total_events

    alerts_count = db_session.query(Alert).count()
    assert alerts_count == 88, f"Expected 88 operational alerts, got {alerts_count}"


# =============================================================================
# 7. ANALYTICS /COMMAND-CENTER KPI PAYLOAD ACCURACY
# =============================================================================

def test_analytics_command_center_kpi_payload_accuracy():
    """Verify GET /api/v1/analytics/command-center returns authoritative counts in KPIs."""
    resp = client.get("/api/v1/analytics/command-center")
    assert resp.status_code == 200
    kpis = resp.json().get("kpis", {})

    assert kpis.get("authoritative_facilities") == 35570
    assert kpis.get("cea_generating_units") == 1633
    assert kpis.get("cea_distinct_power_stations") == 502
    assert kpis.get("power_infrastructure_cadastre") == 4125
    assert kpis.get("ibm_mineral_lease_records") == 414
    assert kpis.get("geolocated_mining_sites") == 206
    assert kpis.get("admin_districts") == 735
    assert kpis.get("admin_states") == 36
    assert kpis.get("total_live_events") == 88
    assert kpis.get("active_events") == 82


# =============================================================================
# 8. GIS /LAYERS CATALOG LABELS & SEMANTIC DETAILS
# =============================================================================

def test_gis_layers_catalog_labels_and_semantics():
    """Verify /api/v1/gis/layers provides disambiguated counts and historical explanations."""
    resp = client.get("/api/v1/gis/layers")
    assert resp.status_code == 200
    layers = {l["id"]: l for l in resp.json().get("layers", [])}

    # Industrial facilities layer
    fac_layer = layers["industrial_facilities"]
    assert fac_layer["record_count"] == 35570
    assert fac_layer["semantic_details"]["authoritative_geolocated_facilities"] == 35570
    assert fac_layer["semantic_details"]["historical_reference_count"] == 35684
    assert "114 non-geolocated provisional project entries" in fac_layer["semantic_details"]["variance_explanation"]

    # Power stations layer
    pwr_layer = layers["power_stations"]
    assert pwr_layer["record_count"] == 4125
    assert pwr_layer["semantic_details"]["cea_generating_units"] == 1633
    assert pwr_layer["semantic_details"]["cea_distinct_power_stations"] == 502

    # Mining layer
    mine_layer = layers["mining"]
    assert mine_layer["record_count"] == 206
    assert mine_layer["semantic_details"]["ibm_mineral_lease_records"] == 414


# =============================================================================
# 9. JARVIS DETERMINISTIC NATURAL LANGUAGE INQUIRIES
# =============================================================================

def test_jarvis_data_truth_natural_language_queries():
    """Verify JARVIS provides exact numbers and definitions for all 7 entity queries."""
    test_queries = [
        ("How many industrial facilities are there?", "35,570", "authoritative geolocated facilities"),
        ("How many power stations are there?", "502", "power stations"),
        ("How many generating units are there?", "1,633", "generating units"),
        ("How many mining blocks are there?", "414", "lease"),
        ("How many mining lease records are there?", "414", "lease"),
        ("How many active thermal events are there?", "82", "active"),
        ("How many verified incidents are there?", "6", "verified")
    ]

    for query, expected_count, expected_term in test_queries:
        resp = client.post("/api/v1/jarvis/command", json={
            "command": query,
            "session_id": "test-data-truth-session",
            "user_role": "ANALYST"
        })
        assert resp.status_code == 200, f"JARVIS returned status {resp.status_code} for query: {query}"
        summary = resp.json().get("summary", "")
        assert expected_count in summary, (
            f"Query '{query}' expected count '{expected_count}', but got summary:\n{summary[:300]}"
        )
        assert expected_term.lower() in summary.lower(), (
            f"Query '{query}' expected term '{expected_term}', but got summary:\n{summary[:300]}"
        )


# =============================================================================
# 10. SAFETY INVARIANTS STRICTLY LOCKED
# =============================================================================

def test_operational_safety_invariants_strictly_locked(db_session: Session):
    """Verify dispatch gates and model activation remain hardlocked to False."""
    assert settings.ENABLE_OPERATIONAL_DISPATCH_GATE is False
    assert settings.ENABLE_AUTOMATED_MODEL_ACTIVATION is False

    # Invariant: 0 live dispatches emitted across all alerts
    live_dispatches = db_session.query(Alert).filter(Alert.is_operational_dispatch == True).count()
    assert live_dispatches == 0, f"Expected 0 live dispatches, found {live_dispatches}"
