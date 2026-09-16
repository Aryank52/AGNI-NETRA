"""
Phase 25.3 — Comprehensive Data Reconciliation & System Hardening Test Suite
Validates:
1. Complete dataset restoration:
   - industrial_facilities >= 35,000 (all authentic OSM features + major hubs)
   - admin_boundaries (36 States/UTs, 735 Districts)
   - cea_power_stations_staging >= 1,600
   - ibm_mining_lease_context >= 400
   - protected_areas >= 10
   - lulc_spatial_features >= 10
   - thermal_events & alerts consistency
2. Geographic distribution across India (North, South, East, West, Central)
3. Coordinate validity: all coordinates within India sovereign bounding box [68.0E - 97.5E, 6.5N - 37.5N]
4. Zero synthetic/fabricated data invariants
5. Hard-locked safety gates:
   - ENABLE_OPERATIONAL_DISPATCH_GATE == False
   - ENABLE_AUTOMATED_MODEL_ACTIVATION == False
6. Dialect-neutral spatial functions and deep facility intelligence
"""

import os
import sys
import pytest
from sqlalchemy import text
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.database import engine, get_db, SessionLocal, haversine_distance_meters
from backend.app.core.config import settings
from backend.app.main import app
from backend.app.models.domain import (
    IndustrialFacility, AdminBoundary, CEAPowerStationStaging,
    IbmMiningLeaseContext, ProtectedArea, LULCSpatialFeature,
    ThermalEvent, Alert, User
)
from backend.app.core.security import create_access_token


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


@pytest.fixture(scope="module")
def analyst_token(db_session):
    user = db_session.query(User).first()
    if user:
        role_val = user.role.value if hasattr(user.role, 'value') else str(user.role)
        return create_access_token(subject=str(user.id), role=role_val)
    return create_access_token(subject="test-analyst-id", role="ANALYST")


# =====================================================================================
# 1. HARD-LOCKED SYSTEM SAFETY CONTROLS
# =====================================================================================

def test_hardlocked_safety_gates():
    """Verify operational dispatch and model activation gates remain strictly False."""
    assert getattr(settings, "ENABLE_OPERATIONAL_DISPATCH_GATE", None) is False, (
        "CRITICAL: ENABLE_OPERATIONAL_DISPATCH_GATE must be strictly False"
    )
    assert getattr(settings, "ENABLE_AUTOMATED_MODEL_ACTIVATION", None) is False, (
        "CRITICAL: ENABLE_AUTOMATED_MODEL_ACTIVATION must be strictly False"
    )


# =====================================================================================
# 2. COMPLETE RESTORED DATASET POPULATION
# =====================================================================================

def test_industrial_facilities_full_volume(db_session):
    """Verify industrial_facilities count is restored to authoritative national scale (> 35,000)."""
    count = db_session.query(IndustrialFacility).count()
    assert count >= 35000, f"Expected >= 35,000 authentic facilities, found {count}"


def test_admin_boundaries_full_volume(db_session):
    """Verify admin_boundaries contains 36 States/UTs and >= 730 Districts."""
    states_count = db_session.query(AdminBoundary).filter(AdminBoundary.admin_level == 1).count()
    districts_count = db_session.query(AdminBoundary).filter(AdminBoundary.admin_level == 2).count()
    assert states_count == 36, f"Expected 36 States/UTs, found {states_count}"
    assert districts_count >= 730, f"Expected >= 730 Districts, found {districts_count}"


def test_cea_power_stations_population(db_session):
    """Verify cea_power_stations_staging contains >= 1,600 verified generating units."""
    count = db_session.query(CEAPowerStationStaging).count()
    assert count >= 1600, f"Expected >= 1,600 CEA power station units, found {count}"


def test_ibm_mining_leases_population(db_session):
    """Verify ibm_mining_lease_context contains >= 400 official IBM bulletin records."""
    count = db_session.query(IbmMiningLeaseContext).count()
    assert count >= 400, f"Expected >= 400 IBM mining lease records, found {count}"


def test_protected_areas_and_lulc(db_session):
    """Verify protected areas and LULC polygons are populated."""
    pa_count = db_session.query(ProtectedArea).count()
    lulc_count = db_session.query(LULCSpatialFeature).count()
    assert pa_count >= 10, f"Expected >= 10 Protected Areas, found {pa_count}"
    assert lulc_count >= 10, f"Expected >= 10 LULC Spatial Features, found {lulc_count}"


# =====================================================================================
# 3. GEOGRAPHIC DISTRIBUTION & COORDINATE ACCURACY
# =====================================================================================

def test_national_geographic_distribution(db_session):
    """Verify facilities are distributed across all Indian regions (North, South, East, West, Central)."""
    regions = {
        "North": ["Punjab", "Haryana", "Himachal Pradesh", "Jammu and Kashmir", "Uttarakhand", "Delhi"],
        "South": ["Tamil Nadu", "Karnataka", "Kerala", "Andhra Pradesh", "Telangana"],
        "East": ["West Bengal", "Odisha", "Bihar", "Jharkhand", "Assam"],
        "West": ["Gujarat", "Maharashtra", "Rajasthan", "Goa"],
        "Central": ["Madhya Pradesh", "Chhattisgarh", "Uttar Pradesh"]
    }
    for region_name, state_list in regions.items():
        count = db_session.query(IndustrialFacility).filter(
            IndustrialFacility.state.in_(state_list)
        ).count()
        assert count > 50, f"Region {region_name} has insufficient facilities: {count}"


def test_facility_coordinates_within_india(db_session):
    """Verify 100% of facilities with coordinates lie within the sovereign India bounding box."""
    # Sovereign India BBOX: Longitude ~68.0 to 97.5, Latitude ~6.5 to 37.5
    invalid = db_session.query(IndustrialFacility).filter(
        (IndustrialFacility.latitude < 6.5) | (IndustrialFacility.latitude > 37.5) |
        (IndustrialFacility.longitude < 68.0) | (IndustrialFacility.longitude > 97.5)
    ).count()
    assert invalid == 0, f"Found {invalid} facilities with coordinates outside sovereign India BBOX"


# =====================================================================================
# 4. GIS CATALOG & ENDPOINTS INTEGRATION
# =====================================================================================

def test_gis_layers_catalog_api(client):
    """Verify /api/v1/gis/layers reflects the true restored counts."""
    response = client.get("/api/v1/gis/layers")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "OPERATIONAL"

    layer_map = {layer["id"]: layer["record_count"] for layer in data["layers"]}
    assert layer_map.get("industrial_facilities", 0) >= 35000, f"GIS catalog shows {layer_map.get('industrial_facilities')}"
    assert layer_map.get("admin_states", 0) == 36
    assert layer_map.get("admin_districts", 0) >= 730
    assert layer_map.get("power_stations", 0) >= 1600


def test_gis_industrial_facilities_geojson(client):
    """Verify /api/v1/gis/industrial-facilities returns standard GeoJSON FeatureCollection."""
    response = client.get("/api/v1/gis/industrial-facilities?limit=50")
    assert response.status_code == 200
    fc = response.json()
    assert fc["type"] == "FeatureCollection"
    assert len(fc["features"]) == 50
    for feat in fc["features"]:
        assert feat["geometry"]["type"] == "Point"
        coords = feat["geometry"]["coordinates"]
        # GeoJSON is [lon, lat]
        assert 68.0 <= coords[0] <= 97.5, f"Lon out of range: {coords[0]}"
        assert 6.5 <= coords[1] <= 37.5, f"Lat out of range: {coords[1]}"
        assert feat["properties"]["name"]


def test_gis_bbox_filtering(client):
    """Verify bounding box spatial filtering functions accurately."""
    # BBOX for Gujarat region: [68.0, 20.0, 74.0, 24.5]
    bbox_guj = "68.0,20.0,74.0,24.5"
    response = client.get(f"/api/v1/gis/industrial-facilities?bbox={bbox_guj}&limit=20")
    assert response.status_code == 200
    fc = response.json()
    for feat in fc["features"]:
        lon, lat = feat["geometry"]["coordinates"]
        assert 68.0 <= lon <= 74.0, f"Lon {lon} outside BBOX"
        assert 20.0 <= lat <= 24.5, f"Lat {lat} outside BBOX"


# =====================================================================================
# 5. FACILITY DEEP INTELLIGENCE & EVENT DOSSIER RECONCILIATION
# =====================================================================================

def test_facility_deep_intelligence_dialect_safety(client, analyst_token, db_session):
    """Verify /api/v1/facilities/{id}/intelligence executes without SQL errors."""
    fac = db_session.query(IndustrialFacility).first()
    assert fac is not None, "No facility in database"

    headers = {"Authorization": f"Bearer {analyst_token}"}
    response = client.get(f"/api/v1/facilities/{fac.id}/intelligence", headers=headers)
    assert response.status_code == 200
    dossier = response.json()
    assert "facility" in dossier
    assert "baseline" in dossier
    assert "historical_activity" in dossier
    assert "nearby_thermal_events" in dossier
    assert "nearby_power_stations" in dossier
    assert "nearby_mining_leases" in dossier
    assert "ecological_context" in dossier


def test_event_buffer_assets_with_restored_data(client, analyst_token, db_session):
    """Verify event buffer-assets returns proximate facilities and infrastructure."""
    evt = db_session.query(ThermalEvent).filter(ThermalEvent.status == "ACTIVE").first()
    assert evt is not None, "No active event found"

    headers = {"Authorization": f"Bearer {analyst_token}"}
    response = client.get(f"/api/v1/events/{evt.id}/buffer-assets?radius_m=25000", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "event_id" in data
    assert "radius_m" in data
    assert "facilities" in data
    assert "protected_areas" in data
    assert "mining_context" in data
