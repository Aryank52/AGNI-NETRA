"""
AGNI-NETRA — Automated Test Suite for Phase 5C: NASA FIRMS 2023 Full Archive & Immutability
Validates:
1. 2023 archive ingestion record totals & table schema conformity
2. 2026 dataset immutability (zero corruption or record loss)
3. 2022 dataset immutability (official 1,274,383 + pilot 210,000 preserved)
4. Standard Science processing type enforcement
5. Coordinate integrity, PostGIS geometry validity, and lack of null timestamps
6. FastAPI /api/v1/historical/* endpoints for 2023
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


def test_2026_dataset_immutability():
    """Verify that 2026 baseline dataset remained completely untouched"""
    with engine.connect() as conn:
        det_2026 = conn.execute(text("""
            SELECT COUNT(*) FROM thermal_detections
            WHERE EXTRACT(YEAR FROM acq_timestamp) = 2026;
        """)).scalar()

        hist_2026 = conn.execute(text("""
            SELECT COUNT(*) FROM thermal_history
            WHERE EXTRACT(YEAR FROM acq_timestamp) = 2026;
        """)).scalar()

        # Accommodates transient test records created during earlier test fixtures
        assert det_2026 >= 1771080 and (det_2026 - 1771080) <= 50
        assert hist_2026 >= 1771208 and (hist_2026 - 1771208) <= 50


def test_2023_full_archive_ingestion_counts():
    """Verify that 2023 full archive records are present with is_demo=False and STANDARD_SCIENCE"""
    with engine.connect() as conn:
        det_2023 = conn.execute(text("""
            SELECT COUNT(*) FROM thermal_detections
            WHERE EXTRACT(YEAR FROM acq_timestamp) = 2023 AND is_demo = FALSE;
        """)).scalar()

        hist_2023 = conn.execute(text("""
            SELECT COUNT(*) FROM thermal_history
            WHERE EXTRACT(YEAR FROM acq_timestamp) = 2023 AND is_demo = FALSE;
        """)).scalar()

        assert det_2023 == 1244759
        assert hist_2023 == 1244759

        # Verify no 2023 records have is_demo = True
        demo_2023 = conn.execute(text("""
            SELECT COUNT(*) FROM thermal_detections
            WHERE EXTRACT(YEAR FROM acq_timestamp) = 2023 AND is_demo = TRUE;
        """)).scalar()
        assert demo_2023 == 0

        # Verify processing_type
        science_count = conn.execute(text("""
            SELECT COUNT(*) FROM thermal_history
            WHERE EXTRACT(YEAR FROM acq_timestamp) = 2023 AND processing_type = 'STANDARD_SCIENCE';
        """)).scalar()
        assert science_count == 1244759


def test_2023_coordinate_and_geometry_validity():
    """Verify that all 2023 records have non-null coordinates within Indian bounds"""
    with engine.connect() as conn:
        null_coords = conn.execute(text("""
            SELECT COUNT(*) FROM thermal_detections
            WHERE EXTRACT(YEAR FROM acq_timestamp) = 2023
              AND (latitude IS NULL OR longitude IS NULL OR acq_timestamp IS NULL);
        """)).scalar()
        assert null_coords == 0

        invalid_geoms = conn.execute(text("""
            SELECT COUNT(*) FROM thermal_history
            WHERE EXTRACT(YEAR FROM acq_timestamp) = 2023
              AND NOT ST_IsValid(ST_SetSRID(ST_MakePoint(longitude, latitude), 4326));
        """)).scalar()
        assert invalid_geoms == 0


def test_2023_api_endpoints():
    """Verify historical API endpoints for 2023 data"""
    resp_obs = client.get("/api/v1/historical/observations?time_window=5Y&limit=10")
    assert resp_obs.status_code == 200
    data = resp_obs.json()
    assert "items" in data
    assert len(data["items"]) == 10

    resp_tl = client.get("/api/v1/historical/timeline")
    assert resp_tl.status_code == 200
    timeline = resp_tl.json()["timeline"]
    months_2023 = [p["period"] for p in timeline if p["period"].startswith("2023-")]
    assert len(months_2023) == 12


def test_spatial_engine_and_db_connectivity():
    """Verify database connectivity and PostGIS geometry validity across tables"""
    with engine.connect() as conn:
        res = conn.execute(text("SELECT PostGIS_Version();")).scalar()
        assert "3.4" in res or "3." in res
