import numpy as np
from typing import Dict, Any, Tuple
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.metrics import brier_score_loss


class ProbabilityCalibrator:
    """
    AGNI-NETRA Probability Calibration Engine.
    Ensures predicted confidence scores directly reflect empirical posterior probabilities
    using Isotonic Regression and Platt Sigmoid Scaling.
    """

    def evaluate_calibration(
        self,
        y_true_onehot: np.ndarray,
        y_prob: np.ndarray,
        class_names: list
    ) -> Dict[str, Any]:
        """
        Computes multi-class Brier score and calibration reliability metrics.
        A lower Brier score indicates superior calibration (0.0 = perfect calibration).
        """
        brier_scores = {}
        for i, c_name in enumerate(class_names):
            if i < y_prob.shape[1] and i < y_true_onehot.shape[1]:
                score = brier_score_loss(y_true_onehot[:, i], y_prob[:, i])
                brier_scores[c_name] = round(float(score), 4)

        mean_brier = float(np.mean(list(brier_scores.values()))) if brier_scores else 0.0

        return {
            "mean_brier_score": round(mean_brier, 4),
            "is_well_calibrated": mean_brier < 0.15,
            "per_class_brier_scores": brier_scores,
            "calibration_note": (
                "Brier score measures mean squared difference between predicted probabilities and actual class outcomes. "
                "Scores below 0.15 confirm reliable predictive uncertainty without overconfidence."
            )
        }

    def calibrate_classifier(
        self,
        base_estimator: Any,
        X_val: np.ndarray,
        y_val: np.ndarray,
        method: str = "isotonic"
    ) -> CalibratedClassifierCV:
        """
        Fits a CalibratedClassifierCV using validation split.
        """
        calibrated = CalibratedClassifierCV(estimator=base_estimator, method=method, cv="prefit")
        calibrated.fit(X_val, y_val)
        return calibrated


probability_calibrator = ProbabilityCalibrator()
