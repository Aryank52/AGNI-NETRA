import sys
sys.stdout.reconfigure(line_buffering=True, encoding='utf-8')
sys.path.insert(0, r"E:\PROJECTS\AGNI-NETRA")
from backend.app.core.database import SessionLocal
from backend.app.models.jarvis_schemas import JarvisCommandRequest
from backend.app.services.jarvis.jarvis_orchestrator import master_orchestrator

db = SessionLocal()

tests = [
    ("Section 20 Complex Acceptance", "JARVIS, identify the most concerning thermal event near an industrial facility, investigate it, determine whether the evidence strongly supports an industrial fire, explain any conflicting evidence, tell me what remains uncertain, and determine whether human verification is required."),
    ("Analyst Prioritization", "JARVIS, identify the events that deserve analyst attention first."),
    ("Priority Explanation", "JARVIS, explain why the winner is stronger."),
    ("Multi-Constraint Search 1", "JARVIS, show high-risk events with low classification confidence."),
    ("Multi-Constraint Search 2", "JARVIS, find persistent thermal anomalies near industrial facilities."),
    ("Evidence Conflict Detection", "JARVIS, find events where historical behavior conflicts with the current classification."),
    ("Evidence Strength Assessment", "JARVIS, how strong is the evidence?"),
    ("Uncertainty Assessment", "JARVIS, what are we still uncertain about?"),
    ("What Could Change", "JARVIS, what evidence could change the conclusion?"),
    ("Operator Intelligence Summary", "JARVIS, summarize current intelligence.")
]

session_id = "test-phase5-session-001"
inv_id = None

for name, cmd in tests:
    print(f"\n==================================================")
    print(f"RUNNING: {name}")
    print(f"COMMAND: {cmd[:60]}...")
    req = JarvisCommandRequest(command=cmd, session_id=session_id, investigation_id=inv_id)
    res = master_orchestrator.execute_command(db, req)
    if res.investigation_id:
        inv_id = res.investigation_id
    print(f"STOPPING REASON: {res.stopping_reason}")
    print(f"CAPABILITIES: {res.capabilities_used}")
    print(f"REQUIRES APPROVAL: {res.requires_human_approval}")
    print(f"DISPATCH BLOCKED: {res.dispatch_gate_blocked}")
    print(f"EVIDENCE STRENGTH: {res.evidence_strength}")
    c_cnt = len(res.evidence_conflicts or res.conflicts or [])
    print(f"CONFLICTS COUNT: {c_cnt}")
    u_pres = (res.uncertainty_assessment is not None) or bool(res.uncertainty)
    print(f"UNCERTAINTY PRESENT: {u_pres}")
    w_cnt = len(res.what_could_change or (res.uncertainty.get("what_could_change") if isinstance(res.uncertainty, dict) else []) or [])
    print(f"WHAT COULD CHANGE COUNT: {w_cnt}")
    print(f"OPERATOR SUMMARY PRESENT: {res.operator_summary is not None}")
    print(f"SUMMARY PREVIEW:\n{res.summary[:200]}...")

print("\nALL 10 ORCHESTRATOR TESTS COMPLETED!")
db.close()
