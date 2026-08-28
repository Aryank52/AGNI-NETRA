from typing import Dict, Any, List, Tuple


def calculate_risk_score(
    max_frp: float,
    avg_frp: float,
    anomaly_info: Dict[str, Any],
    persistence_info: Dict[str, Any],
    nearest_settlement_dist_m: float = 2500.0,
    nearest_facility_dist_m: float = 5000.0,
    landcover_class: str = "Unknown",
    predicted_class: str = "Uncertain"
) -> Tuple[float, str, Dict[str, float], List[str]]:
    """
    Computes the transparent AGNI-NETRA Risk Score (0 - 100) and Risk Level.
    
    Formula:
    Risk = 0.30*S_intensity + 0.25*S_abnormality + 0.20*S_exposure + 0.15*S_persistence + 0.10*S_context
    """
    risk_reasons = []

    # 1. Thermal Intensity Subscore (0 - 100)
    # Scaled against industrial radiative power thresholds
    s_intensity = min(100.0, (max_frp / 250.0) * 80.0 + (avg_frp / 150.0) * 20.0)
    if max_frp >= 200.0:
        risk_reasons.append(f"Severe radiative heat output (Peak FRP: {max_frp:.1f} MW)")
    elif max_frp >= 80.0:
        risk_reasons.append(f"Elevated radiative intensity (Peak FRP: {max_frp:.1f} MW)")

    # 2. Abnormality Subscore (0 - 100)
    z_score = anomaly_info.get("z_score", 0.0)
    dev_ratio = anomaly_info.get("deviation_ratio", 1.0)
    if anomaly_info.get("is_anomaly"):
        s_abnormality = min(100.0, 40.0 + z_score * 20.0 + (dev_ratio - 1.0) * 15.0)
        risk_reasons.append(anomaly_info.get("explanation", "Significant thermal anomaly detected relative to baseline"))
    else:
        s_abnormality = 15.0

    # 3. Exposure & Surrounding Vulnerability Subscore (0 - 100)
    # Proximity to human settlements and critical infrastructure
    s_exposure = 20.0
    if nearest_settlement_dist_m < 500.0:
        s_exposure = 95.0
        risk_reasons.append(f"Immediate proximity to populated settlement (< {int(nearest_settlement_dist_m)}m)")
    elif nearest_settlement_dist_m < 1500.0:
        s_exposure = 70.0
        risk_reasons.append(f"Proximity to residential settlement ({int(nearest_settlement_dist_m)}m)")
    elif nearest_settlement_dist_m < 3000.0:
        s_exposure = 45.0

    # 4. Persistence Subscore (0 - 100)
    p_score = persistence_info.get("persistence_score", 0.0)
    s_persistence = min(100.0, p_score * 10.0)
    if p_score >= 6.5:
        risk_reasons.append("Chronic persistent thermal source with continuous multiday emissions")

    # 5. Industrial Context Subscore (0 - 100)
    s_context = 20.0
    if predicted_class in ["Industrial Fire", "Gas Flare"]:
        s_context = 80.0
        if nearest_facility_dist_m < 300.0:
            s_context = 90.0
            risk_reasons.append("Direct correlation with high-hazard industrial facility boundary")
    elif predicted_class == "Forest Fire":
        s_context = 65.0
        risk_reasons.append("Forest fire zone with potential ecological hazard")
    elif predicted_class == "Mining Activity":
        s_context = 50.0

    # Overall Weighted Score
    total_risk = (
        0.30 * s_intensity +
        0.25 * s_abnormality +
        0.20 * s_exposure +
        0.15 * s_persistence +
        0.10 * s_context
    )
    total_risk = round(min(100.0, max(0.0, total_risk)), 1)

    # Risk Level Categorization
    if total_risk >= 75.0 or (s_abnormality >= 85.0 and s_intensity >= 65.0):
        risk_level = "CRITICAL"
    elif total_risk >= 55.0:
        risk_level = "HIGH"
    elif total_risk >= 35.0:
        risk_level = "MODERATE"
    else:
        risk_level = "LOW"

    if not risk_reasons:
        risk_reasons.append("Thermal indicators within normal baseline operating range")

    subscores = {
        "intensity": round(s_intensity, 1),
        "abnormality": round(s_abnormality, 1),
        "exposure": round(s_exposure, 1),
        "persistence": round(s_persistence, 1),
        "context": round(s_context, 1)
    }

    return total_risk, risk_level, subscores, risk_reasons
