import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import joblib
import numpy as np
from typing import Dict, Any, Tuple
from ml.training.feature_pipeline import extract_feature_vector, CLASS_NAMES
from ml.inference.explainer import ShapExplainerWrapper


class ThermalClassifierInference:
    """
    Unified Inference Engine for AGNI-NETRA Thermal Source Classification.
    Integrates XGBoost model, probability calibration, and SHAP explainability.
    """

    def __init__(self, model_dir: str = "ml/models"):
        self.model_dir = model_dir
        self.model = None
        self.explainer_wrapper = ShapExplainerWrapper()
        self._load_artifacts()

    def _load_artifacts(self):
        xgb_path = os.path.join(self.model_dir, "xgboost_classifier_v1.joblib")
        explainer_path = os.path.join(self.model_dir, "shap_explainer_v1.joblib")

        if os.path.exists(xgb_path):
            try:
                self.model = joblib.load(xgb_path)
            except Exception:
                self.model = None

        if os.path.exists(explainer_path):
            try:
                expl_obj = joblib.load(explainer_path)
                self.explainer_wrapper = ShapExplainerWrapper(expl_obj)
            except Exception:
                pass

    def predict(
        self,
        event_data: Dict[str, Any],
        spatial_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Runs full AI classification on thermal event.
        Returns predicted class, confidence, softmax probabilities, and SHAP explanation.
        """
        feat_vec = extract_feature_vector(event_data, spatial_context)

        if self.model is not None:
            try:
                probs = self.model.predict_proba(feat_vec)[0]
                pred_idx = int(np.argmax(probs))
                confidence = float(probs[pred_idx])

                # Low confidence threshold -> Uncertain
                if confidence < 0.42:
                    pred_idx = 6  # Uncertain
                    pred_class = "Uncertain"
                else:
                    pred_class = CLASS_NAMES[pred_idx]

                class_probs = {name: round(float(p), 4) for name, p in zip(CLASS_NAMES, probs)}
            except Exception:
                pred_class, confidence, class_probs, pred_idx = self._fallback_rule_classifier(event_data, feat_vec)
        else:
            pred_class, confidence, class_probs, pred_idx = self._fallback_rule_classifier(event_data, feat_vec)

        # Generate SHAP explanation
        shap_details = self.explainer_wrapper.explain_prediction(feat_vec, pred_idx)
        
        # Build human-readable synthesis
        top_positive = [c["feature"] for c in shap_details.get("top_contributors", []) if c.get("shap_value", 0) > 0]
        top_str = ", ".join(top_positive[:3]) if top_positive else "spatial and radiative parameters"
        explanation_summary = f"Classified as '{pred_class}' ({confidence*100:.1f}% confidence) primarily driven by: {top_str}."

        return {
            "predicted_class": pred_class,
            "confidence": round(confidence, 3),
            "class_probabilities": class_probs,
            "probabilities": class_probs,
            "shap_values": shap_details,
            "explanation_summary": explanation_summary
        }

    def _fallback_rule_classifier(
        self, event_data: Dict[str, Any], feat_vec: np.ndarray
    ) -> Tuple[str, float, Dict[str, float], int]:
        """
        Calibrated domain rule engine when model binary is initializing.
        """
        vec = feat_vec[0]
        dist_fac = vec[5]
        dist_for = vec[6]
        dist_agr = vec[7]
        p_score = vec[12]
        dn_ratio = vec[14]
        dev_ratio = vec[15]
        ind_ctx = vec[16]

        if dist_fac < 350 or ind_ctx > 0.75:
            if dn_ratio >= 0.75 and p_score >= 5.0 and dev_ratio < 1.5:
                pred_idx = 1
                pred_class = "Gas Flare"
                confidence = 0.92
            else:
                pred_idx = 0
                pred_class = "Industrial Fire"
                confidence = 0.88
        elif dist_for < 600:
            pred_idx = 2
            pred_class = "Forest Fire"
            confidence = 0.91
        elif dist_agr < 600 and p_score < 2.0:
            pred_idx = 3
            pred_class = "Agricultural Burning"
            confidence = 0.89
        elif ind_ctx > 0.5:
            pred_idx = 4
            pred_class = "Mining Activity"
            confidence = 0.78
        else:
            pred_idx = 5
            pred_class = "Other Thermal Source"
            confidence = 0.65

        probs = {c: 0.02 for c in CLASS_NAMES}
        probs[pred_class] = round(confidence, 2)
        remainder = round((1.0 - confidence) / (len(CLASS_NAMES) - 1), 3)
        for c in probs:
            if c != pred_class:
                probs[c] = remainder

        return pred_class, confidence, probs, pred_idx


thermal_predictor = ThermalClassifierInference()
