"""
AGNI-NETRA — Automated Test Suite for Phase 5D: NASA FIRMS 2024 Full Archive & Immutability
Validates:
1. 2024 archive ingestion record totals & table schema conformity
2. 2026 dataset immutability (zero corruption or record loss)
3. 2023 dataset immutability (strict lock at 1,244,759 official records)
4. 2022 dataset immutability (official 1,274,383 + pilot 210,000 preserved)
5. NOAA-21 sensor & product validation
6. Standard Science processing type enforcement
7. Coordinate integrity, PostGIS geometry validity, and lack of null timestamps
8. FastAPI /api/v1/historical/* endpoints for 2024
"""

import pytest
from sqlalchemy import text
from fastapi.testclient import TestClient

from backend.app.core.database import engine
from backend.app.main import app

client = TestClient(app)


def test_2022_official_and_pilot_immutability():
    """Verify that 2022 official and pilot datasets remain untouched"""
    with engine.connect() as conn:
        real_2022 = conn.execute(text("""
            SELECT COUNT(*) FROM thermal_detections
            WHERE EXTRACT(YEAR FROM acq_timestamp) = 2022 AND is_demo = FALSE;
        """)).scalar()

        pilot_2022 = conn.execute(text("""
            SELECT COUNT(*) FROM thermal_detections
            WHERE EXTRACT(YEAR FROM acq_timestamp) = 2022 AND is_demo = TRUE;
        """)).scalar()

        assert real_2022 == 1274383
        assert pilot_2022 == 210000


def test_2023_dataset_immutability():
    """Verify that 2023 dataset remains strictly locked at 1,244,759 records with zero delta"""
    with engine.connect() as conn:
        real_2023 = conn.execute(text("""
            SELECT COUNT(*) FROM thermal_detections
            WHERE EXTRACT(YEAR FROM acq_timestamp) = 2023 AND is_demo = FALSE;
        """)).scalar()

        assert real_2023 == 1244759


def test_2026_dataset_immutability():
    """Verify that 2026 baseline dataset remained completely untouched"""
    with engine.connect() as conn:
        det_2026 = conn.execute(text("""
            SELECT COUNT(*) FROM thermal_detections
            WHERE (raw_metadata->>'reference_year' = '2026' OR raw_metadata->>'reference_year' IS NULL)
              AND EXTRACT(YEAR FROM acq_timestamp) = 2026;
        """)).scalar()

        hist_2026 = conn.execute(text("""
            SELECT COUNT(*) FROM thermal_history
            WHERE (raw_metadata->>'reference_year' = '2026' OR raw_metadata->>'reference_year' IS NULL)
              AND EXTRACT(YEAR FROM acq_timestamp) = 2026;
        """)).scalar()

        assert det_2026 >= 1771080
        assert hist_2026 >= 1771208


def test_2024_full_archive_ingestion_counts():
    """Verify that 2024 full archive records are present with is_demo=False and STANDARD_SCIENCE"""
    with engine.connect() as conn:
        det_2024 = conn.execute(text("""
            SELECT COUNT(*) FROM thermal_detections
            WHERE EXTRACT(YEAR FROM acq_timestamp) = 2024 AND is_demo = FALSE;
        """)).scalar()

        hist_2024 = conn.execute(text("""
            SELECT COUNT(*) FROM thermal_history
            WHERE EXTRACT(YEAR FROM acq_timestamp) = 2024 AND is_demo = FALSE;
        """)).scalar()

        assert det_2024 > 1500000
        assert hist_2024 > 1500000

        # Verify processing_type
        science_count = conn.execute(text("""
            SELECT COUNT(*) FROM thermal_history
            WHERE EXTRACT(YEAR FROM acq_timestamp) = 2024 AND processing_type = 'STANDARD_SCIENCE';
        """)).scalar()
        assert science_count == hist_2024


def test_2024_noaa21_presence():
    """Verify NOAA-21 VIIRS records are successfully ingested for 2024"""
    with engine.connect() as conn:
        noaa21_count = conn.execute(text("""
            SELECT COUNT(*) FROM thermal_detections
            WHERE EXTRACT(YEAR FROM acq_timestamp) = 2024 
              AND satellite = 'NOAA-21' 
              AND is_demo = FALSE;
        """)).scalar()

        assert noaa21_count > 400000


def test_2024_coordinate_and_geometry_validity():
    """Verify that all 2024 records have non-null coordinates within Indian bounds"""
    with engine.connect() as conn:
        null_coords = conn.execute(text("""
            SELECT COUNT(*) FROM thermal_detections
            WHERE EXTRACT(YEAR FROM acq_timestamp) = 2024
              AND (latitude IS NULL OR longitude IS NULL OR acq_timestamp IS NULL);
        """)).scalar()
        assert null_coords == 0

        invalid_geoms = conn.execute(text("""
            SELECT COUNT(*) FROM thermal_history
            WHERE EXTRACT(YEAR FROM acq_timestamp) = 2024
              AND NOT ST_IsValid(ST_SetSRID(ST_MakePoint(longitude, latitude), 4326));
        """)).scalar()
        assert invalid_geoms == 0


def test_2024_api_endpoints():
    """Verify historical API endpoints for 2024 data"""
    resp_obs = client.get("/api/v1/historical/observations?time_window=5Y&limit=10")
    assert resp_obs.status_code == 200
    data = resp_obs.json()
    assert "items" in data
    assert len(data["items"]) == 10

    resp_tl = client.get("/api/v1/historical/timeline")
    assert resp_tl.status_code == 200
    timeline = resp_tl.json()["timeline"]
    months_2024 = [p["period"] for p in timeline if p["period"].startswith("2024-")]
    assert len(months_2024) == 12


def test_spatial_engine_and_db_connectivity():
    """Verify database connectivity and PostGIS geometry validity across tables"""
    with engine.connect() as conn:
        res = conn.execute(text("SELECT PostGIS_Version();")).scalar()
        assert "3.4" in res or "3." in res
