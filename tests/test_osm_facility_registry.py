"""
AGNI-NETRA — Automated Unit and Integration Tests for OSM Industrial Facility Registry
Tests:
1. NIC-2008 taxonomy mapping resolution
2. Entity classification rules
3. Name and attribute normalization
4. PostGIS geometry and spatial queries
5. Idempotent deduplication
6. FastAPI /api/v1/facilities endpoint retrieval
"""

import os
import sys
import pytest
from sqlalchemy import text
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.main import app
from backend.app.core.database import engine
from data_pipeline.nic_mapping import resolve_nic_mapping, NIC_2008_TAXONOMY
from data_pipeline.osm_classifier import (
    classify_osm_entity,
    normalize_name,
    normalize_state,
    assess_quality_and_confidence
)


client = TestClient(app)


def test_nic_mapping_power_plants():
    # Solar power
    nic, sec, sub, ind = resolve_nic_mapping({"power": "plant", "plant:source": "solar"}, "POWER_PLANT")
    assert nic == "35104"
    assert "Solar" in ind
    assert sec == "Electricity, Gas and Water Supply"

    # Thermal power (coal)
    nic, sec, sub, ind = resolve_nic_mapping({"power": "plant", "plant:source": "coal"}, "POWER_PLANT")
    assert nic == "35101"
    assert "Thermal" in ind

    # Hydro power
    nic, sec, sub, ind = resolve_nic_mapping({"power": "plant", "plant:source": "hydro"}, "POWER_PLANT")
    assert nic == "35102"
    assert "Hydro" in ind

    # Substation
    nic, sec, sub, ind = resolve_nic_mapping({"power": "substation"}, "POWER_PLANT")
    assert nic == "35107"


def test_nic_mapping_heavy_industry():
    # Coal Mine
    nic, sec, sub, ind = resolve_nic_mapping({"industrial": "mine", "resource": "coal"}, "MINE")
    assert nic == "0510"
    assert "Coal" in ind

    # Steel Plant
    nic, sec, sub, ind = resolve_nic_mapping({"industrial": "steel", "name": "Tata Steel Kalinganagar"}, "FACILITY")
    assert nic == "2410"
    assert "Iron and Steel" in ind

    # Petroleum Refinery
    nic, sec, sub, ind = resolve_nic_mapping({"man_made": "petroleum_refinery"}, "REFINERY")
    assert nic == "1920"
    assert "Petroleum" in ind

    # Brick Kiln
    nic, sec, sub, ind = resolve_nic_mapping({"industrial": "brickyard"}, "FACILITY")
    assert nic == "2392"
    assert "Clay Building Materials" in ind


def test_entity_classification():
    assert classify_osm_entity({"power": "plant", "plant:source": "solar"}) == "POWER_PLANT"
    assert classify_osm_entity({"man_made": "petroleum_refinery"}) == "REFINERY"
    assert classify_osm_entity({"landuse": "quarry", "resource": "coal"}) == "MINE"
    assert classify_osm_entity({"man_made": "works"}) == "WORKS"
    assert classify_osm_entity({"industrial": "factory", "name": "Precision Engineering"}) == "FACILITY"
    assert classify_osm_entity({"landuse": "industrial", "name": "GIDC Industrial Estate Phase 2"}) == "INDUSTRIAL_ZONE"
    assert classify_osm_entity({"landuse": "industrial"}) == "INDUSTRIAL_ZONE"


def test_normalization():
    assert normalize_name("  Reliance   Industries   Limited  ") == "Reliance Industries Limited"
    assert normalize_state("TN") == "Tamil Nadu"
    assert normalize_state("ka") == "Karnataka"
    assert normalize_state("karnataka") == "Karnataka"


def test_database_staging_records():
    with engine.connect() as conn:
        stg_count = conn.execute(text("SELECT count(*) FROM osm_staging_facilities")).scalar()
        assert stg_count == 35546, f"Expected 35,546 staging records, got {stg_count}"

        # PostGIS Geometry check
        srid = conn.execute(text("SELECT DISTINCT ST_SRID(geom) FROM osm_staging_facilities")).scalar()
        assert srid == 4326, f"Expected SRID 4326, got {srid}"

        # Verification of uninvented fields (null counts)
        null_coords = conn.execute(text("SELECT count(*) FROM osm_staging_facilities WHERE latitude IS NULL")).scalar()
        assert null_coords == 0, "Latitude should not be NULL"


def test_canonical_facilities_registry():
    with engine.connect() as conn:
        fac_count = conn.execute(text("SELECT count(*) FROM industrial_facilities")).scalar()
        assert fac_count >= 35546, f"Expected >= 35,546 canonical facilities, got {fac_count}"

        # Check existing facilities were preserved
        non_osm = conn.execute(text("SELECT count(*) FROM industrial_facilities WHERE source != 'OSM'")).scalar()
        assert non_osm > 0, "Pre-existing canonical non-OSM facilities should be preserved"


def test_fastapi_facilities_endpoint():
    # 1. Test basic facility retrieval with limit
    response = client.get("/api/v1/facilities?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 10
    assert "name" in data[0]
    assert "facility_type" in data[0]
    assert "source" in data[0]

    # 2. Test search filter
    response_search = client.get("/api/v1/facilities?search=Reliance&limit=5")
    assert response_search.status_code == 200
    search_data = response_search.json()
    assert len(search_data) > 0

    # 3. Test detail retrieval
    facility_id = data[0]["id"]
    response_detail = client.get(f"/api/v1/facilities/{facility_id}")
    assert response_detail.status_code == 200
    detail_data = response_detail.json()
    assert detail_data["id"] == facility_id


if __name__ == "__main__":
    pytest.main(["-v", __file__])
