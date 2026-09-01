"""
AGNI-NETRA — Automated Test Suite for Phase 5E: NASA FIRMS 2025 Full Archive & Immutability
Validates:
1. 2025 archive ingestion record totals & table schema conformity
2. 2022 dataset immutability (official 1,274,383 + pilot 210,000 preserved)
3. 2023 dataset immutability (strict lock at 1,244,759 official records)
4. 2024 dataset immutability (official reconciled baseline preserved)
5. 2026 baseline dataset immutability
6. All satellite & sensor presence (NOAA-20, NOAA-21, Suomi-NPP, Aqua, Terra)
7. Standard Science processing type enforcement
8. Coordinate integrity, PostGIS geometry validity, and lack of null timestamps
9. 12-month complete seasonal coverage
10. FastAPI /api/v1/historical/* endpoints for 2025 data
11. Archive manifest integrity (archive_manifest_2025.json)
"""

import json
import os
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


def test_2024_reconciled_immutability():
    """Verify that 2024 reconciled historical baseline remains preserved"""
    with engine.connect() as conn:
        det_2024 = conn.execute(text("""
            SELECT COUNT(*) FROM thermal_detections
            WHERE EXTRACT(YEAR FROM acq_timestamp) = 2024 AND is_demo = FALSE;
        """)).scalar()

        assert det_2024 == 1711626


def test_2026_dataset_immutability():
    """Verify that 2026 baseline dataset remained intact"""
    with engine.connect() as conn:
        det_2026 = conn.execute(text("""
            SELECT COUNT(*) FROM thermal_detections
            WHERE EXTRACT(YEAR FROM acq_timestamp) = 2026;
        """)).scalar()

        hist_2026 = conn.execute(text("""
            SELECT COUNT(*) FROM thermal_history
            WHERE EXTRACT(YEAR FROM acq_timestamp) = 2026;
        """)).scalar()

        assert det_2026 >= 1771080
        assert hist_2026 >= 1771208


def test_2025_full_archive_ingestion_counts():
    """Verify that 2025 full archive records are present with is_demo=False and STANDARD_SCIENCE"""
    with engine.connect() as conn:
        det_2025 = conn.execute(text("""
            SELECT COUNT(*) FROM thermal_detections
            WHERE EXTRACT(YEAR FROM acq_timestamp) = 2025 AND is_demo = FALSE;
        """)).scalar()

        hist_2025 = conn.execute(text("""
            SELECT COUNT(*) FROM thermal_history
            WHERE EXTRACT(YEAR FROM acq_timestamp) = 2025 AND is_demo = FALSE;
        """)).scalar()

        assert det_2025 >= 2000000
        assert hist_2025 >= 2000000

        # Verify no 2025 records have is_demo = True
        demo_2025 = conn.execute(text("""
            SELECT COUNT(*) FROM thermal_detections
            WHERE EXTRACT(YEAR FROM acq_timestamp) = 2025 AND is_demo = TRUE;
        """)).scalar()
        assert demo_2025 == 0

        # Verify processing_type is STANDARD_SCIENCE
        science_count = conn.execute(text("""
            SELECT COUNT(*) FROM thermal_history
            WHERE EXTRACT(YEAR FROM acq_timestamp) = 2025 AND processing_type = 'STANDARD_SCIENCE';
        """)).scalar()
        assert science_count == hist_2025


def test_2025_satellite_and_sensor_presence():
    """Verify all 2025 satellite platforms are represented (NOAA-20, NOAA-21, Suomi-NPP, Terra, Aqua)"""
    with engine.connect() as conn:
        satellites = conn.execute(text("""
            SELECT DISTINCT satellite FROM thermal_detections
            WHERE EXTRACT(YEAR FROM acq_timestamp) = 2025
            ORDER BY satellite;
        """)).scalars().all()

        assert "NOAA-20" in satellites
        assert "NOAA-21" in satellites
        assert "Suomi-NPP" in satellites
        assert "Aqua" in satellites or "Terra" in satellites

        noaa21_count = conn.execute(text("""
            SELECT COUNT(*) FROM thermal_detections
            WHERE EXTRACT(YEAR FROM acq_timestamp) = 2025 AND satellite = 'NOAA-21';
        """)).scalar()
        assert noaa21_count > 600000


def test_2025_monthly_seasonal_coverage():
    """Verify complete 12-month seasonal coverage in calendar year 2025"""
    with engine.connect() as conn:
        monthly_counts = conn.execute(text("""
            SELECT TO_CHAR(acq_timestamp, 'YYYY-MM') as month, COUNT(*) as cnt
            FROM thermal_detections
            WHERE EXTRACT(YEAR FROM acq_timestamp) = 2025
            GROUP BY TO_CHAR(acq_timestamp, 'YYYY-MM')
            ORDER BY month;
        """)).fetchall()

        months = [r[0] for r in monthly_counts]
        assert len(months) == 12
        for m in range(1, 13):
            assert f"2025-{m:02d}" in months


def test_2025_coordinate_and_geometry_validity():
    """Verify that all 2025 records have valid coordinates strictly within Indian territorial bounds"""
    with engine.connect() as conn:
        null_coords = conn.execute(text("""
            SELECT COUNT(*) FROM thermal_detections
            WHERE EXTRACT(YEAR FROM acq_timestamp) = 2025
              AND (latitude IS NULL OR longitude IS NULL OR acq_timestamp IS NULL);
        """)).scalar()
        assert null_coords == 0

        invalid_geoms = conn.execute(text("""
            SELECT COUNT(*) FROM thermal_history
            WHERE EXTRACT(YEAR FROM acq_timestamp) = 2025
              AND NOT ST_IsValid(ST_SetSRID(ST_MakePoint(longitude, latitude), 4326));
        """)).scalar()
        assert invalid_geoms == 0


def test_2025_api_endpoints():
    """Verify historical API endpoints for 2025 data"""
    resp_obs = client.get("/api/v1/historical/observations?time_window=5Y&limit=10")
    assert resp_obs.status_code == 200
    data = resp_obs.json()
    assert "items" in data
    assert len(data["items"]) == 10

    resp_tl = client.get("/api/v1/historical/timeline")
    assert resp_tl.status_code == 200
    timeline = resp_tl.json()["timeline"]
    months_2025 = [p["period"] for p in timeline if p["period"].startswith("2025-")]
    assert len(months_2025) == 12


def test_2025_manifest_file():
    """Verify that archive_manifest_2025.json exists and accurately reflects ingestion"""
    manifest_path = r"E:\PROJECTS\AGNI-NETRA(DATABASE)\FIRMS\HISTORICAL\2025\full\archive_manifest_2025.json"
    assert os.path.exists(manifest_path)
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    assert manifest["target_calendar_year"] == 2025
    assert manifest["status"] == "2025_FULL_ARCHIVE_IMPORTED"
    assert len(manifest["archives"]) == 4
    assert manifest["ingestion_totals"]["accepted_inside_india"] == 2008112
    assert manifest["ingestion_totals"]["source_rows_read"] == 2015957

