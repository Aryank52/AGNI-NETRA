import math
from typing import List, Tuple, Dict, Any, Optional
from shapely.geometry import Point, Polygon, MultiPoint, mapping


def haversine_distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points on the earth in meters.
    """
    R = 6371000.0  # Earth's radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


def compute_cluster_geometry(points: List[Tuple[float, float]]) -> Dict[str, Any]:
    """
    Given a list of (lat, lon) points:
    1. Computes the geometric centroid
    2. Computes the bounding box [min_lat, min_lon, max_lat, max_lon]
    3. Computes the convex hull GeoJSON if > 2 points, else Point/Line
    """
    if not points:
        return {
            "centroid": (0.0, 0.0),
            "bounding_box": [0.0, 0.0, 0.0, 0.0],
            "convex_hull_geojson": None
        }

    # Note: Shapely uses (x, y) = (lon, lat)
    shapely_points = [Point(lon, lat) for lat, lon in points]
    multipoint = MultiPoint(shapely_points)
    
    centroid_geom = multipoint.centroid
    centroid = (centroid_geom.y, centroid_geom.x)  # (lat, lon)
    
    lats = [p[0] for p in points]
    lons = [p[1] for p in points]
    bounding_box = [min(lats), min(lons), max(lats), max(lons)]
    
    if len(points) >= 3:
        hull = multipoint.convex_hull
        convex_hull_geojson = mapping(hull)
    else:
        convex_hull_geojson = None

    return {
        "centroid": centroid,
        "bounding_box": bounding_box,
        "convex_hull_geojson": convex_hull_geojson
    }


def find_nearest_facility(
    lat: float, lon: float, facilities: List[Dict[str, Any]]
) -> Tuple[Optional[Dict[str, Any]], float]:
    """
    Finds the nearest industrial facility from a list of facilities and returns (facility, distance_meters).
    """
    if not facilities:
        return None, 999999.0

    min_dist = float("inf")
    nearest = None

    for fac in facilities:
        f_lat = fac.get("latitude")
        f_lon = fac.get("longitude")
        if f_lat is not None and f_lon is not None:
            dist = haversine_distance_m(lat, lon, f_lat, f_lon)
            if dist < min_dist:
                min_dist = dist
                nearest = fac

    return nearest, min_dist


def point_in_polygon(lat: float, lon: float, polygon_geojson: Dict[str, Any]) -> bool:
    """
    Checks if a (lat, lon) point is strictly within a GeoJSON polygon.
    """
    try:
        poly = Polygon(polygon_geojson["coordinates"][0])
        pt = Point(lon, lat)
        return poly.contains(pt)
    except Exception:
        return False


# Curated Major Indian State Centroids & Bounding Boxes for Fallback Geographic Enrichment
INDIAN_STATES_BOUNDS = {
    "Gujarat": {"min_lat": 20.1, "max_lat": 24.7, "min_lon": 68.1, "max_lon": 74.5},
    "Madhya Pradesh": {"min_lat": 21.1, "max_lat": 26.9, "min_lon": 74.0, "max_lon": 82.8},
    "Chhattisgarh": {"min_lat": 17.8, "max_lat": 24.1, "min_lon": 80.2, "max_lon": 84.4},
    "Odisha": {"min_lat": 17.8, "max_lat": 22.6, "min_lon": 81.4, "max_lon": 87.5},
    "Jharkhand": {"min_lat": 21.9, "max_lat": 25.3, "min_lon": 83.3, "max_lon": 87.9},
    "Punjab": {"min_lat": 29.5, "max_lat": 32.5, "min_lon": 73.8, "max_lon": 76.9},
    "Haryana": {"min_lat": 27.6, "max_lat": 30.9, "min_lon": 74.4, "max_lon": 77.6},
    "Andhra Pradesh": {"min_lat": 12.6, "max_lat": 19.9, "min_lon": 76.7, "max_lon": 84.8},
    "Maharashtra": {"min_lat": 15.6, "max_lat": 22.0, "min_lon": 72.6, "max_lon": 80.9},
    "Rajasthan": {"min_lat": 23.0, "max_lat": 30.2, "min_lon": 69.5, "max_lon": 78.3},
    "Tamil Nadu": {"min_lat": 8.0, "max_lat": 13.6, "min_lon": 76.2, "max_lon": 80.3},
    "Karnataka": {"min_lat": 11.5, "max_lat": 18.5, "min_lon": 74.0, "max_lon": 78.6},
    "West Bengal": {"min_lat": 21.5, "max_lat": 27.2, "min_lon": 85.8, "max_lon": 89.9},
    "Uttar Pradesh": {"min_lat": 23.8, "max_lat": 30.4, "min_lon": 77.0, "max_lon": 84.6},
}


def lookup_state(lat: float, lon: float) -> str:
    """
    Performs quick spatial containment lookup for Indian state.
    """
    for state, bounds in INDIAN_STATES_BOUNDS.items():
        if (bounds["min_lat"] <= lat <= bounds["max_lat"] and
            bounds["min_lon"] <= lon <= bounds["max_lon"]):
            return state
    return "National / Other"
