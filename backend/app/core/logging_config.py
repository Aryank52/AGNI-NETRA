import logging
import sys
import json
import re
import uuid
from datetime import datetime, timezone
from contextvars import ContextVar
from typing import Optional, Dict, Any

# Context Variables for Request & Ingestion Lifecycle Tracing
correlation_id_ctx: ContextVar[str] = ContextVar("correlation_id", default="")
job_id_ctx: ContextVar[str] = ContextVar("job_id", default="")
event_id_ctx: ContextVar[str] = ContextVar("event_id", default="")
alert_id_ctx: ContextVar[str] = ContextVar("alert_id", default="")
analyst_id_ctx: ContextVar[str] = ContextVar("analyst_id", default="")


def get_correlation_id() -> str:
    """Returns the active request correlation ID or generates a new one."""
    cid = correlation_id_ctx.get()
    if not cid:
        cid = f"AGNI-{uuid.uuid4().hex[:12].upper()}"
        correlation_id_ctx.set(cid)
    return cid


def set_correlation_id(cid: Optional[str] = None) -> str:
    """Sets the active correlation ID in context."""
    if not cid:
        cid = f"AGNI-{uuid.uuid4().hex[:12].upper()}"
    correlation_id_ctx.set(cid)
    return cid


class SecretsRedactorFilter(logging.Filter):
    """
    Scrubs sensitive credentials, tokens, and database passwords from all logs.
    """
    PASSWORD_REGEX = re.compile(r"(password|passwd|pwd|secret|token|api_key|map_key)[:=]\s*['\"]?([^'\"\s&]+)", re.IGNORECASE)
    DB_URL_REGEX = re.compile(r":([^@/]+)@")

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = self.DB_URL_REGEX.sub(r":****@", record.msg)
            record.msg = self.PASSWORD_REGEX.sub(r"\1=****", record.msg)
        return True


class StructuredJsonFormatter(logging.Formatter):
    """
    JSON log formatter with correlation ID tracing for production aggregation.
    """
    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": correlation_id_ctx.get() or None,
            "job_id": job_id_ctx.get() or None,
            "event_id": event_id_ctx.get() or None,
            "alert_id": alert_id_ctx.get() or None,
            "analyst_id": analyst_id_ctx.get() or None,
        }

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


def configure_production_logging(level: int = logging.INFO, as_json: bool = False) -> logging.Logger:
    """
    Configures root and application loggers with redacting filters and formatting.
    """
    logger = logging.getLogger("agni_netra")
    logger.setLevel(level)

    # Avoid duplicate handlers
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)

        if as_json:
            formatter = StructuredJsonFormatter()
        else:
            formatter = logging.Formatter(
                "[%(asctime)s] [%(levelname)s] [%(name)s] [CID:%(correlation_id)s] %(message)s",
                defaults={"correlation_id": "NONE"}
            )

        handler.setFormatter(formatter)
        handler.addFilter(SecretsRedactorFilter())
        logger.addHandler(handler)

    return logger


logger = configure_production_logging()
