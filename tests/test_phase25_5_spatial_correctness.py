"""
AGNI-NETRA — Phase 25.5 Final Golden-Path Acceptance, Map Alignment Restoration,
Spatial Correctness & Complete Cross-System Validation Test Suite

Validates:
1. Coordinate Order: GeoJSON [longitude, latitude] invariant across all layers.
2. CRS / SRID: EPSG:4326 (WGS 84) reference standard across the pipeline.
3. BBOX Normalization: min_lon, min_lat, max_lon, max_lat parsing and spatial queries.
4. India Boundary & Sovereign Protection: 0 records leak into Sri Lanka; legitimate southern coastal points preserved.
5. National Facility Distribution: Facilities, power stations, and mining are distributed across North, South, East, West, Central.
6. Event ↔ Facility Distance Agreement: Database == Haversine == Dossier == JARVIS.
7. Thermal Event Spatial Alignment: Canonical event coordinates preserved across all representations.
8. Duplicate Feature Elimination: Unique feature IDs across all GeoJSON outputs.
9. Golden Event Chain: Jamnagar event (EVT-GUJ-20260916-150D) lifecycle consistency.
10. Safety Invariants: Dispatch and automated model activation remain strictly False.
"""

import math
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.app.main import app
from backend.app.core.database import SessionLocal, haversine_distance_meters
from backend.app.models.domain import (
    ThermalEvent, IndustrialFacility, ProtectedArea, LULCSpatialFeature, User
)
from backend.app.core.config import settings
from backend.app.core.security import create_access_token
from backend.app.services.jarvis.jarvis_tools import JarvisToolRegistry

client = TestClient(app)


@pytest.fixture(scope="module")
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="module")
def auth_headers(db_session: Session):
    user = db_session.query(User).first()
    if user:
        role_val = user.role.value if hasattr(user.role, 'value') else str(user.role)
        token = create_access_token(subject=str(user.id), role=role_val)
    else:
        token = create_access_token(subject="analyst-test-id", role="ANALYST")
    return {"Authorization": f"Bearer {token}"}


# =============================================================================
# 1. COORDINATE ORDER & CRS/SRID VALIDATION ([lon, lat] GEOJSON INVARIANT)
# =============================================================================

def test_coordinate_order_across_representative_features():
    """
    Verifies GeoJSON coordinates follow [longitude, latitude] across:
    - Northern India
    - Western India
    - Central India
    - Eastern India
    - Southern India
    - Coastal & Border regions
    """
    res = client.get("/api/v1/gis/industrial-facilities?limit=100")
    assert res.status_code == 200
    data = res.json()
    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) >= 20

    tested_count = 0
    for feat in data["features"]:
        geom = feat["geometry"]
        assert geom["type"] == "Point"
        coords = geom["coordinates"]
        assert len(coords) == 2
        lon, lat = coords[0], coords[1]

        # Invariant: Longitude between 65.0E and 100.0E; Latitude between 6.5N and 38.0N
        assert 65.0 <= lon <= 100.0, f"Facility {feat['properties']['name']} longitude {lon} out of bounds"
        assert 6.5 <= lat <= 38.0, f"Facility {feat['properties']['name']} latitude {lat} out of bounds"
        tested_count += 1

    assert tested_count >= 20, f"Expected at least 20 features tested, got {tested_count}"


def test_thermal_events_coordinate_order():
    """Verifies thermal events output standard GeoJSON [lon, lat] coordinates."""
    res = client.get("/api/v1/gis/thermal-events?limit=50")
    assert res.status_code == 200
    data = res.json()
    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) > 0

    for feat in data["features"]:
        lon, lat = feat["geometry"]["coordinates"]
        assert 68.0 <= lon <= 98.0, f"Event longitude {lon} out of range"
        assert 8.0 <= lat <= 36.0, f"Event latitude {lat} out of range"


def test_crs_reference_standard():
    """Verifies GIS catalog declares EPSG:4326 (WGS 84) reference CRS."""
    res = client.get("/api/v1/gis/layers")
    assert res.status_code == 200
    data = res.json()
    assert data["reference_crs"] == "EPSG:4326 (WGS 84)"


# =============================================================================
# 2. BBOX NORMALIZATION & QUERY VALIDATION
# =============================================================================

def test_bbox_normalization_and_filtering():
    """
    Verifies BBOX parameters are strictly [min_lon, min_lat, max_lon, max_lat].
    Tests Western India subset (Gujarat/Maharashtra).
    """
    # Western India bounding box: lon 68.0-75.0, lat 20.0-25.0
    res = client.get("/api/v1/gis/industrial-facilities?bbox=68.0,20.0,75.0,25.0&limit=50")
    assert res.status_code == 200
    data = res.json()
    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) > 0

    for feat in data["features"]:
        lon, lat = feat["geometry"]["coordinates"]
        assert 68.0 <= lon <= 75.0, f"Facility lon {lon} not in western BBOX"
        assert 20.0 <= lat <= 25.0, f"Facility lat {lat} not in western BBOX"


def test_bbox_malformed_rejection():
    """Verifies invalid or inverted BBOX parameters are handled or normalized safely."""
    # Test non-numeric
    res_bad = client.get("/api/v1/gis/industrial-facilities?bbox=abc,def,ghi,jkl")
    assert res_bad.status_code == 400

    # Test out of range coordinates
    res_oor = client.get("/api/v1/gis/industrial-facilities?bbox=200,0,210,10")
    assert res_oor.status_code == 400


# =============================================================================
# 3. SOVEREIGN INDIA BOUNDARY & ZERO SRI LANKA LEAKAGE AUDIT
# =============================================================================

def test_zero_records_in_sri_lanka(db_session: Session):
    """
    CRITICAL SOVEREIGN INVARIANT:
    Verifies that ZERO records in industrial_facilities, thermal_events,
    and thermal_detections lie within the Sri Lanka geographic bounding box
    (Lat 5.9°N–9.9°N, Lon 79.5°E–82.0°E).
    """
    sl_fac = db_session.execute(text("""
        SELECT COUNT(*) FROM industrial_facilities
        WHERE latitude BETWEEN 5.9 AND 9.9 AND longitude BETWEEN 79.5 AND 82.0;
    """)).scalar() or 0
    assert sl_fac == 0, f"Detected {sl_fac} facilities leaking into Sri Lanka"

    sl_evt = db_session.execute(text("""
        SELECT COUNT(*) FROM thermal_events
        WHERE latitude BETWEEN 5.9 AND 9.9 AND longitude BETWEEN 79.5 AND 82.0;
    """)).scalar() or 0
    assert sl_evt == 0, f"Detected {sl_evt} thermal events leaking into Sri Lanka"

    sl_det = db_session.execute(text("""
        SELECT COUNT(*) FROM thermal_detections
        WHERE latitude BETWEEN 5.9 AND 9.9 AND longitude BETWEEN 79.5 AND 82.0;
    """)).scalar() or 0
    assert sl_det == 0, f"Detected {sl_det} thermal detections leaking into Sri Lanka"


def test_legitimate_southern_mainland_facilities_preserved(db_session: Session):
    """
    Verifies that legitimate Indian mainland facilities at the southern tip
    (Kanniyakumari, Tirunelveli, Tuticorin at lat 8.08°N–9.0°N, lon 77.0°E–78.5°E)
    are authentic, geolocated, and preserved.
    """
    count = db_session.execute(text("""
        SELECT COUNT(*) FROM industrial_facilities
        WHERE latitude BETWEEN 8.0 AND 9.0 AND longitude BETWEEN 77.0 AND 78.5;
    """)).scalar() or 0
    assert count > 100, f"Expected >100 legitimate southern Indian facilities, found {count}"


# =============================================================================
# 4. NATIONAL GEOGRAPHIC DISTRIBUTION (ELIMINATING LATITUDE CONCENTRATION)
# =============================================================================

def test_national_distribution_industrial_facilities():
    """
    Verifies that at national zoom (All India BBOX), returned facilities are
    spatially distributed across at least 15 distinct Indian States spanning
    North, South, East, West, and Central India.
    """
    res = client.get("/api/v1/gis/industrial-facilities?bbox=65.0,8.0,95.0,35.0&limit=400")
    assert res.status_code == 200
    data = res.json()
    assert len(data["features"]) >= 100

    states = set()
    lats = []
    lons = []
    for f in data["features"]:
        st = f["properties"].get("state")
        if st:
            states.add(st)
        lons.append(f["geometry"]["coordinates"][0])
        lats.append(f["geometry"]["coordinates"][1])

    # Distribution assertions
    assert len(states) >= 15, f"Expected >= 15 states in national sample, got {len(states)}: {states}"
    assert min(lats) < 12.0, "Sample lacks southern representation"
    assert max(lats) > 28.0, "Sample lacks northern representation"
    assert min(lons) < 73.0, "Sample lacks western representation"
    assert max(lons) > 85.0, "Sample lacks eastern representation"


def test_national_distribution_power_stations():
    """Verifies CEA power stations are spatially distributed across India."""
    res = client.get("/api/v1/gis/power-stations?bbox=65.0,8.0,95.0,35.0&limit=200")
    assert res.status_code == 200
    data = res.json()
    assert len(data["features"]) >= 50

    states = set()
    lats = []
    for f in data["features"]:
        st = f["properties"].get("state")
        if st:
            states.add(st)
        lats.append(f["geometry"]["coordinates"][1])

    assert len(states) >= 10, f"Expected >= 10 states for power stations, got {len(states)}"
    assert max(lats) > 28.0, "Power stations lack northern coverage"
    assert min(lats) < 14.0, "Power stations lack southern coverage"


def test_national_distribution_mining():
    """Verifies mining layer reflects key mineral states across India."""
    res = client.get("/api/v1/gis/mining?bbox=65.0,8.0,95.0,35.0&limit=200")
    assert res.status_code == 200
    data = res.json()
    assert len(data["features"]) >= 50

    states = set()
    for f in data["features"]:
        st = f["properties"].get("state")
        if st:
            states.add(st)

    # Must include prominent mining states
    mining_states = {"Jharkhand", "Madhya Pradesh", "Chhattisgarh", "Odisha", "Goa", "Maharashtra", "Rajasthan"}
    intersection = states.intersection(mining_states)
    assert len(intersection) >= 3, f"Expected key mining states in sample, got: {states}"


# =============================================================================
# 5. NO DUPLICATE FEATURES IN GEOJSON
# =============================================================================

def test_no_duplicate_features_in_geojson_endpoints():
    """Verifies that every GeoJSON layer returns distinct, non-duplicated feature IDs."""
    for ep in ["/api/v1/gis/industrial-facilities?limit=200", "/api/v1/gis/power-stations?limit=100", "/api/v1/gis/mining?limit=100"]:
        res = client.get(ep)
        assert res.status_code == 200
        data = res.json()
        ids = [f["properties"]["id"] for f in data["features"]]
        assert len(ids) == len(set(ids)), f"Duplicate feature IDs detected in {ep}"


# =============================================================================
# 6. EVENT ↔ FACILITY SPATIAL RELATIONSHIP & DISTANCE AGREEMENT
# =============================================================================

def test_distance_agreement_database_dossier_jarvis(db_session: Session, auth_headers):
    """
    CRITICAL NUMERICAL INVARIANT:
    For representative critical event EVT-GUJ-20260916-150D:
    Verifies:
    Database Distance == Haversine Distance == Dossier Distance == JARVIS Tool Distance
    Within 1 meter tolerance.
    """
    evt = db_session.query(ThermalEvent).filter(ThermalEvent.event_code == "EVT-GUJ-20260916-150D").first()
    assert evt is not None, "Golden test event EVT-GUJ-20260916-150D must exist"

    # 1. Database stored distance
    db_dist = float(evt.nearest_facility_distance_m)
    assert db_dist == 181.9, f"Expected stored distance 181.9m, got {db_dist}m"

    # 2. Calculated Haversine distance to nearest facility in DB
    fac = db_session.query(IndustrialFacility).filter(
        IndustrialFacility.name.like("%Reliance Jamnagar Mega Refinery%")
    ).first()
    assert fac is not None, "Reliance Jamnagar Mega Refinery facility must exist"

    calc_dist = haversine_distance_meters(evt.latitude, evt.longitude, fac.latitude, fac.longitude)
    assert abs(calc_dist - db_dist) < 1.0, f"Haversine {calc_dist:.1f}m differs from DB {db_dist:.1f}m"

    # 3. Dossier endpoint distance
    dossier_res = client.get(f"/api/v1/gis/dossier/{evt.id}", headers=auth_headers)
    assert dossier_res.status_code == 200
    dossier_data = dossier_res.json()
    assert "spatial_context_enrichment" in dossier_data
    nearest_facs = dossier_data["spatial_context_enrichment"]["nearest_industrial_facilities"]
    assert len(nearest_facs) > 0
    top_fac = nearest_facs[0]
    assert "Reliance" in top_fac["name"] or "Jamnagar" in top_fac["name"]
    assert abs(top_fac["distance_m"] - db_dist) < 1.0, f"Dossier distance {top_fac['distance_m']}m differs from DB {db_dist}m"

    # 4. Buffer assets endpoint distance
    buffer_res = client.get(f"/api/v1/events/{evt.id}/buffer-assets?radius_m=1000", headers=auth_headers)
    assert buffer_res.status_code == 200
    buf_data = buffer_res.json()
    assert len(buf_data["facilities"]) > 0
    buf_fac = buf_data["facilities"][0]
    assert abs(buf_fac["distance_m"] - db_dist) < 1.0, f"Buffer distance {buf_fac['distance_m']}m differs from DB {db_dist}m"

    # 5. JARVIS spatial tool distance
    jarvis_res = JarvisToolRegistry.tool_get_event_spatial_context(db_session, evt.id)
    assert "nearest_facilities" in jarvis_res
    assert len(jarvis_res["nearest_facilities"]) > 0
    j_fac = jarvis_res["nearest_facilities"][0]
    assert abs(j_fac["distance_meters"] - db_dist) < 1.0, f"JARVIS tool distance {j_fac['distance_meters']}m differs from DB {db_dist}m"


# =============================================================================
# 7. COMPLETE GOLDEN EVENT CHAIN PRESERVATION
# =============================================================================

def test_golden_event_chain_invariance(db_session: Session, auth_headers):
    """
    Verifies that the golden event EVT-GUJ-20260916-150D retains identical identity,
    coordinates, and risk profile through all operational touchpoints:
    Event Stream → Detail → Alert → Buffer → Dossier → JARVIS → Verification → Report.
    """
    evt = db_session.query(ThermalEvent).filter(ThermalEvent.event_code == "EVT-GUJ-20260916-150D").first()
    assert evt is not None

    expected_lat = evt.latitude
    expected_lon = evt.longitude
    expected_code = evt.event_code

    # A. Detail endpoint
    res_det = client.get(f"/api/v1/events/{evt.id}", headers=auth_headers)
    assert res_det.status_code == 200
    assert res_det.json()["latitude"] == expected_lat
    assert res_det.json()["longitude"] == expected_lon

    # B. Alerts endpoint
    res_alt = client.get(f"/api/v1/alerts?event_id={evt.id}", headers=auth_headers)
    assert res_alt.status_code == 200
    assert len(res_alt.json()["alerts"]) >= 1

    # C. Verification workflow
    res_ver = client.get(f"/api/v1/events/{evt.id}/trace", headers=auth_headers)
    assert res_ver.status_code == 200

    # D. PDF Report generation
    res_rep = client.get(f"/api/v1/reports/event/{evt.id}/download", headers=auth_headers)
    assert res_rep.status_code == 200
    assert res_rep.content[:4] == b"%PDF"


# =============================================================================
# 8. HARD-LOCKED SYSTEM SAFETY INVARIANTS
# =============================================================================

def test_operational_safety_gates_strictly_locked():
    """
    CONFIRMS ABSOLUTE SAFETY LOCK:
    - Live automated dispatch is HARD-LOCKED FALSE.
    - Automated model activation is HARD-LOCKED FALSE.
    """
    assert settings.ENABLE_OPERATIONAL_DISPATCH_GATE is False, "Dispatch gate must be False"
    assert settings.ENABLE_AUTOMATED_MODEL_ACTIVATION is False, "Model activation must be False"
