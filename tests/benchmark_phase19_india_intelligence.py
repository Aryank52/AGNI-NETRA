"""
AGNI-NETRA — PHASE 19 BENCHMARK SUITE
India Intelligence Depth & Operational Analytics

Measures operational performance metrics across all 11 core Phase 19 capabilities:
1. Hotspot Operational Intelligence Query (Target: < 20ms)
2. Persistent Hotspot Clustering & Deterministic Categorization (Target: < 50ms)
3. Spatial Cross-Referencing & Proximity Intelligence (Target: < 25ms)
4. State-Level Operational Intelligence Aggregation (Target: < 30ms)
5. District-Level Operational Intelligence Aggregation (Target: < 30ms)
6. Multi-Window Temporal Trends (24h, 7d, 30d, 90d, 1yr) (Target: < 40ms)
7. Governed Priority Ranking Engine (Target: < 20ms)
8. 'Why This Event Matters' 7-Factor Briefing Engine (Target: < 30ms)
9. Competing Hypotheses 5-Hypothesis Matrix (Target: < 25ms)
10. Next-Best-Evidence Recommendation Engine (Target: < 15ms)
11. Corridor Incident Synthesis (Target: < 35ms)
12. JARVIS Master Orchestrator End-to-End Latency across Phase 19 commands (Target: < 150ms)
"""

import os
import sys
import time
import statistics
from typing import List, Dict, Any

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath("."))

from backend.app.core.database import SessionLocal
from backend.app.services.intelligence.india_intelligence_service import india_intelligence_service
from backend.app.services.jarvis.jarvis_orchestrator import master_orchestrator as jarvis_orchestrator
from backend.app.models.jarvis_schemas import JarvisCommandRequest


def math_ceil(x: float) -> int:
    return int(-(-x // 1))


def benchmark_component(name: str, fn, iterations: int = 15) -> Dict[str, Any]:
    """Runs fn multiple times, collecting latencies in ms."""
    latencies = []
    # Warmup
    try:
        fn()
    except Exception as e:
        print(f"Warmup error in {name}: {e}", flush=True)
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

    res = {
        "name": name,
        "iterations": iterations,
        "mean_ms": round(mean_lat, 2),
        "p50_ms": round(p50, 2),
        "p95_ms": round(p95, 2),
        "max_ms": round(max_lat, 2),
    }
    print(f"  -> {name:50s} | Mean: {res['mean_ms']:6.2f} ms | P50: {res['p50_ms']:6.2f} ms | P95: {res['p95_ms']:6.2f} ms | Max: {res['max_ms']:6.2f} ms", flush=True)
    return res


def run_benchmarks():
    db = SessionLocal()
    print("=" * 100, flush=True)
    print("AGNI-NETRA — PHASE 19: INDIA INTELLIGENCE DEPTH & OPERATIONAL ANALYTICS BENCHMARKS", flush=True)
    print("=" * 100, flush=True)

    results = []

    # 1. Hotspot Operational Intelligence Query
    print("\n[BENCHMARK 1] Hotspot Operational Intelligence Query (Target: < 20ms):", flush=True)
    r1 = benchmark_component(
        "Hotspot Operational Query (Metric Separation)",
        lambda: india_intelligence_service.get_india_hotspot_intelligence(db, limit=10),
        iterations=15
    )
    results.append(r1)

    # 2. Persistent Hotspot Deterministic Clustering
    print("\n[BENCHMARK 2] Persistent Hotspot Clustering (Target: < 50ms):", flush=True)
    r2 = benchmark_component(
        "Persistent Hotspot Clustering & Categorization",
        lambda: india_intelligence_service.get_persistent_hotspots(db, limit=20),
        iterations=15
    )
    results.append(r2)

    # Get sample hotspot ID
    hotspots = india_intelligence_service.get_india_hotspot_intelligence(db, limit=1)
    sample_id = hotspots[0]["event_id"] if hotspots else None

    # 3. Spatial Cross-Referencing & Proximity Intelligence
    print("\n[BENCHMARK 3] Spatial Cross-Referencing (Target: < 25ms):", flush=True)
    r3 = benchmark_component(
        "Spatial Cross-Referencing (CEA/IBM/OSM Proximity)",
        lambda: india_intelligence_service.get_industrial_correlations(db, radius_km=10.0, limit=10),
        iterations=15
    )
    results.append(r3)

    # 4. State-Level Operational Intelligence
    print("\n[BENCHMARK 4] State-Level Operational Intelligence (Target: < 30ms):", flush=True)
    r4 = benchmark_component(
        "State-Level Intelligence Rollup Aggregation",
        lambda: india_intelligence_service.get_state_intelligence(db),
        iterations=15
    )
    results.append(r4)

    # 5. District-Level Operational Intelligence
    print("\n[BENCHMARK 5] District-Level Operational Intelligence (Target: < 30ms):", flush=True)
    r5 = benchmark_component(
        "District-Level Operational Intelligence",
        lambda: india_intelligence_service.get_district_intelligence(db, limit=20),
        iterations=15
    )
    results.append(r5)

    # 6. Multi-Window Temporal Trends
    print("\n[BENCHMARK 6] Multi-Window Temporal Trends (Target: < 40ms):", flush=True)
    r6 = benchmark_component(
        "Multi-Window Trends (7d Window)",
        lambda: india_intelligence_service.get_trend_intelligence(db, time_window="7d"),
        iterations=15
    )
    results.append(r6)

    # 7. Governed Priority Ranking Engine
    if sample_id:
        print("\n[BENCHMARK 7] Governed Priority Ranking Engine (Target: < 20ms):", flush=True)
        r7 = benchmark_component(
            "Governed Priority Formula Scoring (0.4R+0.2C+0.3T+0.1Rec)",
            lambda: india_intelligence_service.explain_event_priority(db, sample_id),
            iterations=15
        )
        results.append(r7)

    # 8. 'Why This Event Matters' Briefing
    if sample_id:
        print("\n[BENCHMARK 8] 'Why This Event Matters' 7-Factor Briefing (Target: < 30ms):", flush=True)
        r8 = benchmark_component(
            "7-Factor Structured Briefing Generation",
            lambda: india_intelligence_service.get_why_this_event_matters(db, sample_id),
            iterations=15
        )
        results.append(r8)

    # 9. Competing Hypotheses Evaluation
    if sample_id:
        print("\n[BENCHMARK 9] Competing Hypotheses Evaluation Matrix (Target: < 25ms):", flush=True)
        r9 = benchmark_component(
            "5-Hypothesis Evaluation Matrix Computation",
            lambda: india_intelligence_service.evaluate_competing_hypotheses(db, sample_id),
            iterations=15
        )
        results.append(r9)

    # 10. Next-Best-Evidence Recommendations
    if sample_id:
        print("\n[BENCHMARK 10] Next-Best-Evidence Recommendations (Target: < 15ms):", flush=True)
        r10 = benchmark_component(
            "Next-Best-Evidence Actionable Recommendation",
            lambda: india_intelligence_service.recommend_next_best_evidence(db, sample_id),
            iterations=15
        )
        results.append(r10)

    # 11. Infrastructure Corridor Incident Synthesis
    print("\n[BENCHMARK 11] Infrastructure Corridor Synthesis (Target: < 35ms):", flush=True)
    r11 = benchmark_component(
        "Corridor Incident Synthesis Aggregation",
        lambda: india_intelligence_service.get_india_incident_intelligence(db, limit=10),
        iterations=15
    )
    results.append(r11)

    # 12. JARVIS Master Orchestrator End-to-End Latency
    print("\n[BENCHMARK 12] JARVIS Master Orchestrator End-to-End Latency (Target: < 150ms):", flush=True)
    req = JarvisCommandRequest(command="JARVIS, run India data quality and integrity audit.")
    r12 = benchmark_component(
        "JARVIS Command: India Data Quality Audit",
        lambda: jarvis_orchestrator.execute_command(db, req),
        iterations=5
    )
    results.append(r12)

    db.close()

    print("\n" + "=" * 100, flush=True)
    print("PHASE 19 BENCHMARK SUMMARY TABLE", flush=True)
    print("=" * 100, flush=True)
    print(f"{'Capability':50s} | {'Mean (ms)':10s} | {'P50 (ms)':10s} | {'P95 (ms)':10s} | {'Max (ms)':10s}", flush=True)
    print("-" * 100, flush=True)
    for res in results:
        print(f"{res['name']:50s} | {res['mean_ms']:10.2f} | {res['p50_ms']:10.2f} | {res['p95_ms']:10.2f} | {res['max_ms']:10.2f}", flush=True)
    print("=" * 100, flush=True)


if __name__ == "__main__":
    run_benchmarks()
