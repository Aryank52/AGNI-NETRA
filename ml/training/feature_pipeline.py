import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple, Optional

FEATURE_COLUMNS = [
    "frp_max",
    "frp_avg",
    "frp_std",
    "bright_max",
    "bright_avg",
    "delta_brightness",
    "dist_to_facility_m",
    "dist_to_forest_m",
    "dist_to_agriculture_m",
    "dist_to_settlement_m",
    "dist_to_water_m",
    "dist_to_mine_m",
    "landcover_code",
    "persistence_score",
    "recurrence_rate",
    "day_night_ratio",
    "baseline_deviation_ratio",
    "industrial_context_score"
]

LANDCOVER_MAPPING = {
    "Industrial": 1,
    "Mining": 2,
    "Urban / Built-up": 3,
    "Settlement": 3,
    "Agriculture / Cropland": 4,
    "Agricultural": 4,
    "Forest": 5,
    "Barren / Scrub": 6,
    "Barren": 6,
    "Water Body": 7,
    "Water": 7,
    "Unknown": 0
}

CLASS_NAMES = [
    "Industrial Fire",
    "Gas Flare",
    "Forest Fire",
    "Agricultural Burning",
    "Mining Activity",
    "Other Thermal Source",
    "Uncertain"
]


def extract_feature_vector(
    event_data: Dict[str, Any],
    spatial_context: Optional[Dict[str, Any]] = None
) -> np.ndarray:
    """
    Extracts an ordered 18-dimensional feature vector from thermal observations and spatial context.
    Features:
    - 1-6: Thermal radiative & temperature metrics (FRP max, avg, std, Brightness max, avg, delta)
    - 7-12: Proximity to key land use & physical assets (facility, forest, agriculture, settlement, water, mine)
    - 13: Land-use land-cover code (ISRO Bhuvan / ESA WorldCover)
    - 14-16: Spatiotemporal persistence & diurnal metrics (persistence score, recurrence rate, day/night ratio)
    - 17-18: Contextual deviation & industrial affinity (baseline deviation ratio, industrial context score)
    """
    if spatial_context is None:
        spatial_context = {}

    # 1. Thermal Radiative Features
    frp_max = float(event_data.get("max_frp", event_data.get("frp_max", 0.0)))
    frp_avg = float(event_data.get("avg_frp", event_data.get("frp_avg", 0.0)))
    frp_std = float(event_data.get("frp_std", event_data.get("frp_variance", 0.0) ** 0.5))
    
    b_avg = float(event_data.get("avg_brightness", event_data.get("bright_avg", 320.0)))
    b_max = float(event_data.get("bright_max", b_avg * 1.05))
    delta_brightness = max(0.0, b_max - b_avg)

    # 2. Spatial Proximity Features (in meters)
    dist_facility = float(event_data.get("nearest_facility_distance_m") or spatial_context.get("dist_to_facility_m", 99999.0))
    dist_forest = float(event_data.get("nearest_forest_distance_m") or spatial_context.get("dist_to_forest_m", 50000.0))
    dist_agri = float(event_data.get("nearest_agri_distance_m") or spatial_context.get("dist_to_agriculture_m", spatial_context.get("dist_to_agri_m", 20000.0)))
    dist_settlement = float(event_data.get("nearest_settlement_distance_m") or spatial_context.get("dist_to_settlement_m", 15000.0))
    dist_water = float(event_data.get("nearest_water_distance_m") or spatial_context.get("dist_to_water_m", 25000.0))
    dist_mine = float(event_data.get("nearest_mine_distance_m") or spatial_context.get("dist_to_mine_m", 80000.0))

    # 3. LULC Categorical Code
    lc_name = event_data.get("landcover_class", spatial_context.get("landcover_class", "Unknown"))
    lc_code = LANDCOVER_MAPPING.get(lc_name, 0)

    # 4. Spatiotemporal & Diurnal Features
    p_score = float(event_data.get("persistence_score", spatial_context.get("persistence_score", 0.0)))
    rec_rate = float(event_data.get("recurrence_rate", spatial_context.get("recurrence_rate", 0.0)))
    dn_ratio = float(event_data.get("day_night_ratio", spatial_context.get("day_night_ratio", 1.0)))

    # 5. Baseline & Industrial Context Features
    dev_ratio = float(event_data.get("baseline_deviation_ratio", spatial_context.get("baseline_deviation_ratio", 1.0)))
    ind_context = float(event_data.get("industrial_context_score", spatial_context.get("industrial_context_score", 0.5)))

    vec = [
        frp_max,
        frp_avg,
        frp_std,
        b_max,
        b_avg,
        delta_brightness,
        dist_facility,
        dist_forest,
        dist_agri,
        dist_settlement,
        dist_water,
        dist_mine,
        lc_code,
        p_score,
        rec_rate,
        dn_ratio,
        dev_ratio,
        ind_context
    ]

    return np.array([vec], dtype=np.float32)


def calculate_prediction_uncertainty(probabilities: np.ndarray) -> float:
    """
    Computes normalized Shannon entropy as an exact measure of classification uncertainty.
    Output bounded in [0.0, 1.0]:
    - 0.0 = completely certain (100% probability assigned to one class)
    - 1.0 = maximum uncertainty (uniform probability distribution across all 7 classes)
    """
    probs = np.clip(probabilities, 1e-12, 1.0)
    k = len(probs)
    if k <= 1:
        return 0.0
    entropy = -np.sum(probs * np.log2(probs))
    max_entropy = np.log2(k)
    return float(np.clip(entropy / max_entropy, 0.0, 1.0))
