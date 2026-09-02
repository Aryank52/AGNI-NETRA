"""
AGNI-NETRA — Complete Frontend–Backend–PostGIS Integration Test Suite (Phase 16)
Validates:
1. All PostGIS GIS GeoJSON endpoints (/api/v1/gis/*)
2. Spatial bounding-box filtering with PostGIS indexing
3. 7-layer spatial investigation dossier generation & proximity measurements
4. Integration between GIS layer metadata, command center telemetry, and frontend contracts
5. Immutability of historical FIRMS partitions (6,448,666 sealed records)
6. Dispatch safety gates (ENABLE_OPERATIONAL_DISPATCH_GATE = False)
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from backend.app.main import app
from backend.app.core.database import SessionLocal
from backend.app.core.config import settings

client = TestClient(app)


class TestGISCatalogAndMetadata:
    """Verifies the master GIS layer catalog and table connectivity."""

    def test_gis_layers_catalog(self):
        response = client.get("/api/v1/gis/layers")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["status"] == "OPERATIONAL"
        assert "layers" in data
        layer_ids = [l["id"] for l in data["layers"]]
        expected_layers = [
            "thermal_events", "industrial_facilities", "power_stations",
            "mining", "protected_areas", "lulc", "admin_states", "admin_districts"
        ]
        for el in expected_layers:
            assert el in layer_ids, f"Layer {el} missing from GIS catalog"


class TestGISGeoJSONEndpoints:
    """Verifies all spatial GeoJSON FeatureCollection endpoints."""

    def test_thermal_events_geojson(self):
        response = client.get("/api/v1/gis/thermal-events?limit=20")
        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "FeatureCollection"
        assert len(data["features"]) > 0
        feat = data["features"][0]
        assert feat["geometry"]["type"] == "Point"
        assert len(feat["geometry"]["coordinates"]) == 2
        props = feat["properties"]
        assert "event_code" in props
        assert "predicted_class" in props
        assert "risk_level" in props
        assert "max_frp" in props

    def test_industrial_facilities_geojson_with_bbox(self):
        # National query
        response = client.get("/api/v1/gis/industrial-facilities?limit=25")
        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "FeatureCollection"
        assert len(data["features"]) > 0
        props = data["features"][0]["properties"]
        assert "name" in props
        assert "facility_type" in props
        assert "master_sector" in props

        # BBox query (Western India: Gujarat / Maharashtra)
        bbox_response = client.get("/api/v1/gis/industrial-facilities?bbox=68.0,18.0,76.0,24.0&limit=25")
        assert bbox_response.status_code == 200
        bbox_data = bbox_response.json()
        assert bbox_data["type"] == "FeatureCollection"
        for f in bbox_data["features"]:
            lon, lat = f["geometry"]["coordinates"]
            assert 68.0 <= lon <= 76.0, f"Longitude {lon} out of bbox"
            assert 18.0 <= lat <= 24.0, f"Latitude {lat} out of bbox"

    def test_power_stations_geojson(self):
        response = client.get("/api/v1/gis/power-stations?limit=20")
        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "FeatureCollection"
        assert len(data["features"]) > 0
        props = data["features"][0]["properties"]
        assert "name" in props
        assert "prime_mover" in props
        assert "cea_organisation" in props

    def test_mining_intelligence_geojson(self):
        response = client.get("/api/v1/gis/mining?limit=20")
        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "FeatureCollection"
        assert len(data["features"]) > 0
        props = data["features"][0]["properties"]
        assert "name" in props
        assert "mineral" in props

    def test_protected_areas_geojson(self):
        response = client.get("/api/v1/gis/protected-areas?limit=15")
        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "FeatureCollection"
        assert len(data["features"]) > 0
        props = data["features"][0]["properties"]
        assert "name" in props
        assert "pa_type" in props

    def test_lulc_geojson(self):
        response = client.get("/api/v1/gis/lulc?limit=15")
        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "FeatureCollection"
        assert len(data["features"]) > 0
        props = data["features"][0]["properties"]
        assert "canonical_class" in props

    def test_admin_states_geojson(self):
        response = client.get("/api/v1/gis/admin/states?simplify=0.01")
        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "FeatureCollection"
        # 36 States & UTs in India
        assert len(data["features"]) >= 30
        props = data["features"][0]["properties"]
        assert "state_name" in props
        assert "state_code" in props

    def test_admin_districts_geojson(self):
        response = client.get("/api/v1/gis/admin/districts?state=Maharashtra&limit=50")
        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "FeatureCollection"
        assert len(data["features"]) > 0
        props = data["features"][0]["properties"]
        assert "district_name" in props
        assert props["state_name"] == "Maharashtra"


class TestSpatialInvestigationDossier:
    """Verifies the 7-layer spatial evidence dossier for selected thermal events."""

    def test_dossier_generation_for_active_event(self):
        # 1. Fetch a sample active event ID
        events_res = client.get("/api/v1/gis/thermal-events?limit=1")
        assert events_res.status_code == 200
        events_data = events_res.json()
        assert len(events_data["features"]) > 0
        sample_id = events_data["features"][0]["properties"]["id"]

        # 2. Retrieve 7-layer dossier
        dossier_res = client.get(f"/api/v1/gis/dossier/{sample_id}")
        assert dossier_res.status_code == 200
        dossier = dossier_res.json()

        assert dossier["event_id"] == sample_id
        assert "event_code" in dossier
        assert "location" in dossier
        assert "telemetry" in dossier
        assert "ml_intelligence" in dossier
        assert "risk_assessment" in dossier
        assert "spatial_context_enrichment" in dossier
        assert "intelligence_coverage" in dossier
        assert "alert_workflow" in dossier

        # Verify Proximity Matrix
        spatial = dossier["spatial_context_enrichment"]
        assert "nearest_industrial_facilities" in spatial
        assert "nearest_power_stations" in spatial
        assert "district_forest_stats" in spatial

        # Verify Intelligence Coverage Provenance
        cov = dossier["intelligence_coverage"]
        assert cov["firms_telemetry"] is True
        assert isinstance(cov["industrial_facility"], bool)
        assert isinstance(cov["cea_power_station"], bool)
        assert isinstance(cov["mining_intelligence"], bool)
        assert isinstance(cov["forest_intelligence"], bool)
        assert isinstance(cov["protected_area"], bool)
        assert isinstance(cov["bhuvan_lulc"], bool)


class TestSafetyInvariantsAndPartitionIntegrity:
    """Verifies that historical records remain sealed and dispatch safety invariants held."""

    def test_historical_firms_partition_immutability(self):
        db = SessionLocal()
        try:
            sealed_sum = db.execute(text("""
                SELECT COUNT(*) FROM thermal_detections
                WHERE acq_timestamp >= '2022-01-01' AND acq_timestamp < '2026-01-01';
            """)).scalar()
            # Must match exact Phase 15 sealed baseline of 6,448,666 records
            assert sealed_sum == 6448666, f"Historical records modified: {sealed_sum} != 6448666"
        finally:
            db.close()

    def test_dispatch_safety_gates(self):
        assert getattr(settings, "ENABLE_OPERATIONAL_DISPATCH_GATE", False) is False
        db = SessionLocal()
        try:
            live_dispatches = db.execute(text("""
                SELECT COUNT(*) FROM alerts WHERE is_operational_dispatch = True;
            """)).scalar()
            assert live_dispatches == 0, f"Safety violation: {live_dispatches} live dispatches found"
        finally:
            db.close()
