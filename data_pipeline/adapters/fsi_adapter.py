"""
AGNI-NETRA — Forest Survey of India (FSI) & Protected Areas Forest Intelligence Adapter
Integrates:
1. Forest Survey of India (ISFR 2021) District Forest Cover & Canopy Density
2. Wildlife Institute of India (WII) Protected Area Network (NP, WLS, TR, BR)
3. FSI Van Agni Geo-Portal Source Provenance
"""

import time
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
import httpx
from sqlalchemy import text

from data_pipeline.adapters.base import (
    LandCoverSourceAdapter, NormalizedLULCRecord, SourceProvenance
)


class FSIAdapter(LandCoverSourceAdapter):
    """
    FSI Forest Intelligence & Protected Area Spatial Adapter.
    Executes PostGIS Point-in-Polygon containment and geodesic distance calculations
    against verified Indian Protected Areas and ISFR canopy density statistics.
    """

    FSI_PORTAL_URL = "https://fsi.nic.in/"

    @property
    def source_name(self) -> str:
        return "FSI_ISFR_2021"

    def validate_connection(self) -> Dict[str, Any]:
        """
        Validates reachability of official FSI portal and verifies PostGIS table health.
        """
        start = time.time()
        fsi_online = False
        portal_msg = "FSI Official Portal reachable."

        try:
            resp = httpx.get(self.FSI_PORTAL_URL, timeout=5.0, verify=False, follow_redirects=True)
            if resp.status_code == 200:
                fsi_online = True
            else:
                portal_msg = f"FSI portal returned HTTP {resp.status_code}"
        except Exception as e:
            portal_msg = f"FSI portal check: {e.__class__.__name__}"

        db_healthy = False
        pa_count, stat_count = 0, 0
        try:
            from backend.app.core.database import engine
            with engine.connect() as conn:
                pa_count = conn.execute(text("SELECT COUNT(*) FROM protected_areas;")).scalar() or 0
                stat_count = conn.execute(text("SELECT COUNT(*) FROM fsi_isfr_district_forest_stats;")).scalar() or 0
                db_healthy = (pa_count > 0 and stat_count > 0)
        except Exception:
            db_healthy = False

        latency = int((time.time() - start) * 1000)

        if db_healthy:
            return {
                "source": self.source_name,
                "status": "HEALTHY",
                "configured": True,
                "message": f"FSI ISFR 2021 & Protected Areas PostGIS Engine Active ({pa_count} PAs, {stat_count} ISFR district records). {portal_msg}",
                "latency_ms": latency,
                "last_success": datetime.now(timezone.utc).isoformat(),
                "last_failure": None,
                "records_processed": pa_count + stat_count
            }
        else:
            return {
                "source": self.source_name,
                "status": "DEGRADED" if fsi_online else "NOT_CONFIGURED",
                "configured": True,
                "message": "FSI tables not populated in database.",
                "latency_ms": latency,
                "last_success": None,
                "last_failure": datetime.now(timezone.utc).isoformat(),
                "records_processed": 0
            }

    def classify_location(
        self,
        latitude: float,
        longitude: float
    ) -> NormalizedLULCRecord:
        """
        Evaluates geographic coordinate against official Indian Protected Areas and ISFR canopy density statistics.
        """
        pa_match = None
        dist_pa = 999999.0
        dist_forest = 999999.0
        district_name = None
        forest_pct = None

        try:
            from backend.app.core.database import engine
            with engine.connect() as conn:
                # 1. Check direct Protected Area containment
                pa_match = conn.execute(text("""
                    SELECT id, pa_name, pa_type, state, district, area_sqkm, legal_status
                    FROM protected_areas
                    WHERE ST_Contains(geom, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326))
                    LIMIT 1;
                """), {"lat": latitude, "lon": longitude}).fetchone()

                # 2. Compute geodesic distance to nearest Protected Area
                dist_pa_row = conn.execute(text("""
                    SELECT MIN(ST_Distance(ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, geom::geography)) as dist_pa
                    FROM protected_areas;
                """), {"lat": latitude, "lon": longitude}).fetchone()
                if dist_pa_row and dist_pa_row.dist_pa is not None:
                    dist_pa = round(float(dist_pa_row.dist_pa), 1)

                # 3. Compute geodesic distance to nearest Bhuvan forest feature
                dist_for_row = conn.execute(text("""
                    SELECT MIN(ST_Distance(ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, geom::geography)) as dist_for
                    FROM lulc_spatial_features
                    WHERE canonical_class = 'FOREST';
                """), {"lat": latitude, "lon": longitude}).fetchone()
                if dist_for_row and dist_for_row.dist_for is not None:
                    dist_forest = round(float(dist_for_row.dist_for), 1)

                # 4. Check district ISFR statistics via admin_boundaries
                isfr_row = conn.execute(text("""
                    SELECT s.district, s.percent_of_geo_area, s.total_forest_sqkm, s.very_dense_forest_sqkm
                    FROM admin_boundaries a
                    JOIN fsi_isfr_district_forest_stats s ON a.id = s.admin_boundary_id
                    WHERE a.admin_level = 2
                      AND ST_Contains(a.geom, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326))
                    LIMIT 1;
                """), {"lat": latitude, "lon": longitude}).fetchone()
                if isfr_row:
                    district_name = isfr_row.district
                    forest_pct = float(isfr_row.percent_of_geo_area)

        except Exception:
            pass

        # Determine explicit rule-based Forest Context Level
        if pa_match or dist_forest == 0.0 or dist_pa <= 500.0:
            context_level = "HIGH"
            density_class = "VDF" if pa_match else "MDF"
            confidence = 0.98 if pa_match else 0.95
        elif dist_pa <= 5000.0 or dist_forest <= 1000.0:
            context_level = "MEDIUM"
            density_class = "OF"
            confidence = 0.90
        elif dist_pa <= 10000.0 or dist_forest <= 3000.0:
            context_level = "LOW"
            density_class = "SCRUB"
            confidence = 0.85
        else:
            context_level = "NONE"
            density_class = "NON_FOREST"
            confidence = 0.95

        prov = SourceProvenance(
            source_name="FSI_ISFR_2021" if not pa_match else "WII_NATIONAL_WILDLIFE_DATABASE",
            source_record_id=f"FSI_FOR_{latitude:.4f}_{longitude:.4f}" if not pa_match else f"WII_{pa_match.id}",
            source_version="ISFR-2021" if not pa_match else "WII-PA-2024",
            acquisition_time=datetime(2021, 12, 31, tzinfo=timezone.utc),
            raw_reference="FSI_ISFR_CANOPY_DENSITY_MAPPING" if not pa_match else "WII_PROTECTED_AREAS_NETWORK",
            data_quality_score=confidence,
            additional_metadata={
                "forest_context_level": context_level,
                "forest_density_class": density_class,
                "is_inside_protected_area": bool(pa_match),
                "protected_area_name": pa_match.pa_name if pa_match else None,
                "protected_area_type": pa_match.pa_type if pa_match else None,
                "distance_to_protected_area_m": dist_pa,
                "distance_to_forest_m": dist_forest,
                "is_within_10km_esz": (dist_pa <= 10000.0),
                "isfr_district": district_name,
                "district_forest_cover_pct": forest_pct,
                "reference_year": 2021 if not pa_match else 2024
            }
        )

        return NormalizedLULCRecord(
            category="Forest" if context_level in ("HIGH", "MEDIUM") else "Non-Forest",
            zone_code=5 if context_level in ("HIGH", "MEDIUM") else 0,
            zone_description=f"{pa_match.pa_name} ({pa_match.pa_type})" if pa_match else f"Forest Context: {context_level} (Dist: {dist_forest:,.1f}m)",
            is_industrial_zone=False,
            distance_to_forest_m=dist_forest,
            distance_to_agri_m=999999.0,
            distance_to_settlement_m=999999.0,
            distance_to_water_m=999999.0,
            distance_to_mine_m=999999.0,
            provenance=prov
        )


fsi_adapter = FSIAdapter()
