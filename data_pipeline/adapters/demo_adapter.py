import random
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any
from data_pipeline.adapters.base import NormalizedThermalObservation

# Canonical Real-World Ground Truth Hubs in India
DEMO_INDUSTRIAL_HUBS = [
    {
        "name": "Reliance Jamnagar Mega Refinery & Petrochemical Complex",
        "facility_type": "REFINERY",
        "state": "Gujarat",
        "district": "Jamnagar",
        "latitude": 22.3552,
        "longitude": 69.8658,
        "mean_frp": 125.0,
        "std_frp": 25.0,
        "day_night_ratio": 1.2,
        "operating_hours": "24x7",
        "landcover": "Industrial",
        "expected_class": "Gas Flare",
        "is_abnormal": False
    },
    {
        "name": "NTPC Singrauli Super Thermal Power Station",
        "facility_type": "POWER_PLANT",
        "state": "Madhya Pradesh",
        "district": "Singrauli",
        "latitude": 24.1032,
        "longitude": 82.6841,
        "mean_frp": 85.0,
        "std_frp": 18.0,
        "day_night_ratio": 0.95,
        "operating_hours": "24x7",
        "landcover": "Industrial",
        "expected_class": "Industrial Fire",
        "is_abnormal": True  # Seeded abnormal spike!
    },
    {
        "name": "Korba Coal Mining & Thermal Belt (SECL / NTPC)",
        "facility_type": "MINING",
        "state": "Chhattisgarh",
        "district": "Korba",
        "latitude": 22.3595,
        "longitude": 82.7501,
        "mean_frp": 45.0,
        "std_frp": 12.0,
        "day_night_ratio": 0.75,
        "operating_hours": "24x7",
        "landcover": "Mining",
        "expected_class": "Mining Activity",
        "is_abnormal": False
    },
    {
        "name": "JSPL Angul Integrated Steel Plant",
        "facility_type": "STEEL_PLANT",
        "state": "Odisha",
        "district": "Angul",
        "latitude": 20.8402,
        "longitude": 85.1205,
        "mean_frp": 110.0,
        "std_frp": 22.0,
        "day_night_ratio": 1.1,
        "operating_hours": "24x7",
        "landcover": "Industrial",
        "expected_class": "Industrial Fire",
        "is_abnormal": False
    },
    {
        "name": "ONGC Tatipaka Gas Flaring Station (KG Basin)",
        "facility_type": "REFINERY",
        "state": "Andhra Pradesh",
        "district": "East Godavari",
        "latitude": 16.5184,
        "longitude": 81.8682,
        "mean_frp": 65.0,
        "std_frp": 14.0,
        "day_night_ratio": 1.4,
        "operating_hours": "24x7",
        "landcover": "Industrial",
        "expected_class": "Gas Flare",
        "is_abnormal": False
    },
    {
        "name": "SAIL Bokaro Steel Plant",
        "facility_type": "STEEL_PLANT",
        "state": "Jharkhand",
        "district": "Bokaro",
        "latitude": 23.6693,
        "longitude": 86.1511,
        "mean_frp": 95.0,
        "std_frp": 20.0,
        "day_night_ratio": 1.0,
        "operating_hours": "24x7",
        "landcover": "Industrial",
        "expected_class": "Industrial Fire",
        "is_abnormal": False
    }
]

# Non-Industrial Control Locations
DEMO_NON_INDUSTRIAL_ZONES = [
    {
        "name_desc": "Sangrur Agricultural Belt (Crop Stubble Burning)",
        "state": "Punjab",
        "district": "Sangrur",
        "latitude": 30.2450,
        "longitude": 75.8420,
        "landcover": "Agriculture / Cropland",
        "expected_class": "Agricultural Burning",
        "day_night_ratio": 0.05,
        "avg_frp": 28.0
    },
    {
        "name_desc": "Bathinda Agricultural Region",
        "state": "Punjab",
        "district": "Bathinda",
        "latitude": 30.2110,
        "longitude": 74.9455,
        "landcover": "Agriculture / Cropland",
        "expected_class": "Agricultural Burning",
        "day_night_ratio": 0.08,
        "avg_frp": 32.0
    },
    {
        "name_desc": "Similipal Biosphere Reserve Forest Fire Sector",
        "state": "Odisha",
        "district": "Mayurbhanj",
        "latitude": 21.8650,
        "longitude": 86.3420,
        "landcover": "Forest",
        "expected_class": "Forest Fire",
        "day_night_ratio": 0.15,
        "avg_frp": 85.0
    },
    {
        "name_desc": "Western Ghats High Canopy Fire Zone",
        "state": "Karnataka",
        "district": "Uttara Kannada",
        "latitude": 14.8520,
        "longitude": 74.6530,
        "landcover": "Forest",
        "expected_class": "Forest Fire",
        "day_night_ratio": 0.12,
        "avg_frp": 60.0
    }
]

# Unknown Candidate Hotspot (Triggers Candidate Facility Engine)
DEMO_CANDIDATE_ZONES = [
    {
        "name_label": "Candidate-Thermal-Source-GJ-Ankleshwar-SEZ",
        "state": "Gujarat",
        "district": "Bharuch",
        "latitude": 21.6280,
        "longitude": 73.0150,
        "landcover": "Barren / Scrub",
        "expected_class": "Industrial Fire",
        "day_night_ratio": 0.85,
        "avg_frp": 72.0
    }
]


def generate_seed_observations() -> List[NormalizedThermalObservation]:
    """
    Generates deterministic, physically realistic multi-temporal satellite thermal observations.
    """
    random.seed(42)
    observations = []
    now = datetime.now(timezone.utc)

    # 1. Industrial Hub Observations (multi-day, 24x7)
    for hub in DEMO_INDUSTRIAL_HUBS:
        # Generate 15 distinct satellite passes over the last 10 days
        for i in range(15):
            days_ago = random.uniform(0.1, 9.5)
            pass_time = now - timedelta(days=days_ago)
            
            # Diurnal determination
            is_night = random.random() < (hub["day_night_ratio"] / (1.0 + hub["day_night_ratio"]))
            dn = "N" if is_night else "D"

            # FRP calculation with potential anomaly injection
            frp = random.gauss(hub["mean_frp"], hub["std_frp"])
            if hub["is_abnormal"] and days_ago < 2.0:
                frp = hub["mean_frp"] * 2.85  # +3.5 sigma spike!
            
            frp = max(5.0, round(frp, 1))
            lat_jitter = hub["latitude"] + random.gauss(0, 0.003)
            lon_jitter = hub["longitude"] + random.gauss(0, 0.003)

            obs = NormalizedThermalObservation(
                source_record_id=f"DEMO_{hub['facility_type']}_{hub['state'][:2]}_{i+1:03d}",
                source="FIRMS",
                sensor="VIIRS_NOAA20",
                satellite="NOAA-20",
                latitude=round(lat_jitter, 5),
                longitude=round(lon_jitter, 5),
                acq_timestamp=pass_time,
                brightness=round(330.0 + frp * 0.45, 1),
                bright_t31=round(295.0 + frp * 0.15, 1),
                frp=frp,
                confidence=round(random.uniform(85.0, 99.0), 1),
                day_night=dn,
                metadata={"facility_target": hub["name"], "is_demo": True},
                is_demo=True
            )
            observations.append(obs)

    # 2. Non-Industrial Observations (stubble + forest)
    for zone in DEMO_NON_INDUSTRIAL_ZONES:
        for i in range(6):
            days_ago = random.uniform(0.1, 4.0)
            pass_time = now - timedelta(days=days_ago)
            
            is_night = random.random() < zone["day_night_ratio"]
            dn = "N" if is_night else "D"
            frp = max(5.0, round(random.gauss(zone["avg_frp"], 8.0), 1))
            
            lat_jitter = zone["latitude"] + random.gauss(0, 0.015)
            lon_jitter = zone["longitude"] + random.gauss(0, 0.015)

            obs = NormalizedThermalObservation(
                source_record_id=f"DEMO_ENV_{zone['state'][:2]}_{i+1:03d}",
                source="FIRMS",
                sensor="VIIRS_SNPP",
                satellite="Suomi-NPP",
                latitude=round(lat_jitter, 5),
                longitude=round(lon_jitter, 5),
                acq_timestamp=pass_time,
                brightness=round(315.0 + frp * 0.35, 1),
                bright_t31=round(290.0 + frp * 0.1, 1),
                frp=frp,
                confidence=round(random.uniform(70.0, 95.0), 1),
                day_night=dn,
                metadata={"zone_desc": zone["name_desc"], "is_demo": True},
                is_demo=True
            )
            observations.append(obs)

    # 3. Candidate Discovery Zone Observations
    for cand in DEMO_CANDIDATE_ZONES:
        for i in range(10):
            days_ago = random.uniform(0.2, 8.0)
            pass_time = now - timedelta(days=days_ago)
            is_night = random.random() < cand["day_night_ratio"]
            dn = "N" if is_night else "D"
            frp = max(10.0, round(random.gauss(cand["avg_frp"], 12.0), 1))
            
            lat_jitter = cand["latitude"] + random.gauss(0, 0.002)
            lon_jitter = cand["longitude"] + random.gauss(0, 0.002)

            obs = NormalizedThermalObservation(
                source_record_id=f"DEMO_CAND_{cand['state'][:2]}_{i+1:03d}",
                source="FIRMS",
                sensor="VIIRS_NOAA20",
                satellite="NOAA-20",
                latitude=round(lat_jitter, 5),
                longitude=round(lon_jitter, 5),
                acq_timestamp=pass_time,
                brightness=round(340.0 + frp * 0.4, 1),
                bright_t31=round(298.0 + frp * 0.12, 1),
                frp=frp,
                confidence=round(random.uniform(88.0, 98.0), 1),
                day_night=dn,
                metadata={"candidate_label": cand["name_label"], "is_demo": True},
                is_demo=True
            )
            observations.append(obs)

    return observations
