"use client";

import React, { useState, useEffect } from "react";
import Header from "@/components/layout/Header";
import Sidebar from "@/components/layout/Sidebar";
import { fetchApi } from "@/lib/api";
import { 
  BarChart3, PieChart, Activity, 
  TrendingUp, Layers, MapPin
} from "lucide-react";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, 
  ResponsiveContainer, Cell, PieChart as RePieChart, Pie
} from "recharts";

export default function AnalyticsPage() {
  const [classDist, setClassDist] = useState<any[]>([]);
  const [riskDist, setRiskDist] = useState<any[]>([]);
  const [stateSummary, setStateSummary] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadAnalytics = async () => {
      try {
        const [cData, rData, sData] = await Promise.all([
          fetchApi<any[]>("/analytics/class-distribution"),
          fetchApi<any[]>("/analytics/risk-distribution"),
          fetchApi<any[]>("/analytics/state-summary"),
        ]);
        setClassDist(cData);
        setRiskDist(rData);
        setStateSummary(sData);
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

  const COLORS = ["#f59e0b", "#f97316", "#10b981", "#3b82f6", "#a855f7", "#64748b"];

  return (
    <div className="min-h-screen bg-agni-navy flex flex-col selection:bg-amber-500 selection:text-slate-950">
      <Header />

      <div className="flex flex-1 overflow-hidden">
        <Sidebar />

        <main className="flex-1 overflow-y-auto p-6 space-y-6 max-w-6xl mx-auto">
          {/* Header */}
          <div className="border-b border-agni-border pb-4">
            <h1 className="text-xl sm:text-2xl font-extrabold text-white flex items-center gap-2.5">
              <BarChart3 className="w-6 h-6 text-amber-400" />
              National Thermal Analytics & Machine Learning Metrics
            </h1>
            <p className="text-xs text-slate-400 mt-1">
              Macro spatial distribution, classification breakdown, and risk trends derived across India.
            </p>
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
                      <td className="p-3 text-slate-300">{st.avg_frp.toFixed(1)} MW</td>
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
