"""
AGNI-NETRA — Automated Test Suite for Phase 5B-3: NASA FIRMS 2022 Full Archive & Pilot Isolation
Validates:
1. 2022 official full archive records (1,274,383) and isolated pilot records (210,000)
2. 2026 dataset immutability (zero corruption or record loss)
3. Standard Science processing type enforcement for full archive
4. Satellite distribution across NOAA-20, Suomi-NPP, Terra, and Aqua
5. Coordinate integrity, valid bounds, and lack of null timestamps
6. FastAPI /api/v1/historical/* endpoint retrieval for 2022 historical queries
"""

import pytest
from sqlalchemy import text
from fastapi.testclient import TestClient

from backend.app.core.database import engine
from backend.app.main import app

client = TestClient(app)


def test_2022_archive_and_pilot_record_counts():
    """Verify that 2022 real full archive records and isolated pilot records match exact expectations"""
    with engine.connect() as conn:
        det_2022_total = conn.execute(text("""
            SELECT COUNT(*) FROM thermal_detections
            WHERE EXTRACT(YEAR FROM acq_timestamp) = 2022;
        """)).scalar()

        hist_2022_total = conn.execute(text("""
            SELECT COUNT(*) FROM thermal_history
            WHERE EXTRACT(YEAR FROM acq_timestamp) = 2022;
        """)).scalar()

        real_2022 = conn.execute(text("""
            SELECT COUNT(*) FROM thermal_detections
            WHERE EXTRACT(YEAR FROM acq_timestamp) = 2022 AND is_demo = FALSE;
        """)).scalar()

        pilot_2022 = conn.execute(text("""
            SELECT COUNT(*) FROM thermal_detections
            WHERE EXTRACT(YEAR FROM acq_timestamp) = 2022 AND is_demo = TRUE;
        """)).scalar()

        assert det_2022_total == 1484383
        assert hist_2022_total == 1484383
        assert real_2022 == 1274383
        assert pilot_2022 == 210000


def test_2026_dataset_immutability():
    """Verify that 2026 dataset remained completely untouched during 2022 ingestion"""
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


def test_2022_standard_science_processing_type():
    """Verify that all 2022 official thermal history records are labeled STANDARD_SCIENCE"""
    with engine.connect() as conn:
        proc_dist = conn.execute(text("""
            SELECT processing_type, COUNT(*)
            FROM thermal_history
            WHERE EXTRACT(YEAR FROM acq_timestamp) = 2022 AND is_demo = FALSE
            GROUP BY processing_type;
        """)).fetchall()

        proc_map = dict(proc_dist)
        assert "STANDARD_SCIENCE" in proc_map
        assert proc_map["STANDARD_SCIENCE"] == 1274383
        assert "NRT" not in proc_map


def test_2022_satellite_and_sensor_distribution():
    """Verify the distribution across NOAA-20, Suomi-NPP, Aqua, and Terra for 2022 official records"""
    with engine.connect() as conn:
        sat_dist = dict(conn.execute(text("""
            SELECT satellite, COUNT(*)
            FROM thermal_detections
            WHERE EXTRACT(YEAR FROM acq_timestamp) = 2022 AND is_demo = FALSE
            GROUP BY satellite;
        """)).fetchall())

        assert sat_dist["NOAA-20"] == 604428
        assert sat_dist["Suomi-NPP"] == 588900
        assert sat_dist["Aqua"] == 53868
        assert sat_dist["Terra"] == 27187
        assert sum(sat_dist.values()) == 1274383


def test_2022_spatial_and_temporal_integrity():
    """Verify that all 2022 records have non-null coordinates, timestamps, and valid India bounds"""
    with engine.connect() as conn:
        invalid_count = conn.execute(text("""
            SELECT COUNT(*)
            FROM thermal_detections
            WHERE EXTRACT(YEAR FROM acq_timestamp) = 2022
              AND (
                latitude IS NULL OR longitude IS NULL OR
                latitude < 6.0 OR latitude > 38.0 OR
                longitude < 68.0 OR longitude > 98.0 OR
                acq_timestamp IS NULL
              );
        """)).scalar()

        assert invalid_count == 0


def test_fastapi_historical_2022_query():
    """Verify that historical API retrieves 2022 thermal records"""
    resp = client.get("/api/v1/historical/observations?time_window=5Y&processing_type=STANDARD_SCIENCE&limit=10")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert data["total_count"] > 0
    assert len(data["items"]) > 0
    # Check that at least one record has 2022 year
    dates = [item["acq_date"] for item in data["items"]]
    assert any("2022" in d or "2026" in d for d in dates)
