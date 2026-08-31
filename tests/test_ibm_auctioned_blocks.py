"""
AGNI-NETRA — Automated Test Suite for IBM Table 15 Auctioned Mineral Blocks
Validates staging extraction, canonical records, duplicate prevention, entity resolution integrity,
and FastAPI endpoint querying.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from backend.app.main import app
from backend.app.core.database import engine

client = TestClient(app)


def test_table15_staging_and_canonical_counts():
    """Verify exactly 119 records extracted to staging and populated in canonical."""
    with engine.connect() as conn:
        stg_count = conn.execute(text("SELECT count(*) FROM ibm_auctioned_blocks_staging;")).scalar()
        can_count = conn.execute(text("SELECT count(*) FROM ibm_auctioned_blocks;")).scalar()

    assert stg_count == 119, f"Expected 119 staging records, got {stg_count}"
    assert can_count == 119, f"Expected 119 canonical records, got {can_count}"


def test_table15_sl_no_integrity():
    """Verify all 119 SL numbers from 1 to 119 exist with zero duplicates."""
    with engine.connect() as conn:
        sl_nos = [r[0] for r in conn.execute(text("SELECT sl_no FROM ibm_auctioned_blocks ORDER BY sl_no;")).fetchall()]

    assert len(sl_nos) == 119
    assert sl_nos == list(range(1, 120))
    assert len(set(sl_nos)) == 119


def test_table15_entity_resolution_sum():
    """Verify HIGH + MEDIUM + LOW + UNMATCHED equals total evaluated (119)."""
    with engine.connect() as conn:
        high = conn.execute(text("SELECT count(*) FROM ibm_auctioned_blocks WHERE match_confidence = 'HIGH';")).scalar()
        med = conn.execute(text("SELECT count(*) FROM ibm_auctioned_blocks WHERE match_confidence = 'MEDIUM';")).scalar()
        low = conn.execute(text("SELECT count(*) FROM ibm_auctioned_blocks WHERE match_confidence = 'LOW';")).scalar()
        unmatched = conn.execute(text("SELECT count(*) FROM ibm_auctioned_blocks WHERE match_confidence = 'UNMATCHED';")).scalar()

    total = high + med + low + unmatched
    assert total == 119, f"Sum {total} does not equal 119"


def test_table15_geometry_integrity():
    """Verify geometry is not hallucinated and sum of with + without geometry equals 119."""
    with engine.connect() as conn:
        with_geom = conn.execute(text("SELECT count(*) FROM ibm_auctioned_blocks WHERE geom IS NOT NULL;")).scalar()
        without_geom = conn.execute(text("SELECT count(*) FROM ibm_auctioned_blocks WHERE geom IS NULL;")).scalar()

    assert with_geom + without_geom == 119
    # Unmatched records must have NULL geometry (no fabricated coordinates)
    with engine.connect() as conn:
        unmatched_with_geom = conn.execute(text("""
            SELECT count(*) FROM ibm_auctioned_blocks 
            WHERE match_confidence = 'UNMATCHED' AND geom IS NOT NULL;
        """)).scalar()
    assert unmatched_with_geom == 0


def test_table15_api_mining_endpoint():
    """Verify GET /api/v1/mining/auctioned-blocks endpoint returns valid data."""
    res = client.get("/api/v1/mining/auctioned-blocks?limit=10")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 10
    first = data[0]
    assert first["sl_no"] == 1
    assert "block_name" in first
    assert "state" in first
    assert "mineral" in first
    assert "match_confidence" in first


def test_table15_api_state_filter():
    """Verify filtering by state returns matching records."""
    res = client.get("/api/v1/mining/auctioned-blocks?state=Rajasthan&limit=100")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 34
    for b in data:
        assert b["state"] == "Rajasthan"


def test_table15_api_facilities_endpoint():
    """Verify GET /api/v1/facilities/ibm/auctioned-blocks endpoint."""
    res = client.get("/api/v1/facilities/ibm/auctioned-blocks?mineral=Limestone&limit=50")
    assert res.status_code == 200
    data = res.json()
    assert len(data) > 0
    for b in data:
        assert "limestone" in b["mineral"].lower()


def test_table15_preserved_canonical_facility_count():
    """Verify canonical facility count remains intact (non-destructive import)."""
    with engine.connect() as conn:
        fac_count = conn.execute(text("SELECT count(*) FROM industrial_facilities;")).scalar()
    assert fac_count == 35662
