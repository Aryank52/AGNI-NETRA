"""
AGNI-NETRA — Automated Test Suite for IBM Mining Lease Bulletin 2024 Context Layer
Verifies staging layer integrity, deterministic record hashing, mathematical sum integrity,
provisional/historical provenance flags, zero coordinate hallucinations, and FastAPI endpoints.
"""

import os
import sys
import pytest
from sqlalchemy import text
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.database import engine
from backend.app.main import app


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def test_ibm_staging_records():
    """
    Verifies that IBM Mining Lease Bulletin records are staged with deterministic record IDs,
    clean uniqueness (0 duplicates), and required metadata.
    """
    with engine.connect() as conn:
        staging_count = conn.execute(text("SELECT count(*) FROM ibm_mining_lease_context_staging;")).scalar()
        distinct_records = conn.execute(text("SELECT count(DISTINCT record_id) FROM ibm_mining_lease_context_staging;")).scalar()
        sample = conn.execute(text("""
            SELECT record_id, state, district, mineral, lease_count, lease_area_ha, table_number, reference_year, provisional_flag
            FROM ibm_mining_lease_context_staging
            WHERE table_number = 'Table-3'
            LIMIT 1;
        """)).fetchone()

    assert staging_count >= 400, f"Expected at least 400 staged IBM records, got {staging_count}"
    assert staging_count == distinct_records, "All record_id values must be distinct (0 duplicates)"
    assert sample is not None
    assert sample[7] == 2024, "Reference year must be 2024"
    assert sample[8] is True, "Provisional flag must be True"


def test_ibm_canonical_context_records():
    """
    Verifies canonical ibm_mining_lease_context table attributes and provenance.
    """
    with engine.connect() as conn:
        canonical_count = conn.execute(text("SELECT count(*) FROM ibm_mining_lease_context;")).scalar()
        source_val = conn.execute(text("SELECT DISTINCT source FROM ibm_mining_lease_context;")).scalars().all()
        ref_year_val = conn.execute(text("SELECT DISTINCT reference_year FROM ibm_mining_lease_context;")).scalars().all()

    assert canonical_count >= 400, f"Expected at least 400 canonical IBM records, got {canonical_count}"
    assert source_val == ["IBM"], "Source must strictly be 'IBM'"
    assert ref_year_val == [2024], "Reference year must strictly be 2024"


def test_ibm_table_3_district_totals():
    """
    Verifies the mathematical identity of Table 3 (District-wise / Mineral-wise):
    Sum of Leases = 2,995
    Sum of Area = 293,811.54 hectares
    """
    with engine.connect() as conn:
        t3_metrics = conn.execute(text("""
            SELECT count(*), sum(lease_count), round(sum(lease_area_ha)::numeric, 2)
            FROM ibm_mining_lease_context
            WHERE table_number = 'Table-3';
        """)).fetchone()

    row_cnt, total_leases, total_area = t3_metrics
    assert row_cnt >= 300, f"Expected ~319 Table 3 rows, got {row_cnt}"
    assert total_leases == 2995, f"Expected exact 2,995 total leases in Table 3, got {total_leases}"
    assert float(total_area) == 293811.54, f"Expected exact 293,811.54 hectares in Table 3, got {total_area}"


def test_ibm_tables_4_5_6_potential_tier_totals():
    """
    Verifies High, Medium, and Low Mineral Potential tier categories and lease sum.
    High (628) + Medium (564) + Low (1,803) == 2,995 total leases.
    """
    with engine.connect() as conn:
        high_cnt = conn.execute(text("SELECT sum(lease_count) FROM ibm_mining_lease_context WHERE table_number = 'Table-4';")).scalar()
        med_cnt = conn.execute(text("SELECT sum(lease_count) FROM ibm_mining_lease_context WHERE table_number = 'Table-5';")).scalar()
        low_cnt = conn.execute(text("SELECT sum(lease_count) FROM ibm_mining_lease_context WHERE table_number = 'Table-6';")).scalar()

    assert high_cnt == 628, f"Expected 628 leases in High Potential districts, got {high_cnt}"
    assert med_cnt == 564, f"Expected 564 leases in Medium Potential districts, got {med_cnt}"
    assert low_cnt == 1803, f"Expected 1,803 leases in Low Potential districts, got {low_cnt}"
    assert high_cnt + med_cnt + low_cnt == 2995, "Sum of potential tier leases must equal 2,995"


def test_zero_coordinate_hallucination_and_facility_registry_integrity():
    """
    Verifies that no fake point coordinates were invented from IBM aggregate tables,
    and that canonical physical facilities (industrial_facilities) remained unmutated.
    """
    with engine.connect() as conn:
        # Check industrial_facilities count
        fac_count = conn.execute(text("SELECT count(*) FROM industrial_facilities;")).scalar()
        # Verify no facility source is mistakenly created from aggregate tables
        ibm_fac_count = conn.execute(text("SELECT count(*) FROM industrial_facilities WHERE source = 'IBM_AGGREGATE';")).scalar()

    assert fac_count == 35662, f"Canonical facilities must remain exactly 35,662, got {fac_count}"
    assert ibm_fac_count == 0, "No aggregate IBM records should be converted into fake physical facilities"


def test_fastapi_ibm_mining_leases_endpoint(client):
    """
    Verifies FastAPI GET /api/v1/facilities/ibm/mining-leases endpoint filters.
    """
    # 1. Query by table_number and state
    res = client.get("/api/v1/facilities/ibm/mining-leases?table_number=Table-3&state=Andhra%20Pradesh&limit=10")
    assert res.status_code == 200
    data = res.json()
    assert len(data) > 0
    assert data[0]["state"] == "Andhra Pradesh"
    assert data[0]["table_number"] == "Table-3"
    assert data[0]["provisional_flag"] is True

    # 2. Query by potential_category
    res_pot = client.get("/api/v1/facilities/ibm/mining-leases?potential_category=HIGH")
    assert res_pot.status_code == 200
    high_data = res_pot.json()
    assert len(high_data) == 4, f"Expected 4 high potential districts, got {len(high_data)}"
