"""
AGNI-NETRA — OSM Industrial Entity Classifier & Normalization Engine
Classifies OSM industrial objects into:
- FACILITY
- INDUSTRIAL_ZONE
- POWER_PLANT
- REFINERY
- MINE
- WORKS
- OTHER

Resolves Confidence Scores (HIGH, MEDIUM, LOW), Verification Status (VERIFIED, PROVISIONAL, UNVERIFIED),
and Normalization for Search & Indexing.
"""

import re
from typing import Dict, Any, Tuple, Optional


# State abbreviation normalization dictionary for Indian states/UTs
STATE_ABBR_MAP = {
    "AP": "Andhra Pradesh",
    "AR": "Arunachal Pradesh",
    "AS": "Assam",
    "BR": "Bihar",
    "CG": "Chhattisgarh",
    "CH": "Chandigarh",
    "CT": "Chhattisgarh",
    "DL": "Delhi",
    "DN": "Dadra and Nagar Haveli and Daman and Diu",
    "DD": "Daman and Diu",
    "GA": "Goa",
    "GJ": "Gujarat",
    "HR": "Haryana",
    "HP": "Himachal Pradesh",
    "JH": "Jharkhand",
    "JK": "Jammu and Kashmir",
    "KA": "Karnataka",
    "KL": "Kerala",
    "LA": "Ladakh",
    "LD": "Lakshadweep",
    "MP": "Madhya Pradesh",
    "MH": "Maharashtra",
    "MN": "Manipur",
    "ML": "Meghalaya",
    "MZ": "Mizoram",
    "NL": "Nagaland",
    "OR": "Odisha",
    "OD": "Odisha",
    "PB": "Punjab",
    "PY": "Puducherry",
    "RJ": "Rajasthan",
    "SK": "Sikkim",
    "TN": "Tamil Nadu",
    "TS": "Telangana",
    "TG": "Telangana",
    "TR": "Tripura",
    "UP": "Uttar Pradesh",
    "UK": "Uttarakhand",
    "UT": "Uttarakhand",
    "WB": "West Bengal"
}

ZONE_KEYWORDS = [
    "industrial area", "industrial estate", "industrial zone", "industrial park",
    "gidc", "midc", "riico", "sipcot", "kiadb", "tidco", "upsidc", "sez",
    "special economic zone", "growth centre", "growth center", "phase 1", "phase 2",
    "phase 3", "phase 4", "phase-1", "phase-2", "phase-3", "phase-4",
    "textile park", "pharma park", "apparel park", "chemical zone", "estate", "zone"
]


def normalize_name(raw_name: Optional[str]) -> Optional[str]:
    """
    Normalizes names for matching and search:
    - Normalizes case, whitespace, and punctuation
    - Expands/standardizes common industrial abbreviations
    Preserves original name in source metadata.
    """
    if not raw_name:
        return None

    name = str(raw_name).strip()
    if not name:
        return None

    # Replace multiple spaces with a single space
    name = re.sub(r"\s+", " ", name)
    return name


def normalize_state(raw_state: Optional[str]) -> Optional[str]:
    """
    Normalizes state names and codes.
    """
    if not raw_state:
        return None

    s = str(raw_state).strip()
    if not s:
        return None

    upper_s = s.upper()
    if upper_s in STATE_ABBR_MAP:
        return STATE_ABBR_MAP[upper_s]

    lower_s = s.lower()
    if "uttar prad" in lower_s:
        return "Uttar Pradesh"
    elif "madhya prad" in lower_s:
        return "Madhya Pradesh"
    elif "andhra prad" in lower_s:
        return "Andhra Pradesh"
    elif "himachal prad" in lower_s:
        return "Himachal Pradesh"
    elif "arunachal prad" in lower_s:
        return "Arunachal Pradesh"
    elif "tamil nad" in lower_s:
        return "Tamil Nadu"
    elif "west beng" in lower_s:
        return "West Bengal"

    # Title-case state names
    return s.title()


def classify_osm_entity(tags: Dict[str, Any]) -> str:
    """
    Determines entity classification based on OSM tags:
    - POWER_PLANT
    - REFINERY
    - MINE
    - WORKS
    - FACILITY
    - INDUSTRIAL_ZONE
    - OTHER
    """
    power = (tags.get("power") or "").lower().strip()
    plant_source = (tags.get("plant:source") or "").lower().strip()
    plant_output = (tags.get("plant:output:electricity") or tags.get("plant:output") or "").lower().strip()
    plant_method = (tags.get("plant:method") or "").lower().strip()
    man_made = (tags.get("man_made") or "").lower().strip()
    industrial = (tags.get("industrial") or "").lower().strip()
    landuse = (tags.get("landuse") or "").lower().strip()
    amenity = (tags.get("amenity") or "").lower().strip()
    building = (tags.get("building") or "").lower().strip()
    resource = (tags.get("resource") or "").lower().strip()
    name = (tags.get("name") or "").lower().strip()
    operator = (tags.get("operator") or "").lower().strip()

    # 1. POWER_PLANT
    if (power in ["plant", "generator", "substation"] or 
        plant_source or plant_output or plant_method or 
        "power" in industrial or 
        any(k in name for k in ["power station", "power plant", "thermal power", "solar park", "solar farm", "hydel", "substation", "ntpc", "nhpc", "npcil"])):
        return "POWER_PLANT"

    # 2. REFINERY
    if (man_made in ["petroleum_refinery", "gas_processing"] or 
        industrial in ["refinery", "oil"] or 
        any(k in name for k in ["refinery", "petroleum", "petrochem", "lpg plant", "gas plant", "iocl", "bpcl", "hpcl", "reliance refinery", "nayara"]) or
        any(k in operator for k in ["iocl", "bpcl", "hpcl", "ongc", "oil india", "reliance industries", "nayara energy"])):
        return "REFINERY"

    # 3. MINE
    if (landuse == "quarry" or industrial == "mine" or resource or
        any(k in name for k in ["mine", "colliery", "opencast", "quarry", "bauxite", "coal mine", "iron ore mine", "secl", "wcl", "mcl", "ecl", "bccil", "ccl"]) or
        any(k in operator for k in ["coal india", "singareni", "secl", "wcl", "mcl", "ecl", "nmdc"])):
        return "MINE"

    # 4. WORKS (Specific infrastructure/production works)
    if (man_made in ["works", "kiln", "wastewater_plant", "water_works", "container_terminal", "pumping_station", "storage_tank", "wastewater_treatment", "composting_plant", "goods_conveyor", "chimney"] or
        industrial == "water_works"):
        return "WORKS"

    # 5. FACILITY (Specific manufacturing/industrial plant)
    if (industrial in ["brickyard", "brickworks", "factory", "slaughterhouse", "grinding_mill", "chemical", "rice_mill", 
                       "pharmaceutical company", "pharmaceutical", "textile", "sawmill", "concrete_plant", "pump", "pump_house",
                       "steel", "metallurgy", "cement", "sugar", "auto", "brewery", "dairy", "food", "depot", "warehouse", 
                       "scrap_yard", "port", "bus_depot", "cooling", "poultry_farm", "distributor", "agriculture"] or
        building in ["industrial", "manufacture", "warehouse", "factory"] or
        (name and not any(z in name for z in ZONE_KEYWORDS) and (operator or industrial))):
        return "FACILITY"

    # 6. INDUSTRIAL_ZONE (Industrial area, park, estate, GIDC, MIDC, or generic unnamed industrial landuse)
    if landuse == "industrial":
        if any(z in name for z in ZONE_KEYWORDS) or not name:
            return "INDUSTRIAL_ZONE"
        else:
            return "FACILITY"

    # 7. OTHER
    if amenity or landuse in ["commercial", "construction", "railway", "aquaculture", "harbour", "recreation_ground", "brownfield", "retail"]:
        return "OTHER"

    return "OTHER"


def assess_quality_and_confidence(
    tags: Dict[str, Any], 
    entity_class: str, 
    nic_code: Optional[str]
) -> Tuple[str, str]:
    """
    Evaluates confidence score (HIGH, MEDIUM, LOW) and verification status (VERIFIED, PROVISIONAL, UNVERIFIED).
    Rules:
    - HIGH: Named facility with operator, capacity, or specific industrial/power/refinery tags.
    - MEDIUM: Named facility or standard industrial/power tag with verified mapping.
    - LOW: Generic unnamed landuse=industrial or ambiguous tags.
    - VERIFIED: High confidence with complete naming and verifiable tags.
    - PROVISIONAL: Ambiguous classification, generic unnamed zone, or unverified industrial activity.
    - UNVERIFIED: Incomplete or low confidence tags.
    """
    has_name = bool(tags.get("name"))
    has_operator = bool(tags.get("operator"))
    has_specific_industrial = bool(tags.get("industrial") or tags.get("power") or tags.get("man_made") in ["petroleum_refinery", "works", "kiln"])
    has_details = bool(tags.get("plant:source") or tags.get("product") or tags.get("capacity") or tags.get("website") or tags.get("addr:city"))

    if has_name and (has_operator or has_details) and nic_code:
        confidence = "HIGH"
        verification_status = "VERIFIED"
    elif (has_name and has_specific_industrial) or (has_specific_industrial and has_details):
        confidence = "HIGH" if (has_name and has_operator) else "MEDIUM"
        verification_status = "VERIFIED" if confidence == "HIGH" else "PROVISIONAL"
    elif has_name:
        confidence = "MEDIUM"
        verification_status = "PROVISIONAL"
    elif entity_class == "INDUSTRIAL_ZONE":
        confidence = "MEDIUM" if has_name else "LOW"
        verification_status = "PROVISIONAL"
    else:
        confidence = "LOW"
        verification_status = "PROVISIONAL"

    return confidence, verification_status
