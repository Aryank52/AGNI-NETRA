"""
AGNI-NETRA — Official PARIVESH Environmental Clearance Source Adapter
Exposes normalized environmental clearance records and spatial lookups.
"""

from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple

from data_pipeline.adapters.base import (
    FacilitySourceAdapter, NormalizedFacilityRecord, SourceProvenance
)
from backend.app.core.database import engine
from sqlalchemy import text


class PariveshFacilityAdapter(FacilitySourceAdapter):
    """
    Adapter for official MoEFCC PARIVESH Environmental Clearance Project Registry.
    Queries the PostGIS `parivesh_projects_staging` table.
    """

    @property
    def source_name(self) -> str:
        return "PARIVESH"

    def validate_connection(self) -> bool:
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1;"))
            return True
        except Exception:
            return False

    def fetch_facilities(
        self,
        state: Optional[str] = None,
        facility_types: Optional[List[str]] = None,
        bbox: Optional[Tuple[float, float, float, float]] = None,
        sector: Optional[str] = None,
        **kwargs
    ) -> List[NormalizedFacilityRecord]:
        records = []
        try:
            with engine.connect() as conn:
                query_str = """
                    SELECT id, proposal_id, project_name, project_type, proponent,
                           state, district, category, sector, clearance_type, clearance_status,
                           proposal_date, decision_date, forest_related_flag, wildlife_related_flag,
                           crz_related_flag, latitude, longitude, source_url, source_file,
                           source_date, raw_metadata, match_status, matched_facility_id
                    FROM parivesh_projects_staging
                    WHERE 1=1
                """
                params = {}
                if state and state.lower() != "all":
                    query_str += " AND lower(state) = lower(:state)"
                    params["state"] = state
                if sector and sector.lower() != "all":
                    query_str += " AND lower(sector) = lower(:sector)"
                    params["sector"] = sector

                query_str += " ORDER BY id LIMIT 500"
                rows = conn.execute(text(query_str), params).fetchall()

                for r in rows:
                    lat = r[16]
                    lon = r[17]
                    norm_rec = NormalizedFacilityRecord(
                        source="PARIVESH",
                        source_id=r[1],
                        name=r[2],
                        facility_type=r[3] or "ENVIRONMENTAL_PROJECT",
                        operator=r[4],
                        state=r[5] or "National / Unspecified",
                        district=r[6],
                        latitude=lat if lat is not None else 0.0,
                        longitude=lon if lon is not None else 0.0,
                        confidence_score=0.90 if r[22] in ["HIGH", "MEDIUM"] else 0.50,
                        operating_status="CLEARANCE_ACTIVE",
                        provenance=SourceProvenance(
                            source_name="PARIVESH",
                            source_record_id=r[1],
                            source_version="PARIVESH-2022-EC",
                            acquisition_time=datetime(2022, 12, 31, tzinfo=timezone.utc),
                            ingestion_time=datetime.now(timezone.utc),
                            raw_reference=r[18] or "https://parivesh.nic.in",
                            data_quality_score=0.95,
                            additional_metadata={
                                "proposal_id": r[1],
                                "category": r[7],
                                "sector": r[8],
                                "clearance_type": r[9],
                                "clearance_status": r[10],
                                "decision_date": r[12],
                                "forest_related": r[13],
                                "wildlife_related": r[14],
                                "crz_related": r[15],
                                "match_status": r[22],
                                "matched_facility_id": r[23]
                            }
                        ),
                        raw_tags=r[21] or {}
                    )
                    records.append(norm_rec)
        except Exception as e:
            print(f"[PARIVESH Adapter] Database query fallback: {e}")

        return records

    def get_clearance_by_facility_id(self, facility_id: str) -> Optional[Dict[str, Any]]:
        with engine.connect() as conn:
            row = conn.execute(text("""
                SELECT proposal_id, project_name, project_type, proponent,
                       state, district, category, sector, clearance_type, clearance_status,
                       decision_date, forest_related_flag, wildlife_related_flag,
                       crz_related_flag, match_confidence, match_score
                FROM parivesh_projects_staging
                WHERE matched_facility_id = :fac_id
                LIMIT 1;
            """), {"fac_id": facility_id}).fetchone()

            if row:
                return {
                    "proposal_id": row[0],
                    "project_name": row[1],
                    "project_type": row[2],
                    "proponent": row[3],
                    "state": row[4],
                    "district": row[5],
                    "category": row[6],
                    "sector": row[7],
                    "clearance_type": row[8],
                    "clearance_status": row[9],
                    "decision_date": row[10],
                    "forest_related": row[11],
                    "wildlife_related": row[12],
                    "crz_related": row[13],
                    "match_confidence": row[14],
                    "match_score": row[15]
                }
        return None


parivesh_adapter = PariveshFacilityAdapter()
