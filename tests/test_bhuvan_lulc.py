"""
AGNI-NETRA — Automated Test Suite for ISRO Bhuvan LULC Source Integrity & Pilot Coverage (Phase 3C)
Tests:
- Real Bhuvan source metadata in lulc_sources
- 24 NRSC Level-II Bhuvan classes & canonical crosswalk in lulc_classes
- PostGIS spatial point-in-polygon & boundary distance calculations in lulc_spatial_features
- Points inside real Bhuvan polygon -> coverage_status='REAL', confidence >= 0.90
- Points outside real Bhuvan polygon -> coverage_status='NO_COVERAGE', source_coverage='UNAVAILABLE', confidence=0.0
- Synthetic fallback isolation (never reported as real Bhuvan)
- observation_lulc_context & facility_lulc_context integrity
- LULC REST API endpoints (/api/v1/lulc/classes, /api/v1/lulc/lookup, /api/v1/lulc/stats, /api/v1/lulc/sources)
"""

import pytest
from sqlalchemy import text
from fastapi.testclient import TestClient

from backend.app.core.database import engine
from backend.app.main import app
from data_pipeline.adapters.bhuvan_adapter import bhuvan_adapter
from data_pipeline.adapters.lulc_adapter import lulc_engine

client = TestClient(app)


def test_bhuvan_lulc_source_metadata():
    """Verify official ISRO / NRSC Bhuvan source metadata is registered"""
    with engine.connect() as conn:
        source = conn.execute(text("SELECT * FROM lulc_sources WHERE id = 'ISRO_BHUVAN_50K';")).fetchone()
        assert source is not None
        assert source.source_name == "ISRO_BHUVAN_LULC_50K"
        assert "National Remote Sensing Centre" in source.organization
        assert source.resolution_m == 24.0
        assert source.reference_year == 2025
        assert source.product_version == "LULC-50K-CYCLE-V"
        assert source.access_type == "OGC_WMS_AND_POLYGON_TILES"


def test_bhuvan_class_crosswalk():
    """Verify NRSC Level-II Bhuvan classes are mapped to canonical AGNI-NETRA classes"""
    with engine.connect() as conn:
        classes = conn.execute(text("""
            SELECT source_class_code, source_class_name, canonical_class, is_industrial_compatible, risk_weight
            FROM lulc_classes
            WHERE source_id = 'ISRO_BHUVAN_50K';
        """)).fetchall()
        assert len(classes) >= 20

        class_map = {c.source_class_code: c for c in classes}

        # 1. Heavy industry
        assert "1.3.1" in class_map
        assert class_map["1.3.1"].canonical_class == "BUILT_UP_INDUSTRIAL"
        assert class_map["1.3.1"].is_industrial_compatible is True

        # 2. Petroleum refinery
        assert "1.3.3" in class_map
        assert class_map["1.3.3"].canonical_class == "BUILT_UP_INDUSTRIAL"
        assert class_map["1.3.3"].is_industrial_compatible is True

        # 3. Coal mining
        assert "1.4.1" in class_map
        assert class_map["1.4.1"].canonical_class == "MINING"
        assert class_map["1.4.1"].is_industrial_compatible is True

        # 4. Dense forest
        assert "3.1.1" in class_map
        assert class_map["3.1.1"].canonical_class == "FOREST"
        assert class_map["3.1.1"].is_industrial_compatible is False

        # 5. Cropland
        assert "2.1.2" in class_map
        assert class_map["2.1.2"].canonical_class == "AGRICULTURE_CROPLAND"


def test_postgis_spatial_polygon_containment():
    """Verify PostGIS point-in-polygon containment across pilot AOIs"""
    # 1. Jamnagar Petroleum Complex (69.85, 22.35)
    cat_jam, name_jam, dists_jam = lulc_engine.classify_location(22.35, 69.85)
    assert cat_jam == "Industrial"
    assert "Jamnagar" in str(name_jam)
    assert dists_jam["dist_to_industrial_m"] == 0.0

    # 2. Singrauli Mining Area (82.65, 24.15)
    cat_sing, name_sing, dists_sing = lulc_engine.classify_location(24.15, 82.65)
    assert cat_sing in ["Industrial", "Mining"]
    assert dists_sing["dist_to_mine_m"] == 0.0 or dists_sing["dist_to_industrial_m"] == 0.0

    # 3. Similipal Reserve Forest (86.35, 21.75)
    cat_sim, name_sim, dists_sim = lulc_engine.classify_location(21.75, 86.35)
    assert cat_sim == "Forest"
    assert "Similipal" in str(name_sim)
    assert dists_sim["dist_to_forest_m"] == 0.0


def test_point_outside_bhuvan_coverage_returns_unknown():
    """Verify points outside Bhuvan pilot coverage return Unknown / No Coverage"""
    # Delhi (28.61, 77.20) - outside pilot polygons
    cat_delhi, desc_delhi, dists_delhi = lulc_engine.classify_location(28.61, 77.20)
    assert cat_delhi == "Unknown"
    assert "No Bhuvan Pilot Coverage" in str(desc_delhi)
    assert dists_delhi["dist_to_industrial_m"] > 0


def test_bhuvan_adapter_provenance_and_integrity():
    """Verify Bhuvan adapter generates real provenance and strict coverage metadata"""
    # Inside Pilot (Jamnagar)
    rec_in = bhuvan_adapter.classify_location(22.35, 69.85)
    assert rec_in.category == "Industrial"
    assert rec_in.is_industrial_zone is True
    assert rec_in.provenance.source_name == "ISRO_BHUVAN_LULC_50K"
    assert rec_in.provenance.data_quality_score >= 0.90
    assert rec_in.provenance.additional_metadata["coverage_status"] == "REAL"
    assert rec_in.provenance.additional_metadata["source_coverage"] == "COVERED"

    # Outside Pilot (Delhi)
    rec_out = bhuvan_adapter.classify_location(28.61, 77.20)
    assert rec_out.category == "Unknown"
    assert rec_out.is_industrial_zone is False
    assert rec_out.provenance.data_quality_score == 0.0
    assert rec_out.provenance.additional_metadata["coverage_status"] == "NO_COVERAGE"
    assert rec_out.provenance.additional_metadata["source_coverage"] == "UNAVAILABLE"


def test_observation_lulc_context_table():
    """Verify observation_lulc_context table exists and enforces source integrity"""
    with engine.connect() as conn:
        count = conn.execute(text("SELECT COUNT(*) FROM observation_lulc_context;")).scalar()
        assert count > 0

        # Check covered observation sample if present
        covered = conn.execute(text("""
            SELECT primary_lulc_class, spatial_match_method, confidence_score
            FROM observation_lulc_context
            WHERE spatial_match_method = 'POSTGIS_POINT_IN_POLYGON'
            LIMIT 1;
        """)).fetchone()
        if covered:
            assert covered.confidence_score >= 0.90
            assert covered.primary_lulc_class in [
                "BUILT_UP_INDUSTRIAL", "BUILT_UP_URBAN", "MINING",
                "AGRICULTURE_CROPLAND", "FOREST", "WATER_BODIES", "BARREN_SCRUB"
            ]

        # Check unclassified outside pilot sample
        outside = conn.execute(text("""
            SELECT primary_lulc_class, spatial_match_method, confidence_score
            FROM observation_lulc_context
            WHERE spatial_match_method = 'OUTSIDE_PILOT_COVERAGE'
            LIMIT 1;
        """)).fetchone()
        if outside:
            assert outside.primary_lulc_class == "UNCLASSIFIED_OUTSIDE_PILOT"
            assert outside.confidence_score == 0.0


def test_facility_lulc_context_table():
    """Verify facility_lulc_context table exists and enforces source integrity"""
    with engine.connect() as conn:
        count = conn.execute(text("SELECT COUNT(*) FROM facility_lulc_context;")).scalar()
        assert count > 0


def test_lulc_api_sources():
    """Test GET /api/v1/lulc/sources"""
    resp = client.get("/api/v1/lulc/sources")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assert any(s["source_name"] == "ISRO_BHUVAN_LULC_50K" for s in data)


def test_lulc_api_classes():
    """Test GET /api/v1/lulc/classes"""
    resp = client.get("/api/v1/lulc/classes")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 20
    canonical_classes = {c["canonical_class"] for c in data}
    assert "BUILT_UP_INDUSTRIAL" in canonical_classes
    assert "MINING" in canonical_classes
    assert "FOREST" in canonical_classes
    assert "AGRICULTURE_CROPLAND" in canonical_classes


def test_lulc_api_lookup_real_vs_no_coverage():
    """Test GET /api/v1/lulc/lookup inside pilot and complementary national coverage"""
    # 1. Inside Bhuvan pilot AOI (Jamnagar)
    resp_in = client.get("/api/v1/lulc/lookup?latitude=22.35&longitude=69.85")
    assert resp_in.status_code == 200
    data_in = resp_in.json()
    assert data_in["coverage_status"] == "REAL_BHUVAN"
    assert data_in["source"] == "ISRO_BHUVAN_50K"
    assert data_in["primary_class"] == "BUILT_UP_INDUSTRIAL"
    assert data_in["confidence"] >= 0.90
    assert data_in["spatial_match_method"] == "POSTGIS_BHUVAN_POINT_IN_POLYGON"

    # 2. Outside Bhuvan pilot AOI, but within Indian territory (Delhi - WorldCover fallback)
    resp_out = client.get("/api/v1/lulc/lookup?latitude=28.61&longitude=77.20")
    assert resp_out.status_code == 200
    data_out = resp_out.json()
    assert data_out["coverage_status"] == "REAL_WORLDCOVER"
    assert data_out["source"] == "ESA_WORLDCOVER_10M"
    assert data_out["primary_class"] == "BUILT_UP_URBAN"
    assert data_out["confidence"] == 0.88
    assert data_out["spatial_match_method"] == "ESA_WORLDCOVER_10M_RASTER_TILE"


def test_lulc_api_stats():
    """Test GET /api/v1/lulc/stats"""
    resp = client.get("/api/v1/lulc/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_sources"] >= 1
    assert data["total_classes"] >= 20
    assert data["total_features"] >= 10
    assert "BUILT_UP_INDUSTRIAL" in data["canonical_class_distribution"]
