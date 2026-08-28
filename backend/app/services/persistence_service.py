import math
from datetime import datetime, timezone
from typing import List, Dict, Any


def calculate_persistence_metrics(
    detections: List[Dict[str, Any]],
    current_time: datetime = None
) -> Dict[str, Any]:
    """
    Computes rigorous temporal persistence metrics for thermal observations at a site.
    
    Persistence Score Formula:
    P = log(1 + active_days) * (detection_count / max(1, span_days)) * (1 + 0.5 * night_ratio)
    """
    if not detections:
        return {
            "persistence_score": 0.0,
            "persistence_category": "TRANSIENT",
            "recurrence_rate": 0.0,
            "day_night_ratio": 0.0,
            "active_days_count": 0,
            "span_days": 0,
            "temporal_gaps_avg_days": 0.0
        }

    timestamps = sorted([
        d["acq_timestamp"] if isinstance(d["acq_timestamp"], datetime) 
        else datetime.fromisoformat(str(d["acq_timestamp"]))
        for d in detections
    ])
    
    unique_dates = {t.date() for t in timestamps}
    active_days_count = len(unique_dates)
    
    span_days = max(1, (timestamps[-1] - timestamps[0]).days + 1)
    recurrence_rate = round(len(detections) / float(span_days), 3)

    # Day / Night breakdown
    night_count = sum(1 for d in detections if d.get("day_night") == "N")
    day_count = len(detections) - night_count
    day_night_ratio = round(night_count / max(1, day_count), 2)

    # Temporal gap analysis
    if len(timestamps) > 1:
        gaps = [(timestamps[i] - timestamps[i-1]).total_seconds() / 86400.0 for i in range(1, len(timestamps))]
        avg_gap_days = round(float(sum(gaps) / len(gaps)), 2)
    else:
        avg_gap_days = 0.0

    # Persistence Score (normalized 0.0 to 10.0 range)
    raw_p = math.log1p(active_days_count) * min(3.0, (len(detections) / float(span_days))) * (1.0 + 0.4 * min(2.0, day_night_ratio))
    persistence_score = round(min(10.0, raw_p * 2.2), 2)

    if persistence_score >= 6.5 or active_days_count >= 14:
        persistence_category = "HIGHLY_PERSISTENT"
    elif persistence_score >= 3.5 or active_days_count >= 5:
        persistence_category = "PERSISTENT"
    elif persistence_score >= 1.2 or active_days_count >= 2:
        persistence_category = "RECURRING"
    else:
        persistence_category = "TRANSIENT"

    return {
        "persistence_score": persistence_score,
        "persistence_category": persistence_category,
        "recurrence_rate": recurrence_rate,
        "day_night_ratio": day_night_ratio,
        "active_days_count": active_days_count,
        "span_days": span_days,
        "temporal_gaps_avg_days": avg_gap_days
    }
