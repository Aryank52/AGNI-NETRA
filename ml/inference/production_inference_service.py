"""
AGNI-NETRA — PRODUCTION ML INFERENCE SERVICE (PHASE 9)
Versioned, Calibrated, Explainable, and Audited Thermal Classifier

Features:
1. Dynamic model loading for `xgb-v3.0-real-candidate` champion and `rf-v3.0-real-candidate` baseline.
2. Balanced Platt calibration for well-calibrated probabilities across 6 target classes.
3. TreeExplainer SHAP local feature attribution waterfall for interpretability.
4. Tri-Tier Human-in-the-Loop (HITL) operational routing policy.
5. Multi-dimensional risk score integration (0-100 scale, Critical/High/Medium/Low).
6. Input feature snapshotting and persistent PostgreSQL audit logging.
7. Graceful degradation and fallback handling with zero service disruption.
8. Controlled production invariant: Automated live dispatch is held in candidate state (is_operational_dispatch = FALSE).
"""

import os
import sys
import time
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import joblib
from sqlalchemy import text

WORKSPACE_DIR = r"E:\PROJECTS\AGNI-NETRA"
if WORKSPACE_DIR not in sys.path:
    sys.path.insert(0, WORKSPACE_DIR)

from backend.app.core.database import engine

FEATURE_COLUMNS = [
    "frp_max", "frp_avg", "frp_std",
    "bright_max", "bright_avg", "delta_brightness",
    "dist_to_facility_m", "dist_to_forest_m", "dist_to_agriculture_m",
    "dist_to_settlement_m", "dist_to_water_m", "dist_to_mine_m",
    "landcover_code", "persistence_score", "recurrence_rate",
    "day_night_ratio", "baseline_deviation_ratio", "industrial_context_score"
]

TARGET_CLASSES = [
    "Industrial Fire",
    "Gas Flare",
    "Forest Fire",
    "Agricultural Burning",
    "Mining Activity",
    "Other Thermal Source"
]

LANDCOVER_MAPPING = {
    "Industrial": 1, "Settlement": 2, "Agriculture": 3,
    "Water": 4, "Forest": 5, "Mining": 6, "Barren": 7, "Other": 8
}


class ProductionThermalInferenceService:
    """
    Production-grade thermal source classifier for the AGNI-NETRA operational pipeline.
    """

    def __init__(self, model_dir: str = os.path.join(WORKSPACE_DIR, "ml", "models")):
        self.model_dir = model_dir
        self.model_version = "xgb-v3.0-real-candidate"
        self.calibrator_version = "balanced-platt-v3.0"
        self.dataset_lineage = "v3.2-real-final"
        
        self.xgb_model = None
        self.platt_calibrator = None
        self.rf_model = None
        self.shap_explainer = None
        self.is_loaded = False
        
        self.load_artifacts()

    def load_artifacts(self) -> bool:
        """Loads champion XGBoost, Platt calibrator, RF baseline, and SHAP explainer."""
        try:
            xgb_path = os.path.join(self.model_dir, "xgb_v3_real_candidate.joblib")
            platt_path = os.path.join(self.model_dir, "xgb_v3_calibrated_candidate.joblib")
            rf_path = os.path.join(self.model_dir, "rf_v3_real_candidate.joblib")
            shap_path = os.path.join(self.model_dir, "shap_explainer_v3.joblib")

            if os.path.exists(xgb_path):
                self.xgb_model = joblib.load(xgb_path)
            if os.path.exists(platt_path):
                self.platt_calibrator = joblib.load(platt_path)
            if os.path.exists(rf_path):
                self.rf_model = joblib.load(rf_path)
            if os.path.exists(shap_path):
                self.shap_explainer = joblib.load(shap_path)

            self.is_loaded = (self.xgb_model is not None and self.platt_calibrator is not None)
            return self.is_loaded
        except Exception as e:
            print(f"[ProductionInferenceService] Warning: Failed to load models: {e}")
            self.is_loaded = False
            return False

    def extract_feature_vector(
        self,
        event_data: Dict[str, Any],
        spatial_context: Optional[Dict[str, Any]] = None
    ) -> Tuple[np.ndarray, Dict[str, float]]:
        """
        Extracts and normalizes the standard 18-element feature vector from raw event data.
        """
        ctx = spatial_context or {}

        def safe_float(val: Any, default: float) -> float:
            try:
                if val is None or val == "":
                    return default
                return float(val)
            except (ValueError, TypeError):
                return default
        
        frp_max = safe_float(event_data.get("frp_max", event_data.get("max_frp", event_data.get("frp"))), 25.0)
        frp_avg = safe_float(event_data.get("frp_avg", event_data.get("avg_frp")), frp_max * 0.85)
        frp_std = safe_float(event_data.get("frp_std", event_data.get("frp_variance")), frp_avg * 0.20)

        b_max = safe_float(event_data.get("bright_max", event_data.get("max_brightness")), 335.0)
        b_avg = safe_float(event_data.get("bright_avg", event_data.get("avg_brightness")), b_max * 0.96)
        delta_b = safe_float(event_data.get("delta_brightness"), b_max - b_avg)

        dist_fac = safe_float(ctx.get("dist_to_facility_m", event_data.get("dist_to_facility_m", event_data.get("nearest_facility_distance_m"))), 5000.0)
        dist_for = safe_float(ctx.get("dist_to_forest_m", event_data.get("dist_to_forest_m")), 15000.0)
        dist_agr = safe_float(ctx.get("dist_to_agriculture_m", event_data.get("dist_to_agriculture_m")), 10000.0)
        dist_set = safe_float(ctx.get("dist_to_settlement_m", event_data.get("dist_to_settlement_m")), 8000.0)
        dist_wat = safe_float(ctx.get("dist_to_water_m", event_data.get("dist_to_water_m")), 4000.0)
        dist_min = safe_float(ctx.get("dist_to_mine_m", event_data.get("dist_to_mine_m")), 25000.0)

        lc_val = ctx.get("landcover_code", event_data.get("landcover_code"))
        if lc_val is None:
            lc_str = str(ctx.get("landcover_class", event_data.get("landcover_class", "Other")))
            lc_val = LANDCOVER_MAPPING.get(lc_str, 8)
        lc_code = safe_float(lc_val, 8.0)

        p_score = safe_float(event_data.get("persistence_score"), 0.05)
        
        # Lookback-normalized recurrence
        raw_rec = safe_float(event_data.get("recurrence_rate"), 1.0)
        avail_days = safe_float(event_data.get("available_history_days"), 365.0)
        if avail_days > 0 and raw_rec > 0 and raw_rec > 15.0:  # If raw count was passed
            rec_rate = float(np.round(np.log1p(raw_rec * (365.0 / avail_days)), 3))
        else:
            rec_rate = raw_rec

        dn_ratio = safe_float(event_data.get("day_night_ratio"), 1.0)
        dev_ratio = safe_float(event_data.get("baseline_deviation_ratio"), 2.0)
        ind_ctx = safe_float(ctx.get("industrial_context_score", event_data.get("industrial_context_score")), 0.10)

        feat_dict = {
            "frp_max": frp_max, "frp_avg": frp_avg, "frp_std": frp_std,
            "bright_max": b_max, "bright_avg": b_avg, "delta_brightness": delta_b,
            "dist_to_facility_m": dist_fac, "dist_to_forest_m": dist_for, "dist_to_agriculture_m": dist_agr,
            "dist_to_settlement_m": dist_set, "dist_to_water_m": dist_wat, "dist_to_mine_m": dist_min,
            "landcover_code": lc_code, "persistence_score": p_score, "recurrence_rate": rec_rate,
            "day_night_ratio": dn_ratio, "baseline_deviation_ratio": dev_ratio, "industrial_context_score": ind_ctx
        }

        feat_vec = np.array([[feat_dict[col] for col in FEATURE_COLUMNS]], dtype=np.float32)
        return feat_vec, feat_dict

    def calculate_risk_score(
        self,
        features: Dict[str, float],
        predicted_class: str,
        confidence: float
    ) -> Dict[str, Any]:
        """
        Computes multi-criteria operational fire risk score (0-100 scale).
        """
        frp_max = features.get("frp_max", 20.0)
        dist_fac = features.get("dist_to_facility_m", 10000.0)
        dist_for = features.get("dist_to_forest_m", 10000.0)
        dist_set = features.get("dist_to_settlement_m", 10000.0)

        # 1. Thermal Intensity Component (0 - 40 pts)
        frp_score = min(40.0, (frp_max / 250.0) * 40.0)

        # 2. Asset Proximity Hazard (0 - 35 pts)
        prox_score = 0.0
        if dist_fac < 500.0:
            prox_score += 25.0
        elif dist_fac < 2000.0:
            prox_score += 15.0
        
        if dist_set < 1000.0:
            prox_score += 10.0
        elif dist_set < 3000.0:
            prox_score += 5.0
        prox_score = min(35.0, prox_score)

        # 3. Ecological / Context Hazard (0 - 25 pts)
        eco_score = 0.0
        if predicted_class in ["Industrial Fire", "Gas Flare"] and dist_fac < 1000.0:
            eco_score += 20.0
        elif predicted_class == "Forest Fire" and dist_for < 500.0:
            eco_score += 25.0
        elif predicted_class == "Agricultural Burning":
            eco_score += 10.0
        else:
            eco_score += 5.0

        total_risk = round(min(100.0, max(0.0, (frp_score + prox_score + eco_score) * (0.5 + 0.5 * confidence))), 1)

        if total_risk >= 75.0:
            risk_tier = "CRITICAL"
        elif total_risk >= 50.0:
            risk_tier = "HIGH"
        elif total_risk >= 25.0:
            risk_tier = "MEDIUM"
        else:
            risk_tier = "LOW"

        return {
            "risk_score": total_risk,
            "risk_tier": risk_tier,
            "components": {
                "thermal_intensity_score": round(frp_score, 1),
                "asset_proximity_score": round(prox_score, 1),
                "ecological_hazard_score": round(eco_score, 1)
            }
        }

    def determine_tri_tier_routing(
        self,
        top1_prob: float,
        margin: float
    ) -> Tuple[str, str]:
        """
        Evaluates operational Tri-Tier Human-in-the-Loop dispatch routing.
        """
        if top1_prob >= 0.65 and margin >= 0.20:
            return "TIER_1_AUTO_DISPATCH_CANDIDATE", "High statistical confidence and decisive class margin."
        elif top1_prob >= 0.45 and margin >= 0.08:
            return "TIER_2_ANALYST_REVIEW_QUEUE", "Moderate confidence or competitive class boundary requiring human verification."
        else:
            return "TIER_3_UNCERTAINTY_QUEUE", "Low prediction margin or high entropy; queued for active learning."

    def compute_shap_explanation(
        self,
        feat_vec: np.ndarray,
        pred_idx: int
    ) -> Dict[str, Any]:
        """
        Extracts SHAP feature attributions for the predicted class.
        """
        if self.shap_explainer is None:
            return {"top_contributors": [], "method": "HEURISTIC_FALLBACK"}
        
        try:
            shap_raw = self.shap_explainer.shap_values(feat_vec)
            if isinstance(shap_raw, list):
                class_shap = shap_raw[pred_idx][0]
            elif shap_raw.ndim == 3:
                class_shap = shap_raw[0, :, pred_idx]
            else:
                class_shap = shap_raw[0]

            contributors = []
            for i, feat_name in enumerate(FEATURE_COLUMNS):
                val = float(feat_vec[0, i])
                s_val = float(class_shap[i])
                contributors.append({
                    "feature": feat_name,
                    "value": round(val, 3),
                    "shap_value": round(s_val, 4),
                    "impact": "POSITIVE" if s_val > 0 else "NEGATIVE"
                })

            contributors.sort(key=lambda x: abs(x["shap_value"]), reverse=True)
            return {
                "top_contributors": contributors[:6],
                "base_value": 0.0,
                "method": "TREE_SHAP_V3"
            }
        except Exception as e:
            return {"top_contributors": [], "method": f"SHAP_ERROR: {str(e)}"}

    def predict(
        self,
        event_data: Dict[str, Any],
        spatial_context: Optional[Dict[str, Any]] = None,
        log_audit: bool = True
    ) -> Dict[str, Any]:
        """
        Executes unified, calibrated, explainable inference on thermal event parameters.
        """
        t_start = time.time()
        prediction_id = str(uuid.uuid4())
        feat_vec, feat_dict = self.extract_feature_vector(event_data, spatial_context)
        fallback_invoked = False
        error_msg = None

        if self.is_loaded and self.xgb_model is not None and self.platt_calibrator is not None:
            try:
                raw_probs = self.xgb_model.predict_proba(feat_vec)[0]
                cal_probs = self.platt_calibrator.predict_proba(raw_probs.reshape(1, -1))[0]
            except Exception as e:
                error_msg = str(e)
                fallback_invoked = True
                cal_probs = self._fallback_probabilities(feat_dict)
                raw_probs = cal_probs
        elif self.rf_model is not None:
            try:
                raw_probs = self.rf_model.predict_proba(feat_vec)[0]
                cal_probs = raw_probs
            except Exception as e:
                error_msg = str(e)
                fallback_invoked = True
                cal_probs = self._fallback_probabilities(feat_dict)
                raw_probs = cal_probs
        else:
            fallback_invoked = True
            cal_probs = self._fallback_probabilities(feat_dict)
            raw_probs = cal_probs

        sorted_indices = np.argsort(cal_probs)[::-1]
        top1_idx = int(sorted_indices[0])
        top2_idx = int(sorted_indices[1])
        top1_prob = float(cal_probs[top1_idx])
        top2_prob = float(cal_probs[top2_idx])
        margin = float(top1_prob - top2_prob)

        predicted_class = TARGET_CLASSES[top1_idx]
        class_probabilities = {TARGET_CLASSES[i]: round(float(cal_probs[i]), 4) for i in range(len(TARGET_CLASSES))}
        raw_probabilities = {TARGET_CLASSES[i]: round(float(raw_probs[i]), 4) for i in range(len(TARGET_CLASSES))}

        # Calculate Normalized Shannon Entropy Uncertainty
        eps = 1e-12
        clipped_p = np.clip(cal_probs, eps, 1.0)
        entropy = -float(np.sum(clipped_p * np.log(clipped_p)))
        max_entropy = np.log(len(TARGET_CLASSES))
        uncertainty = round(float(entropy / max_entropy), 3)

        # Operational Tri-Tier HITL Routing
        routing_tier, routing_reason = self.determine_tri_tier_routing(top1_prob, margin)

        # Risk Score Integration
        risk_info = self.calculate_risk_score(feat_dict, predicted_class, top1_prob)

        # SHAP Feature Attributions
        shap_info = self.compute_shap_explanation(feat_vec, top1_idx)

        elapsed_ms = round((time.time() - t_start) * 1000.0, 2)

        # Construct Human-Readable Explanation Summary
        top_features = [c["feature"] for c in shap_info.get("top_contributors", []) if c.get("shap_value", 0) > 0]
        feat_str = ", ".join(top_features[:3]) if top_features else "spatial and radiative features"
        summary = f"Classified as '{predicted_class}' with {top1_prob*100:.1f}% calibrated confidence (Tier: {routing_tier}, Risk: {risk_info['risk_tier']}), driven by {feat_str}."

        result = {
            "prediction_id": prediction_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "predicted_class": predicted_class,
            "confidence": round(top1_prob, 4),
            "confidence_margin": round(margin, 4),
            "uncertainty": uncertainty,
            "class_probabilities": class_probabilities,
            "raw_probabilities": raw_probabilities,
            "routing_tier": routing_tier,
            "routing_reason": routing_reason,
            "risk_assessment": risk_info,
            "shap_explanation": shap_info,
            "explanation_summary": summary,
            "feature_snapshot": feat_dict,
            "model_lineage": {
                "model_version": self.model_version,
                "calibrator_version": self.calibrator_version,
                "dataset_version": self.dataset_lineage,
                "fallback_invoked": fallback_invoked,
                "error": error_msg
            },
            "operational_dispatch_status": {
                "is_operational_dispatch": False,  # Strict production safety invariant
                "dispatch_candidate": (routing_tier == "TIER_1_AUTO_DISPATCH_CANDIDATE"),
                "gate_status": "CONTROLLED_INACTIVE"
            },
            "latency_ms": elapsed_ms
        }

        if log_audit:
            self.persist_audit_log(result)

        return result

    def _fallback_probabilities(self, features: Dict[str, float]) -> np.ndarray:
        """Heuristic rule-based fallback if ML artifacts are unavailable."""
        dist_fac = features.get("dist_to_facility_m", 5000.0)
        dist_for = features.get("dist_to_forest_m", 15000.0)
        dist_agr = features.get("dist_to_agriculture_m", 10000.0)
        p_score = features.get("persistence_score", 0.05)

        if dist_fac < 400.0 and p_score > 0.40:
            return np.array([0.55, 0.35, 0.02, 0.02, 0.04, 0.02], dtype=np.float32)
        elif dist_for < 1000.0:
            return np.array([0.02, 0.01, 0.85, 0.05, 0.02, 0.05], dtype=np.float32)
        elif dist_agr < 2000.0:
            return np.array([0.02, 0.01, 0.05, 0.82, 0.02, 0.08], dtype=np.float32)
        else:
            return np.array([0.166, 0.166, 0.166, 0.166, 0.166, 0.170], dtype=np.float32)

    def persist_audit_log(self, prediction_result: Dict[str, Any]):
        """Persists the prediction result and feature snapshot into PostgreSQL."""
        try:
            with engine.begin() as conn:
                conn.execute(text("""
                    INSERT INTO ml_prediction_audit_logs (
                        id, prediction_id, timestamp, model_version, dataset_version,
                        predicted_class, confidence, confidence_margin, uncertainty,
                        routing_tier, risk_score, risk_tier, is_operational_dispatch,
                        fallback_invoked, feature_snapshot, class_probabilities,
                        shap_contributors, latency_ms
                    ) VALUES (
                        :id, :prediction_id, :timestamp, :model_version, :dataset_version,
                        :predicted_class, :confidence, :confidence_margin, :uncertainty,
                        :routing_tier, :risk_score, :risk_tier, :is_operational_dispatch,
                        :fallback_invoked, CAST(:feature_snapshot AS jsonb),
                        CAST(:class_probabilities AS jsonb), CAST(:shap_contributors AS jsonb),
                        :latency_ms
                    );
                """), {
                    "id": str(uuid.uuid4()),
                    "prediction_id": prediction_result["prediction_id"],
                    "timestamp": prediction_result["timestamp"],
                    "model_version": prediction_result["model_lineage"]["model_version"],
                    "dataset_version": prediction_result["model_lineage"]["dataset_version"],
                    "predicted_class": prediction_result["predicted_class"],
                    "confidence": prediction_result["confidence"],
                    "confidence_margin": prediction_result["confidence_margin"],
                    "uncertainty": prediction_result["uncertainty"],
                    "routing_tier": prediction_result["routing_tier"],
                    "risk_score": prediction_result["risk_assessment"]["risk_score"],
                    "risk_tier": prediction_result["risk_assessment"]["risk_tier"],
                    "is_operational_dispatch": prediction_result["operational_dispatch_status"]["is_operational_dispatch"],
                    "fallback_invoked": prediction_result["model_lineage"]["fallback_invoked"],
                    "feature_snapshot": json.dumps(prediction_result["feature_snapshot"]),
                    "class_probabilities": json.dumps(prediction_result["class_probabilities"]),
                    "shap_contributors": json.dumps(prediction_result["shap_explanation"].get("top_contributors", [])),
                    "latency_ms": prediction_result["latency_ms"]
                })
        except Exception as e:
            # Audit logging failure should not crash inference
            print(f"[ProductionInferenceService] Audit logging notice: {e}")


# Singleton service instance
production_thermal_predictor = ProductionThermalInferenceService()
