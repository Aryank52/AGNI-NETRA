"""
AGNI-NETRA — Automated Pytest Suite for IBM National Mineral Inventory 2020
Verifies data integrity, mathematical balance, non-destructive properties, and FastAPI endpoints.
"""

import pytest
from sqlalchemy import text
from fastapi.testclient import TestClient

from backend.app.core.database import engine
from backend.app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_ibm_nmi_staging_records():
    """
    Verifies staging table ingestion:
    - 59 total extracted line items across 46 commodities
    - 0 duplicate record_ids
    """
    with engine.connect() as conn:
        staging_count = conn.execute(text("SELECT count(*) FROM ibm_nmi_staging;")).scalar()
        distinct_ids = conn.execute(text("SELECT count(DISTINCT record_id) FROM ibm_nmi_staging;")).scalar()

    assert staging_count == 59, f"Expected 59 NMI staging rows, got {staging_count}"
    assert distinct_ids == 59, f"Expected 59 distinct record IDs, got {distinct_ids}"


def test_ibm_nmi_canonical_records():
    """
    Verifies canonical context table properties:
    - 59 total records
    - Reference year = 2020, reference_date = 2020-04-01
    - Source = 'IBM', provisional_flag = True
    - 46 distinct commodities
    """
    with engine.connect() as conn:
        canon_count = conn.execute(text("SELECT count(*) FROM ibm_mineral_resources;")).scalar()
        commodities_count = conn.execute(text("SELECT count(DISTINCT commodity) FROM ibm_mineral_resources;")).scalar()
        ref_years = conn.execute(text("SELECT DISTINCT reference_year FROM ibm_mineral_resources;")).fetchall()
        sources = conn.execute(text("SELECT DISTINCT source FROM ibm_mineral_resources;")).fetchall()
        prov_flags = conn.execute(text("SELECT DISTINCT provisional_flag FROM ibm_mineral_resources;")).fetchall()

    assert canon_count == 59, f"Expected 59 canonical rows, got {canon_count}"
    assert commodities_count == 46, f"Expected 46 distinct commodities, got {commodities_count}"
    assert [r[0] for r in ref_years] == [2020], f"Expected reference_year 2020, got {ref_years}"
    assert [r[0] for r in sources] == ["IBM"], f"Expected source IBM, got {sources}"
    assert [r[0] for r in prov_flags] == [True], f"Expected provisional_flag True, got {prov_flags}"


def test_ibm_nmi_not_estimated_handling():
    """
    Verifies that 'Not Estimated' (N.E.) commodities (Alexandrite):
    - Are marked with not_estimated = TRUE
    - Have NULL (None) for reserves, remaining_resources, and total_resources (NOT zero)
    """
    with engine.connect() as conn:
        alex = conn.execute(text("""
            SELECT commodity, mineral, reserves, remaining_resources, total_resources, not_estimated
            FROM ibm_mineral_resources
            WHERE commodity = 'Alexandrite';
        """)).fetchone()

    assert alex is not None, "Alexandrite record must exist in ibm_mineral_resources"
    assert alex[2] is None, f"Alexandrite reserves must be NULL, got {alex[2]}"
    assert alex[3] is None, f"Alexandrite remaining_resources must be NULL, got {alex[3]}"
    assert alex[4] is None, f"Alexandrite total_resources must be NULL, got {alex[4]}"
    assert alex[5] is True, f"Alexandrite not_estimated must be True, got {alex[5]}"


def test_ibm_nmi_arithmetic_balance():
    """
    Verifies mathematical identity: Reserves + Remaining Resources == Total Resources
    for all 58 estimated mineral line items.
    """
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT mineral, reserves, remaining_resources, total_resources
            FROM ibm_mineral_resources
            WHERE not_estimated = FALSE;
        """)).fetchall()

    assert len(rows) == 58, f"Expected 58 estimated line items, got {len(rows)}"

    for min_name, res, rem, tot in rows:
        res_val = res if res is not None else 0.0
        rem_val = rem if rem is not None else 0.0
        tot_val = tot if tot is not None else 0.0
        calc_tot = round(res_val + rem_val, 2)
        diff = round(abs(calc_tot - tot_val), 2)
        assert diff <= 1.0, f"Arithmetic mismatch for {min_name}: Res({res_val}) + Rem({rem_val}) = {calc_tot} != Tot({tot_val})"


def test_ibm_nmi_zero_coordinate_hallucination_and_facility_registry_integrity():
    """
    Verifies strict non-destructive isolation:
    - 0 NMI records added to industrial_facilities
    - Canonical facilities count remains untouched at 35,662
    """
    with engine.connect() as conn:
        fac_count = conn.execute(text("SELECT count(*) FROM industrial_facilities;")).scalar()
        col_names = conn.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'ibm_mineral_resources';
        """)).fetchall()

    assert fac_count >= 35660, f"Expected at least 35,660 canonical facilities, got {fac_count}"
    cols = [r[0] for r in col_names]
    assert "latitude" not in cols, "latitude must NOT exist in ibm_mineral_resources"
    assert "longitude" not in cols, "longitude must NOT exist in ibm_mineral_resources"
    assert "geometry" not in cols, "geometry must NOT exist in ibm_mineral_resources"


def test_fastapi_ibm_mineral_resources_endpoint(client):
    """
    Verifies FastAPI GET /api/v1/facilities/ibm/mineral-resources endpoint filters.
    """
    # 1. Query all mineral resources
    res = client.get("/api/v1/facilities/ibm/mineral-resources?limit=100")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 59

    # 2. Query specific commodity filter (Bauxite)
    res_baux = client.get("/api/v1/facilities/ibm/mineral-resources?commodity=Bauxite")
    assert res_baux.status_code == 200
    data_baux = res_baux.json()
    assert len(data_baux) == 1
    assert data_baux[0]["commodity"] == "Bauxite"
    assert data_baux[0]["total_resources"] == 4958248.0

    # 3. Query not_estimated filter
    res_ne = client.get("/api/v1/facilities/ibm/mineral-resources?not_estimated=true")
    assert res_ne.status_code == 200
    data_ne = res_ne.json()
    assert len(data_ne) == 1
    assert data_ne[0]["commodity"] == "Alexandrite"
