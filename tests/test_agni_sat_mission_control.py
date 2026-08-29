import os
import sys
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.main import app
from backend.app.core.database import SessionLocal
from backend.app.models.domain import User, ThermalEvent, SatelliteTelemetryLog, MissionTask
from backend.app.services.satellite_simulator import satellite_simulator, SCENARIOS_CATALOG, VIRTUAL_SATELLITE
from backend.app.services.pipeline_service import pipeline_service

client = TestClient(app)


def test_satellite_info_and_ground_track():
    """Verify AGNI-SAT-01 specifications, active sensors and ground track geometry"""
    info = satellite_simulator.get_satellite_info()
    assert info["satellite_id"] == "AGNI-SAT-01"
    assert info["altitude_km"] == 505.0
    assert info["telemetry_mode"] == "SIMULATION"
    assert len(info["sensors"]) == 4
    assert info["active_scenarios_count"] == 12

    gt = satellite_simulator.get_ground_track(hours_ahead=1.0)
    assert gt["type"] == "FeatureCollection"
    assert len(gt["features"]) >= 1
    assert gt["features"][0]["geometry"]["type"] == "LineString"
    assert len(gt["features"][0]["geometry"]["coordinates"]) > 5


def test_scenarios_catalog_12_templates():
    """Verify all 12 standardized incident templates exist with deterministic parameters"""
    scenarios = satellite_simulator.list_scenarios()
    assert len(scenarios) == 12

    scenario_ids = [s["id"] for s in scenarios]
    assert "scenario-01-industrial-surge" in scenario_ids
    assert "scenario-02-gas-flare" in scenario_ids
    assert "scenario-03-forest-fire" in scenario_ids
    assert "scenario-04-agricultural-burning" in scenario_ids
    assert "scenario-05-mining-activity" in scenario_ids
    assert "scenario-06-unknown-persistent" in scenario_ids
    assert "scenario-07-multi-event" in scenario_ids
    assert "scenario-08-missing-facility" in scenario_ids
    assert "scenario-09-delayed-telemetry" in scenario_ids
    assert "scenario-10-sensor-dropout" in scenario_ids
    assert "scenario-11-cloud-obscured" in scenario_ids
    assert "scenario-12-high-thermal-anomaly" in scenario_ids


def test_sensor_footprint_calculation():
    """Verify sensor footprint polygon is calculated dynamically from swath width"""
    fp_mwir = satellite_simulator.calculate_sensor_footprint_geojson(22.3552, 69.8654, "THERMAL_MWIR")
    assert fp_mwir["type"] == "Polygon"
    coords = fp_mwir["coordinates"][0]
    assert len(coords) == 5  # Closed ring
    assert coords[0] == coords[-1]

    # MWIR 350km swath should span ~3.15 degrees latitude
    lat_span = abs(coords[2][1] - coords[0][1])
    assert 2.5 <= lat_span <= 3.8

    # Optical RGB 60km swath should be significantly smaller
    fp_opt = satellite_simulator.calculate_sensor_footprint_geojson(22.3552, 69.8654, "OPTICAL_RGB")
    lat_span_opt = abs(fp_opt["coordinates"][0][2][1] - fp_opt["coordinates"][0][0][1])
    assert 0.4 <= lat_span_opt <= 0.8
    assert lat_span > lat_span_opt


def test_calculated_next_pass_prediction():
    """Verify simulated future pass opportunity calculation based on orbit dynamics"""
    pass_info = satellite_simulator.calculate_next_pass(22.3552, 69.8654)
    assert "calculated_pass_time" in pass_info
    assert pass_info["pass_delay_minutes"] > 0
    assert "closest_approach_distance_km" in pass_info
    assert isinstance(pass_info["swath_coverage"], bool)


def test_mission_tasking_scheduling_and_persistence():
    """Verify satellite mission tasking saves to DB with scheduled pass time"""
    db = SessionLocal()
    try:
        task_res = satellite_simulator.schedule_mission_task(
            db=db,
            target_name="Jamnagar Test Task AOI",
            target_lat=22.3552,
            target_lon=69.8654,
            sensor_id="THERMAL_MWIR",
            priority="CRITICAL"
        )
        assert task_res["status"] == "SIMULATED_TASK_ACCEPTED"
        assert task_res["task_code"].startswith("TASK-SAT-")
        assert task_res["priority"] == "CRITICAL"

        # Verify in DB
        db_task = db.query(MissionTask).filter(MissionTask.id == task_res["task_id"]).first()
        assert db_task is not None
        assert db_task.target_name == "Jamnagar Test Task AOI"
    finally:
        db.close()


def test_golden_scenario_execution_and_real_stage_latencies():
    """Verify deterministic scenario execution and independent real stage timing"""
    db = SessionLocal()
    try:
        res = satellite_simulator.run_scenario(db, "scenario-01-industrial-surge")
        assert res["status"] == "SUCCESS"
        assert res["mode"] == "SIMULATION"
        assert res["scenario"]["expected_class"] == "Industrial Fire"
        assert res["event"] is not None
        assert res["event"]["predicted_class"] == "Industrial Fire"
        assert res["validation"]["is_match"] is True

        # Check real benchmark metrics
        bm = res["benchmark"]
        assert bm["observation_to_telemetry_ms"] >= 0.0
        assert bm["total_processing_ms"] > 0.0
        assert bm["clustering_ms"] >= 0.0
        assert bm["ml_inference_ms"] >= 0.0
        assert bm["shap_explanation_ms"] >= 0.0
        assert bm["risk_evaluation_ms"] >= 0.0
    finally:
        db.close()


def test_golden_historical_replay_timestamp_preservation():
    """Verify historical replay preserves original acquisition timestamp"""
    db = SessionLocal()
    try:
        historical_sample = {
            "source": "NASA_FIRMS",
            "sensor": "VIIRS_NOAA21",
            "satellite": "NOAA-21",
            "latitude": 22.3552,
            "longitude": 69.8654,
            "acq_date": "2026-04-12",
            "acq_time": "1845",
            "acq_timestamp": "2026-04-12T18:45:00+00:00",
            "brightness": 372.0,
            "bright_t31": 340.0,
            "frp": 165.0,
            "confidence": 98.0,
            "day_night": "N"
        }

        replay_res = satellite_simulator.replay_historical_observation(db, historical_sample)
        assert replay_res["status"] == "REPLAY_PROCESSED"
        assert replay_res["mode"] == "HISTORICAL_REPLAY"
        assert replay_res["original_acquisition_timestamp"] == "2026-04-12T18:45:00+00:00"
        assert replay_res["replay_execution_timestamp"] != replay_res["original_acquisition_timestamp"]
        assert replay_res["pipeline_result"]["status"] == "SUCCESS"
    finally:
        db.close()
