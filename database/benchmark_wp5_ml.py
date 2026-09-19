#!/usr/bin/env python3
"""
AGNI-NETRA — WP5: ML INFERENCE & EXPLAINABILITY PERFORMANCE BENCHMARK
Measures cold-start, warm single inference, batch inference (10, 50, 100),
SHAP explanation latency (cold vs warm), calibration latency, and feature extraction.
"""

import os
import sys
import time
import numpy as np

WORKSPACE_DIR = r"E:\PROJECTS\AGNI-NETRA"
if WORKSPACE_DIR not in sys.path:
    sys.path.insert(0, WORKSPACE_DIR)

from ml.inference.production_inference_service import (
    ProductionThermalInferenceService,
    FEATURE_COLUMNS
)


def run_benchmarks():
    print("=" * 80)
    print("AGNI-NETRA — WP5: ML PERFORMANCE & LATENCY BENCHMARK")
    print("=" * 80)

    # 1. Cold-Start Model Loading
    print("\n[1/6] Benchmarking Cold-Start Model Loading Latency...")
    cold_load_times = []
    for _ in range(3):
        t0 = time.perf_counter()
        svc = ProductionThermalInferenceService()
        cold_load_times.append((time.perf_counter() - t0) * 1000.0)
    print(f"  Cold-Start Load Latency: Mean = {np.mean(cold_load_times):.2f} ms | P50 = {np.percentile(cold_load_times, 50):.2f} ms | P95 = {np.percentile(cold_load_times, 95):.2f} ms")

    predictor = ProductionThermalInferenceService()
    test_event = {
        "frp_max": 85.0,
        "bright_max": 355.0,
        "dist_to_facility_m": 150.0,
        "dist_to_forest_m": 12000.0,
        "dist_to_agriculture_m": 8000.0,
        "landcover_code": 1,
        "persistence_score": 0.65,
        "recurrence_rate": 2.1
    }

    # 2. Feature Extraction Latency
    print("\n[2/6] Benchmarking Feature Extraction Latency (1,000 iterations)...")
    feat_times = []
    for _ in range(1000):
        t0 = time.perf_counter()
        _vec, _dict = predictor.extract_feature_vector(test_event)
        feat_times.append((time.perf_counter() - t0) * 1000.0)
    print(f"  Feature Extraction: Mean = {np.mean(feat_times):.3f} ms | P50 = {np.percentile(feat_times, 50):.3f} ms | P95 = {np.percentile(feat_times, 95):.3f} ms | P99 = {np.percentile(feat_times, 99):.3f} ms")

    # 3. Warm Single Inference Latency
    print("\n[3/6] Benchmarking Warm Single Inference Latency (500 iterations)...")
    warm_times = []
    for _ in range(500):
        t0 = time.perf_counter()
        _res = predictor.predict(test_event, log_audit=False)
        warm_times.append((time.perf_counter() - t0) * 1000.0)
    print(f"  Warm Single Inference: Mean = {np.mean(warm_times):.2f} ms | P50 = {np.percentile(warm_times, 50):.2f} ms | P95 = {np.percentile(warm_times, 95):.2f} ms | P99 = {np.percentile(warm_times, 99):.2f} ms")

    # 4. Batch Inference Latency (10, 50, 100 items)
    print("\n[4/6] Benchmarking Batch Inference Latency...")
    for batch_size in [10, 50, 100]:
        batch_events = [test_event for _ in range(batch_size)]
        batch_times = []
        for _ in range(20):
            t0 = time.perf_counter()
            for ev in batch_events:
                _ = predictor.predict(ev, log_audit=False)
            batch_times.append((time.perf_counter() - t0) * 1000.0)
        throughput = batch_size / (np.mean(batch_times) / 1000.0)
        print(f"  Batch ({batch_size:3d} items): Mean = {np.mean(batch_times):.2f} ms | P50 = {np.percentile(batch_times, 50):.2f} ms | Throughput = {throughput:.2f} predictions/sec")

    # 5. SHAP Explanation Latency (Warm)
    print("\n[5/6] Benchmarking SHAP Explanation Latency (200 iterations)...")
    feat_vec, _ = predictor.extract_feature_vector(test_event)
    shap_times = []
    for _ in range(200):
        t0 = time.perf_counter()
        _shap = predictor.compute_shap_explanation(feat_vec, 0)
        shap_times.append((time.perf_counter() - t0) * 1000.0)
    print(f"  SHAP Explanation: Mean = {np.mean(shap_times):.2f} ms | P50 = {np.percentile(shap_times, 50):.2f} ms | P95 = {np.percentile(shap_times, 95):.2f} ms | P99 = {np.percentile(shap_times, 99):.2f} ms")

    # 6. Probability Calibration Latency (Platt Scaling)
    print("\n[6/6] Benchmarking Balanced Platt Calibration Latency (1,000 iterations)...")
    raw_probs = predictor.xgb_model.predict_proba(feat_vec)
    cal_times = []
    for _ in range(1000):
        t0 = time.perf_counter()
        _cal = predictor.platt_calibrator.predict_proba(raw_probs)
        cal_times.append((time.perf_counter() - t0) * 1000.0)
    print(f"  Platt Calibration: Mean = {np.mean(cal_times):.3f} ms | P50 = {np.percentile(cal_times, 50):.3f} ms | P95 = {np.percentile(cal_times, 95):.3f} ms | P99 = {np.percentile(cal_times, 99):.3f} ms")

    print("\n" + "=" * 80)
    print("BENCHMARK COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    run_benchmarks()
