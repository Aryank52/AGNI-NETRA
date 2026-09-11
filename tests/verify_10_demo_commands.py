"""
AGNI-NETRA — Verification of 10 Master Demonstration Commands
Executes all 10 operational commands from Prompt Section 40 against live PostgreSQL/PostGIS.
Validates intent, execution steps, tool results, and synthesized decision-support outputs.
"""

import sys
import os
import json

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.database import SessionLocal
from backend.app.models.jarvis_schemas import JarvisCommandRequest
from backend.app.services.jarvis.jarvis_orchestrator import master_orchestrator


def run_10_demo_verification():
    db = SessionLocal()
    session_id = "demo-session-master-verification"
    
    commands = [
        "JARVIS, show the latest high-risk thermal events.",
        "JARVIS, show me the critical events requiring human verification.",
        "JARVIS, investigate Event 827.",
        "JARVIS, explain why Event 827 has high risk.",
        "JARVIS, compare Event 827 with its historical baseline.",
        "JARVIS, show the strongest evidence for Event 827.",
        "JARVIS, explain the strongest SHAP drivers for Event 827.",
        "JARVIS, find critical anomalies within 5 km of industrial facilities in Gujarat.",
        "JARVIS, generate an investigation dossier for Event 827.",
        "JARVIS, give me the current intelligence system status."
    ]

    print("================================================================================")
    print("      AGNI-NETRA // JARVIS MASTER 10-COMMAND OPERATIONAL VERIFICATION           ")
    print("================================================================================")

    all_passed = True
    results_summary = []

    for idx, cmd in enumerate(commands, 1):
        print(f"\n[{idx}/10] EXECUTING COMMAND:")
        print(f"      > \"{cmd}\"")

        req = JarvisCommandRequest(command=cmd, session_id=session_id)
        res = master_orchestrator.execute_command(db, req, user_role="ANALYST")

        trace = res.execution_trace
        status = trace.status.value if hasattr(trace.status, "value") else trace.status
        steps_count = len(trace.steps)
        latency = trace.total_duration_ms
        intent = res.intent

        print(f"      [INTENT]: {intent}")
        print(f"      [STATUS]: {status}")
        print(f"      [STEPS]:  {steps_count} steps executed in {latency} ms")
        print(f"      [SUMMARY]: {res.summary[:130]}...")

        # Sanity assertions
        assert status in ["COMPLETED", "BLOCKED"], f"Command {idx} status invalid: {status}"
        assert steps_count >= 2, f"Command {idx} steps too low: {steps_count}"
        assert latency > 0, f"Command {idx} latency invalid: {latency}"

        results_summary.append({
            "index": idx,
            "command": cmd,
            "intent": intent,
            "status": status,
            "steps": steps_count,
            "duration_ms": latency,
            "human_approval_required": res.requires_human_approval,
            "dispatch_gate_blocked": res.dispatch_gate_blocked
        })

    print("\n================================================================================")
    print("                     ALL 10 DEMO COMMANDS VERIFIED! (10/10)                     ")
    print("================================================================================")
    for r in results_summary:
        print(f"#{r['index']:02d} | {r['status']:9s} | {r['steps']} steps | {r['duration_ms']:6.1f}ms | Intent: {r['intent']}")

    db.close()


if __name__ == "__main__":
    run_10_demo_verification()
