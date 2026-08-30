"""
AGNI-NETRA — Official NIC-2008 (National Industrial Classification) Taxonomy & Mapping Engine
Maps OpenStreetMap tags and industrial attributes to official 5-digit / 4-digit NIC-2008 codes,
Master Sectors, and Sub-Sectors.
"""

from typing import Dict, Any, Optional, Tuple


NIC_2008_TAXONOMY = {
    # Division 05 - Mining of Coal and Lignite
    "0510": {
        "nic_code": "0510",
        "master_sector": "Mining and Quarrying",
        "sub_sector": "Mining of Coal and Lignite",
        "industry_type": "Coal Mining & Extraction"
    },
    "0520": {
        "nic_code": "0520",
        "master_sector": "Mining and Quarrying",
        "sub_sector": "Mining of Coal and Lignite",
        "industry_type": "Lignite Mining"
    },
    # Division 07 - Mining of Metal Ores
    "0710": {
        "nic_code": "0710",
        "master_sector": "Mining and Quarrying",
        "sub_sector": "Mining of Metal Ores",
        "industry_type": "Iron Ore Mining"
    },
    "0729": {
        "nic_code": "0729",
        "master_sector": "Mining and Quarrying",
        "sub_sector": "Mining of Metal Ores",
        "industry_type": "Non-Ferrous Metal Ore Mining (Bauxite/Copper/Uranium)"
    },
    # Division 08 - Other Mining and Quarrying
    "0810": {
        "nic_code": "0810",
        "master_sector": "Mining and Quarrying",
        "sub_sector": "Other Mining and Quarrying",
        "industry_type": "Quarrying of Stone, Sand and Clay"
    },
    "0899": {
        "nic_code": "0899",
        "master_sector": "Mining and Quarrying",
        "sub_sector": "Other Mining and Quarrying",
        "industry_type": "Mining and Quarrying n.e.c."
    },
    # Division 10 - Manufacture of Food Products
    "1010": {
        "nic_code": "1010",
        "master_sector": "Manufacturing",
        "sub_sector": "Food Processing",
        "industry_type": "Processing & Preserving of Meat / Slaughterhouse"
    },
    "1040": {
        "nic_code": "1040",
        "master_sector": "Manufacturing",
        "sub_sector": "Food Processing",
        "industry_type": "Manufacture of Vegetable & Edible Oils"
    },
    "1050": {
        "nic_code": "1050",
        "master_sector": "Manufacturing",
        "sub_sector": "Food Processing",
        "industry_type": "Dairy Products Manufacturing"
    },
    "1061": {
        "nic_code": "1061",
        "master_sector": "Manufacturing",
        "sub_sector": "Food Processing",
        "industry_type": "Grain Milling (Rice Mill / Flour Mill)"
    },
    "1072": {
        "nic_code": "1072",
        "master_sector": "Manufacturing",
        "sub_sector": "Food Processing",
        "industry_type": "Sugar Manufacturing"
    },
    "1079": {
        "nic_code": "1079",
        "master_sector": "Manufacturing",
        "sub_sector": "Food Processing",
        "industry_type": "Food Products Manufacturing (Tea / Bakery / Spices)"
    },
    # Division 11 - Manufacture of Beverages
    "1101": {
        "nic_code": "1101",
        "master_sector": "Manufacturing",
        "sub_sector": "Beverages",
        "industry_type": "Distilling, Rectifying & Blending of Spirits"
    },
    "1103": {
        "nic_code": "1103",
        "master_sector": "Manufacturing",
        "sub_sector": "Beverages",
        "industry_type": "Brewery / Manufacture of Malt Liquors & Beer"
    },
    "1104": {
        "nic_code": "1104",
        "master_sector": "Manufacturing",
        "sub_sector": "Beverages",
        "industry_type": "Soft Drinks & Mineral Water Production"
    },
    # Division 13 - Manufacture of Textiles
    "1311": {
        "nic_code": "1311",
        "master_sector": "Manufacturing",
        "sub_sector": "Textiles",
        "industry_type": "Spinning, Weaving & Finishing of Textiles"
    },
    # Division 14 - Wearing Apparel
    "1410": {
        "nic_code": "1410",
        "master_sector": "Manufacturing",
        "sub_sector": "Apparel & Garments",
        "industry_type": "Manufacture of Wearing Apparel"
    },
    # Division 15 - Leather
    "1511": {
        "nic_code": "1511",
        "master_sector": "Manufacturing",
        "sub_sector": "Leather & Footwear",
        "industry_type": "Tanning and Dressing of Leather"
    },
    # Division 16 - Wood & Wood Products
    "1610": {
        "nic_code": "1610",
        "master_sector": "Manufacturing",
        "sub_sector": "Wood & Furniture",
        "industry_type": "Sawmilling and Planing of Wood"
    },
    # Division 17 - Paper & Paper Products
    "1701": {
        "nic_code": "1701",
        "master_sector": "Manufacturing",
        "sub_sector": "Paper & Pulp",
        "industry_type": "Manufacture of Pulp, Paper and Paperboard"
    },
    # Division 19 - Petroleum Refining & Coke
    "1920": {
        "nic_code": "1920",
        "master_sector": "Manufacturing",
        "sub_sector": "Petroleum & Petrochemicals",
        "industry_type": "Manufacture of Refined Petroleum Products (Refinery)"
    },
    # Division 20 - Chemicals & Chemical Products
    "2011": {
        "nic_code": "2011",
        "master_sector": "Manufacturing",
        "sub_sector": "Chemicals & Fertilizers",
        "industry_type": "Basic Chemicals & Petrochemicals"
    },
    "2012": {
        "nic_code": "2012",
        "master_sector": "Manufacturing",
        "sub_sector": "Chemicals & Fertilizers",
        "industry_type": "Manufacture of Fertilizers and Nitrogen Compounds"
    },
    "2029": {
        "nic_code": "2029",
        "master_sector": "Manufacturing",
        "sub_sector": "Chemicals & Fertilizers",
        "industry_type": "Industrial Gases (Oxygen/Nitrogen) & Chemical Products"
    },
    # Division 21 - Pharmaceuticals
    "2100": {
        "nic_code": "2100",
        "master_sector": "Manufacturing",
        "sub_sector": "Pharmaceuticals & Biotechnology",
        "industry_type": "Manufacture of Pharmaceuticals and Medicinal Products"
    },
    # Division 22 - Rubber & Plastics
    "2211": {
        "nic_code": "2211",
        "master_sector": "Manufacturing",
        "sub_sector": "Rubber & Plastics",
        "industry_type": "Manufacture of Rubber Tyres and Products"
    },
    "2220": {
        "nic_code": "2220",
        "master_sector": "Manufacturing",
        "sub_sector": "Rubber & Plastics",
        "industry_type": "Manufacture of Plastics Products"
    },
    # Division 23 - Non-Metallic Mineral Products
    "2392": {
        "nic_code": "2392",
        "master_sector": "Manufacturing",
        "sub_sector": "Non-Metallic Mineral Products",
        "industry_type": "Clay Building Materials (Brickyard / Brickworks / Kiln)"
    },
    "2394": {
        "nic_code": "2394",
        "master_sector": "Manufacturing",
        "sub_sector": "Non-Metallic Mineral Products",
        "industry_type": "Manufacture of Cement, Lime and Plaster"
    },
    "2395": {
        "nic_code": "2395",
        "master_sector": "Manufacturing",
        "sub_sector": "Non-Metallic Mineral Products",
        "industry_type": "Manufacture of Concrete, Ready-Mix & Cement Articles"
    },
    # Division 24 - Basic Metals & Metallurgy
    "2410": {
        "nic_code": "2410",
        "master_sector": "Manufacturing",
        "sub_sector": "Basic Metals & Metallurgy",
        "industry_type": "Manufacture of Basic Iron and Steel"
    },
    "2420": {
        "nic_code": "2420",
        "master_sector": "Manufacturing",
        "sub_sector": "Basic Metals & Metallurgy",
        "industry_type": "Non-Ferrous Metals Metallurgy (Aluminium, Zinc, Copper)"
    },
    # Division 28 - Machinery & Equipment
    "2813": {
        "nic_code": "2813",
        "master_sector": "Manufacturing",
        "sub_sector": "Machinery & Capital Goods",
        "industry_type": "Manufacture of Pumps, Compressors, Valves & Motors"
    },
    # Division 29 - Automotive
    "2910": {
        "nic_code": "2910",
        "master_sector": "Manufacturing",
        "sub_sector": "Automotive",
        "industry_type": "Manufacture of Motor Vehicles and Parts"
    },
    # Division 35 - Electricity, Gas and Air Conditioning Supply
    "35101": {
        "nic_code": "35101",
        "master_sector": "Electricity, Gas and Water Supply",
        "sub_sector": "Thermal Power Generation",
        "industry_type": "Thermal Electric Power Generation (Coal / Gas / Diesel)"
    },
    "35102": {
        "nic_code": "35102",
        "master_sector": "Electricity, Gas and Water Supply",
        "sub_sector": "Hydro-electric Power Generation",
        "industry_type": "Hydro-Electric Power Generation"
    },
    "35103": {
        "nic_code": "35103",
        "master_sector": "Electricity, Gas and Water Supply",
        "sub_sector": "Nuclear Power Generation",
        "industry_type": "Nuclear Electric Power Generation"
    },
    "35104": {
        "nic_code": "35104",
        "master_sector": "Electricity, Gas and Water Supply",
        "sub_sector": "Solar Power Generation",
        "industry_type": "Solar Photovoltaic / Solar Thermal Power Generation"
    },
    "35105": {
        "nic_code": "35105",
        "master_sector": "Electricity, Gas and Water Supply",
        "sub_sector": "Wind Power Generation",
        "industry_type": "Wind Electric Power Generation"
    },
    "35106": {
        "nic_code": "35106",
        "master_sector": "Electricity, Gas and Water Supply",
        "sub_sector": "Biomass & Renewable Power",
        "industry_type": "Biomass, Biogas & Waste-to-Energy Power Generation"
    },
    "35107": {
        "nic_code": "35107",
        "master_sector": "Electricity, Gas and Water Supply",
        "sub_sector": "Transmission and Distribution",
        "industry_type": "Electric Power Transmission & Substation"
    },
    "35200": {
        "nic_code": "35200",
        "master_sector": "Electricity, Gas and Water Supply",
        "sub_sector": "Gas Supply",
        "industry_type": "Manufacture & Distribution of Gas / LPG"
    },
    # Division 36 - Water Supply & Works
    "36000": {
        "nic_code": "36000",
        "master_sector": "Electricity, Gas and Water Supply",
        "sub_sector": "Water Supply & Treatment",
        "industry_type": "Water Collection, Treatment and Supply (Water Works)"
    },
    # Division 37 - Sewerage & Wastewater
    "37000": {
        "nic_code": "37000",
        "master_sector": "Water Supply; Sewerage, Waste Management",
        "sub_sector": "Wastewater Treatment",
        "industry_type": "Sewerage & Effluent Treatment (STP / ETP / CETP)"
    },
    # Division 38 - Waste Management & Material Recovery
    "38110": {
        "nic_code": "38110",
        "master_sector": "Water Supply; Sewerage, Waste Management",
        "sub_sector": "Waste Management",
        "industry_type": "Waste Collection, Transfer Station & Processing"
    },
    "38210": {
        "nic_code": "38210",
        "master_sector": "Water Supply; Sewerage, Waste Management",
        "sub_sector": "Waste Management",
        "industry_type": "Composting & Waste Treatment Plant"
    },
    "38300": {
        "nic_code": "38300",
        "master_sector": "Water Supply; Sewerage, Waste Management",
        "sub_sector": "Materials Recovery",
        "industry_type": "Materials Recovery, Recycling & Scrap Processing"
    },
    # Division 52 - Warehousing & Transport Support
    "52101": {
        "nic_code": "52101",
        "master_sector": "Transportation and Storage",
        "sub_sector": "Warehousing & Logistics",
        "industry_type": "Warehousing, Logistics & Cold Storage"
    },
    "52210": {
        "nic_code": "52210",
        "master_sector": "Transportation and Storage",
        "sub_sector": "Transport Logistics",
        "industry_type": "Transport Terminal / Bus Depot / Rail Yard"
    },
    "52220": {
        "nic_code": "52220",
        "master_sector": "Transportation and Storage",
        "sub_sector": "Maritime & Port Logistics",
        "industry_type": "Port, Harbour & Container Terminal Activities"
    }
}


def resolve_nic_mapping(tags: Dict[str, Any], entity_class: str) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
    """
    Deterministically resolves official NIC-2008 code, master sector, sub-sector, and industry type.
    Returns (nic_code, master_sector, sub_sector, industry_type).
    If no reliable mapping can be established, returns (None, None, None, fallback_industry_type).
    """
    industrial = (tags.get("industrial") or "").lower().strip()
    power = (tags.get("power") or "").lower().strip()
    plant_source = (tags.get("plant:source") or "").lower().strip()
    plant_output = (tags.get("plant:output:electricity") or tags.get("plant:output") or "").lower().strip()
    man_made = (tags.get("man_made") or "").lower().strip()
    product = (tags.get("product") or "").lower().strip()
    resource = (tags.get("resource") or "").lower().strip()
    landuse = (tags.get("landuse") or "").lower().strip()
    amenity = (tags.get("amenity") or "").lower().strip()
    name = (tags.get("name") or "").lower().strip()

    nic_key = None

    # 1. Power Generation & Substations
    if power == "plant" or plant_source or plant_output or entity_class == "POWER_PLANT":
        if "solar" in plant_source or "solar" in name:
            nic_key = "35104"
        elif "hydro" in plant_source or "hydel" in name or "hydro" in name:
            nic_key = "35102"
        elif "nuclear" in plant_source or "atomic" in name or "nuclear" in name:
            nic_key = "35103"
        elif "wind" in plant_source or "wind" in name:
            nic_key = "35105"
        elif any(b in plant_source for b in ["biomass", "biogas", "biofuel", "waste"]):
            nic_key = "35106"
        elif any(t in plant_source for t in ["coal", "gas", "diesel", "oil", "thermal"]) or "thermal" in name:
            nic_key = "35101"
        elif power == "generator":
            nic_key = "35101"
        elif power == "substation" or "substation" in name:
            nic_key = "35107"
        else:
            nic_key = "35101"  # Default generic power generation

    elif power == "substation":
        nic_key = "35107"

    # 2. Mining & Quarrying
    elif entity_class == "MINE" or landuse == "quarry" or industrial == "mine" or resource or "mine" in name or "colliery" in name:
        if resource == "coal" or "coal" in name or "colliery" in name:
            nic_key = "0510"
        elif resource == "lignite" or "lignite" in name:
            nic_key = "0520"
        elif resource in ["iron", "iron_ore"] or "iron ore" in name:
            nic_key = "0710"
        elif resource in ["bauxite", "copper", "uranium", "zinc", "lead", "manganese"]:
            nic_key = "0729"
        elif landuse == "quarry" or resource in ["clay", "stone", "sand", "sand;aggregate"]:
            nic_key = "0810"
        else:
            nic_key = "0899"

    # 3. Petroleum Refinery & Petrochemicals
    elif entity_class == "REFINERY" or man_made in ["petroleum_refinery", "gas_processing"] or industrial in ["refinery", "oil"] or "refinery" in name:
        if "gas" in man_made or "gas" in name or industrial == "gas":
            nic_key = "35200"
        else:
            nic_key = "1920"

    # 4. Brickworks & Clay Kilns
    elif industrial in ["brickyard", "brickworks"] or man_made == "kiln" or "brick" in product or "brick" in name or "kiln" in name:
        nic_key = "2392"

    # 5. Food & Agro Processing
    elif industrial in ["rice_mill", "grinding_mill"] or product in ["rice", "flour", "grain"] or "rice mill" in name or "flour mill" in name:
        nic_key = "1061"
    elif industrial == "sugar" or product == "sugar" or "sugar" in name:
        nic_key = "1072"
    elif industrial == "slaughterhouse" or "slaughterhouse" in name or "abattoir" in name:
        nic_key = "1010"
    elif industrial in ["dairy", "milk"] or product == "dairy" or "dairy" in name:
        nic_key = "1050"
    elif product == "beer" or "brewery" in name or "distillery" in name or industrial == "brewery":
        nic_key = "1103" if "beer" in product or "brewery" in name else "1101"
    elif product in ["food", "tea", "coffee", "spices"] or "tea" in name:
        nic_key = "1079"

    # 6. Chemicals, Fertilizers & Pharmaceuticals
    elif industrial in ["chemical", "petrochemical"] or "chemical" in name or "petrochem" in name:
        nic_key = "2011"
    elif industrial == "fertilizer" or "fertilizer" in name or "iffco" in name or "kribhco" in name:
        nic_key = "2012"
    elif industrial in ["pharmaceutical", "pharmaceutical company", "pharma"] or "pharma" in name or "laboratories" in name:
        nic_key = "2100"
    elif product == "oxygen" or "oxygen" in name:
        nic_key = "2029"

    # 7. Basic Metals, Steel & Metallurgy
    elif industrial in ["metallurgy", "steel", "foundry", "smelter"] or "steel" in name or "iron" in name or "ispat" in name:
        nic_key = "2410"
    elif "aluminium" in name or "copper" in name or "hindalco" in name or "nalco" in name or "vedanta" in name:
        nic_key = "2420"

    # 8. Cement & Concrete
    elif industrial in ["cement", "concrete_plant"] or product in ["cement", "concrete"] or "cement" in name:
        nic_key = "2394" if "cement" in industrial or "cement" in name else "2395"

    # 9. Textiles & Garments
    elif industrial in ["textile", "spinning", "weaving", "cotton"] or product in ["clothes", "fabric", "textiles"] or "textile" in name or "spinning" in name:
        nic_key = "1311"

    # 10. Machinery, Pumps & Motors
    elif industrial in ["pump", "pump_house", "machinery"] or man_made == "pump" or product == "machinery" or "pumps" in name or "motors" in name:
        nic_key = "2813"

    # 11. Wood & Sawmills
    elif industrial in ["sawmill", "timber", "wood"] or product in ["wood", "furniture"] or "saw mill" in name:
        nic_key = "1610"

    # 12. Water & Wastewater Utilities
    elif man_made in ["water_works", "pumping_station", "water_tower"] or industrial == "water_works":
        nic_key = "36000"
    elif man_made in ["wastewater_plant", "wastewater_treatment"] or industrial == "effluent_treatment":
        nic_key = "37000"

    # 13. Waste Management & Recycling
    elif man_made == "composting_plant" or amenity == "waste_transfer_station":
        nic_key = "38210"
    elif industrial == "scrap_yard" or amenity == "recycling" or "scrap" in name or "recycling" in name:
        nic_key = "38300"

    # 14. Logistics, Warehousing & Depots
    elif industrial in ["warehouse", "storage", "depot"] or "godown" in name or "warehouse" in name:
        nic_key = "52101"
    elif industrial == "bus_depot" or amenity == "bus_station":
        nic_key = "52210"
    elif industrial == "port" or man_made == "container_terminal" or "container terminal" in name or "port" in name:
        nic_key = "52220"

    # Lookup taxonomy entry
    if nic_key and nic_key in NIC_2008_TAXONOMY:
        entry = NIC_2008_TAXONOMY[nic_key]
        return entry["nic_code"], entry["master_sector"], entry["sub_sector"], entry["industry_type"]

    # Fallback when no reliable NIC mapping exists
    fallback_type = None
    if entity_class == "INDUSTRIAL_ZONE":
        fallback_type = "Designated Industrial Park / Estate"
    elif entity_class == "WORKS":
        fallback_type = f"Industrial Works ({man_made or 'Generic'})"
    elif entity_class == "FACILITY":
        fallback_type = f"Industrial Manufacturing ({industrial or 'Unclassified'})"
    else:
        fallback_type = "Unclassified Industrial Activity"

    return None, None, None, fallback_type
