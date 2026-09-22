"use client";

import React, { useState, useEffect } from "react";
import Header from "@/components/layout/Header";
import Sidebar from "@/components/layout/Sidebar";
import { fetchApi } from "@/lib/api";
import { formatFrp } from "@/lib/formatters";
import { 
  BarChart3, PieChart, Activity, 
  TrendingUp, Layers, MapPin, Calendar, Clock, Sparkles,
  ShieldAlert, RefreshCw
} from "lucide-react";
import PageHeader from "@/components/common/PageHeader";
import EmptyState from "@/components/common/EmptyState";
import { CardSkeleton } from "@/components/common/Skeletons";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, 
  ResponsiveContainer, Cell, PieChart as RePieChart, Pie,
  LineChart, Line, Legend, AreaChart, Area
} from "recharts";

export default function AnalyticsPage() {
  const [classDist, setClassDist] = useState<any[]>([]);
  const [riskDist, setRiskDist] = useState<any[]>([]);
  const [stateSummary, setStateSummary] = useState<any[]>([]);
  const [operationalTrends, setOperationalTrends] = useState<any | null>(null);
  const [timeHorizon, setTimeHorizon] = useState<"24H" | "7D" | "30D" | "365D" | "2022-2026">("30D");
  const [timeline, setTimeline] = useState<any[]>([]);
  const [timelineLoading, setTimelineLoading] = useState<boolean>(false);
  const [timelineError, setTimelineError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [analyticsError, setAnalyticsError] = useState<string | null>(null);

  const loadAnalytics = async () => {
    setLoading(true);
    setAnalyticsError(null);
    try {
      const [cData, rData, sData, oData] = await Promise.all([
        fetchApi<any[]>("/analytics/class-distribution"),
        fetchApi<any[]>("/analytics/risk-distribution"),
        fetchApi<any[]>("/analytics/state-summary"),
        fetchApi<any>("/analytics/operational-trends").catch(() => null),
      ]);
      setClassDist(cData || []);
      setRiskDist(rData || []);
      setStateSummary(sData || []);
      setOperationalTrends(oData);
    } catch (err: any) {
      console.error("Failed to load national analytics:", err);
      setAnalyticsError(err?.message || "Failed to load national analytics data from API");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAnalytics();
  }, []);

  const loadTimeline = () => {
    setTimelineLoading(true);
    setTimelineError(null);
    fetchApi<any>("/historical/timeline")
      .then((data) => {
        if (data?.timeline && Array.isArray(data.timeline)) {
          setTimeline(data.timeline);
        } else {
          setTimeline([]);
        }
      })
      .catch((err) => {
        console.warn("Failed to load historical timeline:", err);
        setTimelineError(err?.message || "Failed to load historical timeline");
      })
      .finally(() => setTimelineLoading(false));
  };

  useEffect(() => {
    loadTimeline();
  }, [timeHorizon]);

  const COLORS = ["#f59e0b", "#f97316", "#10b981", "#3b82f6", "#a855f7", "#64748b"];

  return (
    <div className="min-h-screen bg-agni-navy flex flex-col selection:bg-amber-500 selection:text-slate-950">
      <Header />

      <div className="flex flex-1 overflow-hidden">
        <Sidebar />

        <main className="flex-1 overflow-y-auto p-6 space-y-6 max-w-6xl mx-auto">
          {/* Standardized Page Header with Time Horizon Pills */}
          <PageHeader
            category="MULTI-TEMPORAL OPERATIONAL INTELLIGENCE"
            title="National Thermal Analytics & Multi-Temporal Horizons"
            description="Multi-year satellite thermal observation trends, temporal horizons, and 7-class taxonomy distributions across India."
            icon={<BarChart3 className="w-6 h-6 text-amber-400" />}
            actions={
              <div className="flex flex-wrap items-center gap-1.5 bg-slate-900/90 p-1.5 rounded-xl border border-slate-800 text-xs">
                {[
                  { label: "24-Hour", value: "24H" },
                  { label: "7-Day", value: "7D" },
                  { label: "30-Day", value: "30D" },
                  { label: "365-Day", value: "365D" },
                  { label: "2022–2026 Archive", value: "2022-2026" },
                ].map((pill) => (
                  <button
                    key={pill.value}
                    onClick={() => setTimeHorizon(pill.value as any)}
                    className={`px-3 py-1 rounded-lg font-mono font-bold transition-all ${
                      timeHorizon === pill.value
                        ? "bg-amber-500 text-slate-950 shadow-sm"
                        : "text-slate-400 hover:text-white"
                    }`}
                  >
                    {pill.label}
                  </button>
                ))}
              </div>
            }
          />

          {/* Multi-Year Timeline Chart */}
          <div className="p-5 rounded-2xl bg-agni-card border border-agni-border shadow-xl space-y-3">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 border-b border-slate-800 pb-2.5">
              <div>
                <div className="text-[10px] font-mono text-cyan-400 uppercase font-bold tracking-wider">
                  QUESTION: How has thermal activity and radiated energy evolved across time?
                </div>
                <h3 className="text-sm font-bold uppercase tracking-wider text-slate-200 flex items-center gap-2 mt-0.5">
                  <TrendingUp className="w-4 h-4 text-cyan-400" />
                  <span>Temporal Hotspot Ingestion & Mean FRP Trend ({timeHorizon})</span>
                </h3>
              </div>
              <span className="text-[10px] font-mono text-slate-400">
                NASA FIRMS VIIRS / MODIS Archive (8.22M Records)
              </span>
            </div>

            <div className="h-64 w-full flex items-center justify-center">
              {timelineLoading ? (
                <div className="flex items-center gap-2 text-xs font-mono text-slate-400">
                  <RefreshCw className="w-4 h-4 animate-spin text-amber-400" />
                  <span>Loading temporal horizon telemetry...</span>
                </div>
              ) : timelineError ? (
                <div className="text-center space-y-2">
                  <p className="text-xs text-rose-400 font-mono">Failed to load temporal trend: {timelineError}</p>
                  <button
                    onClick={loadTimeline}
                    className="px-3 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-semibold inline-flex items-center gap-1.5"
                  >
                    <RefreshCw className="w-3.5 h-3.5" />
                    <span>Retry Timeline</span>
                  </button>
                </div>
              ) : timeline.length === 0 ? (
                <p className="text-xs text-slate-500 font-mono">No observations recorded for the selected temporal horizon.</p>
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={timeline} margin={{ left: 10, right: 10, top: 10, bottom: 10 }}>
                    <defs>
                      <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.4}/>
                        <stop offset="95%" stopColor="#f59e0b" stopOpacity={0.0}/>
                      </linearGradient>
                    </defs>
                    <XAxis dataKey="period" stroke="#64748b" fontSize={10} />
                    <YAxis stroke="#94a3b8" fontSize={10} />
                    <Tooltip
                      contentStyle={{ background: "#0b1426", border: "1px solid #1e2e4f", borderRadius: "8px", fontSize: "11px" }}
                    />
                    <Area type="monotone" dataKey="detection_count" stroke="#f59e0b" strokeWidth={2} fillOpacity={1} fill="url(#colorCount)" name="Detections" />
                    <Line type="monotone" dataKey="avg_frp" stroke="#38bdf8" strokeWidth={2} dot={{ r: 3 }} name="Mean FRP (MW)" />
                  </AreaChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>

          {/* Loading or Error States for Analytics Sections */}
          {loading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <CardSkeleton />
              <CardSkeleton />
            </div>
          ) : analyticsError ? (
            <EmptyState
              icon={ShieldAlert}
              title="Failed to Load National Analytics"
              description={`The analytics service returned an error (${analyticsError}). National distributions and state breakdowns could not be retrieved.`}
              actionLabel="Retry Loading Analytics"
              onAction={loadAnalytics}
            />
          ) : (
            <>
              {/* Charts Grid */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Classification Distribution */}
                <div className="p-5 rounded-2xl bg-agni-card border border-agni-border shadow-xl space-y-3">
                  <div className="border-b border-slate-800 pb-2">
                <div className="text-[10px] font-mono text-amber-400 uppercase font-bold tracking-wider">
                  QUESTION: Which thermal sources dominate the observation stream?
                </div>
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200 flex items-center gap-2 mt-0.5">
                  <PieChart className="w-4 h-4 text-amber-400" />
                  <span>7-Class Machine Learning Taxonomy Breakdown</span>
                </h3>
              </div>

              <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={classDist} layout="vertical" margin={{ left: 20, right: 20, top: 10, bottom: 10 }}>
                    <XAxis type="number" stroke="#64748b" fontSize={10} />
                    <YAxis dataKey="label" type="category" stroke="#94a3b8" fontSize={10} width={120} />
                    <Tooltip
                      contentStyle={{ background: "#0b1426", border: "1px solid #1e2e4f", borderRadius: "8px", fontSize: "11px" }}
                    />
                    <Bar dataKey="count" fill="#f59e0b" radius={[0, 4, 4, 0]}>
                      {classDist.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Risk Distribution */}
            <div className="p-5 rounded-2xl bg-agni-card border border-agni-border shadow-xl space-y-3">
              <div className="border-b border-slate-800 pb-2">
                <div className="text-[10px] font-mono text-red-400 uppercase font-bold tracking-wider">
                  QUESTION: Where are risk concentrations situated across severity tiers?
                </div>
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200 flex items-center gap-2 mt-0.5">
                  <Activity className="w-4 h-4 text-red-400" />
                  <span>5-Factor Deterministic Risk Distribution</span>
                </h3>
              </div>

              <div className="h-64 w-full flex items-center justify-center">
                <ResponsiveContainer width="100%" height="100%">
                  <RePieChart>
                    <Pie
                      data={riskDist}
                      dataKey="count"
                      nameKey="level"
                      cx="50%"
                      cy="50%"
                      outerRadius={80}
                      innerRadius={45}
                      paddingAngle={4}
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    >
                      {riskDist.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{ background: "#0b1426", border: "1px solid #1e2e4f", borderRadius: "8px", fontSize: "11px" }}
                    />
                  </RePieChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {/* State Wise Summary Table */}
          <div className="p-5 rounded-2xl bg-agni-card border border-agni-border shadow-xl space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200 flex items-center gap-2">
              <MapPin className="w-4 h-4 text-cyan-400" />
              State-Wise Thermal Radiative Intensity & Incident Density
            </h3>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead className="bg-slate-900/80 text-slate-400 border-b border-slate-800">
                  <tr>
                    <th className="p-3">STATE / REGION</th>
                    <th className="p-3">ACTIVE EVENTS</th>
                    <th className="p-3">AVERAGE FRP (MW)</th>
                    <th className="p-3">HIGH/CRITICAL INCIDENTS</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {stateSummary.map((st, idx) => (
                    <tr key={idx} className="hover:bg-slate-800/40">
                      <td className="p-3 font-bold text-white font-sans">{st.state}</td>
                      <td className="p-3 text-amber-400 font-bold">{st.event_count}</td>
                      <td className="p-3 text-slate-300">{formatFrp(st.avg_frp)}</td>
                      <td className="p-3 text-red-400 font-bold">{st.high_risk_count}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
          </>
          )}
        </main>
      </div>
    </div>
  );
}
