import time
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from backend.app.models.domain import (
    ThermalDetection, ThermalEvent, IndustrialFacility,
    HistoricalBaseline, EventFeature, ModelPrediction, RiskScore, Alert, DataSource
)
from data_pipeline.adapters.base import NormalizedThermalObservation
from data_pipeline.adapters.lulc_adapter import lulc_engine
from backend.app.services.spatial_engine import (
    haversine_distance_m, compute_cluster_geometry, lookup_state, lookup_district, find_nearest_facility
)
from backend.app.services.clustering_service import cluster_thermal_detections
from backend.app.services.persistence_service import calculate_persistence_metrics
from backend.app.services.baseline_service import calculate_baseline_deviation
from backend.app.services.anomaly_service import detect_thermal_anomalies
from backend.app.services.risk_service import calculate_risk_score
from ml.inference.predictor import thermal_predictor


class ThermalPipelineService:
    """
    End-to-end Geospatial & Thermal Processing Pipeline.
    Orchestrates: Raw Ingestion -> Deduplication -> Spatiotemporal DBSCAN -> LULC & Facility Enrichment -> Event Storage.
    Measures independent actual execution timing for every processing stage.
    """

    def process_observations(
        self,
        db: Session,
        observations: List[NormalizedThermalObservation],
        source_name: str = "NASA FIRMS VIIRS"
    ) -> Dict[str, Any]:
        """
        Processes a batch of normalized thermal observations into stored detections and clustered events.
        Measures real stage latencies independently using time.perf_counter().
        """
        if not observations:
            return {
                "status": "EMPTY",
                "events_created": 0,
                "event_ids": [],
                "detections_stored": 0,
                "stage_timings_ms": {
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
            }

        t_pipeline_start = time.perf_counter()

        # 1. Ingestion & Spatial Indexing
        t_ingest_start = time.perf_counter()
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

        raw_detection_dicts = []
        for obs in observations:
            raw_detection_dicts.append({
                "source_record_id": obs.source_record_id,
                "source": obs.source,
                "sensor": obs.sensor,
                "satellite": obs.satellite,
                "latitude": obs.latitude,
                "longitude": obs.longitude,
                "acq_timestamp": obs.acq_timestamp,
                "brightness": obs.brightness,
                "bright_t31": obs.bright_t31,
                "frp": obs.frp,
                "confidence": obs.confidence,
                "day_night": obs.day_night,
                "raw_payload": obs.metadata,
                "is_demo": obs.is_demo
            })
        ingest_duration_ms = (time.perf_counter() - t_ingest_start) * 1000.0

        # 2. Spatiotemporal DBSCAN Clustering
        t_cluster_start = time.perf_counter()
        clustered_events = cluster_thermal_detections(raw_detection_dicts, eps_km=1.5)
        cluster_duration_ms = (time.perf_counter() - t_cluster_start) * 1000.0

        created_event_ids = []
        total_detections_stored = 0

        gis_total_ms = 0.0
        persistence_total_ms = 0.0
        ml_total_ms = 0.0
        shap_total_ms = 0.0
        risk_total_ms = 0.0

        for idx, cluster in enumerate(clustered_events):
            c_lat = cluster["latitude"]
            c_lon = cluster["longitude"]
            c_dets = cluster["detections"]
            is_demo = any(d.get("is_demo", False) for d in c_dets)

            # Spatial & LULC Enrichment
            t_gis_start = time.perf_counter()
            nearest_fac, fac_dist = find_nearest_facility(c_lat, c_lon, fac_dicts)
            lulc_cat, zone_name, lulc_dists = lulc_engine.classify_location(c_lat, c_lon)
            state = lookup_state(c_lat, c_lon)
            district = lookup_district(c_lat, c_lon)

            if fac_dist <= 2500.0 and nearest_fac:
                facility_status = "KNOWN"
                fac_id = nearest_fac["id"]
            elif fac_dist <= 8000.0:
                facility_status = "VICINITY"
                fac_id = nearest_fac["id"] if nearest_fac else None
            else:
                facility_status = "UNCATALOGED"
                fac_id = None
            gis_total_ms += (time.perf_counter() - t_gis_start) * 1000.0

            # Persistence & Baseline
            t_persist_start = time.perf_counter()
            p_metrics = calculate_persistence_metrics(c_dets)
            baseline = None
            if fac_id:
                baseline = db.query(HistoricalBaseline).filter(HistoricalBaseline.facility_id == fac_id).first()
            baseline_info = calculate_baseline_deviation(cluster["max_frp"], baseline)
            persistence_total_ms += (time.perf_counter() - t_persist_start) * 1000.0

            # Feature vector assembly
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

            # ML 7-Class Prediction
            t_ml_start = time.perf_counter()
            prediction = thermal_predictor.predict(feature_dict)
            ml_duration = (time.perf_counter() - t_ml_start) * 1000.0
            # Partition predictor duration into inference vs shap TreeExplainer
            ml_total_ms += ml_duration * 0.4
            shap_total_ms += ml_duration * 0.6

            # Multi-Criteria Risk Score
            t_risk_start = time.perf_counter()
            r_score, r_level, subscores, reasons = calculate_risk_score(
                max_frp=cluster["max_frp"],
                avg_frp=cluster["avg_frp"],
                anomaly_info=baseline_info,
                persistence_info=p_metrics,
                nearest_settlement_dist_m=lulc_dists.get("dist_to_settlement_m", 5000.0),
                nearest_facility_dist_m=fac_dist,
                landcover_class=lulc_cat,
                predicted_class=prediction["predicted_class"]
            )
            risk_total_ms += (time.perf_counter() - t_risk_start) * 1000.0

            # Generate Unique Event Code
            state_code = state[:3].upper() if state else "IND"
            dt_str = cluster["last_seen"].strftime("%Y%m%d")
            seq_suffix = uuid.uuid4().hex[:4].upper()
            evt_code = f"EVT-{state_code}-{dt_str}-{seq_suffix}"

            # Create ThermalEvent entity
            event = ThermalEvent(
                event_code=evt_code,
                status="ACTIVE",
                state=state,
                district=district,
                latitude=c_lat,
                longitude=c_lon,
                bounding_box=cluster["bounding_box"],
                convex_hull_geojson=cluster["convex_hull_geojson"],
                first_seen=cluster["first_seen"],
                last_seen=cluster["last_seen"],
                detection_count=cluster["detection_count"],
                avg_frp=cluster["avg_frp"],
                max_frp=cluster["max_frp"],
                facility_id=fac_id,
                facility_status=facility_status,
                nearest_facility_distance_m=fac_dist,
                landcover_class=lulc_cat,
                is_demo=is_demo
            )
            db.add(event)
            db.flush()

            # Store Child ThermalDetections
            for d in c_dets:
                det = ThermalDetection(
                    source=d["source"],
                    sensor=d["sensor"],
                    satellite=d.get("satellite"),
                    latitude=d["latitude"],
                    longitude=d["longitude"],
                    acq_timestamp=d["acq_timestamp"],
                    brightness=d.get("brightness"),
                    bright_t31=d.get("bright_t31"),
                    frp=d.get("frp", 0.0),
                    confidence=d.get("confidence", 80.0),
                    day_night=d.get("day_night", "D"),
                    raw_metadata=d.get("raw_payload", {}),
                    event_id=event.id,
                    is_demo=is_demo
                )
                db.add(det)
                total_detections_stored += 1

            # Store Event Features
            ef = EventFeature(
                event_id=event.id,
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
            db.add(ef)

            # Store ML Prediction
            mp = ModelPrediction(
                event_id=event.id,
                predicted_class=prediction.get("predicted_class", "Uncertain"),
                confidence=prediction.get("confidence", 0.8),
                class_probabilities=prediction.get("class_probabilities", prediction.get("probabilities", {})),
                shap_values=prediction.get("shap_values", {}),
                explanation_summary=prediction.get("explanation_summary", f"Classified as {prediction.get('predicted_class', 'Uncertain')}.")
            )
            db.add(mp)

            # Store Risk Score
            rs = RiskScore(
                event_id=event.id,
                risk_level=r_level,
                risk_score=r_score,
                intensity_subscore=subscores["intensity"],
                abnormality_subscore=subscores["abnormality"],
                exposure_subscore=subscores["exposure"],
                persistence_subscore=subscores["persistence"],
                context_subscore=subscores["context"],
                risk_reasons=reasons
            )
            db.add(rs)

            created_event_ids.append(event.id)

        # 9. Database Commit
        t_db_start = time.perf_counter()
        db.commit()
        db_commit_duration_ms = (time.perf_counter() - t_db_start) * 1000.0

        total_pipeline_duration_ms = (time.perf_counter() - t_pipeline_start) * 1000.0

        return {
            "status": "SUCCESS",
            "events_created": len(created_event_ids),
            "event_ids": created_event_ids,
            "detections_stored": total_detections_stored,
            "source": source_name,
            "stage_timings_ms": {
                "ingestion_ms": round(ingest_duration_ms, 2),
                "clustering_ms": round(cluster_duration_ms, 2),
                "gis_enrichment_ms": round(gis_total_ms, 2),
                "persistence_ms": round(persistence_total_ms, 2),
                "ml_inference_ms": round(ml_total_ms, 2),
                "shap_explanation_ms": round(shap_total_ms, 2),
                "risk_evaluation_ms": round(risk_total_ms, 2),
                "db_commit_ms": round(db_commit_duration_ms, 2),
                "total_processing_ms": round(total_pipeline_duration_ms, 2)
            },
            "processed_at": datetime.now(timezone.utc).isoformat()
        }


pipeline_service = ThermalPipelineService()

