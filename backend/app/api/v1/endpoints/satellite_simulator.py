from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.app.core.database import get_db
from backend.app.api.deps import get_current_active_user, get_optional_current_user
from backend.app.models.domain import User, SatelliteTelemetryLog, MissionTask
from backend.app.models.schemas import SatelliteTaskingRequest, SatelliteTelemetryOut, MissionTaskOut
from backend.app.services.satellite_simulator import satellite_simulator

router = APIRouter()


@router.get("/info")
def get_satellite_mission_info():
    """
    Returns virtual satellite specifications (AGNI-SAT-01), active sensor payloads,
    and real-time simulated subsatellite ground coordinates.
    """
    return satellite_simulator.get_satellite_info()


@router.get("/ground-track")
def get_satellite_ground_track(hours_ahead: float = Query(2.0, ge=0.5, le=12.0)):
    """
    Returns predicted orbital ground-track GeoJSON linestrings and sensor swaths over India.
    """
    return satellite_simulator.get_ground_track(hours_ahead=hours_ahead)


@router.get("/scenarios")
def list_simulation_scenarios():
    """
    Lists all 12 standardized disaster and industrial incident simulation templates.
    """
    return satellite_simulator.list_scenarios()


@router.post("/scenarios/{scenario_id}/run")
def run_simulation_scenario(
    scenario_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """
    Triggers an end-to-end satellite observation sequence for the selected scenario:
    Telemetry Packet -> DBSCAN Event -> GIS Context -> XGBoost & SHAP -> Risk Score -> Latency Benchmark.
    """
    try:
        user_id = current_user.id if current_user else None
        result = satellite_simulator.run_scenario(db, scenario_id=scenario_id, analyst_user_id=user_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scenario execution failed: {str(e)}")


@router.get("/next-pass")
def predict_next_satellite_pass(
    latitude: float = Query(..., ge=6.0, le=38.0),
    longitude: float = Query(..., ge=68.0, le=98.0)
):
    """
    Calculates the next simulated orbital pass opportunity for specific Indian coordinates.
    """
    return satellite_simulator.calculate_next_pass(latitude, longitude)


@router.get("/footprint")
def get_sensor_footprint(
    latitude: float = Query(..., ge=6.0, le=38.0),
    longitude: float = Query(..., ge=68.0, le=98.0),
    sensor_id: str = Query("THERMAL_MWIR")
):
    """
    Returns dynamic sensor swath polygon geometry based on sensor optical/thermal field of view.
    """
    return satellite_simulator.calculate_sensor_footprint_geojson(latitude, longitude, sensor_id)


@router.post("/tasking")
def task_virtual_satellite(
    request: SatelliteTaskingRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """
    Schedules operational simulated satellite tasking for targeted emergency or industrial AOIs.
    """
    user_id = current_user.id if current_user else None
    return satellite_simulator.schedule_mission_task(
        db=db,
        target_name=request.target_name,
        target_lat=request.target_lat,
        target_lon=request.target_lon,
        sensor_id=request.sensor_id,
        priority=request.priority,
        user_id=user_id
    )


@router.get("/tasks")
def list_mission_tasks(
    db: Session = Depends(get_db),
    limit: int = Query(20, ge=1, le=100)
):
    """
    Retrieves history of scheduled and executed satellite mission tasks.
    """
    tasks = db.query(MissionTask).order_by(MissionTask.created_at.desc()).limit(limit).all()
    return [
        {
            "id": t.id,
            "task_code": t.task_code,
            "satellite_id": t.satellite_id,
            "target_name": t.target_name,
            "target_lat": t.target_lat,
            "target_lon": t.target_lon,
            "sensor_id": t.sensor_id,
            "priority": t.priority,
            "status": t.status,
            "scheduled_pass_time": t.scheduled_pass_time.isoformat() if t.scheduled_pass_time else None,
            "observed_at": t.observed_at.isoformat() if t.observed_at else None,
            "created_at": t.created_at.isoformat() if t.created_at else None
        }
        for t in tasks
    ]


@router.get("/telemetry/logs")
def get_telemetry_logs(
    db: Session = Depends(get_db),
    limit: int = Query(25, ge=1, le=100)
):
    """
    Retrieves incoming downlink telemetry packets from AGNI-SAT-01.
    """
    logs = db.query(SatelliteTelemetryLog).order_by(SatelliteTelemetryLog.timestamp.desc()).limit(limit).all()
    return [
        {
            "id": l.id,
            "satellite_id": l.satellite_id,
            "sensor_id": l.sensor_id,
            "scenario_id": l.scenario_id,
            "timestamp": l.timestamp.isoformat() if l.timestamp else None,
            "latitude": l.latitude,
            "longitude": l.longitude,
            "frp": l.frp,
            "brightness": l.brightness,
            "confidence": l.confidence,
            "footprint_geojson": l.footprint_geojson,
            "status": l.status,
            "is_simulation": l.is_simulation
        }
        for l in logs
    ]


@router.post("/replay")
def replay_historical_incident(
    payload: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """
    Replays a real historical Indian thermal event from FIRMS/Landsat through the AGNI-SAT virtual pipeline.
    Preserves original historical acquisition timestamp.
    """
    required_fields = ["latitude", "longitude", "frp"]
    for f in required_fields:
        if f not in payload:
            raise HTTPException(status_code=400, detail=f"Missing required field: {f}")

    return satellite_simulator.replay_historical_observation(db, payload)
