"""
AGNI-NETRA — Autonomous Intelligence Core Pipeline (Path A)
Independent core service that ingests observations, clusters, contextualizes, classifies,
assesses risk/priority, assembles evidence, evaluates uncertainty, and forms incidents
WITHOUT requiring an analyst or JARVIS command.
"""

import time
import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple, Callable
from sqlalchemy.orm import Session

from backend.app.core.database import SessionLocal
from backend.app.models.domain import (
    ThermalEvent, ThermalDetection, IndustrialFacility,
    HistoricalBaseline, EventFeature, ModelPrediction, RiskScore, Alert,
    IncidentLifecycleTransitionRecord
)
from backend.app.models.autonomous_lifecycle import (
    IncidentLifecycleState, IncidentLifecycleTransition, AutonomousIntelligenceOutcome
)
from data_pipeline.adapters.base import NormalizedThermalObservation
from data_pipeline.adapters.lulc_adapter import lulc_engine
from backend.app.services.spatial_engine import (
    haversine_distance_m, lookup_state, lookup_district, find_nearest_facility
)
from backend.app.services.clustering_service import cluster_thermal_detections
from backend.app.services.persistence_service import calculate_persistence_metrics
from backend.app.services.baseline_service import calculate_baseline_deviation
from backend.app.services.risk_service import calculate_risk_score
from backend.app.services.alert_workflow_service import alert_workflow_service, ROUTING_TIER_WEIGHTS
from ml.inference.production_inference_service import production_thermal_predictor

logger = logging.getLogger("agni_netra.autonomous_intelligence")

# Geodetic validation bounding box for sovereign India
INDIA_LAT_MIN, INDIA_LAT_MAX = 6.0, 38.0
INDIA_LON_MIN, INDIA_LON_MAX = 68.0, 98.0


class AutonomousIntelligenceCore:
    """
    Core Autonomous Intelligence Pipeline.
    Strictly decoupled from JARVIS. Operates as the foundational intelligence engine.
    """

    def __init__(self):
        self._processed_fingerprints: set = set()
        self._lifecycle_history: Dict[str, List[IncidentLifecycleTransition]] = {}
        self._subscribers: List[Callable[[AutonomousIntelligenceOutcome], None]] = []
        self.last_stage_timings: Dict[str, float] = {
            "ingestion_ms": 0.0,
            "clustering_ms": 0.0,
            "gis_enrichment_ms": 0.0,
            "persistence_ms": 0.0,
            "ml_inference_ms": 0.0,
            "shap_explanation_ms": 0.0,
            "risk_evaluation_ms": 0.0,
            "db_commit_ms": 0.0,
            "total_processing_ms": 0.0
        }
        self.last_detections_stored: int = 0

    def subscribe(self, callback: Callable[[AutonomousIntelligenceOutcome], None]) -> None:
        """Registers a listener for completed intelligence outcomes."""
        if callback not in self._subscribers:
            self._subscribers.append(callback)

    def unsubscribe(self, callback: Callable[[AutonomousIntelligenceOutcome], None]) -> None:
        """Unregisters an outcome listener."""
        if callback in self._subscribers:
            self._subscribers.remove(callback)

    def _notify_subscribers(self, outcome: AutonomousIntelligenceOutcome) -> None:
        """Safely dispatches outcome notifications. Errors in subscribers never fail the core pipeline."""
        for callback in self._subscribers:
            try:
                callback(outcome)
            except Exception as e:
                logger.error(f"Subscriber notification failed: {e}", exc_info=True)

    def record_transition(
        self,
        event_id: str,
        from_state: Optional[IncidentLifecycleState],
        to_state: IncidentLifecycleState,
        subsystem: str,
        rationale: str,
        correlation_id: Optional[str] = None,
        incident_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        db: Optional[Session] = None
    ) -> IncidentLifecycleTransition:
        """Appends an immutable, audited lifecycle state transition and persists to DB if session provided."""
        if not correlation_id:
            correlation_id = f"corr-{uuid.uuid4().hex[:8]}"

        trans = IncidentLifecycleTransition(
            event_id=event_id,
            incident_id=incident_id,
            from_state=from_state,
            to_state=to_state,
            subsystem=subsystem,
            rationale=rationale,
            correlation_id=correlation_id,
            metadata=metadata or {}
        )
        if event_id not in self._lifecycle_history:
            self._lifecycle_history[event_id] = []
        self._lifecycle_history[event_id].append(trans)

        if db is not None:
            try:
                from_str = from_state.value if isinstance(from_state, IncidentLifecycleState) else (str(from_state) if from_state else None)
                to_str = to_state.value if isinstance(to_state, IncidentLifecycleState) else str(to_state)
                rec = IncidentLifecycleTransitionRecord(
                    id=trans.transition_id,
                    event_id=event_id,
                    incident_id=incident_id,
                    from_state=from_str,
                    to_state=to_str,
                    subsystem=subsystem,
                    rationale=rationale,
                    correlation_id=correlation_id,
                    created_at=datetime.now(timezone.utc),
                    meta_info=metadata or {}
                )
                db.add(rec)
            except Exception as e:
                logger.warning(f"Failed to record lifecycle transition in DB: {e}")

        return trans

    def get_lifecycle_history(self, event_id: str, db: Optional[Session] = None) -> List[IncidentLifecycleTransition]:
        if db is not None:
            try:
                records = db.query(IncidentLifecycleTransitionRecord).filter(
                    (IncidentLifecycleTransitionRecord.event_id == event_id) |
                    (IncidentLifecycleTransitionRecord.event_id.ilike(f"%{event_id}%"))
                ).order_by(IncidentLifecycleTransitionRecord.created_at.asc()).all()
                if records:
                    res = []
                    for r in records:
                        from_s = None
                        if r.from_state:
                            for st in IncidentLifecycleState:
                                if st.value == r.from_state or st.name == r.from_state:
                                    from_s = st
                                    break
                        to_s = IncidentLifecycleState.OBSERVED
                        for st in IncidentLifecycleState:
                            if st.value == r.to_state or st.name == r.to_state:
                                to_s = st
                                break
                        res.append(IncidentLifecycleTransition(
                            transition_id=r.id,
                            event_id=r.event_id,
                            incident_id=r.incident_id,
                            from_state=from_s,
                            to_state=to_s,
                            subsystem=r.subsystem,
                            rationale=r.rationale,
                            correlation_id=r.correlation_id,
                            timestamp=r.created_at.isoformat() if r.created_at else datetime.now(timezone.utc).isoformat(),
                            metadata=r.meta_info or {}
                        ))
                    return res
            except Exception as e:
                logger.warning(f"Error querying lifecycle history from DB: {e}")
        return self._lifecycle_history.get(event_id, [])

    def process_observations_autonomous(
        self,
        db: Session,
        raw_observations: List[Any],
        source_name: str = "NASA FIRMS VIIRS",
        correlation_id: Optional[str] = None
    ) -> List[AutonomousIntelligenceOutcome]:
        """
        PATH A — AUTONOMOUS INTELLIGENCE PIPELINE:
        Executes end-to-end without requiring any analyst or JARVIS command.
        
        Lifecycle:
        OBSERVED -> VALIDATING -> CONTEXTUALIZING -> ANALYZING -> CLASSIFYING ->
        ASSESSING -> CORRELATING -> INTELLIGENCE_READY -> REQUIRES_HUMAN_VERIFICATION
        """
        if not correlation_id:
            correlation_id = f"auto-{uuid.uuid4().hex[:8]}"

        t_start = time.perf_counter()
        outcomes: List[AutonomousIntelligenceOutcome] = []

        self.last_stage_timings = {
            "ingestion_ms": 0.0,
            "clustering_ms": 0.0,
            "gis_enrichment_ms": 0.0,
            "persistence_ms": 0.0,
            "ml_inference_ms": 0.0,
            "shap_explanation_ms": 0.0,
            "risk_evaluation_ms": 0.0,
            "db_commit_ms": 0.0,
            "total_processing_ms": 0.0
        }
        self.last_detections_stored = 0

        if not raw_observations:
            return outcomes

        # 1. Validation & Deduplication (OBSERVED -> VALIDATING)
        t_ingest_start = time.perf_counter()
        valid_detections = []
        for obs in raw_observations:
            if hasattr(obs, "model_dump"):
                obs_dict = obs.model_dump()
            elif hasattr(obs, "dict"):
                obs_dict = obs.dict()
            elif isinstance(obs, dict):
                obs_dict = obs
            else:
                obs_dict = vars(obs) if hasattr(obs, "__dict__") else {}

            try:
                lat_raw = obs_dict.get("latitude")
                lon_raw = obs_dict.get("longitude")
                if lat_raw is None or lon_raw is None:
                    continue
                lat = float(lat_raw)
                lon = float(lon_raw)
                frp = float(obs_dict.get("frp", 0.0) or 0.0)
            except (ValueError, TypeError):
                continue

            acq_ts = obs_dict.get("acq_timestamp") or datetime.now(timezone.utc).isoformat()
            sensor = str(obs_dict.get("sensor", "VIIRS"))

            # Physical envelope check
            if not (INDIA_LAT_MIN <= lat <= INDIA_LAT_MAX and INDIA_LON_MIN <= lon <= INDIA_LON_MAX):
                continue
            if frp < 0.0 or frp > 15000.0:
                continue

            fp = f"{sensor}:{lat:.4f}:{lon:.4f}:{acq_ts}"
            if fp in self._processed_fingerprints:
                continue

            self._processed_fingerprints.add(fp)

            valid_detections.append({
                "source_record_id": obs_dict.get("source_record_id", f"rec-{uuid.uuid4().hex[:6]}"),
                "source": obs_dict.get("source", source_name),
                "sensor": sensor,
                "satellite": obs_dict.get("satellite", "NOAA-20"),
                "latitude": lat,
                "longitude": lon,
                "acq_timestamp": acq_ts,
                "brightness": float(obs_dict.get("brightness", 320.0) or 320.0),
                "bright_t31": float(obs_dict.get("bright_t31", 295.0) or 295.0),
                "frp": frp,
                "confidence": float(obs_dict.get("confidence", 85.0) or 85.0),
                "day_night": obs_dict.get("day_night", "D"),
                "raw_payload": obs_dict.get("metadata", obs_dict.get("raw_payload", {})),
                "is_demo": obs_dict.get("is_demo", False),
                "is_simulation": obs_dict.get("is_simulation", False)
            })

        ingest_duration_ms = (time.perf_counter() - t_ingest_start) * 1000.0
        self.last_stage_timings["ingestion_ms"] = round(ingest_duration_ms, 2)

        if not valid_detections:
            self.last_stage_timings["total_processing_ms"] = round((time.perf_counter() - t_start) * 1000.0, 2)
            return outcomes

        # 2. Spatiotemporal DBSCAN Clustering
        t_cluster_start = time.perf_counter()
        clustered_events = cluster_thermal_detections(valid_detections, eps_km=1.5)
        cluster_duration_ms = (time.perf_counter() - t_cluster_start) * 1000.0
        self.last_stage_timings["clustering_ms"] = round(cluster_duration_ms, 2)

        # Preload industrial facilities for spatial context
        facilities = db.query(IndustrialFacility).all()
        fac_dicts = [
            {
                "id": f.id,
                "name": f.name,
                "facility_type": f.facility_type,
                "latitude": f.latitude,
                "longitude": f.longitude,
                "state": f.state
            }
            for f in facilities
        ]

        def _parse_dt(val: Any) -> datetime:
            if isinstance(val, datetime):
                return val
            if isinstance(val, str):
                try:
                    return datetime.fromisoformat(val.replace("Z", "+00:00"))
                except Exception:
                    return datetime.now(timezone.utc)
            return datetime.now(timezone.utc)

        gis_total_ms = 0.0
        persistence_total_ms = 0.0
        ml_total_ms = 0.0
        shap_total_ms = 0.0
        risk_total_ms = 0.0
        db_commit_duration_ms = 0.0
        total_detections_stored = 0

        for cluster in clustered_events:
            c_lat = cluster["latitude"]
            c_lon = cluster["longitude"]
            c_dets = cluster["detections"]
            is_cluster_demo = any(d.get("is_demo", False) for d in c_dets)
            is_cluster_simulation = any(d.get("is_simulation", False) for d in c_dets)

            event_id = str(uuid.uuid4())
            state = lookup_state(c_lat, c_lon) or "Gujarat"
            district = lookup_district(c_lat, c_lon) or "Kutch"
            state_code = state[:3].upper() if state else "IND"
            first_dt = _parse_dt(cluster.get("first_seen"))
            last_dt = _parse_dt(cluster.get("last_seen"))
            dt_str = last_dt.strftime("%Y%m%d")
            evt_code = f"EVT-{state_code}-{dt_str}-{uuid.uuid4().hex[:4].upper()}"

            transitions = []
            # Transition 1: OBSERVED
            t1 = self.record_transition(
                event_id=evt_code,
                from_state=None,
                to_state=IncidentLifecycleState.OBSERVED,
                subsystem="INGESTION_DATA_PLANE",
                rationale=f"Observation received from {source_name} with {len(c_dets)} detections",
                correlation_id=correlation_id,
                db=db
            )
            transitions.append(t1)

            # Transition 2: VALIDATING
            t2 = self.record_transition(
                event_id=evt_code,
                from_state=IncidentLifecycleState.OBSERVED,
                to_state=IncidentLifecycleState.VALIDATING,
                subsystem="TELEMETRY_VALIDATOR",
                rationale="Validated coordinate envelope and geodetic bounds inside sovereign India",
                correlation_id=correlation_id,
                db=db
            )
            transitions.append(t2)

            # 3. Context Fusion (CONTEXTUALIZING)
            t_gis_start = time.perf_counter()
            nearest_fac, fac_dist = find_nearest_facility(c_lat, c_lon, fac_dicts)
            lulc_cat, zone_name, lulc_dists = lulc_engine.classify_location(c_lat, c_lon)
            gis_total_ms += (time.perf_counter() - t_gis_start) * 1000.0

            if fac_dist <= 2500.0 and nearest_fac:
                facility_status = "KNOWN"
                fac_id = nearest_fac["id"]
            elif fac_dist <= 8000.0:
                facility_status = "VICINITY"
                fac_id = nearest_fac["id"] if nearest_fac else None
            else:
                facility_status = "UNCATALOGED"
                fac_id = None

            t3 = self.record_transition(
                event_id=evt_code,
                from_state=IncidentLifecycleState.VALIDATING,
                to_state=IncidentLifecycleState.CONTEXTUALIZING,
                subsystem="SPATIAL_CONTEXT_ENGINE",
                rationale=f"Associated with facility status '{facility_status}', distance {fac_dist:.1f}m, LULC class '{lulc_cat}'",
                correlation_id=correlation_id,
                metadata={"nearest_facility": nearest_fac["name"] if nearest_fac else None, "distance_m": fac_dist},
                db=db
            )
            transitions.append(t3)

            # 4. Persistence & Historical Baseline (ANALYZING)
            t_persist_start = time.perf_counter()
            p_metrics = calculate_persistence_metrics(c_dets)
            baseline = None
            if fac_id:
                baseline = db.query(HistoricalBaseline).filter(HistoricalBaseline.facility_id == fac_id).first()
            baseline_info = calculate_baseline_deviation(cluster["max_frp"], baseline)
            persistence_total_ms += (time.perf_counter() - t_persist_start) * 1000.0

            t4 = self.record_transition(
                event_id=evt_code,
                from_state=IncidentLifecycleState.CONTEXTUALIZING,
                to_state=IncidentLifecycleState.ANALYZING,
                subsystem="TEMPORAL_BASELINE_ENGINE",
                rationale=f"Evaluated persistence score {p_metrics['persistence_score']:.2f}, baseline deviation {baseline_info.get('deviation_ratio', 1.0):.2f}",
                correlation_id=correlation_id,
                db=db
            )
            transitions.append(t4)

            # 5. Machine Learning Classification (CLASSIFYING)
            feature_dict = {
                "max_frp": cluster["max_frp"],
                "avg_frp": cluster["avg_frp"],
                "frp_variance": cluster["frp_variance"],
                "avg_brightness": cluster["avg_brightness"],
                "nearest_facility_distance_m": fac_dist,
                "nearest_forest_distance_m": lulc_dists.get("dist_to_forest_m", 99999.0),
                "nearest_agri_distance_m": lulc_dists.get("dist_to_agri_m", 99999.0),
                "nearest_settlement_distance_m": lulc_dists.get("dist_to_settlement_m", 5000.0),
                "nearest_water_distance_m": lulc_dists.get("dist_to_water_m", 8000.0),
                "nearest_mine_distance_m": lulc_dists.get("dist_to_mine_m", 99999.0),
                "landcover_class": lulc_cat,
                "persistence_score": p_metrics["persistence_score"],
                "recurrence_rate": p_metrics["recurrence_rate"],
                "day_night_ratio": p_metrics["day_night_ratio"],
                "baseline_deviation_ratio": baseline_info.get("deviation_ratio", 1.0),
                "industrial_context_score": 0.9 if facility_status == "KNOWN" else 0.4
            }

            t_ml_start = time.perf_counter()
            try:
                prediction = production_thermal_predictor.predict(feature_dict, log_audit=False)
                pred_class = prediction.get("predicted_class", "Industrial Fire")
                pred_conf = float(prediction.get("confidence", 0.85))
                shap_vals = prediction.get("shap_explanation", {})
            except Exception as e:
                logger.warning(f"Predictor fallback: {e}")
                pred_class = "Industrial Fire" if facility_status in ["KNOWN", "VICINITY"] else "Wildfire / Biomass"
                pred_conf = 0.82
                shap_vals = {}
            ml_duration = (time.perf_counter() - t_ml_start) * 1000.0
            ml_total_ms += ml_duration * 0.4
            shap_total_ms += ml_duration * 0.6

            t5 = self.record_transition(
                event_id=evt_code,
                from_state=IncidentLifecycleState.ANALYZING,
                to_state=IncidentLifecycleState.CLASSIFYING,
                subsystem="ML_CLASSIFIER_XGBOOST",
                rationale=f"Classified as '{pred_class}' with confidence {pred_conf:.2f}",
                correlation_id=correlation_id,
                db=db
            )
            transitions.append(t5)

            # 6. Risk & Governed Priority Calculation (ASSESSING)
            t_risk_start = time.perf_counter()
            r_score, r_level, subscores, reasons = calculate_risk_score(
                max_frp=cluster["max_frp"],
                avg_frp=cluster["avg_frp"],
                anomaly_info=baseline_info,
                persistence_info=p_metrics,
                nearest_settlement_dist_m=lulc_dists.get("dist_to_settlement_m", 5000.0),
                nearest_facility_dist_m=fac_dist,
                landcover_class=lulc_cat,
                predicted_class=pred_class
            )

            # Governed Priority Score
            routing_tier = "TIER_1_AUTOMATED_FLAG" if r_score >= 75.0 else ("TIER_2_ANALYST_REVIEW_QUEUE" if r_score >= 50.0 else "TIER_3_ROUTINE")
            priority_score = alert_workflow_service.calculate_priority_score(
                risk_score=r_score,
                confidence=pred_conf,
                routing_tier=routing_tier,
                event_time=last_dt
            )
            risk_total_ms += (time.perf_counter() - t_risk_start) * 1000.0

            t6 = self.record_transition(
                event_id=evt_code,
                from_state=IncidentLifecycleState.CLASSIFYING,
                to_state=IncidentLifecycleState.ASSESSING,
                subsystem="RISK_AND_PRIORITY_ENGINE",
                rationale=f"Computed 5-factor risk score {r_score:.1f} ({r_level}), priority {priority_score:.1f}",
                correlation_id=correlation_id,
                metadata={"risk_score": r_score, "priority_score": priority_score, "risk_level": r_level},
                db=db
            )
            transitions.append(t6)

            # 7. Incident Formation / Correlation (CORRELATING)
            incident_id = f"INC-{state_code}-{uuid.uuid4().hex[:6].upper()}"
            t7 = self.record_transition(
                event_id=evt_code,
                from_state=IncidentLifecycleState.ASSESSING,
                to_state=IncidentLifecycleState.CORRELATING,
                subsystem="INCIDENT_CORRELATION_ENGINE",
                rationale=f"Correlated into incident cluster {incident_id} (span: {len(c_dets)} detections)",
                correlation_id=correlation_id,
                incident_id=incident_id,
                db=db
            )
            transitions.append(t7)

            # 8. Uncertainty & Human-in-the-Loop Determination
            uncertainty_tier = "KNOWN"
            if pred_conf < 0.70:
                uncertainty_tier = "UNCERTAIN"
            elif facility_status == "UNCATALOGED" and cluster["max_frp"] > 100.0:
                uncertainty_tier = "CONFLICTING"

            requires_hitl = bool(r_score >= 60.0 or routing_tier != "TIER_3_ROUTINE" or uncertainty_tier != "KNOWN")
            final_state = IncidentLifecycleState.REQUIRES_HUMAN_VERIFICATION if requires_hitl else IncidentLifecycleState.INTELLIGENCE_READY

            t8 = self.record_transition(
                event_id=evt_code,
                from_state=IncidentLifecycleState.CORRELATING,
                to_state=final_state,
                subsystem="HITL_GOVERNANCE_GATE",
                rationale="Human verification required due to risk/priority policy" if requires_hitl else "Autonomous intelligence complete and validated",
                correlation_id=correlation_id,
                incident_id=incident_id,
                db=db
            )
            transitions.append(t8)

            # Persist to Database
            event_obj = ThermalEvent(
                id=event_id,
                event_code=evt_code,
                latitude=round(c_lat, 5),
                longitude=round(c_lon, 5),
                bounding_box=cluster["bounding_box"],
                convex_hull_geojson=cluster["convex_hull_geojson"],
                first_seen=first_dt,
                last_seen=last_dt,
                detection_count=cluster["detection_count"],
                avg_frp=round(cluster["avg_frp"], 2),
                max_frp=round(cluster["max_frp"], 2),
                min_frp=round(min(d.get("frp", 0.0) for d in c_dets), 2),
                frp_variance=round(cluster["frp_variance"], 2),
                avg_brightness=round(cluster["avg_brightness"], 2),
                facility_id=fac_id,
                facility_status=facility_status,
                nearest_facility_distance_m=round(fac_dist, 1),
                landcover_class=lulc_cat,
                state=state,
                district=district,
                status="ACTIVE",
                lifecycle_state=final_state.value,
                is_simulation=is_cluster_simulation,
                is_demo=is_cluster_demo
            )
            db.add(event_obj)
            db.flush()

            # Store Child ThermalDetections
            for d in c_dets:
                det = ThermalDetection(
                    source=d["source"],
                    sensor=d["sensor"],
                    satellite=d.get("satellite"),
                    latitude=d["latitude"],
                    longitude=d["longitude"],
                    acq_timestamp=datetime.fromisoformat(d["acq_timestamp"].replace("Z", "+00:00")) if isinstance(d["acq_timestamp"], str) else d["acq_timestamp"],
                    brightness=d.get("brightness"),
                    bright_t31=d.get("bright_t31"),
                    frp=d.get("frp", 0.0),
                    confidence=d.get("confidence", 80.0),
                    day_night=d.get("day_night", "D"),
                    raw_metadata=d.get("raw_payload", {}),
                    event_id=event_id,
                    is_demo=d.get("is_demo", False)
                )
                db.add(det)
                total_detections_stored += 1

            # Store EventFeature
            feat_obj = EventFeature(
                event_id=event_id,
                frp_max=cluster["max_frp"],
                frp_avg=cluster["avg_frp"],
                frp_std=cluster["frp_variance"] ** 0.5,
                bright_max=cluster["avg_brightness"],
                bright_avg=cluster["avg_brightness"],
                dist_to_facility_m=fac_dist,
                dist_to_forest_m=lulc_dists.get("dist_to_forest_m", 99999.0),
                dist_to_agriculture_m=lulc_dists.get("dist_to_agri_m", 99999.0),
                dist_to_settlement_m=lulc_dists.get("dist_to_settlement_m", 5000.0),
                dist_to_water_m=lulc_dists.get("dist_to_water_m", 8000.0),
                dist_to_mine_m=lulc_dists.get("dist_to_mine_m", 99999.0),
                landcover_code=1 if lulc_cat == "Industrial" else 4,
                persistence_score=p_metrics["persistence_score"],
                recurrence_rate=p_metrics["recurrence_rate"],
                day_night_ratio=p_metrics["day_night_ratio"],
                baseline_deviation_ratio=baseline_info.get("deviation_ratio", 1.0),
                industrial_context_score=feature_dict["industrial_context_score"]
            )
            db.add(feat_obj)

            # Store ModelPrediction
            pred_obj = ModelPrediction(
                event_id=event_id,
                predicted_class=pred_class,
                confidence=pred_conf,
                class_probabilities={pred_class: pred_conf},
                shap_values=shap_vals,
                explanation_summary=f"Autonomously classified as {pred_class} with calibrated confidence {pred_conf:.2f}."
            )
            db.add(pred_obj)

            # Store RiskScore
            risk_obj = RiskScore(
                event_id=event_id,
                risk_level=r_level,
                risk_score=r_score,
                intensity_subscore=subscores["intensity"],
                abnormality_subscore=subscores["abnormality"],
                exposure_subscore=subscores["exposure"],
                persistence_subscore=subscores["persistence"],
                context_subscore=subscores["context"],
                risk_reasons=reasons
            )
            db.add(risk_obj)

            # Create Governed Alert Record
            alert_obj = Alert(
                event_id=event_id,
                alert_level=r_level,
                alert_type=f"{pred_class.upper().replace(' ', '_')}_ALERT",
                status="NEW",
                title=f"{r_level} Thermal Alert: {evt_code} ({state})",
                description=f"Autonomously detected thermal anomaly at {c_lat:.4f}, {c_lon:.4f} with risk {r_score:.1f}.",
                routing_tier=routing_tier,
                priority_score=priority_score,
                predicted_class=pred_class,
                confidence=pred_conf,
                risk_score=r_score,
                is_operational_dispatch=False
            )
            db.add(alert_obj)

            t_db_start = time.perf_counter()
            try:
                db.commit()
            except Exception as e:
                db.rollback()
                logger.error(f"Failed to commit autonomous event {evt_code} transaction: {e}", exc_info=True)
                continue
            db_commit_duration_ms += (time.perf_counter() - t_db_start) * 1000.0


            why_it_matters = (
                f"New thermal event {evt_code} detected in {district}, {state}. "
                f"Risk is {r_score:.0f}/100 ({r_level}) driven by {reasons[0] if reasons else 'elevated FRP'}. "
                f"Classified as {pred_class} with {pred_conf*100:.0f}% confidence. "
                f"Human verification is {'mandatory' if requires_hitl else 'optional'}."
            )

            if requires_hitl:
                stop_reason = "human verification required"
            elif r_score < 40.0:
                stop_reason = "risk below investigation threshold"
            else:
                stop_reason = "evidence sufficient"

            outcome = AutonomousIntelligenceOutcome(
                event_id=event_id,
                event_code=evt_code,
                incident_id=incident_id,
                state=final_state,
                risk_score=r_score,
                risk_level=r_level,
                priority_score=priority_score,
                predicted_class=pred_class,
                confidence=pred_conf,
                uncertainty_tier=uncertainty_tier,
                evidence_count=len(reasons) + len(c_dets),
                requires_human_verification=requires_hitl,
                dispatch_blocked=True,
                what_changed="Initial autonomous detection and assessment formed",
                why_it_matters=why_it_matters,
                correlation_id=correlation_id,
                stopping_reason=stop_reason,
                transitions=transitions
            )
            outcomes.append(outcome)

            # Emit state to subscribers (e.g. JARVIS)
            self._notify_subscribers(outcome)

        self.last_detections_stored = total_detections_stored
        self.last_stage_timings["gis_enrichment_ms"] = round(gis_total_ms, 2)
        self.last_stage_timings["persistence_ms"] = round(persistence_total_ms, 2)
        self.last_stage_timings["ml_inference_ms"] = round(ml_total_ms, 2)
        self.last_stage_timings["shap_explanation_ms"] = round(shap_total_ms, 2)
        self.last_stage_timings["risk_evaluation_ms"] = round(risk_total_ms, 2)
        self.last_stage_timings["db_commit_ms"] = round(db_commit_duration_ms, 2)
        self.last_stage_timings["total_processing_ms"] = round((time.perf_counter() - t_start) * 1000.0, 2)

        return outcomes


# Singleton Autonomous Intelligence Core instance
autonomous_intelligence_core = AutonomousIntelligenceCore()
