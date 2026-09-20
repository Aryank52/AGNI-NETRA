"""
AGNI-NETRA — WP3 Persistent Ingestion Checkpoint & Watermark Service
Maintains durable cursor positions in the database so workers can safely
restart without reprocessing the entire dataset or generating duplicate downstream intelligence.
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from backend.app.models.domain import IngestionCheckpointModel


class CheckpointService:
    """
    Manages durable watermark cursors for external data feeds.
    """

    @staticmethod
    def get_checkpoint_key(provider: str, dataset: str) -> str:
        return f"{provider.upper()}:{dataset.upper()}"

    def get_checkpoint(
        self,
        db: Session,
        provider: str,
        dataset: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieves the current persistent watermark cursor for a given provider/dataset.
        """
        key = self.get_checkpoint_key(provider, dataset)
        cp = db.query(IngestionCheckpointModel).filter(
            IngestionCheckpointModel.checkpoint_key == key
        ).first()

        if not cp:
            return None

        return {
            "checkpoint_key": cp.checkpoint_key,
            "provider": cp.provider,
            "dataset": cp.dataset,
            "last_successful_observation_time": (
                cp.last_successful_observation_time.isoformat()
                if cp.last_successful_observation_time else None
            ),
            "last_successful_source_record_id": cp.last_successful_source_record_id,
            "last_successful_batch_id": cp.last_successful_batch_id,
            "cursor_state": cp.cursor_state or {},
            "updated_at": cp.updated_at.isoformat() if cp.updated_at else None
        }

    def update_checkpoint(
        self,
        db: Session,
        provider: str,
        dataset: str,
        latest_observation_time: Optional[datetime],
        last_source_record_id: Optional[str] = None,
        batch_id: Optional[str] = None,
        cursor_metadata: Optional[Dict[str, Any]] = None
    ) -> IngestionCheckpointModel:
        """
        Atomically updates or creates a durable watermark cursor in the database.
        """
        key = self.get_checkpoint_key(provider, dataset)
        cp = db.query(IngestionCheckpointModel).filter(
            IngestionCheckpointModel.checkpoint_key == key
        ).first()

        now_utc = datetime.now(timezone.utc)
        obs_utc = None
        if latest_observation_time:
            obs_utc = (
                latest_observation_time.replace(tzinfo=timezone.utc)
                if latest_observation_time.tzinfo is None
                else latest_observation_time.astimezone(timezone.utc)
            )

        if not cp:
            cp = IngestionCheckpointModel(
                id=str(uuid.uuid4()),
                checkpoint_key=key,
                provider=provider.upper(),
                dataset=dataset.upper(),
                last_successful_observation_time=obs_utc,
                last_successful_source_record_id=last_source_record_id,
                last_successful_batch_id=batch_id,
                cursor_state=cursor_metadata or {},
                updated_at=now_utc
            )
            db.add(cp)
        else:
            if obs_utc:
                if (not cp.last_successful_observation_time or
                        obs_utc > cp.last_successful_observation_time.replace(tzinfo=timezone.utc)):
                    cp.last_successful_observation_time = obs_utc
            if last_source_record_id:
                cp.last_successful_source_record_id = last_source_record_id
            if batch_id:
                cp.last_successful_batch_id = batch_id
            if cursor_metadata:
                current_state = dict(cp.cursor_state or {})
                current_state.update(cursor_metadata)
                cp.cursor_state = current_state
            cp.updated_at = now_utc

        db.flush()
        return cp


checkpoint_service = CheckpointService()
