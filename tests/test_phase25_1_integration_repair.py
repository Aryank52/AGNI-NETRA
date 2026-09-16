"""
AGNI-NETRA — Phase 25.1 Integration Repair & Cross-System Validation Test Suite

Validates:
1. /api/v1/analytics/command-center returns HTTP 200 with full KPI & stream freshness telemetry
2. /api/v1/gis/mining returns HTTP 200 authentic GeoJSON FeatureCollection without PostGIS crash
3. /api/v1/gis/protected-areas returns HTTP 200 authentic FeatureCollection with 11 WII protected areas
4. /api/v1/gis/lulc returns HTTP 200 authentic FeatureCollection with 15 Bhuvan LULC polygons
5. /api/v1/gis/dossier/{event_id} returns HTTP 200 multi-source 7-layer spatial investigation dossier
6. Dialect-aware geodesic calculation (haversine_distance_meters)
7. Authoritative database table counts (protected_areas >= 11, lulc_spatial_features >= 15)
8. Strict safety invariant gates:
   - ENABLE_OPERATIONAL_DISPATCH_GATE = False
   - ENABLE_AUTOMATED_MODEL_ACTIVATION = False
"""

import pytest
from datetime import datetime, timezone
from sqlalchemy import text
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.database import SessionLocal, haversine_distance_meters
from backend.app.models.domain import ThermalEvent
from backend.app.core.config import settings

client = TestClient(app)


@pytest.fixture(scope="module")
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="module")
def sample_event(db: Session):
    event = db.query(ThermalEvent).first()
    assert event is not None, "At least one thermal event must exist in database"
    return event


# =============================================================================
# 1. Command Center Telemetry Repair
# =============================================================================

def test_command_center_endpoint():
    """
    Verifies /api/v1/analytics/command-center returns HTTP 200 with complete KPIs and no 500 crashes.
    """
    response = client.get("/api/v1/analytics/command-center")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    assert data["status"] == "OPERATIONAL"
    assert "kpis" in data
    assert "total_live_events" in data["kpis"]
    assert "total_detections_ingested" in data["kpis"]
    assert data["kpis"]["total_live_events"] >= 1
    assert "alert_queues" in data
    assert "stream_freshness_timestamp" in data["kpis"]


# =============================================================================
# 2. GIS Mining Intelligence Endpoint Repair
# =============================================================================

def test_gis_mining_endpoint():
    """
    Verifies /api/v1/gis/mining returns authentic GeoJSON FeatureCollection without ST_AsGeoJSON failure.
    """
    response = client.get("/api/v1/gis/mining?limit=100")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    assert data.get("type") == "FeatureCollection"
    assert "features" in data
    assert isinstance(data["features"], list)
    assert len(data["features"]) >= 1, "Expected at least 1 mining feature"
    first_feat = data["features"][0]
    assert first_feat["type"] == "Feature"
    assert "geometry" in first_feat
    assert "properties" in first_feat
    assert first_feat["properties"].get("layer") == "mining"


# =============================================================================
# 3. GIS Protected Areas & Reserves Endpoint Repair
# =============================================================================

def test_gis_protected_areas_endpoint():
    """
    Verifies /api/v1/gis/protected-areas returns 11 authentic WII Protected Areas.
    """
    response = client.get("/api/v1/gis/protected-areas?limit=50")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    assert data.get("type") == "FeatureCollection"
    assert len(data["features"]) == 11, f"Expected 11 WII Protected Areas, got {len(data['features'])}"
    pa_names = [f["properties"]["name"] for f in data["features"]]
    assert any("Similipal" in name for name in pa_names)
    assert any("Corbett" in name for name in pa_names)
    assert any("Kaziranga" in name for name in pa_names)
    assert any("Gir" in name for name in pa_names)


# =============================================================================
# 4. GIS Bhuvan LULC Endpoint Repair
# =============================================================================

def test_gis_lulc_endpoint():
    """
    Verifies /api/v1/gis/lulc returns 15 authentic ISRO Bhuvan thematic features.
    """
    response = client.get("/api/v1/gis/lulc?limit=50")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    assert data.get("type") == "FeatureCollection"
    assert len(data["features"]) == 15, f"Expected 15 Bhuvan LULC features, got {len(data['features'])}"
    feat_classes = [f["properties"]["canonical_class"] for f in data["features"]]
    assert "BUILT_UP_INDUSTRIAL" in feat_classes


# =============================================================================
# 5. Multi-Source Spatial Dossier Endpoint Repair
# =============================================================================

def test_gis_dossier_endpoint(sample_event: ThermalEvent):
    """
    Verifies /api/v1/gis/dossier/{event_id} returns the complete 7-layer spatial dossier
    plus Phase 25 historical intelligence without crashing.
    """
    response = client.get(f"/api/v1/gis/dossier/{sample_event.id}")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()

    # Identity & Telemetry
    assert data["event_id"] == sample_event.id
    assert "location" in data
    assert "telemetry" in data
    assert "spatial_context_enrichment" in data

    # 7 Layers Proximity
    enrichment = data["spatial_context_enrichment"]
    assert "nearest_industrial_facilities" in enrichment
    assert isinstance(enrichment["nearest_industrial_facilities"], list)
    assert len(enrichment["nearest_industrial_facilities"]) >= 1

    assert "nearest_power_stations" in enrichment
    assert isinstance(enrichment["nearest_power_stations"], list)

    assert "nearest_protected_areas" in enrichment
    assert isinstance(enrichment["nearest_protected_areas"], list)

    # Historical Intelligence Preservation
    assert "historical_intelligence" in data
    assert data["historical_intelligence"] is not None

    # Intelligence Coverage
    assert "intelligence_coverage" in data
    assert data["intelligence_coverage"]["firms_telemetry"] is True


# =============================================================================
# 6. Geodesic Distance Calculation
# =============================================================================

def test_haversine_geodesic_distance():
    """
    Verifies haversine_distance_meters accurately calculates distances across India.
    New Delhi (28.6139, 77.2090) to Mumbai (19.0760, 72.8777) is ~1,148 km.
    """
    dist = haversine_distance_meters(28.6139, 77.2090, 19.0760, 72.8777)
    assert 1_140_000 <= dist <= 1_160_000, f"Distance {dist}m out of expected range ~1,148,000m"


# =============================================================================
# 7. Database Counts & Immutability Verification
# =============================================================================

def test_database_spatial_counts(db: Session):
    """
    Verifies that authentic GIS layer counts in the database match expected baseline.
    """
    pa_count = db.execute(text("SELECT COUNT(*) FROM protected_areas;")).scalar()
    lulc_count = db.execute(text("SELECT COUNT(*) FROM lulc_spatial_features;")).scalar()
    fac_count = db.execute(text("SELECT COUNT(*) FROM industrial_facilities;")).scalar()

    assert pa_count == 11, f"Expected 11 protected_areas, found {pa_count}"
    assert lulc_count == 15, f"Expected 15 lulc_spatial_features, found {lulc_count}"
    assert fac_count >= 20, f"Expected >=20 industrial_facilities, found {fac_count}"


# =============================================================================
# 8. Platform Invariants & Safety Gates
# =============================================================================

def test_safety_invariants_preserved():
    """
    Confirms safety gates remain hard-locked.
    """
    assert settings.ENABLE_OPERATIONAL_DISPATCH_GATE is False
    assert settings.ENABLE_AUTOMATED_MODEL_ACTIVATION is False
