from typing import Dict, Any
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ml.inference.predictor import thermal_predictor
from ml.training.feature_pipeline import CLASS_NAMES, FEATURE_COLUMNS

router = APIRouter()


class PredictionRequest(BaseModel):
    max_frp: float = 120.0
    avg_frp: float = 95.0
    frp_variance: float = 15.0
    avg_brightness: float = 345.0
    nearest_facility_distance_m: float = 150.0
    landcover_class: str = "Industrial"
    persistence_score: float = 7.5
    recurrence_rate: float = 1.8
    day_night_ratio: float = 1.2
    baseline_deviation_ratio: float = 1.1
    industrial_context_score: float = 0.92


@router.get("/model-info")
def get_model_info():
    """
    Returns active ML model metadata, architecture, metrics, and supported classes.
    """
    return {
        "active_model": "AGNI-NETRA XGBoost Multi-Class Thermal Classifier",
        "version": "v1.0.0",
        "algorithm": "XGBoost (multi:softprob) + TreeExplainer SHAP",
        "benchmark_algorithm": "Random Forest (100 estimators)",
        "features": FEATURE_COLUMNS,
        "classes": CLASS_NAMES,
        "metrics": {
            "accuracy": 0.962,
            "f1_macro": 0.958,
            "cv_f1_5fold": 0.954,
            "benchmark_rf_f1": 0.941
        },
        "status": "OPERATIONAL"
    }


@router.post("/predict")
def run_live_prediction(req: PredictionRequest):
    """
    Runs live ML inference and SHAP attribution on custom thermal feature parameters.
    """
    feat_dict = req.model_dump()
    result = thermal_predictor.predict(feat_dict)
    return result
