"""
AGNI-NETRA — PHASE 16: GLOBAL DATA INGESTION & DATA GOVERNANCE BENCHMARK SUITE
Measures latency and throughput across all 8 mandatory Section 43 benchmarks:
1. Single Record Normalization Latency (Target: <= 100 microseconds)
2. Batch Normalization Throughput (1,000 records) (Target: >= 10,000 rec/s)
3. Batch Normalization Throughput (10,000 records) (Target: >= 10,000 rec/s)
4. Deduplication Evaluation Throughput (Target: >= 5,000 evals/s)
5. Spatial Query Latency (50km radius via PostGIS) (Target: P95 <= 50ms)
6. Provenance Lookup Latency (Target: P95 <= 10ms)
7. Freshness Evaluation Latency (all 18 governed datasets) (Target: <= 50ms)
8. Ingestion Batch Status Query Latency (Target: P95 <= 20ms)

Outputs formatted Markdown summary table with targets, measured results, and pass/fail verdicts.
"""

import sys
import os
import time
import uuid
import numpy as np
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any
from sqlalchemy import text

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.database import SessionLocal
from backend.app.services.data_plane.normalization import NormalizationEngine
from backend.app.services.data_plane.validation import ValidationEngine
from backend.app.services.data_plane.deduplication import DeduplicationEngine
from backend.app.services.data_plane.freshness import FreshnessEngine
from backend.app.services.data_plane.engine import data_plane_engine
from backend.app.models.domain import IngestionBatchModel, IngestionRecordModel, DatasetRegistryModel


def run_benchmarks():
    db = SessionLocal()
    print("=" * 80)
    print("AGNI-NETRA — PHASE 16: GLOBAL DATA-PLANE PERFORMANCE BENCHMARK RUNNER")
    print("=" * 80)

    results = []

    # -------------------------------------------------------------------------
    # 1. Single Record Normalization Latency
    # -------------------------------------------------------------------------
    print("\n[*] Benchmarking Benchmark 1: Single Record Normalization Latency...")
    single_payload = {
        "latitude": 22.350045,
        "longitude": 70.020032,
        "observation_time": "2026-09-10T12:00:00Z",
        "temperature": 350.0,
        "frp": 45.2,
        "wind_speed": 12.5
    }

    n_warmup = 100
    for _ in range(n_warmup):
        NormalizationEngine.normalize_coordinates(single_payload["latitude"], single_payload["longitude"])
        NormalizationEngine.normalize_timestamp(single_payload["observation_time"])
        NormalizationEngine.normalize_unit("temperature", single_payload["temperature"], "K")
        NormalizationEngine.normalize_unit("frp", single_payload["frp"], "MW")
        NormalizationEngine.normalize_unit("wind_speed", single_payload["wind_speed"], "m/s")

    n_runs = 2000
    latencies_us = []
    for _ in range(n_runs):
        t0 = time.perf_counter()
        NormalizationEngine.normalize_coordinates(single_payload["latitude"], single_payload["longitude"])
        NormalizationEngine.normalize_timestamp(single_payload["observation_time"])
        NormalizationEngine.normalize_unit("temperature", single_payload["temperature"], "K")
        NormalizationEngine.normalize_unit("frp", single_payload["frp"], "MW")
        NormalizationEngine.normalize_unit("wind_speed", single_payload["wind_speed"], "m/s")
        t1 = time.perf_counter()
        latencies_us.append((t1 - t0) * 1_000_000.0)

    p50_us = np.percentile(latencies_us, 50)
    p95_us = np.percentile(latencies_us, 95)
    mean_us = np.mean(latencies_us)

    results.append({
        "benchmark": "Single Record Normalization Latency",
        "target": "<= 100 us",
        "measured": f"{p50_us:.1f} us (P50) / {p95_us:.1f} us (P95)",
        "unit": "microseconds",
        "passed": p50_us <= 100.0
    })

    # -------------------------------------------------------------------------
    # 2. Batch Normalization Throughput (1,000 records)
    # -------------------------------------------------------------------------
    print("[*] Benchmarking Benchmark 2: Batch Normalization Throughput (1,000 records)...")
    batch_1k = [
        {
            "latitude": 22.0 + (i * 0.001),
            "longitude": 70.0 + (i * 0.001),
            "observation_time": "2026-09-10T12:00:00Z",
            "temperature": 340.0 + (i % 50),
            "frp": 30.0 + (i % 20)
        }
        for i in range(1000)
    ]

    t0_1k = time.perf_counter()
    for rec in batch_1k:
        NormalizationEngine.normalize_coordinates(rec["latitude"], rec["longitude"])
        NormalizationEngine.normalize_timestamp(rec["observation_time"])
        NormalizationEngine.normalize_unit("temperature", rec["temperature"], "K")
        NormalizationEngine.normalize_unit("frp", rec["frp"], "MW")
    t1_1k = time.perf_counter()
    duration_1k = t1_1k - t0_1k
    throughput_1k = 1000.0 / duration_1k if duration_1k > 0 else 100000.0

    results.append({
        "benchmark": "Batch Normalization (1,000 records)",
        "target": ">= 10,000 rec/s",
        "measured": f"{throughput_1k:,.0f} rec/s ({duration_1k*1000:.2f} ms total)",
        "unit": "rec/s",
        "passed": throughput_1k >= 10000.0
    })

    # -------------------------------------------------------------------------
    # 3. Batch Normalization Throughput (10,000 records)
    # -------------------------------------------------------------------------
    print("[*] Benchmarking Benchmark 3: Batch Normalization Throughput (10,000 records)...")
    batch_10k = [
        {
            "latitude": 22.0 + (i * 0.0001),
            "longitude": 70.0 + (i * 0.0001),
            "observation_time": "2026-09-10T12:00:00Z",
            "temperature": 340.0 + (i % 100),
            "frp": 25.0 + (i % 50)
        }
        for i in range(10000)
    ]

    t0_10k = time.perf_counter()
    for rec in batch_10k:
        NormalizationEngine.normalize_coordinates(rec["latitude"], rec["longitude"])
        NormalizationEngine.normalize_timestamp(rec["observation_time"])
        NormalizationEngine.normalize_unit("temperature", rec["temperature"], "K")
        NormalizationEngine.normalize_unit("frp", rec["frp"], "MW")
    t1_10k = time.perf_counter()
    duration_10k = t1_10k - t0_10k
    throughput_10k = 10000.0 / duration_10k if duration_10k > 0 else 100000.0

    results.append({
        "benchmark": "Batch Normalization (10,000 records)",
        "target": ">= 10,000 rec/s",
        "measured": f"{throughput_10k:,.0f} rec/s ({duration_10k*1000:.2f} ms total)",
        "unit": "rec/s",
        "passed": throughput_10k >= 10000.0
    })

    # -------------------------------------------------------------------------
    # 4. Deduplication Evaluation Throughput
    # -------------------------------------------------------------------------
    print("[*] Benchmarking Benchmark 4: Deduplication Evaluation Throughput...")
    existing_reference = [
        {
            "ingestion_id": f"REF-{i}",
            "provider": "NASA_FIRMS",
            "dataset": "VIIRS",
            "source_record_id": f"SRC-{i}",
            "latitude": 22.35 + (i * 0.01),
            "longitude": 70.02 + (i * 0.01),
            "observation_time": "2026-09-10T12:00:00Z"
        }
        for i in range(200)
    ]

    candidates = [
        {
            "provider": "NASA_FIRMS",
            "dataset": "VIIRS",
            "source_record_id": f"CAND-{i}",
            "latitude": 22.35 + (i * 0.005),
            "longitude": 70.02 + (i * 0.005),
            "observation_time": "2026-09-10T12:00:00Z"
        }
        for i in range(2000)
    ]

    t0_dedup = time.perf_counter()
    for cand in candidates:
        DeduplicationEngine.evaluate(cand, existing_reference)
    t1_dedup = time.perf_counter()
    duration_dedup = t1_dedup - t0_dedup
    throughput_dedup = len(candidates) / duration_dedup if duration_dedup > 0 else 50000.0

    results.append({
        "benchmark": "Deduplication Evaluation Throughput",
        "target": ">= 5,000 evals/s",
        "measured": f"{throughput_dedup:,.0f} evals/s ({duration_dedup*1000:.2f} ms for 2k candidates)",
        "unit": "evals/s",
        "passed": throughput_dedup >= 5000.0
    })

    # -------------------------------------------------------------------------
    # 5. Spatial Query Latency (50km radius via PostGIS)
    # -------------------------------------------------------------------------
    print("[*] Benchmarking Benchmark 5: Spatial Query Latency (50km radius)...")
    spatial_latencies_ms = []
    # Test 20 consecutive spatial queries around Jamnagar industrial cluster
    for _ in range(20):
        t0_sp = time.perf_counter()
        db.execute(text("""
            SELECT id, name, facility_type, state, latitude, longitude
            FROM industrial_facilities
            WHERE geom IS NOT NULL
              AND ST_DWithin(
                geom,
                ST_SetSRID(ST_MakePoint(70.02, 22.35), 4326),
                0.45
            )
            LIMIT 50;
        """)).fetchall()
        t1_sp = time.perf_counter()
        spatial_latencies_ms.append((t1_sp - t0_sp) * 1000.0)

    p95_sp = np.percentile(spatial_latencies_ms, 95)
    p50_sp = np.percentile(spatial_latencies_ms, 50)

    results.append({
        "benchmark": "Spatial Query Latency (50km radius)",
        "target": "P95 <= 50 ms",
        "measured": f"{p50_sp:.2f} ms (P50) / {p95_sp:.2f} ms (P95)",
        "unit": "milliseconds",
        "passed": p95_sp <= 50.0
    })

    # -------------------------------------------------------------------------
    # 6. Provenance Lookup Latency
    # -------------------------------------------------------------------------
    print("[*] Benchmarking Benchmark 6: Provenance Lookup Latency...")
    sample_event = db.execute(text("SELECT id, event_code FROM thermal_events LIMIT 1;")).fetchone()
    sample_code = sample_event[1] if sample_event else "EVT-2026-08-0001"

    prov_latencies_ms = []
    for _ in range(50):
        t0_pr = time.perf_counter()
        db.execute(text("""
            SELECT id, event_code, latitude, longitude, avg_frp, detection_count
            FROM thermal_events
            WHERE event_code = :code
            LIMIT 1;
        """), {"code": sample_code}).fetchone()
        t1_pr = time.perf_counter()
        prov_latencies_ms.append((t1_pr - t0_pr) * 1000.0)

    p95_pr = np.percentile(prov_latencies_ms, 95)
    p50_pr = np.percentile(prov_latencies_ms, 50)

    results.append({
        "benchmark": "Provenance Lookup Latency",
        "target": "P95 <= 10 ms",
        "measured": f"{p50_pr:.2f} ms (P50) / {p95_pr:.2f} ms (P95)",
        "unit": "milliseconds",
        "passed": p95_pr <= 10.0
    })

    # -------------------------------------------------------------------------
    # 7. Freshness Evaluation Latency (all 18 governed datasets)
    # -------------------------------------------------------------------------
    print("[*] Benchmarking Benchmark 7: Freshness Evaluation Latency (all datasets)...")
    fresh_latencies_ms = []
    for _ in range(30):
        t0_fr = time.perf_counter()
        FreshnessEngine.get_all_datasets_freshness(db)
        t1_fr = time.perf_counter()
        fresh_latencies_ms.append((t1_fr - t0_fr) * 1000.0)

    p50_fr = np.percentile(fresh_latencies_ms, 50)
    p95_fr = np.percentile(fresh_latencies_ms, 95)

    results.append({
        "benchmark": "Freshness Evaluation Latency (All Datasets)",
        "target": "<= 50 ms",
        "measured": f"{p50_fr:.2f} ms (P50) / {p95_fr:.2f} ms (P95)",
        "unit": "milliseconds",
        "passed": p95_fr <= 50.0
    })

    # -------------------------------------------------------------------------
    # 8. Ingestion Batch Status Query Latency
    # -------------------------------------------------------------------------
    print("[*] Benchmarking Benchmark 8: Ingestion Batch Status Query Latency...")
    batch_latencies_ms = []
    for _ in range(50):
        t0_bs = time.perf_counter()
        db.query(IngestionBatchModel).order_by(IngestionBatchModel.started_at.desc()).limit(10).all()
        t1_bs = time.perf_counter()
        batch_latencies_ms.append((t1_bs - t0_bs) * 1000.0)

    p50_bs = np.percentile(batch_latencies_ms, 50)
    p95_bs = np.percentile(batch_latencies_ms, 95)

    results.append({
        "benchmark": "Ingestion Batch Status Query Latency",
        "target": "P95 <= 20 ms",
        "measured": f"{p50_bs:.2f} ms (P50) / {p95_bs:.2f} ms (P95)",
        "unit": "milliseconds",
        "passed": p95_bs <= 20.0
    })

    db.close()

    # -------------------------------------------------------------------------
    # Format and Print Results
    # -------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("PHASE 16 BENCHMARK RESULTS TABLE")
    print("=" * 80)
    print(f"| {'Benchmark Metric':<42} | {'Target':<18} | {'Measured Result':<35} | {'Verdict':<8} |")
    print(f"|{'-'*44}|{'-'*20}|{'-'*37}|{'-'*10}|")
    all_passed = True
    for r in results:
        status_str = "PASS" if r["passed"] else "FAIL"
        if not r["passed"]:
            all_passed = False
        print(f"| {r['benchmark']:<42} | {r['target']:<18} | {r['measured']:<35} | {status_str:<8} |")

    print("=" * 80)
    if all_passed:
        print(">> ALL 8/8 PHASE 16 BENCHMARKS PASSED SUCCESSFULLY! <<")
    else:
        print(">> SOME BENCHMARKS DID NOT MEET TARGETS <<")
    print("=" * 80)

    return all_passed, results


if __name__ == "__main__":
    success, _ = run_benchmarks()
    sys.exit(0 if success else 1)
