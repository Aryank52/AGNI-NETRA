"""
AGNI-NETRA — Unified Geospatial & Thermal Ingestion Pipeline Service.
Bridges incoming observations directly into the Proactive Intelligence Event Engine
(AutonomousIntelligenceCore) ensuring all telemetry passes through the complete
8-stage lifecycle with immutable audit persistence and champion v3 inference.
"""

import time
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Union
from sqlalchemy.orm import Session

from backend.app.models.domain import ThermalDetection, ThermalEvent, IndustrialFacility
from data_pipeline.adapters.base import NormalizedThermalObservation
from backend.app.services.autonomous_intelligence_service import autonomous_intelligence_core


class ThermalPipelineService:
    """
    Unified Geospatial & Thermal Ingestion Pipeline Service.
    Orchestrates Proactive Intelligence Event Engine:
    Raw Ingestion -> Geodetic Validation -> Spatiotemporal DBSCAN -> LULC & Facility Fusion
    -> Temporal Baseline -> Champion v3 ML (XGBoost) -> Risk & Priority -> Correlation -> HITL Governance.
    """

    def process_observations(
        self,
        db: Session,
        observations: List[Union[NormalizedThermalObservation, Dict[str, Any]]],
        source_name: str = "NASA FIRMS VIIRS"
    ) -> Dict[str, Any]:
        """
        Processes a batch of normalized thermal observations or telemetry dictionaries
        into stored detections, clustered events, risk assessments, and lifecycle transitions.
        Delegates to AutonomousIntelligenceCore to ensure single-pipeline integrity.
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
                },
                "processed_at": datetime.now(timezone.utc).isoformat()
            }

        raw_detection_dicts: List[Dict[str, Any]] = []
        for obs in observations:
            if isinstance(obs, dict):
                raw_detection_dicts.append(obs)
            else:
                raw_detection_dicts.append({
                    "source_record_id": getattr(obs, "source_record_id", None) or f"rec-{uuid.uuid4().hex[:6]}",
                    "source": getattr(obs, "source", None) or source_name,
                    "sensor": getattr(obs, "sensor", "VIIRS"),
                    "satellite": getattr(obs, "satellite", "NOAA-20"),
                    "latitude": float(getattr(obs, "latitude", 0.0)),
                    "longitude": float(getattr(obs, "longitude", 0.0)),
                    "acq_timestamp": getattr(obs, "acq_timestamp", None) or datetime.now(timezone.utc),
                    "brightness": getattr(obs, "brightness", 320.0),
                    "bright_t31": getattr(obs, "bright_t31", 295.0),
                    "frp": float(getattr(obs, "frp", 0.0)),
                    "confidence": float(getattr(obs, "confidence", 80.0)),
                    "day_night": getattr(obs, "day_night", "D"),
                    "raw_payload": getattr(obs, "metadata", {}) if hasattr(obs, "metadata") else {},
                    "is_demo": getattr(obs, "is_demo", False),
                    "is_simulation": getattr(obs, "is_simulation", False)
                })

        corr_id = f"pipe-{uuid.uuid4().hex[:8]}"
        outcomes = autonomous_intelligence_core.process_observations_autonomous(
            db=db,
            raw_observations=raw_detection_dicts,
            source_name=source_name,
            correlation_id=corr_id
        )

        stage_timings = dict(autonomous_intelligence_core.last_stage_timings)
        detections_stored = autonomous_intelligence_core.last_detections_stored
        processing_id = f"proc-{uuid.uuid4().hex[:8]}"
        created_event_ids = [o.event_id for o in outcomes]
        created_event_codes = [o.event_code for o in outcomes]

        return {
            "status": "SUCCESS",
            "events_created": len(created_event_ids),
            "event_ids": created_event_ids,
            "event_codes": created_event_codes,
            "detections_stored": detections_stored,
            "source": source_name,
            "correlation_id": corr_id,
            "processing_id": processing_id,
            "lifecycle_run_id": corr_id,
            "stage_timings_ms": stage_timings,
            "processed_at": datetime.now(timezone.utc).isoformat()
        }



pipeline_service = ThermalPipelineService()
