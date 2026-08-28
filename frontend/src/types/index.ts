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

export interface AlertItem {
  id: string;
  event_id: string;
  alert_level: "LOW" | "MODERATE" | "HIGH" | "CRITICAL";
  alert_type: string;
  title: string;
  description: string;
  status: "NEW" | "ACKNOWLEDGED" | "UNDER_REVIEW" | "VERIFIED" | "RESOLVED";
  created_at: string;
}

export interface DashboardKPIs {
  active_events_count: number;
  industrial_candidates_count: number;
  persistent_sources_count: number;
  abnormal_anomalies_count: number;
  critical_alerts_count: number;
  verification_queue_count: number;
}
