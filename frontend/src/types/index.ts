export type UserRole = "PUBLIC" | "RESEARCHER" | "INDUSTRY" | "ANALYST" | "AGENCY" | "ADMIN";

export interface User {
  id: string;
  email: string;
  full_name: string;
  organization?: string;
  role: UserRole;
  facility_id?: string;
  is_active: boolean;
  created_at: string;
}

export interface ShapContributor {
  feature: string;
  value: number | string;
  shap_value: number;
}

export interface ShapExplanation {
  base_value: number;
  predicted_class: string;
  top_contributors: ShapContributor[];
  all_contributions?: ShapContributor[];
}

export interface ModelPrediction {
  predicted_class: string;
  confidence: number;
  class_probabilities: Record<string, number>;
  shap_values: ShapExplanation;
  explanation_summary?: string;
  predicted_at: string;
}

export interface RiskScore {
  risk_score: number;
  risk_level: "LOW" | "MODERATE" | "HIGH" | "CRITICAL";
  intensity_subscore: number;
  abnormality_subscore: number;
  persistence_subscore: number;
  exposure_subscore: number;
  context_subscore: number;
  risk_reasons: string[];
  evaluated_at: string;
}

export interface EventFeatures {
  frp_max: number;
  frp_avg: number;
  dist_to_facility_m: number;
  dist_to_forest_m: number;
  dist_to_agriculture_m: number;
  dist_to_settlement_m: number;
  persistence_score: number;
  recurrence_rate: number;
  day_night_ratio: number;
  baseline_deviation_ratio: number;
  industrial_context_score: number;
}

export interface ThermalEvent {
  id: string;
  event_code: string;
  latitude: number;
  longitude: number;
  bounding_box?: [number, number, number, number];
  first_seen: string;
  last_seen: string;
  detection_count: number;
  avg_frp: number;
  max_frp: number;
  min_frp: number;
  frp_variance: number;
  avg_brightness: number;
  satellite_count: number;
  facility_id?: string;
  candidate_facility_id?: string;
  facility_status: "KNOWN" | "CANDIDATE" | "UNKNOWN" | "VERIFIED";
  nearest_facility_distance_m?: number;
  landcover_class: string;
  state: string;
  district?: string;
  status: "ACTIVE" | "DORMANT" | "RESOLVED";
  is_demo: boolean;
  created_at: string;
  
  prediction?: ModelPrediction;
  risk?: RiskScore;
  features?: EventFeatures;
}

export interface HistoricalBaseline {
  id: string;
  mean_frp: number;
  median_frp: number;
  std_frp: number;
  max_historical_frp: number;
  detection_frequency_monthly: number;
  day_night_ratio: number;
  monthly_pattern: Record<string, number>;
  baseline_status: string;
}

export interface IndustrialFacility {
  id: string;
  name: string;
  facility_type: string;
  status: string;
  source: string;
  state: string;
  district?: string;
  latitude: number;
  longitude: number;
  confidence_score: number;
  operating_hours: string;
  contact_info: Record<string, any>;
  baselines: HistoricalBaseline[];
}

export interface CandidateFacility {
  id: string;
  name_label: string;
  status: string;
  latitude: number;
  longitude: number;
  state: string;
  district?: string;
  industrial_context_score: number;
  persistence_days: number;
  detection_count: number;
  first_detected_at: string;
  last_detected_at: string;
  evidence_summary: Record<string, any>;
}

export interface Alert {
  id: string;
  alert_id?: string;
  event_id: string;
  alert_level: "LOW" | "MODERATE" | "HIGH" | "CRITICAL";
  alert_type: string;
  title: string;
  description: string;
  status: "NEW" | "ACKNOWLEDGED" | "UNDER_INVESTIGATION" | "VERIFIED" | "ESCALATED" | "DISMISSED" | "CLOSED" | "RESOLVED";
  routing_tier?: "TIER_1_AUTO_DISPATCH_CANDIDATE" | "TIER_2_ANALYST_REVIEW_QUEUE" | "TIER_3_UNCERTAINTY_QUEUE";
  priority_score?: number;
  predicted_class?: string;
  confidence?: number;
  risk_score?: number;
  evidence_summary?: Record<string, any>;
  is_operational_dispatch?: boolean;
  acknowledged_by?: string;
  created_at: string;
  updated_at?: string;
  event_code?: string;
  state?: string;
  district?: string;
  latitude?: number;
  longitude?: number;
  max_frp?: number;
}

export interface AlertItem extends Alert {}

export interface DashboardKPIs {
  active_events_count: number;
  industrial_candidates_count: number;
  persistent_sources_count: number;
  abnormal_anomalies_count: number;
  critical_alerts_count: number;
  verification_queue_count: number;
}

export interface CommandCenterData {
  status: string;
  system_timestamp: string;
  kpis: {
    total_live_events: number;
    active_events: number;
    total_alerts: number;
    active_alerts: number;
    max_frp_mw: number;
    avg_frp_mw: number;
    total_detections_ingested: number;
    stream_freshness_timestamp: string | null;
  };
  alert_queues: {
    tier_1_auto_dispatch_candidate: number;
    tier_2_analyst_review: number;
    tier_3_uncertainty: number;
  };
  lifecycle_breakdown: Record<string, number>;
  risk_breakdown: {
    CRITICAL: number;
    HIGH: number;
    MODERATE: number;
    LOW: number;
  };
  model_metadata: {
    champion_version: string;
    algorithm: string;
    registry_status: string;
    is_active: boolean;
    accuracy_score: number;
    f1_score: number;
  };
  safety_invariants: {
    is_operational_dispatch: boolean;
    live_dispatches_emitted: number;
    dispatch_gate_status: string;
    database_immutability_status: string;
    provenance_standard: string;
  };
}

export interface AuditTrailItem {
  audit_id: string;
  action: string;
  previous_state: string;
  new_state: string;
  analyst_name: string;
  notes: string;
  verification_outcome?: string;
  timestamp: string;
}

export interface AlertDossier {
  alert_metadata: {
    alert_id: string;
    event_id: string;
    title: string;
    description: string;
    lifecycle_state: string;
    routing_tier: string;
    priority_score: number;
    alert_level: string;
    alert_type: string;
    created_at: string;
    updated_at: string;
  };
  thermal_event: {
    event_id: string;
    event_code: string;
    latitude: number;
    longitude: number;
    state: string;
    district: string;
    detection_count: number;
    max_frp: number;
    avg_frp: number;
    avg_brightness: number;
    first_seen: string;
    last_seen: string;
    status: string;
    is_demo: boolean;
    provenance: string;
  };
  firms_observations: Array<{
    detection_id: string;
    latitude: number;
    longitude: number;
    acq_timestamp: string;
    brightness: number;
    frp: number;
    confidence: number;
    day_night: string;
    sensor: string;
  }>;
  ml_inference: {
    predicted_class: string;
    calibrated_confidence: number;
    class_probabilities: Record<string, number>;
    shap_top_contributors: Array<{ feature: string; shap_value: number }>;
  };
  risk_assessment: {
    composite_risk_score: number;
    risk_level: string;
    intensity_subscore: number;
    exposure_subscore: number;
    context_subscore: number;
  };
  evidence_sources: {
    osm_industrial_facilities: Array<Record<string, any>>;
    cea_power_stations: Array<Record<string, any>>;
    ibm_mining_leases: {
      district: string;
      total_leases: number;
      total_area_hectares: number;
      commodities: string[];
      top_mines: Array<Record<string, any>>;
    };
    bhuvan_lulc_context: {
      landcover_class: string;
      lulc_code: number;
      description: string;
    };
    fsi_forest_context: {
      forest_density_class: string;
      dist_to_protected_area_m: number;
      nearest_protected_area: string;
      is_inside_protected_area: boolean;
    };
    provenance_guarantee: string;
  };
  audit_trail: AuditTrailItem[];
  safety_invariants: {
    is_operational_dispatch: boolean;
    dispatch_gate_status: string;
  };
}

export interface OperationalTrends {
  classifications: Array<{ label: string; count: number }>;
  state_analytics: Array<{ state: string; event_count: number; max_frp: number; high_risk: number }>;
  audit_outcomes: Record<string, number>;
}

// ==============================================================================
// JARVIS MASTER AGENT & COMMAND ORCHESTRATION LAYER TYPES
// ==============================================================================

export type JarvisState = 
  | "IDLE"
  | "UNDERSTANDING"
  | "PLANNING"
  | "EXECUTING"
  | "EVALUATING"
  | "WAITING_FOR_INPUT"
  | "REQUIRES_APPROVAL"
  | "COMPLETED"
  | "FAILED"
  | "BLOCKED";

export type JarvisCapability = 
  | "GEOINT"
  | "THERMAL_INTELLIGENCE"
  | "CLASSIFICATION"
  | "ANOMALY_ANALYSIS"
  | "HISTORICAL_ANALYSIS"
  | "RISK_ANALYSIS"
  | "ALERT_ANALYSIS"
  | "VERIFICATION"
  | "REPORTING"
  | "SYSTEM_GOVERNANCE"
  | "CROSS_SOURCE_CORRELATION";

export type AgentType = 
  | "JARVIS"
  | "JARVIS-MASTER"
  | "JARVIS-GEO"
  | "JARVIS-ML"
  | "JARVIS-ANOM"
  | "JARVIS-RISK"
  | "JARVIS-SAT"
  | "JARVIS-INVEST"
  | "JARVIS-REPORT"
  | "JARVIS-GUARD"
  | string;

export type StepStatus = "PENDING" | "RUNNING" | "COMPLETED" | "FAILED" | "BLOCKED" | "SKIPPED";

export interface ExecutionStep {
  step_number: number;
  agent: string; // Controlled by ONE master agent: JARVIS
  capability?: string; // Internal capability invoked (GEOINT, CLASSIFICATION, etc.)
  action: string;
  tool?: string;
  parameters?: Record<string, any>;
  status: StepStatus;
  result_summary?: string;
  data_snapshot?: Record<string, any>;
  error?: string;
  duration_ms: number;
}

export interface StateTransition {
  state: string;
  timestamp: string;
  note?: string;
}

export interface CommandObjective {
  primary_goal: string;
  candidate_count?: number;
  constraints: string[];
  target_hypothesis?: string;
  ranking_criteria?: string;
  requested_evidence: string[];
  requested_output: string;
  stopping_condition?: string;
  resolved_from_context: boolean;
  contextual_reference?: string;
}

export interface ExecutionTrace {
  trace_id: string;
  command: string;
  parsed_intent: string;
  target_event?: string;
  target_region?: string;
  user_role: string;
  current_state?: JarvisState;
  objective?: CommandObjective;
  stopping_reason?: string;
  capabilities_used?: string[];
  state_transitions?: StateTransition[];
  steps: ExecutionStep[];
  total_duration_ms: number;
  status: StepStatus;
  started_at: string;
  completed_at?: string;
}

export interface CategorizedSynthesis {
  facts: string[];
  derived_analysis: string[];
  model_output: string[];
  spatial_context: string[];
  inferences: string[];
  recommendations: string[];
  uncertainties_and_warnings: string[];
}

export interface FusedEvidence {
  thermal_evidence?: Record<string, any>;
  geospatial_evidence?: Record<string, any>;
  classification?: Record<string, any>;
  anomaly?: Record<string, any>;
  baseline?: Record<string, any>;
  risk?: Record<string, any>;
  alert?: Record<string, any>;
  verification?: Record<string, any>;
  satellite_observations?: Array<Record<string, any>>;
  categorized_synthesis?: CategorizedSynthesis;
  evidence_quality: {
    completeness_score: number;
    provenance: string;
    missing_elements: string[];
    status: string;
  };
}

export interface JarvisResponse {
  command: string;
  intent: string;
  state?: JarvisState;
  objective?: CommandObjective;
  stopping_reason?: string;
  capabilities_used?: string[];
  summary: string;
  details: Record<string, any>;
  fused_evidence: FusedEvidence;
  execution_trace: ExecutionTrace;
  recommendations: string[];
  requires_human_approval: boolean;
  dispatch_gate_blocked: boolean;
  system_notice: string;
  investigation_id?: string;
  investigation_status?: string;
  investigation_summary?: Record<string, any>;
  investigation_workspace?: InvestigationWorkspace;
  evidence_conflicts?: Array<Record<string, any>>;
  evidence_strength?: string;
  evidence_strength_details?: Record<string, any>;
  analyst_ranking?: Array<Record<string, any>>;
  uncertainty_assessment?: Record<string, any>;
  what_could_change?: string[];
  operator_summary?: Record<string, any>;
  // Phase 6 Global Intelligence & Provider Abstraction
  sources_used?: string[];
  coverage_profile?: string;
  missing_sources?: string[];
  partial_sources?: string[];
  source_availability_matrix?: Record<string, string>;
  provenance_records?: Array<Record<string, any>>;
  // Phase 7 Global Thermal Intelligence & Multi-Provider Fusion
  thermal_sources?: string[];
  source_agreement?: string;
  source_conflicts?: Array<Record<string, any>>;
  observation_count?: number;
  observation_provenance?: Array<Record<string, any>>;
  thermal_coverage?: Record<string, any>;
  // Phase 8 Global Context Intelligence & Cross-Domain Fusion
  context_sources?: string[];
  context_provenance?: Array<Record<string, any>>;
  context_relationships?: Array<Record<string, any>>;
  context_coverage?: Record<string, any>;
  context_conflicts?: Array<Record<string, any>>;
  context_uncertainty?: string;
  context_observation_count?: number;
  // Phase 9 Global Historical Baselines & Temporal Pattern Intelligence
  temporal_sources?: string[];
  temporal_provenance?: Array<Record<string, any>>;
  historical_baseline?: Record<string, any>;
  persistence_assessment?: Record<string, any>;
  recurrence_assessment?: Record<string, any>;
  temporal_patterns?: Record<string, any>;
  temporal_anomalies?: Record<string, any>;
  temporal_uncertainty?: Record<string, any>;
  temporal_coverage?: Record<string, any>;
  temporal_observation_count?: number;
  // Phase 10 Global Environmental Intelligence & Cross-Modal Verification
  environmental_sources?: string[];
  environmental_provenance?: Array<Record<string, any>>;
  environmental_observations?: Array<Record<string, any>>;
  environmental_relationships?: Array<Record<string, any>>;
  environmental_coverage?: Record<string, any>;
  environmental_uncertainty?: Record<string, any>;
  environmental_conflicts?: Array<Record<string, any>>;
  cross_modal_sources?: string[];
  cross_modal_evidence?: Record<string, any>;
  cross_modal_uncertainty?: Record<string, any>;
  environmental_observation_count?: number;
  cross_modal_observation_count?: number;
}

export interface JarvisToolInfo {
  name: string;
  purpose?: string;
  capability?: string;
  input_schema?: Record<string, any>;
  output_schema?: Record<string, any>;
  dependencies?: string[];
  description: string;
  agent: string;
  parameters: Record<string, any>;
  required_role: string;
  is_mutation: boolean;
  is_dispatch: boolean;
  risk_level: string;
  audit_required: boolean;
  read_only: boolean;
}

export type InvestigationStatus = 
  | "CREATED"
  | "ACTIVE"
  | "ANALYZING"
  | "AWAITING_INPUT"
  | "REQUIRES_HUMAN_REVIEW"
  | "COMPLETED"
  | "CLOSED";

export type EpistemicType = 
  | "FACT"
  | "MODEL_OUTPUT"
  | "DERIVED_ANALYSIS"
  | "SPATIAL_CONTEXT"
  | "HISTORICAL_CONTEXT"
  | "INFERENCE"
  | "RECOMMENDATION";

export interface StructuredEvidenceItem {
  evidence_id: string;
  type: string;
  source: string;
  timestamp: string;
  value?: any;
  confidence?: number;
  tool?: string;
  execution_id?: string;
  epistemic_type: EpistemicType;
  freshness_status: string;
}

export interface InvestigationWorkspace {
  investigation_id: string;
  session_id: string;
  created_at?: string;
  updated_at?: string;
  created_by?: string;
  user_role?: string;
  status: InvestigationStatus;
  primary_objective?: string;
  target_event_id?: string;
  target_region?: string;
  candidate_set?: Array<Record<string, any>>;
  selected_candidate?: string;
  comparison_set?: string[];
  command_history?: Array<{
    command: string;
    intent: string;
    trace_id?: string;
    timestamp: string;
  }>;
  execution_ids?: string[];
  evidence_summary?: Record<string, any>;
  classification_summary?: Record<string, any>;
  risk_summary?: Record<string, any>;
  anomaly_summary?: Record<string, any>;
  historical_summary?: Record<string, any>;
  spatial_summary?: Record<string, any>;
  verification_status?: string;
  report_status?: string;
  report_id?: string;
  report_file_path?: string;
  open_questions?: Array<{ question: string; status?: string }>;
  resolved_questions?: Array<{ question: string; resolved_by?: string; resolution?: string; resolved_at?: string }>;
  warnings?: string[];
  data_provenance?: Record<string, any>;
  structured_evidence?: StructuredEvidenceItem[];
  current_winner?: string;
  winner_reason?: string;
  completed_subtasks?: Array<{ id: string; name: string; summary: string; completed_at?: string }>;
  pending_subtasks?: Array<{ id: string; name: string; summary: string; capability?: string }>;
  blocked_subtasks?: Array<{ id: string; name: string; summary: string; reason?: string }>;
  action_graph?: {
    active_stage: string;
    stages: Array<{
      id: string;
      label: string;
      status: 'PENDING' | 'IN_PROGRESS' | 'COMPLETED' | 'BLOCKED';
      step_ref?: string | null;
    }>;
    last_updated?: string;
  };
  objective_history?: Array<{
    objective: string;
    target_event?: string;
    timestamp: string;
  }>;
  stopping_condition?: string;
  stopping_evidence?: string;
  conflicts?: Array<{
    conflict_id?: string;
    type?: string;
    severity?: string;
    dimension_a?: string;
    signal_a?: string;
    dimension_b?: string;
    signal_b?: string;
    explanation?: string;
    recommended_action?: string;
  }>;
  uncertainty?: {
    uncertainty_level?: string;
    known?: Array<{ factor?: string; description?: string; source?: string }>;
    uncertain?: Array<{ factor?: string; description?: string; reason?: string }>;
    missing?: Array<{ factor?: string; description?: string; impact?: string }>;
    conflicting?: Array<{ conflict_id?: string; severity?: string; explanation?: string }>;
    what_could_change?: string[];
    recommended_next_step?: string;
  };
  evidence_strength?: string;
  evidence_strength_details?: {
    evidence_strength?: string;
    strength_level?: string;
    verdict?: string;
    completeness_score?: number;
    consistency_score?: number;
    breakdown?: Record<string, any>;
    key_drivers?: string[];
    gaps?: string[];
  };
  analyst_ranking?: Array<{
    event_code: string;
    rank?: number;
    state?: string;
    max_frp?: number;
    risk_score?: number;
    risk_level?: string;
    analyst_priority_score?: number;
    priority_level?: string;
    score_breakdown?: {
      risk_component?: number;
      anomaly_component?: number;
      proximity_component?: number;
      verification_urgency?: number;
      uncertainty_urgency?: number;
    };
    triage_reason?: string;
    facility_name?: string;
    facility_distance_m?: number;
    baseline_ratio?: number;
  }>;
  constraints?: Record<string, any>;
  operational_recommendations?: string[];
  // Phase 6 Global Intelligence & Provider Abstraction
  sources_used?: string[];
  coverage_profile?: string;
  missing_sources?: string[];
  partial_sources?: string[];
  source_availability_matrix?: Record<string, string>;
  provenance_records?: Array<{
    provider: string;
    dataset: string;
    source_record_id?: string;
    observation_time?: string;
    retrieval_time?: string;
    geographic_coverage?: string;
    spatial_resolution?: string;
    temporal_resolution?: string;
    source_version?: string;
    limitations?: string;
    confidence_tier?: string;
  }>;
  country?: string;
  jurisdiction?: string;
  // Phase 7 Global Thermal Intelligence & Multi-Provider Fusion
  thermal_sources?: string[];
  observation_provenance?: Array<Record<string, any>>;
  source_agreement?: string;
  source_conflicts?: Array<Record<string, any>>;
  thermal_coverage?: Record<string, any>;
  observation_count?: number;
  // Phase 8 Global Context Intelligence & Cross-Domain Fusion
  context_sources?: string[];
  context_provenance?: Array<Record<string, any>>;
  context_relationships?: Array<Record<string, any>>;
  context_coverage?: Record<string, any>;
  context_conflicts?: Array<Record<string, any>>;
  context_uncertainty?: string;
  context_observation_count?: number;
  // Phase 9 Global Historical Baselines & Temporal Pattern Intelligence
  temporal_sources?: string[];
  temporal_provenance?: Array<Record<string, any>>;
  historical_baseline?: Record<string, any>;
  persistence_assessment?: Record<string, any>;
  recurrence_assessment?: Record<string, any>;
  temporal_patterns?: Record<string, any>;
  temporal_anomalies?: Record<string, any>;
  temporal_uncertainty?: Record<string, any>;
  temporal_coverage?: Record<string, any>;
  temporal_observation_count?: number;
  baseline_frp_mean?: number | null;
  baseline_frp_std?: number | null;
  baseline_sample_size?: number | null;
  baseline_window_days?: number | null;
  persistence_score?: number | null;
  persistence_tier?: string | null;
  recurrence_category?: string | null;
  recurrence_count?: number | null;
  seasonality_classification?: string | null;
  temporal_deviation_zscore?: number | null;
  temporal_anomaly_flag?: boolean | null;
  // Phase 10 Global Environmental Intelligence & Cross-Modal Verification
  environmental_sources?: string[];
  environmental_provenance?: Array<Record<string, any>>;
  environmental_observations?: Record<string, any> | Array<Record<string, any>>;
  environmental_relationships?: Array<Record<string, any>>;
  environmental_coverage?: Record<string, any>;
  environmental_uncertainty?: Record<string, any>;
  environmental_conflicts?: Array<Record<string, any>>;
  environmental_observation_count?: number;
  cross_modal_sources?: string[];
  cross_modal_evidence?: Record<string, any>;
  cross_modal_uncertainty?: Record<string, any>;
  cross_modal_observation_count?: number;
}


