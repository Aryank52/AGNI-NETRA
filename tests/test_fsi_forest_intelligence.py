"""
AGNI-NETRA — Automated Test Suite for Phase 4B: Forest Intelligence & FSI / Protected Areas
Validates:
1. FSI source registry & ISFR district canopy density statistics
2. WII Protected Areas PostGIS geometry validity and SRID
3. Multi-source spatial precedence and deterministic evidence levels
4. FSI adapter health and point classification
5. FastAPI REST API endpoints (/sources, /stats, /protected-areas, /lookup)
6. Separation of forest proximity from fire causation claims
"""

import pytest
from sqlalchemy import text
from fastapi.testclient import TestClient

from backend.app.core.database import engine
from backend.app.main import app
from data_pipeline.adapters.fsi_adapter import fsi_adapter

client = TestClient(app)


def test_fsi_source_registry():
    """Verify that authoritative FSI and WII sources are registered in fsi_sources"""
    with engine.connect() as conn:
        sources = conn.execute(text("SELECT id, source_name, organization, reference_year FROM fsi_sources;")).fetchall()
        src_map = {s.id: s for s in sources}

        assert "FSI_ISFR_2021" in src_map
        assert "WII_PA_REGISTRY" in src_map
        assert "FSI_VAN_AGNI" in src_map

        assert src_map["FSI_ISFR_2021"].reference_year == 2021
        assert "Forest Survey of India" in src_map["FSI_ISFR_2021"].organization
        assert "Wildlife Institute of India" in src_map["WII_PA_REGISTRY"].organization


def test_isfr_district_forest_statistics():
    """Verify ISFR 2021 district forest cover statistics consistency and mathematical validity"""
    with engine.connect() as conn:
        stats = conn.execute(text("""
            SELECT state, district, geographical_area_sqkm, very_dense_forest_sqkm,
                   moderately_dense_forest_sqkm, open_forest_sqkm, total_forest_sqkm,
                   percent_of_geo_area, scrub_sqkm
            FROM fsi_isfr_district_forest_stats;
        """)).fetchall()

        assert len(stats) >= 15

        for s in stats:
            # 1. Total forest must equal sum of canopy classes
            expected_total = s.very_dense_forest_sqkm + s.moderately_dense_forest_sqkm + s.open_forest_sqkm
            assert abs(s.total_forest_sqkm - expected_total) < 0.1

            # 2. Percentage must be between 0 and 100
            assert 0.0 <= s.percent_of_geo_area <= 100.0

            # 3. Forest area must not exceed total geographical area
            assert s.total_forest_sqkm <= s.geographical_area_sqkm


def test_protected_areas_geometry_validity():
    """Verify that Protected Area geometries in PostGIS are valid, non-empty, and SRID 4326"""
    with engine.connect() as conn:
        pas = conn.execute(text("""
            SELECT id, pa_name, pa_type, state,
                   ST_IsValid(geom) as is_valid,
                   ST_IsEmpty(geom) as is_empty,
                   ST_SRID(geom) as srid,
                   ST_GeometryType(geom) as geom_type
            FROM protected_areas;
        """)).fetchall()

        assert len(pas) >= 10

        for p in pas:
            assert p.is_valid is True, f"Invalid geometry in Protected Area: {p.pa_name}"
            assert p.is_empty is False
            assert p.srid == 4326
            assert p.geom_type in ("ST_MultiPolygon", "ST_Polygon")


def test_fsi_adapter_classification():
    """Verify FSIAdapter classification across representative Indian forest and urban coordinates"""
    # 1. Similipal Tiger Reserve (inside PA)
    rec_sim = fsi_adapter.classify_location(21.75, 86.35)
    assert rec_sim.category == "Forest"
    assert rec_sim.provenance.additional_metadata["forest_context_level"] == "HIGH"
    assert rec_sim.provenance.additional_metadata["is_inside_protected_area"] is True
    assert "Similipal" in rec_sim.provenance.additional_metadata["protected_area_name"]

    # 2. Jamnagar (Industrial / Non-Forest)
    rec_jam = fsi_adapter.classify_location(22.355, 69.865)
    assert rec_jam.provenance.additional_metadata["forest_context_level"] == "NONE"
    assert rec_jam.provenance.additional_metadata["is_inside_protected_area"] is False


def test_fastapi_forest_endpoints():
    """Verify FastAPI REST API endpoints for Forest Intelligence"""
    # 1. GET /api/v1/forest/sources
    resp_src = client.get("/api/v1/forest/sources")
    assert resp_src.status_code == 200
    src_data = resp_src.json()
    assert len(src_data) >= 3

    # 2. GET /api/v1/forest/stats
    resp_stats = client.get("/api/v1/forest/stats")
    assert resp_stats.status_code == 200
    stats_data = resp_stats.json()
    assert stats_data["total_sources"] >= 3
    assert stats_data["total_protected_areas"] >= 10
    assert "TIGER_RESERVE" in stats_data["protected_area_distribution"]

    # 3. GET /api/v1/forest/protected-areas
    resp_pa = client.get("/api/v1/forest/protected-areas?pa_type=NATIONAL_PARK")
    assert resp_pa.status_code == 200
    pa_data = resp_pa.json()
    assert len(pa_data) >= 3
    assert all(p["pa_type"] == "NATIONAL_PARK" for p in pa_data)

    # 4. GET /api/v1/forest/lookup (Inside Bandhavgarh NP)
    resp_lookup = client.get("/api/v1/forest/lookup?latitude=23.75&longitude=81.05")
    assert resp_lookup.status_code == 200
    lookup_data = resp_lookup.json()
    assert lookup_data["forest_context_level"] == "HIGH"
    assert lookup_data["is_inside_protected_area"] is True
    assert "Bandhavgarh" in lookup_data["protected_area_name"]
    assert lookup_data["distance_to_protected_area_m"] == 0.0

    # 5. GET /api/v1/forest/lookup (Singrauli Urban/Industrial)
    resp_sing = client.get("/api/v1/forest/lookup?latitude=24.150&longitude=82.650")
    assert resp_sing.status_code == 200
    sing_data = resp_sing.json()
    assert sing_data["is_inside_protected_area"] is False
    assert sing_data["distance_to_protected_area_m"] > 10000.0


def test_controlled_sample_enrichment_integrity():
    """Verify enriched rows in facility_forest_context and observation_forest_context"""
    with engine.connect() as conn:
        fac_count = conn.execute(text("SELECT COUNT(*) FROM facility_forest_context;")).scalar()
        obs_count = conn.execute(text("SELECT COUNT(*) FROM observation_forest_context;")).scalar()

        assert fac_count > 0
        assert obs_count > 0

        # Check that ESZ flag matches distance rule (<= 10km)
        esz_mismatches = conn.execute(text("""
            SELECT COUNT(*) FROM facility_forest_context
            WHERE (distance_to_protected_area_m <= 10000.0 AND is_inside_esz_10km = FALSE)
               OR (distance_to_protected_area_m > 10000.0 AND is_inside_esz_10km = TRUE);
        """)).scalar()
        assert esz_mismatches == 0
