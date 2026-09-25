"""
AGNI-NETRA — Targeted Regression Suite: Spatial Context Query & Transaction Recovery

Validates:
1. Coordinates-based PostGIS queries on industrial_facilities without requiring a 'geom' column.
2. ST_MakePoint(longitude, latitude) order with SRID 4326 and geography casts.
3. Safe exclusion of NULL coordinates.
4. Savepoint isolation (with db.begin_nested()) ensuring transaction recovery from subquery failure.
"""

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session
from backend.app.core.database import SessionLocal
from backend.app.services.intelligence.india_intelligence_service import india_intelligence_service


@pytest.fixture(scope="module")
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_01_industrial_facilities_schema_contract(db: Session):
    """Prove industrial_facilities uses latitude/longitude and does NOT require 'geom'."""
    cols = db.execute(text("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'industrial_facilities';
    """)).scalars().all()

    assert "latitude" in cols, "industrial_facilities must have 'latitude' column"
    assert "longitude" in cols, "industrial_facilities must have 'longitude' column"
    assert "geom" not in cols, "industrial_facilities must NOT have 'geom' column"


def test_02_spatial_makepoint_order_and_distance_contract(db: Session):
    """Prove ST_MakePoint uses (longitude, latitude), SRID 4326, ST_DWithin, and ST_Distance."""
    # Target coordinate near known facility '00078a6b-e673-4bb4-9d6b-f09678e46a47'
    # Coordinates in DB: lon = 75.2990042, lat = 19.7127408
    target_lat = 19.7127408
    target_lon = 75.2990042

    fac_sql = """
        SELECT id, name, master_sector,
               ROUND(ST_Distance(
                   ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)::geography,
                   ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography
               )::numeric, 0) as dist_m
        FROM industrial_facilities
        WHERE latitude IS NOT NULL AND longitude IS NOT NULL
          AND ST_DWithin(
              ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)::geography,
              ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography,
              10000
          )
        ORDER BY ST_Distance(
            ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)::geography,
            ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography
        )
        LIMIT 1;
    """

    row = db.execute(text(fac_sql), {"lat": target_lat, "lon": target_lon}).mappings().first()
    assert row is not None, "Spatial lookup must return nearest facility"
    assert row["id"] == "00078a6b-e673-4bb4-9d6b-f09678e46a47"
    assert int(row["dist_m"]) == 0, f"Distance to exact coordinate must be 0m, got {row['dist_m']}m"


def test_03_null_coordinates_exclusion(db: Session):
    """Prove NULL coordinates are safely filtered and do not crash PostGIS functions."""
    null_count = db.execute(text("""
        SELECT count(*)
        FROM industrial_facilities
        WHERE latitude IS NULL OR longitude IS NULL;
    """)).scalar()
    assert null_count > 0, "Database must contain staging facilities with NULL coordinates"

    # Ensure query executes cleanly with NULL exclusion
    fac_sql = """
        SELECT count(*)
        FROM industrial_facilities
        WHERE latitude IS NOT NULL AND longitude IS NOT NULL
          AND ST_DWithin(
              ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)::geography,
              ST_SetSRID(ST_MakePoint(75.0, 20.0), 4326)::geography,
              100000
          );
    """
    count = db.execute(text(fac_sql)).scalar()
    assert count >= 0, "Query with NULL filter must execute without PostGIS error"


def test_04_find_nearest_context_real_record(db: Session):
    """Prove _find_nearest_context returns valid context matching actual Supabase schema."""
    target_lat = 19.7127408
    target_lon = 75.2990042
    event_state = "Maharashtra"

    ctx = india_intelligence_service._find_nearest_context(db, target_lat, target_lon, event_state)
    assert ctx is not None
    assert isinstance(ctx, dict)
    assert "osm_industrial" in ctx
    assert ctx["osm_industrial"] is not None
    assert ctx["osm_industrial"]["facility_id"] == "00078a6b-e673-4bb4-9d6b-f09678e46a47"
    assert ctx["osm_industrial"]["distance_m"] == 0


def test_05_transaction_recovery_from_subquery_failure(db: Session):
    """
    Prove that a subquery failure inside begin_nested() is isolated to a SAVEPOINT,
    leaving the parent SQLAlchemy transaction healthy and fully usable.
    """
    # 1. Initial query on session
    initial_check = db.execute(text("SELECT 1;")).scalar()
    assert initial_check == 1

    # 2. Simulate an intentional SQL syntax / relation error inside begin_nested()
    failed = False
    try:
        with db.begin_nested():
            # Deliberately attempt invalid query that would trigger UndefinedTable/UndefinedColumn
            db.execute(text("SELECT * FROM non_existent_table_for_savepoint_test;"))
    except Exception:
        failed = True

    assert failed is True, "Intentional subquery error must raise an exception in Python"

    # 3. CRITICAL: Prove parent session is NOT in InFailedSqlTransaction state
    # Prior to the fix, this query would crash with psycopg2.errors.InFailedSqlTransaction
    subsequent_count = db.execute(text("SELECT count(*) FROM industrial_facilities;")).scalar()
    assert subsequent_count == 35684, f"Parent session must remain healthy and queryable, got {subsequent_count}"


def test_06_find_nearest_context_preserves_parent_session(db: Session):
    """Prove calling _find_nearest_context never leaves the parent session in aborted state."""
    # Call _find_nearest_context with arbitrary coordinates
    ctx = india_intelligence_service._find_nearest_context(db, 28.6139, 77.2090, "Delhi")
    assert isinstance(ctx, dict)

    # Verify session can execute further queries immediately
    healthy_check = db.execute(text("SELECT count(*) FROM admin_boundaries;")).scalar()
    assert healthy_check == 7595, "Parent session must remain healthy after _find_nearest_context"


def test_07_gis_facilities_geojson_boolean_contract(db: Session):
    """
    Prove /api/v1/gis/industrial-facilities query handles PostgreSQL boolean column
    environmental_clearance_present without 'operator does not exist: boolean = integer' error.
    """
    from fastapi.testclient import TestClient
    from backend.app.main import app

    client = TestClient(app)
    res = client.get("/api/v1/gis/industrial-facilities?limit=10&bbox=75.0,19.0,76.0,20.0")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    data = res.json()
    assert data["type"] == "FeatureCollection"
    assert "features" in data
    assert len(data["features"]) > 0
    first_feat = data["features"][0]
    assert first_feat["geometry"]["type"] == "Point"
    coords = first_feat["geometry"]["coordinates"]
    assert 68.0 <= coords[0] <= 97.5, "GeoJSON coordinate 0 must be longitude (X)"
    assert 6.0 <= coords[1] <= 37.5, "GeoJSON coordinate 1 must be latitude (Y)"


def test_08_alert_dossier_resilience(db: Session):
    """
    Prove /api/v1/alerts/{alert_id}/dossier generates full multi-layer investigation dossier
    resiliently without crashing if alert_audit_logs is absent.
    """
    from fastapi.testclient import TestClient
    from backend.app.main import app
    from backend.app.models.domain import Alert
    from backend.app.services.alert_workflow_service import alert_workflow_service

    alert = db.query(Alert).first()
    assert alert is not None, "Database must contain at least one alert"

    # 1. Direct Service Call
    dossier = alert_workflow_service.get_alert_investigation_dossier(db, alert.id)
    assert "alert_metadata" in dossier
    assert "thermal_event" in dossier
    assert "evidence_sources" in dossier
    assert "audit_trail" in dossier
    assert isinstance(dossier["audit_trail"], list)

    # 2. Authenticated API Call
    client = TestClient(app)
    login_res = client.post("/api/v1/auth/login", data={"username": "analyst@agninetra.gov.in", "password": "AnalystPassword123!"})
    if login_res.status_code == 200:
        token = login_res.json()["access_token"]
        res = client.get(f"/api/v1/alerts/{alert.id}/dossier", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
