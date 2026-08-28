import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import joblib
import numpy as np
import pandas as pd
from typing import Tuple, Dict, Any
from sklearn.model_selection import StratifiedKFold
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score, f1_score, confusion_matrix
import xgboost as xgb
import shap

from ml.training.feature_pipeline import FEATURE_COLUMNS, CLASS_NAMES


def generate_synthetic_training_data(n_samples: int = 1500) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generates realistic, physically grounded synthetic training data representing Indian thermal regimes:
    0: Industrial Fire (High FRP, close to facility, high built-up/industrial context, continuous)
    1: Gas Flare (Continuous 24x7, high night ratio, moderate-high FRP, very close to facility)
    2: Forest Fire (High forest proximity, seasonal, daytime dominated, large spread)
    3: Agricultural Burning (High agri proximity, low persistence, sharp seasonal peak, daytime only)
    4: Mining Activity (In mining/barren zones, recurring, moderate FRP)
    5: Other Thermal Source (Brick kilns, isolated furnaces, high-heat workshops)
    6: Uncertain (Ambiguous features, low confidence)
    """
    np.random.seed(42)
    X = []
    y = []

    samples_per_class = n_samples // len(CLASS_NAMES)

    for c_idx, c_name in enumerate(CLASS_NAMES):
        for _ in range(samples_per_class):
            if c_idx == 0:  # Industrial Fire
                frp_max = np.random.uniform(80.0, 350.0)
                frp_avg = frp_max * np.random.uniform(0.6, 0.9)
                frp_std = frp_avg * 0.3
                bright_max = np.random.uniform(360.0, 480.0)
                bright_avg = bright_max * 0.9
                dist_fac = np.random.exponential(150.0)  # Close to industrial site
                dist_for = np.random.uniform(8000.0, 50000.0)
                dist_agr = np.random.uniform(5000.0, 30000.0)
                dist_set = np.random.uniform(500.0, 8000.0)
                dist_wat = np.random.uniform(1000.0, 20000.0)
                dist_min = np.random.uniform(5000.0, 50000.0)
                lc_code = 1  # Industrial
                p_score = np.random.uniform(3.0, 8.5)
                rec_rate = np.random.uniform(0.5, 2.5)
                dn_ratio = np.random.uniform(0.6, 1.8)
                dev_ratio = np.random.uniform(2.0, 6.0)  # Elevated vs baseline
                ind_ctx = np.random.uniform(0.7, 0.98)

            elif c_idx == 1:  # Gas Flare
                frp_max = np.random.uniform(30.0, 140.0)
                frp_avg = frp_max * np.random.uniform(0.75, 0.95)
                frp_std = frp_avg * 0.15  # Steady flare
                bright_max = np.random.uniform(340.0, 420.0)
                bright_avg = bright_max * 0.95
                dist_fac = np.random.exponential(80.0)  # At flare stack
                dist_for = np.random.uniform(10000.0, 60000.0)
                dist_agr = np.random.uniform(8000.0, 40000.0)
                dist_set = np.random.uniform(2000.0, 15000.0)
                dist_wat = np.random.uniform(500.0, 15000.0)
                dist_min = np.random.uniform(10000.0, 60000.0)
                lc_code = 1  # Industrial
                p_score = np.random.uniform(7.0, 9.8)  # Highly persistent
                rec_rate = np.random.uniform(1.2, 4.0)
                dn_ratio = np.random.uniform(0.8, 1.5)  # 24x7
                dev_ratio = np.random.uniform(0.8, 1.3)  # Stable baseline
                ind_ctx = np.random.uniform(0.85, 0.99)

            elif c_idx == 2:  # Forest Fire
                frp_max = np.random.uniform(40.0, 280.0)
                frp_avg = frp_max * np.random.uniform(0.5, 0.8)
                frp_std = frp_avg * 0.4
                bright_max = np.random.uniform(330.0, 440.0)
                bright_avg = bright_max * 0.88
                dist_fac = np.random.uniform(15000.0, 80000.0)
                dist_for = np.random.exponential(200.0)  # Inside forest
                dist_agr = np.random.uniform(3000.0, 25000.0)
                dist_set = np.random.uniform(5000.0, 35000.0)
                dist_wat = np.random.uniform(2000.0, 15000.0)
                dist_min = np.random.uniform(15000.0, 80000.0)
                lc_code = 5  # Forest
                p_score = np.random.uniform(0.5, 3.0)  # Transient
                rec_rate = np.random.uniform(0.1, 0.8)
                dn_ratio = np.random.uniform(0.05, 0.3)  # Daytime dominant
                dev_ratio = 1.0
                ind_ctx = np.random.uniform(0.01, 0.15)

            elif c_idx == 3:  # Agricultural Burning
                frp_max = np.random.uniform(10.0, 75.0)
                frp_avg = frp_max * np.random.uniform(0.6, 0.85)
                frp_std = frp_avg * 0.25
                bright_max = np.random.uniform(315.0, 360.0)
                bright_avg = bright_max * 0.92
                dist_fac = np.random.uniform(8000.0, 45000.0)
                dist_for = np.random.uniform(5000.0, 30000.0)
                dist_agr = np.random.exponential(100.0)  # Inside agricultural fields
                dist_set = np.random.uniform(800.0, 6000.0)
                dist_wat = np.random.uniform(1500.0, 12000.0)
                dist_min = np.random.uniform(10000.0, 60000.0)
                lc_code = 4  # Agriculture
                p_score = np.random.uniform(0.2, 1.5)  # Highly transient stubble fire
                rec_rate = np.random.uniform(0.05, 0.4)
                dn_ratio = np.random.uniform(0.0, 0.15)  # Strict daytime
                dev_ratio = 1.0
                ind_ctx = np.random.uniform(0.02, 0.20)

            elif c_idx == 4:  # Mining Activity
                frp_max = np.random.uniform(25.0, 110.0)
                frp_avg = frp_max * np.random.uniform(0.6, 0.85)
                frp_std = frp_avg * 0.3
                bright_max = np.random.uniform(325.0, 385.0)
                bright_avg = bright_max * 0.92
                dist_fac = np.random.uniform(3000.0, 25000.0)
                dist_for = np.random.uniform(3000.0, 20000.0)
                dist_agr = np.random.uniform(4000.0, 25000.0)
                dist_set = np.random.uniform(3000.0, 15000.0)
                dist_wat = np.random.uniform(2000.0, 15000.0)
                dist_min = np.random.exponential(250.0)  # In/near open-cast mine
                lc_code = 2  # Mining / Barren
                p_score = np.random.uniform(3.5, 7.5)  # Recurring
                rec_rate = np.random.uniform(0.4, 1.8)
                dn_ratio = np.random.uniform(0.3, 0.9)
                dev_ratio = np.random.uniform(0.9, 1.8)
                ind_ctx = np.random.uniform(0.5, 0.85)

            elif c_idx == 5:  # Other Thermal Source (Brick Kiln / Small Workshop)
                frp_max = np.random.uniform(15.0, 50.0)
                frp_avg = frp_max * np.random.uniform(0.7, 0.9)
                frp_std = frp_avg * 0.2
                bright_max = np.random.uniform(320.0, 365.0)
                bright_avg = bright_max * 0.93
                dist_fac = np.random.uniform(2500.0, 18000.0)
                dist_for = np.random.uniform(4000.0, 25000.0)
                dist_agr = np.random.uniform(500.0, 8000.0)
                dist_set = np.random.uniform(1000.0, 5000.0)
                dist_wat = np.random.uniform(1000.0, 10000.0)
                dist_min = np.random.uniform(8000.0, 40000.0)
                lc_code = 6  # Barren / Rural
                p_score = np.random.uniform(2.0, 5.0)
                rec_rate = np.random.uniform(0.3, 1.2)
                dn_ratio = np.random.uniform(0.2, 0.6)
                dev_ratio = np.random.uniform(0.9, 1.4)
                ind_ctx = np.random.uniform(0.3, 0.6)

            else:  # Uncertain (Ambiguous noise)
                frp_max = np.random.uniform(5.0, 40.0)
                frp_avg = frp_max * np.random.uniform(0.4, 0.9)
                frp_std = frp_avg * 0.5
                bright_max = np.random.uniform(310.0, 340.0)
                bright_avg = bright_max * 0.95
                dist_fac = np.random.uniform(5000.0, 30000.0)
                dist_for = np.random.uniform(5000.0, 30000.0)
                dist_agr = np.random.uniform(5000.0, 30000.0)
                dist_set = np.random.uniform(5000.0, 30000.0)
                dist_wat = np.random.uniform(5000.0, 30000.0)
                dist_min = np.random.uniform(5000.0, 30000.0)
                lc_code = 0  # Unknown
                p_score = np.random.uniform(0.1, 2.0)
                rec_rate = np.random.uniform(0.01, 0.3)
                dn_ratio = np.random.uniform(0.1, 0.4)
                dev_ratio = 1.0
                ind_ctx = np.random.uniform(0.1, 0.4)

            X.append([
                frp_max, frp_avg, frp_std, bright_max, bright_avg,
                dist_fac, dist_for, dist_agr, dist_set, dist_wat, dist_min,
                lc_code, p_score, rec_rate, dn_ratio, dev_ratio, ind_ctx
            ])
            y.append(c_idx)

    return np.array(X, dtype=np.float32), np.array(y, dtype=np.int64)


def train_and_export_models(output_dir: str = "ml/models") -> Dict[str, Any]:
    """
    Trains XGBoost and Random Forest models on engineered geospatial-thermal features.
    Saves models and pre-fits SHAP TreeExplainer.
    """
    os.makedirs(output_dir, exist_ok=True)
    X, y = generate_synthetic_training_data(2100)

    # 5-Fold Stratified Cross-Validation
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    xgb_f1_scores = []
    rf_f1_scores = []

    for train_idx, val_idx in skf.split(X, y):
        X_train, X_val = X[train_idx], X[val_idx]
        y_train, y_val = y[train_idx], y[val_idx]

        # XGBoost
        clf_xgb = xgb.XGBClassifier(
            n_estimators=120,
            max_depth=5,
            learning_rate=0.08,
            objective="multi:softprob",
            eval_metric="mlogloss",
            random_state=42
        )
        clf_xgb.fit(X_train, y_train)
        y_pred_xgb = clf_xgb.predict(X_val)
        xgb_f1_scores.append(f1_score(y_val, y_pred_xgb, average="macro"))

        # Random Forest Benchmark
        clf_rf = RandomForestClassifier(n_estimators=100, max_depth=8, random_state=42)
        clf_rf.fit(X_train, y_train)
        y_pred_rf = clf_rf.predict(X_val)
        rf_f1_scores.append(f1_score(y_val, y_pred_rf, average="macro"))

    # Fit final models on full dataset
    final_xgb = xgb.XGBClassifier(
        n_estimators=120,
        max_depth=5,
        learning_rate=0.08,
        objective="multi:softprob",
        eval_metric="mlogloss",
        random_state=42
    )
    final_xgb.fit(X, y)

    final_rf = RandomForestClassifier(n_estimators=100, max_depth=8, random_state=42)
    final_rf.fit(X, y)

    # Evaluate Final Metrics
    y_pred_final = final_xgb.predict(X)
    acc = accuracy_score(y, y_pred_final)
    macro_f1 = f1_score(y, y_pred_final, average="macro")
    cm = confusion_matrix(y, y_pred_final).tolist()

    # Save artifacts
    xgb_path = os.path.join(output_dir, "xgboost_classifier_v1.joblib")
    rf_path = os.path.join(output_dir, "rf_classifier_v1.joblib")
    
    joblib.dump(final_xgb, xgb_path)
    joblib.dump(final_rf, rf_path)

    # Initialize SHAP explainer
    explainer = shap.TreeExplainer(final_xgb)
    explainer_path = os.path.join(output_dir, "shap_explainer_v1.joblib")
    joblib.dump(explainer, explainer_path)

    metrics_summary = {
        "model_name": "AGNI-NETRA XGBoost Thermal Classifier",
        "version": "v1.0.0",
        "accuracy": round(float(acc), 4),
        "f1_macro": round(float(macro_f1), 4),
        "cv_xgb_f1": round(float(np.mean(xgb_f1_scores)), 4),
        "cv_rf_benchmark_f1": round(float(np.mean(rf_f1_scores)), 4),
        "confusion_matrix": cm,
        "classes": CLASS_NAMES,
        "features": FEATURE_COLUMNS
    }

    print(f"[ML PIPELINE] Successfully trained and exported models to {output_dir}")
    print(f"XGBoost Macro F1: {metrics_summary['f1_macro']:.4f} (CV: {metrics_summary['cv_xgb_f1']:.4f})")
    print(f"Random Forest Benchmark CV F1: {metrics_summary['cv_rf_benchmark_f1']:.4f}")

    return metrics_summary


if __name__ == "__main__":
    train_and_export_models()
