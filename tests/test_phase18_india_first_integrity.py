"""
AGNI-NETRA — PHASE 18: INDIA-FIRST DATA INTELLIGENCE, COVERAGE & GEOGRAPHIC INTEGRITY
Comprehensive Test Suite verifying all Phase 18 mandatory requirements:
- Sovereign India PostGIS polygon boundary containment (ST_Within against admin_boundaries)
- Strict exclusion of Sri Lanka (lat 6.18 - 6.67, lon 80.86 - 81.17) and neighboring regions
- Administrative hierarchy resolution (36 States/UTs, 735 Districts, 6,824 Subdistricts)
- Non-destructive isolation of out-of-boundary observations (country='OUTSIDE_INDIA')
- Zero leakage in live telemetry queries (india_only=True)
- Canonical India dataset inventory (18 datasets: 9 REAL, 1 DERIVED, 1 FIXTURE, 7 NOT_CONFIGURED)
- 10-point Data Quality Audit (10/10 PASS)
- 11-point India Coverage Scorecard (96.8% EXCELLENT)
- Preserved frozen 5-factor risk formula (0.30*I + 0.25*A + 0.20*E + 0.15*P + 0.10*C)
- Single Master Agent JARVIS commands across all 9 India operational scenarios
- JARVIS out-of-scope country rejection without data hallucination
- Operational Dispatch Gate strictly BLOCKED (ENABLE_OPERATIONAL_DISPATCH_GATE = False)
- Blocked model activation & public safety RBAC
"""

import math
import pytest
from datetime import datetime, timezone
from typing import Dict, Any, List

from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.app.core.database import SessionLocal
from backend.app.core.config import settings
from backend.app.main import app
from backend.app.models.domain import ThermalEvent, IndustrialFacility, IngestionRecordModel
from backend.app.models.jarvis_schemas import JarvisCommandRequest, JarvisResponse, JarvisState
from backend.app.services.india_boundary_service import india_boundary_service
from backend.app.services.data_plane.india_dataset_inventory import india_dataset_inventory
from backend.app.services.data_plane.live_provider_service import live_provider_service
from backend.app.services.jarvis.jarvis_orchestrator import master_orchestrator as jarvis_orchestrator
from backend.app.services.risk_service import RiskService
from backend.app.services.intelligence.context_engine import ContextDiscoveryEngine


@pytest.fixture(scope="module")
def db_session():
    """Provides a transactional database session for tests."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module")
def test_client():
    """FastAPI TestClient for API verification."""
    return TestClient(app)


# ==============================================================================
# 1. SOVEREIGN INDIA BOUNDARY CONTAINMENT & GEOGRAPHIC ENGINE
# ==============================================================================

def test_01_sovereign_india_boundary_polygon_loaded(db_session: Session):
    """Verify PostGIS admin_boundaries table has 36 sovereign States/UTs loaded."""
    count = db_session.execute(
        text("SELECT COUNT(*) FROM admin_boundaries WHERE admin_level = 1")
    ).scalar()
    assert count == 36, f"Expected 36 sovereign States/UTs in admin_boundaries, found {count}"


def test_02_point_inside_india_validation(db_session: Session):
    """Verify points within major Indian cities return is_inside=True with exact State/UT names."""
    indian_points = [
        (28.6139, 77.2090, "Delhi", "National Capital Territory of Delhi / Delhi"),
        (22.3072, 73.1812, "Gujarat", "Vadodara / Gujarat"),
        (19.0760, 72.8777, "Maharashtra", "Mumbai / Maharashtra"),
        (22.5726, 88.3639, "West Bengal", "Kolkata / West Bengal"),
        (13.0827, 80.2707, "Tamil Nadu", "Chennai / Tamil Nadu"),
        (17.3850, 78.4867, "Telangana", "Hyderabad / Telangana"),
    ]
    for lat, lon, expected_state, desc in indian_points:
        is_inside, state, district, subdistrict = india_boundary_service.is_point_inside_india(lat, lon, db=db_session)
        assert is_inside is True, f"Point {desc} ({lat}, {lon}) should be inside India"
        assert state is not None, f"Point {desc} should have a resolved state"
        if "Delhi" in expected_state:
            assert "Delhi" in state
        else:
            assert state == expected_state


def test_03_sri_lanka_exclusion(db_session: Session):
    """
    Verify points in Sri Lanka (including Phase 17 leaked coordinates lat 6.18-6.67, lon 80.86-81.17)
    are strictly excluded and identified as Sri Lanka.
    """
    sri_lanka_points = [
        (6.18, 80.86),   # Leaked FIRMS coordinate from Phase 17
        (6.58, 81.02),   # Hambantota / Southern Province
        (6.9271, 79.8612), # Colombo
        (8.5874, 81.2152), # Trincomalee
    ]
    for lat, lon in sri_lanka_points:
        is_inside, state, district, subdistrict = india_boundary_service.is_point_inside_india(lat, lon, db=db_session)
        assert is_inside is False, f"Point ({lat}, {lon}) in Sri Lanka must NOT be classified inside India"
        assert state is None
        assert district is None
        detected = india_boundary_service.detect_neighboring_country(lat, lon)
        assert detected == "Sri Lanka", f"Expected 'Sri Lanka' for ({lat}, {lon}), got '{detected}'"


def test_04_neighboring_countries_and_maritime_exclusion(db_session: Session):
    """Verify points in other neighboring nations and open ocean are strictly excluded."""
    foreign_points = [
        (24.8607, 67.0011, "Pakistan"),
        (23.8103, 90.4125, "Bangladesh"),
        (27.7172, 85.3240, "Nepal"),
        (27.4728, 89.6393, "Bhutan"),
        (16.8661, 96.1951, "Myanmar"),
        (15.0000, 65.0000, "Arabian Sea"),
        (15.0000, 88.0000, "Bay of Bengal"),
    ]
    for lat, lon, country_desc in foreign_points:
        is_inside, state, district, subdistrict = india_boundary_service.is_point_inside_india(lat, lon, db=db_session)
        assert is_inside is False, f"Coordinate in {country_desc} ({lat}, {lon}) must not be inside India"


def test_05_bbox_not_boundary(db_session: Session):
    """
    Verify that a bounding box is strictly NOT a boundary proxy.
    A coordinate inside the coarse regional BBOX [6.0, 68.0, 37.5, 97.5] but outside the PostGIS polygon
    must fail territorial containment.
    """
    lat, lon = 6.50, 81.00 # Inside BBOX [6.0, 68.0, 37.5, 97.5]
    bbox = [6.0, 68.0, 37.5, 97.5]
    in_bbox = (bbox[0] <= lat <= bbox[2]) and (bbox[1] <= lon <= bbox[3])
    assert in_bbox is True, "Point must be inside coarse BBOX for this test"

    is_inside, _, _, _ = india_boundary_service.is_point_inside_india(lat, lon, db=db_session)
    assert is_inside is False, "Point inside BBOX but outside polygon must FAIL PostGIS boundary check"


def test_06_state_assignment_accuracy(db_session: Session):
    """Verify state assignment matches official Survey of India / LGD state polygons."""
    is_inside, state, district, _ = india_boundary_service.is_point_inside_india(22.3072, 73.1812, db=db_session)
    assert is_inside is True
    assert state == "Gujarat"


def test_07_district_assignment_accuracy(db_session: Session):
    """Verify district resolution resolves to Vadodara district for Vadodara coordinates."""
    is_inside, state, district, _ = india_boundary_service.is_point_inside_india(22.3072, 73.1812, db=db_session)
    assert is_inside is True
    assert state == "Gujarat"
    assert district == "Vadodara"


def test_08_subdistrict_assignment_resolution(db_session: Session):
    """Verify hierarchical context resolution returns valid structured LGD hierarchy."""
    context = india_boundary_service.get_hierarchical_context(22.3072, 73.1812, db=db_session)
    assert context["is_inside_india"] is True
    assert context["state_name"] == "Gujarat"
    assert context["district_name"] == "Vadodara"


# ==============================================================================
# 2. LIVE INGESTION SCOPE & NON-DESTRUCTIVE REMEDIATION
# ==============================================================================

def test_09_live_ingestion_partitions_india_and_foreign(db_session: Session):
    """Verify incoming raw observations are partitioned into India vs outside without data loss."""
    raw_observations = [
        {"latitude": 28.6139, "longitude": 77.2090, "brightness": 320.5, "source": "NASA_FIRMS"},
        {"latitude": 6.1800, "longitude": 80.8600, "brightness": 315.0, "source": "NASA_FIRMS"},
        {"latitude": 22.3072, "longitude": 73.1812, "brightness": 335.2, "source": "NASA_FIRMS"},
        {"latitude": 15.0000, "longitude": 65.0000, "brightness": 305.0, "source": "NASA_FIRMS"},
    ]
    india_records, outside_records = india_boundary_service.filter_live_observations_for_india(
        raw_observations, db=db_session
    )
    assert len(india_records) == 2, f"Expected 2 India records, got {len(india_records)}"
    assert len(outside_records) == 2, f"Expected 2 outside records, got {len(outside_records)}"

    for rec in india_records:
        assert rec["geographic_scope"] == "INDIA"
        assert rec["country"] == "India"
        assert rec.get("admin_state") is not None or rec.get("jurisdiction") is not None

    for rec in outside_records:
        assert rec["geographic_scope"] == "OUTSIDE_INDIA"
        assert rec["country"] == "OUTSIDE_INDIA"
        assert rec.get("detected_country") in ("Sri Lanka", "Arabian Sea")


def test_10_remediation_zero_sri_lanka_leakage(db_session: Session):
    """Verify that after non-destructive remediation, zero Sri Lanka points are tagged country='IND'."""
    leaked_count = db_session.execute(
        text("""
            SELECT COUNT(*) FROM ingestion_records
            WHERE latitude < 10.0 AND longitude BETWEEN 79.0 AND 82.5
            AND country IN ('IND', 'India')
        """)
    ).scalar()
    assert leaked_count == 0, f"Found {leaked_count} Sri Lanka records incorrectly tagged as India"


def test_11_querying_live_data_india_only_returns_zero_foreign(db_session: Session):
    """Verify querying live latest observations with india_only=True returns 100% India records."""
    observations = live_provider_service.get_latest_live_observations(db_session, limit=100, india_only=True)
    assert len(observations) > 0, "Expected at least some live observations"
    for obs in observations:
        assert obs["country"] == "India", f"Observation {obs['record_id']} has non-India country: {obs['country']}"
        assert obs.get("geographic_scope") == "INDIA"


def test_12_querying_live_data_all_retains_foreign_for_audit(db_session: Session):
    """Verify querying live latest observations with india_only=False retains foreign records for audit."""
    all_observations = live_provider_service.get_latest_live_observations(db_session, limit=300, india_only=False)
    outside_records = [o for o in all_observations if o.get("geographic_scope") == "OUTSIDE_INDIA" or o.get("country") == "OUTSIDE_INDIA"]
    assert len(outside_records) > 0, "Audit trail must preserve outside-India observations"


# ==============================================================================
# 3. CANONICAL DATASET INVENTORY & QUALITY AUDIT
# ==============================================================================

def test_13_dataset_inventory_classifies_all_18_datasets(db_session: Session):
    """Verify canonical inventory registers and audits all 18 specified datasets."""
    inventory = india_dataset_inventory.get_canonical_dataset_inventory(db_session)
    assert inventory["total_registered"] == 18, f"Expected 18 datasets, got {inventory['total_registered']}"
    assert inventory["active_operational_count"] == 9
    assert inventory["derived_count"] == 1
    assert inventory["fixture_count"] == 1
    assert inventory["unconfigured_count"] == 7


def test_14_dataset_inventory_classifications_truthful(db_session: Session):
    """Verify datasets are truthfully classified without mock masquerading."""
    inventory = india_dataset_inventory.get_canonical_dataset_inventory(db_session)
    
    def find_ds(keyword: str):
        for d in inventory["datasets"]:
            if keyword.lower() in d["dataset_id"].lower() or keyword.lower() in d.get("provider", "").lower() or keyword.lower() in d.get("name", "").lower():
                return d
        return None

    # REAL production datasets
    assert find_ds("FIRMS")["data_class"] == "REAL"
    assert find_ds("BHUVAN")["data_class"] == "REAL"
    assert find_ds("FSI")["data_class"] == "REAL"
    assert find_ds("CEA")["data_class"] == "REAL"
    assert find_ds("IBM")["data_class"] == "REAL"
    assert find_ds("PARIVESH")["data_class"] == "REAL"
    assert find_ds("ADMIN")["data_class"] == "REAL"

    # DERIVED
    assert find_ds("OPERATIONAL-EVENTS")["data_class"] == "DERIVED"

    # FIXTURE
    assert find_ds("SIMULATION")["data_class"] == "FIXTURE"

    # NOT_CONFIGURED
    assert find_ds("ERA5")["data_class"] == "NOT_CONFIGURED"
    assert find_ds("CAMS")["data_class"] == "NOT_CONFIGURED"
    assert find_ds("SENTINEL2")["data_class"] == "NOT_CONFIGURED"
    assert find_ds("SENTINEL1")["data_class"] == "NOT_CONFIGURED"


def test_15_quality_audit_reports_ten_passing_checks(db_session: Session):
    """Verify 10-point data quality audit reports 10/10 PASS across coordinates, timestamps, and bounds."""
    audit = india_dataset_inventory.run_india_data_quality_audit(db_session)
    assert audit["total_checks"] == 10
    assert audit["checks_passed"] == 10
    assert audit["overall_status"] == "PASS"


def test_16_quality_audit_detects_sri_lanka_isolated(db_session: Session):
    """Verify quality audit specifically checks and confirms the 171 Sri Lanka observations are isolated."""
    audit = india_dataset_inventory.run_india_data_quality_audit(db_session)
    remediated_check = next((c for c in audit["findings"] if "sri_lanka" in c["check"].lower() or "171" in str(c)), None)
    assert remediated_check is not None
    assert remediated_check["status"] == "PASS"


def test_17_coverage_scorecard_dimensions_and_rating(db_session: Session):
    """Verify 11-point India Coverage Scorecard yields EXCELLENT rating and >= 95% coverage."""
    scorecard = india_dataset_inventory.get_india_coverage_scorecard(db_session)
    assert len(scorecard["scorecard_items"]) == 11
    assert scorecard["overall_score_pct"] >= 95.0
    assert scorecard["coverage_rating"] == "EXCELLENT"


# ==============================================================================
# 4. THERMAL INTELLIGENCE & CONTEXTUAL PIPELINE INTEGRITY
# ==============================================================================

def test_18_thermal_events_sovereign_containment(db_session: Session):
    """Verify all existing operational thermal events are 100% within sovereign India boundaries."""
    non_indian_events = db_session.execute(
        text("""
            SELECT COUNT(*) FROM thermal_events te
            WHERE NOT EXISTS (
                SELECT 1 FROM admin_boundaries ab
                WHERE ab.admin_level = 1
                AND ST_Within(ST_SetSRID(ST_MakePoint(te.longitude, te.latitude), 4326), ab.geom)
            )
        """)
    ).scalar()
    assert non_indian_events == 0, f"Found {non_indian_events} thermal events outside India boundary"


def test_19_context_engine_sets_conflicting_for_foreign_event(db_session: Session):
    """Verify ContextDiscoveryEngine marks administrative context as CONFLICTING for out-of-boundary coordinates."""
    engine = ContextDiscoveryEngine()
    # Test coordinates in Sri Lanka
    ctx, rel = engine._discover_administrative(db_session, "EV-TEST-001", 6.58, 81.02, None, None)
    assert rel.is_conflicting is True
    assert ctx.country == "OUTSIDE_INDIA"
    assert rel.category == "OUTSIDE_BOUNDARY"


def test_20_context_engine_populates_authoritative_hierarchy_for_indian_event(db_session: Session):
    """Verify ContextDiscoveryEngine resolves valid administrative context for Indian coordinate."""
    engine = ContextDiscoveryEngine()
    ctx, rel = engine._discover_administrative(db_session, "EV-TEST-002", 22.3072, 73.1812, None, None)
    assert rel.is_conflicting is False
    assert rel.is_supporting is True
    assert ctx.country == "India"
    assert ctx.state == "Gujarat"
    assert ctx.district == "Vadodara"


def test_21_risk_formula_weights_exact():
    """Verify frozen 5-factor risk formula weights in RiskService (0.30, 0.25, 0.20, 0.15, 0.10)."""
    expected_weights = {
        "intensity": 0.30,
        "proximity": 0.25,
        "environmental": 0.20,
        "persistence": 0.15,
        "confidence": 0.10,
    }
    total_weight = sum(expected_weights.values())
    assert math.isclose(total_weight, 1.0, rel_tol=1e-5)
    
    # Test formula directly with known inputs
    risk = RiskService.compute_5factor_risk_score(
        intensity=80.0,
        proximity=60.0,
        environmental=70.0,
        persistence=90.0,
        confidence=85.0
    )
    expected_score = (0.30 * 80.0) + (0.25 * 60.0) + (0.20 * 70.0) + (0.15 * 90.0) + (0.10 * 85.0)
    assert math.isclose(risk, expected_score, rel_tol=1e-3)


def test_22_risk_scores_strictly_bounded():
    """Verify risk scores never exceed 100.0 or drop below 0.0 even under boundary inputs."""
    min_risk = RiskService.compute_5factor_risk_score(0.0, 0.0, 0.0, 0.0, 0.0)
    max_risk = RiskService.compute_5factor_risk_score(100.0, 100.0, 100.0, 100.0, 100.0)
    clamp_high = RiskService.compute_5factor_risk_score(150.0, 200.0, 120.0, 110.0, 105.0)
    clamp_low = RiskService.compute_5factor_risk_score(-20.0, -10.0, -5.0, 0.0, 0.0)

    assert min_risk == 0.0
    assert max_risk == 100.0
    assert clamp_high <= 100.0
    assert clamp_low >= 0.0


# ==============================================================================
# 5. MASTER AGENT JARVIS INDIA-FIRST COMMAND SUITE
# ==============================================================================

def test_23_jarvis_single_master_agent_invariant():
    """Verify JARVIS operates as a single Master Orchestrator with zero subagents spawned."""
    assert hasattr(jarvis_orchestrator, "execute_command")
    assert not hasattr(jarvis_orchestrator, "subagents")
    assert not hasattr(jarvis_orchestrator, "worker_swarm")


def test_24_jarvis_command_highest_risk_industrial_india(db_session: Session):
    """Verify execution of: 'Show the highest-risk industrial thermal events in India.'"""
    req = JarvisCommandRequest(command="Show the highest-risk industrial thermal events in India.")
    res = jarvis_orchestrator.execute_command(db_session, req)
    assert res.state == JarvisState.COMPLETED
    assert res.dispatch_gate_blocked is True
    assert "India" in res.summary
    assert len(res.details.get("events", [])) > 0


def test_25_jarvis_command_power_plants_persistence(db_session: Session):
    """Verify execution of: 'Find persistent thermal activity around Indian power plants.'"""
    req = JarvisCommandRequest(command="Find persistent thermal activity around Indian power plants.")
    res = jarvis_orchestrator.execute_command(db_session, req)
    assert res.state == JarvisState.COMPLETED
    assert res.dispatch_gate_blocked is True
    assert "power plant" in res.summary.lower()


def test_26_jarvis_command_state_investigation_maharashtra(db_session: Session):
    """Verify execution of: 'Investigate abnormal thermal activity in Maharashtra.'"""
    req = JarvisCommandRequest(command="Investigate abnormal thermal activity in Maharashtra.")
    res = jarvis_orchestrator.execute_command(db_session, req)
    assert res.state == JarvisState.COMPLETED
    assert res.dispatch_gate_blocked is True
    assert "Maharashtra" in res.summary
    assert res.details.get("state") == "Maharashtra"


def test_27_jarvis_command_corridor_comparison_gujarat_odisha(db_session: Session):
    """Verify execution of: 'Compare industrial thermal activity in Gujarat and Odisha.'"""
    req = JarvisCommandRequest(command="Compare industrial thermal activity in Gujarat and Odisha.")
    res = jarvis_orchestrator.execute_command(db_session, req)
    assert res.state == JarvisState.COMPLETED
    assert res.dispatch_gate_blocked is True
    assert "Gujarat" in res.summary
    assert "Odisha" in res.summary


def test_28_jarvis_command_mining_regions_persistence(db_session: Session):
    """Verify execution of: 'Which mining regions show persistent thermal activity?'"""
    req = JarvisCommandRequest(command="Which mining regions show persistent thermal activity?")
    res = jarvis_orchestrator.execute_command(db_session, req)
    assert res.state == JarvisState.COMPLETED
    assert res.dispatch_gate_blocked is True
    assert "mining" in res.summary.lower()


def test_29_jarvis_command_risk_explanation(db_session: Session):
    """Verify execution of: 'Explain why this Indian event received a high risk score.'"""
    req = JarvisCommandRequest(command="Explain why this Indian event received a high risk score.")
    res = jarvis_orchestrator.execute_command(db_session, req)
    assert res.state == JarvisState.COMPLETED
    assert res.dispatch_gate_blocked is True
    assert "risk breakdown" in res.summary.lower() or "risk" in res.summary.lower()
    assert "weights" in res.details or "0.3" in str(res.details) or "risk_score" in res.details


def test_30_jarvis_command_evidence_dossier(db_session: Session):
    """Verify execution of: 'What evidence supports this event?'"""
    req = JarvisCommandRequest(command="What evidence supports this event?")
    res = jarvis_orchestrator.execute_command(db_session, req)
    assert res.state == JarvisState.COMPLETED
    assert res.dispatch_gate_blocked is True
    assert "evidence dossier" in res.summary.lower()
    assert "evidence_sources" in res.details or "evidence" in str(res.details) or res.fused_evidence is not None


def test_31_jarvis_command_intelligence_report(db_session: Session):
    """Verify execution of: 'Generate an India industrial thermal intelligence report.'"""
    req = JarvisCommandRequest(command="Generate an India industrial thermal intelligence report.")
    res = jarvis_orchestrator.execute_command(db_session, req)
    assert res.state == JarvisState.COMPLETED
    assert res.dispatch_gate_blocked is True
    assert "intelligence report" in res.summary.lower()
    assert "key_findings" in res.details or "report" in str(res.details).lower()


def test_32_jarvis_rejection_out_of_scope_country(db_session: Session):
    """
    Verify JARVIS strictly rejects queries about foreign countries (e.g. Sri Lanka, Pakistan)
    with a clear capability limitation message and zero fabricated data.
    """
    out_of_scope_commands = [
        "Investigate fires in Sri Lanka",
        "Show thermal events in Pakistan",
        "Analyze power plants in Bangladesh",
    ]
    for cmd in out_of_scope_commands:
        req = JarvisCommandRequest(command=cmd)
        res = jarvis_orchestrator.execute_command(db_session, req)
        assert res.state == JarvisState.COMPLETED
        assert res.dispatch_gate_blocked is True
        assert "OUT_OF_SCOPE" in str(res.details.get("status")) or "outside" in res.summary.lower() or "india" in res.summary.lower()
        # Verify no fabricated operational thermal events returned
        assert len(res.details.get("events", [])) == 0


# ==============================================================================
# 6. OPERATIONAL GOVERNANCE, RBAC & REST API INTEGRITY
# ==============================================================================

def test_33_operational_dispatch_gate_strictly_blocked():
    """Verify operational dispatch gate setting is strictly False."""
    assert getattr(settings, "ENABLE_OPERATIONAL_DISPATCH_GATE", False) is False


def test_34_model_activations_blocked():
    """Verify ML models remain strictly in shadow / decision-support mode with automated training blocked."""
    assert getattr(settings, "ENABLE_AUTOMATED_MODEL_ACTIVATION", False) is False


def test_35_authoritative_india_geojson_structure(db_session: Session):
    """Verify get_authoritative_india_geojson generates valid GeoJSON FeatureCollection."""
    geojson = india_boundary_service.get_authoritative_india_geojson(db_session)
    assert geojson["type"] == "FeatureCollection"
    assert len(geojson["features"]) == 36
    feature = geojson["features"][0]
    assert feature["type"] == "Feature"
    assert "geometry" in feature
    assert "properties" in feature
    assert "state_name" in feature["properties"]


def test_36_rest_api_inventory_endpoint(test_client: TestClient):
    """Verify GET /api/v1/inventory/india-datasets returns 200 OK and 18 datasets."""
    response = test_client.get("/api/v1/inventory/india-datasets")
    assert response.status_code == 200
    data = response.json()
    assert data["total_registered"] == 18
    assert len(data["datasets"]) == 18


def test_37_rest_api_quality_audit_endpoint(test_client: TestClient):
    """Verify GET /api/v1/inventory/quality-audit returns 200 OK and 10 passing checks."""
    response = test_client.get("/api/v1/inventory/quality-audit")
    assert response.status_code == 200
    data = response.json()
    assert data["overall_status"] == "PASS"
    assert data["total_checks"] == 10


def test_38_rest_api_coverage_scorecard_endpoint(test_client: TestClient):
    """Verify GET /api/v1/inventory/coverage-scorecard returns 200 OK and EXCELLENT rating."""
    response = test_client.get("/api/v1/inventory/coverage-scorecard")
    assert response.status_code == 200
    data = response.json()
    assert data["coverage_rating"] == "EXCELLENT"
    assert data["overall_score_pct"] >= 95.0


def test_39_rest_api_live_latest_india_only(test_client: TestClient):
    """Verify GET /api/v1/data/live/latest?india_only=true excludes all foreign points."""
    response = test_client.get("/api/v1/data/live/latest?limit=50&india_only=true")
    assert response.status_code == 200
    records = response.json()
    assert isinstance(records, list)
    for r in records:
        assert r["country"] == "India"


def test_40_rest_api_india_boundary_geojson(test_client: TestClient):
    """Verify GET /api/v1/data/geography/india-boundary returns valid GeoJSON FeatureCollection."""
    response = test_client.get("/api/v1/data/geography/india-boundary")
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) == 36
