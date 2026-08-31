"""
AGNI-NETRA — ISRO Bhuvan Thematic Geospatial Services & LULC Adapter
Integrates official Bhuvan 1:50,000 / 24m Land Use Land Cover (Resourcesat-2/2A LISS-III derived)
PostGIS spatial features and classification services from NRSC / ISRO.
"""

import time
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
import httpx
from sqlalchemy import text

from data_pipeline.adapters.base import (
    LandCoverSourceAdapter, NormalizedLULCRecord, SourceProvenance
)
from data_pipeline.adapters.lulc_adapter import lulc_engine


class BhuvanLULCAdapter(LandCoverSourceAdapter):
    """
    ISRO Bhuvan Thematic Geospatial Services & LULC Adapter.
    Integrates Bhuvan 1:50,000 / 24m Land Use Land Cover (Resourcesat-2/2A LISS-III derived)
    thematic services from NRSC / ISRO.
    """

    BHUVAN_WMS_URL = "https://bhuvan-vec1.nrsc.gov.in/bhuvan/wms"

    @property
    def source_name(self) -> str:
        return "ISRO_BHUVAN"

    def validate_connection(self) -> Dict[str, Any]:
        """
        Validates connectivity to ISRO Bhuvan endpoints and queries PostGIS LULC database status.
        """
        start = time.time()
        bhuvan_online = False
        portal_msg = "Bhuvan web portal reachable."

        try:
            resp = httpx.get("https://bhuvan.nrsc.gov.in", timeout=5.0)
            if resp.status_code in (200, 301, 302):
                bhuvan_online = True
            else:
                portal_msg = f"Bhuvan returned HTTP {resp.status_code}"
        except Exception as e:
            portal_msg = f"Bhuvan web portal check: {e.__class__.__name__}"

        # Query PostGIS LULC Table Status
        feature_count = 0
        class_count = 0
        db_healthy = False
        try:
            from backend.app.core.database import engine
            with engine.connect() as conn:
                r_feat = conn.execute(text("SELECT COUNT(*) FROM lulc_spatial_features;")).scalar()
                r_cls = conn.execute(text("SELECT COUNT(*) FROM lulc_classes;")).scalar()
                feature_count = r_feat or 0
                class_count = r_cls or 0
                db_healthy = (feature_count > 0 and class_count > 0)
        except Exception:
            db_healthy = False

        latency = int((time.time() - start) * 1000)

        if db_healthy:
            return {
                "source": self.source_name,
                "status": "HEALTHY",
                "configured": True,
                "message": f"ISRO Bhuvan 1:50K / 24m LULC PostGIS Engine Active ({class_count} classes, {feature_count} spatial pilot features). {portal_msg}",
                "latency_ms": latency,
                "last_success": datetime.now(timezone.utc).isoformat(),
                "last_failure": None,
                "records_processed": feature_count
            }
        else:
            return {
                "source": self.source_name,
                "status": "DEGRADED" if bhuvan_online else "NOT_CONFIGURED",
                "configured": True,
                "message": "Bhuvan PostGIS tables not populated; using in-memory demo fallback.",
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
        Classifies geographic coordinate into ISRO Bhuvan LULC categories using PostGIS spatial engine.
        Canonical categories: BUILT_UP_INDUSTRIAL, BUILT_UP_URBAN, MINING, AGRICULTURE_CROPLAND, FOREST, WATER_BODIES, BARREN_SCRUB, OTHER.
        """
        category, desc, dists = lulc_engine.classify_location(latitude, longitude)
        is_fallback = ("[DEMO_FALLBACK]" in str(desc))
        is_covered = (category != "Unknown" and not is_fallback)
        is_ind = (category in ("Industrial", "Mining") or "Industrial" in str(desc)) if is_covered else False

        if is_covered:
            coverage_status = "REAL"
            source_coverage = "COVERED"
            source_name = "ISRO_BHUVAN_LULC_50K"
            quality_score = 0.96
            match_method = "POSTGIS_POINT_IN_POLYGON"
        elif is_fallback:
            coverage_status = "DEMO_FALLBACK"
            source_coverage = "DEMO_MOCK"
            source_name = "SYNTHETIC_DEMO_FALLBACK"
            quality_score = 0.50
            match_method = "SYNTHETIC_POINT_IN_BOX"
        else:
            coverage_status = "NO_COVERAGE"
            source_coverage = "UNAVAILABLE"
            source_name = "ISRO_BHUVAN_50K"
            quality_score = 0.0
            match_method = "NO_SPATIAL_INTERSECT"

        prov = SourceProvenance(
            source_name=source_name,
            source_record_id=f"BHUVAN_LULC_{latitude:.4f}_{longitude:.4f}",
            source_version="LULC-50K-CYCLE-V" if not is_fallback else "DEMO-SYNTHETIC-V1",
            acquisition_time=datetime(2025, 1, 15, tzinfo=timezone.utc),
            raw_reference="NRSC_ISRO_BHUVAN_THEMATIC_PORTAL" if is_covered else ("INTERNAL_SYNTHETIC_BOUNDING_BOX" if is_fallback else "NO_BHUVAN_PILOT_COVERAGE"),
            data_quality_score=quality_score,
            additional_metadata={
                "coverage_status": coverage_status,
                "source_coverage": source_coverage,
                "spatial_resolution": "24 meters (1:50,000 Scale)" if not is_fallback else "Synthetic Polygon Buffer",
                "sensor_platform": "Resourcesat-2 / Resourcesat-2A LISS-III" if not is_fallback else "Synthetic Mock Geometry",
                "classification_scheme": "NRSC Level-II National LULC Scheme",
                "reference_year": 2025,
                "match_method": match_method
            }
        )

        zone_code = 1 if category == "Industrial" else \
                    2 if category == "Mining" else \
                    3 if category == "Urban" else \
                    4 if category == "Agricultural" else \
                    5 if category == "Forest" else \
                    6 if category == "Water" else \
                    0 if category == "Unknown" else 7

        return NormalizedLULCRecord(
            category=category,
            zone_code=zone_code,
            zone_description=desc or f"{category} Terrain",
            is_industrial_zone=is_ind,
            distance_to_forest_m=dists.get("dist_to_forest_m", 999999.0),
            distance_to_agri_m=dists.get("dist_to_agri_m", 999999.0),
            distance_to_settlement_m=dists.get("dist_to_settlement_m", 4200.0),
            distance_to_water_m=dists.get("dist_to_water_m", 999999.0),
            distance_to_mine_m=dists.get("dist_to_mine_m", 999999.0),
            provenance=prov
        )


bhuvan_adapter = BhuvanLULCAdapter()
