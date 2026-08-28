"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import Header from "@/components/layout/Header";
import Sidebar from "@/components/layout/Sidebar";
import MapLibreView from "@/components/map/MapLibreView";
import LayerControl from "@/components/map/LayerControl";
import TimeSlider from "@/components/map/TimeSlider";
import RiskBadge from "@/components/intelligence/RiskBadge";
import ShapWaterfallChart from "@/components/intelligence/ShapWaterfallChart";
import EvidenceSummaryCard from "@/components/intelligence/EvidenceSummaryCard";
import { ThermalEvent, DashboardKPIs } from "@/types";
import { fetchApi } from "@/lib/api";
import { 
  Flame, ShieldAlert, Activity, Search, 
  Layers, FileText, CheckCircle2, ChevronRight, 
  Download, X, RefreshCw, Filter, Sparkles
} from "lucide-react";

const INDIAN_STATES = [
  "India",
  "Gujarat",
  "Madhya Pradesh",
  "Chhattisgarh",
  "Odisha",
  "Punjab",
  "Andhra Pradesh",
  "Jharkhand",
  "Maharashtra",
];

export default function DashboardPage() {
  const [events, setEvents] = useState<ThermalEvent[]>([]);
  const [kpis, setKpis] = useState<DashboardKPIs | null>(null);
  const [selectedEvent, setSelectedEvent] = useState<ThermalEvent | null>(null);
  const [selectedState, setSelectedState] = useState("India");
  const [selectedRisk, setSelectedRisk] = useState("ALL");
  const [timeRange, setTimeRange] = useState("30d");
  const [loading, setLoading] = useState(true);
  const [eventsDrawerOpen, setEventsDrawerOpen] = useState(false);

  const [layers, setLayers] = useState({
    thermalHotspots: true,
    riskHeatmap: true,
    facilities: true,
    candidates: true,
    stateBoundaries: true,
  });

  const handleToggleLayer = (key: keyof typeof layers) => {
    setLayers((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const loadData = async () => {
    setLoading(true);
    try {
      const stateParam = selectedState === "India" ? "" : `?state=${selectedState}`;
      const [eventsData, kpisData] = await Promise.all([
        fetchApi<ThermalEvent[]>(`/events${stateParam}`),
        fetchApi<DashboardKPIs>("/analytics/kpis"),
      ]);
      setEvents(eventsData);
      setKpis(kpisData);
      if (eventsData.length > 0 && !selectedEvent) {
        setSelectedEvent(eventsData[0]);
      }
    } catch (err) {
      console.warn("Using offline seed fallback for frontend dashboard:", err);
      // Deterministic client fallback if backend is momentarily offline
      const mockEvents: ThermalEvent[] = [
        {
          id: "evt-mock-01",
          event_code: "EVT-2026-08-0001",
          latitude: 22.3552,
          longitude: 69.8658,
          first_seen: new Date(Date.now() - 86400000 * 5).toISOString(),
          last_seen: new Date().toISOString(),
          detection_count: 15,
          avg_frp: 128.5,
          max_frp: 210.0,
          min_frp: 45.0,
          frp_variance: 450.0,
          avg_brightness: 345.0,
          satellite_count: 3,
          facility_status: "KNOWN",
          nearest_facility_distance_m: 120.0,
          landcover_class: "Industrial",
          state: "Gujarat",
          district: "Jamnagar",
          status: "ACTIVE",
          is_demo: true,
          created_at: new Date().toISOString(),
          prediction: {
            predicted_class: "Gas Flare",
            confidence: 0.94,
            class_probabilities: { "Gas Flare": 0.94, "Industrial Fire": 0.04, "Other": 0.02 },
            shap_values: {
              base_value: 0.143,
              predicted_class: "Gas Flare",
              top_contributors: [
                { feature: "day_night_ratio", value: 1.4, shap_value: 0.42 },
                { feature: "dist_to_facility_m", value: 120.0, shap_value: 0.35 },
                { feature: "persistence_score", value: 8.2, shap_value: 0.31 },
              ],
            },
            explanation_summary: "Classified as Gas Flare (94.0% confidence) based on continuous 24x7 flaring within Jamnagar Refinery.",
            predicted_at: new Date().toISOString(),
          },
          risk: {
            risk_score: 54.0,
            risk_level: "MODERATE",
            intensity_subscore: 65.0,
            abnormality_subscore: 20.0,
            persistence_subscore: 82.0,
            exposure_subscore: 40.0,
            context_subscore: 90.0,
            risk_reasons: ["Continuous flaring within registered refinery footprint", "Elevated radiative output"],
            evaluated_at: new Date().toISOString(),
          },
          features: {
            frp_max: 210.0,
            frp_avg: 128.5,
            dist_to_facility_m: 120.0,
            dist_to_forest_m: 15000.0,
            dist_to_agriculture_m: 12000.0,
            dist_to_settlement_m: 3500.0,
            persistence_score: 8.2,
            recurrence_rate: 1.8,
            day_night_ratio: 1.4,
            baseline_deviation_ratio: 1.05,
            industrial_context_score: 0.95,
          },
        },
        {
          id: "evt-mock-02",
          event_code: "EVT-2026-08-0002",
          latitude: 24.1032,
          longitude: 82.6841,
          first_seen: new Date(Date.now() - 86400000 * 3).toISOString(),
          last_seen: new Date().toISOString(),
          detection_count: 12,
          avg_frp: 245.0,
          max_frp: 320.0,
          min_frp: 80.0,
          frp_variance: 620.0,
          avg_brightness: 395.0,
          satellite_count: 2,
          facility_status: "KNOWN",
          nearest_facility_distance_m: 150.0,
          landcover_class: "Industrial",
          state: "Madhya Pradesh",
          district: "Singrauli",
          status: "ACTIVE",
          is_demo: true,
          created_at: new Date().toISOString(),
          prediction: {
            predicted_class: "Industrial Fire",
            confidence: 0.91,
            class_probabilities: { "Industrial Fire": 0.91, "Gas Flare": 0.06, "Other": 0.03 },
            shap_values: {
              base_value: 0.143,
              predicted_class: "Industrial Fire",
              top_contributors: [
                { feature: "baseline_deviation_ratio", value: 2.85, shap_value: 0.45 },
                { feature: "frp_max", value: 320.0, shap_value: 0.38 },
                { feature: "dist_to_facility_m", value: 150.0, shap_value: 0.28 },
              ],
            },
            explanation_summary: "Critical thermal deviation spike (+3.2σ above historical mean) detected at Singrauli Power Station.",
            predicted_at: new Date().toISOString(),
          },
          risk: {
            risk_score: 88.5,
            risk_level: "CRITICAL",
            intensity_subscore: 95.0,
            abnormality_subscore: 90.0,
            persistence_subscore: 75.0,
            exposure_subscore: 85.0,
            context_subscore: 95.0,
            risk_reasons: [
              "Severe radiative heat output (Peak FRP: 320.0 MW)",
              "Critical baseline deviation (+3.2σ above historical mean)",
              "Proximity to residential settlement and heavy power infrastructure",
            ],
            evaluated_at: new Date().toISOString(),
          },
          features: {
            frp_max: 320.0,
            frp_avg: 245.0,
            dist_to_facility_m: 150.0,
            dist_to_forest_m: 8000.0,
            dist_to_agriculture_m: 6000.0,
            dist_to_settlement_m: 800.0,
            persistence_score: 7.2,
            recurrence_rate: 2.4,
            day_night_ratio: 0.95,
            baseline_deviation_ratio: 2.85,
            industrial_context_score: 0.92,
          },
        },
        {
          id: "evt-mock-03",
          event_code: "EVT-2026-08-0003",
          latitude: 21.6280,
          longitude: 73.0150,
          first_seen: new Date(Date.now() - 86400000 * 7).toISOString(),
          last_seen: new Date().toISOString(),
          detection_count: 10,
          avg_frp: 72.0,
          max_frp: 110.0,
          min_frp: 25.0,
          frp_variance: 180.0,
          avg_brightness: 340.0,
          satellite_count: 2,
          facility_status: "CANDIDATE",
          nearest_facility_distance_m: 3500.0,
          landcover_class: "Barren / Scrub",
          state: "Gujarat",
          district: "Bharuch",
          status: "ACTIVE",
          is_demo: true,
          created_at: new Date().toISOString(),
          prediction: {
            predicted_class: "Industrial Fire",
            confidence: 0.82,
            class_probabilities: { "Industrial Fire": 0.82, "Mining Activity": 0.12, "Other": 0.06 },
            shap_values: {
              base_value: 0.143,
              predicted_class: "Industrial Fire",
              top_contributors: [
                { feature: "industrial_context_score", value: 0.85, shap_value: 0.38 },
                { feature: "day_night_ratio", value: 0.85, shap_value: 0.32 },
                { feature: "persistence_score", value: 6.8, shap_value: 0.25 },
              ],
            },
            explanation_summary: "Discovered Candidate Industrial Source (USP): Recurrent 24x7 night emissions with high spatial stability in uncataloged zone.",
            predicted_at: new Date().toISOString(),
          },
          risk: {
            risk_score: 62.0,
            risk_level: "HIGH",
            intensity_subscore: 55.0,
            abnormality_subscore: 60.0,
            persistence_subscore: 70.0,
            exposure_subscore: 65.0,
            context_subscore: 75.0,
            risk_reasons: [
              "Emerging candidate industrial thermal source requiring validation",
              "Continuous multiday emissions detected over 7 days",
            ],
            evaluated_at: new Date().toISOString(),
          },
          features: {
            frp_max: 110.0,
            frp_avg: 72.0,
            dist_to_facility_m: 3500.0,
            dist_to_forest_m: 20000.0,
            dist_to_agriculture_m: 8000.0,
            dist_to_settlement_m: 1800.0,
            persistence_score: 6.8,
            recurrence_rate: 1.4,
            day_night_ratio: 0.85,
            baseline_deviation_ratio: 1.0,
            industrial_context_score: 0.85,
          },
        },
      ];

      setEvents(mockEvents);
      setSelectedEvent(mockEvents[0]);
      setKpis({
        active_events_count: 8,
        industrial_candidates_count: 1,
        persistent_sources_count: 4,
        abnormal_anomalies_count: 1,
        critical_alerts_count: 1,
        verification_queue_count: 2,
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [selectedState, selectedRisk]);

  const filteredEvents = events.filter((e) => {
    if (selectedRisk !== "ALL" && e.risk?.risk_level !== selectedRisk) return false;
    return true;
  });

  return (
    <div className="min-h-screen bg-agni-navy flex flex-col selection:bg-amber-500 selection:text-slate-950">
      <Header />

      <div className="flex flex-1 overflow-hidden">
        <Sidebar />

        <main className="flex-1 flex flex-col min-w-0 overflow-hidden relative">
          {/* Top KPI Metric Cards Strip */}
          <div className="p-3 bg-agni-slate border-b border-agni-border grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2.5 shrink-0">
            <div className="p-2.5 rounded-xl bg-agni-card border border-agni-border flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-amber-500/10 text-amber-400 flex items-center justify-center font-bold">
                <Flame className="w-4 h-4" />
              </div>
              <div>
                <div className="text-sm font-mono font-bold text-white">
                  {kpis?.active_events_count ?? 8}
                </div>
                <div className="text-[10px] text-slate-400 font-medium leading-none">Active Events</div>
              </div>
            </div>

            <div className="p-2.5 rounded-xl bg-agni-card border border-purple-500/30 flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-purple-500/15 text-purple-300 flex items-center justify-center font-bold">
                <Search className="w-4 h-4" />
              </div>
              <div>
                <div className="text-sm font-mono font-bold text-purple-300">
                  {kpis?.industrial_candidates_count ?? 1}
                </div>
                <div className="text-[10px] text-slate-400 font-medium leading-none">Candidates (USP)</div>
              </div>
            </div>

            <div className="p-2.5 rounded-xl bg-agni-card border border-agni-border flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-emerald-500/10 text-emerald-400 flex items-center justify-center font-bold">
                <Activity className="w-4 h-4" />
              </div>
              <div>
                <div className="text-sm font-mono font-bold text-white">
                  {kpis?.persistent_sources_count ?? 4}
                </div>
                <div className="text-[10px] text-slate-400 font-medium leading-none">Persistent Sources</div>
              </div>
            </div>

            <div className="p-2.5 rounded-xl bg-agni-card border border-agni-border flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-cyan-500/10 text-cyan-400 flex items-center justify-center font-bold">
                <Sparkles className="w-4 h-4" />
              </div>
              <div>
                <div className="text-sm font-mono font-bold text-white">
                  {kpis?.abnormal_anomalies_count ?? 1}
                </div>
                <div className="text-[10px] text-slate-400 font-medium leading-none">Abnormal (+3σ)</div>
              </div>
            </div>

            <div className="p-2.5 rounded-xl bg-agni-card border border-red-500/30 flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-red-500/15 text-red-400 flex items-center justify-center font-bold">
                <ShieldAlert className="w-4 h-4" />
              </div>
              <div>
                <div className="text-sm font-mono font-bold text-red-400">
                  {kpis?.critical_alerts_count ?? 1}
                </div>
                <div className="text-[10px] text-slate-400 font-medium leading-none">Critical Alerts</div>
              </div>
            </div>

            <div className="p-2.5 rounded-xl bg-agni-card border border-agni-border flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-blue-500/10 text-blue-400 flex items-center justify-center font-bold">
                <CheckCircle2 className="w-4 h-4" />
              </div>
              <div>
                <div className="text-sm font-mono font-bold text-white">
                  {kpis?.verification_queue_count ?? 2}
                </div>
                <div className="text-[10px] text-slate-400 font-medium leading-none">HITL Review Queue</div>
              </div>
            </div>
          </div>

          {/* Map Filter Strip */}
          <div className="p-2.5 bg-agni-slate/90 border-b border-agni-border flex flex-wrap items-center justify-between gap-3 text-xs z-20">
            <div className="flex items-center gap-2 flex-wrap">
              <div className="flex items-center gap-1.5 font-semibold text-slate-300">
                <Filter className="w-3.5 h-3.5 text-amber-400" />
                <span>Geographic Scope:</span>
              </div>
              <select
                value={selectedState}
                onChange={(e) => setSelectedState(e.target.value)}
                className="px-2.5 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-white font-medium focus:outline-none focus:border-amber-500"
              >
                {INDIAN_STATES.map((st) => (
                  <option key={st} value={st}>
                    {st === "India" ? "National (All India)" : st}
                  </option>
                ))}
              </select>

              <div className="flex items-center gap-1.5 ml-2 font-semibold text-slate-300">
                <span>Risk Level:</span>
              </div>
              <select
                value={selectedRisk}
                onChange={(e) => setSelectedRisk(e.target.value)}
                className="px-2.5 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-white font-medium focus:outline-none focus:border-amber-500"
              >
                <option value="ALL">All Risk Levels</option>
                <option value="CRITICAL">Critical Risk Only</option>
                <option value="HIGH">High Risk</option>
                <option value="MODERATE">Moderate Risk</option>
                <option value="LOW">Low Risk</option>
              </select>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={() => setEventsDrawerOpen(!eventsDrawerOpen)}
                className="px-3 py-1.5 rounded-lg bg-agni-card hover:bg-slate-800 border border-agni-border text-slate-200 font-semibold flex items-center gap-1.5 transition-colors"
              >
                <Layers className="w-3.5 h-3.5 text-amber-400" />
                <span>Events List ({filteredEvents.length})</span>
              </button>
              <button
                onClick={loadData}
                disabled={loading}
                className="p-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-400 hover:text-white"
                title="Refresh Map Observations"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin text-amber-400" : ""}`} />
              </button>
            </div>
          </div>

          {/* Main Map Viewport */}
          <div className="flex-1 relative overflow-hidden">
            <MapLibreView
              events={filteredEvents}
              selectedEventId={selectedEvent?.id}
              onSelectEvent={(evt) => setSelectedEvent(evt)}
              selectedState={selectedState}
              layers={layers}
            />

            <LayerControl layers={layers} onToggleLayer={handleToggleLayer} />
            <TimeSlider selectedRange={timeRange} onSelectRange={setTimeRange} />

            {/* Selected Event Quick Intelligence Drawer */}
            {selectedEvent && (
              <div className="absolute top-4 left-4 z-20 w-96 max-w-[calc(100vw-2rem)] bg-agni-card/95 border border-agni-border rounded-2xl p-4 shadow-2xl backdrop-blur-xl space-y-3.5 max-h-[calc(100vh-14rem)] overflow-y-auto animate-in fade-in slide-in-from-left-4">
                <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-sm font-bold text-amber-400">
                      {selectedEvent.event_code}
                    </span>
                    <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-400">
                      {selectedEvent.state}
                    </span>
                  </div>
                  <button
                    onClick={() => setSelectedEvent(null)}
                    className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>

                {/* Classification & Risk Badge */}
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-[10px] uppercase font-mono text-slate-400">AI Classification</div>
                    <div className="text-base font-extrabold text-white">
                      {selectedEvent.prediction?.predicted_class || "Uncertain"}
                    </div>
                  </div>
                  <RiskBadge
                    level={selectedEvent.risk?.risk_level || "LOW"}
                    score={selectedEvent.risk?.risk_score}
                  />
                </div>

                {/* Metric Strip */}
                <div className="grid grid-cols-3 gap-2 text-xs font-mono p-2.5 rounded-xl bg-slate-900/80 border border-slate-800">
                  <div>
                    <div className="text-[10px] text-slate-500">PEAK FRP</div>
                    <div className="font-bold text-amber-400">{selectedEvent.max_frp.toFixed(1)} MW</div>
                  </div>
                  <div>
                    <div className="text-[10px] text-slate-500">OBSERVATIONS</div>
                    <div className="font-bold text-white">{selectedEvent.detection_count} passes</div>
                  </div>
                  <div>
                    <div className="text-[10px] text-slate-500">PERSISTENCE</div>
                    <div className="font-bold text-emerald-400">
                      {selectedEvent.features?.persistence_score?.toFixed(1) || "N/A"}/10
                    </div>
                  </div>
                </div>

                {/* SHAP Feature Contribution Waterfall */}
                <ShapWaterfallChart
                  shapData={selectedEvent.prediction?.shap_values}
                  predictedClass={selectedEvent.prediction?.predicted_class}
                  confidence={selectedEvent.prediction?.confidence}
                />

                {/* Multi-Sensor Evidence Breakdown */}
                <EvidenceSummaryCard event={selectedEvent} />

                {/* Action Buttons */}
                <div className="pt-2 flex items-center gap-2">
                  <Link
                    href={`/dashboard/events/${selectedEvent.id}`}
                    className="flex-1 py-2 rounded-xl bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold text-xs flex items-center justify-center gap-1.5 shadow-md transition-colors"
                  >
                    <span>Full Intelligence Dossier</span>
                    <ChevronRight className="w-3.5 h-3.5" />
                  </Link>

                  <a
                    href={`http://localhost:8000/api/v1/reports/event/${selectedEvent.id}/download`}
                    target="_blank"
                    rel="noreferrer"
                    className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200"
                    title="Download Official PDF Intelligence Report"
                  >
                    <Download className="w-4 h-4 text-amber-400" />
                  </a>
                </div>
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}
