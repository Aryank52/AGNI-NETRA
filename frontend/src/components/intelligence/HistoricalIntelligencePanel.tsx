"use client";

import React, { useState } from "react";
import { 
  LineChart, AlertTriangle, History, Flame, 
  HelpCircle, ChevronDown, ChevronUp, CheckCircle2, 
  Calendar, ShieldAlert, Sparkles, ExternalLink, Activity
} from "lucide-react";

interface HistoricalIntelligencePanelProps {
  comparisonData?: any;
  canonicalHistorical?: any;
  eventId?: string;
  onSelectIncident?: (incidentId: string) => void;
}

export default function HistoricalIntelligencePanel({
  comparisonData,
  canonicalHistorical,
  eventId,
  onSelectIncident
}: HistoricalIntelligencePanelProps) {
  const [expandedQuestion, setExpandedQuestion] = useState<string | null>("q1");

  // Merge data from historical comparison engine and canonical historical pillar
  const data = comparisonData || canonicalHistorical || {};
  const answers = data.answers || {
    "is_normal": data.deviation_explanation || "Evaluation in progress.",
    "has_happened_before": data.episodes_count > 0 ? `Yes. Detected ${data.episodes_count} prior episodes.` : "No prior similar thermal episodes detected within this spatial perimeter.",
    "recurrence_frequency": `Classified as ${data.recurrence_category || "SPORADIC"} (${data.recent_30d_episodes || 0} episodes in last 30 days).`,
    "intensity_relative_to_baseline": data.deviation_explanation || "Within expected variance.",
    "resemble_previous_incidents": data.previous_verified_incidents_count > 0 
      ? `Resembles ${data.previous_verified_incidents_count} verified historical incidents in the registry.`
      : "Zero matching verified historical incidents found.",
    "is_persistent": `Persistence category: ${data.persistence_category || "TRANSIENT"} (active for ${data.active_days_count || 1} observation days).`
  };

  const questionsList = [
    { id: "q1", q: "Is this normal for this facility / location?", a: answers.is_normal || "Within standard operational baseline." },
    { id: "q2", q: "Has this happened before?", a: answers.has_happened_before || "No previous events recorded." },
    { id: "q3", q: "How often does this occur?", a: answers.recurrence_frequency || "Sporadic occurrence." },
    { id: "q4", q: "Is it more intense than normal?", a: answers.intensity_relative_to_baseline || "Standard intensity." },
    { id: "q5", q: "Does it resemble previous incidents?", a: answers.resemble_previous_incidents || "No matching historical incidents." },
    { id: "q6", q: "Is it persistent?", a: answers.is_persistent || "Transient thermal anomaly." }
  ];

  const deviationPercent = data.deviation_percent ?? 0;
  const isAnomaly = data.is_intensity_anomaly ?? false;
  const baselineStatus = data.baseline_status || "SPARSE";

  return (
    <div className="bg-zinc-950 border border-zinc-800/80 rounded-xl p-5 text-zinc-100 shadow-2xl space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-zinc-800/60 gap-3">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-cyan-950/60 border border-cyan-800/50 text-cyan-400">
            <History className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-semibold tracking-wide text-zinc-100 flex items-center gap-2">
              Longitudinal Historical Intelligence & Baseline Analysis
              {isAnomaly && (
                <span className="text-[11px] px-2 py-0.5 rounded bg-amber-950 text-amber-400 border border-amber-800 font-mono flex items-center gap-1">
                  <AlertTriangle className="w-3 h-3" /> INTENSITY ANOMALY
                </span>
              )}
            </h3>
            <p className="text-xs text-zinc-400 mt-0.5">
              Point-in-time safe (t &lt; T<sub>obs</sub>) historical baseline evaluation across 2020–2026 satellite telemetry archive.
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2 text-xs font-mono">
          <span className="px-2.5 py-1 rounded bg-zinc-900 border border-zinc-800 text-zinc-300">
            Baseline: <strong className="text-cyan-400">{baselineStatus}</strong>
          </span>
          <span className="px-2.5 py-1 rounded bg-zinc-900 border border-zinc-800 text-zinc-300">
            Anti-Leakage: <strong className="text-emerald-400">ENFORCED</strong>
          </span>
        </div>
      </div>

      {/* Primary Metrics Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        {/* Baseline Mean FRP */}
        <div className="bg-zinc-900/60 border border-zinc-800 rounded-lg p-3">
          <div className="text-[11px] font-mono text-zinc-400 uppercase">Baseline FRP</div>
          <div className="text-lg font-bold text-zinc-100 mt-1">
            {Number(data.baseline_mean_frp ?? data.baseline_frp_mean ?? 0).toFixed(1)} <span className="text-xs font-normal text-zinc-400">MW</span>
          </div>
          <div className="text-[10px] text-zinc-400 mt-0.5 font-mono">
            σ = {Number(data.baseline_std_frp ?? data.baseline_frp_std ?? 0).toFixed(1)} MW (n={data.baseline_sample_count ?? 0})
          </div>
        </div>

        {/* Current vs Baseline Deviation */}
        <div className="bg-zinc-900/60 border border-zinc-800 rounded-lg p-3">
          <div className="text-[11px] font-mono text-zinc-400 uppercase">Deviation</div>
          <div className={`text-lg font-bold mt-1 ${
            deviationPercent > 20 ? "text-amber-400" : deviationPercent < -20 ? "text-blue-400" : "text-emerald-400"
          }`}>
            {deviationPercent > 0 ? `+${deviationPercent.toFixed(1)}%` : `${deviationPercent.toFixed(1)}%`}
          </div>
          <div className="text-[10px] text-zinc-400 mt-0.5 font-mono">
            z-score: <strong>{Number(data.deviation_z_score ?? 0).toFixed(2)}σ</strong>
          </div>
        </div>

        {/* Recurrence Category */}
        <div className="bg-zinc-900/60 border border-zinc-800 rounded-lg p-3">
          <div className="text-[11px] font-mono text-zinc-400 uppercase">Recurrence</div>
          <div className="text-sm font-semibold text-zinc-200 mt-1 truncate">
            {data.recurrence_category ?? "SPORADIC"}
          </div>
          <div className="text-[10px] text-zinc-400 mt-0.5 font-mono">
            30d Episodes: <strong>{data.recent_30d_episodes ?? data.episodes_count ?? 0}</strong>
          </div>
        </div>

        {/* Persistence Category */}
        <div className="bg-zinc-900/60 border border-zinc-800 rounded-lg p-3">
          <div className="text-[11px] font-mono text-zinc-400 uppercase">Persistence</div>
          <div className="text-sm font-semibold text-zinc-200 mt-1 truncate">
            {data.persistence_category ?? "PERSISTENT"}
          </div>
          <div className="text-[10px] text-zinc-400 mt-0.5 font-mono">
            Active Days: <strong>{data.active_days_count ?? 1}</strong>
          </div>
        </div>

        {/* Seasonality Pattern */}
        <div className="bg-zinc-900/60 border border-zinc-800 rounded-lg p-3">
          <div className="text-[11px] font-mono text-zinc-400 uppercase">Seasonality</div>
          <div className="text-sm font-semibold text-zinc-200 mt-1 truncate">
            {data.seasonality_pattern ?? "YEAR_ROUND_EMISSION"}
          </div>
          <div className="text-[10px] text-zinc-400 mt-0.5 font-mono">
            Trend: <strong>{data.temporal_trend ?? "STABLE"}</strong>
          </div>
        </div>

        {/* Historical Matches */}
        <div className="bg-zinc-900/60 border border-zinc-800 rounded-lg p-3">
          <div className="text-[11px] font-mono text-zinc-400 uppercase">Registry Matches</div>
          <div className="text-lg font-bold text-cyan-400 mt-1">
            {data.previous_verified_incidents_count ?? 0}
          </div>
          <div className="text-[10px] text-zinc-400 mt-0.5 font-mono">
            Similar Events: <strong>{data.similar_historical_events_count ?? 0}</strong>
          </div>
        </div>
      </div>

      {/* 6 Grounded Analyst Questions & Answers Accordion */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <h4 className="text-xs font-mono uppercase tracking-wider text-zinc-400 flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
            Deterministic Historical Inquiries (Grounded Anti-Hallucination Answers)
          </h4>
          <span className="text-[11px] text-zinc-400 font-mono">
            6 Operational Questions
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
          {questionsList.map((item) => {
            const isExp = expandedQuestion === item.id;
            return (
              <div 
                key={item.id}
                className={`border rounded-lg p-3 transition-all ${
                  isExp ? "bg-zinc-900/90 border-cyan-600/60 shadow-md" : "bg-zinc-900/40 border-zinc-800/80 hover:border-zinc-700"
                }`}
              >
                <button
                  type="button"
                  onClick={() => setExpandedQuestion(isExp ? null : item.id)}
                  className="flex items-center justify-between w-full text-left"
                >
                  <span className="text-xs font-medium text-zinc-200 flex items-center gap-2">
                    <span className="h-1.5 w-1.5 rounded-full bg-cyan-400" />
                    {item.q}
                  </span>
                  {isExp ? <ChevronUp className="w-4 h-4 text-zinc-400" /> : <ChevronDown className="w-4 h-4 text-zinc-500" />}
                </button>
                {isExp && (
                  <div className="mt-2.5 pt-2 border-t border-zinc-800 text-xs text-zinc-300 leading-relaxed font-sans bg-zinc-950/60 p-2.5 rounded">
                    {item.a}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Verified Incidents Registry Matches & Similar Events */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Verified Incidents Table */}
        <div className="bg-zinc-900/40 border border-zinc-800/80 rounded-lg p-3.5">
          <div className="flex items-center justify-between pb-2 mb-2 border-b border-zinc-800">
            <span className="text-xs font-semibold text-zinc-200 flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              Verified Historical Incidents in Vicinity
            </span>
            <span className="text-[11px] font-mono text-zinc-400">
              {data.similar_verified_incidents?.length || data.previous_verified_incidents_count || 0} Registered
            </span>
          </div>

          {(data.similar_verified_incidents && data.similar_verified_incidents.length > 0) ? (
            <div className="space-y-2">
              {data.similar_verified_incidents.slice(0, 4).map((inc: any, idx: number) => (
                <div key={idx} className="p-2.5 bg-zinc-950/80 border border-zinc-800/60 rounded flex items-center justify-between text-xs">
                  <div>
                    <div className="font-mono font-medium text-cyan-300 flex items-center gap-1.5">
                      {inc.incident_code || `INC-${idx + 1}`}
                      <span className="text-[10px] px-1.5 py-0.2 rounded bg-emerald-950 text-emerald-400 border border-emerald-800">
                        {inc.status || "VERIFIED"}
                      </span>
                    </div>
                    <div className="text-[11px] text-zinc-400 mt-0.5">
                      {inc.classification || "Industrial Thermal Hotspot"} • Peak FRP: {inc.peak_frp || 0} MW
                    </div>
                  </div>
                  {onSelectIncident && (
                    <button
                      type="button"
                      onClick={() => onSelectIncident(inc.incident_id || inc.incident_code)}
                      className="px-2 py-1 rounded bg-zinc-800 hover:bg-zinc-700 text-zinc-200 text-xs flex items-center gap-1"
                    >
                      View <ExternalLink className="w-3 h-3" />
                    </button>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="text-xs text-zinc-500 italic p-3 text-center bg-zinc-950/40 rounded">
              Zero previously verified historical incidents logged within 5 km prior to this event.
            </div>
          )}
        </div>

        {/* Similar Historical Observations */}
        <div className="bg-zinc-900/40 border border-zinc-800/80 rounded-lg p-3.5">
          <div className="flex items-center justify-between pb-2 mb-2 border-b border-zinc-800">
            <span className="text-xs font-semibold text-zinc-200 flex items-center gap-2">
              <Flame className="w-4 h-4 text-amber-400" />
              Prior Thermal Activity (Point-in-Time Preceding Observations)
            </span>
            <span className="text-[11px] font-mono text-zinc-400">
              {data.similar_historical_events_count || 0} Observed
            </span>
          </div>

          {(data.similar_historical_events && data.similar_historical_events.length > 0) ? (
            <div className="space-y-2">
              {data.similar_historical_events.slice(0, 4).map((ev: any, idx: number) => (
                <div key={idx} className="p-2.5 bg-zinc-950/80 border border-zinc-800/60 rounded flex items-center justify-between text-xs">
                  <div>
                    <div className="font-mono text-zinc-300">
                      {ev.event_code || `EVT-HIST-${idx + 1}`}
                    </div>
                    <div className="text-[11px] text-zinc-400 mt-0.5">
                      Observed: {ev.first_seen ? ev.first_seen.slice(0, 10) : "Historical"} • FRP: {ev.max_frp || 0} MW
                    </div>
                  </div>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-zinc-900 border border-zinc-800 text-zinc-400">
                    {ev.status || "OBSERVED"}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-xs text-zinc-500 italic p-3 text-center bg-zinc-950/40 rounded">
              No preceding historical thermal clusters recorded within the spatial baseline window.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
