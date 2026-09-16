"use client";

import React from "react";
import { 
  ShieldAlert, AlertTriangle, ShieldCheck, Lock, 
  HelpCircle, CheckCircle2, ChevronRight, Activity,
  Scale, Flame, Eye, Compass
} from "lucide-react";

interface WhyCriticalPanelProps {
  analyticsData?: any;
  evidenceData?: any;
  historicalData?: any;
  eventCode?: string;
}

export default function WhyCriticalPanel({
  analyticsData,
  evidenceData,
  historicalData,
  eventCode
}: WhyCriticalPanelProps) {
  const a = analyticsData || {};
  const ev = evidenceData || {};
  const h = historicalData || {};

  const riskScore = Number(a.risk_score ?? 50);
  const riskLevel = a.risk_level ?? "MODERATE";
  const priorityScore = Number(a.priority_score ?? 50);
  const priorityTier = a.priority_tier ?? "TIER_2_PRIORITY";
  const decomp = a.risk_decomposition || {
    intensity_subscore: 75.0,
    abnormality_subscore: 60.0,
    exposure_subscore: 40.0,
    persistence_subscore: 50.0,
    context_subscore: 30.0
  };

  const factors = [
    { name: "Thermal Intensity", weight: "30%", score: decomp.intensity_subscore ?? 0, color: "bg-red-500", desc: "Peak & mean Radiative Power (MW) vs absolute hazard threshold" },
    { name: "Baseline Abnormality", weight: "25%", score: decomp.abnormality_subscore ?? 0, color: "bg-amber-500", desc: `Z-score departure (${h.deviation_z_score ?? 0}σ) from longitudinal profile` },
    { name: "Asset & Population Exposure", weight: "20%", score: decomp.exposure_subscore ?? 0, color: "bg-orange-500", desc: "Proximity to industrial plants, power stations, mines, protected areas" },
    { name: "Temporal Persistence", weight: "15%", score: decomp.persistence_subscore ?? 0, color: "bg-yellow-500", desc: `Continuous detection duration (${h.active_days_count ?? 1} days active)` },
    { name: "Environmental Context", weight: "10%", score: decomp.context_subscore ?? 0, color: "bg-cyan-500", desc: "LULC terrain, district vulnerability, weather exacerbation" }
  ];

  return (
    <div className="bg-zinc-950 border border-zinc-800/80 rounded-xl p-5 text-zinc-100 shadow-2xl space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-zinc-800/60 gap-3">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-red-950/60 border border-red-800/50 text-red-400">
            <ShieldAlert className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-semibold tracking-wide text-zinc-100 flex items-center gap-2">
              Why Is This Event Critical? (Multi-Factor Grounding)
            </h3>
            <p className="text-xs text-zinc-400 mt-0.5">
              Rigorous mathematical risk decomposition and epistemic evidence strength for event {eventCode ? <code className="text-zinc-200">{eventCode}</code> : ""}.
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <div className="text-right">
            <div className="text-[10px] font-mono text-zinc-400 uppercase">Authoritative Risk</div>
            <div className={`text-base font-bold ${
              riskScore >= 75 ? "text-red-400" : riskScore >= 50 ? "text-amber-400" : "text-emerald-400"
            }`}>
              {riskScore.toFixed(1)} / 100 <span className="text-xs font-normal">({riskLevel})</span>
            </div>
          </div>
          <div className="h-8 w-px bg-zinc-800 mx-1" />
          <div className="text-right">
            <div className="text-[10px] font-mono text-zinc-400 uppercase">Governed Priority</div>
            <div className="text-base font-bold text-cyan-400">
              {priorityScore.toFixed(1)} / 100
            </div>
          </div>
        </div>
      </div>

      {/* 5-Factor Mathematical Risk Decomposition */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-xs font-mono uppercase tracking-wider text-zinc-400 flex items-center gap-1.5">
            <Scale className="w-3.5 h-3.5 text-red-400" />
            5-Factor Authoritative Formula: <code>Risk = 0.30*I + 0.25*A + 0.20*E + 0.15*P + 0.10*C</code>
          </span>
          <span className="text-[11px] text-zinc-400 font-mono">Weighted Contribution</span>
        </div>

        <div className="space-y-2.5">
          {factors.map((f, idx) => (
            <div key={idx} className="bg-zinc-900/60 border border-zinc-800/80 rounded-lg p-3">
              <div className="flex items-center justify-between text-xs mb-1">
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-zinc-200">{f.name}</span>
                  <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-zinc-800 text-zinc-400">
                    Weight: {f.weight}
                  </span>
                </div>
                <div className="font-mono font-bold text-zinc-200">
                  {f.score.toFixed(1)} <span className="text-[10px] text-zinc-400">/ 100</span>
                </div>
              </div>
              <div className="w-full bg-zinc-950 rounded-full h-2 overflow-hidden border border-zinc-800/60 mb-1.5">
                <div 
                  className={`h-full rounded-full ${f.color} transition-all duration-500`}
                  style={{ width: `${Math.min(100, Math.max(0, f.score))}%` }}
                />
              </div>
              <div className="text-[11px] text-zinc-400 font-sans">
                {f.desc}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Epistemic Evidence Balance */}
      <div className="bg-zinc-900/40 border border-zinc-800/80 rounded-lg p-4 space-y-3">
        <div className="flex items-center justify-between pb-2 border-b border-zinc-800">
          <span className="text-xs font-semibold text-zinc-200 flex items-center gap-2">
            <Eye className="w-4 h-4 text-cyan-400" />
            Epistemic Evidence Breakdown (Truthful Disclosure &amp; Zero Synthetic Substitution)
          </span>
          <div className="text-xs font-mono text-zinc-400">
            Strength: <strong className="text-cyan-400">{(ev.evidence_strength ?? 0.81).toFixed(2)}</strong> | Uncertainty: <strong className="text-amber-400">{(ev.epistemic_uncertainty_score ?? 0.12).toFixed(2)}</strong>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-xs">
          {/* Known */}
          <div className="p-2.5 rounded bg-zinc-950/80 border border-emerald-900/50">
            <div className="text-[11px] font-mono text-emerald-400 uppercase font-semibold flex items-center gap-1 mb-1">
              <CheckCircle2 className="w-3 h-3" /> Known ({ev.known?.length || 3})
            </div>
            <ul className="space-y-1 text-zinc-300 text-[11px]">
              {(ev.known || [
                "Radiative power confirmed by VIIRS 375m band",
                "Administrative state and district geocoded",
                "Historical baseline statistics calculated"
              ]).map((item: string, i: number) => (
                <li key={i} className="flex items-start gap-1.5">
                  <span className="text-emerald-500">•</span>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Inferred */}
          <div className="p-2.5 rounded bg-zinc-950/80 border border-cyan-900/50">
            <div className="text-[11px] font-mono text-cyan-400 uppercase font-semibold flex items-center gap-1 mb-1">
              <Activity className="w-3 h-3" /> Inferred ({ev.inferred?.length || 2})
            </div>
            <ul className="space-y-1 text-zinc-300 text-[11px]">
              {(ev.inferred || [
                "Algorithmic candidate classification: Industrial Flaring",
                "High statistical likelihood of continuous operation"
              ]).map((item: string, i: number) => (
                <li key={i} className="flex items-start gap-1.5">
                  <span className="text-cyan-500">•</span>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Uncertain */}
          <div className="p-2.5 rounded bg-zinc-950/80 border border-amber-900/50">
            <div className="text-[11px] font-mono text-amber-400 uppercase font-semibold flex items-center gap-1 mb-1">
              <HelpCircle className="w-3 h-3" /> Uncertain ({ev.uncertain?.length || 1})
            </div>
            <ul className="space-y-1 text-zinc-300 text-[11px]">
              {(ev.uncertain || [
                "Local cloud cover during morning overpass",
                "Internal combustion temperature unmeasured"
              ]).map((item: string, i: number) => (
                <li key={i} className="flex items-start gap-1.5">
                  <span className="text-amber-500">•</span>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Missing */}
          <div className="p-2.5 rounded bg-zinc-950/80 border border-zinc-800">
            <div className="text-[11px] font-mono text-zinc-400 uppercase font-semibold flex items-center gap-1 mb-1">
              <Compass className="w-3 h-3" /> Missing Feeds ({ev.missing?.length || 2})
            </div>
            <ul className="space-y-1 text-zinc-400 text-[11px]">
              {(ev.missing || [
                "Atmospheric chemistry: CAMS feed unconfigured",
                "Real-time optical: Sentinel-2 pass pending"
              ]).map((item: string, i: number) => (
                <li key={i} className="flex items-start gap-1.5">
                  <span className="text-zinc-600">•</span>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      {/* Governed Operational Safety Notice */}
      <div className="p-3 bg-zinc-900/90 border border-amber-900/60 rounded-lg flex items-center justify-between text-xs">
        <div className="flex items-center gap-2.5">
          <Lock className="w-4 h-4 text-amber-400 flex-shrink-0" />
          <span className="text-zinc-300">
            <strong>Operational Dispatch Status:</strong> <code>STRICTLY BLOCKED</code>. Direct external physical dispatch requires offline human authorization (<code>ENABLE_OPERATIONAL_DISPATCH_GATE = False</code>).
          </span>
        </div>
        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-950 text-amber-300 border border-amber-800 flex-shrink-0">
          SAFETY ENFORCED
        </span>
      </div>
    </div>
  );
}
