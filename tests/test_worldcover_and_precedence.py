"""
AGNI-NETRA — Automated Test Suite for Phase 3D: Multi-Source LULC & Strict Bhuvan Precedence
Tests:
- ESA WorldCover 10m source registration in lulc_sources
- ESA WorldCover 11 classes mapped in lulc_classes (built-up mapped to BUILT_UP_URBAN)
- National 3x3 degree tile indexing in lulc_raster_tiles
- Strict Bhuvan precedence over WorldCover in overlapping areas
- WorldCover national complementary fallback in uncovered areas
- NO_COVERAGE for points outside Indian territorial extent
- Confidence values: 0.96 for Bhuvan, 0.88 for WorldCover, 0.0 for No coverage
- Source resolution: 24m for Bhuvan, 10m for WorldCover
- Source reference year: 2025 for Bhuvan, 2021 for WorldCover
- REST API /api/v1/lulc/lookup returns correct coverage_status and provenance
"""

import pytest
from sqlalchemy import text
from fastapi.testclient import TestClient

from backend.app.core.database import engine
from backend.app.main import app
from data_pipeline.adapters.worldcover_adapter import worldcover_adapter
from backend.app.services.lulc_service import lookup_unified_lulc

client = TestClient(app)


def test_worldcover_source_metadata():
    """Verify ESA WorldCover 10m source metadata is registered"""
    with engine.connect() as conn:
        source = conn.execute(text("SELECT * FROM lulc_sources WHERE id = 'ESA_WORLDCOVER_10M';")).fetchone()
        assert source is not None
        assert source.source_name == "ESA_WORLDCOVER_10M"
        assert "European Space Agency" in source.organization
        assert source.resolution_m == 10.0
        assert source.reference_year == 2021
        assert source.product_version == "v200"
        assert source.access_type == "CLOUD_OPTIMIZED_GEOTIFF_TILES"


def test_worldcover_class_crosswalk():
    """Verify WorldCover class crosswalk maps built-up to BUILT_UP_URBAN (not industrial)"""
    with engine.connect() as conn:
        classes = conn.execute(text("""
            SELECT source_class_code, source_class_name, canonical_class, is_industrial_compatible, risk_weight
            FROM lulc_classes
            WHERE source_id = 'ESA_WORLDCOVER_10M';
        """)).fetchall()
        assert len(classes) == 11
        class_map = {c.source_class_code: c for c in classes}

        # Tree cover
        assert class_map["10"].canonical_class == "FOREST"
        assert class_map["10"].is_industrial_compatible is False

        # Cropland
        assert class_map["40"].canonical_class == "AGRICULTURE_CROPLAND"

        # Built-up -> BUILT_UP_URBAN (NOT BUILT_UP_INDUSTRIAL)
        assert class_map["50"].canonical_class == "BUILT_UP_URBAN"
        assert class_map["50"].is_industrial_compatible is False

        # Water bodies
        assert class_map["80"].canonical_class == "WATER_BODIES"


def test_worldcover_tile_grid_coverage():
    """Verify national 3x3 degree tile indexing covers India"""
    with engine.connect() as conn:
        count = conn.execute(text("SELECT COUNT(*) FROM lulc_raster_tiles WHERE source_id = 'ESA_WORLDCOVER_10M';")).scalar()
        assert count >= 60

        # Check Delhi is covered by tile N27E075 or N27E078
        delhi_tile = conn.execute(text("""
            SELECT tile_id FROM lulc_raster_tiles
            WHERE source_id = 'ESA_WORLDCOVER_10M'
              AND ST_Contains(geom, ST_SetSRID(ST_MakePoint(77.209, 28.613), 4326));
        """)).fetchone()
        assert delhi_tile is not None


def test_strict_bhuvan_precedence_over_worldcover():
    """Verify Bhuvan is selected when a point is inside a real Bhuvan polygon"""
    with engine.connect() as conn:
        # Jamnagar Refinery is inside Bhuvan polygon AND inside WorldCover tile N21E069
        resp = client.get("/api/v1/lulc/lookup?latitude=22.355&longitude=69.865")
        assert resp.status_code == 200
        data = resp.json()
        assert data["coverage_status"] == "REAL_BHUVAN"
        assert data["source"] == "ISRO_BHUVAN_50K"
        assert data["primary_class"] == "BUILT_UP_INDUSTRIAL"
        assert data["resolution_m"] == 24.0
        assert data["reference_year"] == 2025
        assert data["confidence"] >= 0.95
        assert data["spatial_match_method"] == "POSTGIS_BHUVAN_POINT_IN_POLYGON"


def test_worldcover_complementary_fallback():
    """Verify WorldCover is selected when a point is outside Bhuvan but inside India"""
    # Delhi is outside Bhuvan pilot polygons, but inside WorldCover India grid
    resp = client.get("/api/v1/lulc/lookup?latitude=28.613&longitude=77.209")
    assert resp.status_code == 200
    data = resp.json()
    assert data["coverage_status"] == "REAL_WORLDCOVER"
    assert data["source"] == "ESA_WORLDCOVER_10M"
    assert data["primary_class"] == "BUILT_UP_URBAN"
    assert data["resolution_m"] == 10.0
    assert data["reference_year"] == 2021
    assert data["confidence"] == 0.88
    assert data["spatial_match_method"] == "ESA_WORLDCOVER_10M_RASTER_TILE"


def test_no_coverage_outside_territorial_grid():
    """Verify NO_COVERAGE is returned for coordinates outside Indian territory"""
    # Point in South Indian Ocean
    resp = client.get("/api/v1/lulc/lookup?latitude=-5.0&longitude=75.0")
    assert resp.status_code == 200
    data = resp.json()
    assert data["coverage_status"] == "NO_COVERAGE"
    assert data["source_coverage"] == "UNAVAILABLE"
    assert data["primary_class"] == "UNCLASSIFIED_NO_COVERAGE"
    assert data["confidence"] == 0.0
    assert data["spatial_match_method"] == "NO_SPATIAL_INTERSECT"


def test_no_synthetic_data_contamination():
    """Verify synthetic demo tags never appear in production lookup responses"""
    for lat, lon in [(22.355, 69.865), (28.613, 77.209), (13.082, 80.270), (-5.0, 75.0)]:
        resp = client.get(f"/api/v1/lulc/lookup?latitude={lat}&longitude={lon}")
        data = resp.json()
        assert data["coverage_status"] != "DEMO_FALLBACK"
        assert "SYNTHETIC" not in data.get("source", "")
        assert "SYNTHETIC" not in data.get("spatial_match_method", "")
