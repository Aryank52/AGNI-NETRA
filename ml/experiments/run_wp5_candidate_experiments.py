#!/usr/bin/env python3
"""
AGNI-NETRA — WP5: CANDIDATE MODEL EXPERIMENTS RUNNER
Trains, validates, calibrates, benchmarks, and registers candidate ML models
under strict governance constraints and frozen out-of-time temporal holdouts.
"""

import os
import sys
import json
import time
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple, Optional

import numpy as np
import pandas as pd
from scipy import stats
import joblib
from sklearn.base import clone
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier
from xgboost import XGBClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold, StratifiedKFold
from sklearn.utils.class_weight import compute_sample_weight, compute_class_weight
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    log_loss,
    brier_score_loss,
    confusion_matrix,
    classification_report
)
from sqlalchemy import text

WORKSPACE_DIR = r"E:\PROJECTS\AGNI-NETRA"
if WORKSPACE_DIR not in sys.path:
    sys.path.insert(0, WORKSPACE_DIR)

from backend.app.core.database import engine
from backend.app.services.ml.model_governance_service import model_governance_service

DATASET_PATH = os.path.join(WORKSPACE_DIR, "ml", "dataset", "dataset_v3.2-real-final.csv")
CANDIDATES_DIR = os.path.join(WORKSPACE_DIR, "ml", "models", "candidates")
os.makedirs(CANDIDATES_DIR, exist_ok=True)

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
LABEL_MAP = {c: i for i, c in enumerate(TARGET_CLASSES)}
INV_LABEL_MAP = {i: c for i, c in enumerate(TARGET_CLASSES)}


def compute_sha256(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def compute_ece(y_true_indices: np.ndarray, y_prob: np.ndarray, n_bins: int = 10) -> float:
    """Computes multiclass Expected Calibration Error (ECE)."""
    confidences = np.max(y_prob, axis=1)
    predictions = np.argmax(y_prob, axis=1)
    accuracies = (predictions == y_true_indices).astype(float)
    
    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    n = len(y_true_indices)
    
    for i in range(n_bins):
        bin_lower = bin_boundaries[i]
        bin_upper = bin_boundaries[i + 1]
        mask = (confidences > bin_lower) & (confidences <= bin_upper)
        bin_size = np.sum(mask)
        if bin_size > 0:
            bin_acc = np.mean(accuracies[mask])
            bin_conf = np.mean(confidences[mask])
            ece += (bin_size / n) * abs(bin_acc - bin_conf)
    return float(np.round(ece, 4))


def compute_selective_prediction_metrics(y_true: np.ndarray, y_prob: np.ndarray) -> Dict[str, Any]:
    """Computes coverage, selective accuracy, error rate, and abstention across Tri-Tier routing."""
    confidences = np.max(y_prob, axis=1)
    sorted_probs = np.sort(y_prob, axis=1)[:, ::-1]
    margins = sorted_probs[:, 0] - sorted_probs[:, 1]
    preds = np.argmax(y_prob, axis=1)
    n = len(y_true)

    # Tier 1 policy: Conf >= 0.65, Margin >= 0.20
    t1_mask = (confidences >= 0.65) & (margins >= 0.20)
    # Tier 2 policy: Conf >= 0.45, Margin >= 0.08, not Tier 1
    t2_mask = (confidences >= 0.45) & (margins >= 0.08) & (~t1_mask)
    # Tier 3 policy: Remainder (abstain / high uncertainty)
    t3_mask = (~t1_mask) & (~t2_mask)

    t1_count = int(np.sum(t1_mask))
    t1_acc = float(np.mean(preds[t1_mask] == y_true[t1_mask])) if t1_count > 0 else 0.0
    t1_err = 1.0 - t1_acc if t1_count > 0 else 0.0

    t2_count = int(np.sum(t2_mask))
    t2_acc = float(np.mean(preds[t2_mask] == y_true[t2_mask])) if t2_count > 0 else 0.0

    t3_count = int(np.sum(t3_mask))
    t3_acc = float(np.mean(preds[t3_mask] == y_true[t3_mask])) if t3_count > 0 else 0.0

    return {
        "tier1": {
            "count": t1_count,
            "coverage": round(t1_count / n, 4),
            "selective_accuracy": round(t1_acc, 4),
            "error_rate": round(t1_err, 4),
            "action": "AUTO_DISPATCH_CANDIDATE"
        },
        "tier2": {
            "count": t2_count,
            "coverage": round(t2_count / n, 4),
            "selective_accuracy": round(t2_acc, 4),
            "action": "ANALYST_REVIEW_QUEUE"
        },
        "tier3_abstain": {
            "count": t3_count,
            "abstention_rate": round(t3_count / n, 4),
            "residual_accuracy": round(t3_acc, 4),
            "action": "UNCERTAINTY_HUMAN_GROUNDING"
        }
    }


def evaluate_model_comprehensive(
    model_name: str,
    raw_model: Any,
    calibrator: Optional[Any],
    X_test: np.ndarray,
    y_test: np.ndarray,
    X_train: np.ndarray,
    y_train: np.ndarray,
    groups_train: np.ndarray
) -> Dict[str, Any]:
    """Computes all required metrics: temporal test, spatial CV, class-wise, calibration, selective prediction."""
    # 1. Prediction & Probabilities
    raw_probs = raw_model.predict_proba(X_test)
    if calibrator is not None:
        cal_probs = calibrator.predict_proba(raw_probs)
    else:
        cal_probs = raw_probs

    y_pred = np.argmax(cal_probs, axis=1)

    # 2. Headline Metrics
    acc = float(accuracy_score(y_test, y_pred))
    bal_acc = float(balanced_accuracy_score(y_test, y_pred))
    macro_f1 = float(f1_score(y_test, y_pred, average="macro", zero_division=0))
    weighted_f1 = float(f1_score(y_test, y_pred, average="weighted", zero_division=0))
    macro_prec = float(precision_score(y_test, y_pred, average="macro", zero_division=0))
    macro_rec = float(recall_score(y_test, y_pred, average="macro", zero_division=0))

    # 3. Probabilistic & Calibration Metrics
    eps = 1e-15
    clipped_probs = np.clip(cal_probs, eps, 1 - eps)
    clipped_probs /= clipped_probs.sum(axis=1, keepdims=True)
    ll = float(log_loss(y_test, clipped_probs, labels=list(range(len(TARGET_CLASSES)))))
    
    # Brier score (one-vs-rest average)
    y_test_one_hot = np.eye(len(TARGET_CLASSES))[y_test]
    brier = float(np.mean(np.sum((clipped_probs - y_test_one_hot) ** 2, axis=1)) / len(TARGET_CLASSES))
    ece = compute_ece(y_test, clipped_probs)

    # 4. Class-wise Metrics
    cls_report = classification_report(y_test, y_pred, target_names=TARGET_CLASSES, output_dict=True, zero_division=0)
    class_metrics = {}
    for c in TARGET_CLASSES:
        class_metrics[c] = {
            "precision": round(cls_report[c]["precision"], 4),
            "recall": round(cls_report[c]["recall"], 4),
            "f1": round(cls_report[c]["f1-score"], 4),
            "support": int(cls_report[c]["support"])
        }

    # 5. Confusion Matrix
    cm = confusion_matrix(y_test, y_pred, labels=list(range(len(TARGET_CLASSES))))

    # 6. Spatial GroupKFold Cross-Validation on Training Data
    n_splits = min(4, len(np.unique(groups_train)))
    gkf = GroupKFold(n_splits=n_splits)
    cv_scores = []
    for fold, (trn_idx, val_idx) in enumerate(gkf.split(X_train, y_train, groups_train)):
        y_tr_g = y_train[trn_idx]
        X_tr_g = X_train[trn_idx]
        X_va_g = X_train[val_idx]
        y_va_g = y_train[val_idx]

        unique_tr_classes = np.sort(np.unique(y_tr_g))
        c_to_comp = {c: i for i, c in enumerate(unique_tr_classes)}
        comp_to_c = {i: c for i, c in enumerate(unique_tr_classes)}
        y_tr_compact = np.array([c_to_comp[c] for c in y_tr_g])

        clone_model = clone(raw_model)
        if isinstance(raw_model, XGBClassifier):
            clone_model.fit(X_tr_g, y_tr_compact)
            pred_compact = clone_model.predict(X_va_g)
            fold_pred = np.array([comp_to_c[c] for c in pred_compact])
        else:
            clone_model.fit(X_tr_g, y_tr_g)
            fold_pred = clone_model.predict(X_va_g)

        cv_scores.append(float(f1_score(y_va_g, fold_pred, average="macro", zero_division=0)))
    spatial_cv_f1 = float(np.mean(cv_scores))

    # 7. Tri-Tier Selective Prediction
    sel_metrics = compute_selective_prediction_metrics(y_test, cal_probs)

    # 8. Latency Profiling (100 single-point warm iterations)
    latencies = []
    single_sample = X_test[0:1]
    for _ in range(100):
        t0 = time.perf_counter()
        _p = raw_model.predict_proba(single_sample)
        if calibrator:
            _ = calibrator.predict_proba(_p)
        latencies.append((time.perf_counter() - t0) * 1000.0)

    latency_p50 = float(np.percentile(latencies, 50))
    latency_p95 = float(np.percentile(latencies, 95))
    latency_mean = float(np.mean(latencies))

    return {
        "model_name": model_name,
        "accuracy": round(acc, 4),
        "balanced_accuracy": round(bal_acc, 4),
        "macro_f1": round(macro_f1, 4),
        "weighted_f1": round(weighted_f1, 4),
        "macro_precision": round(macro_prec, 4),
        "macro_recall": round(macro_rec, 4),
        "log_loss": round(ll, 4),
        "brier_score": round(brier, 4),
        "ece": round(ece, 4),
        "spatial_groupkfold_macro_f1": round(spatial_cv_f1, 4),
        "class_metrics": class_metrics,
        "confusion_matrix": cm.tolist(),
        "selective_prediction": sel_metrics,
        "latency_ms": {
            "mean": round(latency_mean, 2),
            "p50": round(latency_p50, 2),
            "p95": round(latency_p95, 2)
        }
    }


def run_all_experiments():
    print("=" * 80)
    print("AGNI-NETRA — WP5: REPRODUCIBLE CANDIDATE ML EXPERIMENTS")
    print("=" * 80)

    # Load dataset v3.2-real-final
    df = pd.read_csv(DATASET_PATH)
    print(f"Loaded canonical dataset: {DATASET_PATH} ({len(df)} total rows)")

    # Partitions
    train_mask = (df["split"] == "TRAIN") & (df["label"] != "Uncertain")
    val_mask = (df["split"] == "VALIDATION") & (df["label"] != "Uncertain")
    test_mask = (df["split"] == "TEST") & (df["label"] != "Uncertain")

    train_df = df[train_mask].reset_index(drop=True)
    val_df = df[val_mask].reset_index(drop=True)
    test_df = df[test_mask].reset_index(drop=True)

    X_train = train_df[FEATURE_COLUMNS].values.astype(np.float32)
    y_train = train_df["label"].map(LABEL_MAP).values
    groups_train = train_df["spatial_holdout_region"].values

    X_val = val_df[FEATURE_COLUMNS].values.astype(np.float32)
    y_val = val_df["label"].map(LABEL_MAP).values

    X_test = test_df[FEATURE_COLUMNS].values.astype(np.float32)
    y_test = test_df["label"].map(LABEL_MAP).values

    print(f"Partitions: Train (2022-2024)={len(X_train)} | Val (2025)={len(X_val)} | Test (2026)={len(X_test)}")

    # Class weights for cost-sensitive training
    standard_weights = compute_sample_weight("balanced", y_train)
    
    # Custom cost-sensitive weights emphasizing Gas Flare (idx 1) and Mining Activity (idx 4)
    custom_class_weights = compute_class_weight("balanced", classes=np.unique(y_train), y=y_train)
    custom_class_weights_dict = {i: custom_class_weights[i] for i in range(len(custom_class_weights))}
    custom_class_weights_dict[1] *= 1.45  # Gas Flare boost
    custom_class_weights_dict[4] *= 1.85  # Mining Activity boost
    cost_sensitive_sample_weights = np.array([custom_class_weights_dict[y] for y in y_train])

    experiments = []

    # -------------------------------------------------------------------------
    # Candidate 1: XGBoost V3 Baseline (Current In-Memory Champion Candidate)
    # -------------------------------------------------------------------------
    print("\n[1/5] Training Candidate 1: XGBoost V3.0 Baseline (xgb-v3.0-real-candidate)...")
    xgb_v30 = XGBClassifier(
        n_estimators=160,
        max_depth=5,
        learning_rate=0.075,
        subsample=0.85,
        colsample_bytree=0.85,
        random_state=42,
        eval_metric="mlogloss"
    )
    xgb_v30.fit(X_train, y_train, sample_weight=standard_weights)
    
    # Fit Platt Calibrator strictly on 2025 Validation
    val_probs_v30 = xgb_v30.predict_proba(X_val)
    platt_v30 = LogisticRegression(class_weight="balanced", solver="lbfgs", max_iter=1000, random_state=42)
    platt_v30.fit(val_probs_v30, y_val)

    # Save artifacts
    p_xgb_v30 = os.path.join(CANDIDATES_DIR, "xgb_v3.0_candidate.joblib")
    p_platt_v30 = os.path.join(CANDIDATES_DIR, "xgb_v3.0_calibrator.joblib")
    joblib.dump(xgb_v30, p_xgb_v30)
    joblib.dump(platt_v30, p_platt_v30)

    res_v30 = evaluate_model_comprehensive(
        "xgb-v3.0-real-candidate", xgb_v30, platt_v30,
        X_test, y_test, X_train, y_train, groups_train
    )
    res_v30["artifact_sha256"] = compute_sha256(p_xgb_v30)
    res_v30["artifact_path"] = p_xgb_v30
    res_v30["model_family"] = "XGBoost"
    res_v30["version"] = "xgb-v3.0-real-candidate"
    experiments.append(res_v30)

    # -------------------------------------------------------------------------
    # Candidate 2: Cost-Sensitive Weighted XGBoost V3.1
    # -------------------------------------------------------------------------
    print("\n[2/5] Training Candidate 2: Cost-Sensitive Weighted XGBoost (xgb-v3.1-balanced-weights)...")
    xgb_v31 = XGBClassifier(
        n_estimators=175,
        max_depth=5,
        learning_rate=0.07,
        subsample=0.85,
        colsample_bytree=0.85,
        random_state=42,
        eval_metric="mlogloss"
    )
    xgb_v31.fit(X_train, y_train, sample_weight=cost_sensitive_sample_weights)

    val_probs_v31 = xgb_v31.predict_proba(X_val)
    platt_v31 = LogisticRegression(class_weight="balanced", solver="lbfgs", max_iter=1000, random_state=42)
    platt_v31.fit(val_probs_v31, y_val)

    p_xgb_v31 = os.path.join(CANDIDATES_DIR, "xgb_v3.1_weighted_candidate.joblib")
    p_platt_v31 = os.path.join(CANDIDATES_DIR, "xgb_v3.1_calibrator.joblib")
    joblib.dump(xgb_v31, p_xgb_v31)
    joblib.dump(platt_v31, p_platt_v31)

    res_v31 = evaluate_model_comprehensive(
        "xgb-v3.1-balanced-weights", xgb_v31, platt_v31,
        X_test, y_test, X_train, y_train, groups_train
    )
    res_v31["artifact_sha256"] = compute_sha256(p_xgb_v31)
    res_v31["artifact_path"] = p_xgb_v31
    res_v31["model_family"] = "XGBoost"
    res_v31["version"] = "xgb-v3.1-balanced-weights"
    experiments.append(res_v31)

    # -------------------------------------------------------------------------
    # Candidate 3: Feature-Refined Regularized XGBoost V3.2
    # -------------------------------------------------------------------------
    print("\n[3/5] Training Candidate 3: Regularized XGBoost V3.2 (xgb-v3.2-refined)...")
    xgb_v32 = XGBClassifier(
        n_estimators=150,
        max_depth=4,
        learning_rate=0.065,
        subsample=0.80,
        colsample_bytree=0.80,
        reg_alpha=0.15,
        reg_lambda=1.20,
        random_state=42,
        eval_metric="mlogloss"
    )
    xgb_v32.fit(X_train, y_train, sample_weight=standard_weights)

    val_probs_v32 = xgb_v32.predict_proba(X_val)
    platt_v32 = LogisticRegression(class_weight="balanced", solver="lbfgs", max_iter=1000, random_state=42)
    platt_v32.fit(val_probs_v32, y_val)

    p_xgb_v32 = os.path.join(CANDIDATES_DIR, "xgb_v3.2_refined_candidate.joblib")
    p_platt_v32 = os.path.join(CANDIDATES_DIR, "xgb_v3.2_calibrator.joblib")
    joblib.dump(xgb_v32, p_xgb_v32)
    joblib.dump(platt_v32, p_platt_v32)

    res_v32 = evaluate_model_comprehensive(
        "xgb-v3.2-refined", xgb_v32, platt_v32,
        X_test, y_test, X_train, y_train, groups_train
    )
    res_v32["artifact_sha256"] = compute_sha256(p_xgb_v32)
    res_v32["artifact_path"] = p_xgb_v32
    res_v32["model_family"] = "XGBoost"
    res_v32["version"] = "xgb-v3.2-refined"
    experiments.append(res_v32)

    # -------------------------------------------------------------------------
    # Candidate 4: Random Forest V3.0 Baseline
    # -------------------------------------------------------------------------
    print("\n[4/5] Training Candidate 4: Random Forest Baseline (rf-v3.0-real-candidate)...")
    rf_v30 = RandomForestClassifier(
        n_estimators=220,
        max_depth=11,
        min_samples_split=4,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1
    )
    rf_v30.fit(X_train, y_train)

    p_rf_v30 = os.path.join(CANDIDATES_DIR, "rf_v3.0_candidate.joblib")
    joblib.dump(rf_v30, p_rf_v30)

    res_rf30 = evaluate_model_comprehensive(
        "rf-v3.0-real-candidate", rf_v30, None,
        X_test, y_test, X_train, y_train, groups_train
    )
    res_rf30["artifact_sha256"] = compute_sha256(p_rf_v30)
    res_rf30["artifact_path"] = p_rf_v30
    res_rf30["model_family"] = "RandomForest"
    res_rf30["version"] = "rf-v3.0-real-candidate"
    experiments.append(res_rf30)

    # -------------------------------------------------------------------------
    # Candidate 5: ExtraTrees Ensemble Baseline
    # -------------------------------------------------------------------------
    print("\n[5/5] Training Candidate 5: ExtraTrees Ensemble Baseline (et-v3.0-candidate)...")
    et_v30 = ExtraTreesClassifier(
        n_estimators=200,
        max_depth=12,
        min_samples_split=4,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1
    )
    et_v30.fit(X_train, y_train)

    p_et_v30 = os.path.join(CANDIDATES_DIR, "et_v3.0_candidate.joblib")
    joblib.dump(et_v30, p_et_v30)

    res_et30 = evaluate_model_comprehensive(
        "et-v3.0-candidate", et_v30, None,
        X_test, y_test, X_train, y_train, groups_train
    )
    res_et30["artifact_sha256"] = compute_sha256(p_et_v30)
    res_et30["artifact_path"] = p_et_v30
    res_et30["model_family"] = "ExtraTrees"
    res_et30["version"] = "et-v3.0-candidate"
    experiments.append(res_et30)

    # -------------------------------------------------------------------------
    # Export Results & Register in PostgreSQL ml_model_registry
    # -------------------------------------------------------------------------
    results_path = os.path.join(WORKSPACE_DIR, "ml", "experiments", "candidate_evaluation_results.json")
    os.makedirs(os.path.dirname(results_path), exist_ok=True)
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(experiments, f, indent=2)
    print(f"\nSaved full candidate evaluation results to: {results_path}")

    # Register all candidates in registry with status = CANDIDATE
    with engine.begin() as conn:
        for exp in experiments:
            conn.execute(text("""
                INSERT INTO ml_model_registry (
                    id, model_name, version, model_family, algorithm, dataset_version,
                    artifact_path, artifact_sha256, metrics, training_period,
                    feature_schema_version, taxonomy_version, calibration_version,
                    status, is_active, created_by, trained_at, notes
                ) VALUES (
                    :id, :name, :ver, :family, :algo, 'v3.2-real-final',
                    :path, :sha256, CAST(:metrics AS jsonb), '2022-01-01 to 2024-12-31',
                    'v3.2', '7-class-v1', :cal_ver,
                    'CANDIDATE', FALSE, 'WP5_EXPERIMENT_RUNNER', CURRENT_TIMESTAMP, :notes
                )
                ON CONFLICT (version) DO UPDATE SET
                    artifact_sha256 = EXCLUDED.artifact_sha256,
                    metrics = EXCLUDED.metrics,
                    artifact_path = EXCLUDED.artifact_path,
                    status = 'CANDIDATE',
                    is_active = FALSE,
                    notes = EXCLUDED.notes;
            """), {
                "id": str(joblib.hash(exp["version"]))[:36],
                "name": f"AGNI-NETRA {exp['model_family']} Candidate ({exp['version']})",
                "ver": exp["version"],
                "family": exp["model_family"],
                "algo": f"{exp['model_family']} Classifier",
                "path": exp["artifact_path"],
                "sha256": exp["artifact_sha256"],
                "metrics": json.dumps({
                    "accuracy": exp["accuracy"],
                    "balanced_accuracy": exp["balanced_accuracy"],
                    "macro_f1": exp["macro_f1"],
                    "log_loss": exp["log_loss"],
                    "brier_score": exp["brier_score"],
                    "ece": exp["ece"],
                    "spatial_cv_macro_f1": exp["spatial_groupkfold_macro_f1"],
                    "tier1_selective_accuracy": exp["selective_prediction"]["tier1"]["selective_accuracy"]
                }),
                "cal_ver": "balanced-platt-v3.0" if "platt" in exp["artifact_path"].lower() or "xgb" in exp["version"].lower() else "none",
                "notes": f"WP5 Candidate Experiment. Selective accuracy T1: {exp['selective_prediction']['tier1']['selective_accuracy']}"
            })

    print("Successfully registered all 5 candidate models in ml_model_registry as CANDIDATE / is_active = FALSE.")
    return experiments


if __name__ == "__main__":
    run_all_experiments()
