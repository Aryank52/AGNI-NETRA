import math
import time
import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session

from backend.app.models.domain import (
    SimulationScenario, SatelliteTelemetryLog, ThermalEvent, IndustrialFacility, User, MissionTask
)
from data_pipeline.adapters.base import NormalizedThermalObservation, SourceProvenance
from backend.app.services.pipeline_service import pipeline_service
from backend.app.services.spatial_engine import lookup_state, lookup_district, haversine_distance_m


# Canonical Virtual Satellite Model: AGNI-SAT-01
VIRTUAL_SATELLITE = {
    "satellite_id": "AGNI-SAT-01",
    "name": "AGNI-SAT-01 (Digital Twin Simulator)",
    "orbit_type": "Sun-Synchronous LEO",
    "altitude_km": 505.0,
    "inclination_deg": 97.4,
    "orbital_period_min": 94.6,
    "swath_width_km": 350.0,
    "ground_speed_km_s": 7.6,
    "sensors": [
        {
            "sensor_id": "THERMAL_MWIR",
            "name": "Mid-Wave Infrared Radiometer (3.9µm / 11.0µm)",
            "type": "THERMAL",
            "resolution_m": 250,
            "swath_width_km": 350.0,
            "field_of_view_deg": 38.2,
            "calibrated_range_k": (300, 1800),
            "status": "ACTIVE"
        },
        {
            "sensor_id": "OPTICAL_RGB",
            "name": "High-Resolution True Color Imager (RGB)",
            "type": "OPTICAL",
            "resolution_m": 15,
            "swath_width_km": 60.0,
            "field_of_view_deg": 6.8,
            "bands": ["Red (665nm)", "Green (560nm)", "Blue (490nm)"],
            "status": "ACTIVE"
        },
        {
            "sensor_id": "SWIR_2200NM",
            "name": "Short-Wave Infrared Flare & Combustion Sensor (2.2µm)",
            "type": "SWIR",
            "resolution_m": 50,
            "swath_width_km": 120.0,
            "field_of_view_deg": 13.5,
            "status": "ACTIVE"
        },
        {
            "sensor_id": "MULTISPECTRAL",
            "name": "Multispectral Environmental Payload (RedEdge/NIR/SWIR)",
            "type": "MULTISPECTRAL",
            "resolution_m": 30,
            "swath_width_km": 150.0,
            "field_of_view_deg": 16.8,
            "status": "ACTIVE"
        }
    ]
}

# 12 Standardized Incident & Disaster Simulation Scenarios
SCENARIOS_CATALOG: List[Dict[str, Any]] = [
    {
        "id": "scenario-01-industrial-surge",
        "name": "Industrial Thermal Surge (Jamnagar Refinery Flare Spike)",
        "scenario_type": "INDUSTRIAL_SURGE",
        "description": "Simulates an emergency pressure safety flare release and sudden thermal radiative power spike (+4.1σ) within the Reliance Jamnagar complex.",
        "target_state": "Gujarat",
        "target_district": "Jamnagar",
        "target_lat": 22.3552,
        "target_lon": 69.8654,
        "target_facility": "Reliance Jamnagar Petroleum Refinery Complex",
        "expected_class": "Industrial Fire",
        "expected_risk_level": "HIGH",
        "parameters": {
            "frp_mw": 285.0,
            "brightness_k": 382.5,
            "confidence": 98.5,
            "day_night": "N",
            "detection_count": 6,
            "anomaly_z_score": 4.1
        }
    },
    {
        "id": "scenario-02-gas-flare",
        "name": "Routine Offshore / Onshore Gas Flare (Kakinada KG-Basin)",
        "scenario_type": "GAS_FLARE",
        "description": "Continuous 24x7 hydrocarbon flare with stable thermal signature and elevated diurnal day/night ratio.",
        "target_state": "Andhra Pradesh",
        "target_district": "East Godavari",
        "target_lat": 16.9891,
        "target_lon": 82.2475,
        "target_facility": "ONGC Kakinada Gas Processing Terminal",
        "expected_class": "Gas Flare",
        "expected_risk_level": "MODERATE",
        "parameters": {
            "frp_mw": 95.0,
            "brightness_k": 348.0,
            "confidence": 94.0,
            "day_night": "N",
            "detection_count": 4,
            "anomaly_z_score": 0.4
        }
    },
    {
        "id": "scenario-03-forest-fire",
        "name": "Forest Wildfire (Simlipal Biosphere Reserve)",
        "scenario_type": "FOREST_FIRE",
        "description": "Rapidly spreading canopy and surface forest fire across dense deciduous forest during dry pre-monsoon season.",
        "target_state": "Odisha",
        "target_district": "Mayurbhanj",
        "target_lat": 21.8540,
        "target_lon": 86.3420,
        "target_facility": None,
        "expected_class": "Forest Fire",
        "expected_risk_level": "HIGH",
        "parameters": {
            "frp_mw": 140.0,
            "brightness_k": 338.0,
            "confidence": 92.0,
            "day_night": "D",
            "detection_count": 8,
            "anomaly_z_score": 2.8
        }
    },
    {
        "id": "scenario-04-agricultural-burning",
        "name": "Agricultural Stubble Burning (Sangrur Paddy Belt)",
        "scenario_type": "AGRICULTURAL_BURNING",
        "description": "Post-harvest paddy stubble burning in agricultural parcels, transient diurnal cluster with zero industrial context.",
        "target_state": "Punjab",
        "target_district": "Sangrur",
        "target_lat": 30.2450,
        "target_lon": 75.8420,
        "target_facility": None,
        "expected_class": "Agricultural Burning",
        "expected_risk_level": "MODERATE",
        "parameters": {
            "frp_mw": 48.0,
            "brightness_k": 326.0,
            "confidence": 88.0,
            "day_night": "D",
            "detection_count": 5,
            "anomaly_z_score": 1.2
        }
    },
    {
        "id": "scenario-05-mining-activity",
        "name": "Opencast Coal Mine Thermal Activity (Korba Gevra)",
        "scenario_type": "MINING_ACTIVITY",
        "description": "Spontaneous coal seam combustion and heavy overburden thermal emissions within opencast pit boundary.",
        "target_state": "Chhattisgarh",
        "target_district": "Korba",
        "target_lat": 22.3485,
        "target_lon": 82.7231,
        "target_facility": "SECL Korba Gevra Opencast Coal Mine",
        "expected_class": "Mining Activity",
        "expected_risk_level": "MODERATE",
        "parameters": {
            "frp_mw": 115.0,
            "brightness_k": 342.0,
            "confidence": 90.0,
            "day_night": "D",
            "detection_count": 4,
            "anomaly_z_score": 0.8
        }
    },
    {
        "id": "scenario-06-unknown-persistent",
        "name": "Persistent Unknown Thermal Cluster (Raigarh Industrial Belt)",
        "scenario_type": "UNKNOWN_PERSISTENT",
        "description": "Autonomous discovery scenario: Recurrent 24x7 thermal detections in built-up industrial area with no known registry entry.",
        "target_state": "Chhattisgarh",
        "target_district": "Raigarh",
        "target_lat": 21.8974,
        "target_lon": 83.3951,
        "target_facility": None,
        "expected_class": "Other Thermal Source",
        "expected_risk_level": "HIGH",
        "parameters": {
            "frp_mw": 165.0,
            "brightness_k": 358.0,
            "confidence": 96.0,
            "day_night": "N",
            "detection_count": 7,
            "anomaly_z_score": 3.4
        }
    },
    {
        "id": "scenario-07-multi-event",
        "name": "Multiple Simultaneous Industrial Incidents (Hazira Petrochemical Hub)",
        "scenario_type": "MULTI_EVENT",
        "description": "Simultaneous co-occurring thermal anomalies across multiple petrochemical, fertilizer, and LNG processing units in Hazira cluster.",
        "target_state": "Gujarat",
        "target_district": "Surat",
        "target_lat": 21.1160,
        "target_lon": 72.6510,
        "target_facility": "Hazira Industrial Complex",
        "expected_class": "Industrial Fire",
        "expected_risk_level": "CRITICAL",
        "parameters": {
            "frp_mw": 340.0,
            "brightness_k": 395.0,
            "confidence": 99.0,
            "day_night": "N",
            "detection_count": 12,
            "anomaly_z_score": 5.2
        }
    },
    {
        "id": "scenario-08-missing-facility",
        "name": "Unregistered Smelter Candidate (Angul Industrial Cluster)",
        "scenario_type": "MISSING_FACILITY",
        "description": "High-intensity metallurgical furnace signature with zero OSM/CEA registry linkage, triggering candidate induction.",
        "target_state": "Odisha",
        "target_district": "Angul",
        "target_lat": 20.8400,
        "target_lon": 85.1100,
        "target_facility": None,
        "expected_class": "Industrial Fire",
        "expected_risk_level": "HIGH",
        "parameters": {
            "frp_mw": 210.0,
            "brightness_k": 370.0,
            "confidence": 95.0,
            "day_night": "N",
            "detection_count": 5,
            "anomaly_z_score": 3.1
        }
    },
    {
        "id": "scenario-09-delayed-telemetry",
        "name": "Delayed Telemetry / Ground Link Recovery (Jaisalmer Test Site)",
        "scenario_type": "DELAYED_TELEMETRY",
        "description": "Simulates spacecraft telemetry buffer retention and subsequent ground downlink pass with timestamp preservation.",
        "target_state": "Rajasthan",
        "target_district": "Jaisalmer",
        "target_lat": 26.9157,
        "target_lon": 70.9083,
        "target_facility": None,
        "expected_class": "Other Thermal Source",
        "expected_risk_level": "LOW",
        "parameters": {
            "frp_mw": 42.0,
            "brightness_k": 320.0,
            "confidence": 85.0,
            "day_night": "D",
            "detection_count": 3,
            "anomaly_z_score": 0.2
        }
    },
    {
        "id": "scenario-10-sensor-dropout",
        "name": "Sensor Dropout & Fail-Safe Recovery (Singrauli Thermal Power Hub)",
        "scenario_type": "SENSOR_DROPOUT",
        "description": "Simulates partial optical sensor degradation gracefully falling back to calibrated MWIR radiometer stream.",
        "target_state": "Madhya Pradesh",
        "target_district": "Singrauli",
        "target_lat": 24.1012,
        "target_lon": 82.6841,
        "target_facility": "NTPC Vindhyachal Super Thermal Power Station",
        "expected_class": "Industrial Fire",
        "expected_risk_level": "HIGH",
        "parameters": {
            "frp_mw": 220.0,
            "brightness_k": 375.0,
            "confidence": 96.0,
            "day_night": "N",
            "detection_count": 6,
            "anomaly_z_score": 3.6
        }
    },
    {
        "id": "scenario-11-cloud-obscured",
        "name": "Cloud-Obscured Optical Scene with Active MWIR (Western Ghats)",
        "scenario_type": "CLOUD_OBSCURED",
        "description": "High cloud cover (78%) obscuring optical RGB, successfully resolved via 3.9µm MWIR atmospheric penetration.",
        "target_state": "Maharashtra",
        "target_district": "Ratnagiri",
        "target_lat": 16.9902,
        "target_lon": 73.3120,
        "target_facility": None,
        "expected_class": "Industrial Fire",
        "expected_risk_level": "MODERATE",
        "parameters": {
            "frp_mw": 130.0,
            "brightness_k": 345.0,
            "confidence": 91.0,
            "day_night": "N",
            "detection_count": 4,
            "anomaly_z_score": 1.9
        }
    },
    {
        "id": "scenario-12-high-thermal-anomaly",
        "name": "Extreme Radiative Surge & Safety Relief (Nagothane Petrochemical)",
        "scenario_type": "HIGH_THERMAL_ANOMALY",
        "description": "Extreme flare combustion burst (+5.8σ) requiring priority NDMA/Analyst incident dispatch and immediate dossier generation.",
        "target_state": "Maharashtra",
        "target_district": "Raigad",
        "target_lat": 18.5240,
        "target_lon": 73.1250,
        "target_facility": "IPCL Nagothane Petrochemical Complex",
        "expected_class": "Industrial Fire",
        "expected_risk_level": "CRITICAL",
        "parameters": {
            "frp_mw": 395.0,
            "brightness_k": 410.0,
            "confidence": 99.5,
            "day_night": "N",
            "detection_count": 10,
            "anomaly_z_score": 5.8
        }
    }
]


class SatelliteSimulatorService:
    """
    AGNI-SAT Software Satellite & Mission Control Engine (Digital Twin).
    Simulates:
    - Orbit ground tracks over Indian coordinates
    - Sensor-derived swath footprint geometry
    - Calculated simulated next-pass opportunities
    - Real historical telemetry replay preserving original acquisition timestamps
    - Deterministic scenario generation & execution
    - End-to-end telemetry-to-intelligence actual latency benchmarking
    """

    def get_satellite_info(self) -> Dict[str, Any]:
        """Returns virtual spacecraft specifications and payload status."""
        current_time = datetime.now(timezone.utc)
        sub_lat, sub_lon = self.calculate_current_subsatellite_point(current_time)
        return {
            **VIRTUAL_SATELLITE,
            "telemetry_mode": "SIMULATION",
            "current_utc": current_time.isoformat(),
            "subsatellite_latitude": round(sub_lat, 4),
            "subsatellite_longitude": round(sub_lon, 4),
            "mission_status": "OPERATIONAL",
            "active_scenarios_count": len(SCENARIOS_CATALOG)
        }

    def calculate_current_subsatellite_point(self, dt: datetime) -> Tuple[float, float]:
        """
        Propagates simplified Sun-Synchronous LEO orbit over Indian longitudes.
        """
        epoch_seconds = dt.timestamp()
        period_sec = VIRTUAL_SATELLITE["orbital_period_min"] * 60.0
        phase = (epoch_seconds % period_sec) / period_sec
        # Orbital latitude sweep [-80, 80]
        lat = 80.0 * math.sin(2 * math.pi * phase)
        # Ground track longitude progression over India [68, 98]
        lon = 68.0 + (epoch_seconds % 86400 / 86400.0) * 360.0
        lon = ((lon + 180.0) % 360.0) - 180.0
        # If outside India bounds in simulation, anchor ground track in Indian territorial corridor
        if lon < 65.0 or lon > 100.0:
            lon = 78.5 + 10.0 * math.cos(2 * math.pi * phase)
        return lat, lon

    def calculate_sensor_footprint_geojson(
        self,
        center_lat: float,
        center_lon: float,
        sensor_id: str = "THERMAL_MWIR"
    ) -> Dict[str, Any]:
        """
        Calculates realistic sensor ground swath footprint polygon dynamically based
        on the sensor's physical swath width and target latitude.
        """
        sensor = next((s for s in VIRTUAL_SATELLITE["sensors"] if s["sensor_id"] == sensor_id), None)
        swath_km = sensor["swath_width_km"] if sensor else VIRTUAL_SATELLITE["swath_width_km"]

        # Half width in degrees latitude (~111.0 km per degree)
        half_swath_deg_lat = (swath_km / 2.0) / 111.0
        # Half width in degrees longitude adjusted for spherical convergence
        cos_lat = max(math.cos(math.radians(center_lat)), 0.1)
        half_swath_deg_lon = (swath_km / 2.0) / (111.0 * cos_lat)

        min_lat = round(center_lat - half_swath_deg_lat, 5)
        max_lat = round(center_lat + half_swath_deg_lat, 5)
        min_lon = round(center_lon - half_swath_deg_lon, 5)
        max_lon = round(center_lon + half_swath_deg_lon, 5)

        return {
            "type": "Polygon",
            "coordinates": [[
                [min_lon, min_lat],
                [max_lon, min_lat],
                [max_lon, max_lat],
                [min_lon, max_lat],
                [min_lon, min_lat]
            ]],
            "properties": {
                "sensor_id": sensor_id,
                "swath_width_km": swath_km,
                "center": [center_lon, center_lat]
            }
        }

    def calculate_next_pass(
        self,
        target_lat: float,
        target_lon: float,
        start_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Calculates true simulated future observation opportunity for a target coordinate
        based on orbital inclination, period, and ground track closest approach.
        """
        t0 = start_time or datetime.now(timezone.utc)
        period_min = VIRTUAL_SATELLITE["orbital_period_min"]

        # Search next 12 orbital revolutions for closest approach
        best_delta_minutes = 15.0  # default minimum
        closest_distance_km = 99999.0

        for m in range(5, int(12 * period_min), 5):
            eval_time = t0 + timedelta(minutes=m)
            sub_lat, sub_lon = self.calculate_current_subsatellite_point(eval_time)
            dist_m = haversine_distance_m(target_lat, target_lon, sub_lat, sub_lon)
            dist_km = dist_m / 1000.0
            if dist_km < closest_distance_km:
                closest_distance_km = dist_km
                best_delta_minutes = m
                if dist_km < (VIRTUAL_SATELLITE["swath_width_km"] / 2.0):
                    break

        calculated_pass_time = t0 + timedelta(minutes=best_delta_minutes)
        return {
            "target_lat": target_lat,
            "target_lon": target_lon,
            "calculated_pass_time": calculated_pass_time.isoformat(),
            "pass_delay_minutes": round(best_delta_minutes, 1),
            "closest_approach_distance_km": round(closest_distance_km, 1),
            "swath_coverage": closest_distance_km <= (VIRTUAL_SATELLITE["swath_width_km"] / 2.0)
        }

    def get_ground_track(self, hours_ahead: float = 2.0) -> Dict[str, Any]:
        """
        Generates simulated orbital ground track coordinates and footprint polygons over India.
        """
        now = datetime.now(timezone.utc)
        points = []
        for minute in range(0, int(hours_ahead * 60), 3):
            t = now + timedelta(minutes=minute)
            lat, lon = self.calculate_current_subsatellite_point(t)
            points.append([round(lon, 4), round(lat, 4)])

        return {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "LineString",
                        "coordinates": points
                    },
                    "properties": {
                        "satellite": "AGNI-SAT-01",
                        "orbit": "Sun-Synchronous LEO",
                        "start_time": now.isoformat(),
                        "swath_width_km": VIRTUAL_SATELLITE["swath_width_km"]
                    }
                }
            ]
        }

    def list_scenarios(self) -> List[Dict[str, Any]]:
        """Returns all 12 available standardized simulation scenarios."""
        return SCENARIOS_CATALOG

    def run_scenario(
        self,
        db: Session,
        scenario_id: str,
        analyst_user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes a deterministic satellite observation scenario through the EXACT SAME AGNI-NETRA pipeline.
        Pipeline:
        1. Telemetry Packet Generation
        2. Normalized Observation Synthesis
        3. AGNI-NETRA 10-Stage Pipeline Processing
        4. Independent Real Stage Latency Benchmarking
        5. Verification (Expected vs Predicted)
        """
        scenario = next((s for s in SCENARIOS_CATALOG if s["id"] == scenario_id), None)
        if not scenario:
            raise ValueError(f"Scenario '{scenario_id}' not found.")

        t_scenario_start = time.perf_counter()
        obs_time = datetime.now(timezone.utc)

        # 1. Telemetry Packet Generation
        t_telemetry_start = time.perf_counter()
        lat = scenario["target_lat"]
        lon = scenario["target_lon"]
        params = scenario["parameters"]

        footprint_geojson = self.calculate_sensor_footprint_geojson(lat, lon, "THERMAL_MWIR")

        telemetry_log = SatelliteTelemetryLog(
            satellite_id="AGNI-SAT-01",
            sensor_id="THERMAL_MWIR",
            scenario_id=scenario["id"],
            timestamp=obs_time,
            latitude=lat,
            longitude=lon,
            frp=params["frp_mw"],
            brightness=params["brightness_k"],
            confidence=params["confidence"],
            footprint_geojson=footprint_geojson,
            status="PROCESSING",
            raw_packet={
                "scenario": scenario["name"],
                "sensor_band": "3.9um_MWIR",
                "calibration_factor": 1.042,
                "telemetry_rate_kbps": 128
            },
            is_simulation=True
        )
        db.add(telemetry_log)
        db.commit()
        telemetry_duration_ms = (time.perf_counter() - t_telemetry_start) * 1000.0

        # 2. Synthesize Normalized Observation Cluster
        provenance = SourceProvenance(
            source_name="AGNI-SAT-01",
            source_type="SIMULATED_SATELLITE",
            sensor="THERMAL_MWIR",
            acquisition_time=obs_time,
            ingested_at=obs_time,
            additional_metadata={"terms_url": "https://agninetra.gov.in/telemetry/sim"}
        )

        sim_observations = []
        count = params.get("detection_count", 3)
        for i in range(count):
            offset_lat = (i - count / 2.0) * 0.002
            offset_lon = (i - count / 2.0) * 0.002
            obs = NormalizedThermalObservation(
                source="AGNI-SAT-01",
                sensor="THERMAL_MWIR",
                satellite="AGNI-SAT-01",
                latitude=round(lat + offset_lat, 6),
                longitude=round(lon + offset_lon, 6),
                acq_timestamp=obs_time,
                brightness=params["brightness_k"],
                bright_t31=params["brightness_k"] - 15.0,
                frp=round(params["frp_mw"] * (1.0 - i * 0.05), 1),
                confidence=params["confidence"],
                day_night=params["day_night"],
                source_record_id=f"AGNI-SAT-SIM-{uuid.uuid4().hex[:8]}",
                provenance=provenance,
                metadata={
                    "is_simulation": True,
                    "scenario_id": scenario["id"],
                    "scenario_name": scenario["name"]
                },
                is_demo=False
            )
            sim_observations.append(obs)

        # 3. Pipeline Ingestion & Intelligence Processing (Exact Same Pipeline)
        pipeline_result = pipeline_service.process_observations(
            db=db,
            observations=sim_observations,
            source_name=f"AGNI-SAT-01 [{scenario['name']}]"
        )

        # Update Telemetry Log Status
        telemetry_log.status = "PROCESSED"
        db.commit()

        total_latency_ms = (time.perf_counter() - t_scenario_start) * 1000.0

        # Fetch created event to inspect prediction & risk
        created_event_id = None
        event_details = None
        if pipeline_result.get("event_ids"):
            created_event_id = pipeline_result["event_ids"][0]
            evt = db.query(ThermalEvent).filter(ThermalEvent.id == created_event_id).first()
            if evt:
                event_details = {
                    "event_id": evt.id,
                    "event_code": evt.event_code,
                    "state": evt.state,
                    "district": evt.district,
                    "avg_frp": evt.avg_frp,
                    "max_frp": evt.max_frp,
                    "facility_status": evt.facility_status,
                    "predicted_class": evt.prediction.predicted_class if evt.prediction else None,
                    "confidence": evt.prediction.confidence if evt.prediction else None,
                    "risk_level": evt.risk.risk_level if evt.risk else None,
                    "risk_score": evt.risk.risk_score if evt.risk else None,
                    "shap_summary": evt.prediction.explanation_summary if evt.prediction else None
                }

        # Actual Measured Stage Durations
        st = pipeline_result.get("stage_timings_ms", {})
        benchmark = {
            "observation_to_telemetry_ms": round(telemetry_duration_ms, 2),
            "telemetry_to_ingestion_ms": st.get("ingestion_ms", 0.0),
            "clustering_ms": st.get("clustering_ms", 0.0),
            "gis_enrichment_ms": st.get("gis_enrichment_ms", 0.0),
            "ml_inference_ms": st.get("ml_inference_ms", 0.0),
            "shap_explanation_ms": st.get("shap_explanation_ms", 0.0),
            "risk_evaluation_ms": st.get("risk_evaluation_ms", 0.0),
            "total_processing_ms": round(total_latency_ms, 2),
            "target_fps_or_hz": round(1000.0 / max(total_latency_ms, 1.0), 1)
        }

        # Record scenario last_run_at in DB
        db_sc = db.query(SimulationScenario).filter(SimulationScenario.id == scenario_id).first()
        if db_sc:
            db_sc.status = "COMPLETED"
            db_sc.last_run_at = datetime.now(timezone.utc)
            db.commit()

        return {
            "status": "SUCCESS",
            "mode": "SIMULATION",
            "scenario": {
                "id": scenario["id"],
                "name": scenario["name"],
                "type": scenario["scenario_type"],
                "target": f"{scenario['target_state']} ({lat}, {lon})",
                "expected_class": scenario["expected_class"],
                "expected_risk_level": scenario["expected_risk_level"]
            },
            "satellite": {
                "id": "AGNI-SAT-01",
                "sensor": "THERMAL_MWIR",
                "observations_generated": len(sim_observations)
            },
            "event": event_details,
            "benchmark": benchmark,
            "validation": {
                "expected_class": scenario["expected_class"],
                "predicted_class": event_details["predicted_class"] if event_details else "N/A",
                "is_match": (event_details["predicted_class"] == scenario["expected_class"]) if event_details else False
            }
        }

    def replay_historical_observation(
        self,
        db: Session,
        historical_record: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Replays a real historical observation through AGNI-SAT virtual telemetry down to live processing.
        STRICT REQUIREMENT: Preserves original historical acquisition timestamp and original provenance.
        """
        replay_start_time = datetime.now(timezone.utc)

        # 1. Parse or preserve original acquisition timestamp
        raw_acq = historical_record.get("acq_timestamp")
        if isinstance(raw_acq, str):
            try:
                original_acq_time = datetime.fromisoformat(raw_acq.replace("Z", "+00:00"))
            except Exception:
                original_acq_time = datetime.now(timezone.utc) - timedelta(days=90)
        elif isinstance(raw_acq, datetime):
            original_acq_time = raw_acq
        else:
            # Reconstruct from acq_date and acq_time if available
            acq_date = historical_record.get("acq_date", "2026-06-01")
            acq_time_str = str(historical_record.get("acq_time", "0000")).zfill(4)
            try:
                original_acq_time = datetime.strptime(f"{acq_date} {acq_time_str}", "%Y-%m-%d %H%M").replace(tzinfo=timezone.utc)
            except Exception:
                original_acq_time = datetime.now(timezone.utc) - timedelta(days=90)

        # 2. Construct SourceProvenance with preserved acquisition timestamp & separate replay execution timestamp
        provenance = SourceProvenance(
            source_name="HISTORICAL_REPLAY",
            source_type="HISTORICAL_ARCHIVE",
            sensor=historical_record.get("sensor", "VIIRS_NOAA20"),
            acquisition_time=original_acq_time,
            ingested_at=replay_start_time,
            additional_metadata={
                "original_source": historical_record.get("source", "NASA_FIRMS"),
                "original_record_id": historical_record.get("source_record_id", f"HIST-{uuid.uuid4().hex[:8]}"),
                "replay_execution_time": replay_start_time.isoformat(),
                "terms_url": "https://firms.modaps.eosdis.nasa.gov"
            }
        )

        obs = NormalizedThermalObservation(
            source="HISTORICAL_REPLAY",
            sensor=historical_record.get("sensor", "VIIRS_NOAA20"),
            satellite=historical_record.get("satellite", "NOAA-20"),
            latitude=float(historical_record["latitude"]),
            longitude=float(historical_record["longitude"]),
            acq_timestamp=original_acq_time,
            brightness=float(historical_record.get("brightness", 340.0)),
            bright_t31=float(historical_record.get("bright_t31", 320.0)),
            frp=float(historical_record.get("frp", 85.0)),
            confidence=float(historical_record.get("confidence", 95.0)),
            day_night=historical_record.get("day_night", "D"),
            source_record_id=f"REPLAY-{uuid.uuid4().hex[:8]}",
            provenance=provenance,
            metadata={
                "is_replay": True,
                "original_acquisition_time": original_acq_time.isoformat(),
                "replay_execution_time": replay_start_time.isoformat(),
                "original_source": historical_record.get("source", "NASA_FIRMS")
            },
            is_demo=False
        )

        pipeline_result = pipeline_service.process_observations(
            db=db,
            observations=[obs],
            source_name="HISTORICAL REPLAY [AGNI-SAT]"
        )

        return {
            "status": "REPLAY_PROCESSED",
            "mode": "HISTORICAL_REPLAY",
            "original_acquisition_timestamp": original_acq_time.isoformat(),
            "replay_execution_timestamp": replay_start_time.isoformat(),
            "pipeline_result": pipeline_result
        }

    def schedule_mission_task(
        self,
        db: Session,
        target_name: str,
        target_lat: float,
        target_lon: float,
        sensor_id: str = "THERMAL_MWIR",
        priority: str = "HIGH",
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Creates and persists a simulated satellite mission task with true calculated next pass time.
        """
        now = datetime.now(timezone.utc)
        pass_info = self.calculate_next_pass(target_lat, target_lon, start_time=now)
        task_code = f"TASK-SAT-{int(now.timestamp())}-{uuid.uuid4().hex[:4].upper()}"

        task = MissionTask(
            task_code=task_code,
            satellite_id="AGNI-SAT-01",
            target_name=target_name,
            target_lat=target_lat,
            target_lon=target_lon,
            sensor_id=sensor_id,
            priority=priority,
            status="SIMULATED_TASK_ACCEPTED",
            tasked_by=user_id,
            scheduled_pass_time=datetime.fromisoformat(pass_info["calculated_pass_time"]),
            metadata_info={
                "calculated_pass_info": pass_info,
                "mode": "SIMULATION",
                "notes": "Simulated task scheduled for next orbital pass window."
            }
        )
        db.add(task)
        db.commit()

        return {
            "status": "SIMULATED_TASK_ACCEPTED",
            "task_id": task.id,
            "task_code": task.task_code,
            "satellite_id": "AGNI-SAT-01",
            "target": {
                "name": target_name,
                "latitude": target_lat,
                "longitude": target_lon
            },
            "sensor_id": sensor_id,
            "priority": priority,
            "scheduled_pass_time": pass_info["calculated_pass_time"],
            "pass_delay_minutes": pass_info["pass_delay_minutes"],
            "closest_approach_distance_km": pass_info["closest_approach_distance_km"],
            "swath_coverage": pass_info["swath_coverage"],
            "mode": "SIMULATION",
            "message": f"Virtual task {task_code} accepted. Next observation opportunity in {pass_info['pass_delay_minutes']} minutes."
        }


satellite_simulator = SatelliteSimulatorService()
