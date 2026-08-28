import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple

FEATURE_COLUMNS = [
    "frp_max",
    "frp_avg",
    "frp_std",
    "bright_max",
    "bright_avg",
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
    "Forest": 5,
    "Barren / Scrub": 6,
    "Water Body": 7,
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


def extract_feature_vector(event_data: Dict[str, Any], spatial_context: Dict[str, Any] = None) -> np.ndarray:
    """
    Extracts an ordered feature vector from raw event metrics and spatial context.
    """
    if spatial_context is None:
        spatial_context = {}

    frp_max = float(event_data.get("max_frp", 0.0))
    frp_avg = float(event_data.get("avg_frp", 0.0))
    frp_std = float(event_data.get("frp_variance", 0.0) ** 0.5)
    bright_max = float(event_data.get("avg_brightness", 320.0) * 1.05)
    bright_avg = float(event_data.get("avg_brightness", 320.0))
    
    dist_to_facility = float(event_data.get("nearest_facility_distance_m") or spatial_context.get("dist_to_facility_m", 99999.0))
    dist_to_forest = float(spatial_context.get("dist_to_forest_m", 50000.0))
    dist_to_agri = float(spatial_context.get("dist_to_agriculture_m", 20000.0))
    dist_to_settle = float(spatial_context.get("dist_to_settlement_m", 15000.0))
    dist_to_water = float(spatial_context.get("dist_to_water_m", 25000.0))
    dist_to_mine = float(spatial_context.get("dist_to_mine_m", 80000.0))
    
    lc_name = event_data.get("landcover_class", "Unknown")
    lc_code = LANDCOVER_MAPPING.get(lc_name, 0)
    
    p_score = float(event_data.get("persistence_score", 0.0))
    rec_rate = float(event_data.get("recurrence_rate", 0.0))
    dn_ratio = float(event_data.get("day_night_ratio", 0.0))
    dev_ratio = float(event_data.get("baseline_deviation_ratio", 1.0))
    ind_context = float(event_data.get("industrial_context_score", 0.0))

    vec = [
        frp_max,
        frp_avg,
        frp_std,
        bright_max,
        bright_avg,
        dist_to_facility,
        dist_to_forest,
        dist_to_agri,
        dist_to_settle,
        dist_to_water,
        dist_to_mine,
        lc_code,
        p_score,
        rec_rate,
        dn_ratio,
        dev_ratio,
        ind_context
    ]

    return np.array([vec], dtype=np.float32)
