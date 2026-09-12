"""
AGNI-NETRA JARVIS Phase 16: Deduplication Engine
Multi-tier deduplication distinguishing:
- EXACT_DUPLICATE
- SOURCE_DUPLICATE
- CROSS_PROVIDER_DUPLICATE
- SAME_SOURCE_REPETITION
- UNIQUE
Deduplication NEVER deletes or drops records; it tags relationships to preserve
cross-sensor multi-provider fusion.
"""

import hashlib
import math
from typing import Dict, Any, List, Optional, Tuple
from backend.app.services.data_plane.models import DedupStatus


def compute_sha256_fingerprint(provider: str, dataset: str, src_id: str, lat: float, lon: float, ts_str: str) -> str:
    """Computes a deterministic SHA-256 fingerprint for exact matching."""
    raw = f"{provider.upper()}:{dataset.upper()}:{src_id}:{lat:.5f}:{lon:.5f}:{ts_str}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates great-circle distance in kilometers."""
    r = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r * c


class DeduplicationResult:
    def __init__(
        self,
        status: DedupStatus,
        fingerprint: str,
        matched_record_id: Optional[str] = None,
        reason: Optional[str] = None
    ):
        self.status = status
        self.fingerprint = fingerprint
        self.matched_record_id = matched_record_id
        self.reason = reason


class DeduplicationEngine:
    """
    Evaluates new records against existing in-memory / database observations.
    """

    @classmethod
    def evaluate(
        cls,
        candidate: Dict[str, Any],
        existing_records: List[Dict[str, Any]]
    ) -> DeduplicationResult:
        provider = str(candidate.get("provider", "")).upper()
        dataset = str(candidate.get("dataset", "")).upper()
        src_id = str(candidate.get("source_record_id", ""))
        lat = float(candidate.get("latitude") or 0.0)
        lon = float(candidate.get("longitude") or 0.0)
        obs_time = str(candidate.get("observation_time") or candidate.get("received_at", ""))

        fingerprint = compute_sha256_fingerprint(provider, dataset, src_id, lat, lon, obs_time)

        for ex in existing_records:
            ex_src_id = ex.get("source_record_id")
            # 1 & 2: Same source ID fast path
            if src_id and ex_src_id == src_id:
                ex_prov = str(ex.get("provider", "")).upper()
                if ex_prov == provider:
                    ex_id = ex.get("ingestion_id") or ex.get("id")
                    ex_ds = str(ex.get("dataset", "")).upper()
                    ex_lat = float(ex.get("latitude") or 0.0)
                    ex_lon = float(ex.get("longitude") or 0.0)
                    ex_time = str(ex.get("observation_time") or ex.get("received_at", ""))
                    if (
                        ex_ds == dataset and
                        abs(ex_lat - lat) < 0.0001 and
                        abs(ex_lon - lon) < 0.0001 and
                        ex_time == obs_time
                    ):
                        return DeduplicationResult(
                            status=DedupStatus.EXACT_DUPLICATE,
                            fingerprint=fingerprint,
                            matched_record_id=ex_id,
                            reason=f"Exact duplicate matching record {ex_id}"
                        )
                    return DeduplicationResult(
                        status=DedupStatus.SOURCE_DUPLICATE,
                        fingerprint=fingerprint,
                        matched_record_id=ex_id,
                        reason=f"Same source record ID {src_id} from provider {provider}"
                    )

            # Fast bounding box pre-filtering before string manipulations or trigonometry
            ex_lat = ex.get("latitude")
            if ex_lat is None:
                continue
            dlat = abs(float(ex_lat) - lat)
            if dlat > 0.015:
                continue

            ex_lon = ex.get("longitude")
            if ex_lon is None:
                continue
            dlon = abs(float(ex_lon) - lon)
            if dlon > 0.02:
                continue

            ex_prov = str(ex.get("provider", "")).upper()
            ex_id = ex.get("ingestion_id") or ex.get("id")
            dist_km = haversine_distance_km(lat, lon, float(ex_lat), float(ex_lon))

            # 3. SAME_SOURCE_REPETITION: same sensor/dataset, exact same coordinates, slightly different time
            if ex_prov == provider:
                ex_ds = str(ex.get("dataset", "")).upper()
                if ex_ds == dataset and dist_km < 0.3:
                    return DeduplicationResult(
                        status=DedupStatus.SAME_SOURCE_REPETITION,
                        fingerprint=fingerprint,
                        matched_record_id=ex_id,
                        reason=f"Same sensor repeated observation within 300m of {ex_id}"
                    )
            # 4. CROSS_PROVIDER_DUPLICATE: different provider, spatial overlap <= 1.0 km
            elif dist_km <= 1.0:
                return DeduplicationResult(
                    status=DedupStatus.CROSS_PROVIDER_DUPLICATE,
                    fingerprint=fingerprint,
                    matched_record_id=ex_id,
                    reason=f"Cross-provider spatial overlap ({dist_km:.2f}km) with {ex_prov} record {ex_id}"
                )

        return DeduplicationResult(
            status=DedupStatus.UNIQUE,
            fingerprint=fingerprint,
            matched_record_id=None,
            reason="Novel observation"
        )


deduplication_engine = DeduplicationEngine()
