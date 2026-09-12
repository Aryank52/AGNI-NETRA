"""
AGNI-NETRA — Authoritative India Boundary & Geographic Integrity Service
Phase 18: Strict India-First Operating Scope

Responsibilities:
1. Authoritative sovereign India boundary containment (polygon-level via PostGIS admin_boundaries).
2. Elimination of bounding-box as country proxy.
3. Non-destructive classification of out-of-boundary telemetry (e.g. Sri Lanka, neighboring waters/states).
4. Administrative hierarchy resolution (State -> District -> Subdistrict/Tehsil).
5. Canonical geographic provenance tagging and auditing.
"""

import time
import json
import logging
from typing import List, Tuple, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.app.core.database import SessionLocal

logger = logging.getLogger("agni_netra.india_boundary_service")

# Coarse Bounding Box for regional acquisition (used only for pre-filtering ingestion networks, NEVER as boundary)
REGIONAL_ACQUISITION_BBOX = {
    "min_lat": 6.0,
    "min_lon": 68.0,
    "max_lat": 37.5,
    "max_lon": 97.5,
    "note": "REGIONAL ACQUISITION BBOX ONLY — NOT AUTHORITATIVE SOVEREIGN BOUNDARY"
}

# Neighboring geographic bounding heuristics for provenance tagging
NEIGHBORING_REGIONS = [
    {
        "name": "Sri Lanka",
        "min_lat": 5.8,
        "max_lat": 9.9,
        "min_lon": 79.5,
        "max_lon": 82.0
    },
    {
        "name": "Pakistan",
        "min_lat": 23.5,
        "max_lat": 37.2,
        "min_lon": 60.5,
        "max_lon": 75.5
    },
    {
        "name": "Bangladesh",
        "min_lat": 20.5,
        "max_lat": 26.7,
        "min_lon": 88.0,
        "max_lon": 92.7
    },
    {
        "name": "Nepal",
        "min_lat": 26.3,
        "max_lat": 30.5,
        "min_lon": 80.0,
        "max_lon": 88.2
    },
    {
        "name": "Bhutan",
        "min_lat": 26.7,
        "max_lat": 28.3,
        "min_lon": 88.8,
        "max_lon": 92.2
    },
    {
        "name": "Myanmar",
        "min_lat": 9.5,
        "max_lat": 28.5,
        "min_lon": 92.2,
        "max_lon": 101.2
    }
]

# Maritime extent heuristics (approximate)
MARITIME_REGIONS = [
    {
        "name": "Arabian Sea",
        "min_lat": 7.0,
        "max_lat": 25.0,
        "min_lon": 55.0,
        "max_lon": 73.0
    },
    {
        "name": "Bay of Bengal",
        "min_lat": 6.0,
        "max_lat": 22.0,
        "min_lon": 82.0,
        "max_lon": 95.0
    },
    {
        "name": "Indian Ocean",
        "min_lat": 0.0,
        "max_lat": 6.0,
        "min_lon": 65.0,
        "max_lon": 95.0
    }
]


class IndiaBoundaryService:
    """
    Canonical singleton service enforcing authoritative India territorial boundaries
    and administrative hierarchy resolution.
    """

    _instance = None
    _cached_geojson: Optional[Dict[str, Any]] = None
    _cached_geojson_timestamp: float = 0.0
    _CACHE_TTL_SECONDS: float = 1800.0  # 30 minutes

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(IndiaBoundaryService, cls).__new__(cls)
        return cls._instance

    @staticmethod
    def detect_neighboring_country(lat: float, lon: float) -> str:
        """
        Identifies neighboring countries or maritime zones when coordinates are outside India.
        """
        for n in NEIGHBORING_REGIONS:
            if n["min_lat"] <= lat <= n["max_lat"] and n["min_lon"] <= lon <= n["max_lon"]:
                return n["name"]
        for m in MARITIME_REGIONS:
            if m["min_lat"] <= lat <= m["max_lat"] and m["min_lon"] <= lon <= m["max_lon"]:
                return m["name"]
        return "OUTSIDE_INDIA"

    def is_point_inside_india(
        self,
        lat: float,
        lon: float,
        db: Optional[Session] = None
    ) -> Tuple[bool, Optional[str], Optional[str], Optional[str]]:
        """
        Determines if (lat, lon) is strictly within sovereign India administrative boundaries.
        Returns:
            (is_inside: bool, state_name: Optional[str], district_name: Optional[str], subdistrict_name: Optional[str])
        """
        # Rapid coordinate range rejection
        if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
            return False, None, None, None
        
        # Coarse exclusion filter for fast rejection of distant continents
        if lat < 5.0 or lat > 38.0 or lon < 65.0 or lon > 100.0:
            return False, None, None, None

        own_session = False
        if db is None:
            db = SessionLocal()
            own_session = True

        try:
            query = text("""
                WITH pt AS (
                    SELECT ST_SetSRID(ST_MakePoint(:lon, :lat), 4326) as geom
                ),
                st AS (
                    SELECT state_code, normalized_name as state_name
                    FROM admin_boundaries, pt
                    WHERE admin_level = 1 AND ST_Within(pt.geom, admin_boundaries.geom)
                    LIMIT 1
                ),
                dt AS (
                    SELECT district_code, normalized_name as district_name
                    FROM admin_boundaries, pt
                    WHERE admin_level = 2 AND ST_Within(pt.geom, admin_boundaries.geom)
                    LIMIT 1
                ),
                sub AS (
                    SELECT subdistrict_code, normalized_name as subdistrict_name
                    FROM admin_boundaries, pt
                    WHERE admin_level = 3 AND ST_Within(pt.geom, admin_boundaries.geom)
                    LIMIT 1
                )
                SELECT 
                    st.state_name,
                    dt.district_name,
                    sub.subdistrict_name
                FROM (SELECT 1) dummy
                LEFT JOIN st ON TRUE
                LEFT JOIN dt ON TRUE
                LEFT JOIN sub ON TRUE;
            """)
            row = db.execute(query, {"lat": lat, "lon": lon}).fetchone()
            if row and row[0]:
                return True, row[0], row[1], row[2]
            return False, None, None, None
        except Exception as e:
            logger.error(f"Error during PostGIS containment check for ({lat}, {lon}): {e}")
            return False, None, None, None
        finally:
            if own_session:
                db.close()

    def get_hierarchical_context(
        self,
        lat: float,
        lon: float,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Returns full structured administrative and sovereign provenance context.
        """
        own_session = False
        if db is None:
            db = SessionLocal()
            own_session = True

        try:
            query = text("""
                WITH pt AS (
                    SELECT ST_SetSRID(ST_MakePoint(:lon, :lat), 4326) as geom
                ),
                st AS (
                    SELECT state_code, normalized_name as state_name
                    FROM admin_boundaries, pt
                    WHERE admin_level = 1 AND ST_Within(pt.geom, admin_boundaries.geom)
                    LIMIT 1
                ),
                dt AS (
                    SELECT district_code, normalized_name as district_name
                    FROM admin_boundaries, pt
                    WHERE admin_level = 2 AND ST_Within(pt.geom, admin_boundaries.geom)
                    LIMIT 1
                ),
                sub AS (
                    SELECT subdistrict_code, normalized_name as subdistrict_name
                    FROM admin_boundaries, pt
                    WHERE admin_level = 3 AND ST_Within(pt.geom, admin_boundaries.geom)
                    LIMIT 1
                )
                SELECT 
                    st.state_name, st.state_code,
                    dt.district_name, dt.district_code,
                    sub.subdistrict_name, sub.subdistrict_code
                FROM (SELECT 1) dummy
                LEFT JOIN st ON TRUE
                LEFT JOIN dt ON TRUE
                LEFT JOIN sub ON TRUE;
            """)
            row = db.execute(query, {"lat": lat, "lon": lon}).fetchone()
            if row and row[0]:
                return {
                    "is_inside_india": True,
                    "geographic_scope": "INDIA",
                    "country": "India",
                    "state_name": row[0],
                    "state_code": row[1],
                    "district_name": row[2],
                    "district_code": row[3],
                    "subdistrict_name": row[4],
                    "subdistrict_code": row[5],
                    "boundary_authority": "Survey of India / Local Government Directory (LGD)",
                    "srid": 4326,
                    "boundary_level": 1,
                    "validation_method": "POSTGIS_ST_WITHIN_POLYGON"
                }
            
            neighbor = self.detect_neighboring_country(lat, lon)
            return {
                "is_inside_india": False,
                "geographic_scope": "OUTSIDE_INDIA",
                "country": "OUTSIDE_INDIA",
                "detected_country": neighbor,
                "state_name": None,
                "state_code": None,
                "district_name": None,
                "district_code": None,
                "subdistrict_name": None,
                "subdistrict_code": None,
                "boundary_authority": "Survey of India / Local Government Directory (LGD)",
                "srid": 4326,
                "boundary_level": 0,
                "validation_method": "POSTGIS_ST_WITHIN_POLYGON",
                "rejection_reason": f"Point ({lat}, {lon}) lies outside India sovereign polygon boundary (identified as {neighbor})"
            }
        finally:
            if own_session:
                db.close()

    def filter_live_observations_for_india(
        self,
        observations: List[Dict[str, Any]],
        db: Optional[Session] = None
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Partitions raw telemetry observations into:
        (india_observations, outside_india_observations)
        Preserves complete data provenance for both sets.
        """
        india_records: List[Dict[str, Any]] = []
        outside_records: List[Dict[str, Any]] = []

        own_session = False
        if db is None:
            db = SessionLocal()
            own_session = True

        try:
            for obs in observations:
                lat = float(obs.get("latitude") or obs.get("lat") or 0.0)
                lon = float(obs.get("longitude") or obs.get("lon") or 0.0)

                is_inside, state_name, district_name, subdistrict_name = self.is_point_inside_india(lat, lon, db=db)
                
                # Copy or update metadata
                record = dict(obs)
                if is_inside:
                    record["country"] = "India"
                    record["geographic_scope"] = "INDIA"
                    record["jurisdiction"] = state_name or "India"
                    record["admin_state"] = state_name
                    record["admin_district"] = district_name
                    record["admin_subdistrict"] = subdistrict_name
                    record["sovereign_filter"] = "PASS_SOVEREIGN_INDIA"
                    india_records.append(record)
                else:
                    detected_country = self.detect_neighboring_country(lat, lon)
                    record["country"] = "OUTSIDE_INDIA"
                    record["geographic_scope"] = "OUTSIDE_INDIA"
                    record["detected_country"] = detected_country
                    record["jurisdiction"] = detected_country
                    record["admin_state"] = None
                    record["admin_district"] = None
                    record["admin_subdistrict"] = None
                    record["sovereign_filter"] = "EXCLUDED_OUTSIDE_INDIA"
                    
                    # Track exclusion reason in quality metadata
                    reasons = list(record.get("quality_reasons") or [])
                    reasons.append(f"GEOGRAPHIC_SCOPE: Point ({lat}, {lon}) is outside sovereign India ({detected_country})")
                    record["quality_reasons"] = reasons
                    outside_records.append(record)

            return india_records, outside_records
        finally:
            if own_session:
                db.close()

    def classify_and_remediate_ingestion_records(self, db: Session) -> Dict[str, Any]:
        """
        Non-destructively classifies and remediates existing raw records in ingestion_records:
        - Classifies records strictly inside India boundary: country='India', geographic_scope='INDIA'
        - Classifies records outside India boundary: country='OUTSIDE_INDIA', jurisdiction=<Neighboring country/waters>
        - NEVER drops or deletes raw records, preserving full provenance and original timestamps.
        """
        logger.info("Starting non-destructive remediation of ingestion_records...")
        
        # Step 1: Identify records outside India boundary
        find_outside_query = text("""
            SELECT ir.id, ir.latitude, ir.longitude, ir.country, ir.jurisdiction, ir.normalized_payload, ir.quality_reasons
            FROM ingestion_records ir
            WHERE ir.latitude IS NOT NULL AND ir.longitude IS NOT NULL
              AND NOT EXISTS (
                  SELECT 1 FROM admin_boundaries ab
                  WHERE ab.admin_level = 1 
                    AND ST_Within(ST_SetSRID(ST_MakePoint(ir.longitude, ir.latitude), 4326), ab.geom)
              );
        """)
        outside_rows = db.execute(find_outside_query).fetchall()

        outside_remediated = 0
        sri_lanka_count = 0

        for row in outside_rows:
            rec_id, lat, lon, curr_country, curr_jurisdiction, norm_payload, q_reasons = row
            detected_neighbor = self.detect_neighboring_country(lat, lon)
            if detected_neighbor == "Sri Lanka":
                sri_lanka_count += 1

            norm_payload = dict(norm_payload or {})
            norm_payload["geographic_scope"] = "OUTSIDE_INDIA"
            norm_payload["detected_country"] = detected_neighbor
            norm_payload["sovereign_filter"] = "EXCLUDED_OUTSIDE_INDIA"

            q_reasons = list(q_reasons or [])
            reason_str = f"GEOGRAPHIC_SCOPE: Outside sovereign territory of India ({detected_neighbor})"
            if reason_str not in q_reasons:
                q_reasons.append(reason_str)

            update_query = text("""
                UPDATE ingestion_records
                SET country = 'OUTSIDE_INDIA',
                    jurisdiction = :jurisdiction,
                    normalized_payload = :norm_payload,
                    quality_reasons = :q_reasons
                WHERE id = :id;
            """)
            db.execute(update_query, {
                "id": rec_id,
                "jurisdiction": detected_neighbor,
                "norm_payload": json.dumps(norm_payload),
                "q_reasons": json.dumps(q_reasons)
            })
            outside_remediated += 1

        # Step 2: Ensure inside India records are standardized
        find_inside_query = text("""
            SELECT ir.id, ab.normalized_name as state_name, ir.normalized_payload
            FROM ingestion_records ir
            JOIN admin_boundaries ab ON ab.admin_level = 1 
              AND ST_Within(ST_SetSRID(ST_MakePoint(ir.longitude, ir.latitude), 4326), ab.geom)
            WHERE ir.country != 'India' OR ir.country IS NULL;
        """)
        inside_rows = db.execute(find_inside_query).fetchall()
        inside_remediated = 0

        for row in inside_rows:
            rec_id, state_name, norm_payload = row
            norm_payload = dict(norm_payload or {})
            norm_payload["geographic_scope"] = "INDIA"
            norm_payload["sovereign_filter"] = "PASS_SOVEREIGN_INDIA"

            update_inside = text("""
                UPDATE ingestion_records
                SET country = 'India',
                    jurisdiction = COALESCE(jurisdiction, :state_name),
                    normalized_payload = :norm_payload
                WHERE id = :id;
            """)
            db.execute(update_inside, {
                "id": rec_id,
                "state_name": state_name,
                "norm_payload": json.dumps(norm_payload)
            })
            inside_remediated += 1

        db.commit()

        # Audit current counts
        total_records = db.execute(text("SELECT COUNT(*) FROM ingestion_records;")).scalar() or 0
        india_records = db.execute(text("SELECT COUNT(*) FROM ingestion_records WHERE country = 'India';")).scalar() or 0
        outside_records = db.execute(text("SELECT COUNT(*) FROM ingestion_records WHERE country = 'OUTSIDE_INDIA';")).scalar() or 0

        summary = {
            "total_ingestion_records": total_records,
            "india_records": india_records,
            "outside_india_records": outside_records,
            "outside_remediated": outside_remediated,
            "sri_lanka_records_isolated": sri_lanka_count,
            "inside_remediated": inside_remediated,
            "provenance_preserved": True
        }
        logger.info(f"Remediation complete: {summary}")
        return summary

    def get_authoritative_india_geojson(self, db: Session, simplified: bool = True) -> Dict[str, Any]:
        """
        Returns simplified GeoJSON FeatureCollection of all 36 States/UTs of India.
        Results are cached in-memory with TTL.
        """
        now = time.time()
        if self._cached_geojson is not None and (now - self._cached_geojson_timestamp) < self._CACHE_TTL_SECONDS:
            return self._cached_geojson

        tolerance = 0.01 if simplified else 0.001
        query = text("""
            SELECT 
                state_code,
                normalized_name as state_name,
                ST_AsGeoJSON(ST_Simplify(geom, :tol)) as geojson
            FROM admin_boundaries
            WHERE admin_level = 1
            ORDER BY normalized_name ASC;
        """)
        rows = db.execute(query, {"tol": tolerance}).fetchall()

        features = []
        for r in rows:
            if r[2]:
                try:
                    geometry = json.loads(r[2])
                    features.append({
                        "type": "Feature",
                        "properties": {
                            "state_code": r[0],
                            "state_name": r[1],
                            "country": "India",
                            "admin_level": 1,
                            "authority": "Survey of India / Local Government Directory"
                        },
                        "geometry": geometry
                    })
                except Exception as e:
                    logger.warning(f"Failed to parse GeoJSON for state {r[1]}: {e}")

        feature_collection = {
            "type": "FeatureCollection",
            "crs": {
                "type": "name",
                "properties": {
                    "name": "urn:ogc:def:crs:OGC:1.3:CRS84"
                }
            },
            "features": features
        }

        self._cached_geojson = feature_collection
        self._cached_geojson_timestamp = time.time()
        return feature_collection


# Canonical singleton export
india_boundary_service = IndiaBoundaryService()
