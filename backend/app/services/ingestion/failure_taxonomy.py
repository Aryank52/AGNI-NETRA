"""
AGNI-NETRA — WP3 Ingestion Failure Taxonomy & Provider Health Definitions
Defines structured failure categories, provider health state machines,
and sanitized error reporting.
"""

import re
from enum import Enum
from typing import Dict, Any, Optional
from datetime import datetime, timezone


class IngestionFailureCategory(str, Enum):
    """
    Standardized taxonomy of ingestion failure modes.
    Ensures failures are explicitly classified without masking in generic exception strings.
    """
    PROVIDER_TIMEOUT = "PROVIDER_TIMEOUT"
    PROVIDER_RATE_LIMITED = "PROVIDER_RATE_LIMITED"
    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
    AUTHENTICATION_FAILURE = "AUTHENTICATION_FAILURE"
    MALFORMED_RESPONSE = "MALFORMED_RESPONSE"
    SCHEMA_MISMATCH = "SCHEMA_MISMATCH"
    INVALID_COORDINATE = "INVALID_COORDINATE"
    INVALID_TIMESTAMP = "INVALID_TIMESTAMP"
    PHYSICAL_OUT_OF_RANGE = "PHYSICAL_OUT_OF_RANGE"
    DUPLICATE_OBSERVATION = "DUPLICATE_OBSERVATION"
    DATABASE_FAILURE = "DATABASE_FAILURE"
    PERSISTENCE_FAILURE = "PERSISTENCE_FAILURE"
    DOWNSTREAM_PROCESSING_FAILURE = "DOWNSTREAM_PROCESSING_FAILURE"
    UNKNOWN_FAILURE = "UNKNOWN_FAILURE"


class ProviderHealthState(str, Enum):
    """
    Deterministic provider health state semantics.
    """
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    STALE = "STALE"
    FAILED = "FAILED"
    UNAVAILABLE = "UNAVAILABLE"


# Sensitive patterns for secret redaction
SENSITIVE_PATTERNS = [
    (re.compile(r"(/api/(?:area|country|data_availability)/csv/)[^/]+", re.IGNORECASE), r"\1[REDACTED]"),
    (re.compile(r"([?&](?:api[_-]?key|map[_-]?key|token|secret|password)=)[^&]+", re.IGNORECASE), r"\1[REDACTED]"),
    (re.compile(r"((?:Bearer|Basic)\s+)[A-Za-z0-9_\-\.~+/=]+", re.IGNORECASE), r"\1[REDACTED]"),
    (re.compile(r"\bSECRET_[A-Za-z0-9_]+\b", re.IGNORECASE), "[REDACTED]"),
    (re.compile(r"\b[a-f0-9]{32,64}\b", re.IGNORECASE), "[REDACTED]")
]


def sanitize_error_message(message: str) -> str:
    """
    Redacts credentials, API keys, and sensitive tokens from error messages and logs.
    """
    if not message:
        return ""
    sanitized = str(message)
    for pat, repl in SENSITIVE_PATTERNS:
        sanitized = pat.sub(repl, sanitized)
    return sanitized


class IngestionException(Exception):
    """
    Base structured exception for AGNI-NETRA ingestion errors.
    """
    def __init__(
        self,
        category: IngestionFailureCategory,
        message: str,
        provider: str = "NASA_FIRMS",
        status_code: Optional[int] = None,
        retryable: bool = False,
        details: Optional[Dict[str, Any]] = None
    ):
        self.category = category
        self.safe_message = sanitize_error_message(message)
        self.provider = provider
        self.status_code = status_code
        self.retryable = retryable
        self.details = details or {}
        self.timestamp = datetime.now(timezone.utc)
        super().__init__(f"[{provider}:{category.value}] {self.safe_message}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category.value,
            "message": self.safe_message,
            "provider": self.provider,
            "status_code": self.status_code,
            "retryable": self.retryable,
            "timestamp": self.timestamp.isoformat(),
            "details": self.details
        }
