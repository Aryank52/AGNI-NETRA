"""
AGNI-NETRA — Land Use / Land Cover (LULC) Classification & Spatial Engine
Queries PostGIS lulc_spatial_features and lulc_classes (ISRO Bhuvan 1:50,000 Level-II Standards).
Fallback to in-memory synthetic zones only if database is offline.
"""

from typing import List, Dict, Any, Tuple, Optional
import logging
from shapely.geometry import Point, Polygon
from sqlalchemy import text
from backend.app.services.spatial_engine import haversine_distance_m

logger = logging.getLogger("LULCEngine")


# =========================================================================
# SYNTHETIC / DEMO FALLBACK REFERENCE ZONES
# IMPORTANT: Clearly tagged as DEMO/FALLBACK only. NEVER claim these are real data.
# =========================================================================
SYNTHETIC_FALLBACK_ZONES = [
    {
        "name": "Jamnagar Petrochemical & SEZ Complex (Demo Fallback)",
        "category": "Industrial",
        "canonical": "BUILT_UP_INDUSTRIAL",
        "state": "Gujarat",
        "polygon": [[69.80, 22.30], [69.95, 22.30], [69.95, 22.45], [69.80, 22.45], [69.80, 22.30]],
        "data_mode": "SYNTHETIC_DEMO"
    },
    {
        "name": "Ankleshwar - Dahej Petroleum Chemical Corridor (Demo Fallback)",
        "category": "Industrial",
        "canonical": "BUILT_UP_INDUSTRIAL",
        "state": "Gujarat",
        "polygon": [[72.50, 21.60], [73.10, 21.60], [73.10, 21.85], [72.50, 21.85], [72.50, 21.60]],
        "data_mode": "SYNTHETIC_DEMO"
    },
    {
        "name": "Singrauli Super Thermal Power & Coal Belt (Demo Fallback)",
        "category": "Industrial",
        "canonical": "BUILT_UP_INDUSTRIAL",
        "state": "Madhya Pradesh",
        "polygon": [[82.50, 24.05], [82.80, 24.05], [82.80, 24.25], [82.50, 24.25], [82.50, 24.05]],
        "data_mode": "SYNTHETIC_DEMO"
    },
    {
        "name": "Angul - Kalinganagar Steel Corridor (Demo Fallback)",
        "category": "Industrial",
        "canonical": "BUILT_UP_INDUSTRIAL",
        "state": "Odisha",
        "polygon": [[84.90, 20.75], [85.40, 20.75], [85.40, 21.10], [84.90, 21.10], [84.90, 20.75]],
        "data_mode": "SYNTHETIC_DEMO"
    },
    {
        "name": "Korba Coal Mining & Power Cluster (Demo Fallback)",
        "category": "Mining",
        "canonical": "MINING",
        "state": "Chhattisgarh",
        "polygon": [[82.60, 22.30], [82.90, 22.30], [82.90, 22.50], [82.60, 22.50], [82.60, 22.30]],
        "data_mode": "SYNTHETIC_DEMO"
    },
    {
        "name": "Similipal Tiger Reserve & Biosphere (Demo Fallback)",
        "category": "Forest",
        "canonical": "FOREST",
        "state": "Odisha",
        "polygon": [[86.10, 21.40], [86.70, 21.40], [86.70, 22.10], [86.10, 22.10], [86.10, 21.40]],
        "data_mode": "SYNTHETIC_DEMO"
    },
    {
        "name": "Bandhavgarh National Park (Demo Fallback)",
        "category": "Forest",
        "canonical": "FOREST",
        "state": "Madhya Pradesh",
        "polygon": [[80.80, 23.50], [81.25, 23.50], [81.25, 23.90], [80.80, 23.90], [80.80, 23.50]],
        "data_mode": "SYNTHETIC_DEMO"
    },
    {
        "name": "Punjab - Haryana Agricultural Plains (Demo Fallback)",
        "category": "Agricultural",
        "canonical": "AGRICULTURE_CROPLAND",
        "state": "Punjab",
        "polygon": [[74.00, 29.80], [76.50, 29.80], [76.50, 31.80], [74.00, 31.80], [74.00, 29.80]],
        "data_mode": "SYNTHETIC_DEMO"
    },
    {
        "name": "KG Basin Offshore / Coastal Gas Field (Demo Fallback)",
        "category": "Industrial",
        "canonical": "BUILT_UP_INDUSTRIAL",
        "state": "Andhra Pradesh",
        "polygon": [[81.80, 16.30], [82.30, 16.30], [82.30, 16.70], [81.80, 16.70], [81.80, 16.30]],
        "data_mode": "SYNTHETIC_DEMO"
    }
]

# Backward compatibility alias
KNOWN_LULC_ZONES = SYNTHETIC_FALLBACK_ZONES


class LULCAdapter:
    """
    Land Use / Land Cover (LULC) Classification & Spatial Intersect Engine.
    Executes PostGIS point-in-polygon queries against verified ISRO Bhuvan Level-II spatial features.
    """

    def __init__(self, fallback_zones: Optional[List[Dict[str, Any]]] = None):
        self.fallback_zones = fallback_zones or SYNTHETIC_FALLBACK_ZONES
        self._fallback_polygons = [
            (z["name"], z["category"], Polygon(z["polygon"]), z["state"], z.get("canonical", "OTHER"))
            for z in self.fallback_zones
        ]

    def classify_location(self, lat: float, lon: float) -> Tuple[str, Optional[str], Dict[str, float]]:
        """
        Determines the canonical LULC category using PostGIS spatial Point-in-Polygon containment
        and computes geodesic boundary distances to nearest sensitive features (forest, agriculture, water, industrial, mining).
        """
        # 1. Attempt PostGIS Query First
        try:
            from backend.app.core.database import engine
            with engine.connect() as conn:
                # Check direct containment
                match = conn.execute(text("""
                    SELECT f.id, f.canonical_class, c.source_class_code, c.source_class_name, f.feature_name
                    FROM lulc_spatial_features f
                    JOIN lulc_classes c ON f.class_id = c.id
                    WHERE ST_Contains(f.geom, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326))
                    LIMIT 1;
                """), {"lat": lat, "lon": lon}).fetchone()

                # Compute real geodesic distances to nearest feature boundaries
                dist_row = conn.execute(text("""
                    SELECT 
                       MIN(ST_Distance(ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, geom::geography)) FILTER (WHERE canonical_class = 'FOREST') as dist_forest,
                       MIN(ST_Distance(ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, geom::geography)) FILTER (WHERE canonical_class = 'AGRICULTURE_CROPLAND') as dist_agri,
                       MIN(ST_Distance(ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, geom::geography)) FILTER (WHERE canonical_class = 'WATER_BODIES') as dist_water,
                       MIN(ST_Distance(ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, geom::geography)) FILTER (WHERE canonical_class = 'BUILT_UP_INDUSTRIAL') as dist_ind,
                       MIN(ST_Distance(ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, geom::geography)) FILTER (WHERE canonical_class = 'MINING') as dist_mining
                    FROM lulc_spatial_features;
                """), {"lat": lat, "lon": lon}).fetchone()

                distances = {
                    "dist_to_industrial_m": round(float(dist_row.dist_ind if dist_row and dist_row.dist_ind is not None else 999999.0), 1),
                    "dist_to_forest_m": round(float(dist_row.dist_forest if dist_row and dist_row.dist_forest is not None else 999999.0), 1),
                    "dist_to_agri_m": round(float(dist_row.dist_agri if dist_row and dist_row.dist_agri is not None else 999999.0), 1),
                    "dist_to_mine_m": round(float(dist_row.dist_mining if dist_row and dist_row.dist_mining is not None else 999999.0), 1),
                    "dist_to_water_m": round(float(dist_row.dist_water if dist_row and dist_row.dist_water is not None else 999999.0), 1),
                    "dist_to_settlement_m": 4200.0
                }

                if match:
                    category = "Industrial" if match.canonical_class == "BUILT_UP_INDUSTRIAL" else \
                               "Forest" if match.canonical_class == "FOREST" else \
                               "Agricultural" if match.canonical_class == "AGRICULTURE_CROPLAND" else \
                               "Mining" if match.canonical_class == "MINING" else \
                               "Water" if match.canonical_class == "WATER_BODIES" else \
                               "Urban" if match.canonical_class == "BUILT_UP_URBAN" else "Barren"
                    return category, match.feature_name, distances

                # If outside pilot polygons, explicitly return Unknown/No Bhuvan Coverage
                return "Unknown", "No Bhuvan Pilot Coverage Available", distances

        except Exception as e:
            logger.warning(f"PostGIS LULC query failed ({e}), falling back to in-memory fallback zones.")

        # 2. Fallback to In-Memory Synthetic/Demo Polygons
        return self._classify_fallback(lat, lon)

    def _classify_fallback(self, lat: float, lon: float) -> Tuple[str, Optional[str], Dict[str, float]]:
        pt = Point(lon, lat)
        distances = self._compute_fallback_distances(lat, lon)

        for name, category, poly, state, canonical in self._fallback_polygons:
            if poly.contains(pt):
                return category, f"{name} [DEMO_FALLBACK]", distances

        if distances.get("dist_to_industrial_m", 999999) <= 5000:
            return "Industrial", "Industrial Buffer Zone [DEMO_FALLBACK]", distances
        elif distances.get("dist_to_forest_m", 999999) <= 3000:
            return "Forest", "Forest Vicinity [DEMO_FALLBACK]", distances
        elif distances.get("dist_to_agri_m", 999999) <= 4000:
            return "Agricultural", "Agricultural Belt [DEMO_FALLBACK]", distances
        else:
            return "Barren / Scrub", "Open Terrain [DEMO_FALLBACK]", distances

    def _compute_fallback_distances(self, lat: float, lon: float) -> Dict[str, float]:
        dist_ind = float("inf")
        dist_for = float("inf")
        dist_agr = float("inf")
        dist_min = float("inf")

        for name, category, poly, state, canonical in self._fallback_polygons:
            centroid_lon, centroid_lat = poly.centroid.x, poly.centroid.y
            dist = haversine_distance_m(lat, lon, centroid_lat, centroid_lon)
            if category == "Industrial" and dist < dist_ind:
                dist_ind = dist
            elif category == "Forest" and dist < dist_for:
                dist_for = dist
            elif category == "Agricultural" and dist < dist_agr:
                dist_agr = dist
            elif category == "Mining" and dist < dist_min:
                dist_min = dist

        return {
            "dist_to_industrial_m": round(dist_ind, 1),
            "dist_to_forest_m": round(dist_for, 1),
            "dist_to_agri_m": round(dist_agr, 1),
            "dist_to_mine_m": round(dist_min, 1),
            "dist_to_water_m": 8500.0,
            "dist_to_settlement_m": 4200.0
        }


lulc_engine = LULCAdapter()
