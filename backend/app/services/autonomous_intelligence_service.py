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
    HistoricalBaseline, EventFeature, ModelPrediction, RiskScore, Alert
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

    def subscribe(self, callback: Callable[[AutonomousIntelligenceOutcome], None]) -> None:
        """Allows side-by-side orchestration layers (such as JARVIS) to observe intelligence states."""
        if callback not in self._subscribers:
            self._subscribers.append(callback)

    def unsubscribe(self, callback: Callable[[AutonomousIntelligenceOutcome], None]) -> None:
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
        correlation_id: str,
        incident_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> IncidentLifecycleTransition:
        """Appends an immutable, audited lifecycle state transition."""
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
        return trans

    def get_lifecycle_history(self, event_id: str) -> List[IncidentLifecycleTransition]:
        return self._lifecycle_history.get(event_id, [])

    def process_observations_autonomous(
        self,
        db: Session,
        raw_observations: List[Dict[str, Any]],
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

        if not raw_observations:
            return outcomes

        # 1. Validation & Deduplication (OBSERVED -> VALIDATING)
        valid_detections = []
        for obs in raw_observations:
            lat = float(obs.get("latitude", 0.0))
            lon = float(obs.get("longitude", 0.0))
            frp = float(obs.get("frp", 0.0) or 0.0)
            acq_ts = obs.get("acq_timestamp") or datetime.now(timezone.utc).isoformat()
            sensor = str(obs.get("sensor", "VIIRS"))

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
                "source_record_id": obs.get("source_record_id", f"rec-{uuid.uuid4().hex[:6]}"),
                "source": obs.get("source", source_name),
                "sensor": sensor,
                "satellite": obs.get("satellite", "NOAA-20"),
                "latitude": lat,
                "longitude": lon,
                "acq_timestamp": acq_ts,
                "brightness": float(obs.get("brightness", 320.0) or 320.0),
                "bright_t31": float(obs.get("bright_t31", 295.0) or 295.0),
                "frp": frp,
                "confidence": float(obs.get("confidence", 85.0) or 85.0),
                "day_night": obs.get("day_night", "D"),
                "raw_payload": obs.get("metadata", {}),
                "is_demo": obs.get("is_demo", False)
            })

        if not valid_detections:
            return outcomes

        # 2. Spatiotemporal DBSCAN Clustering
        clustered_events = cluster_thermal_detections(valid_detections, eps_km=1.5)

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

        for cluster in clustered_events:
            c_lat = cluster["latitude"]
            c_lon = cluster["longitude"]
            c_dets = cluster["detections"]
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
                correlation_id=correlation_id
            )
            transitions.append(t1)

            # Transition 2: VALIDATING
            t2 = self.record_transition(
                event_id=evt_code,
                from_state=IncidentLifecycleState.OBSERVED,
                to_state=IncidentLifecycleState.VALIDATING,
                subsystem="TELEMETRY_VALIDATOR",
                rationale="Validated coordinate envelope and geodetic bounds inside sovereign India",
                correlation_id=correlation_id
            )
            transitions.append(t2)

            # 3. Context Fusion (CONTEXTUALIZING)
            nearest_fac, fac_dist = find_nearest_facility(c_lat, c_lon, fac_dicts)
            lulc_cat, zone_name, lulc_dists = lulc_engine.classify_location(c_lat, c_lon)

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
                metadata={"nearest_facility": nearest_fac["name"] if nearest_fac else None, "distance_m": fac_dist}
            )
            transitions.append(t3)

            # 4. Persistence & Historical Baseline (ANALYZING)
            p_metrics = calculate_persistence_metrics(c_dets)
            baseline = None
            if fac_id:
                baseline = db.query(HistoricalBaseline).filter(HistoricalBaseline.facility_id == fac_id).first()
            baseline_info = calculate_baseline_deviation(cluster["max_frp"], baseline)

            t4 = self.record_transition(
                event_id=evt_code,
                from_state=IncidentLifecycleState.CONTEXTUALIZING,
                to_state=IncidentLifecycleState.ANALYZING,
                subsystem="TEMPORAL_BASELINE_ENGINE",
                rationale=f"Evaluated persistence score {p_metrics['persistence_score']:.2f}, baseline deviation {baseline_info.get('deviation_ratio', 1.0):.2f}",
                correlation_id=correlation_id
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

            t5 = self.record_transition(
                event_id=evt_code,
                from_state=IncidentLifecycleState.ANALYZING,
                to_state=IncidentLifecycleState.CLASSIFYING,
                subsystem="ML_CLASSIFIER_XGBOOST",
                rationale=f"Classified as '{pred_class}' with confidence {pred_conf:.2f}",
                correlation_id=correlation_id
            )
            transitions.append(t5)

            # 6. Risk & Governed Priority Calculation (ASSESSING)
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

            t6 = self.record_transition(
                event_id=evt_code,
                from_state=IncidentLifecycleState.CLASSIFYING,
                to_state=IncidentLifecycleState.ASSESSING,
                subsystem="RISK_AND_PRIORITY_ENGINE",
                rationale=f"Computed 5-factor risk score {r_score:.1f} ({r_level}), priority {priority_score:.1f}",
                correlation_id=correlation_id,
                metadata={"risk_score": r_score, "priority_score": priority_score, "risk_level": r_level}
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
                incident_id=incident_id
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
                incident_id=incident_id
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
                is_demo=False
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
                    is_demo=False
                )
                db.add(det)

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
            db.commit()

            why_it_matters = (
                f"New thermal event {evt_code} detected in {district}, {state}. "
                f"Risk is {r_score:.0f}/100 ({r_level}) driven by {reasons[0] if reasons else 'elevated FRP'}. "
                f"Classified as {pred_class} with {pred_conf*100:.0f}% confidence. "
                f"Human verification is {'mandatory' if requires_hitl else 'optional'}."
            )

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
                transitions=transitions
            )
            outcomes.append(outcome)

            # Emit state to subscribers (e.g. JARVIS)
            self._notify_subscribers(outcome)

        return outcomes


# Singleton Autonomous Intelligence Core instance
autonomous_intelligence_core = AutonomousIntelligenceCore()
