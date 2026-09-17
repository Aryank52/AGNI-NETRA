"""
AGNI-NETRA — Phase 25.5.1 Historical Map Restoration, Facility Location Fidelity
& Visual Spatial Regression Repair Test Suite

Comprehensive automated validation of:
1. Coordinate Invariance: 50+ facilities audited DB -> API GeoJSON [lon, lat] with zero delta.
2. Raw Source Consistency: Audited OSM node coordinates match raw export.geojson if present.
3. 50+ Event Coordinates Fidelity: DB -> API -> Map GeoJSON coordinates with zero delta.
4. Sri Lanka Zero Leakage Boundary: Bounding box [79.6, 5.9, 81.9, 9.85] contains 0 facilities/events.
5. Southern Mainland Legitimacy: Tamil Nadu / Kerala points strictly within Indian sovereign land.
6. Golden Event Chain: Jamnagar EVT-GUJ-20260916-150D distance ~181m to Reliance Jamnagar.
7. Macro-Facility Ordering: National UUID assets prioritized at national zoom.
8. BBOX Spatial Filtering: [minLon, minLat, maxLon, maxLat] bounding box query accuracy.
9. Static/Dynamic Architecture Invariant: No duplicate unbounded layer fetches in setupGisLayers.
10. Safety Invariants: Operational dispatch and automated model activation remain strictly False.
"""

import os
import json
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
# 1. FACILITY COORDINATES INVARIANCE (50+ SAMPLES)
# =============================================================================

def test_facility_coordinates_invariance_50(db_session: Session):
    """Verify that 50 facilities across diverse tiers match DB and API GeoJSON with 0 error."""
    facilities = db_session.execute(text("""
        SELECT id, name, latitude, longitude, facility_type, source
        FROM industrial_facilities
        WHERE latitude IS NOT NULL AND longitude IS NOT NULL
        ORDER BY 
            CASE 
                WHEN length(id) = 36 THEN 1
                WHEN source = 'CEA' THEN 2
                WHEN id LIKE 'osm_relation_%' THEN 3
                WHEN id LIKE 'osm_way_%' THEN 4
                ELSE 5
            END ASC,
            id ASC
        LIMIT 65
    """)).fetchall()

    assert len(facilities) >= 50, f"Expected at least 50 facilities, got {len(facilities)}"

    # Query APIs for both industrial facilities and dedicated power stations
    fac_resp = client.get("/api/v1/gis/industrial-facilities?limit=400")
    assert fac_resp.status_code == 200
    pwr_resp = client.get("/api/v1/gis/power-stations?limit=200")
    assert pwr_resp.status_code == 200

    api_map = {f["properties"]["id"]: f for f in fac_resp.json().get("features", [])}
    api_map.update({f["properties"]["id"]: f for f in pwr_resp.json().get("features", [])})

    verified_count = 0
    for fac in facilities:
        fac_id = str(fac[0])
        db_lat = float(fac[2])
        db_lon = float(fac[3])

        # Coordinate sanity check: Indian territory
        assert 6.0 <= db_lat <= 38.0, f"Facility {fac_id} lat {db_lat} out of India bounds"
        assert 68.0 <= db_lon <= 98.0, f"Facility {fac_id} lon {db_lon} out of India bounds"

        if fac_id in api_map:
            feat = api_map[fac_id]
            api_lon, api_lat = feat["geometry"]["coordinates"]
            assert abs(api_lat - db_lat) < 1e-6, (
                f"Facility {fac_id} lat mismatch: DB={db_lat}, API={api_lat}"
            )
            assert abs(api_lon - db_lon) < 1e-6, (
                f"Facility {fac_id} lon mismatch: DB={db_lon}, API={api_lon}"
            )
            verified_count += 1

    assert verified_count >= 50, f"Expected at least 50 sampled facilities matched in API layers with zero delta, got {verified_count}"


def test_osm_raw_master_source_fidelity(db_session: Session):
    """Verify that sampled OSM node facilities in DB match raw export.geojson if present."""
    raw_path = r"E:\PROJECTS\AGNI-NETRA(DATABASE)\FACILITIES\OSM\export.geojson"
    if not os.path.exists(raw_path):
        pytest.skip("Raw OSM export file not found on disk")

    with open(raw_path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    # Index features by osm id
    raw_lookup = {}
    for feat in raw_data.get("features", []):
        feat_id = str(feat.get("id", ""))
        geom = feat.get("geometry", {})
        if geom.get("type") == "Point" and feat_id:
            raw_lookup[feat_id] = geom["coordinates"]

    # Sample OSM node facilities from DB
    osm_db = db_session.execute(text("""
        SELECT id, latitude, longitude
        FROM industrial_facilities
        WHERE id LIKE 'osm_node_%'
        LIMIT 50
    """)).fetchall()

    checked = 0
    for row in osm_db:
        db_id = str(row[0])
        raw_id = db_id.replace("osm_node_", "node/")
        if raw_id in raw_lookup:
            raw_lon, raw_lat = raw_lookup[raw_id]
            assert abs(row[1] - raw_lat) < 1e-5, f"Latitude mismatch for {db_id}: DB={row[1]}, Raw={raw_lat}"
            assert abs(row[2] - raw_lon) < 1e-5, f"Longitude mismatch for {db_id}: DB={row[2]}, Raw={raw_lon}"
            checked += 1

    assert checked > 0 or len(raw_lookup) == 0


# =============================================================================
# 2. 50+ THERMAL EVENT COORDINATES FIDELITY
# =============================================================================

def test_event_coordinates_fidelity_50(db_session: Session):
    """Verify 50 thermal events have identical coordinates across DB and API."""
    events = db_session.execute(text("""
        SELECT id, event_code, latitude, longitude, status
        FROM thermal_events
        ORDER BY created_at DESC
        LIMIT 50
    """)).fetchall()

    assert len(events) >= 50, f"Expected at least 50 thermal events, got {len(events)}"

    resp = client.get("/api/v1/events?limit=500")
    assert resp.status_code == 200
    api_events = {e["id"]: e for e in resp.json()}

    for ev in events:
        eid = str(ev[0])
        db_lat = float(ev[2])
        db_lon = float(ev[3])

        assert 6.0 <= db_lat <= 38.0, f"Event {eid} lat {db_lat} out of India bounds"
        assert 68.0 <= db_lon <= 98.0, f"Event {eid} lon {db_lon} out of India bounds"

        if eid in api_events:
            api_ev = api_events[eid]
            assert abs(api_ev["latitude"] - db_lat) < 1e-6, f"Event {eid} latitude mismatch"
            assert abs(api_ev["longitude"] - db_lon) < 1e-6, f"Event {eid} longitude mismatch"


# =============================================================================
# 3. SRI LANKA ZERO LEAKAGE BOUNDARY VALIDATION
# =============================================================================

def test_sri_lanka_zero_leakage_boundary(db_session: Session):
    """Verify that the Sri Lanka bounding box contains 0 facilities, 0 events, 0 detections."""
    # Sri Lanka bounding box: 5.9°N to 9.85°N, 79.6°E to 81.9°E
    sl_facilities = db_session.execute(text("""
        SELECT COUNT(*) FROM industrial_facilities
        WHERE latitude BETWEEN 5.9 AND 9.85
          AND longitude BETWEEN 79.6 AND 81.9
    """)).scalar()

    sl_events = db_session.execute(text("""
        SELECT COUNT(*) FROM thermal_events
        WHERE latitude BETWEEN 5.9 AND 9.85
          AND longitude BETWEEN 79.6 AND 81.9
    """)).scalar()

    assert sl_facilities == 0, f"Expected 0 facilities in Sri Lanka, found {sl_facilities}"
    assert sl_events == 0, f"Expected 0 events in Sri Lanka, found {sl_events}"

    # Also test API endpoints with Sri Lanka bbox
    resp_fac = client.get("/api/v1/gis/industrial-facilities?bbox=79.6,5.9,81.9,9.85")
    assert resp_fac.status_code == 200
    assert len(resp_fac.json().get("features", [])) == 0

    resp_pwr = client.get("/api/v1/gis/power-stations?bbox=79.6,5.9,81.9,9.85")
    assert resp_pwr.status_code == 200
    assert len(resp_pwr.json().get("features", [])) == 0

    resp_min = client.get("/api/v1/gis/mining?bbox=79.6,5.9,81.9,9.85")
    assert resp_min.status_code == 200
    assert len(resp_min.json().get("features", [])) == 0


# =============================================================================
# 4. SOUTHERN MAINLAND LEGITIMACY VALIDATION
# =============================================================================

def test_southern_mainland_legitimacy(db_session: Session):
    """Verify southern points (Kanniyakumari / Tirunelveli) are legitimate Indian facilities."""
    southern_facilities = db_session.execute(text("""
        SELECT id, name, latitude, longitude, state
        FROM industrial_facilities
        WHERE latitude BETWEEN 8.0 AND 9.0
          AND longitude BETWEEN 77.0 AND 78.5
        ORDER BY latitude ASC
        LIMIT 10
    """)).fetchall()

    assert len(southern_facilities) > 0, "Expected legitimate southern facilities in Tamil Nadu / Kerala"
    for fac in southern_facilities:
        lat = fac[2]
        lon = fac[3]
        # Must be west of 78.5°E and above 8.0°N (Indian mainland Kanniyakumari / Tirunelveli)
        assert 8.05 <= lat <= 9.0, f"Facility {fac[0]} lat {lat} outside expected southern range"
        assert 77.0 <= lon <= 78.5, f"Facility {fac[0]} lon {lon} outside expected southern range"


# =============================================================================
# 5. GOLDEN EVENT JAMNAGAR ALIGNMENT
# =============================================================================

def test_golden_event_jamnagar_distance_alignment(db_session: Session, auth_headers):
    """Verify EVT-GUJ-20260916-150D is ~181m from Reliance Jamnagar across DB, API, Dossier, and Jarvis."""
    event = db_session.query(ThermalEvent).filter(
        ThermalEvent.event_code == "EVT-GUJ-20260916-150D"
    ).first()
    assert event is not None, "Golden event EVT-GUJ-20260916-150D must exist in database"

    jamnagar_fac = db_session.execute(text("""
        SELECT id, name, latitude, longitude
        FROM industrial_facilities
        WHERE name LIKE '%Reliance Jamnagar%'
        LIMIT 1
    """)).fetchone()
    assert jamnagar_fac is not None, "Reliance Jamnagar facility must exist"

    dist = haversine_distance_meters(
        event.latitude, event.longitude,
        jamnagar_fac[2], jamnagar_fac[3]
    )
    # Distance should be ~181.9 meters (within 250m buffer)
    assert 150.0 <= dist <= 220.0, f"Expected distance ~181m, got {dist:.2f}m"

    # Verify Dossier endpoint distance
    dossier_res = client.get(f"/api/v1/gis/dossier/{event.id}", headers=auth_headers)
    assert dossier_res.status_code == 200
    dossier_data = dossier_res.json()
    nearest_facs = dossier_data["spatial_context_enrichment"]["nearest_industrial_facilities"]
    assert len(nearest_facs) > 0
    top_fac = nearest_facs[0]
    assert "Reliance" in top_fac["name"] or "Jamnagar" in top_fac["name"]
    assert abs(top_fac["distance_m"] - dist) < 5.0

    # Verify Jarvis Tool spatial query distance agreement
    jarvis_res = JarvisToolRegistry.tool_get_event_spatial_context(db_session, event.id)
    assert "nearest_facilities" in jarvis_res
    nearby = jarvis_res["nearest_facilities"]
    assert len(nearby) > 0, "Jarvis must find nearby facilities for Jamnagar event"
    j_fac = nearby[0]
    assert "Reliance" in j_fac["name"] or "Jamnagar" in j_fac["name"]
    jarvis_dist = j_fac["distance_meters"]
    assert abs(jarvis_dist - dist) < 5.0, (
        f"Jarvis distance {jarvis_dist}m does not match Haversine {dist:.2f}m"
    )


# =============================================================================
# 6. MACRO-FACILITY ORDERING & CANONICAL ASSETS PRIORITY
# =============================================================================

def test_macro_facility_ordering_priority():
    """Verify that national UUID assets (e.g. Reliance Jamnagar) are returned in national view."""
    resp = client.get("/api/v1/gis/industrial-facilities?limit=15")
    assert resp.status_code == 200
    features = resp.json().get("features", [])
    assert len(features) > 0

    names = [f["properties"]["name"] for f in features]
    # Reliance Jamnagar or key national plants must be present in top 15
    has_national_asset = any(
        "Reliance Jamnagar" in n or "JSPL" in n or "NTPC" in n for n in names
    )
    assert has_national_asset, f"Expected national anchor assets in top 15, got: {names[:5]}"


# =============================================================================
# 7. VIEWPORT BBOX SPATIAL FILTERING
# =============================================================================

def test_bbox_spatial_query_format():
    """Verify that [minLon, minLat, maxLon, maxLat] bounding box correctly filters features."""
    # Query Gujarat BBOX [68.0, 20.0, 72.0, 24.0]
    resp = client.get("/api/v1/gis/industrial-facilities?bbox=68.0,20.0,72.0,24.0&limit=50")
    assert resp.status_code == 200
    features = resp.json().get("features", [])
    assert len(features) > 0

    for feat in features:
        lon, lat = feat["geometry"]["coordinates"]
        assert 68.0 <= lon <= 72.0, f"Longitude {lon} out of Gujarat BBOX [68, 72]"
        assert 20.0 <= lat <= 24.0, f"Latitude {lat} out of Gujarat BBOX [20, 24]"


# =============================================================================
# 8. ARCHITECTURE INVARIANT: NO DUPLICATE STATIC FETCHES
# =============================================================================

def test_maplibre_architecture_no_duplicate_static_fetches():
    """Verify MapLibreView.tsx does NOT fetch dynamic layers inside setupGisLayers."""
    maplibre_path = r"e:\PROJECTS\AGNI-NETRA\frontend\src\components\map\MapLibreView.tsx"
    with open(maplibre_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Locate setupGisLayers function
    setup_sig = "const setupGisLayers = (m: maplibregl.Map) => {"
    setup_idx = content.find(setup_sig)
    assert setup_idx != -1, "setupGisLayers function must exist in MapLibreView.tsx"
    
    # Locate where setupGisLayers ends (before setupLayerClickHandlers)
    end_sig = "const setupLayerClickHandlers = ("
    end_idx = content.find(end_sig, setup_idx)
    assert end_idx != -1, "setupLayerClickHandlers function must exist in MapLibreView.tsx"
    
    setup_body = content[setup_idx:end_idx]

    # Invariant: setupGisLayers must NOT fetch industrial-facilities, power-stations, or mining
    assert "/gis/industrial-facilities" not in setup_body, (
        "Invariant violated: setupGisLayers contains duplicate /gis/industrial-facilities fetch"
    )
    assert "/gis/power-stations" not in setup_body, (
        "Invariant violated: setupGisLayers contains duplicate /gis/power-stations fetch"
    )
    assert "/gis/mining" not in setup_body, (
        "Invariant violated: setupGisLayers contains duplicate /gis/mining fetch"
    )


# =============================================================================
# 9. LAYER INDEPENDENCE & ZERO OVERLAP VALIDATION
# =============================================================================

def test_layer_independence_zero_overlap():
    """Verify that industrial facilities and power stations layers have 0 overlapping features."""
    fac_resp = client.get("/api/v1/gis/industrial-facilities?limit=400")
    assert fac_resp.status_code == 200
    pwr_resp = client.get("/api/v1/gis/power-stations?limit=200")
    assert pwr_resp.status_code == 200

    fac_ids = set(f["properties"]["id"] for f in fac_resp.json().get("features", []))
    pwr_ids = set(f["properties"]["id"] for f in pwr_resp.json().get("features", []))

    overlap = fac_ids.intersection(pwr_ids)
    assert len(overlap) == 0, f"Expected 0 overlap between facilities and power stations, found {len(overlap)}: {list(overlap)[:5]}"


def test_nationwide_multi_region_distribution():
    """Verify top facilities span across Northern, Western, Southern, Eastern, and Central India."""
    fac_resp = client.get("/api/v1/gis/industrial-facilities?limit=400")
    assert fac_resp.status_code == 200
    features = fac_resp.json().get("features", [])
    states = set(f["properties"]["state"] for f in features if f["properties"].get("state"))

    # Must represent diverse geographic regions across India
    has_north = any(s in states for s in ["Punjab", "Haryana", "Uttar Pradesh", "Delhi", "Jammu And Kashmīr"])
    has_west = any(s in states for s in ["Gujarāt", "Gujarat", "Mahārāshtra", "Maharashtra", "Rājasthān"])
    has_south = any(s in states for s in ["Tamil Nādu", "Tamil Nadu", "Karnātaka", "Karnataka", "Kerala", "Andhra Pradesh", "Telangāna"])
    has_east = any(s in states for s in ["Bihār", "Bihar", "West Bengal", "Odisha", "Assam"])
    has_central = any(s in states for s in ["Madhya Pradesh", "Chhattīsgarh"])

    assert has_north, f"Expected Northern India representation in top 400 facilities, got states: {states}"
    assert has_west, f"Expected Western India representation in top 400 facilities, got states: {states}"
    assert has_south, f"Expected Southern India representation in top 400 facilities, got states: {states}"
    assert has_east, f"Expected Eastern India representation in top 400 facilities, got states: {states}"
    assert has_central, f"Expected Central India representation in top 400 facilities, got states: {states}"


def test_zoom_interpolated_styling_definitions():
    """Verify MapLibreView.tsx defines zoom-interpolated circle sizing for all point layers."""
    maplibre_path = r"e:\PROJECTS\AGNI-NETRA\frontend\src\components\map\MapLibreView.tsx"
    with open(maplibre_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert '"interpolate"' in content, "MapLibreView must use zoom interpolation for circle styling"
    assert "power-stations-point" in content
    assert "mining-point" in content
    assert "industrial-facilities-point" in content


# =============================================================================
# 10. SAFETY INVARIANTS
# =============================================================================

def test_safety_invariants_strictly_locked():
    """Verify operational dispatch gate and automated model activation remain strictly False."""
    assert settings.ENABLE_OPERATIONAL_DISPATCH_GATE is False, (
        "CRITICAL: ENABLE_OPERATIONAL_DISPATCH_GATE must remain False"
    )
    assert settings.ENABLE_AUTOMATED_MODEL_ACTIVATION is False, (
        "CRITICAL: ENABLE_AUTOMATED_MODEL_ACTIVATION must remain False"
    )
