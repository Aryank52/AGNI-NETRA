import math
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any
from sklearn.cluster import DBSCAN
from backend.app.services.spatial_engine import compute_cluster_geometry, lookup_state


def cluster_thermal_detections(
    detections: List[Dict[str, Any]],
    eps_km: float = 1.5,
    min_samples: int = 1
) -> List[Dict[str, Any]]:
    """
    Spatiotemporal clustering of raw satellite thermal observations into logical ThermalEvents.
    Uses DBSCAN with Haversine metric on radian coordinates.
    """
    if not detections:
        return []

    # Earth radius in km
    kms_per_radian = 6371.0088
    eps_rad = eps_km / kms_per_radian

    coords = []
    for d in detections:
        lat = d["latitude"]
        lon = d["longitude"]
        coords.append([math.radians(lat), math.radians(lon)])

    coords_arr = np.array(coords)

    db = DBSCAN(eps=eps_rad, min_samples=min_samples, metric="haversine")
    labels = db.fit_predict(coords_arr)

    # Group detections by cluster label
    clusters_map: Dict[int, List[Dict[str, Any]]] = {}
    for idx, label in enumerate(labels):
        if label not in clusters_map:
            clusters_map[label] = []
        clusters_map[label].append(detections[idx])

    events = []
    for cluster_id, cluster_dets in clusters_map.items():
        points = [(d["latitude"], d["longitude"]) for d in cluster_dets]
        geom_info = compute_cluster_geometry(points)
        
        frps = [d.get("frp", 0.0) for d in cluster_dets]
        brightnesses = [d.get("brightness", 300.0) for d in cluster_dets if d.get("brightness")]
        satellites = set(d.get("satellite") or d.get("sensor", "VIIRS") for d in cluster_dets)
        
        timestamps = [d["acq_timestamp"] for d in cluster_dets]
        first_seen = min(timestamps)
        last_seen = max(timestamps)

        centroid_lat, centroid_lon = geom_info["centroid"]
        state = lookup_state(centroid_lat, centroid_lon)

        events.append({
            "cluster_label": int(cluster_id),
            "latitude": round(centroid_lat, 5),
            "longitude": round(centroid_lon, 5),
            "bounding_box": geom_info["bounding_box"],
            "convex_hull_geojson": geom_info["convex_hull_geojson"],
            "first_seen": first_seen,
            "last_seen": last_seen,
            "detection_count": len(cluster_dets),
            "avg_frp": round(float(np.mean(frps)), 2),
            "max_frp": round(float(np.max(frps)), 2),
            "min_frp": round(float(np.min(frps)), 2),
            "frp_variance": round(float(np.var(frps)), 2) if len(frps) > 1 else 0.0,
            "avg_brightness": round(float(np.mean(brightnesses)), 2) if brightnesses else 320.0,
            "satellite_count": len(satellites),
            "state": state,
            "detections": cluster_dets
        })

    return events
