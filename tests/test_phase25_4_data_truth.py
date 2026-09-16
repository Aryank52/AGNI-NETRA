"""
Phase 25.4 — Comprehensive Data Truth, Entity Semantics & Cross-System Consistency Test Suite
Validates:
1. Master Entity Semantics & Definitions:
   - Thermal (285 detections, 88 clustered events, 82 active hotspots, 6 verified incidents)
   - Industrial Facilities (35,570 geolocated authoritative vs 35,684 historical reference, with 114 non-geolocated delta)
   - CEA Power Generation (1,633 units, 502 stations, 4,125 power cadastre)
   - IBM Mining Context (414 extraction records, 206 geolocated mining sites)
   - Administrative Boundaries (735 districts in geoBoundaries IND-ADM2, 36 states/UTs)
2. Cross-System Consistency (DB, REST API, Map Layers, Dossier, JARVIS)
3. Representative Facility Geolocation & Sovereign Bounding Box Validation
4. Safety Gates & Zero Synthetic Data Governance Invariants
"""

import os
import sys
import pytest
from sqlalchemy import text
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.main import app
from backend.app.core.database import SessionLocal, IS_POSTGRESQL
from backend.app.core.config import settings
from backend.app.core.security import create_access_token
from backend.app.models.domain import (
    IndustrialFacility, AdminBoundary, CEAPowerStationStaging,
    IbmMiningLeaseContext, ProtectedArea, LULCSpatialFeature,
    ThermalEvent, ThermalDetection, Alert, User
)


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


@pytest.fixture(scope="module")
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module")
def analyst_token(db_session):
    user = db_session.query(User).first()
    if user:
        role_val = user.role.value if hasattr(user.role, 'value') else str(user.role)
        return create_access_token(subject=str(user.id), role=role_val)
    return create_access_token(subject="test-analyst-id", role="ANALYST")


# =====================================================================================
# 1. DISCREPANCY RECONCILIATION & COUNT VALIDATION
# =====================================================================================

def test_industrial_facility_authoritative_count_and_delta(db_session):
    """
    Verify industrial_facilities contains exactly 35,570 authoritative geolocated facilities.
    Document and assert the exact 114 non-geolocated staging delta from historical 35,684.
    """
    total_count = db_session.query(IndustrialFacility).count()
    assert total_count == 35570, (
        f"Expected authoritative count 35,570, got {total_count}. "
        "Every record in industrial_facilities must represent an authentic geolocated facility."
    )

    # Breakdown verification
    osm_count = db_session.query(IndustrialFacility).filter(IndustrialFacility.source == "OSM").count()
    cea_count = db_session.query(IndustrialFacility).filter(IndustrialFacility.source == "CEA").count()
    cand_count = db_session.query(IndustrialFacility).filter(IndustrialFacility.source == "PROMOTED_CANDIDATE").count()

    assert osm_count == 35557  # 35,546 raw OSM features + 11 seed hubs
    assert cea_count == 8      # 8 geolocated CEA Super Thermal Power Stations
    assert cand_count == 5     # 5 promoted verified candidates
    assert osm_count + cea_count + cand_count == 35570

    # Verify historical delta is exactly 114
    historical_reference = 35684
    delta = historical_reference - total_count
    assert delta == 114, f"Expected historical staging delta of exactly 114, got {delta}"


def test_cea_power_stations_and_generating_units(db_session):
    """
    Verify CEA dataset semantics:
    - 1,633 individual generating units in cea_power_stations_staging
    - 502 distinct power stations / projects represented
    - 4,125 facilities in industrial_facilities under the power sector cadastre
    """
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


def test_ibm_mining_leases_and_mining_sites(db_session):
    """
    Verify Mining dataset semantics:
    - 414 official mineral extraction lease distribution records in ibm_mining_lease_context
    - 206 geolocated mining sites & quarries in industrial_facilities
    """
    ibm_lease_count = db_session.query(IbmMiningLeaseContext).count()
    assert ibm_lease_count == 414, f"Expected 414 IBM mineral lease context records, got {ibm_lease_count}"

    mining_sites_count = db_session.execute(text("""
        SELECT COUNT(*) FROM industrial_facilities 
        WHERE facility_type = 'MINING' OR LOWER(name) LIKE '%mine%' OR LOWER(master_sector) LIKE '%mining%';
    """)).scalar()
    assert mining_sites_count == 206, f"Expected 206 geolocated mining sites, got {mining_sites_count}"


def test_admin_boundaries_vector_polygons(db_session):
    """
    Verify Administrative Boundaries:
    - 36 States and Union Territories (admin_level = 1)
    - 735 sovereign district vector polygons (admin_level = 2) in geoBoundaries IND-ADM2
    """
    states_count = db_session.query(AdminBoundary).filter(AdminBoundary.admin_level == 1).count()
    assert states_count == 36, f"Expected 36 sovereign States/UTs, got {states_count}"

    districts_count = db_session.query(AdminBoundary).filter(AdminBoundary.admin_level == 2).count()
    assert districts_count == 735, f"Expected 735 sovereign district boundaries, got {districts_count}"


def test_thermal_event_hierarchy(db_session):
    """
    Verify Thermal telemetry hierarchy:
    - 285 raw satellite pixel detections
    - 88 total clustered events (and 88 corresponding alerts)
    - 82 active hotspots (status = 'ACTIVE')
    - 6 verified operational incidents (status = 'VERIFIED')
    """
    raw_detections = db_session.query(ThermalDetection).count()
    assert raw_detections == 285, f"Expected 285 raw detections, got {raw_detections}"

    total_events = db_session.query(ThermalEvent).count()
    assert total_events == 88, f"Expected 88 clustered events, got {total_events}"

    active_events = db_session.query(ThermalEvent).filter(ThermalEvent.status == "ACTIVE").count()
    assert active_events == 82, f"Expected 82 active hotspots, got {active_events}"

    verified_events = db_session.query(ThermalEvent).filter(ThermalEvent.status == "VERIFIED").count()
    assert verified_events == 6, f"Expected 6 verified incidents, got {verified_events}"

    assert active_events + verified_events == total_events


# =====================================================================================
# 2. DATA TRUTH REST API ENDPOINT VALIDATION
# =====================================================================================

def test_data_truth_endpoint(client):
    """
    Verify GET /api/v1/admin/data-truth returns status 200, operational state,
    authoritative summary metrics, and full Master Truth Table.
    """
    resp = client.get("/api/v1/admin/data-truth")
    assert resp.status_code == 200, f"Expected 200 OK, got {resp.status_code}: {resp.text}"
    data = resp.json()

    assert data["status"] == "OPERATIONAL"
    assert "governance" in data
    assert data["governance"]["operational_dispatch_gate"] is False
    assert data["governance"]["automated_model_activation"] is False
    assert data["governance"]["human_in_the_loop_mandatory"] is True
    assert data["governance"]["zero_synthetic_data_verified"] is True

    summary = data["summary"]
    assert summary["authoritative_facilities"] == 35570
    assert summary["cea_generating_units"] == 1633
    assert summary["cea_distinct_power_stations"] == 502
    assert summary["power_infrastructure_cadastre"] == 4125
    assert summary["ibm_mineral_lease_records"] == 414
    assert summary["geolocated_mining_sites"] == 206
    assert summary["admin_states_and_uts"] == 36
    assert summary["admin_districts"] == 735
    assert summary["raw_satellite_detections"] == 285
    assert summary["total_pipeline_events"] == 88
    assert summary["active_hotspots"] == 82
    assert summary["verified_incidents"] == 6

    # Verify Truth Table items
    truth_table = data["truth_table"]
    assert len(truth_table) >= 7
    dataset_ids = [item["dataset_id"] for item in truth_table]
    assert "DS-FAC-OSM-CANONICAL" in dataset_ids
    assert "DS-CEA-UNITS" in dataset_ids
    assert "DS-IBM-LEASES" in dataset_ids
    assert "DS-ADMIN-DISTRICTS" in dataset_ids
    assert "DS-ADMIN-STATES" in dataset_ids
    assert "DS-FIRMS-HOTSPOTS" in dataset_ids


def test_gis_layers_catalog_semantic_disambiguation(client):
    """
    Verify /api/v1/gis/layers reflects the disambiguated counts and semantic details.
    """
    resp = client.get("/api/v1/gis/layers")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "OPERATIONAL"
    layers = {l["id"]: l for l in data["layers"]}

    # Facilities layer
    fac_layer = layers["industrial_facilities"]
    assert fac_layer["record_count"] == 35570
    assert fac_layer["semantic_details"]["authoritative_geolocated_facilities"] == 35570
    assert fac_layer["semantic_details"]["historical_reference_count"] == 35684

    # Power stations layer
    pwr_layer = layers["power_stations"]
    assert pwr_layer["record_count"] == 4125
    assert pwr_layer["semantic_details"]["power_infrastructure_cadastre"] == 4125
    assert pwr_layer["semantic_details"]["cea_generating_units"] == 1633
    assert pwr_layer["semantic_details"]["cea_distinct_power_stations"] == 502

    # Mining layer
    mine_layer = layers["mining"]
    assert mine_layer["record_count"] == 206
    assert mine_layer["semantic_details"]["geolocated_mining_sites"] == 206
    assert mine_layer["semantic_details"]["ibm_mineral_lease_records"] == 414

    # Districts layer
    dist_layer = layers["admin_districts"]
    assert dist_layer["record_count"] == 735
    assert dist_layer["semantic_details"]["authoritative_districts"] == 735
    assert dist_layer["semantic_details"]["historical_reference_count"] == 736


# =====================================================================================
# 3. FACILITY GEOLOCATION & SOVEREIGN BOUNDING BOX VALIDATION
# =====================================================================================

def test_facility_geolocation_crs_and_sovereign_boundary(db_session):
    """
    Sample 50 representative facilities across multiple states/regions and verify:
    - Longitude in [68.0, 97.5]
    - Latitude in [6.5, 37.5]
    - Valid non-null coordinates
    - Source is authentic
    """
    facilities = db_session.query(IndustrialFacility).limit(50).all()
    assert len(facilities) >= 25

    for fac in facilities:
        assert fac.longitude is not None and fac.latitude is not None
        assert 68.0 <= fac.longitude <= 97.5, f"Facility {fac.name} longitude {fac.longitude} out of India bounds"
        assert 6.5 <= fac.latitude <= 37.5, f"Facility {fac.name} latitude {fac.latitude} out of India bounds"
        assert fac.source in ["OSM", "CEA", "PROMOTED_CANDIDATE"]


# =====================================================================================
# 4. CROSS-SYSTEM CANONICAL EVENT CONSISTENCY
# =====================================================================================

def test_canonical_event_consistency_across_layers(client, analyst_token, db_session):
    """
    Select an active event and verify that its key attributes match identically across:
    1. Database direct query
    2. /api/v1/events/{id}
    3. /api/v1/events/buffer-assets
    """
    evt = db_session.query(ThermalEvent).filter(ThermalEvent.status == "ACTIVE").first()
    assert evt is not None

    # API call for single event
    headers = {"Authorization": f"Bearer {analyst_token}"}
    resp = client.get(f"/api/v1/events/{evt.id}", headers=headers)
    assert resp.status_code == 200
    evt_api = resp.json()

    assert evt_api["event_code"] == evt.event_code
    assert round(evt_api["latitude"], 4) == round(evt.latitude, 4)
    assert round(evt_api["longitude"], 4) == round(evt.longitude, 4)
    assert evt_api["status"] == evt.status

    # Buffer assets call
    b_resp = client.get(f"/api/v1/events/{evt.id}/buffer-assets?radius_m=5000", headers=headers)
    assert b_resp.status_code == 200
    b_data = b_resp.json()
    assert b_data["event_id"] == str(evt.id)
    assert b_data["event_code"] == evt.event_code
    assert "facilities" in b_data
    assert "protected_areas" in b_data
    assert "mining_context" in b_data


# =====================================================================================
# 5. JARVIS COMMAND ORCHESTRATION & SEMANTIC RESPONSES
# =====================================================================================

def test_jarvis_data_truth_command(client, analyst_token):
    """
    Verify JARVIS processes a Data Truth / Entity Semantics query, returns status COMPLETED,
    and includes reconciled counts and discrepancy explanations in its response summary.
    """
    headers = {"Authorization": f"Bearer {analyst_token}"}
    payload = {
        "command": "Show me the data truth and reconciled counts across all datasets"
    }
    resp = client.post("/api/v1/jarvis/command", json=payload, headers=headers)
    assert resp.status_code == 200
    data = resp.json()

    assert data["state"] == "COMPLETED"
    summary = data["summary"]
    assert "35,570" in summary
    assert "1,633" in summary
    assert "502" in summary
    assert "4,125" in summary
    assert "414" in summary
    assert "206" in summary
    assert "735" in summary
    assert "BLOCKED" in summary or "False" in summary


# =====================================================================================
# 6. SAFETY GATES & HARD INVARIANTS
# =====================================================================================

def test_safety_gates_hard_invariants():
    """
    Verify critical safety gates remain strictly locked.
    """
    assert settings.ENABLE_OPERATIONAL_DISPATCH_GATE is False, "Operational dispatch gate MUST remain False"
    assert settings.ENABLE_AUTOMATED_MODEL_ACTIVATION is False, "Automated model activation MUST remain False"
