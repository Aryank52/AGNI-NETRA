"""
AGNI-NETRA JARVIS Phase 16: Freshness Evaluation Engine
Calculates dataset-specific observation age and deterministic status:
FRESH, STALE, VERY_STALE, UNKNOWN.
Ensures freshness reflects actual observation time, not merely ingestion completion time.
"""

from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text

from backend.app.models.domain import DatasetRegistryModel
from backend.app.services.data_plane.models import FreshnessStatus


class FreshnessEngine:
    """
    Evaluates dataset observation freshness against configured SLA thresholds.
    """

    @classmethod
    def evaluate_dataset_freshness(
        cls,
        dataset_id: str,
        last_obs_time: Optional[datetime],
        threshold_seconds: int = 86400,
        current_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Computes factual age and freshness status for a given dataset.
        """
        now_utc = current_time or datetime.now(timezone.utc)

        if last_obs_time is None:
            return {
                "dataset_id": dataset_id,
                "latest_observation_time": None,
                "age_seconds": None,
                "threshold_seconds": threshold_seconds,
                "freshness_status": FreshnessStatus.UNKNOWN.value,
                "summary": "No observation recorded"
            }

        # Normalize timezone
        if last_obs_time.tzinfo is None:
            last_obs_time = last_obs_time.replace(tzinfo=timezone.utc)
        else:
            last_obs_time = last_obs_time.astimezone(timezone.utc)

        age = max(0.0, (now_utc - last_obs_time).total_seconds())

        if age <= threshold_seconds:
            status = FreshnessStatus.FRESH
            summary = f"Observations are current ({round(age / 3600.0, 1)}h old, SLA <= {round(threshold_seconds / 3600.0, 1)}h)"
        elif age <= threshold_seconds * 3:
            status = FreshnessStatus.STALE
            summary = f"Observations are stale ({round(age / 3600.0, 1)}h old, SLA <= {round(threshold_seconds / 3600.0, 1)}h)"
        else:
            status = FreshnessStatus.VERY_STALE
            summary = f"Observations are severely out of date ({round(age / 86400.0, 1)} days old)"

        return {
            "dataset_id": dataset_id,
            "latest_observation_time": last_obs_time.isoformat(),
            "age_seconds": round(age, 1),
            "age_hours": round(age / 3600.0, 2),
            "threshold_seconds": threshold_seconds,
            "freshness_status": status.value,
            "summary": summary
        }

    @classmethod
    def get_all_datasets_freshness(cls, db: Session) -> List[Dict[str, Any]]:
        """
        Inspects all registered datasets in governed_dataset_registry and evaluates freshness.
        """
        datasets = db.query(DatasetRegistryModel).all()
        results = []
        for ds in datasets:
            res = cls.evaluate_dataset_freshness(
                dataset_id=ds.dataset_id,
                last_obs_time=ds.last_observation_time,
                threshold_seconds=ds.freshness_threshold_seconds or 86400
            )
            res["provider"] = ds.provider
            res["name"] = ds.name
            res["status"] = ds.status
            results.append(res)
        return results


freshness_engine = FreshnessEngine()
