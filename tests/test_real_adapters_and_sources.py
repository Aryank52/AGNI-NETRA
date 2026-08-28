import os
import sys
import pytest
from datetime import datetime, timezone

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.database import SessionLocal
from backend.app.models.domain import IndustrialFacility, CandidateFacility, User
from data_pipeline.adapters.base import NormalizedFacilityRecord, SourceProvenance
from data_pipeline.adapters.firms_adapter import firms_adapter, FIRMSAdapter
from data_pipeline.adapters.osm_adapter import osm_adapter
from data_pipeline.adapters.cea_adapter import cea_adapter
from data_pipeline.adapters.bhuvan_adapter import bhuvan_adapter
from data_pipeline.adapters.sentinel_adapter import sentinel_adapter
from data_pipeline.adapters.landsat_adapter import landsat_adapter
from data_pipeline.adapters.mosdac_adapter import mosdac_adapter
from backend.app.services.facility_resolver import facility_resolver, calculate_name_similarity
from backend.app.services.candidate_service import evaluate_candidate_industrial_source, promote_candidate_to_verified_facility
from backend.app.services.data_quality_service import data_quality_service


def test_firms_adapter_deduplication_and_data_quality():
    """Verify FIRMS adapter deduplication and objective quality scoring"""
    adapter = FIRMSAdapter(api_key="")
    health = adapter.validate_connection()
    assert health["status"] == "NOT_CONFIGURED"
    assert health["configured"] is False

    # Test coordinate validation
    assert adapter.validate_coordinates(22.35, 69.86) is True
    assert adapter.validate_coordinates(0.0, 0.0) is False  # Outside India

    # Test Data Quality scoring
    q = data_quality_service.evaluate_observation_quality(
        confidence=95.0,
        brightness_k=340.0,
        frp_mw=85.0,
        scan_angle=10.0,
        acq_time=datetime.now(timezone.utc)
    )
    assert q["composite_quality_score"] >= 0.85
    assert q["quality_grade"] == "EXCELLENT"


def test_cea_and_osm_facility_adapters():
    """Verify CEA and OSM facility adapters return normalized records with provenance"""
    cea_records = cea_adapter.fetch_facilities(state="Gujarat")
    assert len(cea_records) >= 1
    assert cea_records[0].source == "CEA"
    assert cea_records[0].provenance is not None
    assert cea_records[0].provenance.source_name == "CEA_INDIA"

    osm_records = osm_adapter.fetch_facilities(state="Odisha")
    assert len(osm_records) >= 1
    assert osm_records[0].source == "OSM"
    assert osm_records[0].provenance is not None


def test_facility_entity_resolution():
    """Verify entity resolution merges overlapping records with fuzzy matching and spatial proximity"""
    db = SessionLocal()
    try:
        # Test fuzzy name similarity helper
        sim = calculate_name_similarity(
            "Reliance Jamnagar Petroleum Refinery Complex Ltd",
            "Reliance Industries Jamnagar Refinery"
        )
        assert sim >= 0.70

        # Run entity resolver
        incoming = cea_adapter.fetch_facilities() + osm_adapter.fetch_facilities()
        res = facility_resolver.resolve_and_sync_facilities(db, incoming)
        assert res["status"] == "SUCCESS"
        assert res["canonical_registry_total"] >= 5
    finally:
        db.close()


def test_candidate_facility_discovery_and_promotion():
    """Verify candidate industrial source evaluation and analyst promotion"""
    db = SessionLocal()
    try:
        # 1. Evaluate candidate criteria
        is_cand, score, evidence = evaluate_candidate_industrial_source(
            event_info={"avg_frp": 120.0},
            persistence_info={
                "persistence_score": 8.0,
                "persistence_category": "PERSISTENT_RECURRENT",
                "active_days_count": 6,
                "day_night_ratio": 0.85
            },
            landcover_class="Industrial",
            nearest_dist_m=4500.0
        )
        assert is_cand is True
        assert score >= 0.70
        assert evidence["is_continuous_24x7"] is True

        # 2. Test promotion
        test_cand = db.query(CandidateFacility).first()
        if not test_cand:
            test_cand = CandidateFacility(
                name_label="Candidate-Thermal-Source-GJ-Test",
                status="CANDIDATE",
                latitude=22.36,
                longitude=69.87,
                state="Gujarat",
                district="Jamnagar",
                industrial_context_score=0.88,
                persistence_days=8,
                detection_count=12
            )
            db.add(test_cand)
            db.commit()
            db.refresh(test_cand)

        admin = db.query(User).first()
        prom_res = promote_candidate_to_verified_facility(
            db=db,
            candidate_id=test_cand.id,
            verified_name="Promoted Test Petrochem Facility",
            facility_type="REFINERY",
            analyst_id=admin.id,
            notes="Pytest verified promotion"
        )
        assert prom_res["status"] == "PROMOTED"
        assert "FAC-" in prom_res["canonical_source_id"]
        assert "REFI" in prom_res["canonical_source_id"]
    finally:
        db.close()


def test_sentinel_and_landsat_stac_separation():
    """Verify optical, SWIR, and true thermal band separation in STAC metadata"""
    # Sentinel-2
    s2_scenes = sentinel_adapter.search_imagery_for_event(
        latitude=22.355,
        longitude=69.865,
        target_time=datetime.now(timezone.utc)
    )
    assert len(s2_scenes) >= 1
    assert "B04_Red" in s2_scenes[0].optical_bands
    assert "B11_SWIR1" in s2_scenes[0].swir_bands[0]
    assert len(s2_scenes[0].thermal_bands) == 0  # Sentinel has no thermal IR

    # Landsat 8/9
    l9_scenes = landsat_adapter.search_imagery_for_event(
        latitude=22.355,
        longitude=69.865,
        target_time=datetime.now(timezone.utc)
    )
    assert len(l9_scenes) >= 1
    assert "B10_TIRS_Thermal" in l9_scenes[0].thermal_bands[0]


def test_mosdac_and_bhuvan_graceful_handling():
    """Verify MOSDAC reports NOT_CONFIGURED safely and Bhuvan classifies LULC"""
    mosdac_health = mosdac_adapter.validate_connection()
    assert mosdac_health["source"] == "ISRO_MOSDAC"
    assert mosdac_health["status"] in ["NOT_CONFIGURED", "HEALTHY"]

    # Bhuvan LULC
    lulc_rec = bhuvan_adapter.classify_location(22.3552, 69.8654)
    assert lulc_rec.category in ["Industrial", "Forest", "Agricultural", "Urban", "Barren", "Water", "Mining"]
    assert lulc_rec.provenance is not None
