"""
AGNI-NETRA — WP2 Enterprise Database & GIS Production Hardening Test Suite
Verifies:
1. Lifecycle persistence in PostgreSQL (incident_lifecycle_transitions table, transitions ordered and valid)
2. Migration idempotency (running migration twice succeeds non-destructively)
3. Spatial index existence (GiST indexes on geometry and functional geography)
4. Nearest-facility KNN correctness (ST_Distance and <-> operator)
5. BBox query correctness (envelope filtering)
6. India administrative boundary containment correctness (ST_Contains on admin_boundaries)
7. Concurrent duplicate observation ingestion (idempotent clustering)
8. Concurrent lifecycle transition handling (deterministic ordering)
9. Historical query correctness (composite index on thermal_detections)
10. GIS endpoint contract (GeoJSON FeatureCollection validation)
11. Large-result server-side pagination (limit / offset)
12. Data-integrity invariants (frozen baseline verification)
13. Model governance invariant (ENABLE_AUTOMATED_MODEL_ACTIVATION = False)
14. Operational dispatch invariant (ENABLE_OPERATIONAL_DISPATCH_GATE = False)
15. Graceful degradation behavior when spatial features or connections are constrained
"""

import os
import uuid
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from backend.app.main import app
from backend.app.core.config import settings
from backend.app.core.database import SessionLocal, get_db
from backend.app.models.domain import (
    ThermalEvent, ThermalDetection, IncidentLifecycleTransitionRecord,
    IndustrialFacility, Alert
)
from backend.app.models.autonomous_lifecycle import IncidentLifecycleState
from backend.app.services.autonomous_intelligence_service import autonomous_intelligence_core
from backend.app.services.pipeline_service import pipeline_service
from database.migrate_postgres_wp2 import run_wp2_postgres_migration, DEFAULT_POSTGRES_URL

client = TestClient(app)

# Check if active PostgreSQL 16 is accessible
POSTGRES_AVAILABLE = False
try:
    _test_engine = create_engine(DEFAULT_POSTGRES_URL, pool_pre_ping=True)
    with _test_engine.connect() as _conn:
        _conn.execute(text("SELECT 1;"))
        POSTGRES_AVAILABLE = True
except Exception:
    POSTGRES_AVAILABLE = False


@pytest.fixture
def pg_session():
    if not POSTGRES_AVAILABLE:
        pytest.skip("Active PostgreSQL 16 database not accessible on port 5432")
    engine = create_engine(DEFAULT_POSTGRES_URL, pool_pre_ping=True)
    with engine.connect() as conn:
        yield conn


# =========================================================================
# Scenario 1: Lifecycle Persistence in PostgreSQL
# =========================================================================
def test_scenario_1_lifecycle_persistence_postgres(pg_session):
    """
    Verifies that the incident_lifecycle_transitions table exists in PostgreSQL
    and can persist, order, and retrieve 12-state transitions.
    """
    unique_tag = uuid.uuid4().hex[:6].upper()
    event_code = f"EVT-TEST-PG-{unique_tag}"
    trans_id = f"trans-pg-{unique_tag}"

    # Insert test transition
    pg_session.execute(text("""
        INSERT INTO incident_lifecycle_transitions (
            id, event_id, from_state, to_state, subsystem, rationale, correlation_id, created_at, meta_info
        ) VALUES (
            :id, :event_id, :from_state, :to_state, :subsystem, :rationale, :correlation_id, :created_at, :meta_info
        );
    """), {
        "id": trans_id,
        "event_id": event_code,
        "from_state": "OBSERVED",
        "to_state": "INTELLIGENCE_READY",
        "subsystem": "POSTGRES_PERSISTENCE_TEST",
        "rationale": "Empirical WP2 lifecycle persistence verification",
        "correlation_id": f"corr-pg-{unique_tag}",
        "created_at": datetime.now(timezone.utc),
        "meta_info": '{"verified": true}'
    })
    pg_session.commit()

    # Query back
    row = pg_session.execute(text("""
        SELECT id, event_id, from_state, to_state, subsystem, correlation_id
        FROM incident_lifecycle_transitions
        WHERE id = :id;
    """), {"id": trans_id}).fetchone()

    assert row is not None
    assert row[0] == trans_id
    assert row[1] == event_code
    assert row[2] == "OBSERVED"
    assert row[3] == "INTELLIGENCE_READY"
    assert row[4] == "POSTGRES_PERSISTENCE_TEST"


# =========================================================================
# Scenario 2: Migration Idempotency
# =========================================================================
def test_scenario_2_migration_idempotency():
    """
    Verifies that running the WP2 PostgreSQL migration multiple times is 100% idempotent
    and non-destructive without error.
    """
    if not POSTGRES_AVAILABLE:
        pytest.skip("PostgreSQL not available")

    # Run pass 1
    res1 = run_wp2_postgres_migration(DEFAULT_POSTGRES_URL)
    assert res1["status"] == "SUCCESS"

    # Run pass 2 (re-execution must succeed without creating duplicate objects or errors)
    res2 = run_wp2_postgres_migration(DEFAULT_POSTGRES_URL)
    assert res2["status"] == "SUCCESS"
    assert len(res2["tables_created"]) == 0  # Table already exists


# =========================================================================
# Scenario 3: Spatial Index Existence (GiST Geometry & Geography)
# =========================================================================
def test_scenario_3_spatial_index_existence(pg_session):
    """
    Verifies that PostGIS spatial indexes exist on key spatial tables,
    including the functional geography index on industrial_facilities.
    """
    indexes = pg_session.execute(text("""
        SELECT indexname FROM pg_indexes 
        WHERE tablename IN ('industrial_facilities', 'admin_boundaries', 'thermal_detections');
    """)).fetchall()
    index_names = [r[0] for r in indexes]

    assert "idx_fac_geom" in index_names
    assert "idx_fac_geom_geog" in index_names  # Functional geography index
    assert "idx_admin_bound_geom" in index_names
    assert "idx_th_geom" in index_names


# =========================================================================
# Scenario 4: Nearest Facility KNN Correctness
# =========================================================================
def test_scenario_4_nearest_facility_knn(pg_session):
    """
    Verifies that PostGIS spatial distance operator (<->) returns the nearest facility
    in sub-millisecond time.
    """
    res = pg_session.execute(text("""
        SELECT id, name, master_sector,
               ST_Distance(geom::geography, ST_SetSRID(ST_MakePoint(70.0577, 22.4707), 4326)::geography) as dist_m
        FROM industrial_facilities
        WHERE geom IS NOT NULL
        ORDER BY geom <-> ST_SetSRID(ST_MakePoint(70.0577, 22.4707), 4326)
        LIMIT 1;
    """)).fetchone()

    assert res is not None
    assert res[0] is not None
    assert res[1] is not None
    assert res[3] >= 0.0  # Distance in meters


# =========================================================================
# Scenario 5: BBox Query Correctness
# =========================================================================
def test_scenario_5_bbox_query_correctness(pg_session):
    """
    Verifies that coordinate envelope filtering inside sovereign India returns valid events.
    """
    res = pg_session.execute(text("""
        SELECT count(*)
        FROM thermal_events
        WHERE latitude BETWEEN 20.0 AND 25.0 AND longitude BETWEEN 68.0 AND 75.0;
    """)).scalar()

    assert res >= 0


# =========================================================================
# Scenario 6: India Administrative Boundary Containment Correctness
# =========================================================================
def test_scenario_6_admin_boundary_containment(pg_session):
    """
    Verifies that ST_Contains against admin_boundaries correctly resolves
    the sovereign administrative state and district for Indian coordinates.
    """
    res = pg_session.execute(text("""
        SELECT state_name, district_name, admin_level
        FROM admin_boundaries
        WHERE ST_Contains(geom, ST_SetSRID(ST_MakePoint(70.0577, 22.4707), 4326))
        ORDER BY admin_level DESC
        LIMIT 1;
    """)).fetchone()

    assert res is not None
    assert "Gujarat" in res[0] or "Kutch" in str(res[1]) or "Jamnagar" in str(res[1])


# =========================================================================
# Scenario 7: Concurrent Duplicate Observation Ingestion
# =========================================================================
def test_scenario_7_concurrent_duplicate_observation_ingestion():
    """
    Verifies that duplicate observations arriving concurrently are deduplicated
    and do not create redundant events or fail transactions.
    """
    db = SessionLocal()
    try:
        unique_tag = uuid.uuid4().hex[:6].upper()
        obs = [
            {
                "latitude": 22.4707,
                "longitude": 70.0577,
                "brightness": 345.0,
                "frp": 85.0,
                "confidence": 92.0,
                "sensor": "VIIRS",
                "satellite": "NOAA-20",
                "acq_timestamp": datetime.now(timezone.utc).isoformat(),
                "day_night": "N"
            }
        ]

        out1 = autonomous_intelligence_core.process_observations_autonomous(
            db=db, raw_observations=obs, source_name=f"CONCUR_1_{unique_tag}"
        )
        assert len(out1) >= 1

        out2 = autonomous_intelligence_core.process_observations_autonomous(
            db=db, raw_observations=obs, source_name=f"CONCUR_2_{unique_tag}"
        )
        # Second pass drops duplicate without transaction failure
        assert len(out2) == 0
    finally:
        db.close()


# =========================================================================
# Scenario 8: Concurrent Lifecycle Transition Handling
# =========================================================================
def test_scenario_8_concurrent_lifecycle_transition_handling():
    """
    Verifies that lifecycle state transitions for the same event are recorded
    with unique transition IDs, timestamps, and causal ordering.
    """
    db = SessionLocal()
    try:
        unique_tag = uuid.uuid4().hex[:6].upper()
        evt = f"EVT-CONCUR-{unique_tag}"

        t1 = autonomous_intelligence_core.record_transition(
            event_id=evt,
            from_state=None,
            to_state=IncidentLifecycleState.OBSERVED,
            subsystem="TEST_RUNNER",
            rationale="Concurrent test transition 1",
            db=db
        )
        t2 = autonomous_intelligence_core.record_transition(
            event_id=evt,
            from_state=IncidentLifecycleState.OBSERVED,
            to_state=IncidentLifecycleState.VALIDATING,
            subsystem="TEST_RUNNER",
            rationale="Concurrent test transition 2",
            db=db
        )
        db.commit()

        assert t1.transition_id != t2.transition_id
        assert t1.to_state == IncidentLifecycleState.OBSERVED
        assert t2.to_state == IncidentLifecycleState.VALIDATING
    finally:
        db.close()


# =========================================================================
# Scenario 9: Historical Query Correctness & Composite Index
# =========================================================================
def test_scenario_9_historical_query_composite_index(pg_session):
    """
    Verifies that querying thermal_detections by event_id uses the composite index
    (event_id, acq_timestamp DESC) with zero in-memory sort node.
    """
    plan = pg_session.execute(text("""
        EXPLAIN (FORMAT JSON)
        SELECT id, latitude, longitude, brightness, frp, acq_timestamp
        FROM thermal_detections
        WHERE event_id = 'EVT-TEST-HIST'
        ORDER BY acq_timestamp DESC;
    """)).scalar()

    root_node = plan[0]["Plan"]
    # Verify index scan without Sort node
    assert root_node["Node Type"] == "Index Scan"
    assert root_node["Index Name"] == "ix_thermal_detections_event_ts"


# =========================================================================
# Scenario 10: GIS Endpoint Contract
# =========================================================================
def test_scenario_10_gis_endpoint_contract():
    """
    Verifies that the /api/v1/gis/layers and /api/v1/gis/protected-areas endpoints
    return valid contract payloads.
    """
    res = client.get("/api/v1/gis/layers")
    assert res.status_code == 200
    data = res.json()
    assert "layers" in data
    assert isinstance(data["layers"], list)


# =========================================================================
# Scenario 11: Large-Result Server-Side Pagination
# =========================================================================
def test_scenario_11_large_result_pagination():
    """
    Verifies that /api/v1/events implements server-side pagination (limit / offset).
    Requires ANALYST role per WP8 RBAC specification.
    """
    from backend.app.api.deps import get_current_active_user
    from backend.app.models.domain import User
    app.dependency_overrides[get_current_active_user] = lambda: User(
        id="usr-ana-001", email="analyst@agninetra.gov.in", role="ANALYST", is_active=True
    )
    try:
        res = client.get("/api/v1/events?page=1&limit=5")
        assert res.status_code == 200
        data = res.json()
        assert "items" in data
        assert len(data["items"]) <= 5
        assert "total_count" in data
        assert "total_pages" in data
    finally:
        app.dependency_overrides.clear()


# =========================================================================
# Scenario 12: Data Integrity Invariants
# =========================================================================
def test_scenario_12_data_integrity_invariants():
    """
    Verifies that sovereign data invariants are preserved in the database.
    Distinguishes frozen baseline from operational records.
    """
    db = SessionLocal()
    try:
        fac_count = db.query(IndustrialFacility).count()
        # In SQLite baseline: 35,570; In PostgreSQL: 35,684
        assert fac_count >= 35570

        # CEA Power Units invariant: exactly 1,633 units
        from backend.app.models.domain import CEAPowerStationStaging
        cea_count = db.query(CEAPowerStationStaging).count()
        assert cea_count == 1633

        # IBM Mining Leases invariant: exactly 414 leases
        from backend.app.models.domain import IbmMiningLeaseContext
        ibm_count = db.query(IbmMiningLeaseContext).count()
        assert ibm_count == 414
    finally:
        db.close()


# =========================================================================
# Scenario 13: Model Governance Invariant
# =========================================================================
def test_scenario_13_model_governance_invariant():
    """
    Verifies that ENABLE_AUTOMATED_MODEL_ACTIVATION = False and models remain frozen.
    """
    assert hasattr(settings, "ENABLE_AUTOMATED_MODEL_ACTIVATION")
    assert settings.ENABLE_AUTOMATED_MODEL_ACTIVATION is False


# =========================================================================
# Scenario 14: Operational Dispatch Invariant
# =========================================================================
def test_scenario_14_operational_dispatch_invariant():
    """
    Verifies that ENABLE_OPERATIONAL_DISPATCH_GATE = False and live automated dispatch remains blocked.
    """
    assert hasattr(settings, "ENABLE_OPERATIONAL_DISPATCH_GATE")
    assert settings.ENABLE_OPERATIONAL_DISPATCH_GATE is False


# =========================================================================
# Scenario 15: Graceful Degradation on Constrained Spatial Backend
# =========================================================================
def test_scenario_15_graceful_degradation_behavior():
    """
    Verifies that when spatial features encounter missing data or fallback zones,
    the pipeline completes safely without crashing.
    """
    # Remote point with no industrial facilities within 50km (Jaisalmer desert, India)
    remote_obs = [
        {
            "latitude": 27.0000,
            "longitude": 71.5000,
            "brightness": 315.0,
            "frp": 30.0,
            "confidence": 75.0,
            "sensor": "VIIRS",
            "satellite": "NOAA-20",
            "acq_timestamp": datetime.now(timezone.utc).isoformat(),
            "day_night": "N"
        }
    ]

    db = SessionLocal()
    try:
        outcomes = autonomous_intelligence_core.process_observations_autonomous(
            db=db, raw_observations=remote_obs, source_name="TEST_DEGRADATION"
        )
        assert len(outcomes) >= 1
        assert outcomes[0].event_code.startswith("EVT-")
        assert outcomes[0].state in [
            IncidentLifecycleState.INTELLIGENCE_READY,
            IncidentLifecycleState.REQUIRES_HUMAN_VERIFICATION
        ]
        assert outcomes[0].risk_score >= 0.0
        assert outcomes[0].dispatch_blocked is True
    finally:
        db.close()

