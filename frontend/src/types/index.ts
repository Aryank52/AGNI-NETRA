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
