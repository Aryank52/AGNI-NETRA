"""
AGNI-NETRA — PHASE 18 BENCHMARK SUITE
India-First Data Intelligence & Geographic Performance

Measures operational performance metrics across:
1. Boundary Containment Latency: PostGIS ST_Within point-in-polygon checks (Target: < 5ms)
2. Administrative Assignment Latency: Hierarchical State, District, Subdistrict resolution (Target: < 20ms)
3. Inventory & Coverage Scorecard Generation Latency (Target: < 50ms)
4. Contextual Resolution Latency: Out-of-boundary conflict detection & support determination (Target: < 10ms)
5. JARVIS Master Orchestrator End-to-End Latency across India Scenarios (Target: < 100ms)
"""

import os
import sys
import time
import statistics
from typing import List, Dict, Any

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath("."))

from backend.app.core.database import SessionLocal
from backend.app.services.india_boundary_service import india_boundary_service
from backend.app.services.data_plane.india_dataset_inventory import india_dataset_inventory
from backend.app.services.jarvis.jarvis_orchestrator import master_orchestrator as jarvis_orchestrator
from backend.app.models.jarvis_schemas import JarvisCommandRequest


def benchmark_component(name: str, fn, iterations: int = 20) -> Dict[str, float]:
    """Runs fn multiple times, collecting latencies in ms."""
    latencies = []
    # Warmup
    fn()
    for _ in range(iterations):
        t0 = time.perf_counter()
        fn()
        latencies.append((time.perf_counter() - t0) * 1000.0)
    
    sorted_lat = sorted(latencies)
    p50 = statistics.median(sorted_lat)
    p95_idx = int(math_ceil(0.95 * len(sorted_lat))) - 1
    p95 = sorted_lat[max(0, min(p95_idx, len(sorted_lat) - 1))]
    max_lat = max(sorted_lat)
    mean_lat = statistics.mean(sorted_lat)

    return {
        "name": name,
        "iterations": iterations,
        "mean_ms": mean_lat,
        "p50_ms": p50,
        "p95_ms": p95,
        "max_ms": max_lat,
    }


def math_ceil(x: float) -> int:
    return int(-(-x // 1))


def run_benchmarks():
    db = SessionLocal()
    print("=" * 80)
    print("AGNI-NETRA — PHASE 18: INDIA-FIRST PERFORMANCE BENCHMARKS")
    print("=" * 80)

    results = []

    # 1. Boundary Containment Latency (Target: < 5ms)
    print("\n[BENCHMARK 1] Sovereign India Boundary Containment (PostGIS ST_Within):")
    # Test points inside and outside India
    test_points = [
        (28.6139, 77.2090), # Delhi
        (22.3072, 73.1812), # Vadodara
        (19.0760, 72.8777), # Mumbai
        (6.5800, 81.0200),  # Sri Lanka
        (24.8607, 67.0011), # Pakistan
    ]
    
    def run_boundary_check():
        for lat, lon in test_points:
            india_boundary_service.is_point_inside_india(lat, lon, db=db)

    res1 = benchmark_component("PostGIS Boundary Containment (5 pts)", run_boundary_check, iterations=30)
    # Per-point latency
    per_pt_p50 = res1["p50_ms"] / 5.0
    per_pt_p95 = res1["p95_ms"] / 5.0
    per_pt_max = res1["max_ms"] / 5.0
    print(f"  - Per-Point Latency: p50={per_pt_p50:.2f}ms, p95={per_pt_p95:.2f}ms, max={per_pt_max:.2f}ms (Target: < 5.0ms)")
    results.append({
        "component": "Boundary Check (per point)",
        "target_ms": "< 5.0 ms",
        "p50_ms": per_pt_p50,
        "p95_ms": per_pt_p95,
        "max_ms": per_pt_max,
        "status": "PASS" if per_pt_p50 < 5.0 else "MARGINAL"
    })

    # 2. Administrative Assignment Latency (Target: < 20ms)
    print("\n[BENCHMARK 2] Hierarchical Administrative Assignment (State, District, LGD):")
    def run_admin_assignment():
        india_boundary_service.get_hierarchical_context(22.3072, 73.1812, db=db)

    res2 = benchmark_component("Hierarchical Admin Context", run_admin_assignment, iterations=30)
    print(f"  - Admin Resolution Latency: p50={res2['p50_ms']:.2f}ms, p95={res2['p95_ms']:.2f}ms, max={res2['max_ms']:.2f}ms (Target: < 20.0ms)")
    results.append({
        "component": "Administrative Assignment",
        "target_ms": "< 20.0 ms",
        "p50_ms": res2["p50_ms"],
        "p95_ms": res2["p95_ms"],
        "max_ms": res2["max_ms"],
        "status": "PASS" if res2["p50_ms"] < 20.0 else "MARGINAL"
    })

    # 3. Inventory & Coverage Scorecard Generation Latency (Target: < 50ms)
    print("\n[BENCHMARK 3] Inventory & Coverage Scorecard Generation:")
    def run_inventory_scorecard():
        india_dataset_inventory.get_canonical_dataset_inventory(db)
        india_dataset_inventory.get_india_coverage_scorecard(db)

    res3 = benchmark_component("Inventory & Scorecard (Cached)", run_inventory_scorecard, iterations=25)
    print(f"  - Scorecard Latency: p50={res3['p50_ms']:.2f}ms, p95={res3['p95_ms']:.2f}ms, max={res3['max_ms']:.2f}ms (Target: < 50.0ms)")
    results.append({
        "component": "Inventory & Scorecard",
        "target_ms": "< 50.0 ms",
        "p50_ms": res3["p50_ms"],
        "p95_ms": res3["p95_ms"],
        "max_ms": res3["max_ms"],
        "status": "PASS" if res3["p50_ms"] < 50.0 else "MARGINAL"
    })

    # 4. Out-of-Scope Geographic Rejection Latency (Target: < 5ms)
    print("\n[BENCHMARK 4] Foreign Country Detection & Geographic Rejection:")
    def run_foreign_rejection():
        india_boundary_service.detect_neighboring_country(6.58, 81.02)
        india_boundary_service.detect_neighboring_country(24.86, 67.0)

    res4 = benchmark_component("Foreign Detection (2 pts)", run_foreign_rejection, iterations=50)
    print(f"  - Rejection Latency: p50={res4['p50_ms']:.3f}ms, p95={res4['p95_ms']:.3f}ms, max={res4['max_ms']:.3f}ms (Target: < 5.0ms)")
    results.append({
        "component": "Foreign Country Detection",
        "target_ms": "< 5.0 ms",
        "p50_ms": res4["p50_ms"],
        "p95_ms": res4["p95_ms"],
        "max_ms": res4["max_ms"],
        "status": "PASS" if res4["p50_ms"] < 5.0 else "MARGINAL"
    })

    # 5. JARVIS India Command Latency (Target: < 100ms)
    print("\n[BENCHMARK 5] JARVIS Master Orchestrator India Operational Commands:")
    commands = [
        "Show the highest-risk industrial thermal events in India.",
        "Find persistent thermal activity around Indian power plants.",
        "Investigate abnormal thermal activity in Maharashtra.",
        "Compare industrial thermal activity in Gujarat and Odisha.",
        "Investigate fires in Sri Lanka", # Out-of-scope rejection
    ]
    for cmd in commands:
        req = JarvisCommandRequest(command=cmd)
        def run_jarvis():
            jarvis_orchestrator.execute_command(db, req)
        res_cmd = benchmark_component(f"JARVIS: {cmd[:35]}...", run_jarvis, iterations=15)
        print(f"  - '{cmd[:40]}...': p50={res_cmd['p50_ms']:.2f}ms, p95={res_cmd['p95_ms']:.2f}ms, max={res_cmd['max_ms']:.2f}ms (Target: < 100.0ms)")
        results.append({
            "component": f"JARVIS: {cmd[:30]}",
            "target_ms": "< 100.0 ms",
            "p50_ms": res_cmd["p50_ms"],
            "p95_ms": res_cmd["p95_ms"],
            "max_ms": res_cmd["max_ms"],
            "status": "PASS" if res_cmd["p50_ms"] < 100.0 else "MARGINAL"
        })

    print("\n" + "=" * 80)
    print("PHASE 18 PERFORMANCE BENCHMARK SUMMARY TABLE")
    print("=" * 80)
    print(f"{'COMPONENT':<35} | {'TARGET':<12} | {'P50 (ms)':<10} | {'P95 (ms)':<10} | {'STATUS':<8}")
    print("-" * 80)
    for r in results:
        print(f"{r['component']:<35} | {r['target_ms']:<12} | {r['p50_ms']:<10.2f} | {r['p95_ms']:<10.2f} | {r['status']:<8}")
    print("=" * 80)

    db.close()


if __name__ == "__main__":
    run_benchmarks()
