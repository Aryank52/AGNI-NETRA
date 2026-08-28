import json
from typing import List, Dict, Any
from shapely.geometry import shape, Point
import httpx


class OSMIndustrialAdapter:
    """
    OpenStreetMap Overpass API adapter for querying and normalizing industrial facilities in India.
    Extracts: landuse=industrial, industrial=*, power=plant, man_made=works/petroleum_well.
    """

    OVERPASS_URL = "https://overpass-api.de/api/interpreter"

    def fetch_facilities_by_bbox(
        self,
        min_lat: float,
        min_lon: float,
        max_lat: float,
        max_lon: float
    ) -> List[Dict[str, Any]]:
        """
        Queries OSM Overpass for industrial nodes, ways, and relations within bounding box.
        """
        query = f"""
        [out:json][timeout:25];
        (
          node["landuse"="industrial"]({min_lat},{min_lon},{max_lat},{max_lon});
          way["landuse"="industrial"]({min_lat},{min_lon},{max_lat},{max_lon});
          node["power"="plant"]({min_lat},{min_lon},{max_lat},{max_lon});
          way["power"="plant"]({min_lat},{min_lon},{max_lat},{max_lon});
          node["man_made"="petroleum_well"]({min_lat},{min_lon},{max_lat},{max_lon});
          node["industrial"]({min_lat},{min_lon},{max_lat},{max_lon});
        );
        out center;
        """
        try:
            resp = httpx.post(self.OVERPASS_URL, data={"data": query}, timeout=30.0)
            if resp.status_code != 200:
                return []
            
            data = resp.json()
            return self._parse_elements(data.get("elements", []))
        except Exception:
            return []

    def _parse_elements(self, elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        facilities = []
        for el in elements:
            tags = el.get("tags", {})
            name = tags.get("name") or tags.get("operator") or f"Industrial Facility OSM #{el.get('id')}"
            
            lat = el.get("lat") or el.get("center", {}).get("lat")
            lon = el.get("lon") or el.get("center", {}).get("lon")
            if not lat or not lon:
                continue

            # Classify facility type
            if tags.get("power") == "plant" or "power" in tags.get("industrial", ""):
                fac_type = "POWER_PLANT"
            elif "oil" in name.lower() or "refinery" in name.lower() or "petroleum" in tags.get("man_made", ""):
                fac_type = "REFINERY"
            elif "steel" in name.lower() or "metallurgy" in tags.get("industrial", ""):
                fac_type = "STEEL_PLANT"
            elif "chemical" in name.lower():
                fac_type = "CHEMICAL"
            elif "cement" in name.lower():
                fac_type = "CEMENT"
            elif "mine" in name.lower() or tags.get("landuse") == "quarry":
                fac_type = "MINING"
            else:
                fac_type = "OTHER"

            facilities.append({
                "source": "OSM",
                "source_id": str(el.get("id")),
                "name": name,
                "facility_type": fac_type,
                "latitude": float(lat),
                "longitude": float(lon),
                "raw_tags": tags
            })

        return facilities
