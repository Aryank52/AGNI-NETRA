"use client";

import React, { useState, useEffect } from "react";
import { formatNumber, formatFrp, formatPercent, formatDistance, safeArray } from "@/lib/formatters";
import { 
  Flame, ShieldAlert, Cpu, Activity, 
  Layers, MapPin, Factory, Zap, Pickaxe, 
  Trees, Clock, ChevronRight, CheckCircle2, 
  AlertTriangle, Radio, BarChart3, Database,
  ArrowUpRight, Info, ShieldCheck, FileText
} from "lucide-react";
import RiskBadge from "./RiskBadge";
import IntelligenceCoveragePanel from "./IntelligenceCoveragePanel";
import ShapWaterfallChart from "./ShapWaterfallChart";
import { fetchApi } from "@/lib/api";

interface DossierProps {
  eventId: string | null;
  onClose?: () => void;
}

export default function EventInvestigationDossier({ eventId, onClose }: DossierProps) {
  const [dossier, setDossier] = useState<any | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<string>("summary");

  useEffect(() => {
    if (!eventId) {
      setDossier(null);
      return;
    }

    setLoading(true);
    setError(null);
    fetchApi<any>(`/gis/dossier/${eventId}`)
      .then((data) => {
        setDossier(data);
      })
      .catch((err) => {
        console.error("Failed to load GIS dossier:", err);
        setError("Failed to load multi-source spatial dossier.");
      })
      .finally(() => setLoading(false));
  }, [eventId]);

  if (!eventId) {
    return (
      <div className="h-full flex flex-col items-center justify-center p-6 text-center text-slate-400 space-y-3 bg-agni-card/40 border border-agni-border/60 rounded-xl">
        <Layers className="w-12 h-12 text-slate-600 stroke-1" />
        <div className="space-y-1">
          <p className="font-semibold text-sm text-slate-300">No Thermal Event Selected</p>
          <p className="text-xs text-slate-500 max-w-xs">
            Click on any thermal hotspot on the GIS map or select from the live event stream to inspect the complete 7-layer evidence cascade.
          </p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="h-full flex flex-col items-center justify-center p-8 space-y-4 bg-agni-card/60 border border-agni-border rounded-xl">
        <div className="w-8 h-8 border-2 border-amber-500 border-t-transparent rounded-full animate-spin" />
        <div className="text-center space-y-1">
          <p className="text-xs font-mono font-bold text-amber-400">FUSING 7-LAYER SPATIAL INTELLIGENCE...</p>
          <p className="text-[11px] text-slate-400">Querying FIRMS • OSM • CEA • IBM • FSI • Bhuvan</p>
        </div>
      </div>
    );
  }

  if (error || !dossier) {
    return (
      <div className="h-full p-6 bg-slate-900/80 border border-red-500/30 rounded-xl text-center space-y-3 text-xs text-slate-300">
        <AlertTriangle className="w-8 h-8 text-red-400 mx-auto" />
        <p className="font-bold text-red-300">{error || "Dossier unavailable"}</p>
        <p className="text-slate-400">Unable to retrieve multi-source dossier for event {eventId}.</p>
      </div>
    );
  }

  const {
    event_code,
    location,
    telemetry,
    ml_intelligence,
    risk_assessment,
    spatial_context_enrichment,
    intelligence_coverage,
    alert_workflow,
  } = dossier;

  const tabs = [
    { id: "summary", label: "Overview & AI" },
    { id: "proximity", label: "Proximity & Energy" },
    { id: "ecology", label: "Forest & LULC" },
    { id: "firms", label: `Observations (${telemetry?.detection_count || 0})` },
    { id: "audit", label: "Alert & Trail" },
  ];

  return (
    <div className="h-full flex flex-col bg-agni-card border border-agni-border rounded-xl overflow-hidden font-sans">
      {/* Dossier Header */}
      <div className="bg-slate-950/80 border-b border-agni-border p-3.5 space-y-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="font-mono text-sm font-extrabold text-amber-400">
              {event_code}
            </span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
              {location?.state}, {location?.district}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <RiskBadge level={risk_assessment?.risk_level || "LOW"} score={risk_assessment?.risk_score} />
            <a
              href={`http://localhost:8000/api/v1/reports/event/${eventId}/download`}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 border border-amber-500/40 text-[11px] font-bold transition-all"
              title="Download Certified PDF Dossier"
            >
              <FileText className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Export PDF</span>
            </a>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex items-center gap-1 border-b border-slate-800/80 pt-1 overflow-x-auto text-xs">
          {tabs.map((t) => (
            <button
              key={t.id}
              onClick={() => setActiveTab(t.id)}
              className={`px-3 py-1.5 font-semibold transition-all border-b-2 whitespace-nowrap text-xs ${
                activeTab === t.id
                  ? "border-amber-500 text-amber-400 bg-amber-500/10 rounded-t"
                  : "border-transparent text-slate-400 hover:text-slate-200"
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>

      {/* Dossier Content Body */}
      <div className="flex-1 overflow-y-auto p-3.5 space-y-3.5 text-xs text-slate-200">
        {/* TAB 1: SUMMARY & AI INTELLIGENCE */}
        {activeTab === "summary" && (
          <div className="space-y-3">
            {/* Intelligence Provenance Panel */}
            <IntelligenceCoveragePanel coverage={intelligence_coverage} eventCode={event_code} />

            {/* AI Classification & Confidence Card */}
            <div className="bg-slate-900/90 border border-indigo-500/30 rounded-xl p-3.5 space-y-2.5">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                <div className="flex items-center gap-2">
                  <Cpu className="w-4 h-4 text-indigo-400" />
                  <span className="font-bold text-xs text-white">AI CLASSIFICATION & CALIBRATION</span>
                </div>
                <span className="text-[10px] font-mono text-indigo-300 bg-indigo-500/20 px-2 py-0.5 rounded">
                  {ml_intelligence?.model_champion}
                </span>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div className="bg-slate-950/60 p-2.5 rounded-lg border border-slate-800">
                  <div className="text-[10px] text-slate-400">Predicted Thermal Source</div>
                  <div className="text-sm font-extrabold text-amber-400 mt-0.5">
                    {ml_intelligence?.predicted_class || "Uncertain"}
                  </div>
                </div>
                <div className="bg-slate-950/60 p-2.5 rounded-lg border border-slate-800">
                  <div className="text-[10px] text-slate-400">Calibrated Confidence</div>
                  <div className="text-sm font-extrabold text-emerald-400 font-mono mt-0.5">
                    {formatPercent(ml_intelligence?.confidence, 1, "80.0%")}
                  </div>
                </div>
              </div>

              {/* SHAP TreeExplainer Attribution Waterfall */}
              <ShapWaterfallChart
                shapData={
                  ml_intelligence?.shap_waterfall?.top_contributors
                    ? ml_intelligence.shap_waterfall
                    : {
                        top_contributors: Object.entries(ml_intelligence?.shap_waterfall || {})
                          .filter(([k, v]) => k !== "base_value" && k !== "predicted_class" && !isNaN(Number(v)))
                          .map(([feature, val]) => ({
                            feature,
                            value: 0,
                            shap_value: Number(val) || 0,
                            impact: (Number(val) || 0) >= 0 ? "POSITIVE" : "NEGATIVE"
                          })),
                        base_value: 0.143
                      }
                }
                predictedClass={ml_intelligence?.predicted_class || "Uncertain"}
                confidence={ml_intelligence?.confidence || 0.8}
              />
            </div>

            {/* Risk Breakdown Card */}
            <div className="bg-slate-900/90 border border-amber-500/30 rounded-xl p-3.5 space-y-2">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                <div className="flex items-center gap-2">
                  <ShieldAlert className="w-4 h-4 text-amber-400" />
                  <span className="font-bold text-xs text-white">MULTI-FACTOR RISK ENGINE</span>
                </div>
                <span className="font-mono text-xs font-bold text-amber-300">
                  {risk_assessment?.risk_score} / 100
                </span>
              </div>

              <div className="grid grid-cols-3 gap-2 text-center">
                <div className="bg-slate-950/60 p-2 rounded-lg border border-slate-800">
                  <div className="text-[10px] text-slate-400">Intensity</div>
                  <div className="text-xs font-bold font-mono text-red-400">{risk_assessment?.intensity_subscore}</div>
                </div>
                <div className="bg-slate-950/60 p-2 rounded-lg border border-slate-800">
                  <div className="text-[10px] text-slate-400">Exposure</div>
                  <div className="text-xs font-bold font-mono text-orange-400">{risk_assessment?.exposure_subscore}</div>
                </div>
                <div className="bg-slate-950/60 p-2 rounded-lg border border-slate-800">
                  <div className="text-[10px] text-slate-400">Context</div>
                  <div className="text-xs font-bold font-mono text-yellow-400">{risk_assessment?.context_subscore}</div>
                </div>
              </div>
            </div>

            {/* WHY WAS THIS EVENT FLAGGED? PANEL */}
            <div className="bg-gradient-to-br from-slate-900 via-slate-900/90 to-slate-950 border border-cyan-500/30 rounded-xl p-3.5 space-y-2.5">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                <div className="flex items-center gap-2">
                  <Info className="w-4 h-4 text-cyan-400" />
                  <span className="font-bold text-xs text-white uppercase tracking-wider">Why Was This Event Flagged?</span>
                </div>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300 font-bold border border-cyan-500/30">
                  Decision Context
                </span>
              </div>

              <div className="space-y-2 text-xs">
                {/* 1. Deterministic Geospatial Facts */}
                <div className="bg-slate-950/60 p-2.5 rounded-lg border border-slate-800/80 space-y-1">
                  <div className="font-bold text-slate-300 text-[11px] flex items-center gap-1.5">
                    <MapPin className="w-3.5 h-3.5 text-amber-400" />
                    <span>1. Deterministic Geospatial Facts</span>
                  </div>
                  <ul className="text-[11px] text-slate-400 space-y-0.5 pl-4 list-disc">
                    <li>
                      Peak FRP: <strong className="text-white">{telemetry?.max_frp_mw} MW</strong> across {telemetry?.detection_count} detection pixels.
                    </li>
                    {spatial_context_enrichment?.nearest_industrial_facilities?.length > 0 ? (
                      <li>
                        Proximity to <strong className="text-cyan-300">{spatial_context_enrichment.nearest_industrial_facilities[0].name}</strong>: {spatial_context_enrichment.nearest_industrial_facilities[0].distance_m}m.
                      </li>
                    ) : (
                      <li>No registered industrial plant within 5,000m buffer.</li>
                    )}
                    <li>
                      LULC Landcover: <strong className="text-lime-400">{spatial_context_enrichment?.landcover_class || "NO_COVERAGE"}</strong>.
                    </li>
                  </ul>
                </div>

                {/* 2. Statistical Baseline Context */}
                <div className="bg-slate-950/60 p-2.5 rounded-lg border border-slate-800/80 space-y-1">
                  <div className="font-bold text-slate-300 text-[11px] flex items-center gap-1.5">
                    <Activity className="w-3.5 h-3.5 text-purple-400" />
                    <span>2. Statistical Baseline & Dynamics</span>
                  </div>
                  <ul className="text-[11px] text-slate-400 space-y-0.5 pl-4 list-disc">
                    <li>
                      30-Day Persistence: <strong className="text-white">{spatial_context_enrichment?.persistence_metrics?.persistence_score}</strong>.
                    </li>
                    <li>
                      365-Day Recurrence: <strong className="text-white">{spatial_context_enrichment?.persistence_metrics?.recurrence_rate}</strong>.
                    </li>
                    <li>
                      Baseline Deviation: <strong className="text-amber-400">{spatial_context_enrichment?.persistence_metrics?.baseline_deviation_ratio}x</strong> historical average.
                    </li>
                  </ul>
                </div>

                {/* 3. ML Attribution Context */}
                <div className="bg-slate-950/60 p-2.5 rounded-lg border border-slate-800/80 space-y-1">
                  <div className="font-bold text-slate-300 text-[11px] flex items-center gap-1.5">
                    <Cpu className="w-3.5 h-3.5 text-indigo-400" />
                    <span>3. Calibrated ML Attribution</span>
                  </div>
                  <p className="text-[11px] text-slate-400">
                    Target classified as <strong className="text-amber-400">{ml_intelligence?.predicted_class}</strong> ({formatPercent(ml_intelligence?.confidence, 1, "80.0%")} confidence).
                    <span className="text-slate-500 italic block mt-0.5">SHAP values provide local mathematical feature attributions, distinguishing statistical alignment from causal physical proof.</span>
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: PROXIMITY & ENERGY INFRASTRUCTURE */}
        {activeTab === "proximity" && (
          <div className="space-y-3">
            {/* Nearest Industrial Facilities */}
            <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-3.5 space-y-2.5">
              <div className="flex items-center gap-2 text-cyan-400 font-bold text-xs border-b border-slate-800 pb-2">
                <Factory className="w-4 h-4" />
                <span>NEAREST INDUSTRIAL FACILITIES (POSTGIS 10KM BUFFER)</span>
              </div>

              {spatial_context_enrichment?.nearest_industrial_facilities?.length > 0 ? (
                <div className="space-y-2">
                  {spatial_context_enrichment.nearest_industrial_facilities.map((fac: any, idx: number) => (
                    <div key={fac.facility_id || idx} className="p-2.5 rounded-lg bg-slate-950/80 border border-slate-800 flex items-center justify-between">
                      <div>
                        <div className="font-semibold text-white text-xs">{fac.name}</div>
                        <div className="text-[10px] text-slate-400">{fac.type} • {fac.sector}</div>
                      </div>
                      <div className="text-right font-mono">
                        <div className="text-xs font-bold text-cyan-300">
                          {formatDistance(fac.distance_m)}
                        </div>
                        <div className="text-[9px] text-slate-500">PROXIMITY</div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-xs text-slate-500 italic p-3 bg-slate-950/40 rounded border border-slate-800/80 text-center">
                  No registered industrial facilities located within 10 km buffer.
                </div>
              )}
            </div>

            {/* Nearest CEA Power Stations */}
            <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-3.5 space-y-2.5">
              <div className="flex items-center gap-2 text-amber-400 font-bold text-xs border-b border-slate-800 pb-2">
                <Zap className="w-4 h-4" />
                <span>CEA POWER GENERATING STATIONS</span>
              </div>

              {spatial_context_enrichment?.nearest_power_stations?.length > 0 ? (
                <div className="space-y-2">
                  {spatial_context_enrichment.nearest_power_stations.map((pow: any, idx: number) => (
                    <div key={pow.facility_id || idx} className="p-2.5 rounded-lg bg-slate-950/80 border border-slate-800 flex items-center justify-between">
                      <div>
                        <div className="font-semibold text-white text-xs">{pow.project_name}</div>
                        <div className="text-[10px] text-slate-400">{pow.organisation} • {pow.prime_mover}</div>
                      </div>
                      <div className="text-right font-mono">
                        <div className="text-xs font-bold text-amber-300">
                          {formatDistance(pow.distance_m)}
                        </div>
                        <div className="text-[9px] text-slate-500">DISTANCE</div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-xs text-slate-500 italic p-3 bg-slate-950/40 rounded border border-slate-800/80 text-center">
                  No CEA power generating stations within vicinity.
                </div>
              )}
            </div>
          </div>
        )}

        {/* TAB 3: ECOLOGICAL & LAND COVER */}
        {activeTab === "ecology" && (
          <div className="space-y-3">
            {/* FSI ISFR District Forest Density */}
            <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-3.5 space-y-2.5">
              <div className="flex items-center gap-2 text-emerald-400 font-bold text-xs border-b border-slate-800 pb-2">
                <Trees className="w-4 h-4" />
                <span>FSI ISFR CANOPY DENSITY ({spatial_context_enrichment?.district_forest_stats?.district})</span>
              </div>

              <div className="grid grid-cols-2 gap-2 text-center font-mono">
                <div className="p-2 bg-slate-950/60 rounded border border-slate-800">
                  <div className="text-[10px] text-slate-400 font-sans">Forest Cover Ratio</div>
                  <div className="text-sm font-bold text-emerald-400 mt-0.5">
                    {spatial_context_enrichment?.district_forest_stats?.forest_cover_percent}%
                  </div>
                </div>
                <div className="p-2 bg-slate-950/60 rounded border border-slate-800">
                  <div className="text-[10px] text-slate-400 font-sans">Very Dense Forest</div>
                  <div className="text-sm font-bold text-white mt-0.5">
                    {spatial_context_enrichment?.district_forest_stats?.very_dense_forest_sqkm || 0} km²
                  </div>
                </div>
              </div>
            </div>

            {/* Nearest Protected Area */}
            <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-3.5 space-y-2.5">
              <div className="flex items-center gap-2 text-emerald-300 font-bold text-xs border-b border-slate-800 pb-2">
                <ShieldCheck className="w-4 h-4" />
                <span>WII PROTECTED AREAS & 10KM ESZ BUFFER</span>
              </div>

              {spatial_context_enrichment?.nearest_protected_areas?.length > 0 ? (
                <div className="space-y-2">
                  {spatial_context_enrichment.nearest_protected_areas.map((pa: any, idx: number) => (
                    <div key={pa.pa_id || idx} className="p-2.5 rounded-lg bg-slate-950/80 border border-slate-800 flex items-center justify-between">
                      <div>
                        <div className="font-semibold text-white text-xs">{pa.name}</div>
                        <div className="text-[10px] text-slate-400">{pa.type} • {pa.state}</div>
                      </div>
                      <div className="text-right font-mono">
                        <div className="text-xs font-bold text-emerald-400">
                          {formatDistance(pa.distance_m)}
                        </div>
                        <div className="text-[9px] text-slate-500">
                          {pa.distance_m <= 10000 ? "INSIDE ESZ" : "OUTSIDE ESZ"}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-xs text-slate-500 italic p-3 bg-slate-950/40 rounded border border-slate-800/80 text-center">
                  No Protected Areas intersecting immediate corridor.
                </div>
              )}
            </div>

            {/* Bhuvan LULC Classification */}
            <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-3.5 space-y-2">
              <div className="flex items-center gap-2 text-lime-400 font-bold text-xs border-b border-slate-800 pb-2">
                <MapPin className="w-4 h-4" />
                <span>ISRO BHUVAN LULC CANONICAL CLASS</span>
              </div>
              <div className="p-2.5 bg-slate-950/80 rounded-lg border border-slate-800 text-xs">
                <span className="text-slate-400">Land Use / Cover: </span>
                <span className="font-bold text-lime-300 font-mono">
                  {spatial_context_enrichment?.landcover_class}
                </span>
              </div>
            </div>
          </div>
        )}

        {/* TAB 4: FIRMS OBSERVATIONS */}
        {activeTab === "firms" && (
          <div className="space-y-2.5">
            <div className="text-[11px] font-bold text-slate-400">
              NASA SATELLITE DETECTIONS FOR EVENT ({telemetry?.firms_observations?.length || 0})
            </div>
            {telemetry?.firms_observations?.map((obs: any, idx: number) => (
              <div key={obs.detection_id || idx} className="p-2.5 rounded-lg bg-slate-950/80 border border-slate-800 flex items-center justify-between text-xs font-mono">
                <div>
                  <div className="text-white font-bold">{obs.sensor} ({obs.satellite})</div>
                  <div className="text-[10px] text-slate-400">{obs.acq_timestamp ? new Date(obs.acq_timestamp).toLocaleString() : "Live"}</div>
                </div>
                <div className="text-right">
                  <div className="text-amber-400 font-bold">{formatFrp(obs.frp)}</div>
                  <div className="text-[10px] text-slate-400">{obs.day_night === "D" ? "Day" : "Night"} • Conf: {obs.confidence}</div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* TAB 5: ALERT WORKFLOW & AUDIT TRAIL */}
        {activeTab === "audit" && (
          <div className="space-y-3">
            <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-3.5 space-y-2">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                <div className="flex items-center gap-2 font-bold text-xs text-white">
                  <Radio className="w-4 h-4 text-cyan-400" />
                  <span>ALERT ROUTING STATUS</span>
                </div>
                <span className="font-mono text-xs font-bold text-cyan-300">
                  {alert_workflow?.routing_tier}
                </span>
              </div>
              <div className="text-xs text-slate-400">
                Current Alert Level: <strong className="text-white">{alert_workflow?.alert_level}</strong>
              </div>
            </div>

            {/* Audit Trail Records */}
            <div className="space-y-2">
              <div className="text-[11px] font-bold text-slate-400">AUDIT TRAIL LOGS</div>
              {alert_workflow?.audit_trail?.length > 0 ? (
                alert_workflow.audit_trail.map((log: any, idx: number) => (
                  <div key={log.audit_id || idx} className="p-2.5 rounded-lg bg-slate-950/80 border border-slate-800 space-y-1 text-xs">
                    <div className="flex items-center justify-between font-mono text-[10px]">
                      <span className="text-amber-400 font-bold">{log.action}</span>
                      <span className="text-slate-500">{log.timestamp ? new Date(log.timestamp).toLocaleString() : "Recorded"}</span>
                    </div>
                    <div className="text-slate-300 text-[11px]">{log.notes || "Workflow transition executed."}</div>
                    <div className="text-[10px] text-slate-400">Analyst: {log.analyst_name}</div>
                  </div>
                ))
              ) : (
                <div className="p-3 bg-slate-950/40 rounded border border-slate-800/80 text-xs text-slate-500 text-center italic">
                  No manual review actions logged yet.
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
