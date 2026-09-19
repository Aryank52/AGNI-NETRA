import math
from typing import List, Tuple, Dict, Any, Optional
from shapely.geometry import Point, Polygon, MultiPoint, mapping


def haversine_distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points on Earth in meters.
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


def validate_coordinates(lat: float, lon: float, check_sovereign: bool = True) -> bool:
    """
    Validates if coordinates are valid float numbers and (optionally) within authoritative
    sovereign India polygon boundaries.
    """
    try:
        if lat is None or lon is None:
            return False
        lat = float(lat)
        lon = float(lon)
        if math.isnan(lat) or math.isnan(lon) or math.isinf(lat) or math.isinf(lon):
            return False
        if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
            return False
        if check_sovereign:
            from backend.app.services.india_boundary_service import india_boundary_service
            return india_boundary_service.is_within_india(lat, lon)
        return True
    except Exception:
        return False



def compute_cluster_geometry(points: List[Tuple[float, float]]) -> Dict[str, Any]:
    """
    Given a list of (lat, lon) points:
    1. Computes the geometric centroid
    2. Computes the bounding box [min_lat, min_lon, max_lat, max_lon]
    3. Computes the convex hull GeoJSON if >= 3 points, else centroid point
    """
    if not points:
        return {
            "centroid": (0.0, 0.0),
            "bounding_box": [0.0, 0.0, 0.0, 0.0],
            "convex_hull_geojson": None
        }

    # Shapely coordinates: (lon, lat)
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
        convex_hull_geojson = {
            "type": "Point",
            "coordinates": [centroid[1], centroid[0]]
        }

    return {
        "centroid": centroid,
        "bounding_box": bounding_box,
        "convex_hull_geojson": convex_hull_geojson
    }


class SpatialIndex:
    """
    Fast Spatial Indexing Engine for nearest-neighbor facility queries and polygon containment.
    """

    def __init__(self, facilities: Optional[List[Dict[str, Any]]] = None):
        self.facilities: List[Dict[str, Any]] = facilities or []

    def set_facilities(self, facilities: List[Dict[str, Any]]) -> None:
        self.facilities = facilities

    def find_nearest(self, lat: float, lon: float) -> Tuple[Optional[Dict[str, Any]], float]:
        """
        Finds the nearest facility from indexed items and returns (facility_dict, distance_meters).
        """
        if not self.facilities:
            return None, 999999.0

        min_dist = float("inf")
        nearest = None

        for fac in self.facilities:
            f_lat = fac.get("latitude")
            f_lon = fac.get("longitude")
            if f_lat is not None and f_lon is not None:
                dist = haversine_distance_m(lat, lon, float(f_lat), float(f_lon))
                if dist < min_dist:
                    min_dist = dist
                    nearest = fac

        return nearest, min_dist


# Global Spatial Index
spatial_index = SpatialIndex()


def find_nearest_facility(
    lat: float,
    lon: float,
    facilities: List[Dict[str, Any]]
) -> Tuple[Optional[Dict[str, Any]], float]:
    """
    Convenience wrapper for nearest facility lookup.
    """
    idx = SpatialIndex(facilities)
    return idx.find_nearest(lat, lon)


def point_in_polygon(lat: float, lon: float, polygon_geojson: Dict[str, Any]) -> bool:
    """
    Checks if a (lat, lon) point is within a GeoJSON polygon.
    """
    try:
        poly = Polygon(polygon_geojson["coordinates"][0])
        pt = Point(lon, lat)
        return poly.contains(pt)
    except Exception:
        return False


INDIAN_STATES_BOUNDS = {
    "Gujarat": {"min_lat": 20.1, "max_lat": 24.7, "min_lon": 68.1, "max_lon": 74.5, "district": "Jamnagar"},
    "Madhya Pradesh": {"min_lat": 21.1, "max_lat": 26.9, "min_lon": 74.0, "max_lon": 82.8, "district": "Singrauli"},
    "Chhattisgarh": {"min_lat": 17.8, "max_lat": 24.1, "min_lon": 80.2, "max_lon": 84.4, "district": "Korba"},
    "Odisha": {"min_lat": 17.8, "max_lat": 22.6, "min_lon": 81.4, "max_lon": 87.5, "district": "Angul"},
    "Jharkhand": {"min_lat": 21.9, "max_lat": 25.3, "min_lon": 83.3, "max_lon": 87.9, "district": "Dhanbad"},
    "Punjab": {"min_lat": 29.5, "max_lat": 32.5, "min_lon": 73.8, "max_lon": 76.9, "district": "Sangrur"},
    "Haryana": {"min_lat": 27.6, "max_lat": 30.9, "min_lon": 74.4, "max_lon": 77.6, "district": "Karnal"},
    "Andhra Pradesh": {"min_lat": 12.6, "max_lat": 19.9, "min_lon": 76.7, "max_lon": 84.8, "district": "East Godavari"},
    "Maharashtra": {"min_lat": 15.6, "max_lat": 22.0, "min_lon": 72.6, "max_lon": 80.9, "district": "Nagpur"},
    "Rajasthan": {"min_lat": 23.0, "max_lat": 30.2, "min_lon": 69.5, "max_lon": 78.3, "district": "Barmer"},
    "Tamil Nadu": {"min_lat": 8.0, "max_lat": 13.6, "min_lon": 76.2, "max_lon": 80.3, "district": "Chennai"},
    "Karnataka": {"min_lat": 11.5, "max_lat": 18.5, "min_lon": 74.0, "max_lon": 78.6, "district": "Ballari"},
    "West Bengal": {"min_lat": 21.5, "max_lat": 27.2, "min_lon": 85.8, "max_lon": 89.9, "district": "Haldia"},
    "Uttar Pradesh": {"min_lat": 23.8, "max_lat": 30.4, "min_lon": 77.0, "max_lon": 84.6, "district": "Sonbhadra"},
    "Delhi": {"min_lat": 28.3, "max_lat": 28.9, "min_lon": 76.8, "max_lon": 77.4, "district": "New Delhi"},
}


def lookup_state(lat: float, lon: float) -> str:
    """
    Performs authoritative spatial containment lookup for Indian state via PostGIS / boundary service.
    Returns 'UNKNOWN' if outside India or unresolvable.
    """
    try:
        from backend.app.services.india_boundary_service import india_boundary_service
        is_in, state_name, _, _ = india_boundary_service.is_point_inside_india(lat, lon)
        if is_in and state_name:
            return state_name
        return "UNKNOWN"
    except Exception:
        return "UNKNOWN"


def lookup_district(lat: float, lon: float) -> Optional[str]:
    """
    Resolves authoritative district context from spatial coordinates.
    Returns 'UNKNOWN' if inside India but district cannot be confidently assigned.
    Returns None if outside sovereign India.
    """
    try:
        from backend.app.services.india_boundary_service import india_boundary_service
        is_in, _, district_name, _ = india_boundary_service.is_point_inside_india(lat, lon)
        if is_in:
            return district_name or "UNKNOWN"
        return None
    except Exception:
        return None

