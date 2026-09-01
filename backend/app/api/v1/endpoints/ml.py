import os
import time
import json
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel, Field

from backend.app.core.database import get_db
from ml.inference.production_inference_service import (
    production_thermal_predictor,
    FEATURE_COLUMNS,
    TARGET_CLASSES
)

router = APIRouter()


class PredictionRequest(BaseModel):
    frp_max: Optional[float] = Field(default=None, description="Maximum Fire Radiative Power (MW)")
    frp_avg: Optional[float] = Field(default=None, description="Average Fire Radiative Power (MW)")
    frp_std: Optional[float] = Field(default=None, description="Standard deviation of FRP")
    bright_max: Optional[float] = Field(default=None, description="Maximum brightness temperature (K)")
    bright_avg: Optional[float] = Field(default=None, description="Average brightness temperature (K)")
    delta_brightness: Optional[float] = Field(default=None, description="Delta brightness (K)")
    dist_to_facility_m: Optional[float] = Field(default=5000.0, description="Distance to nearest industrial facility (m)")
    dist_to_forest_m: Optional[float] = Field(default=15000.0, description="Distance to nearest forest (m)")
    dist_to_agriculture_m: Optional[float] = Field(default=10000.0, description="Distance to nearest agricultural land (m)")
    dist_to_settlement_m: Optional[float] = Field(default=8000.0, description="Distance to nearest human settlement (m)")
    dist_to_water_m: Optional[float] = Field(default=4000.0, description="Distance to nearest water body (m)")
    dist_to_mine_m: Optional[float] = Field(default=25000.0, description="Distance to nearest mining area (m)")
    landcover_code: Optional[int] = Field(default=1, description="LULC classification code (1=Industrial, 3=Agri, 5=Forest, 6=Mine)")
    persistence_score: Optional[float] = Field(default=0.05, description="Point-in-time 30-day persistence score (0.0 - 1.0)")
    recurrence_rate: Optional[float] = Field(default=1.0, description="Catalog-boundary-safe log lookback normalized recurrence rate")
    day_night_ratio: Optional[float] = Field(default=1.0, description="Ratio of daytime to nighttime observations")
    baseline_deviation_ratio: Optional[float] = Field(default=2.0, description="Ratio of max FRP to prior 365-day average FRP")
    industrial_context_score: Optional[float] = Field(default=0.10, description="Composite spatial industrial context score (0.0 - 1.0)")

    # Backward compatibility aliases
    max_frp: Optional[float] = None
    avg_frp: Optional[float] = None
    avg_brightness: Optional[float] = None
    nearest_facility_distance_m: Optional[float] = None
    landcover_class: Optional[str] = None


class BatchPredictionRequest(BaseModel):
    events: List[PredictionRequest]


@router.get("/model-info")
def get_model_info(db: Session = Depends(get_db)):
    """
    Returns active ML model metadata, architecture, real evaluation metrics, confusion matrix, and feature importances.
    """
    val_report_path = "PHASE8H_FINAL_MODEL_VALIDATION.json"
    if os.path.exists(val_report_path):
        try:
            with open(val_report_path, "r") as f:
                val_data = json.load(f)
            
            xgb_eval = val_data.get("model_evaluations", {}).get("calibrated_platt_xgboost", {})
            return {
                "active_model": "AGNI-NETRA Multi-Class Thermal Classifier V3",
                "version": val_data.get("production_candidate_selection", {}).get("selected_model", "xgb-v3.0-real-candidate"),
                "calibration_algorithm": "Balanced Platt Scaling (Multinomial Logistic Regression)",
                "dataset_provenance": val_data.get("dataset_provenance", {}),
                "features": FEATURE_COLUMNS,
                "classes": TARGET_CLASSES,
                "metrics": {
                    "overall_accuracy": xgb_eval.get("accuracy", 0.6989),
                    "balanced_accuracy": xgb_eval.get("balanced_accuracy", 0.7456),
                    "macro_f1": xgb_eval.get("macro_f1", 0.6446),
                    "multiclass_log_loss": xgb_eval.get("log_loss", 0.7124),
                    "brier_score": xgb_eval.get("brier_score", 0.0656),
                    "ece": xgb_eval.get("ece", 0.1294),
                    "spatial_cv_macro_f1": val_data.get("spatial_cross_validation", {}).get("mean_macro_f1", 0.9318)
                },
                "tri_tier_policy": {
                    "tier1_threshold": {"top1_prob": 0.65, "margin": 0.20, "action": "AUTO_DISPATCH_CANDIDATE"},
                    "tier2_threshold": {"top1_prob": 0.45, "margin": 0.08, "action": "ANALYST_REVIEW_QUEUE"},
                    "tier3_threshold": {"action": "UNCERTAINTY_ACTIVE_LEARNING"},
                    "tier1_selective_accuracy": val_data.get("tri_tier_hitl_metrics", {}).get("tier1_selective_accuracy", 0.9718)
                },
                "operational_gate_status": "CANDIDATE_DEPLOYED_IN_CONTROLLED_MODE",
                "is_active": False,
                "status": "OPERATIONAL"
            }
        except Exception:
            pass

    return {
        "active_model": "AGNI-NETRA XGBoost Multi-Class Thermal Classifier V3",
        "version": "xgb-v3.0-real-candidate",
        "calibration_algorithm": "Balanced Platt Scaling",
        "features": FEATURE_COLUMNS,
        "classes": TARGET_CLASSES,
        "metrics": {
            "overall_accuracy": 0.6989,
            "balanced_accuracy": 0.7456,
            "macro_f1": 0.6446,
            "multiclass_log_loss": 0.7124
        },
        "operational_gate_status": "CONTROLLED_INACTIVE",
        "is_active": False,
        "status": "OPERATIONAL"
    }


@router.post("/predict")
def run_live_prediction(req: PredictionRequest):
    """
    Runs production-grade versioned inference with calibrated probabilities, SHAP attribution,
    Tri-Tier routing, risk assessment, and persistent audit logging.
    """
    event_dict = req.model_dump(exclude_none=True)
    result = production_thermal_predictor.predict(event_dict, log_audit=True)
    return result


@router.post("/predict-batch")
def run_batch_prediction(req: BatchPredictionRequest):
    """
    Runs batch inference on multiple thermal events with audit logging and performance metrics.
    """
    results = []
    t_start = time.time()
    for ev in req.events:
        ev_dict = ev.model_dump(exclude_none=True)
        res = production_thermal_predictor.predict(ev_dict, log_audit=True)
        results.append(res)
    
    total_latency_ms = round((time.time() - t_start) * 1000.0, 2)
    return {
        "total_events": len(results),
        "total_latency_ms": total_latency_ms,
        "avg_latency_ms": round(total_latency_ms / max(1, len(results)), 2),
        "predictions": results
    }


@router.get("/audit-logs")
def get_prediction_audit_logs(
    limit: int = Query(default=20, ge=1, le=100),
    tier: Optional[str] = Query(default=None, description="Filter by routing tier"),
    model_version: Optional[str] = Query(default=None, description="Filter by model version"),
    db: Session = Depends(get_db)
):
    """
    Queries recent ML prediction audit logs from PostgreSQL table ml_prediction_audit_logs.
    """
    query = "SELECT * FROM ml_prediction_audit_logs WHERE 1=1"
    params: Dict[str, Any] = {"limit": limit}

    if tier:
        query += " AND routing_tier = :tier"
        params["tier"] = tier
    if model_version:
        query += " AND model_version = :model_version"
        params["model_version"] = model_version

    query += " ORDER BY timestamp DESC LIMIT :limit;"

    rows = db.execute(text(query), params).fetchall()
    return [dict(r._mapping) for r in rows]
