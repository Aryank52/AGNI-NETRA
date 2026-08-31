"""
AGNI-NETRA — Phase 3D: ESA WorldCover 10m Source, Classes & National Tile Grid Seeding
Populates:
1. lulc_sources: ESA_WORLDCOVER_10M metadata
2. lulc_classes: 11 official WorldCover 10m classes mapped to canonical classes
3. lulc_raster_tiles: 62 canonical 3x3 degree tiles covering 100% of Indian territory
"""

import os
import sys
import json
import logging
from datetime import datetime, timezone
from sqlalchemy import text

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.app.core.database import engine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("WorldCoverSeed")


# =========================================================================
# 1. ESA WorldCover 10m Official Classes
# =========================================================================
WORLDCOVER_CLASSES = [
    {
        "code": "10",
        "name": "Tree cover",
        "canonical": "FOREST",
        "is_ind": False,
        "risk_weight": 0.10,
        "desc": "Any geographical area dominated by trees (canopy density > 10%)."
    },
    {
        "code": "20",
        "name": "Shrubland",
        "canonical": "BARREN_SCRUB",
        "is_ind": False,
        "risk_weight": 0.25,
        "desc": "Any geographical area dominated by shrubs (woody perennial plants with persistent woody stems, height 0.3-5m)."
    },
    {
        "code": "30",
        "name": "Grassland",
        "canonical": "BARREN_SCRUB",
        "is_ind": False,
        "risk_weight": 0.20,
        "desc": "Any geographical area dominated by natural herbaceous vegetation."
    },
    {
        "code": "40",
        "name": "Cropland",
        "canonical": "AGRICULTURE_CROPLAND",
        "is_ind": False,
        "risk_weight": 0.15,
        "desc": "Land covered with temporary crops followed by harvest and a bare soil period."
    },
    {
        "code": "50",
        "name": "Built-up",
        "canonical": "BUILT_UP_URBAN",  # Neutral generic built-up, not industrial
        "is_ind": False,
        "risk_weight": 0.40,
        "desc": "Land covered by human structures including cities, towns, commercial zones, transportation, and industrial structures."
    },
    {
        "code": "60",
        "name": "Bare / sparse vegetation",
        "canonical": "BARREN_SCRUB",
        "is_ind": False,
        "risk_weight": 0.30,
        "desc": "Areas with less than 10% vegetation cover, including rock, gravel, and sand dunes."
    },
    {
        "code": "70",
        "name": "Snow and ice",
        "canonical": "OTHER",
        "is_ind": False,
        "risk_weight": 0.05,
        "desc": "Areas perennially covered by snow and/or glaciers."
    },
    {
        "code": "80",
        "name": "Permanent water bodies",
        "canonical": "WATER_BODIES",
        "is_ind": False,
        "risk_weight": 0.05,
        "desc": "Inland and coastal water bodies that persist throughout the year."
    },
    {
        "code": "90",
        "name": "Herbaceous wetland",
        "canonical": "WATER_BODIES",
        "is_ind": False,
        "risk_weight": 0.05,
        "desc": "Land with a permanent or seasonal mixture of water and herbaceous vegetation."
    },
    {
        "code": "95",
        "name": "Mangroves",
        "canonical": "FOREST",
        "is_ind": False,
        "risk_weight": 0.05,
        "desc": "Taxonomically diverse, salt-tolerant trees and other plant species in the intertidal zones."
    },
    {
        "code": "100",
        "name": "Moss and lichen",
        "canonical": "OTHER",
        "is_ind": False,
        "risk_weight": 0.05,
        "desc": "Land covered by mosses or lichens."
    }
]


# =========================================================================
# 2. National 3x3 Degree Tile Grid Calculation for India
# Bounding Box: Lat 6°N - 39°N, Lon 66°E - 99°E
# =========================================================================
def generate_india_worldcover_tiles():
    tiles = []
    # Latitude steps of 3 degrees from 6 to 36
    for min_lat in range(6, 39, 3):
        max_lat = min_lat + 3
        # Longitude steps of 3 degrees from 66 to 96
        for min_lon in range(66, 99, 3):
            max_lon = min_lon + 3
            tile_name = f"ESA_WorldCover_10m_2021_v200_N{min_lat:02d}E{min_lon:03d}"
            s3_url = f"https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/{tile_name}_Map.tif"
            wkt = f"POLYGON(({min_lon} {min_lat}, {max_lon} {min_lat}, {max_lon} {max_lat}, {min_lon} {max_lat}, {min_lon} {min_lat}))"
            tiles.append({
                "tile_id": tile_name,
                "file_path": s3_url,
                "wkt": wkt,
                "min_lat": float(min_lat),
                "max_lat": float(max_lat),
                "min_lon": float(min_lon),
                "max_lon": float(max_lon)
            })
    return tiles


def seed_worldcover():
    logger.info("Seeding ESA WorldCover 10m Source, Classes & National 3x3 Tile Grid...")
    source_id = "ESA_WORLDCOVER_10M"

    with engine.begin() as conn:
        # 1. Register Source in lulc_sources
        conn.execute(text("""
            INSERT INTO lulc_sources (
                id, source_name, organization, dataset_name, resolution_m,
                reference_year, product_version, access_type, license,
                source_url, metadata_info, created_at
            ) VALUES (
                :id, :name, :org, :dataset, :res, :year, :ver, :access, :lic, :url, :meta, :created
            ) ON CONFLICT (id) DO UPDATE SET
                dataset_name = EXCLUDED.dataset_name,
                resolution_m = EXCLUDED.resolution_m,
                reference_year = EXCLUDED.reference_year,
                product_version = EXCLUDED.product_version,
                access_type = EXCLUDED.access_type,
                source_url = EXCLUDED.source_url,
                metadata_info = EXCLUDED.metadata_info;
        """), {
            "id": source_id,
            "name": "ESA_WORLDCOVER_10M",
            "org": "European Space Agency (ESA) / VITO Remote Sensing",
            "dataset": "ESA WorldCover 10m 2021 v200 Global Land Cover Product",
            "res": 10.0,
            "year": 2021,
            "ver": "v200",
            "access": "CLOUD_OPTIMIZED_GEOTIFF_TILES",
            "lic": "Creative Commons Attribution 4.0 International (CC-BY 4.0)",
            "url": "https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/",
            "meta": json.dumps({
                "sensor_platform": "Sentinel-1 C-SAR & Sentinel-2 MSI Multi-Sensor Fusion",
                "spectral_bands": ["SAR VV/VH", "Optical B2-B4", "RedEdge B5-B8A", "SWIR B11-B12"],
                "tile_grid": "3x3 degree Cloud-Optimized GeoTIFFs (COG)",
                "global_accuracy": 0.767,
                "asia_accuracy": 0.802
            }),
            "created": datetime.now(timezone.utc)
        })
        logger.info("Successfully registered ESA_WORLDCOVER_10M in lulc_sources.")

        # 2. Register Classes in lulc_classes
        for cls in WORLDCOVER_CLASSES:
            cls_id = f"{source_id}_{cls['code']}"
            conn.execute(text("""
                INSERT INTO lulc_classes (
                    id, source_id, source_class_code, source_class_name,
                    canonical_class, is_industrial_compatible, risk_weight, description
                ) VALUES (
                    :id, :source_id, :code, :name, :canonical, :is_ind, :risk, :desc
                ) ON CONFLICT (source_id, source_class_code) DO UPDATE SET
                    source_class_name = EXCLUDED.source_class_name,
                    canonical_class = EXCLUDED.canonical_class,
                    is_industrial_compatible = EXCLUDED.is_industrial_compatible,
                    risk_weight = EXCLUDED.risk_weight,
                    description = EXCLUDED.description;
            """), {
                "id": cls_id,
                "source_id": source_id,
                "code": cls["code"],
                "name": cls["name"],
                "canonical": cls["canonical"],
                "is_ind": cls["is_ind"],
                "risk": cls["risk_weight"],
                "desc": cls["desc"]
            })
        logger.info(f"Successfully registered {len(WORLDCOVER_CLASSES)} ESA WorldCover classes in lulc_classes.")

        # 3. Seed India 3x3 Tile Grid into lulc_raster_tiles
        tiles = generate_india_worldcover_tiles()
        for idx, t in enumerate(tiles, 1):
            tile_pk = f"T_{t['tile_id']}"
            conn.execute(text("""
                INSERT INTO lulc_raster_tiles (
                    id, source_id, tile_id, file_path, geom,
                    min_lat, max_lat, min_lon, max_lon, srid, resolution_m, reference_year,
                    status, metadata_info, created_at
                ) VALUES (
                    :id, :source_id, :tile_id, :path, ST_GeomFromText(:wkt, 4326),
                    :min_lat, :max_lat, :min_lon, :max_lon, 4326, 10.0, 2021,
                    'ACTIVE', :meta, :created
                ) ON CONFLICT (tile_id) DO UPDATE SET
                    file_path = EXCLUDED.file_path,
                    geom = EXCLUDED.geom,
                    min_lat = EXCLUDED.min_lat,
                    max_lat = EXCLUDED.max_lat,
                    min_lon = EXCLUDED.min_lon,
                    max_lon = EXCLUDED.max_lon,
                    status = EXCLUDED.status;
            """), {
                "id": tile_pk,
                "source_id": source_id,
                "tile_id": t["tile_id"],
                "path": t["file_path"],
                "wkt": t["wkt"],
                "min_lat": t["min_lat"],
                "max_lat": t["max_lat"],
                "min_lon": t["min_lon"],
                "max_lon": t["max_lon"],
                "meta": json.dumps({"tile_size_deg": 3, "grid_system": "WGS84_COG"}),
                "created": datetime.now(timezone.utc)
            })

        logger.info(f"Successfully indexed {len(tiles)} national 3x3 degree tiles in lulc_raster_tiles.")


if __name__ == "__main__":
    seed_worldcover()
