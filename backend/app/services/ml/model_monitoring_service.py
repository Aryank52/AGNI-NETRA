"""
AGNI-NETRA — OPERATIONAL MODEL MONITORING & DRIFT DETECTION SERVICE (WP5)
Provides streaming and batch feature drift (PSI, KS statistic), prediction distribution drift,
confidence decay tracking, and operational drift alerting without automated model activation.
"""

import os
import sys
import numpy as np
import pandas as pd
from enum import Enum
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from scipy import stats
from sqlalchemy.orm import Session
from sqlalchemy import text

WORKSPACE_DIR = r"E:\PROJECTS\AGNI-NETRA"
if WORKSPACE_DIR not in sys.path:
    sys.path.insert(0, WORKSPACE_DIR)

from backend.app.core.config import settings

FEATURE_COLUMNS = [
    "frp_max", "frp_avg", "frp_std",
    "bright_max", "bright_avg", "delta_brightness",
    "dist_to_facility_m", "dist_to_forest_m", "dist_to_agriculture_m",
    "dist_to_settlement_m", "dist_to_water_m", "dist_to_mine_m",
    "landcover_code", "persistence_score", "recurrence_rate",
    "day_night_ratio", "baseline_deviation_ratio", "industrial_context_score"
]


class DriftAlertLevel(str, Enum):
    HEALTHY = "HEALTHY"                     # PSI < 0.10
    WATCH = "WATCH"                         # 0.10 <= PSI < 0.20
    DRIFT_DETECTED = "DRIFT_DETECTED"       # 0.20 <= PSI < 0.25
    SEVERE_DRIFT = "SEVERE_DRIFT"           # PSI >= 0.25


class ModelMonitoringService:
    """
    Evaluates statistical drift on production telemetry and prediction streams.
    Adheres strictly to the safety invariant: Drift emits operational telemetry
    and warnings, but NEVER triggers automatic model retraining or promotion.
    """

    @staticmethod
    def compute_psi(baseline: np.ndarray, current: np.ndarray, num_bins: int = 10) -> float:
        """
        Calculates Population Stability Index (PSI) with epsilon smoothing.
        PSI = sum((Actual% - Expected%) * ln(Actual% / Expected%))
        """
        baseline = baseline[~np.isnan(baseline)]
        current = current[~np.isnan(current)]
        
        if len(baseline) == 0 or len(current) == 0:
            return 0.0

        # Uniform percentiles based on baseline
        percentiles = np.linspace(0, 100, num_bins + 1)
        bins = np.percentile(baseline, percentiles)
        bins = np.unique(bins)
        
        if len(bins) < 2:
            return 0.0

        bins[0] = -np.inf
        bins[-1] = np.inf

        base_counts, _ = np.histogram(baseline, bins=bins)
        curr_counts, _ = np.histogram(current, bins=bins)

        eps = 1e-4
        base_pct = np.maximum(base_counts / max(1, len(baseline)), eps)
        curr_pct = np.maximum(curr_counts / max(1, len(current)), eps)

        base_pct /= np.sum(base_pct)
        curr_pct /= np.sum(curr_pct)

        psi_val = np.sum((curr_pct - base_pct) * np.log(curr_pct / base_pct))
        return float(np.round(max(0.0, psi_val), 4))

    @staticmethod
    def compute_ks_test(baseline: np.ndarray, current: np.ndarray) -> Tuple[float, float]:
        """Calculates two-sample Kolmogorov-Smirnov statistic and p-value."""
        baseline = baseline[~np.isnan(baseline)]
        current = current[~np.isnan(current)]
        if len(baseline) < 2 or len(current) < 2:
            return 0.0, 1.0
        res = stats.ks_2samp(baseline, current)
        return float(np.round(res.statistic, 4)), float(np.round(res.pvalue, 6))

    def evaluate_drift_level(self, psi_value: float) -> DriftAlertLevel:
        """Categorizes PSI into standard operational alert tiers."""
        if psi_value < 0.10:
            return DriftAlertLevel.HEALTHY
        elif psi_value < 0.20:
            return DriftAlertLevel.WATCH
        elif psi_value < 0.25:
            return DriftAlertLevel.DRIFT_DETECTED
        else:
            return DriftAlertLevel.SEVERE_DRIFT

    def compute_feature_drift_report(
        self,
        baseline_df: pd.DataFrame,
        current_df: pd.DataFrame,
        features: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Computes comprehensive feature-by-feature drift metrics across the 18 standard features.
        """
        feat_list = features or [f for f in FEATURE_COLUMNS if f in baseline_df.columns and f in current_df.columns]
        feature_reports = {}
        max_psi = 0.0
        drifted_features = []

        for feat in feat_list:
            b_vals = baseline_df[feat].values.astype(float)
            c_vals = current_df[feat].values.astype(float)

            psi = self.compute_psi(b_vals, c_vals)
            ks_stat, ks_pval = self.compute_ks_test(b_vals, c_vals)
            level = self.evaluate_drift_level(psi)

            if psi > max_psi:
                max_psi = psi

            if level in [DriftAlertLevel.DRIFT_DETECTED, DriftAlertLevel.SEVERE_DRIFT]:
                drifted_features.append(feat)

            feature_reports[feat] = {
                "psi": psi,
                "ks_statistic": ks_stat,
                "ks_pvalue": ks_pval,
                "status": level.value,
                "baseline_mean": float(np.round(np.nanmean(b_vals), 2)) if len(b_vals) > 0 else 0.0,
                "current_mean": float(np.round(np.nanmean(c_vals), 2)) if len(c_vals) > 0 else 0.0,
                "baseline_std": float(np.round(np.nanstd(b_vals), 2)) if len(b_vals) > 0 else 0.0,
                "current_std": float(np.round(np.nanstd(c_vals), 2)) if len(c_vals) > 0 else 0.0
            }

        overall_status = self.evaluate_drift_level(max_psi)

        return {
            "evaluation_timestamp": datetime.now(timezone.utc).isoformat(),
            "overall_status": overall_status.value,
            "max_psi": round(max_psi, 4),
            "drifted_features_count": len(drifted_features),
            "drifted_features": drifted_features,
            "baseline_samples": len(baseline_df),
            "current_samples": len(current_df),
            "features": feature_reports,
            "governance_note": "Automated retraining is disabled (ENABLE_AUTOMATED_MODEL_ACTIVATION = False). Analyst review required if status is DRIFT_DETECTED."
        }

    def compute_prediction_drift_report(
        self,
        baseline_predictions: List[str],
        current_predictions: List[str],
        baseline_confidences: List[float],
        current_confidences: List[float]
    ) -> Dict[str, Any]:
        """
        Evaluates drift in output class distribution and calibrated confidence.
        """
        all_classes = sorted(list(set(baseline_predictions + current_predictions)))
        n_b = max(1, len(baseline_predictions))
        n_c = max(1, len(current_predictions))

        b_counts = {c: baseline_predictions.count(c) / n_b for c in all_classes}
        c_counts = {c: current_predictions.count(c) / n_c for c in all_classes}

        # Class distribution PSI
        eps = 1e-4
        b_pct = np.array([max(b_counts.get(c, 0.0), eps) for c in all_classes])
        c_pct = np.array([max(c_counts.get(c, 0.0), eps) for c in all_classes])
        b_pct /= np.sum(b_pct)
        c_pct /= np.sum(c_pct)
        class_psi = float(np.round(np.sum((c_pct - b_pct) * np.log(c_pct / b_pct)), 4))

        # Confidence PSI & KS
        conf_b = np.array(baseline_confidences, dtype=float)
        conf_c = np.array(current_confidences, dtype=float)
        conf_psi = self.compute_psi(conf_b, conf_c)
        conf_ks, conf_pval = self.compute_ks_test(conf_b, conf_c)

        return {
            "evaluation_timestamp": datetime.now(timezone.utc).isoformat(),
            "class_distribution_psi": class_psi,
            "class_drift_status": self.evaluate_drift_level(class_psi).value,
            "confidence_psi": conf_psi,
            "confidence_drift_status": self.evaluate_drift_level(conf_psi).value,
            "confidence_ks": conf_ks,
            "confidence_mean_delta": round(float(np.mean(conf_c) - np.mean(conf_b)), 4) if len(conf_c) and len(conf_b) else 0.0,
            "baseline_distribution": {c: round(v, 4) for c, v in b_counts.items()},
            "current_distribution": {c: round(v, 4) for c, v in c_counts.items()}
        }


model_monitoring_service = ModelMonitoringService()
