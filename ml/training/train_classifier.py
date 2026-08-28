import os
import sys
import json
import joblib
import numpy as np
import pandas as pd
from typing import Tuple, Dict, Any
from sklearn.model_selection import StratifiedKFold
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.metrics import classification_report, accuracy_score, f1_score, precision_score, recall_score, confusion_matrix
import xgboost as xgb
import shap

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from ml.training.feature_pipeline import FEATURE_COLUMNS, CLASS_NAMES, LANDCOVER_MAPPING


def generate_synthetic_training_data(n_samples: int = 2800) -> Tuple[np.ndarray, np.ndarray, Dict[str, Any]]:
    """
    Generates realistic, physically grounded synthetic training data representing Indian thermal regimes.
    Explicitly documented as an initial labeled calibration set until full operational telemetry is collected.
    """
    np.random.seed(42)
    X = []
    y = []

    samples_per_class = n_samples // len(CLASS_NAMES)

    for c_idx, c_name in enumerate(CLASS_NAMES):
        for _ in range(samples_per_class):
            if c_idx == 0:  # 0: Industrial Fire
                frp_max = float(np.random.uniform(90.0, 380.0))
                frp_avg = frp_max * float(np.random.uniform(0.65, 0.90))
                frp_std = frp_avg * float(np.random.uniform(0.20, 0.40))
                b_avg = float(np.random.uniform(340.0, 420.0))
                b_max = b_avg * float(np.random.uniform(1.05, 1.25))
                delta_b = b_max - b_avg
                dist_fac = float(np.random.exponential(140.0))  # within 500m
                dist_for = float(np.random.uniform(8000.0, 60000.0))
                dist_agr = float(np.random.uniform(5000.0, 35000.0))
                dist_set = float(np.random.uniform(500.0, 8000.0))
                dist_wat = float(np.random.uniform(1000.0, 20000.0))
                dist_min = float(np.random.uniform(5000.0, 50000.0))
                lc_code = 1  # Industrial
                p_score = float(np.random.uniform(3.5, 8.5))
                rec_rate = float(np.random.uniform(0.6, 2.8))
                dn_ratio = float(np.random.uniform(0.7, 1.8))
                dev_ratio = float(np.random.uniform(2.2, 6.5))  # High deviation vs baseline
                ind_ctx = float(np.random.uniform(0.75, 0.99))

            elif c_idx == 1:  # 1: Gas Flare
                frp_max = float(np.random.uniform(35.0, 150.0))
                frp_avg = frp_max * float(np.random.uniform(0.78, 0.96))
                frp_std = frp_avg * float(np.random.uniform(0.08, 0.18))  # Continuous steady output
                b_avg = float(np.random.uniform(330.0, 390.0))
                b_max = b_avg * float(np.random.uniform(1.02, 1.10))
                delta_b = b_max - b_avg
                dist_fac = float(np.random.exponential(75.0))  # At flare stack
                dist_for = float(np.random.uniform(10000.0, 70000.0))
                dist_agr = float(np.random.uniform(8000.0, 45000.0))
                dist_set = float(np.random.uniform(2000.0, 15000.0))
                dist_wat = float(np.random.uniform(500.0, 15000.0))
                dist_min = float(np.random.uniform(10000.0, 60000.0))
                lc_code = 1  # Industrial
                p_score = float(np.random.uniform(7.5, 9.9))  # 24x7 persistent
                rec_rate = float(np.random.uniform(1.5, 4.5))
                dn_ratio = float(np.random.uniform(0.85, 1.45))
                dev_ratio = float(np.random.uniform(0.85, 1.25))  # Steady nominal baseline
                ind_ctx = float(np.random.uniform(0.88, 0.99))

            elif c_idx == 2:  # 2: Forest Fire
                frp_max = float(np.random.uniform(45.0, 290.0))
                frp_avg = frp_max * float(np.random.uniform(0.50, 0.80))
                frp_std = frp_avg * float(np.random.uniform(0.30, 0.55))
                b_avg = float(np.random.uniform(320.0, 410.0))
                b_max = b_avg * float(np.random.uniform(1.10, 1.30))
                delta_b = b_max - b_avg
                dist_fac = float(np.random.uniform(15000.0, 85000.0))
                dist_for = float(np.random.exponential(180.0))  # Inside forest canopy
                dist_agr = float(np.random.uniform(3000.0, 30000.0))
                dist_set = float(np.random.uniform(6000.0, 40000.0))
                dist_wat = float(np.random.uniform(2000.0, 18000.0))
                dist_min = float(np.random.uniform(15000.0, 80000.0))
                lc_code = 5  # Forest
                p_score = float(np.random.uniform(0.4, 2.8))  # Wildfire event
                rec_rate = float(np.random.uniform(0.1, 0.7))
                dn_ratio = float(np.random.uniform(0.05, 0.28))  # Daytime dominant
                dev_ratio = 1.0
                ind_ctx = float(np.random.uniform(0.01, 0.12))

            elif c_idx == 3:  # 3: Agricultural Burning
                frp_max = float(np.random.uniform(12.0, 80.0))
                frp_avg = frp_max * float(np.random.uniform(0.60, 0.85))
                frp_std = frp_avg * float(np.random.uniform(0.18, 0.32))
                b_avg = float(np.random.uniform(315.0, 355.0))
                b_max = b_avg * float(np.random.uniform(1.03, 1.12))
                delta_b = b_max - b_avg
                dist_fac = float(np.random.uniform(8000.0, 50000.0))
                dist_for = float(np.random.uniform(5000.0, 35000.0))
                dist_agr = float(np.random.exponential(90.0))  # Cropland
                dist_set = float(np.random.uniform(800.0, 7000.0))
                dist_wat = float(np.random.uniform(1200.0, 15000.0))
                dist_min = float(np.random.uniform(10000.0, 60000.0))
                lc_code = 4  # Agriculture
                p_score = float(np.random.uniform(0.1, 1.4))  # Stubble clearing
                rec_rate = float(np.random.uniform(0.05, 0.35))
                dn_ratio = float(np.random.uniform(0.0, 0.12))  # Strict afternoon
                dev_ratio = 1.0
                ind_ctx = float(np.random.uniform(0.02, 0.18))

            elif c_idx == 4:  # 4: Mining Activity
                frp_max = float(np.random.uniform(30.0, 120.0))
                frp_avg = frp_max * float(np.random.uniform(0.62, 0.88))
                frp_std = frp_avg * float(np.random.uniform(0.22, 0.38))
                b_avg = float(np.random.uniform(325.0, 380.0))
                b_max = b_avg * float(np.random.uniform(1.05, 1.18))
                delta_b = b_max - b_avg
                dist_fac = float(np.random.uniform(3000.0, 28000.0))
                dist_for = float(np.random.uniform(3000.0, 25000.0))
                dist_agr = float(np.random.uniform(4000.0, 28000.0))
                dist_set = float(np.random.uniform(3000.0, 16000.0))
                dist_wat = float(np.random.uniform(2000.0, 16000.0))
                dist_min = float(np.random.exponential(220.0))  # Inside open pit / coal seam
                lc_code = 2  # Mining / Barren
                p_score = float(np.random.uniform(3.8, 7.8))
                rec_rate = float(np.random.uniform(0.5, 2.0))
                dn_ratio = float(np.random.uniform(0.35, 0.95))
                dev_ratio = float(np.random.uniform(0.9, 1.9))
                ind_ctx = float(np.random.uniform(0.55, 0.88))

            elif c_idx == 5:  # 5: Other Thermal Source (Brick Kiln, Furnace, Workshop)
                frp_max = float(np.random.uniform(15.0, 55.0))
                frp_avg = frp_max * float(np.random.uniform(0.68, 0.90))
                frp_std = frp_avg * float(np.random.uniform(0.15, 0.28))
                b_avg = float(np.random.uniform(318.0, 360.0))
                b_max = b_avg * float(np.random.uniform(1.04, 1.14))
                delta_b = b_max - b_avg
                dist_fac = float(np.random.uniform(2500.0, 20000.0))
                dist_for = float(np.random.uniform(4000.0, 30000.0))
                dist_agr = float(np.random.uniform(500.0, 10000.0))
                dist_set = float(np.random.uniform(1000.0, 6000.0))
                dist_wat = float(np.random.uniform(1000.0, 12000.0))
                dist_min = float(np.random.uniform(8000.0, 45000.0))
                lc_code = 6  # Barren / Rural
                p_score = float(np.random.uniform(2.2, 5.2))
                rec_rate = float(np.random.uniform(0.35, 1.3))
                dn_ratio = float(np.random.uniform(0.25, 0.65))
                dev_ratio = float(np.random.uniform(0.9, 1.45))
                ind_ctx = float(np.random.uniform(0.35, 0.65))

            else:  # 6: Uncertain (Ambiguous noise, border readings)
                frp_max = float(np.random.uniform(5.0, 45.0))
                frp_avg = frp_max * float(np.random.uniform(0.45, 0.90))
                frp_std = frp_avg * float(np.random.uniform(0.35, 0.60))
                b_avg = float(np.random.uniform(310.0, 345.0))
                b_max = b_avg * float(np.random.uniform(1.02, 1.15))
                delta_b = b_max - b_avg
                dist_fac = float(np.random.uniform(5000.0, 35000.0))
                dist_for = float(np.random.uniform(5000.0, 35000.0))
                dist_agr = float(np.random.uniform(5000.0, 35000.0))
                dist_set = float(np.random.uniform(5000.0, 35000.0))
                dist_wat = float(np.random.uniform(5000.0, 35000.0))
                dist_min = float(np.random.uniform(5000.0, 35000.0))
                lc_code = 0  # Unknown
                p_score = float(np.random.uniform(0.1, 2.2))
                rec_rate = float(np.random.uniform(0.01, 0.4))
                dn_ratio = float(np.random.uniform(0.1, 0.45))
                dev_ratio = 1.0
                ind_ctx = float(np.random.uniform(0.1, 0.45))

            X.append([
                frp_max, frp_avg, frp_std, b_max, b_avg, delta_b,
                dist_fac, dist_for, dist_agr, dist_set, dist_wat, dist_min,
                lc_code, p_score, rec_rate, dn_ratio, dev_ratio, ind_ctx
            ])
            y.append(c_idx)

    provenance = {
        "dataset_name": "AGNI-NETRA Synthetic Grounded Calibration Set",
        "dataset_version": "v1.0-synthetic-grounded",
        "total_samples": len(y),
        "is_demo_dataset": True,
        "class_distribution": {name: samples_per_class for name in CLASS_NAMES}
    }

    return np.array(X, dtype=np.float32), np.array(y, dtype=np.int64), provenance


def train_and_export_models(output_dir: str = "ml/models") -> Dict[str, Any]:
    """
    Trains XGBoost (Primary), Random Forest (Benchmark), and Isolation Forest (Anomaly Detection).
    Performs Stratified 5-Fold Cross Validation.
    Serializes models, SHAP TreeExplainer, and exact metrics to ml/models/.
    """
    os.makedirs(output_dir, exist_ok=True)
    X, y, dataset_provenance = generate_synthetic_training_data(2800)

    # 1. Stratified 5-Fold Cross-Validation Evaluation
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    xgb_f1_scores, xgb_acc_scores = [], []
    rf_f1_scores, rf_acc_scores = [], []

    for fold_idx, (train_idx, val_idx) in enumerate(skf.split(X, y)):
        X_train, X_val = X[train_idx], X[val_idx]
        y_train, y_val = y[train_idx], y[val_idx]

        # XGBoost Primary Model
        clf_xgb = xgb.XGBClassifier(
            n_estimators=130,
            max_depth=5,
            learning_rate=0.08,
            subsample=0.85,
            colsample_bytree=0.85,
            objective="multi:softprob",
            eval_metric="mlogloss",
            random_state=42 + fold_idx
        )
        clf_xgb.fit(X_train, y_train)
        y_pred_xgb = clf_xgb.predict(X_val)
        xgb_f1_scores.append(f1_score(y_val, y_pred_xgb, average="macro"))
        xgb_acc_scores.append(accuracy_score(y_val, y_pred_xgb))

        # Random Forest Benchmark Model
        clf_rf = RandomForestClassifier(n_estimators=120, max_depth=9, random_state=42 + fold_idx)
        clf_rf.fit(X_train, y_train)
        y_pred_rf = clf_rf.predict(X_val)
        rf_f1_scores.append(f1_score(y_val, y_pred_rf, average="macro"))
        rf_acc_scores.append(accuracy_score(y_val, y_pred_rf))

    # 2. Fit Final Primary & Benchmark Models on Full Dataset
    final_xgb = xgb.XGBClassifier(
        n_estimators=130,
        max_depth=5,
        learning_rate=0.08,
        subsample=0.85,
        colsample_bytree=0.85,
        objective="multi:softprob",
        eval_metric="mlogloss",
        random_state=42
    )
    final_xgb.fit(X, y)

    final_rf = RandomForestClassifier(n_estimators=120, max_depth=9, random_state=42)
    final_rf.fit(X, y)

    # 3. Fit Unsupervised Isolation Forest on Normal Operation Vectors (Industrial + Flare)
    normal_indices = np.where((y == 0) | (y == 1))[0]
    X_normal = X[normal_indices]
    final_iso = IsolationForest(n_estimators=120, contamination=0.08, random_state=42)
    final_iso.fit(X_normal)

    # 4. Generate Final Metrics
    y_pred_final = final_xgb.predict(X)
    overall_acc = accuracy_score(y, y_pred_final)
    overall_macro_f1 = f1_score(y, y_pred_final, average="macro")
    overall_precision = precision_score(y, y_pred_final, average="macro")
    overall_recall = recall_score(y, y_pred_final, average="macro")
    cm = confusion_matrix(y, y_pred_final).tolist()
    
    report = classification_report(y, y_pred_final, target_names=CLASS_NAMES, output_dict=True)

    # Feature Importance (Gain-based for XGBoost)
    feature_importances = {
        feat: round(float(imp), 4)
        for feat, imp in zip(FEATURE_COLUMNS, final_xgb.feature_importances_)
    }

    # 5. Initialize & Serialize SHAP TreeExplainer
    explainer = shap.TreeExplainer(final_xgb)

    # 6. Save Model Artifacts
    xgb_path = os.path.join(output_dir, "xgboost_classifier_v1.joblib")
    rf_path = os.path.join(output_dir, "rf_classifier_v1.joblib")
    iso_path = os.path.join(output_dir, "isolation_forest_v1.joblib")
    explainer_path = os.path.join(output_dir, "shap_explainer_v1.joblib")
    metrics_path = os.path.join(output_dir, "metrics.json")
    schema_path = os.path.join(output_dir, "feature_schema.json")

    joblib.dump(final_xgb, xgb_path)
    joblib.dump(final_rf, rf_path)
    joblib.dump(final_iso, iso_path)
    joblib.dump(explainer, explainer_path)

    metrics_summary = {
        "model_name": "AGNI-NETRA XGBoost Thermal Classifier",
        "version": "v1.0.0",
        "algorithm": "XGBOOST",
        "benchmark_algorithm": "RANDOM_FOREST",
        "dataset_provenance": dataset_provenance,
        "evaluation_metrics": {
            "overall_accuracy": round(float(overall_acc), 4),
            "macro_f1": round(float(overall_macro_f1), 4),
            "macro_precision": round(float(overall_precision), 4),
            "macro_recall": round(float(overall_recall), 4),
            "cv_5fold_xgb_f1_mean": round(float(np.mean(xgb_f1_scores)), 4),
            "cv_5fold_xgb_f1_std": round(float(np.std(xgb_f1_scores)), 4),
            "cv_5fold_xgb_acc_mean": round(float(np.mean(xgb_acc_scores)), 4),
            "cv_5fold_rf_f1_mean": round(float(np.mean(rf_f1_scores)), 4),
            "cv_5fold_rf_acc_mean": round(float(np.mean(rf_acc_scores)), 4),
            "benchmark_lift_f1": round(float(np.mean(xgb_f1_scores) - np.mean(rf_f1_scores)), 4)
        },
        "per_class_metrics": {
            cls_name: {
                "precision": round(float(report[cls_name]["precision"]), 4),
                "recall": round(float(report[cls_name]["recall"]), 4),
                "f1_score": round(float(report[cls_name]["f1-score"]), 4),
                "support": int(report[cls_name]["support"])
            }
            for cls_name in CLASS_NAMES
        },
        "confusion_matrix": cm,
        "feature_importances": feature_importances,
        "classes": CLASS_NAMES,
        "features": FEATURE_COLUMNS
    }

    with open(metrics_path, "w") as f:
        json.dump(metrics_summary, f, indent=2)

    with open(schema_path, "w") as f:
        json.dump({
            "features": FEATURE_COLUMNS,
            "classes": CLASS_NAMES,
            "landcover_mapping": LANDCOVER_MAPPING,
            "version": "v1.0.0"
        }, f, indent=2)

    print(f"[ML PIPELINE] Successfully exported models and metrics to {output_dir}")
    print(f"XGBoost Macro F1 (CV): {metrics_summary['evaluation_metrics']['cv_5fold_xgb_f1_mean']:.4f}")
    print(f"Random Forest Benchmark F1 (CV): {metrics_summary['evaluation_metrics']['cv_5fold_rf_f1_mean']:.4f}")
    print(f"LIFT over Benchmark: +{metrics_summary['evaluation_metrics']['benchmark_lift_f1']:.4f}")

    return metrics_summary


if __name__ == "__main__":
    train_and_export_models()
