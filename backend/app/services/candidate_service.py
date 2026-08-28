from typing import Dict, Any, Tuple


def evaluate_candidate_industrial_source(
    event_info: Dict[str, Any],
    persistence_info: Dict[str, Any],
    landcover_class: str,
    nearest_dist_m: float
) -> Tuple[bool, float, Dict[str, Any]]:
    """
    Evaluates whether an uncataloged thermal anomaly meets candidate industrial source criteria.
    
    Formula for Industrial Context Score (0.0 to 1.0):
    - Persistence duration & score (30%)
    - Day/Night continuous burning signature (25%)
    - FRP intensity & stability (20%)
    - Non-forest/non-pure agriculture LULC context (15%)
    - Spatial stability (low centroid drift) (10%)
    """
    p_score = persistence_info.get("persistence_score", 0.0)
    p_cat = persistence_info.get("persistence_category", "TRANSIENT")
    active_days = persistence_info.get("active_days_count", 1)
    dn_ratio = persistence_info.get("day_night_ratio", 0.0)
    avg_frp = event_info.get("avg_frp", 0.0)
    
    # Sub-scores
    # 1. Persistence factor (0 - 0.30)
    s_persist = min(0.30, (p_score / 10.0) * 0.30)
    if active_days >= 7:
        s_persist = max(s_persist, 0.22)

    # 2. Continuous Day/Night factor (0 - 0.25)
    # Industrial stacks/flares burn at night; agriculture/forest fires are predominantly daytime
    if dn_ratio >= 0.6:
        s_diurnal = 0.25
    elif dn_ratio >= 0.3:
        s_diurnal = 0.15
    else:
        s_diurnal = 0.05

    # 3. Intensity factor (0 - 0.20)
    s_intensity = min(0.20, (avg_frp / 100.0) * 0.20)

    # 4. Landcover context (0 - 0.15)
    lc_lower = landcover_class.lower()
    if "industrial" in lc_lower or "built" in lc_lower or "urban" in lc_lower or "barren" in lc_lower:
        s_lulc = 0.15
    elif "mine" in lc_lower or "quarry" in lc_lower:
        s_lulc = 0.15
    elif "agriculture" in lc_lower:
        s_lulc = 0.04
    elif "forest" in lc_lower:
        s_lulc = 0.02
    else:
        s_lulc = 0.08

    # 5. Spatial isolation from known facilities (0 - 0.10)
    s_isolation = 0.10 if nearest_dist_m > 1500 else 0.04

    context_score = round(s_persist + s_diurnal + s_intensity + s_lulc + s_isolation, 2)
    is_candidate = (context_score >= 0.52 and active_days >= 3) or (dn_ratio >= 0.7 and p_score >= 3.0)

    evidence_summary = {
        "persistence_days": active_days,
        "persistence_category": p_cat,
        "day_night_ratio": dn_ratio,
        "is_continuous_24x7": dn_ratio >= 0.5,
        "landcover_context": landcover_class,
        "nearest_known_facility_dist_m": round(nearest_dist_m, 1),
        "supporting_indicators": []
    }

    if dn_ratio >= 0.5:
        evidence_summary["supporting_indicators"].append("High night-to-day detection ratio consistent with 24x7 industrial stack/flare activity")
    if active_days >= 5:
        evidence_summary["supporting_indicators"].append(f"Recurrent thermal activity detected across {active_days} separate observation days")
    if s_lulc >= 0.12:
        evidence_summary["supporting_indicators"].append(f"Location aligns with '{landcover_class}' land-use category")

    return is_candidate, context_score, evidence_summary
