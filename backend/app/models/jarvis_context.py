"""
AGNI-NETRA — STRUCTURED INTELLIGENCE CONTEXT (WP6)
Defines the strongly-typed context object consumed by the Single Master JARVIS Orchestrator.
Eliminates redundant discovery and ensures epistemic traceability.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class StructuredIntelligenceContext(BaseModel):
    """
    Immutable structured intelligence snapshot representing an operational event.
    Consumed directly by JARVIS reasoning engines.
    """
    event_id: str
    incident_id: Optional[str] = None
    event_code: str
    latitude: float
    longitude: float
    state: str
    district: Optional[str] = "UNKNOWN"
    location_category: str = Field(
        default="AUTHORITATIVE_GIS_LOCATION",
        description="One of: EXPLICIT_USER_LOCATION, RESOLVED_LOCATION, AUTHORITATIVE_GIS_LOCATION, UNKNOWN_LOCATION, OUT_OF_DOMAIN_LOCATION"
    )

    # Core Computed Intelligence (Source: AGNI-NETRA Core Engines)
    max_frp: float = 0.0
    brightness: float = 0.0
    predicted_class: str = "Unclassified"
    confidence: float = 0.0
    calibrated_confidence: float = 0.0
    model_provenance: Dict[str, Any] = Field(default_factory=dict)
    
    # Risk, Priority, Anomaly
    risk_score: float = 0.0
    risk_level: str = "LOW"
    priority_score: float = 0.0
    priority_tier: str = "ROUTINE"
    anomaly_score: float = 0.0
    is_anomaly: bool = False

    # Historical & Cadastral Context
    historical_context: Dict[str, Any] = Field(default_factory=dict)
    spatial_context: Dict[str, Any] = Field(default_factory=dict)
    evidence_graph: Dict[str, Any] = Field(default_factory=dict)

    # Epistemic Reasoning State
    epistemic_uncertainty: str = Field(
        default="RESOLVED",
        description="One of: RESOLVED, UNCERTAIN, CONFLICTING, MISSING_DATA"
    )
    verification_state: str = Field(
        default="NOT_REQUIRED",
        description="One of: NOT_REQUIRED, AWAITING_HUMAN_REVIEW, VERIFIED, REJECTED"
    )
    data_freshness: str = Field(
        default="CURRENT",
        description="One of: CURRENT, STALE, DEGRADED, FAILED, UNKNOWN"
    )
    source_health: Dict[str, Any] = Field(default_factory=dict)
    model_config = ConfigDict(frozen=False)
