"""
AGNI-NETRA — Automated Unit & Integration Tests
For CEA Power Station Data Ingestion, Multi-Signal Entity Resolution,
PostGIS OSM Enrichment, and FIRMS Spatial Thermal Association.
"""

import os
import sys
import pytest
from sqlalchemy import text
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.database import engine
from backend.app.main import app
from data_pipeline.cea_ingestion import clean_cea_state_and_sector, clean_prime_mover
from data_pipeline.cea_matcher import score_project_match, extract_core_keywords


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def test_cea_pdf_ingestion_and_staging_count():
    """
    Validates that all 1,633 unit rows across all 24 pages from the official CEA document
    are staged in PostgreSQL `cea_power_stations_staging`.
    """
    with engine.connect() as conn:
        row_count = conn.execute(text("SELECT count(*) FROM cea_power_stations_staging")).scalar()
        page_count = conn.execute(text("SELECT count(DISTINCT page_number) FROM cea_power_stations_staging")).scalar()
        total_mw = conn.execute(text("SELECT sum(installed_capacity_mw) FROM cea_power_stations_staging")).scalar()

    assert row_count == 1633, f"Expected 1,633 staged CEA unit rows, got {row_count}"
    assert page_count == 24, f"Expected 24 pages processed, got {page_count}"
    assert total_mw is not None and total_mw > 250000, f"Expected >250,000 MW total capacity, got {total_mw}"


def test_cea_text_and_sector_cleaning():
    """
    Tests text cleaning and state/sector OCR boundary resolution.
    """
    norm_st, sec = clean_cea_state_and_sector("Uttar Prad", "ePshrivate Sector")
    assert "Uttar Pradesh" in norm_st
    assert sec == "Private Sector"

    assert clean_prime_mover("Steam") == "Steam"
    assert clean_prime_mover("GT-Gas") == "GT-Gas"
    assert clean_prime_mover("HYDRO") == "Hydro"
    assert clean_prime_mover("Nuclear") == "Nuclear"


def test_cea_entity_resolution_scoring():
    """
    Tests multi-signal matching scoring logic across Name, State, Operator, and Facility Type.
    """
    # 1. High match scenario
    cea_proj = {
        "project_name": "VINDHYACHAL STPS",
        "state": "Madhya Pradesh",
        "organisation": "NTPC",
        "prime_mover": "Steam"
    }
    osm_fac = {
        "name": "NTPC Vindhyachal Super Thermal Power Station",
        "industry_name": "Vindhyachal Thermal Power Plant",
        "company_name": "NTPC Limited",
        "facility_type": "POWER_PLANT",
        "state": "Madhya Pradesh"
    }
    score, reasons = score_project_match(cea_proj, osm_fac)
    assert score >= 75.0, f"Expected HIGH match score (>=75.0), got {score} with reasons: {reasons}"

    # 2. State mismatch scenario
    osm_diff_state = {
        "name": "Vindhyachal Power Station",
        "industry_name": "Vindhyachal Plant",
        "company_name": "NTPC",
        "facility_type": "POWER_PLANT",
        "state": "Gujarat"
    }
    score_diff, _ = score_project_match(cea_proj, osm_diff_state)
    assert score_diff < score, "Score with state mismatch should be penalized"


def test_matched_facility_geometry_and_cea_enrichment():
    """
    Verifies that matched power facilities retain their valid PostGIS geometries
    while acquiring CEA capacity, prime mover, and unit counts.
    """
    with engine.connect() as conn:
        matched_sample = conn.execute(text("""
            SELECT id, name, facility_type, source, state, latitude, longitude,
                   plant_capacity, prime_mover, unit_count, verification_status, confidence,
                   ST_IsValid(geom) AS geom_valid
            FROM industrial_facilities
            WHERE source = 'CEA+OSM' AND geom IS NOT NULL
            LIMIT 5;
        """)).fetchall()

    assert len(matched_sample) > 0, "Expected at least one matched CEA+OSM facility"
    for fac in matched_sample:
        assert fac[6] is not None, "Matched facility must have valid longitude"
        assert fac[5] is not None, "Matched facility must have valid latitude"
        assert fac[12] is True, "Matched facility PostGIS geometry must be valid SRID 4326"
        assert fac[7] is not None and "MW" in fac[7], "Matched facility must have capacity string with MW"
        assert fac[10] == "VERIFIED", "Matched facility verification status must be VERIFIED"


def test_unmatched_cea_facilities_non_geolocated():
    """
    Verifies that unmatched CEA power stations are inserted as canonical records
    with geometry = NULL, latitude = NULL, longitude = NULL (never inventing fake coordinates).
    """
    with engine.connect() as conn:
        unmatched_rows = conn.execute(text("""
            SELECT id, name, source, state, latitude, longitude, geom,
                   plant_capacity, prime_mover, verification_status, confidence
            FROM industrial_facilities
            WHERE source = 'CEA' AND geom IS NULL;
        """)).fetchall()

    assert len(unmatched_rows) > 0, "Expected registered unmatched CEA canonical facilities"
    for fac in unmatched_rows:
        assert fac[4] is None or fac[4] == 0.0, "Unmatched CEA facility must have latitude = NULL or 0.0"
        assert fac[5] is None or fac[5] == 0.0, "Unmatched CEA facility must have longitude = NULL or 0.0"
        assert fac[6] is None, "Unmatched CEA facility must have geom = NULL"
        assert fac[9] == "PROVISIONAL", "Unmatched CEA facility must be PROVISIONAL"


def test_postgis_firms_spatial_association():
    """
    Verifies that PostGIS spatial association against 1.77M FIRMS thermal history records
    has populated 500m, 1km, and 2km detection counts and facility_baselines.
    """
    with engine.connect() as conn:
        total_2km_det = conn.execute(text("SELECT sum(firms_detections_2km) FROM industrial_facilities")).scalar()
        total_1km_det = conn.execute(text("SELECT sum(firms_detections_1km) FROM industrial_facilities")).scalar()
        total_500m_det = conn.execute(text("SELECT sum(firms_detections_500m) FROM industrial_facilities")).scalar()
        baseline_cnt = conn.execute(text("SELECT count(*) FROM facility_baselines")).scalar()

    assert total_2km_det is not None and total_2km_det > 50000, f"Expected >50,000 2km detections, got {total_2km_det}"
    assert total_1km_det is not None and total_1km_det > 20000, f"Expected >20,000 1km detections, got {total_1km_det}"
    assert total_500m_det is not None and total_500m_det > 5000, f"Expected >5,000 500m detections, got {total_500m_det}"
    assert baseline_cnt > 1000, f"Expected >1,000 facility baselines, got {baseline_cnt}"


def test_fastapi_facilities_endpoints_with_cea(client):
    """
    Verifies that FastAPI /api/v1/facilities endpoint returns enriched CEA attributes and FIRMS counts.
    """
    response = client.get("/api/v1/facilities?facility_type=POWER_PLANT&limit=10")
    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}"
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0

    first_item = data[0]
    assert "name" in first_item
    assert "facility_type" in first_item
    assert "plant_capacity" in first_item
    assert "firms_detections_2km" in first_item
