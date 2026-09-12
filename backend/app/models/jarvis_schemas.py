"""
AGNI-NETRA — JARVIS Autonomous Intelligence & Command Layer
Pydantic Schemas & Types for Master Agent Orchestration, Dynamic Planning,
Evidence Fusion, Operating Policy, and Execution Traces.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field, ConfigDict


class JarvisState(str, Enum):
    """
    JARVIS State Machine:
    IDLE -> UNDERSTANDING -> PLANNING -> EXECUTING -> EVALUATING -> COMPLETED / REQUIRES_APPROVAL / FAILED / BLOCKED -> IDLE
    """
    IDLE = "IDLE"
    UNDERSTANDING = "UNDERSTANDING"
    PLANNING = "PLANNING"
    EXECUTING = "EXECUTING"
    EVALUATING = "EVALUATING"
    WAITING_FOR_INPUT = "WAITING_FOR_INPUT"
    REQUIRES_APPROVAL = "REQUIRES_APPROVAL"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"


class JarvisCapability(str, Enum):
    """
    Internal capabilities controlled by the ONE master JARVIS agent.
    """
    GEOINT = "GEOINT"
    THERMAL_INTELLIGENCE = "THERMAL_INTELLIGENCE"
    CLASSIFICATION = "CLASSIFICATION"
    ANOMALY_ANALYSIS = "ANOMALY_ANALYSIS"
    HISTORICAL_ANALYSIS = "HISTORICAL_ANALYSIS"
    RISK_ANALYSIS = "RISK_ANALYSIS"
    ALERT_ANALYSIS = "ALERT_ANALYSIS"
    VERIFICATION = "VERIFICATION"
    REPORTING = "REPORTING"
    SYSTEM_GOVERNANCE = "SYSTEM_GOVERNANCE"
    CROSS_SOURCE_CORRELATION = "CROSS_SOURCE_CORRELATION"
    TEMPORAL_ANALYSIS = "TEMPORAL_ANALYSIS"
    ENVIRONMENTAL_INTELLIGENCE = "ENVIRONMENTAL_INTELLIGENCE"
    CROSS_MODAL_VERIFICATION = "CROSS_MODAL_VERIFICATION"
    EVIDENCE_GRAPH = "EVIDENCE_GRAPH"
    EVALUATION = "EVALUATION"
    SYNTHESIS = "SYNTHESIS"
    INVESTIGATION = "INVESTIGATION"


class AgentType(str, Enum):
    """
    Agent identity enum. In the unified architecture, JARVIS is the single master agent.
    """
    JARVIS = "JARVIS"
    JARVIS_MASTER = "JARVIS"
    JARVIS_GEO = "JARVIS-GEO"
    JARVIS_ML = "JARVIS-ML"
    JARVIS_ANOM = "JARVIS-ANOM"
    JARVIS_RISK = "JARVIS-RISK"
    JARVIS_SAT = "JARVIS-SAT"
    JARVIS_INVEST = "JARVIS-INVEST"
    JARVIS_REPORT = "JARVIS-REPORT"
    JARVIS_GUARD = "JARVIS-GUARD"


class StepStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
    SKIPPED = "SKIPPED"


class EvidenceStatus(str, Enum):
    VERIFIED = "VERIFIED"
    PARTIAL = "PARTIAL"
    SIMULATED = "SIMULATED"
    UNKNOWN = "UNKNOWN"
    INSUFFICIENT = "INSUFFICIENT"


class CommandIntent(str, Enum):
    QUERY = "QUERY"
    INVESTIGATE = "INVESTIGATE"
    EXPLAIN = "EXPLAIN"
    COMPARE = "COMPARE"
    FILTER = "FILTER"
    LOCATE = "LOCATE"
    RANK = "RANK"
    MONITOR = "MONITOR"
    SUMMARIZE = "SUMMARIZE"
    GENERATE_REPORT = "GENERATE_REPORT"
    VERIFY = "VERIFY"
    TRACE = "TRACE"
    STATUS = "STATUS"
    DISPATCH_REQUEST = "DISPATCH_REQUEST"
    SYNTHESIZE = "SYNTHESIZE"
    GENERAL = "GENERAL"


class CommandObjective(BaseModel):
    """
    Structured operational objective extracted from user natural language command.
    Defines the explicit goal, constraints, hypotheses, requested evidence, output format,
    and deterministic stopping condition.
    """
    primary_goal: str = "QUERY"
    target_event: Optional[str] = None
    target_region: Optional[str] = None
    facility_context: Optional[str] = None
    max_distance_m: Optional[float] = None
    risk_threshold: Optional[str] = None
    baseline_condition: Optional[str] = None
    candidate_count: int = 1
    constraints: List[str] = Field(default_factory=list)
    ranking_criteria: Optional[str] = None
    target_hypothesis: Optional[str] = None
    requested_evidence: List[str] = Field(default_factory=list)
    requested_output: str = "SYNTHESIS"
    stopping_condition: str = "SUFFICIENT_EVIDENCE_FOR_OBJECTIVE"
    resolved_from_context: bool = False
    contextual_reference: Optional[str] = None


class InvestigationStatus(str, Enum):
    CREATED = "CREATED"
    ACTIVE = "ACTIVE"
    ANALYZING = "ANALYZING"
    INVESTIGATING = "INVESTIGATING"
    AWAITING_INPUT = "AWAITING_INPUT"
    REQUIRES_HUMAN_REVIEW = "REQUIRES_HUMAN_REVIEW"
    REQUIRES_REVIEW = "REQUIRES_REVIEW"
    VERIFIED = "VERIFIED"
    CONTESTED = "CONTESTED"
    RESOLVED = "RESOLVED"
    COMPLETED = "COMPLETED"
    CLOSED = "CLOSED"



class EpistemicType(str, Enum):
    FACT = "FACT"
    MODEL_OUTPUT = "MODEL_OUTPUT"
    DERIVED_ANALYSIS = "DERIVED_ANALYSIS"
    SPATIAL_CONTEXT = "SPATIAL_CONTEXT"
    HISTORICAL_CONTEXT = "HISTORICAL_CONTEXT"
    INFERENCE = "INFERENCE"
    RECOMMENDATION = "RECOMMENDATION"


class StructuredEvidenceItem(BaseModel):
    evidence_id: str
    type: str
    source: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    value: Any = None
    confidence: Optional[float] = None
    tool: Optional[str] = None
    execution_id: Optional[str] = None
    epistemic_type: EpistemicType = EpistemicType.FACT
    freshness_status: str = "CURRENT"  # CURRENT, STALE, REFRESH_REQUIRED


class JarvisCommandRequest(BaseModel):
    command: str = Field(..., description="High-level natural language or structured operational command")
    session_id: Optional[str] = Field(default=None, description="Optional working memory session ID")
    investigation_id: Optional[str] = Field(default=None, description="Optional active investigation workspace ID")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Session and UI viewport context")


class ExecutionStep(BaseModel):
    step_number: int
    agent: str = "JARVIS"  # Unified Master Agent: JARVIS
    capability: Optional[str] = None  # Internal capability invoked (e.g. GEOINT, CLASSIFICATION)
    action: str
    tool: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    status: StepStatus = StepStatus.PENDING
    result_summary: Optional[str] = None
    data_snapshot: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    duration_ms: float = 0.0


class ExecutionTrace(BaseModel):
    trace_id: str
    command: str
    parsed_intent: str
    target_event: Optional[str] = None
    target_region: Optional[str] = None
    user_role: str = "ANALYST"
    current_state: JarvisState = JarvisState.COMPLETED
    objective: Optional[CommandObjective] = None
    stopping_reason: Optional[str] = None
    capabilities_used: List[str] = Field(default_factory=list)
    state_transitions: List[Dict[str, Any]] = Field(default_factory=list)
    steps: List[ExecutionStep] = Field(default_factory=list)
    total_duration_ms: float = 0.0
    status: StepStatus = StepStatus.COMPLETED
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None


class EvidenceQuality(BaseModel):
    completeness_score: float = 1.0  # 0.0 - 1.0
    provenance: str = "POSTGIS_POSTGRESQL_AND_NASA_FIRMS"
    missing_elements: List[str] = Field(default_factory=list)
    status: EvidenceStatus = EvidenceStatus.VERIFIED


class CategorizedSynthesis(BaseModel):
    """
    Distinguishes epistemic categories of intelligence:
    FACT, DERIVED ANALYSIS, MODEL OUTPUT, SPATIAL CONTEXT, INFERENCE, RECOMMENDATION.
    """
    facts: List[str] = Field(default_factory=list)
    derived_analysis: List[str] = Field(default_factory=list)
    model_output: List[str] = Field(default_factory=list)
    spatial_context: List[str] = Field(default_factory=list)
    inferences: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    uncertainties_and_warnings: List[str] = Field(default_factory=list)


class FusedEvidence(BaseModel):
    model_config = ConfigDict(extra="allow")

    thermal_evidence: Optional[Dict[str, Any]] = None
    geospatial_evidence: Optional[Dict[str, Any]] = None
    classification: Optional[Dict[str, Any]] = None
    anomaly: Optional[Dict[str, Any]] = None
    baseline: Optional[Dict[str, Any]] = None
    risk: Optional[Dict[str, Any]] = None
    alert: Optional[Dict[str, Any]] = None
    verification: Optional[Dict[str, Any]] = None
    satellite_observations: Optional[List[Dict[str, Any]]] = None
    categorized_synthesis: Optional[CategorizedSynthesis] = None
    context_evidence: Optional[Dict[str, Any]] = None
    temporal_evidence: Optional[Dict[str, Any]] = None
    environmental_evidence: Optional[Dict[str, Any]] = None
    cross_modal_evidence: Optional[Dict[str, Any]] = None
    evidence_quality: EvidenceQuality = Field(default_factory=EvidenceQuality)


class JarvisResponse(BaseModel):
    command: str
    intent: str
    state: JarvisState = JarvisState.COMPLETED
    objective: Optional[CommandObjective] = None
    stopping_reason: Optional[str] = None
    capabilities_used: List[str] = Field(default_factory=list)
    summary: str
    details: Dict[str, Any] = Field(default_factory=dict)
    fused_evidence: FusedEvidence = Field(default_factory=FusedEvidence)
    execution_trace: ExecutionTrace
    recommendations: List[str] = Field(default_factory=list)
    requires_human_approval: bool = False
    dispatch_gate_blocked: bool = True  # Controlled dispatch gate invariant: True (cannot emit live dispatch)
    system_notice: str = "JARVIS: Master Intelligence & Command Agent for AGNI-NETRA. Deterministic models and PostGIS remain authoritative."
    investigation_id: Optional[str] = None
    investigation_status: Optional[str] = None
    investigation_summary: Optional[Any] = None
    investigation_workspace: Optional[Any] = None
    conflicts: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    evidence_conflicts: Optional[List[Dict[str, Any]]] = None
    evidence_strength: Optional[str] = None
    evidence_strength_details: Optional[Dict[str, Any]] = None
    uncertainty: Optional[Dict[str, Any]] = Field(default_factory=dict)
    uncertainty_assessment: Optional[Dict[str, Any]] = None
    what_could_change: Optional[List[str]] = None
    analyst_ranking: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    operator_summary: Optional[Dict[str, Any]] = None

    # Phase 6 Global Intelligence & Provider Abstraction
    sources_used: Optional[List[str]] = Field(default_factory=list)
    coverage_profile: Optional[str] = "INDIA"
    missing_sources: Optional[List[str]] = Field(default_factory=list)
    partial_sources: Optional[List[str]] = Field(default_factory=list)
    source_availability_matrix: Optional[Dict[str, Any]] = Field(default_factory=dict)
    provenance_records: Optional[List[Dict[str, Any]]] = Field(default_factory=list)

    # Phase 7 Global Thermal Intelligence & Multi-Provider Fusion
    thermal_sources: Optional[List[str]] = Field(default_factory=list)
    source_agreement: Optional[str] = None
    thermal_conflicts: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    source_conflicts: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    observation_count: Optional[int] = 0
    thermal_provenance: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    observation_provenance: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    thermal_coverage: Optional[Dict[str, Any]] = Field(default_factory=dict)

    # Phase 8 Global Context Intelligence & Cross-Domain Fusion
    context_sources: Optional[List[str]] = Field(default_factory=list)
    context_provenance: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    context_relationships: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    context_coverage: Optional[Dict[str, Any]] = Field(default_factory=dict)
    context_conflicts: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    context_uncertainty: Optional[Dict[str, Any]] = Field(default_factory=dict)
    context_observation_count: Optional[int] = 0

    # Phase 9 Global Historical Baselines & Temporal Pattern Intelligence
    temporal_sources: Optional[List[str]] = Field(default_factory=list)
    temporal_provenance: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    historical_baseline: Optional[Dict[str, Any]] = Field(default_factory=dict)
    persistence_assessment: Optional[Dict[str, Any]] = Field(default_factory=dict)
    recurrence_assessment: Optional[Dict[str, Any]] = Field(default_factory=dict)
    temporal_patterns: Optional[Dict[str, Any]] = Field(default_factory=dict)
    temporal_anomalies: Optional[Dict[str, Any]] = Field(default_factory=dict)
    temporal_uncertainty: Optional[Dict[str, Any]] = Field(default_factory=dict)
    temporal_coverage: Optional[Dict[str, Any]] = Field(default_factory=dict)
    temporal_observation_count: Optional[int] = 0

    # Phase 10 Global Environmental Intelligence & Cross-Modal Verification
    environmental_sources: Optional[List[str]] = Field(default_factory=list)
    environmental_provenance: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    environmental_observations: Optional[Any] = Field(default_factory=dict)
    environmental_relationships: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    environmental_coverage: Optional[Dict[str, Any]] = Field(default_factory=dict)
    environmental_uncertainty: Optional[Dict[str, Any]] = Field(default_factory=dict)
    environmental_conflicts: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    cross_modal_sources: Optional[List[str]] = Field(default_factory=list)
    cross_modal_evidence: Optional[Dict[str, Any]] = Field(default_factory=dict)
    cross_modal_uncertainty: Optional[Dict[str, Any]] = Field(default_factory=dict)
    environmental_observation_count: Optional[int] = 0
    cross_modal_observation_count: Optional[int] = 0

    # Phase 11 Global Evidence Graph & Explainable Intelligence
    evidence_graph: Optional[Dict[str, Any]] = Field(default_factory=dict)
    hypotheses: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    evidence_nodes: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    evidence_edges: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    evidence_lineage: Optional[Dict[str, Any]] = Field(default_factory=dict)
    evidence_uncertainty: Optional[Dict[str, Any]] = Field(default_factory=dict)
    assessment_lineage: Optional[Dict[str, Any]] = Field(default_factory=dict)
    data_gaps: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    what_would_change_assessment: Optional[List[str]] = Field(default_factory=list)

    # Phase 13 Global Intelligence Fusion & Decision-Support Synthesis
    unified_assessment: Optional[Dict[str, Any]] = None
    decision_support: Optional[Dict[str, Any]] = None
    next_best_evidence: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    assessment_history: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    assessment_changes: Optional[Union[Dict[str, Any], str]] = None
    decision_support_packages: Optional[Dict[str, Any]] = Field(default_factory=dict)

    @property
    def temporal_anomaly(self) -> Optional[Dict[str, Any]]:
        return self.temporal_anomalies

    @property
    def temporal_evidence(self) -> Optional[Dict[str, Any]]:
        return self.temporal_uncertainty

    @property
    def environmental_evidence(self) -> Optional[Dict[str, Any]]:
        return self.details.get("environmental_evidence") or (self.fused_evidence.environmental_evidence if self.fused_evidence else None)

    @property
    def environmental_conditions(self) -> Optional[Dict[str, Any]]:
        return self.details.get("environmental_conditions")

    @property
    def cross_modal_verification(self) -> Optional[Dict[str, Any]]:
        return self.details.get("cross_modal_verification") or (self.details.get("cross_modal_evidence") or (self.fused_evidence.cross_modal_evidence if self.fused_evidence else None))

    @property
    def operational_dispatch_gate_blocked(self) -> bool:
        return self.dispatch_gate_blocked




class JarvisToolInfo(BaseModel):
    name: str
    purpose: str = ""
    capability: str = "THERMAL_INTELLIGENCE"
    input_schema: Dict[str, Any] = Field(default_factory=dict)
    output_schema: Dict[str, Any] = Field(default_factory=dict)
    required_permissions: List[str] = Field(default_factory=lambda: ["ANALYST"])
    side_effects: bool = False
    risk_level: str = "LOW"
    dependencies: List[str] = Field(default_factory=list)
    
    # Legacy fields for backward compatibility
    description: str = ""
    agent: str = "JARVIS"
    parameters: Dict[str, Any] = Field(default_factory=dict)
    required_role: str = "ANALYST"
    is_mutation: bool = False
    is_dispatch: bool = False
    audit_required: bool = True
    read_only: bool = True


class SystemStatusReport(BaseModel):
    status: str = "OPERATIONAL"
    system: str = "JARVIS Autonomous Intelligence & Command Layer"
    platform: str = "AGNI-NETRA Global Geospatial Thermal Intelligence Platform"
    firms_ingestion: Dict[str, Any] = Field(default_factory=dict)
    database_status: Dict[str, Any] = Field(default_factory=dict)
    postgis_status: Dict[str, Any] = Field(default_factory=dict)
    ml_governance: Dict[str, Any] = Field(default_factory=dict)
    anomaly_service: Dict[str, Any] = Field(default_factory=dict)
    risk_engine: Dict[str, Any] = Field(default_factory=dict)
    alert_engine: Dict[str, Any] = Field(default_factory=dict)
    verification_queue_count: int = 0
    operational_dispatch_gate: Dict[str, Any] = Field(default_factory=dict)
    active_specialists: List[str] = Field(default_factory=list)
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class InvestigationSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    case_id: str
    target: Optional[str] = None
    objective: Optional[str] = None
    status: InvestigationStatus = InvestigationStatus.CREATED
    classification: Optional[str] = None
    risk_score: Optional[float] = None
    risk_level: Optional[str] = None
    anomaly_sigma: Optional[float] = None
    evidence_checklist: List[str] = Field(default_factory=list)
    open_questions: List[str] = Field(default_factory=list)
    resolved_questions: List[Dict[str, Any]] = Field(default_factory=list)
    last_action: Optional[str] = None


class InvestigationWorkspaceSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    investigation_id: str
    session_id: str
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    user_role: str = "ANALYST"
    status: InvestigationStatus = InvestigationStatus.CREATED
    primary_objective: Optional[str] = None
    target_event_id: Optional[str] = None
    target_region: Optional[str] = None
    candidate_set: List[Dict[str, Any]] = Field(default_factory=list)
    selected_candidate: Optional[str] = None
    comparison_set: List[str] = Field(default_factory=list)
    command_history: List[Dict[str, Any]] = Field(default_factory=list)
    execution_ids: List[str] = Field(default_factory=list)
    evidence_summary: Dict[str, Any] = Field(default_factory=dict)
    classification_summary: Dict[str, Any] = Field(default_factory=dict)
    risk_summary: Dict[str, Any] = Field(default_factory=dict)
    anomaly_summary: Dict[str, Any] = Field(default_factory=dict)
    historical_summary: Dict[str, Any] = Field(default_factory=dict)
    spatial_summary: Dict[str, Any] = Field(default_factory=dict)
    verification_status: str = "NOT_REQUIRED"
    report_status: str = "NOT_REQUESTED"
    report_id: Optional[str] = None
    report_file_path: Optional[str] = None
    open_questions: List[Dict[str, Any]] = Field(default_factory=list)
    resolved_questions: List[Dict[str, Any]] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    data_provenance: Dict[str, Any] = Field(default_factory=dict)
    structured_evidence: List[Dict[str, Any]] = Field(default_factory=list)

    # Phase 4 Intelligence Operations & Operational State Tracking
    current_winner: Optional[str] = None
    winner_reason: Optional[str] = None
    completed_subtasks: List[Dict[str, Any]] = Field(default_factory=list)
    pending_subtasks: List[Dict[str, Any]] = Field(default_factory=list)
    blocked_subtasks: List[Dict[str, Any]] = Field(default_factory=list)
    action_graph: Dict[str, Any] = Field(default_factory=dict)
    objective_history: List[Dict[str, Any]] = Field(default_factory=list)
    stopping_condition: Optional[str] = None
    stopping_evidence: List[str] = Field(default_factory=list)

    # Phase 5 Operational Intelligence Depth
    conflicts: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    uncertainty: Optional[Dict[str, Any]] = Field(default_factory=dict)
    evidence_strength: Optional[str] = None
    evidence_strength_details: Optional[Dict[str, Any]] = Field(default_factory=dict)
    analyst_ranking: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    constraints: Optional[Dict[str, Any]] = Field(default_factory=dict)
    operational_recommendations: Optional[List[str]] = Field(default_factory=list)

    # Phase 6 Global Intelligence Architecture & Provider Abstraction
    sources_used: Optional[List[str]] = Field(default_factory=list)
    coverage_profile: Optional[str] = "INDIA"
    missing_sources: Optional[List[str]] = Field(default_factory=list)
    partial_sources: Optional[List[str]] = Field(default_factory=list)
    provenance_records: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    source_availability_matrix: Optional[Dict[str, Any]] = Field(default_factory=dict)
    country: Optional[str] = "India"
    jurisdiction: Optional[str] = None

    # Phase 7 Global Thermal Intelligence & Multi-Provider Fusion
    thermal_sources: Optional[List[str]] = Field(default_factory=list)
    observation_provenance: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    source_agreement: Optional[str] = "SINGLE_SOURCE"
    source_conflicts: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    thermal_coverage: Optional[Dict[str, Any]] = Field(default_factory=dict)
    observation_count: Optional[int] = 0

    # Phase 8 Global Context Intelligence & Cross-Domain Fusion
    context_sources: Optional[List[str]] = Field(default_factory=list)
    context_provenance: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    context_relationships: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    context_coverage: Optional[Dict[str, Any]] = Field(default_factory=dict)
    context_conflicts: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    context_uncertainty: Optional[Dict[str, Any]] = Field(default_factory=dict)
    context_observation_count: Optional[int] = 0

    # Phase 9 Global Historical Baselines & Temporal Pattern Intelligence
    temporal_sources: Optional[List[str]] = Field(default_factory=list)
    temporal_provenance: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    historical_baseline: Optional[Dict[str, Any]] = Field(default_factory=dict)
    persistence_assessment: Optional[Dict[str, Any]] = Field(default_factory=dict)
    recurrence_assessment: Optional[Dict[str, Any]] = Field(default_factory=dict)
    temporal_patterns: Optional[Dict[str, Any]] = Field(default_factory=dict)
    temporal_anomalies: Optional[Dict[str, Any]] = Field(default_factory=dict)
    temporal_uncertainty: Optional[Dict[str, Any]] = Field(default_factory=dict)
    temporal_coverage: Optional[Dict[str, Any]] = Field(default_factory=dict)
    temporal_observation_count: Optional[int] = 0

    # Phase 10 Global Environmental Intelligence & Cross-Modal Verification
    environmental_sources: Optional[List[str]] = Field(default_factory=list)
    environmental_provenance: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    environmental_observations: Optional[Any] = Field(default_factory=dict)
    environmental_relationships: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    environmental_coverage: Optional[Dict[str, Any]] = Field(default_factory=dict)
    environmental_uncertainty: Optional[Dict[str, Any]] = Field(default_factory=dict)
    environmental_conflicts: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    cross_modal_sources: Optional[List[str]] = Field(default_factory=list)
    cross_modal_evidence: Optional[Dict[str, Any]] = Field(default_factory=dict)
    cross_modal_uncertainty: Optional[Dict[str, Any]] = Field(default_factory=dict)
    environmental_observation_count: Optional[int] = 0
    cross_modal_observation_count: Optional[int] = 0

    # Phase 11 Global Evidence Graph & Explainable Intelligence
    evidence_graph: Optional[Dict[str, Any]] = Field(default_factory=dict)
    evidence_nodes: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    evidence_edges: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    hypotheses: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    hypothesis_support: Optional[Dict[str, Any]] = Field(default_factory=dict)
    hypothesis_conflicts: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    evidence_lineage: Optional[Dict[str, Any]] = Field(default_factory=dict)
    evidence_uncertainty: Optional[Dict[str, Any]] = Field(default_factory=dict)
    assessment_lineage: Optional[Dict[str, Any]] = Field(default_factory=dict)
    data_gaps: Optional[List[Dict[str, Any]]] = Field(default_factory=list)

    # Phase 12 Multi-Event Global Incident Correlation
    related_event_ids: Optional[List[str]] = Field(default_factory=list)
    event_relationships: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    event_clusters: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    incident_hypotheses: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    incident_assessment: Optional[Dict[str, Any]] = Field(default_factory=dict)
    incident_geometry: Optional[Dict[str, Any]] = Field(default_factory=dict)
    incident_evidence: Optional[Dict[str, Any]] = Field(default_factory=dict)
    incident_uncertainty: Optional[Dict[str, Any]] = Field(default_factory=dict)
    incident_data_gaps: Optional[List[Dict[str, Any]]] = Field(default_factory=list)

    # Phase 13 Global Intelligence Fusion & Decision-Support Synthesis
    unified_assessment: Optional[Dict[str, Any]] = Field(default_factory=dict)
    assessment_history: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    assessment_changes: Optional[Union[Dict[str, Any], str]] = Field(default_factory=dict)
    decision_support: Optional[Dict[str, Any]] = Field(default_factory=dict)
    recommended_verification: Optional[List[Union[str, Dict[str, Any]]]] = Field(default_factory=list)
    assessment_provenance: Optional[Dict[str, Any]] = Field(default_factory=dict)
    assessment_evidence_ids: Optional[List[str]] = Field(default_factory=list)
    assessment_uncertainty: Optional[Dict[str, Any]] = Field(default_factory=dict)
    assessment_mode: Optional[str] = "ANALYST"


class SessionContext(BaseModel):

    session_id: str
    current_event_ref: Optional[str] = None
    current_region: Optional[str] = None
    active_investigation_id: Optional[str] = None
    last_intent: Optional[str] = None
    candidate_set: List[Dict[str, Any]] = Field(default_factory=list)
    selected_candidate_ref: Optional[str] = None
    comparison_set: List[str] = Field(default_factory=list)
    last_winner_reason: Optional[str] = None
    command_history: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# =================================================================================
# PHASE 14 CASE ACTION & GOVERNANCE REQUEST SCHEMAS
# =================================================================================

class CaseActionExecutionRequest(BaseModel):
    action: str = Field(..., description="Action name, e.g. OPEN_CASE, START_INVESTIGATION, REQUEST_REVIEW, VERIFY, REJECT, MARK_INCONCLUSIVE, REQUEST_MORE_EVIDENCE, ADD_NOTE, ADD_EVIDENCE_REFERENCE, ESCALATE, RESOLVE, CLOSE, REOPEN")
    reason: Optional[str] = Field(None, description="Detailed justification or verification notes")
    evidence_ids: Optional[List[str]] = Field(default_factory=list, description="Associated evidence identifiers")
    supporting_evidence: Optional[List[str]] = Field(default_factory=list, description="Supporting evidence references")
    verifier: Optional[str] = Field(None, description="Explicit human verifier identifier")
    confirm_governed_action: bool = Field(False, description="Explicit human confirmation flag for protected write actions")


class CaseNoteCreateRequest(BaseModel):
    content: str = Field(..., description="Structured analyst note content")
    case_version: Optional[int] = Field(None, description="Associated case or assessment version")


class EvidenceReviewUpdateRequest(BaseModel):
    evidence_id: str = Field(..., description="Target evidence item identifier")
    status: str = Field(..., description="Review status: UNREVIEWED, REVIEWED, ACCEPTED, QUESTIONED, REJECTED")
    notes: Optional[str] = Field(None, description="Analyst review notes or justification")


class EvidenceRequestCreateRequest(BaseModel):
    requested_source: str = Field(..., description="Requested source, e.g. HIGH_RESOLUTION_OPTICAL, SAR_RADAR, GROUND_TELEMETRY")
    reason: str = Field(..., description="Rationale for requested telemetry")
    uncertainty_target: Optional[str] = Field(None, description="Targeted epistemic uncertainty gap")
    priority: Optional[str] = Field("MEDIUM", description="CRITICAL, HIGH, MEDIUM, LOW")

