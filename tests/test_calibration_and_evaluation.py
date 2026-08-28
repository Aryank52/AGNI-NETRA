import os
import sys
import pytest
import numpy as np
import pandas as pd

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ml.dataset.dataset_builder import dataset_builder, VALID_DATASET_TYPES
from ml.training.feature_pipeline import FEATURE_COLUMNS, CLASS_NAMES
from ml.training.calibrate import probability_calibrator
from ml.training.evaluate import evaluate_spatial_holdout, evaluate_temporal_holdout, evaluate_saved_models


def test_dataset_builder_provenance_and_filtering():
    """Verify strict dataset type filtering and schema validation"""
    # 1. Build sample
    sample = dataset_builder.build_real_dataset_sample(
        event_id="EVT-TEST-001",
        features={col: 10.0 for col in FEATURE_COLUMNS},
        label="Industrial Fire",
        dataset_type="REAL",
        label_source="NASA_FIRMS_VIIRS",
        verification_status="ANALYST_CONFIRMED"
    )
    assert sample["dataset_type"] == "REAL"
    assert sample["label"] == "Industrial Fire"
    assert len(sample) >= len(FEATURE_COLUMNS)

    # 2. Strict filtering test
    samples_list = [
        sample,
        dataset_builder.build_real_dataset_sample(
            event_id="EVT-TEST-002",
            features={col: 5.0 for col in FEATURE_COLUMNS},
            label="Forest Fire",
            dataset_type="SYNTHETIC"
        )
    ]

    # Only permit REAL dataset types
    df_real = dataset_builder.filter_dataset(samples_list, permitted_types=["REAL"])
    assert len(df_real) == 1
    assert df_real.iloc[0]["dataset_type"] == "REAL"


def test_probability_calibrator_brier_score():
    """Verify Brier score multi-class reliability evaluation"""
    np.random.seed(42)
    n_samples = 100
    n_classes = len(CLASS_NAMES)

    # Perfectly calibrated dummy predictions
    y_true_indices = np.random.randint(0, n_classes, size=n_samples)
    y_true_onehot = np.eye(n_classes)[y_true_indices]

    # Add slight noise to one-hot for probas
    y_prob = y_true_onehot * 0.8 + 0.2 / n_classes

    res = probability_calibrator.evaluate_calibration(y_true_onehot, y_prob, CLASS_NAMES)
    assert "mean_brier_score" in res
    assert res["mean_brier_score"] < 0.15
    assert res["is_well_calibrated"] is True


def test_spatial_and_temporal_holdout_evaluations():
    """Verify spatial GroupKFold and temporal TimeSeriesSplit evaluations"""
    spatial_res = evaluate_spatial_holdout(models_dir="ml/models", n_splits=3)
    assert "mean_spatial_holdout_f1" in spatial_res
    assert spatial_res["mean_spatial_holdout_f1"] >= 0.85
    assert len(spatial_res["fold_f1_scores"]) == 3

    temporal_res = evaluate_temporal_holdout(models_dir="ml/models", n_splits=3)
    assert "mean_temporal_holdout_f1" in temporal_res
    assert temporal_res["mean_temporal_holdout_f1"] >= 0.85
