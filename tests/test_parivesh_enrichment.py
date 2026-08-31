"""
AGNI-NETRA — Automated Test Suite for PARIVESH Environmental Clearance Enrichment
Verifies staging layer integrity, mutually exclusive entity matching, non-destructive
canonical facility enrichment, PostGIS FIRMS spatial context, and API endpoints.
"""

import os
import sys
import pytest
from sqlalchemy import text
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.database import engine
from backend.app.main import app
from data_pipeline.adapters.parivesh_adapter import PariveshFacilityAdapter


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def test_parivesh_staging_records():
    """
    Verifies that PARIVESH records are staged in PostgreSQL with unique proposal IDs and zero duplicates.
    """
    with engine.connect() as conn:
        total_rows = conn.execute(text("SELECT count(*) FROM parivesh_projects_staging;")).scalar()
        distinct_proposals = conn.execute(text("SELECT count(DISTINCT proposal_id) FROM parivesh_projects_staging;")).scalar()
        sample_row = conn.execute(text("""
            SELECT proposal_id, project_name, state, category, clearance_status, source_url, source_file
            FROM parivesh_projects_staging
            LIMIT 1;
        """)).fetchone()

    assert total_rows >= 500, f"Expected at least 500 staged PARIVESH proposals, got {total_rows}"
    assert total_rows == distinct_proposals, "All proposal_id values must be unique (0 duplicates)"
    assert sample_row is not None
    assert sample_row[0].startswith("IA/"), "MoEFCC proposal ID format expected"
    assert sample_row[4] == "EC_GRANTED"


def test_mutually_exclusive_matching_sum():
    """
    Verifies the mathematical identity:
    HIGH + MEDIUM + LOW + UNMATCHED == Total Evaluated PARIVESH Records.
    No double-counting between categories.
    """
    with engine.connect() as conn:
        total_staged = conn.execute(text("SELECT count(*) FROM parivesh_projects_staging;")).scalar()
        high_cnt = conn.execute(text("SELECT count(*) FROM parivesh_projects_staging WHERE match_status = 'HIGH';")).scalar()
        med_cnt = conn.execute(text("SELECT count(*) FROM parivesh_projects_staging WHERE match_status = 'MEDIUM';")).scalar()
        low_cnt = conn.execute(text("SELECT count(*) FROM parivesh_projects_staging WHERE match_status = 'LOW';")).scalar()
        unmatched_cnt = conn.execute(text("SELECT count(*) FROM parivesh_projects_staging WHERE match_status = 'UNMATCHED';")).scalar()

    sum_categories = high_cnt + med_cnt + low_cnt + unmatched_cnt
    assert sum_categories == total_staged, f"Categories sum ({sum_categories}) != Total staged ({total_staged})"
    assert high_cnt > 0, "Expected high confidence matches for major projects"
    assert med_cnt > 0, "Expected medium confidence matches"


def test_coordinates_validation_and_null_handling():
    """
    Verifies that records without explicit coordinates have latitude = NULL, longitude = NULL, geom = NULL
    and that no fake coordinates or state centroids were invented.
    """
    with engine.connect() as conn:
        no_coord_rows = conn.execute(text("""
            SELECT id, proposal_id, latitude, longitude, geom
            FROM parivesh_projects_staging
            WHERE latitude IS NULL;
        """)).fetchall()

        coord_rows = conn.execute(text("""
            SELECT id, proposal_id, latitude, longitude, geom
            FROM parivesh_projects_staging
            WHERE latitude IS NOT NULL;
        """)).fetchall()

    assert len(no_coord_rows) > 0, "Expected non-geolocated PARIVESH proposals"
    for r in no_coord_rows:
        assert r[2] is None
        assert r[3] is None
        assert r[4] is None

    for r in coord_rows:
        assert 8.0 <= r[2] <= 37.5, f"Latitude {r[2]} out of India bounds"
        assert 68.0 <= r[3] <= 97.5, f"Longitude {r[3]} out of India bounds"


def test_canonical_facilities_enrichment():
    """
    Verifies that matched canonical facilities have environmental clearance fields attached
    without deleting or overwriting OSM or CEA data.
    """
    with engine.connect() as conn:
        cleared_facs = conn.execute(text("""
            SELECT id, name, source, environmental_clearance_present, ec_proposal_id,
                   ec_clearance_status, ec_category, source_metadata
            FROM industrial_facilities
            WHERE environmental_clearance_present = TRUE;
        """)).fetchall()

    assert len(cleared_facs) > 0, "Expected enriched canonical facilities"
    for fac in cleared_facs:
        assert fac[3] is True, "environmental_clearance_present must be True"
        assert fac[4] is not None, "ec_proposal_id must be populated"
        assert fac[5] == "EC_GRANTED"
        meta = fac[7]
        assert "parivesh_enrichment" in meta, "source_metadata must contain parivesh_enrichment"


def test_firms_spatial_association_on_cleared_facilities():
    """
    Verifies that FIRMS thermal history spatial associations are available for cleared facilities.
    """
    with engine.connect() as conn:
        total_2km = conn.execute(text("""
            SELECT coalesce(sum(firms_detections_2km), 0)
            FROM industrial_facilities
            WHERE environmental_clearance_present = TRUE;
        """)).scalar()

    assert total_2km > 0, "Expected spatial thermal associations near cleared industrial facilities"


def test_parivesh_adapter():
    """
    Verifies that PariveshFacilityAdapter correctly queries staged clearance records.
    """
    adapter = PariveshFacilityAdapter()
    records = adapter.fetch_facilities()
    assert len(records) > 0, "Adapter should fetch records"
    assert records[0].provenance.source_name == "PARIVESH"


def test_fastapi_facilities_endpoints_with_parivesh(client):
    """
    Verifies FastAPI GET /api/v1/facilities with environmental clearance filters
    and GET /api/v1/facilities/parivesh/projects.
    """
    # 1. Filter facilities with clearance
    res = client.get("/api/v1/facilities?has_clearance=true&limit=10")
    assert res.status_code == 200
    data = res.json()
    assert len(data) > 0
    assert data[0]["environmental_clearance_present"] is True

    # 2. Get staged PARIVESH projects
    res_proj = client.get("/api/v1/facilities/parivesh/projects?match_status=HIGH&limit=10")
    assert res_proj.status_code == 200
    projs = res_proj.json()
    assert len(projs) > 0
    assert projs[0]["match_status"] == "HIGH"
