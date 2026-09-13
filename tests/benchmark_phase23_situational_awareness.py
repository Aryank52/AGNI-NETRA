"""
AGNI-NETRA — Phase 23 Performance Regression & Latency Benchmark
Measures P50, P95, P99, Mean, and Max latencies across Phase 23 Situational Awareness & Command Center capabilities:
1. Situational Snapshot Generation
2. Change Detection Engine (Target < 500ms)
3. Analyst Attention Queue Ranking (Target < 800ms)
4. 60-Second Situational Awareness Brief (Target < 2000ms)
5. India Macro Situation Brief (Target < 2500ms)
6. Operational Timeline Aggregation (Target < 300ms)
7. End-to-End Command Center Orchestration ("JARVIS, give me a 60-second situation brief.")
8. REST API /api/v1/jarvis/situational/brief/60-second
9. REST API /api/v1/jarvis/situational/attention-queue
10. REST API /api/v1/jarvis/situational/brief/india
"""

import time
import json
import statistics
import os
import sys
from typing import List, Dict, Any

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.database import SessionLocal
from backend.app.services.jarvis.jarvis_situational_service import jarvis_situational_service
from backend.app.services.jarvis.jarvis_orchestrator import jarvis_orchestrator
from backend.app.models.jarvis_schemas import JarvisCommandRequest
from fastapi.testclient import TestClient
from backend.app.main import app


def percentile(data: List[float], p: float) -> float:
    if not data:
        return 0.0
    sorted_data = sorted(data)
    idx = int(len(sorted_data) * p)
    return sorted_data[min(idx, len(sorted_data) - 1)]


def run_benchmark():
    db = SessionLocal()
    client = TestClient(app)

    print("=" * 85)
    print("AGNI-NETRA PHASE 23 SITUATIONAL AWARENESS & COMMAND CENTER BENCHMARK")
    print("Sovereign Territory of India Scope — 10 Iterations Per Capability")
    print("=" * 85)

    benchmarks: Dict[str, Any] = {}

    def measure(name: str, fn, target_ms: float = 3000.0, iterations: int = 10):
        latencies = []
        # Warmup
        try:
            fn()
        except Exception as e:
            print(f"Warmup error for {name}: {e}")

        for _ in range(iterations):
            t0 = time.perf_counter()
            fn()
            latencies.append((time.perf_counter() - t0) * 1000.0)

        mean_val = statistics.mean(latencies)
        p50 = statistics.median(latencies)
        p95 = percentile(latencies, 0.95)
        p99 = percentile(latencies, 0.99)
        max_val = max(latencies)

        target_status = "PASS" if p95 <= target_ms else "FAIL"

        benchmarks[name] = {
            "mean_ms": round(mean_val, 2),
            "p50_ms": round(p50, 2),
            "p95_ms": round(p95, 2),
            "p99_ms": round(p99, 2),
            "max_ms": round(max_val, 2),
            "target_ms": target_ms,
            "status": target_status,
            "iterations": iterations,
        }
        print(f"[{name:<45}] P50: {p50:6.2f}ms | P95: {p95:6.2f}ms | P99: {p99:6.2f}ms | Mean: {mean_val:6.2f}ms | Target: <{target_ms}ms [{target_status}]")

    # 1. Situational Snapshot Generation
    measure(
        "1. Situational Snapshot Generation",
        lambda: jarvis_situational_service.generate_snapshot(db),
        target_ms=1000.0,
        iterations=10
    )

    # 2. Change Detection Engine (Target < 500ms)
    measure(
        "2. Change Detection Engine",
        lambda: jarvis_situational_service.detect_changes(db),
        target_ms=500.0,
        iterations=10
    )

    # 3. Attention Queue Ranking (Target < 800ms)
    measure(
        "3. Attention Queue Ranking",
        lambda: jarvis_situational_service.build_attention_queue(db),
        target_ms=800.0,
        iterations=10
    )

    # 4. 60-Second Situational Awareness Brief (Target < 2000ms)
    measure(
        "4. 60-Second Situational Brief",
        lambda: jarvis_situational_service.generate_60s_brief(db),
        target_ms=2000.0,
        iterations=10
    )

    # 5. India Macro Situation Brief (Target < 2500ms)
    measure(
        "5. India Macro Situation Brief",
        lambda: jarvis_situational_service.generate_india_brief(db),
        target_ms=2500.0,
        iterations=10
    )

    # 6. Operational Timeline Aggregation (Target < 300ms)
    measure(
        "6. Operational Timeline Aggregation",
        lambda: jarvis_situational_service.get_situational_timeline(db),
        target_ms=300.0,
        iterations=10
    )

    # 7. End-to-End JARVIS Situational Brief Orchestration
    measure(
        "7. E2E JARVIS Situational Orchestration",
        lambda: jarvis_orchestrator.execute_command(
            db=db,
            request=JarvisCommandRequest(command="JARVIS, give me a 60-second situation brief.")
        ),
        target_ms=2500.0,
        iterations=10
    )

    # 8. REST API /api/v1/jarvis/situational/brief/60-second
    measure(
        "8. REST API /situational/brief/60-second",
        lambda: client.get("/api/v1/jarvis/situational/brief/60-second"),
        target_ms=2000.0,
        iterations=10
    )

    # 9. REST API /api/v1/jarvis/situational/attention-queue
    measure(
        "9. REST API /situational/attention-queue",
        lambda: client.get("/api/v1/jarvis/situational/attention-queue"),
        target_ms=1000.0,
        iterations=10
    )

    # 10. REST API /api/v1/jarvis/situational/brief/india
    measure(
        "10. REST API /situational/brief/india",
        lambda: client.get("/api/v1/jarvis/situational/brief/india"),
        target_ms=2500.0,
        iterations=10
    )

    print("=" * 85)
    print("ALL PHASE 23 BENCHMARKS COMPLETED SUCCESSFULLY")
    print("=" * 85)

    output_path = os.path.join(os.path.dirname(__file__), "benchmark_phase23_results.json")
    with open(output_path, "w") as f:
        json.dump(benchmarks, f, indent=2)
    print(f"Results written to: {output_path}")

    db.close()
    return benchmarks


if __name__ == "__main__":
    run_benchmark()
