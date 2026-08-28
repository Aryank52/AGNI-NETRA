import numpy as np
from typing import Dict, Any, List
from sklearn.ensemble import IsolationForest


class AnomalyDetectionEngine:
    """
    Dual-method Anomaly Detection:
    1. Statistical Baseline Deviation (Z-score & Deviation Ratio)
    2. Unsupervised Isolation Forest for multivariate behavioral anomalies
    """

    def __init__(self):
        # Initialize standard pre-configured Isolation Forest
        self.iso_forest = IsolationForest(
            n_estimators=100,
            contamination=0.1,
            random_state=42
        )
        # Synthetic baseline fit for quick multivariate outlier detection
        sample_normal_vectors = np.array([
            [25.0, 45.0, 10.0, 0.8, 4.5],
            [15.0, 30.0, 5.0, 1.2, 5.0],
            [50.0, 80.0, 20.0, 0.9, 6.0],
            [10.0, 20.0, 3.0, 0.5, 3.0],
            [40.0, 70.0, 15.0, 1.0, 5.5],
            [80.0, 120.0, 25.0, 1.1, 7.0],
            [30.0, 50.0, 8.0, 0.7, 4.0]
        ])
        self.iso_forest.fit(sample_normal_vectors)

    def evaluate_anomaly(
        self,
        event_features: Dict[str, Any],
        baseline_stats: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Evaluates whether a thermal event exhibits anomalous intensity or behavior.
        """
        avg_frp = float(event_features.get("frp_avg", 0.0))
        max_frp = float(event_features.get("frp_max", 0.0))
        frp_std = float(event_features.get("frp_std", 0.0))
        dn_ratio = float(event_features.get("day_night_ratio", 0.0))
        p_score = float(event_features.get("persistence_score", 0.0))

        # 1. Statistical Baseline Check
        stat_anomaly = False
        z_score = 0.0
        deviation_ratio = 1.0
        if baseline_stats and baseline_stats.get("mean_frp", 0.0) > 0:
            mean = baseline_stats["mean_frp"]
            std = baseline_stats.get("std_frp") or (mean * 0.35)
            z_score = round((avg_frp - mean) / max(1.0, std), 2)
            deviation_ratio = round(avg_frp / max(1.0, mean), 2)
            if z_score >= 2.0 or deviation_ratio >= 2.0:
                stat_anomaly = True

        # 2. Multivariate Isolation Forest Evaluation
        feature_vec = np.array([[avg_frp, max_frp, frp_std, dn_ratio, p_score]])
        iso_pred = self.iso_forest.predict(feature_vec)[0]  # -1 for anomaly, 1 for normal
        iso_anomaly_score = -float(self.iso_forest.score_samples(feature_vec)[0])  # Higher = more anomalous
        
        is_behavioral_anomaly = (iso_pred == -1 or iso_anomaly_score > 0.65)
        is_overall_anomaly = stat_anomaly or is_behavioral_anomaly

        if stat_anomaly and is_behavioral_anomaly:
            severity = "CRITICAL_ANOMALY"
            reason = f"Combined critical baseline deviation (+{z_score}σ) and abnormal multivariate signature."
        elif stat_anomaly:
            severity = "BASELINE_DEVIATION"
            reason = f"Significant intensity spike compared to historical baseline ({deviation_ratio}x normal)."
        elif is_behavioral_anomaly:
            severity = "BEHAVIORAL_ANOMALY"
            reason = "Multivariate emission signature deviates from typical industrial patterns."
        else:
            severity = "NORMAL_BEHAVIOR"
            reason = "Thermal behavior aligns with expected historical and spatial baselines."

        return {
            "is_anomaly": is_overall_anomaly,
            "anomaly_type": severity,
            "z_score": z_score,
            "deviation_ratio": deviation_ratio,
            "isolation_forest_score": round(iso_anomaly_score, 3),
            "explanation": reason
        }


anomaly_engine = AnomalyDetectionEngine()
