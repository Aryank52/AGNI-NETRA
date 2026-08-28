import os
import sys
import json
import joblib
import numpy as np
from typing import Dict, Any
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, f1_score

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from ml.training.feature_pipeline import FEATURE_COLUMNS, CLASS_NAMES
from ml.training.train_classifier import generate_synthetic_training_data


def evaluate_saved_models(models_dir: str = "ml/models") -> Dict[str, Any]:
    """
    Evaluates saved XGBoost and Random Forest model artifacts against a holdout test split.
    """
    xgb_path = os.path.join(models_dir, "xgboost_classifier_v1.joblib")
    rf_path = os.path.join(models_dir, "rf_classifier_v1.joblib")
    iso_path = os.path.join(models_dir, "isolation_forest_v1.joblib")

    if not os.path.exists(xgb_path):
        raise FileNotFoundError(f"Model artifact not found at {xgb_path}. Run train_classifier.py first.")

    clf_xgb = joblib.load(xgb_path)
    clf_rf = joblib.load(rf_path) if os.path.exists(rf_path) else None
    clf_iso = joblib.load(iso_path) if os.path.exists(iso_path) else None

    # Generate holdout test set (seed 99)
    np.random.seed(99)
    X_test, y_test, prov = generate_synthetic_training_data(1400)

    # 1. Primary Model Evaluation (XGBoost)
    y_pred_xgb = clf_xgb.predict(X_test)
    y_prob_xgb = clf_xgb.predict_proba(X_test)
    acc_xgb = accuracy_score(y_test, y_pred_xgb)
    macro_f1_xgb = f1_score(y_test, y_pred_xgb, average="macro")
    report_xgb = classification_report(y_test, y_pred_xgb, target_names=CLASS_NAMES, output_dict=True)
    cm_xgb = confusion_matrix(y_test, y_pred_xgb).tolist()

    # 2. Benchmark Evaluation (Random Forest)
    benchmark_metrics = {}
    if clf_rf is not None:
        y_pred_rf = clf_rf.predict(X_test)
        acc_rf = accuracy_score(y_test, y_pred_rf)
        macro_f1_rf = f1_score(y_test, y_pred_rf, average="macro")
        benchmark_metrics = {
            "rf_accuracy": round(float(acc_rf), 4),
            "rf_macro_f1": round(float(macro_f1_rf), 4),
            "xgb_f1_advantage": round(float(macro_f1_xgb - macro_f1_rf), 4)
        }

    # 3. Anomaly Engine Check (Isolation Forest)
    iso_metrics = {}
    if clf_iso is not None:
        iso_preds = clf_iso.predict(X_test)
        anomaly_ratio = float(np.mean(iso_preds == -1))
        iso_metrics = {
            "outlier_detection_rate": round(anomaly_ratio, 4),
            "total_evaluated": len(X_test)
        }

    evaluation_result = {
        "evaluation_dataset": "Holdout Test Set (N=1400, Seed=99)",
        "primary_model": {
            "model_type": "XGBoost Classifier",
            "accuracy": round(float(acc_xgb), 4),
            "macro_f1": round(float(macro_f1_xgb), 4),
            "per_class": {
                cls_name: {
                    "precision": round(float(report_xgb[cls_name]["precision"]), 4),
                    "recall": round(float(report_xgb[cls_name]["recall"]), 4),
                    "f1": round(float(report_xgb[cls_name]["f1-score"]), 4)
                }
                for cls_name in CLASS_NAMES
            },
            "confusion_matrix": cm_xgb
        },
        "benchmark_comparison": benchmark_metrics,
        "isolation_forest_anomaly_engine": iso_metrics
    }

    print("\n========================================================")
    print("      AGNI-NETRA AI MODEL EVALUATION REPORT")
    print("========================================================")
    print(f"XGBoost Holdout Accuracy: {acc_xgb:.4f}")
    print(f"XGBoost Holdout Macro F1: {macro_f1_xgb:.4f}")
    if benchmark_metrics:
        print(f"Random Forest Benchmark F1: {benchmark_metrics.get('rf_macro_f1'):.4f}")
        print(f"Primary Model Lift: +{benchmark_metrics.get('xgb_f1_advantage'):.4f}")
    print("========================================================\n")

    return evaluation_result


if __name__ == "__main__":
    evaluate_saved_models()
