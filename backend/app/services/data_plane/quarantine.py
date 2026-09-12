"""
AGNI-NETRA JARVIS Phase 16: Quarantine Manager
Stores rejected or malformed records in isolated quarantine storage.
Ensures zero secrets are retained and malformed payloads never reach
authoritative intelligence tables.
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text

from backend.app.models.domain import IngestionQuarantineModel
from backend.app.services.data_plane.models import IngestionQuarantineSchema


# Sensitive keys to redact
SENSITIVE_KEYS = {"api_key", "password", "token", "secret", "authorization", "auth", "key", "map_key"}


def sanitize_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Strips secrets and sensitive tokens from debug payloads."""
    clean: Dict[str, Any] = {}
    for k, v in payload.items():
        if k.lower() in SENSITIVE_KEYS:
            clean[k] = "[REDACTED]"
        elif isinstance(v, dict):
            clean[k] = sanitize_payload(v)
        else:
            clean[k] = v
    return clean


class QuarantineManager:
    """
    Manages quarantine logging, resolution, and audit inspection.
    """

    @classmethod
    def quarantine_record(
        cls,
        db: Optional[Session],
        provider: str,
        dataset: str,
        source_record_id: Optional[str],
        reason: str,
        error_code: str = "VALIDATION_FAILURE",
        raw_payload: Optional[Dict[str, Any]] = None,
        batch_id: Optional[str] = None
    ) -> IngestionQuarantineSchema:
        """
        Creates an immutable quarantine entry.
        """
        quarantine_id = f"QRN-{uuid.uuid4().hex[:8].upper()}"
        safe_raw = sanitize_payload(raw_payload or {})
        now_utc = datetime.now(timezone.utc)

        entry = IngestionQuarantineSchema(
            quarantine_id=quarantine_id,
            batch_id=batch_id,
            provider=provider,
            dataset=dataset,
            source_record_id=source_record_id,
            reason=reason,
            error_code=error_code,
            raw_safe_reference=safe_raw,
            detected_at=now_utc.isoformat(),
            resolution="UNRESOLVED"
        )

        if db is not None:
            try:
                db_obj = IngestionQuarantineModel(
                    id=str(uuid.uuid4()),
                    quarantine_id=quarantine_id,
                    batch_id=batch_id,
                    provider=provider,
                    dataset=dataset,
                    source_record_id=source_record_id,
                    reason=reason,
                    error_code=error_code,
                    raw_safe_reference=safe_raw,
                    detected_at=now_utc,
                    resolution="UNRESOLVED"
                )
                db.add(db_obj)
                db.flush()
            except Exception as e:
                print(f"[!] Warning: failed to persist quarantine record to DB: {e}")

        return entry

    @classmethod
    def list_quarantined(
        cls,
        db: Session,
        limit: int = 50,
        provider: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Lists quarantined records from the database."""
        query = db.query(IngestionQuarantineModel)
        if provider:
            query = query.filter(IngestionQuarantineModel.provider == provider.upper())
        items = query.order_by(IngestionQuarantineModel.detected_at.desc()).limit(limit).all()
        return [
            {
                "quarantine_id": q.quarantine_id,
                "batch_id": q.batch_id,
                "provider": q.provider,
                "dataset": q.dataset,
                "source_record_id": q.source_record_id,
                "reason": q.reason,
                "error_code": q.error_code,
                "raw_safe_reference": q.raw_safe_reference,
                "detected_at": q.detected_at.isoformat() if q.detected_at else None,
                "resolved_at": q.resolved_at.isoformat() if q.resolved_at else None,
                "resolution": q.resolution,
                "resolved_by": q.resolved_by
            }
            for q in items
        ]


quarantine_manager = QuarantineManager()
