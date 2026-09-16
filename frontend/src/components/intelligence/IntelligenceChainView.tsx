"use client";

import React, { useState } from "react";
import { 
  Satellite, Flame, Factory, Layers, LineChart, 
  AlertTriangle, Shield, Clock, Bell, CheckSquare, 
  UserCheck, Briefcase, Archive, ChevronRight, CheckCircle2,
  HelpCircle, AlertOctagon, Info
} from "lucide-react";

export interface IntelligenceStageItem {
  stage_id: string;
  stage_number: number;
  label: string;
  category: string;
  status: "COMPLETED" | "CURRENT" | "PENDING" | "BLOCKED" | "NOT_CONFIGURED";
  source: string;
  timestamp?: string;
  summary: string;
  details: Record<string, any>;
}

interface IntelligenceChainViewProps {
  canonicalData?: any;
  onSelectStage?: (stage: IntelligenceStageItem) => void;
}

export default function IntelligenceChainView({ canonicalData, onSelectStage }: IntelligenceChainViewProps) {
  const [selectedStageId, setSelectedStageId] = useState<string>("RISK");

  // Derive stages from canonical intelligence object or provide grounded defaults
  const identity = canonicalData?.identity || {};
  const obs = canonicalData?.observation || {};
  const context = canonicalData?.context || {};
  const hist = canonicalData?.historical || {};
  const analytics = canonicalData?.analytics || {};
  const evidence = canonicalData?.evidence || {};
  const gov = canonicalData?.governance || {};

  const stages: IntelligenceStageItem[] = [
    {
      stage_id: "OBSERVATION",
      stage_number: 1,
      label: "Observation",
      category: "RAW_SATELLITE",
      status: "COMPLETED",
      source: `${obs.primary_sensor || "VIIRS"} (${obs.primary_satellite || "NOAA-20/21"})`,
      timestamp: obs.last_observed_timestamp || identity.first_observed_at,
      summary: `${obs.total_detections || 1} detections with Peak FRP ${obs.peak_frp_mw || 0} MW`,
      details: {
        "Sensor": obs.primary_sensor || "VIIRS",
        "Satellite": obs.primary_satellite || "NOAA-20",
        "Total Detections": obs.total_detections || 1,
        "Peak FRP": `${obs.peak_frp_mw || 0} MW`,
        "Mean FRP": `${obs.mean_frp_mw || 0} MW`,
        "Mean Confidence": `${((obs.mean_confidence || 0.8) * 100).toFixed(0)}%`,
        "Day/Night": obs.day_night_breakdown || { "DAY": 1, "NIGHT": 0 }
      }
    },
    {
      stage_id: "EVENT",
      stage_number: 2,
      label: "Event Formation",
      category: "CLUSTERING",
      status: "COMPLETED",
      source: "AGNI-NETRA Spatial Clustering Engine",
      timestamp: identity.first_observed_at,
      summary: `Clustered into ${identity.event_code || "EVT-..."}`,
      details: {
        "Event Code": identity.event_code,
        "Cluster Radius": "750 m",
        "Spatial Footprint": `${identity.footprint_acres || 5.2} acres`,
        "Coordinates": `${canonicalData?.geography?.latitude?.toFixed(4)}, ${canonicalData?.geography?.longitude?.toFixed(4)}`,
        "State / District": `${canonicalData?.geography?.state}, ${canonicalData?.geography?.district}`
      }
    },
    {
      stage_id: "FACILITY",
      stage_number: 3,
      label: "Facility Matching",
      category: "GEOSPATIAL",
      status: context.facility_matched ? "COMPLETED" : "PENDING",
      source: "National Industrial Infrastructure Database",
      summary: context.facility_matched ? (context.facility_name || "Matched Facility") : "No co-located facility within 2km",
      details: {
        "Matched Facility": context.facility_name || "None (Greenfield / Rural)",
        "Facility Type": context.facility_type || "N/A",
        "Proximity Distance": `${context.distance_to_facility_m || 0} meters`,
        "Clearance Status": context.environmental_clearance_status || "UNVERIFIED"
      }
    },
    {
      stage_id: "SECTOR",
      stage_number: 4,
      label: "Sectoral Taxonomy",
      category: "INDUSTRY",
      status: context.industrial_sector ? "COMPLETED" : "PENDING",
      source: "Ministry of Commerce & Industry Classification",
      summary: context.industrial_sector || "Thermal Emitter",
      details: {
        "Industrial Sector": context.industrial_sector || "Thermal / Multi-use",
        "Subsector": context.subsector || "Standard",
        "Regulatory Oversight": context.regulatory_agency || "CPCB / SPCB",
        "Mining Proximity": `${context.mining_proximity_km || "N/A"} km`
      }
    },
    {
      stage_id: "BASELINE",
      stage_number: 5,
      label: "Historical Baseline",
      category: "LONGITUDINAL",
      status: hist.baseline_status === "NO_BASELINE" ? "PENDING" : "COMPLETED",
      source: "Multi-Year Continental Thermal Archive (2020-2026)",
      summary: `Baseline: ${hist.baseline_mean_frp || 0} MW (σ=${hist.baseline_std_frp || 0} MW, n=${hist.baseline_sample_count || 0})`,
      details: {
        "Baseline Mean FRP": `${hist.baseline_mean_frp || 0} MW`,
        "Baseline Std Dev": `${hist.baseline_std_frp || 0} MW`,
        "Sample Observations": hist.baseline_sample_count || 0,
        "Baseline Status": hist.baseline_status || "SPARSE",
        "Temporal Trend": hist.temporal_trend || "STABLE"
      }
    },
    {
      stage_id: "ANOMALY",
      stage_number: 6,
      label: "Anomaly Detection",
      category: "STATISTICAL",
      status: "COMPLETED",
      source: "Deterministic Point-in-Time Baseline Engine",
      summary: hist.deviation_explanation || "Baseline departure evaluated",
      details: {
        "Deviation Ratio": `${hist.deviation_ratio || 1.0}x`,
        "Deviation Percentage": `${hist.deviation_percent ? (hist.deviation_percent > 0 ? "+" : "") + hist.deviation_percent + "%" : "0%"}`,
        "Z-Score": `${hist.deviation_z_score || 0} σ`,
        "Intensity Anomaly Flag": hist.is_intensity_anomaly ? "ANOMALOUS (HIGH)" : "NORMAL_PROFILE"
      }
    },
    {
      stage_id: "RISK",
      stage_number: 7,
      label: "Authoritative Risk",
      category: "MULTI_FACTOR",
      status: "COMPLETED",
      source: "Deterministic 5-Factor Risk Engine",
      summary: `Risk Score: ${analytics.risk_score || 50}/100 (${analytics.risk_level || "MODERATE"})`,
      details: {
        "Risk Score": `${analytics.risk_score || 50} / 100`,
        "Risk Level": analytics.risk_level || "MODERATE",
        "Formula": "Risk = 0.30*I + 0.25*A + 0.20*E + 0.15*P + 0.10*C",
        "Decomposition": analytics.risk_decomposition || {}
      }
    },
    {
      stage_id: "PRIORITY",
      stage_number: 8,
      label: "Governed Priority",
      category: "QUEUE_SLA",
      status: "COMPLETED",
      source: "Sovereign Queue Governance Engine",
      summary: `Priority Tier: ${analytics.priority_tier || "TIER_2"} (${analytics.priority_score || 50}/100)`,
      details: {
        "Priority Tier": analytics.priority_tier || "TIER_2_PRIORITY",
        "Priority Score": `${analytics.priority_score || 50} / 100`,
        "Formula": "Priority = 0.40*Risk + 0.20*Confidence + 0.30*TierWeight + 0.10*Recency",
        "Action SLA": analytics.priority_tier === "TIER_1_CRITICAL" ? "2 Hours" : "8 Hours"
      }
    },
    {
      stage_id: "ALERT",
      stage_number: 9,
      label: "Alert Routing",
      category: "AUTONOMOUS",
      status: "COMPLETED",
      source: "Operational Dispatch Gate (BLOCKED by policy)",
      summary: "Alert routed to Analyst Triage Queue. Automated Dispatch Gate: BLOCKED",
      details: {
        "Alert Level": analytics.risk_level || "MODERATE",
        "Routing Queue": "TIER_2_ANALYST_TRIAGE",
        "Automated Dispatch Gate": "BLOCKED (ENABLE_OPERATIONAL_DISPATCH_GATE = False)",
        "Safety Invariant": "Direct external physical dispatch strictly prohibited"
      }
    },
    {
      stage_id: "EVALUATION",
      stage_number: 10,
      label: "Epistemic Evaluation",
      category: "MULTI_SOURCE",
      status: "COMPLETED",
      source: "Cross-Sensor & Cross-Provider Evidence Fusion",
      summary: `Evidence Strength: ${(evidence.evidence_strength || 0.8).toFixed(2)} (Uncertainty: ${(evidence.epistemic_uncertainty_score || 0.1).toFixed(2)})`,
      details: {
        "Evidence Strength": `${(evidence.evidence_strength || 0.8).toFixed(2)} / 1.00`,
        "Epistemic Uncertainty": `${(evidence.epistemic_uncertainty_score || 0.1).toFixed(2)} / 1.00`,
        "Known Facts": evidence.known?.length || 0,
        "Inferred Hypotheses": evidence.inferred?.length || 0,
        "Uncertain Items": evidence.uncertain?.length || 0,
        "Missing Data Feeds": evidence.missing?.length || 0
      }
    },
    {
      stage_id: "VERIFICATION",
      stage_number: 11,
      label: "HITL Verification",
      category: "HUMAN_ANALYST",
      status: identity.status === "VERIFIED" ? "COMPLETED" : "CURRENT",
      source: "Human-in-the-Loop Analyst Verification Interface",
      summary: identity.status === "VERIFIED" ? "Verified by Analyst" : "Pending Human Verification",
      details: {
        "Current Status": identity.status || "ACTIVE",
        "Automated Model Activation": "DISABLED (ENABLE_AUTOMATED_MODEL_ACTIVATION = False)",
        "Analyst Workflow": "Independent from JARVIS execution"
      }
    },
    {
      stage_id: "INVESTIGATION",
      stage_number: 12,
      label: "Investigation Case",
      category: "GOVERNANCE",
      status: gov.investigation_case_id ? "COMPLETED" : "PENDING",
      source: "Case Management & Regulatory Compliance Ledger",
      summary: gov.investigation_case_id ? `Linked Case: ${gov.investigation_case_id}` : "No formal investigation case opened yet",
      details: {
        "Case ID": gov.investigation_case_id || "None",
        "Audit Log Trail": `${gov.audit_records_count || 0} immutable audit entries`,
        "Legal Record": "Preserved for statutory compliance"
      }
    },
    {
      stage_id: "HISTORICAL_INCIDENT",
      stage_number: 13,
      label: "Incident Registry",
      category: "ARCHIVE",
      status: hist.previous_verified_incidents_count > 0 ? "COMPLETED" : (identity.status === "VERIFIED" ? "CURRENT" : "PENDING"),
      source: "Authoritative Historical Incident Registry (Table: historical_incidents)",
      summary: hist.previous_verified_incidents_count > 0 ? `${hist.previous_verified_incidents_count} verified historical incidents matched` : "Registered upon human verification",
      details: {
        "Registry Table": "historical_incidents",
        "Matching Incidents": hist.previous_verified_incidents_count || 0,
        "Closed-Loop Policy": "Registered upon CONFIRM or CORRECT action without model retraining"
      }
    }
  ];

  const activeStage = stages.find(s => s.stage_id === selectedStageId) || stages[6];

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "COMPLETED":
        return <span className="px-2 py-0.5 text-xs rounded bg-emerald-950/80 text-emerald-400 border border-emerald-800/60 flex items-center gap-1"><CheckCircle2 className="w-3 h-3" /> Complete</span>;
      case "CURRENT":
        return <span className="px-2 py-0.5 text-xs rounded bg-amber-950/80 text-amber-400 border border-amber-800/60 flex items-center gap-1 animate-pulse"><Clock className="w-3 h-3" /> Current</span>;
      case "BLOCKED":
        return <span className="px-2 py-0.5 text-xs rounded bg-red-950/80 text-red-400 border border-red-800/60 flex items-center gap-1"><AlertOctagon className="w-3 h-3" /> Blocked</span>;
      case "NOT_CONFIGURED":
        return <span className="px-2 py-0.5 text-xs rounded bg-zinc-900 text-zinc-500 border border-zinc-800 flex items-center gap-1"><HelpCircle className="w-3 h-3" /> Unconfigured</span>;
      default:
        return <span className="px-2 py-0.5 text-xs rounded bg-zinc-900 text-zinc-400 border border-zinc-800">Pending</span>;
    }
  };

  const getStageIcon = (stageId: string) => {
    switch (stageId) {
      case "OBSERVATION": return <Satellite className="w-4 h-4" />;
      case "EVENT": return <Flame className="w-4 h-4" />;
      case "FACILITY": return <Factory className="w-4 h-4" />;
      case "SECTOR": return <Layers className="w-4 h-4" />;
      case "BASELINE": return <LineChart className="w-4 h-4" />;
      case "ANOMALY": return <AlertTriangle className="w-4 h-4" />;
      case "RISK": return <Shield className="w-4 h-4" />;
      case "PRIORITY": return <Clock className="w-4 h-4" />;
      case "ALERT": return <Bell className="w-4 h-4" />;
      case "EVALUATION": return <CheckSquare className="w-4 h-4" />;
      case "VERIFICATION": return <UserCheck className="w-4 h-4" />;
      case "INVESTIGATION": return <Briefcase className="w-4 h-4" />;
      case "HISTORICAL_INCIDENT": return <Archive className="w-4 h-4" />;
      default: return <Info className="w-4 h-4" />;
    }
  };

  return (
    <div className="bg-zinc-950 border border-zinc-800/80 rounded-xl p-5 text-zinc-100 shadow-2xl">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-4 mb-5 border-b border-zinc-800/60 gap-3">
        <div>
          <div className="flex items-center gap-2">
            <span className="h-2.5 w-2.5 rounded-full bg-cyan-400 animate-ping" />
            <h3 className="text-base font-semibold tracking-wide text-zinc-100 uppercase">
              13-Stage Visual Intelligence Chain
            </h3>
            <span className="text-xs px-2 py-0.5 rounded bg-zinc-900 text-zinc-400 border border-zinc-800 font-mono">
              OBSERVATION → INCIDENT
            </span>
          </div>
          <p className="text-xs text-zinc-400 mt-1">
            Complete lifecycle provenance from raw satellite sensor capture to authoritative historical incident registry.
          </p>
        </div>
        <div className="text-xs text-zinc-500 font-mono flex items-center gap-2">
          <span>Active Step: <strong className="text-cyan-400">{activeStage.stage_number} / 13</strong> ({activeStage.label})</span>
        </div>
      </div>

      {/* Horizontal Scrollable Stages Stepper */}
      <div className="overflow-x-auto pb-3 mb-5 scrollbar-thin scrollbar-thumb-zinc-800">
        <div className="flex items-center min-w-[1040px] gap-1.5">
          {stages.map((st, idx) => {
            const isSelected = st.stage_id === selectedStageId;
            const isCompleted = st.status === "COMPLETED";
            const isCurrent = st.status === "CURRENT";

            return (
              <React.Fragment key={st.stage_id}>
                <button
                  type="button"
                  onClick={() => {
                    setSelectedStageId(st.stage_id);
                    if (onSelectStage) onSelectStage(st);
                  }}
                  className={`flex flex-col items-start p-2.5 rounded-lg border transition-all text-left flex-1 min-w-[76px] ${
                    isSelected
                      ? "bg-cyan-950/40 border-cyan-500/80 text-cyan-200 shadow-lg shadow-cyan-950/50"
                      : isCompleted
                      ? "bg-zinc-900/60 border-zinc-800 hover:border-zinc-700 text-zinc-300"
                      : isCurrent
                      ? "bg-amber-950/20 border-amber-500/50 text-amber-200"
                      : "bg-zinc-950 border-zinc-800/40 text-zinc-500 hover:text-zinc-400"
                  }`}
                >
                  <div className="flex items-center justify-between w-full mb-1">
                    <span className={`text-[10px] font-mono px-1.5 py-0.2 rounded ${
                      isSelected ? "bg-cyan-900/60 text-cyan-300" : isCompleted ? "bg-emerald-950 text-emerald-400" : "bg-zinc-800 text-zinc-400"
                    }`}>
                      #{st.stage_number}
                    </span>
                    <span className={`${isSelected ? "text-cyan-400" : isCompleted ? "text-emerald-400" : "text-zinc-500"}`}>
                      {getStageIcon(st.stage_id)}
                    </span>
                  </div>
                  <div className="text-xs font-medium truncate w-full">{st.label}</div>
                  <div className="text-[10px] text-zinc-400 truncate w-full mt-0.5">{st.category}</div>
                </button>
                {idx < stages.length - 1 && (
                  <ChevronRight className={`w-3.5 h-3.5 flex-shrink-0 ${
                    isCompleted ? "text-emerald-500/60" : "text-zinc-700"
                  }`} />
                )}
              </React.Fragment>
            );
          })}
        </div>
      </div>

      {/* Selected Stage Detail Card */}
      <div className="bg-zinc-900/50 border border-zinc-800/80 rounded-lg p-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 mb-3 border-b border-zinc-800/60 gap-2">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-zinc-800 text-cyan-400">
              {getStageIcon(activeStage.stage_id)}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-sm font-semibold text-zinc-100">
                  Stage {activeStage.stage_number}: {activeStage.label}
                </span>
                {getStatusBadge(activeStage.status)}
              </div>
              <p className="text-xs text-zinc-400 mt-0.5">
                Authority / Source: <span className="text-zinc-300 font-mono">{activeStage.source}</span>
              </p>
            </div>
          </div>
          {activeStage.timestamp && (
            <div className="text-xs text-zinc-400 font-mono">
              Timestamp: {activeStage.timestamp}
            </div>
          )}
        </div>

        <p className="text-xs text-zinc-300 mb-3 bg-zinc-950/60 p-2.5 rounded border border-zinc-800/60">
          <strong>Summary:</strong> {activeStage.summary}
        </p>

        {/* Key-Value Breakdown */}
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2.5">
          {Object.entries(activeStage.details).map(([key, val]) => (
            <div key={key} className="bg-zinc-950/80 border border-zinc-800/60 rounded p-2.5">
              <div className="text-[11px] text-zinc-400 uppercase tracking-wider font-mono">{key}</div>
              <div className="text-xs font-medium text-zinc-200 mt-0.5 break-all">
                {typeof val === "object" && val !== null ? JSON.stringify(val) : String(val)}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
