"""
AGNI-NETRA — Automated Test Suite for National Administrative Geography Layer (Phase 2A)
Validates boundaries, PostGIS geometries, hierarchy resolution, spatial enrichment, and APIs.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from backend.app.main import app
from backend.app.core.database import engine

client = TestClient(app)


def test_admin_boundaries_counts_and_hierarchy():
    """Verify official counts: 36 State/UTs, 735 Districts, 6,824 Sub-districts."""
    with engine.connect() as conn:
        counts = dict(conn.execute(text("""
            SELECT admin_level, COUNT(*) 
            FROM admin_boundaries 
            GROUP BY admin_level;
        """)).fetchall())

        assert counts.get(1) == 36, f"Expected 36 Level 1 State/UT boundaries, got {counts.get(1)}"
        assert counts.get(2) == 735, f"Expected 735 Level 2 District boundaries, got {counts.get(2)}"
        assert counts.get(3) == 6824, f"Expected 6,824 Level 3 Sub-district boundaries, got {counts.get(3)}"

        # Check total
        total = conn.execute(text("SELECT count(*) FROM admin_boundaries;")).scalar()
        assert total == 7595, f"Expected 7,595 total boundaries, got {total}"


def test_admin_boundaries_geometry_quality():
    """Verify 100% geometry validity and 0 empty geometries in PostGIS."""
    with engine.connect() as conn:
        res = conn.execute(text("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN ST_IsValid(geom) THEN 1 ELSE 0 END) as valid_count,
                SUM(CASE WHEN ST_IsEmpty(geom) THEN 1 ELSE 0 END) as empty_count,
                SUM(CASE WHEN ST_SRID(geom) = 4326 THEN 1 ELSE 0 END) as srid_4326_count
            FROM admin_boundaries;
        """)).fetchone()

        assert res[0] == 7595
        assert res[1] == 7595, f"Invalid geometries detected: {7595 - res[1]}"
        assert res[2] == 0, f"Empty geometries detected: {res[2]}"
        assert res[3] == 7595, f"Non-4326 SRID geometries detected: {7595 - res[3]}"


def test_admin_boundaries_hierarchy_completeness():
    """Verify parent-child hierarchy consistency across all levels."""
    with engine.connect() as conn:
        null_state_in_dists = conn.execute(text("""
            SELECT count(*) FROM admin_boundaries WHERE admin_level = 2 AND state_name IS NULL;
        """)).scalar()
        assert null_state_in_dists == 0, "Districts with NULL state_name found"

        null_state_in_subdists = conn.execute(text("""
            SELECT count(*) FROM admin_boundaries WHERE admin_level = 3 AND state_name IS NULL;
        """)).scalar()
        assert null_state_in_subdists == 0, "Sub-districts with NULL state_name found"

        null_dist_in_subdists = conn.execute(text("""
            SELECT count(*) FROM admin_boundaries WHERE admin_level = 3 AND district_name IS NULL;
        """)).scalar()
        assert null_dist_in_subdists == 0, "Sub-districts with NULL district_name found"


def test_facility_administrative_context():
    """Verify administrative context enrichment for 35,662 canonical facilities."""
    with engine.connect() as conn:
        total_fac = conn.execute(text("SELECT count(*) FROM industrial_facilities;")).scalar()
        enriched_fac = conn.execute(text("SELECT count(*) FROM facility_administrative_context;")).scalar()
        state_cov = conn.execute(text("SELECT count(*) FROM facility_administrative_context WHERE state_id IS NOT NULL;")).scalar()
        dist_cov = conn.execute(text("SELECT count(*) FROM facility_administrative_context WHERE district_id IS NOT NULL;")).scalar()
        subdist_cov = conn.execute(text("SELECT count(*) FROM facility_administrative_context WHERE subdistrict_id IS NOT NULL;")).scalar()

        assert enriched_fac >= 35662, f"Expected at least 35,662 enriched facilities, got {enriched_fac}"
        assert state_cov >= 35400, f"State coverage below expected threshold: {state_cov}"
        assert dist_cov >= 35400, f"District coverage below expected threshold: {dist_cov}"
        assert subdist_cov >= 34000, f"Sub-district coverage below expected threshold: {subdist_cov}"


def test_observation_administrative_context():
    """Verify observation administrative context for 1.77M+ thermal detections."""
    with engine.connect() as conn:
        enriched_obs = conn.execute(text("SELECT count(*) FROM observation_administrative_context;")).scalar()
        state_cov = conn.execute(text("SELECT count(*) FROM observation_administrative_context WHERE state_id IS NOT NULL;")).scalar()

        assert enriched_obs >= 1771000, f"Expected at least 1,771,000 enriched observations, got {enriched_obs}"
        assert state_cov >= 1640000, f"Observation state coverage below threshold: {state_cov}"



def test_parivesh_administrative_context():
    """Verify administrative context for 622 PARIVESH environmental clearance projects."""
    with engine.connect() as conn:
        total_p = conn.execute(text("SELECT count(*) FROM parivesh_projects_staging;")).scalar()
        enriched_p = conn.execute(text("SELECT count(*) FROM parivesh_administrative_context;")).scalar()
        spatial_p = conn.execute(text("SELECT count(*) FROM parivesh_administrative_context WHERE administrative_method = 'POSTGIS_SPATIAL_JOIN';")).scalar()
        source_p = conn.execute(text("SELECT count(*) FROM parivesh_administrative_context WHERE administrative_method = 'SOURCE_ATTRIBUTION';")).scalar()

        assert total_p == 622
        assert enriched_p == 622
        assert spatial_p + source_p == 622


def test_api_geography_states():
    """Test GET /api/v1/geography/states returns all 36 States/UTs."""
    response = client.get("/api/v1/geography/states")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 36
    state_names = [s["state_name"] for s in data]
    assert "Maharashtra" in state_names
    assert "Chhattisgarh" in state_names
    assert "Tamil Nadu" in state_names
    assert "Gujarat" in state_names


def test_api_geography_districts_filter():
    """Test GET /api/v1/geography/districts?state=Gujarat returns Gujarat districts."""
    response = client.get("/api/v1/geography/districts?state=Gujarat")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 30
    for d in data:
        assert d["state_name"] == "Gujarat"


def test_api_geography_reverse_lookup():
    """Test GET /api/v1/geography/lookup for Singrauli coordinates."""
    response = client.get("/api/v1/geography/lookup?latitude=24.199&longitude=82.665")
    assert response.status_code == 200
    data = response.json()
    assert data["state_name"] == "Madhya Pradesh"
    assert data["district_name"] == "Singrauli"
    assert data["match_method"] == "POSTGIS_SPATIAL_JOIN"
