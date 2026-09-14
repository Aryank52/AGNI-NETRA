"""
AGNI-NETRA — Autonomous Incident Lifecycle Models
Defines the governed 12-state lifecycle and deterministic transitions for autonomous intelligence.
"""

import uuid
from enum import Enum
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class IncidentLifecycleState(str, Enum):
    OBSERVED = "OBSERVED"
    VALIDATING = "VALIDATING"
    CONTEXTUALIZING = "CONTEXTUALIZING"
    ANALYZING = "ANALYZING"
    CLASSIFYING = "CLASSIFYING"
    ASSESSING = "ASSESSING"
    CORRELATING = "CORRELATING"
    INVESTIGATING = "INVESTIGATING"
    INTELLIGENCE_READY = "INTELLIGENCE_READY"
    REQUIRES_HUMAN_VERIFICATION = "REQUIRES_HUMAN_VERIFICATION"
    VERIFIED = "VERIFIED"
    CONTESTED = "CONTESTED"
    RESOLVED = "RESOLVED"


class IncidentLifecycleTransition(BaseModel):
    """
    Deterministic, observable, and auditable record of an incident lifecycle transition.
    Attributable to the responsible subsystem with correlation IDs and timestamps.
    """
    transition_id: str = Field(default_factory=lambda: f"trans-{uuid.uuid4().hex[:8]}", description="Unique transition ID")
    event_id: str = Field(..., description="Target thermal event ID or code")
    incident_id: Optional[str] = Field(None, description="Correlated incident ID if grouped")
    from_state: Optional[IncidentLifecycleState] = Field(None, description="Source lifecycle state")
    to_state: IncidentLifecycleState = Field(..., description="Target lifecycle state")
    subsystem: str = Field(..., description="Subsystem initiating transition (e.g. DATA_PLANE, ML_CORE, RISK_ENGINE, JARVIS_ORCHESTRATOR, HITL)")
    rationale: str = Field(..., description="Deterministic reason for transition")
    correlation_id: str = Field(default_factory=lambda: f"corr-{uuid.uuid4().hex[:8]}", description="Trace correlation ID")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat(), description="ISO-8601 UTC timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Contextual payloads or metrics")


class AutonomousIntelligenceOutcome(BaseModel):
    """
    Structured outcome emitted by the AGNI-NETRA intelligence core upon forming intelligence.
    """
    event_id: str = Field(..., description="Target event ID")
    event_code: str = Field(..., description="Human-readable event code")
    incident_id: Optional[str] = Field(None, description="Associated incident ID")
    state: IncidentLifecycleState = Field(..., description="Current lifecycle state")
    risk_score: float = Field(..., description="Composite 5-factor risk score (0-100)")
    risk_level: str = Field(..., description="CRITICAL, HIGH, MEDIUM, LOW")
    priority_score: float = Field(..., description="Governed composite priority score (0-100)")
    predicted_class: str = Field(..., description="Predicted ML class")
    confidence: float = Field(..., description="Model classification confidence (0-1)")
    uncertainty_tier: str = Field("KNOWN", description="KNOWN, UNCERTAIN, MISSING, CONFLICTING")
    evidence_count: int = Field(0, description="Number of supporting evidence items assembled")
    requires_human_verification: bool = Field(True, description="Whether human review is required")
    dispatch_blocked: bool = Field(True, description="Strict invariant: automated dispatch remains blocked")
    what_changed: Optional[str] = Field(None, description="Delta summary if re-evaluated")
    why_it_matters: str = Field("", description="Operational context narrative")
    correlation_id: str = Field(..., description="End-to-end correlation ID")
    transitions: List[IncidentLifecycleTransition] = Field(default_factory=list, description="Audit trail of state transitions")
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
