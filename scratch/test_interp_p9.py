import sys
sys.path.insert(0, ".")
from backend.app.services.jarvis.jarvis_command_interpreter import command_interpreter

commands = [
    ("JARVIS, analyze the historical baseline and temporal behavior for EVT-827", "SECTION_26_PHASE9_ACCEPTANCE"),
    ("JARVIS, what is the historical baseline for EVT-827?", "ANALYZE_HISTORICAL_BEHAVIOR"),
    ("JARVIS, is this event persistent?", "DETERMINE_PERSISTENCE"),
    ("JARVIS, has this location burned or flared before?", "DETERMINE_RECURRENCE"),
    ("JARVIS, compare this event to historical baseline", "COMPARE_HISTORICAL_BASELINE"),
    ("JARVIS, is this an anomalous deviation or routine activity?", "DETERMINE_TEMPORAL_ANOMALY"),
    ("JARVIS, does this event follow a seasonal pattern?", "DETERMINE_SEASONALITY"),
    ("JARVIS, show day versus night behavior for this location", "SHOW_DAY_NIGHT_BEHAVIOR"),
    ("JARVIS, explain the temporal evidence for this event", "EXPLAIN_TEMPORAL_EVIDENCE"),
    ("JARVIS, what historical data is missing?", "SHOW_MISSING_HISTORICAL_DATA"),
    ("JARVIS, what observations would reduce temporal uncertainty?", "REDUCE_TEMPORAL_UNCERTAINTY"),
    ("JARVIS, combine all thermal, contextual, and temporal evidence for EVT-827", "COMBINE_ALL_EVIDENCE"),
    ("JARVIS, show the temporal evidence provenance", "TEMPORAL_PROVENANCE"),
    ("JARVIS, what temporal coverage is available for this event?", "TEMPORAL_COVERAGE")
]

for cmd, exp in commands:
    parsed = command_interpreter.interpret(cmd)
    obj = parsed.get("objective")
    pg = obj.primary_goal if obj else None
    res = "OK" if pg == exp else f"FAIL (got {pg})"
    print(f"{cmd} -> {res}")
