"""
AGNI-NETRA — Automated Pytest Suite for IBM Mining Intelligence Fusion Layer
Verifies OSM geometry fusion, IBM lease context linkage, multi-distance FIRMS telemetry, and API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from backend.app.main import app
from backend.app.core.database import SessionLocal, engine
from backend.app.models.domain import FacilityMiningEvidence, MiningThermalAssociation, CandidateFacility

client = TestClient(app)


def test_canonical_facilities_integrity():
    """Verify that canonical facility count remains non-destructively preserved at 35,662."""
    with engine.connect() as conn:
        count = conn.execute(text("SELECT count(*) FROM industrial_facilities;")).scalar()
        assert count == 35662, f"Expected 35,662 canonical facilities, found {count}"


def test_mining_evidence_ingestion():
    """Verify that all target OSM mining facilities are populated in facility_mining_evidence."""
    db = SessionLocal()
    try:
        count = db.query(FacilityMiningEvidence).count()
        assert count >= 200, f"Expected at least 200 mining evidence rows, found {count}"
        
        sample = db.query(FacilityMiningEvidence).filter(
            FacilityMiningEvidence.thermal_activity_present == True
        ).first()
        assert sample is not None
        assert sample.facility_id is not None
        assert sample.facility_name is not None
        assert sample.latitude != 0.0
        assert sample.longitude != 0.0
        assert sample.confidence_score > 0.0
    finally:
        db.close()


def test_ibm_lease_context_linkage():
    """Verify that mining facilities are enriched with official IBM lease context."""
    db = SessionLocal()
    try:
        enriched_count = db.query(FacilityMiningEvidence).filter(
            FacilityMiningEvidence.ibm_lease_context_present == True
        ).count()
        total_count = db.query(FacilityMiningEvidence).count()
        assert total_count > 0
        coverage = (enriched_count / total_count) * 100
        assert coverage >= 90.0, f"Expected >= 90% IBM lease context coverage, got {coverage:.1f}%"
    finally:
        db.close()


def test_multi_distance_thermal_associations():
    """Verify multi-distance FIRMS associations (500m, 1km, 2km) and statistical metrics."""
    db = SessionLocal()
    try:
        bands = db.query(MiningThermalAssociation.distance_band).distinct().all()
        band_names = {b[0] for b in bands}
        assert {"500m", "1km", "2km"}.issubset(band_names), f"Missing distance bands: {band_names}"

        sample_assoc = db.query(MiningThermalAssociation).filter(
            MiningThermalAssociation.detection_count > 5
        ).first()
        if sample_assoc:
            assert sample_assoc.mean_frp is not None
            assert sample_assoc.p90_frp is not None
            assert sample_assoc.active_days_count > 0
            assert sample_assoc.recurrence_rate is not None
    finally:
        db.close()


def test_scientific_attribution_phrasing():
    """Verify that scientific attribution adheres strictly to non-causal spatial association principles."""
    db = SessionLocal()
    try:
        active_mines = db.query(FacilityMiningEvidence).filter(
            FacilityMiningEvidence.thermal_activity_present == True
        ).limit(10).all()

        for mine in active_mines:
            attr = mine.scientific_attribution
            assert "spatially associated" in attr or "associated with a mining context" in attr
            assert "proves this hotspot is a mine" not in attr.lower()
    finally:
        db.close()


def test_candidate_mining_sources_status():
    """Verify that detected candidate mining clusters are assigned status CANDIDATE (never VERIFIED)."""
    db = SessionLocal()
    try:
        candidates = db.query(CandidateFacility).filter(
            CandidateFacility.name_label.like("Candidate-Mining-Source%")
        ).all()
        assert len(candidates) > 0, "Expected candidate mining sources to be generated"
        for cand in candidates:
            assert cand.status == "CANDIDATE", f"Candidate has invalid status: {cand.status}"
            assert cand.industrial_context_score <= 0.85
    finally:
        db.close()


def test_mining_api_facilities_endpoint():
    """Test GET /api/v1/mining/facilities with query parameters."""
    response = client.get("/api/v1/mining/facilities?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) <= 10
    if len(data) > 0:
        first = data[0]
        assert "facility_id" in first
        assert "facility_name" in first
        assert "firms_associated_2km" in first
        assert "ibm_lease_context_present" in first
        assert "scientific_attribution" in first


def test_mining_api_context_summary_endpoint():
    """Test GET /api/v1/mining/context endpoint."""
    response = client.get("/api/v1/mining/context")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    first = data[0]
    assert "state" in first
    assert "facility_count" in first


def test_mining_api_thermal_associations_endpoint():
    """Test GET /api/v1/mining/thermal-associations endpoint."""
    response = client.get("/api/v1/mining/thermal-associations?distance_band=1km&limit=10")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if len(data) > 0:
        assert data[0]["distance_band"] == "1km"


def test_mining_api_candidate_sources_endpoint():
    """Test GET /api/v1/mining/candidate-sources endpoint."""
    response = client.get("/api/v1/mining/candidate-sources?min_detections=3")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    for c in data:
        assert c["status"] == "CANDIDATE"
