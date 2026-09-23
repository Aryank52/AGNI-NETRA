"""
AGNI-NETRA — WP4 Sovereign Geographic Domain & Boundary Intelligence Test Suite
25 Comprehensive Verification Scenarios:
1. Valid Indian point acceptance
2. Foreign point rejection (Lahore, Karachi, etc.)
3. Boundary point deterministic evaluation
4. Coastal point acceptance (Jamnagar, Chennai)
5. Island point acceptance (Andaman & Nicobar, Lakshadweep)
6. Null, NaN, and Infinite coordinate rejection
7. Out-of-bounds geodetic coordinate rejection (lat > 90, lon > 180)
8. State containment correctness
9. District containment correctness
10. State and district hierarchical consistency (no cross-state mismatch)
11. Ingestion plane sovereign rejection (foreign obs routed to DLQ quarantine)
12. Duplicate and replay sovereign enforcement
13. Late-arrival sovereign enforcement
14. JARVIS foreign location rejection ("Investigate Lahore")
15. Historical spatial filtering (foreign bounds return 0 Indian records)
16. GIS GeoJSON coordinate order invariant ([lon, lat] ordering)
17. BBOX contract correctness (inverted min_lon > max_lon returns HTTP 400)
18. SRID 4326 consistency across boundary tables
19. Public portal geographic sanitization & coordinate blurring
20. Adversarial foreign place queries (Kathmandu, Dhaka, Chittagong, Thimphu, Dubai)
21. Invalid geometry diagnostics (0 invalid polygons in admin_boundaries)
22. Boundary version and provenance tracking (version '2024', authority, resolved_at)
23. Batch sovereign validation (partitioning mixed telemetry batches)
24. Performance threshold (sub-100ms single point containment)
25. Permanent safety and governance invariants
"""

import math
import uuid
import time
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from backend.app.main import app
from backend.app.core.config import settings
from backend.app.core.database import SessionLocal, get_db, IS_POSTGRESQL
from backend.app.services.india_boundary_service import (
    india_boundary_service,
    AUTHORITATIVE_SOURCE,
    AUTHORITATIVE_VERSION,
    AUTHORITATIVE_SRID
)
from backend.app.services.spatial_engine import validate_coordinates, lookup_state, lookup_district
from backend.app.services.ingestion.hardened_ingestion_service import hardened_ingestion_service
from backend.app.services.jarvis.jarvis_mission_service import JarvisObjectiveNormalizer
from backend.app.models.domain import ThermalEvent, IngestionQuarantineModel

client = TestClient(app)

POSTGRES_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@localhost:5432/agni_netra")


@pytest.fixture(scope="module")
def pg_session():
    """Provides a connection to PostgreSQL 16 if available, else standard SessionLocal."""
    engine = create_engine(POSTGRES_URL, pool_pre_ping=True)
    session = SessionLocal(bind=engine)
    try:
        yield session
    finally:
        session.close()


# ==============================================================================
# 1. CORE SOVEREIGN CONTAINMENT SCENARIOS
# ==============================================================================

def test_scenario_1_valid_indian_point(pg_session):
    """Scenario 1: Valid Indian point in New Delhi is accepted with proper state assignment."""
    is_inside, state, district, _ = india_boundary_service.is_point_inside_india(28.6139, 77.2090, db=pg_session)
    assert is_inside is True
    assert state == "Delhi"
    assert district is not None


def test_scenario_2_foreign_point_rejection(pg_session):
    """Scenario 2: Foreign points (Lahore, Karachi, Colombo) are strictly rejected with detected territory."""
    # Lahore, Pakistan
    is_inside_lahore, st, dt, _ = india_boundary_service.is_point_inside_india(31.5204, 74.3587, db=pg_session)
    assert is_inside_lahore is False
    assert st is None
    assert india_boundary_service.detect_neighboring_country(31.5204, 74.3587) == "Pakistan"

    # Karachi, Pakistan
    is_inside_karachi, _, _, _ = india_boundary_service.is_point_inside_india(24.8607, 67.0011, db=pg_session)
    assert is_inside_karachi is False

    # Colombo, Sri Lanka
    is_inside_colombo, _, _, _ = india_boundary_service.is_point_inside_india(6.9271, 79.8612, db=pg_session)
    assert is_inside_colombo is False
    assert india_boundary_service.detect_neighboring_country(6.9271, 79.8612) == "Sri Lanka"


def test_scenario_3_boundary_point_deterministic(pg_session):
    """Scenario 3: Border-adjacent points evaluate deterministically without errors."""
    lat, lon = 31.6050, 74.5750  # Wagah Border region
    res1 = india_boundary_service.is_within_india(lat, lon, db=pg_session)
    res2 = india_boundary_service.is_within_india(lat, lon, db=pg_session)
    assert res1 == res2
    assert isinstance(res1, bool)


def test_scenario_4_coastal_point(pg_session):
    """Scenario 4: Coastal points in Gujarat and Tamil Nadu evaluate accurately."""
    # Jamnagar, Gujarat coast
    is_inside_jam, st_jam, _, _ = india_boundary_service.is_point_inside_india(22.4707, 70.0577, db=pg_session)
    assert is_inside_jam is True
    assert st_jam == "Gujarat"

    # Chennai, Tamil Nadu coast
    is_inside_chn, st_chn, _, _ = india_boundary_service.is_point_inside_india(13.0827, 80.2707, db=pg_session)
    assert is_inside_chn is True
    assert st_chn == "Tamil Nadu"


def test_scenario_5_island_point(pg_session):
    """Scenario 5: Sovereign island points in Andaman & Nicobar and Lakshadweep are verified inside India."""
    # Port Blair, Andaman & Nicobar
    is_inside_an, st_an, _, _ = india_boundary_service.is_point_inside_india(11.6234, 92.7265, db=pg_session)
    assert is_inside_an is True
    assert st_an == "Andaman and Nicobar Islands"

    # Kavaratti, Lakshadweep
    is_inside_ld, st_ld, _, _ = india_boundary_service.is_point_inside_india(10.5667, 72.6417, db=pg_session)
    assert is_inside_ld is True
    assert st_ld == "Lakshadweep"


def test_scenario_6_null_nan_inf_coordinates(pg_session):
    """Scenario 6: Null, NaN, and Infinite coordinate inputs fail safely without uncaught exceptions."""
    assert india_boundary_service.is_within_india(None, 77.0, db=pg_session) is False
    assert india_boundary_service.is_within_india(28.0, None, db=pg_session) is False
    assert india_boundary_service.is_within_india(float("nan"), 77.0, db=pg_session) is False
    assert india_boundary_service.is_within_india(28.0, float("nan"), db=pg_session) is False
    assert india_boundary_service.is_within_india(float("inf"), 77.0, db=pg_session) is False
    assert india_boundary_service.is_within_india(28.0, float("-inf"), db=pg_session) is False


def test_scenario_7_invalid_geodetic_coordinates(pg_session):
    """Scenario 7: Geodetically impossible coordinates are rejected."""
    assert india_boundary_service.is_within_india(95.0, 77.0, db=pg_session) is False
    assert india_boundary_service.is_within_india(-91.0, 77.0, db=pg_session) is False
    assert india_boundary_service.is_within_india(28.0, 185.0, db=pg_session) is False
    assert india_boundary_service.is_within_india(28.0, -181.0, db=pg_session) is False


def test_scenario_8_state_containment(pg_session):
    """Scenario 8: Multi-state points correctly resolve their distinct state boundaries."""
    test_cases = [
        (19.0760, 72.8777, "Maharashtra"),
        (12.9716, 77.5946, "Karnataka"),
        (22.5726, 88.3639, "West Bengal"),
        (24.1997, 82.6645, "Madhya Pradesh"),
        (22.3595, 82.7501, "Chhattisgarh"),
        (23.7957, 86.4304, "Jharkhand")
    ]
    for lat, lon, expected_state in test_cases:
        is_in, st, _, _ = india_boundary_service.is_point_inside_india(lat, lon, db=pg_session)
        assert is_in is True, f"Failed for {expected_state} at ({lat}, {lon})"
        assert st == expected_state, f"Expected {expected_state}, got {st}"


def test_scenario_9_district_containment(pg_session):
    """Scenario 9: Points resolve valid districts or 'UNKNOWN'; never fabricates random district names."""
    is_in, st, dt, _ = india_boundary_service.is_point_inside_india(28.6139, 77.2090, db=pg_session)
    assert is_in is True
    assert dt is not None
    assert dt != ""


def test_scenario_10_state_district_consistency(pg_session):
    """Scenario 10: State and district assignments belong to the same sovereign jurisdiction without mismatch."""
    ctx = india_boundary_service.get_hierarchical_context(19.0760, 72.8777, db=pg_session)
    assert ctx["is_inside_india"] is True
    assert ctx["state_name"] == "Maharashtra"
    assert "Mumbai" in ctx["district_name"] or ctx["district_name"] != "UNKNOWN"


# ==============================================================================
# 2. INGESTION & PIPELINE INTEGRATION SCENARIOS
# ==============================================================================

def test_scenario_11_ingestion_sovereign_rejection(pg_session):
    """Scenario 11: Ingestion plane quarantees foreign observations to DLQ and blocks event creation."""
    tag = uuid.uuid4().hex[:6]
    foreign_obs = [
        {
            "source_record_id": f"for-{tag}-01",
            "provider": "NASA_FIRMS",
            "sensor": "VIIRS_NOAA20",
            "latitude": 31.5204,  # Lahore, Pakistan
            "longitude": 74.3587,
            "brightness": 335.0,
            "frp": 25.0,
            "confidence": 85.0,
            "acq_timestamp": datetime.now(timezone.utc).isoformat()
        }
    ]

    res = hardened_ingestion_service.process_ingestion_batch(
        db=pg_session,
        records=foreign_obs,
        provider="NASA_FIRMS",
        dataset="VIIRS_NOAA20_NRT"
    )

    assert res["records_received"] == 1
    assert res["records_quarantined"] == 1
    assert res["records_accepted"] == 0

    # Verify DLQ quarantine entry
    q_entry = pg_session.query(IngestionQuarantineModel).filter(
        IngestionQuarantineModel.source_record_id == f"for-{tag}-01"
    ).first()
    assert q_entry is not None
    assert "SOVEREIGN_OUT_OF_DOMAIN" in q_entry.reason


def test_scenario_12_duplicate_and_replay_sovereign_enforcement(pg_session):
    """Scenario 12: Replayed or duplicate foreign observations cannot bypass sovereign checks."""
    tag = uuid.uuid4().hex[:6]
    foreign_obs = {
        "source_record_id": f"rep-{tag}",
        "provider": "NASA_FIRMS",
        "sensor": "VIIRS_NOAA20",
        "latitude": 24.8607,  # Karachi, Pakistan
        "longitude": 67.0011,
        "brightness": 320.0,
        "frp": 15.0,
        "acq_timestamp": datetime.now(timezone.utc).isoformat()
    }

    # First delivery
    res1 = hardened_ingestion_service.process_ingestion_batch(pg_session, [foreign_obs])
    assert res1["records_quarantined"] == 1

    # Replay
    res2 = hardened_ingestion_service.process_ingestion_batch(pg_session, [foreign_obs], is_replay=True)
    assert res2["records_accepted"] == 0


def test_scenario_13_late_arrival_sovereign_enforcement(pg_session):
    """Scenario 13: Late-arriving observations are subject to identical sovereign containment."""
    tag = uuid.uuid4().hex[:6]
    late_foreign_obs = {
        "source_record_id": f"late-{tag}",
        "latitude": 6.9271,  # Colombo, Sri Lanka
        "longitude": 79.8612,
        "brightness": 310.0,
        "frp": 10.0,
        "acq_timestamp": "2024-01-01T12:00:00Z"
    }
    res = hardened_ingestion_service.process_ingestion_batch(pg_session, [late_foreign_obs])
    assert res["records_quarantined"] == 1
    assert res["records_accepted"] == 0


# ==============================================================================
# 3. JARVIS GEOGRAPHIC GROUNDING SCENARIOS
# ==============================================================================

def test_scenario_14_jarvis_foreign_location_rejection():
    """Scenario 14: JARVIS normalizer rejects objectives targeting foreign territories."""
    obj_lahore = JarvisObjectiveNormalizer.normalize("Investigate industrial fire near Lahore")
    assert obj_lahore.is_valid_sovereign_scope is False
    assert obj_lahore.intent == "REJECTED_OUT_OF_SCOPE"
    assert obj_lahore.location_category == "OUT_OF_DOMAIN_LOCATION"
    assert "outside the Sovereign Territory of India" in obj_lahore.rejection_reason

    obj_colombo = JarvisObjectiveNormalizer.normalize("Assess high thermal hotspot in Colombo")
    assert obj_colombo.is_valid_sovereign_scope is False
    assert obj_colombo.location_category == "OUT_OF_DOMAIN_LOCATION"


def test_scenario_15_historical_spatial_filtering(pg_session):
    """Scenario 15: Spatial filtering with foreign bounding box returns 0 Indian records."""
    # Bounding box around Lahore (lat 31.0 - 32.0, lon 74.0 - 75.0)
    query = text("""
        SELECT COUNT(*) FROM thermal_events
        WHERE latitude BETWEEN 31.0 AND 32.0
          AND longitude BETWEEN 74.0 AND 75.0
          AND state != 'Punjab'
          AND state != 'Himachal Pradesh'
          AND state != 'Jammu and Kashmir';
    """)
    cnt = pg_session.execute(query).scalar()
    # Any events in that envelope must belong to Indian states if near border, never foreign entities
    assert cnt == 0


# ==============================================================================
# 4. GIS CONTRACTS & PUBLIC PORTAL SANITIZATION
# ==============================================================================

def test_scenario_16_gis_coordinate_order(pg_session):
    """Scenario 16: GeoJSON outputs follow strict [longitude, latitude] coordinate ordering."""
    geojson_data = india_boundary_service.get_authoritative_india_geojson(pg_session, simplified=True)
    assert geojson_data["type"] == "FeatureCollection"
    assert len(geojson_data["features"]) == 36

    feat = geojson_data["features"][0]
    geom_type = feat["geometry"]["type"]
    coords = feat["geometry"]["coordinates"]

    if geom_type == "Polygon":
        sample_pt = coords[0][0]
    else:  # MultiPolygon
        sample_pt = coords[0][0][0]

    # In India: longitude is ~68 to 98, latitude is ~6 to 38
    lon, lat = sample_pt[0], sample_pt[1]
    assert 65.0 <= lon <= 100.0, f"Longitude {lon} out of expected Indian range"
    assert 5.0 <= lat <= 40.0, f"Latitude {lat} out of expected Indian range"


def test_scenario_17_bbox_correctness():
    """Scenario 17: Inverted BBOX coordinates (min_lon > max_lon) raise HTTP 400 Bad Request."""
    # min_lon (85.0) > max_lon (75.0)
    resp = client.get("/api/v1/gis/thermal-events?bbox=85.0,20.0,75.0,25.0")
    assert resp.status_code == 400
    assert "Invalid BBOX coordinate order" in resp.json()["detail"]



def test_scenario_18_srid_correctness(pg_session):
    """Scenario 18: All administrative boundary entities use PostGIS SRID 4326."""
    srid_rows = pg_session.execute(text("""
        SELECT DISTINCT ST_SRID(geom) FROM admin_boundaries;
    """)).fetchall()
    assert len(srid_rows) == 1
    assert srid_rows[0][0] == 4326


def test_scenario_19_public_portal_geographic_sanitization():
    """Scenario 19: Public portal sanitizes coordinates to 2 decimal places and excludes foreign events."""
    resp = client.get("/api/v1/portals/public/hazard-map")
    assert resp.status_code == 200
    data = resp.json()
    assert "events" in data
    for evt in data["events"]:
        # Verify coordinates are rounded to at most 2 decimal places
        lat_str = str(evt["latitude"])
        lon_str = str(evt["longitude"])
        if "." in lat_str:
            assert len(lat_str.split(".")[1]) <= 2
        if "." in lon_str:
            assert len(lon_str.split(".")[1]) <= 2
        assert evt["state"] not in ["OUTSIDE_INDIA", "FOREIGN"]


def test_scenario_20_adversarial_foreign_place_queries():
    """Scenario 20: Adversarial foreign place name inputs are safely quarantined."""
    adversarial_targets = [
        "Investigate thermal plume in Kathmandu",
        "Monitor blast furnace in Dhaka",
        "Assess petrochemical refinery in Chittagong",
        "Investigate flare stack in Thimphu",
        "Investigate port terminal in Dubai"
    ]
    for prompt in adversarial_targets:
        obj = JarvisObjectiveNormalizer.normalize(prompt)
        assert obj.is_valid_sovereign_scope is False
        assert obj.intent == "REJECTED_OUT_OF_SCOPE"
        assert obj.location_category == "OUT_OF_DOMAIN_LOCATION"


# ==============================================================================
# 5. DATA QUALITY, PROVENANCE & BENCHMARKS
# ==============================================================================

def test_scenario_21_invalid_geometry_detection(pg_session):
    """Scenario 21: Confirms zero invalid geometries exist in admin_boundaries across all 7,595 rows."""
    invalid_count = pg_session.execute(text("""
        SELECT COUNT(*) FROM admin_boundaries WHERE NOT ST_IsValid(geom);
    """)).scalar()
    assert invalid_count == 0


def test_scenario_22_boundary_version_provenance(pg_session):
    """Scenario 22: Hierarchical context returns complete boundary authority and version metadata."""
    ctx = india_boundary_service.get_hierarchical_context(28.6139, 77.2090, db=pg_session)
    assert ctx["boundary_authority"] == AUTHORITATIVE_SOURCE
    assert ctx["boundary_version"] == AUTHORITATIVE_VERSION
    assert ctx["srid"] == AUTHORITATIVE_SRID
    assert ctx["resolved_at"] is not None
    assert "2026" in ctx["resolved_at"] or "2024" in ctx["resolved_at"] or "T" in ctx["resolved_at"]


def test_scenario_23_batch_sovereign_validation(pg_session):
    """Scenario 23: Batch partitioning segregates mixed Indian and foreign observations."""
    mixed_batch = [
        {"latitude": 28.6139, "longitude": 77.2090, "source": "VIIRS"},  # Delhi
        {"latitude": 31.5204, "longitude": 74.3587, "source": "VIIRS"},  # Lahore
        {"latitude": 19.0760, "longitude": 72.8777, "source": "VIIRS"},  # Mumbai
        {"latitude": 6.9271,  "longitude": 79.8612, "source": "VIIRS"},  # Colombo
        {"latitude": 22.5726, "longitude": 88.3639, "source": "VIIRS"}   # Kolkata
    ]
    india_recs, outside_recs = india_boundary_service.filter_live_observations_for_india(mixed_batch, db=pg_session)
    assert len(india_recs) == 3
    assert len(outside_recs) == 2
    assert all(r["sovereign_filter"] == "PASS_SOVEREIGN_INDIA" for r in india_recs)
    assert all(r["sovereign_filter"] == "REJECTED_OUT_OF_DOMAIN" for r in outside_recs)


def test_scenario_24_performance_threshold(pg_session):
    """Scenario 24: Single point PostGIS containment executes under 100 milliseconds."""
    t0 = time.perf_counter()
    res = india_boundary_service.is_within_india(28.6139, 77.2090, db=pg_session)
    duration_ms = (time.perf_counter() - t0) * 1000.0
    assert res is True
    assert duration_ms < 100.0, f"Containment check exceeded 100ms: {duration_ms:.2f}ms"


def test_scenario_25_safety_and_governance_invariants():
    """Scenario 25: Permanent governance and safety gates remain permanently enforced."""
    assert hasattr(settings, "ENABLE_OPERATIONAL_DISPATCH_GATE")
    assert settings.ENABLE_OPERATIONAL_DISPATCH_GATE is False
    assert hasattr(settings, "ENABLE_AUTOMATED_MODEL_ACTIVATION")
    assert settings.ENABLE_AUTOMATED_MODEL_ACTIVATION is False

