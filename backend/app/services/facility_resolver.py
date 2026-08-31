import re
import difflib
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session

from backend.app.models.domain import IndustrialFacility, CandidateFacility
from data_pipeline.adapters.base import NormalizedFacilityRecord
from backend.app.services.spatial_engine import haversine_distance_m


def normalize_facility_name(name: str) -> str:
    """
    Standardizes plant names by removing generic tokens (Ltd, Complex, Station, Plant, Works).
    """
    cleaned = name.lower()
    cleaned = re.sub(r"[^\w\s]", "", cleaned)
    tokens_to_remove = ["ltd", "limited", "pvt", "private", "complex", "station", "plant", "works", "super", "thermal", "integrated"]
    tokens = [t for t in cleaned.split() if t not in tokens_to_remove]
    return " ".join(tokens)


def calculate_name_similarity(name1: str, name2: str) -> float:
    """
    Calculates token-based fuzzy string similarity ratio between two facility names.
    """
    n1 = normalize_facility_name(name1)
    n2 = normalize_facility_name(name2)
    return difflib.SequenceMatcher(None, n1, n2).ratio()


class FacilityEntityResolver:
    """
    Multi-Source Industrial Facility Entity Resolution & Canonical Registry Service.
    Merges overlapping records from OpenStreetMap (OSM), Central Electricity Authority (CEA),
    and State Pollution Control Boards (SPCB) into deduplicated canonical entities.
    """

    def __init__(self, spatial_match_distance_m: float = 600.0, name_similarity_threshold: float = 0.75):
        self.spatial_match_distance_m = spatial_match_distance_m
        self.name_similarity_threshold = name_similarity_threshold

    def resolve_and_sync_facilities(
        self,
        db: Session,
        incoming_records: List[NormalizedFacilityRecord]
    ) -> Dict[str, Any]:
        """
        Executes entity resolution against the existing PostgreSQL/PostGIS database.
        Inserts new facilities or enriches existing records with additional source provenance.
        """
        existing_facilities = db.query(IndustrialFacility).all()
        created_count = 0
        updated_count = 0

        for record in incoming_records:
            match_found = False

            # Check for existing match
            for existing in existing_facilities:
                if (
                    record.latitude is None or record.longitude is None or
                    existing.latitude is None or existing.longitude is None
                ):
                    continue

                if (
                    abs(record.latitude - existing.latitude) > 0.05 or
                    abs(record.longitude - existing.longitude) > 0.05
                ):
                    continue

                # 1. Spatial proximity check
                dist = haversine_distance_m(record.latitude, record.longitude, existing.latitude, existing.longitude)
                
                if dist <= self.spatial_match_distance_m:
                    # 2. Name similarity or exact facility type concordance
                    name_sim = calculate_name_similarity(record.name, existing.name)
                    type_match = (record.facility_type == existing.facility_type)

                    if name_sim >= self.name_similarity_threshold or (dist <= 250.0 and type_match):
                        # Match confirmed: enrich existing record
                        match_found = True
                        existing_sources = existing.contact_info.get("sources", [])
                        new_source_tag = f"{record.source}:{record.source_id}"
                        if new_source_tag not in existing_sources:
                            existing_sources.append(new_source_tag)
                            existing.contact_info["sources"] = existing_sources
                            existing.confidence_score = min(1.0, existing.confidence_score + 0.05)
                            updated_count += 1
                        break

            if not match_found:
                # Create new canonical facility
                state_code = record.state[:3].upper() if record.state else "IND"
                type_prefix = record.facility_type[:4].upper()
                seq = len(existing_facilities) + created_count + 1
                canonical_source_id = f"FAC-{state_code}-{type_prefix}-{seq:04d}"

                new_facility = IndustrialFacility(
                    name=record.name,
                    facility_type=record.facility_type,
                    status="KNOWN",
                    source=record.source,
                    source_id=canonical_source_id,
                    state=record.state,
                    district=record.district,
                    latitude=record.latitude,
                    longitude=record.longitude,
                    boundary_geojson=record.boundary_geojson,
                    confidence_score=record.confidence_score,
                    operating_hours="24x7",
                    contact_info={
                        "operator": record.operator,
                        "primary_source": record.source,
                        "sources": [f"{record.source}:{record.source_id}"],
                        "raw_tags": record.raw_tags
                    }
                )
                db.add(new_facility)
                existing_facilities.append(new_facility)
                created_count += 1

        db.commit()

        return {
            "status": "SUCCESS",
            "total_processed": len(incoming_records),
            "created": created_count,
            "updated": updated_count,
            "canonical_registry_total": len(existing_facilities)
        }

    def partition_sources(
        self,
        db: Session
    ) -> Dict[str, Any]:
        """
        Partitions the facility database into Known Facilities, Candidate Facilities, and Uncataloged Sources.
        """
        known = db.query(IndustrialFacility).filter(IndustrialFacility.status == "KNOWN").count()
        candidates = db.query(CandidateFacility).filter(CandidateFacility.status == "CANDIDATE").count()
        
        return {
            "known_facilities_count": known,
            "candidate_facilities_count": candidates,
            "status": "HEALTHY"
        }


facility_resolver = FacilityEntityResolver()
