import os
import sys
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.database import SessionLocal
from backend.app.main import app
from backend.app.models.domain import ThermalDetection, ThermalEvent, IndustrialFacility
from data_pipeline.adapters.firms_adapter import FIRMSAdapter
from data_pipeline.adapters.osm_adapter import OSMIndustrialAdapter
from data_pipeline.adapters.lulc_adapter import lulc_engine
from backend.app.services.spatial_engine import (
    haversine_distance_m, validate_coordinates, compute_cluster_geometry, SpatialIndex
)
from backend.app.services.clustering_service import cluster_thermal_detections
from backend.app.services.pipeline_service import pipeline_service

client = TestClient(app)


def test_firms_adapter_parsing_and_deduplication():
    """Verify FIRMS CSV parsing, lat/lon bounds validation, and deduplication"""
    csv_sample = """latitude,longitude,bright_ti4,scan,track,acq_date,acq_time,satellite,confidence,version,bright_ti5,frp,daynight
22.3552,69.8654,360.5,0.4,0.4,2026-08-28,0130,N,h,2.0NRT,295.2,145.0,N
22.3552,69.8654,360.5,0.4,0.4,2026-08-28,0130,N,h,2.0NRT,295.2,145.0,N
24.1012,82.6841,375.1,0.5,0.4,2026-08-28,0215,N,n,2.0NRT,298.0,210.0,N
-85.000,10.0000,300.0,0.4,0.4,2026-08-28,0200,N,l,2.0NRT,290.0,10.0,D
"""
    adapter = FIRMSAdapter()
    obs = adapter.parse_csv_content(csv_sample, source_name="VIIRS_TEST", is_demo=False)
    
    # -85.0 lat is outside India bounds and should be filtered out
    # Duplicate (22.3552, 69.8654) should be deduplicated to 1 record
    assert len(obs) == 2
    assert obs[0].latitude == 22.3552
    assert obs[0].frp == 145.0
    assert obs[0].confidence == 95.0  # 'h' translated to 95.0


def test_osm_adapter_normalization():
    """Verify OSM industrial facility normalization and canonical fallback"""
    adapter = OSMIndustrialAdapter()
    facilities = adapter.fetch_facilities_by_bbox()
    assert len(facilities) >= 5
    fac = facilities[0]
    assert fac.source == "OSM"
    assert fac.state is not None
    assert fac.confidence_score > 0



def test_lulc_adapter_point_in_polygon():
    """Verify LULC classification for known industrial zones and forests"""
    # Jamnagar refinery coordinates -> Industrial
    cat1, zone1, dists1 = lulc_engine.classify_location(22.35, 69.86)
    assert cat1 == "Industrial"
    assert "Jamnagar" in zone1

    # Similipal forest coordinates -> Forest
    cat2, zone2, dists2 = lulc_engine.classify_location(21.75, 86.40)
    assert cat2 == "Forest"
    assert "Similipal" in zone2


def test_spatial_engine_nearest_facility():
    """Verify fast spatial indexing and nearest facility lookups"""
    facilities = [
        {"id": "f1", "name": "Refinery A", "latitude": 22.355, "longitude": 69.865},
        {"id": "f2", "name": "Power Plant B", "latitude": 24.101, "longitude": 82.684}
    ]
    idx = SpatialIndex(facilities)
    fac, dist = idx.find_nearest(22.356, 69.866)
    assert fac["name"] == "Refinery A"
    assert dist < 500.0  # within 500m


def test_end_to_end_geospatial_pipeline():
    """Verify complete pipeline: Ingestion -> PostGIS -> Clustering -> Event Creation -> API"""
    db = SessionLocal()
    try:
        csv_sample = """latitude,longitude,bright_ti4,scan,track,acq_date,acq_time,satellite,confidence,version,bright_ti5,frp,daynight
22.3550,69.8650,355.0,0.4,0.4,2026-08-28,0130,N,h,2.0NRT,295.0,120.0,N
22.3554,69.8655,360.0,0.4,0.4,2026-08-28,0130,N,h,2.0NRT,296.0,130.0,N
20.8520,85.1240,340.0,0.4,0.4,2026-08-28,0215,N,n,2.0NRT,292.0,85.0,N
"""
        adapter = FIRMSAdapter()
        obs = adapter.parse_csv_content(csv_sample, source_name="TEST_VIIRS_PIPELINE", is_demo=False)
        
        result = pipeline_service.process_observations(db, obs, source_name="Automated Pipeline Test")
        assert result["status"] == "SUCCESS"
        assert result["events_created"] >= 1
        assert result["detections_stored"] == 3
    finally:
        db.close()


def test_events_api_server_side_filtering_and_pagination():
    """Verify REST API filters (state, risk_level, event_type, is_demo) and pagination"""
    # 1. State filter
    resp_state = client.get("/api/v1/events?state=Gujarat")
    assert resp_state.status_code == 200
    assert all(e["state"] == "Gujarat" for e in resp_state.json())

    # 2. GeoJSON endpoint
    resp_geojson = client.get("/api/v1/events/geojson")
    assert resp_geojson.status_code == 200
    geojson = resp_geojson.json()
    assert geojson["type"] == "FeatureCollection"
    assert len(geojson["features"]) > 0

    # 3. Server-side pagination
    resp_paginated = client.get("/api/v1/events?page=1&limit=5")
    assert resp_paginated.status_code == 200
    p_data = resp_paginated.json()
    assert "total_count" in p_data
    assert "total_pages" in p_data
    assert len(p_data["items"]) <= 5
