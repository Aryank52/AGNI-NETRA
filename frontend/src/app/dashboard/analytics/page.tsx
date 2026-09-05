"use client";

import React, { useState, useEffect } from "react";
import Header from "@/components/layout/Header";
import Sidebar from "@/components/layout/Sidebar";
import { fetchApi } from "@/lib/api";
import { formatFrp } from "@/lib/formatters";
import { 
  BarChart3, PieChart, Activity, 
  TrendingUp, Layers, MapPin, Calendar, Clock, Sparkles
} from "lucide-react";
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
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadAnalytics = async () => {
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
      } catch (err) {
        console.warn("Using sample chart data fallback:", err);
        setClassDist([
          { label: "Industrial Fire", count: 6, percentage: 40.0 },
          { label: "Gas Flare", count: 4, percentage: 26.7 },
          { label: "Forest Fire", count: 2, percentage: 13.3 },
          { label: "Agricultural Burning", count: 2, percentage: 13.3 },
          { label: "Mining Activity", count: 1, percentage: 6.7 },
        ]);
        setRiskDist([
          { level: "CRITICAL", count: 2, color: "#ef4444" },
          { level: "HIGH", count: 4, color: "#f97316" },
          { level: "MODERATE", count: 6, color: "#eab308" },
          { level: "LOW", count: 3, color: "#10b981" },
        ]);
        setStateSummary([
          { state: "Gujarat", event_count: 5, avg_frp: 145.0, high_risk_count: 2 },
          { state: "Madhya Pradesh", event_count: 3, avg_frp: 185.0, high_risk_count: 2 },
          { state: "Odisha", event_count: 3, avg_frp: 95.0, high_risk_count: 1 },
          { state: "Punjab", event_count: 2, avg_frp: 30.0, high_risk_count: 0 },
          { state: "Chhattisgarh", event_count: 2, avg_frp: 45.0, high_risk_count: 1 },
        ]);
      } finally {
        setLoading(false);
      }
    };
    loadAnalytics();
  }, []);

  useEffect(() => {
    setTimelineLoading(true);
    fetchApi<any>("/historical/timeline")
      .then((data) => {
        if (data?.timeline && Array.isArray(data.timeline)) {
          setTimeline(data.timeline);
        } else {
          setTimeline([
            { period: "2024-08", detection_count: 120, avg_frp: 48.5, max_frp: 180.2 },
            { period: "2024-09", detection_count: 185, avg_frp: 52.1, max_frp: 210.5 },
            { period: "2024-10", detection_count: 340, avg_frp: 61.4, max_frp: 320.0 },
            { period: "2024-11", detection_count: 512, avg_frp: 74.8, max_frp: 450.1 },
            { period: "2024-12", detection_count: 290, avg_frp: 55.3, max_frp: 240.6 },
            { period: "2025-01", detection_count: 198, avg_frp: 49.0, max_frp: 195.0 },
          ]);
        }
      })
      .catch(() => {
        setTimeline([
          { period: "2024-08", detection_count: 120, avg_frp: 48.5, max_frp: 180.2 },
          { period: "2024-09", detection_count: 185, avg_frp: 52.1, max_frp: 210.5 },
          { period: "2024-10", detection_count: 340, avg_frp: 61.4, max_frp: 320.0 },
          { period: "2024-11", detection_count: 512, avg_frp: 74.8, max_frp: 450.1 },
          { period: "2024-12", detection_count: 290, avg_frp: 55.3, max_frp: 240.6 },
          { period: "2025-01", detection_count: 198, avg_frp: 49.0, max_frp: 195.0 },
        ]);
      })
      .finally(() => setTimelineLoading(false));
  }, [timeHorizon]);

  const COLORS = ["#f59e0b", "#f97316", "#10b981", "#3b82f6", "#a855f7", "#64748b"];

  return (
    <div className="min-h-screen bg-agni-navy flex flex-col selection:bg-amber-500 selection:text-slate-950">
      <Header />

      <div className="flex flex-1 overflow-hidden">
        <Sidebar />

        <main className="flex-1 overflow-y-auto p-6 space-y-6 max-w-6xl mx-auto">
          {/* Header & Time Horizon Selector */}
          <div className="flex flex-wrap items-center justify-between gap-4 border-b border-agni-border pb-4">
            <div>
              <h1 className="text-xl sm:text-2xl font-extrabold text-white flex items-center gap-2.5">
                <BarChart3 className="w-6 h-6 text-amber-400" />
                National Thermal Analytics & Multi-Temporal Intelligence
              </h1>
              <p className="text-xs text-slate-400 mt-1">
                Multi-year satellite thermal observation trends, temporal horizons, and AI class distributions across India.
              </p>
            </div>

            {/* Time Horizon Pills */}
            <div className="flex items-center gap-1.5 bg-slate-900/90 p-1.5 rounded-xl border border-slate-800 text-xs">
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
          </div>

          {/* Multi-Year Timeline Chart */}
          <div className="p-5 rounded-2xl bg-agni-card border border-agni-border shadow-xl space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200 flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-cyan-400" />
                <span>Multi-Temporal Thermal Detections & Radiative Power Trend ({timeHorizon})</span>
              </h3>
              <span className="text-[10px] font-mono text-slate-400">
                NASA FIRMS VIIRS / MODIS Archive (8.22M Observations)
              </span>
            </div>

            <div className="h-64 w-full">
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
            </div>
          </div>

          {/* Charts Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Classification Distribution */}
            <div className="p-5 rounded-2xl bg-agni-card border border-agni-border shadow-xl space-y-4">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200 flex items-center gap-2">
                <PieChart className="w-4 h-4 text-amber-400" />
                AI Thermal Source Class Breakdown
              </h3>

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
            <div className="p-5 rounded-2xl bg-agni-card border border-agni-border shadow-xl space-y-4">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200 flex items-center gap-2">
                <Activity className="w-4 h-4 text-red-400" />
                AGNI-NETRA Risk Severity Matrix
              </h3>

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
        </main>
      </div>
    </div>
  );
}
