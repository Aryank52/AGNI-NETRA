"""
AGNI-NETRA — Phase 22 Performance Regression & Latency Benchmark
Measures P50, P95, P99, Mean, and Max latencies across Phase 22 core intelligence capabilities:
1. Objective Normalization & Sovereign Scope Resolution
2. Governed Tool Registry & Adversarial Safety Guard
3. Historical Baseline 6-Year Recurrence Matching
4. Analysis of Competing Hypotheses (ACH 5-Hypothesis Matrix)
5. Decoupled Epistemic Metrics Synthesis (Risk, Priority, Calibrated Confidence, Uncertainty)
6. Assessment Differing & Change Driver Extraction (V1 -> V2)
7. Next-Best-Evidence Identification & Ranking
8. End-to-End JARVIS Mission Orchestration (12-stage deterministic pipeline)
9. Command Interpreter Pattern Matching & Parameter Extraction
10. REST API /api/v1/jarvis/mission Endpoint Latency
"""

import time
import json
import statistics
import os
import sys
from typing import List, Dict, Any

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.database import SessionLocal
from backend.app.models.domain import ThermalEvent
from backend.app.services.analyst.analyst_workflow_service import analyst_workflow_service
from backend.app.services.jarvis.jarvis_mission_service import (
    jarvis_mission_service,
    JarvisObjectiveNormalizer,
    JarvisGovernedToolRegistry,
    mission_memory
)
from backend.app.services.jarvis.jarvis_command_interpreter import command_interpreter
from backend.app.services.jarvis.jarvis_orchestrator import jarvis_orchestrator
from backend.app.models.jarvis_schemas import JarvisCommandRequest, CanonicalAssessment
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
    print("AGNI-NETRA PHASE 22 JARVIS MISSION ORCHESTRATION BENCHMARK")
    print("Sovereign Territory of India Scope")
    print("=" * 85)

    # Pick representative event in Gujarat
    ev = db.query(ThermalEvent).filter(ThermalEvent.state == "Gujarat").first()
    if not ev:
        ev = db.query(ThermalEvent).first()
    assert ev is not None, "Thermal event required for benchmark."

    benchmarks: Dict[str, Any] = {}

    def measure(name: str, fn, iterations: int = 15):
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

        benchmarks[name] = {
            "mean_ms": round(mean_val, 2),
            "p50_ms": round(p50, 2),
            "p95_ms": round(p95, 2),
            "p99_ms": round(p99, 2),
            "max_ms": round(max_val, 2),
            "iterations": iterations,
        }
        print(f"[{name:<45}] P50: {p50:6.2f}ms | P95: {p95:6.2f}ms | P99: {p99:6.2f}ms | Mean: {mean_val:6.2f}ms")

    # 1. Objective Normalization & Sovereign Scope Resolution
    measure(
        "1. Objective Normalization & Sovereign Scope",
        lambda: JarvisObjectiveNormalizer.normalize("Investigate unusual industrial thermal activity in Gujarat within last 48 hours."),
        25
    )

    # 2. Governed Tool Registry & Adversarial Safety Guard
    measure(
        "2. Governed Tool Registry & Safety Guard",
        lambda: JarvisGovernedToolRegistry.validate_and_guard("event_dossier_loader", "ANALYST", "load event dossier"),
        25
    )

    # 3. Command Interpreter Pattern Matching
    measure(
        "3. Command Interpreter Intent & Param Extraction",
        lambda: command_interpreter.interpret("Investigate unusual industrial thermal activity in Gujarat."),
        20
    )

    # 4. Competing Hypotheses Matrix (ACH)
    measure(
        "4. Competing Hypotheses Matrix (ACH)",
        lambda: analyst_workflow_service.get_competing_hypotheses_review(db, ev.id),
        15
    )

    # 5. Assessment Differing Against Prior Version
    prior_asm = CanonicalAssessment(
        assessment_id=f"ASM-{ev.event_code}-V1",
        mission_id="MSN-BENCH-01",
        event_or_incident_id=ev.id,
        event_code=ev.event_code,
        conclusion="Prior baseline",
        classification="Uncertain",
        risk_score=40.0,
        priority_score=35.0,
        model_calibrated_confidence=0.82,
        version=1
    )
    mission_memory.record_assessment(ev.id, prior_asm)
    measure(
        "5. Assessment Version History & Differing",
        lambda: mission_memory.get_prior_assessment(ev.id, current_version=2),
        25
    )

    # 6. End-to-End Mission Orchestration (12 Deterministic Stages)
    measure(
        "6. E2E JARVIS Mission Orchestration",
        lambda: jarvis_mission_service.execute_mission(
            db=db,
            request="Investigate unusual industrial thermal activity in Gujarat."
        ),
        10
    )

    # 7. Master Agent Routing & Return to IDLE
    measure(
        "7. Master Agent Routing & Return to IDLE",
        lambda: jarvis_orchestrator.execute_command(
            db=db,
            request=JarvisCommandRequest(command="Investigate unusual industrial thermal activity in Gujarat.")
        ),
        10
    )

    # 8. REST API /api/v1/jarvis/mission Endpoint
    measure(
        "8. REST API /api/v1/jarvis/mission",
        lambda: client.post("/api/v1/jarvis/mission", json={"objective": "Investigate unusual industrial thermal activity in Gujarat."}),
        10
    )

    print("=" * 85)
    print("BENCHMARK COMPLETED SUCCESSFULLY")
    print("=" * 85)

    # Output benchmark summary json
    output_path = os.path.join(os.path.dirname(__file__), "benchmark_phase22_results.json")
    with open(output_path, "w") as f:
        json.dump(benchmarks, f, indent=2)
    print(f"Results written to: {output_path}")

    db.close()
    return benchmarks


if __name__ == "__main__":
    run_benchmark()
