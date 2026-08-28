"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import Header from "@/components/layout/Header";
import Sidebar from "@/components/layout/Sidebar";
import { fetchApi } from "@/lib/api";
import { 
  Database, RefreshCw, CheckCircle2, AlertTriangle, 
  XCircle, Clock, ShieldCheck, Play, ArrowLeft,
  Activity, Layers, Sliders, Globe, Radio
} from "lucide-react";

interface DataSourceStatus {
  source: string;
  status: "HEALTHY" | "DEGRADED" | "NOT_CONFIGURED" | "UNAVAILABLE" | string;
  configured: boolean;
  message: string;
  latency_ms: number;
}

export default function DataSourcesControlCenterPage() {
  const [sources, setSources] = useState<DataSourceStatus[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [syncResult, setSyncResult] = useState<string | null>(null);

  const loadStatus = async () => {
    setLoading(true);
    try {
      const res = await fetchApi<any>("/ingestion/sources/status");
      setSources(res.sources || []);
    } catch (err) {
      console.warn("Failed to load data sources status:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadStatus();
  }, []);

  const triggerSyncAll = async () => {
    setSyncing(true);
    setSyncResult(null);
    try {
      const res = await fetchApi<any>("/ingestion/trigger/sync-all", { method: "POST" });
      setSyncResult("Multi-source synchronization completed successfully!");
      await loadStatus();
    } catch (err) {
      setSyncResult("Sync failed: " + err);
    } finally {
      setSyncing(false);
    }
  };

  return (
    <div className="min-h-screen bg-agni-navy flex flex-col selection:bg-amber-500 selection:text-slate-950">
      <Header />

      <div className="flex flex-1 overflow-hidden">
        <Sidebar />

        <main className="flex-1 overflow-y-auto p-6 space-y-6 max-w-7xl mx-auto">
          {/* Header */}
          <div className="flex flex-wrap items-center justify-between gap-4 border-b border-agni-border pb-4">
            <div>
              <div className="flex items-center gap-2">
                <Link href="/admin" className="text-xs text-slate-400 hover:text-white flex items-center gap-1">
                  <ArrowLeft className="w-3.5 h-3.5" />
                  <span>Back to Admin</span>
                </Link>
                <span className="text-slate-600">/</span>
                <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30 font-bold">
                  CONTROL CENTER
                </span>
              </div>
              <h1 className="text-xl sm:text-2xl font-extrabold text-white flex items-center gap-2.5 mt-1">
                <Database className="w-6 h-6 text-amber-400" />
                Data Ingestion Control Center & Adapter Health
              </h1>
              <p className="text-xs text-slate-400 mt-1">
                Live monitoring for NASA FIRMS, OpenStreetMap, CEA Power Plants, ISRO Bhuvan, Copernicus Sentinel-2, USGS Landsat, and ISRO MOSDAC.
              </p>
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={loadStatus}
                className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700"
                title="Refresh Status"
              >
                <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin text-amber-400" : ""}`} />
              </button>

              <button
                onClick={triggerSyncAll}
                disabled={syncing}
                className="px-4 py-2 rounded-xl bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-600 hover:to-orange-700 text-slate-950 font-bold text-xs shadow-lg shadow-amber-500/20 flex items-center gap-2 transition-all"
              >
                <Play className={`w-3.5 h-3.5 ${syncing ? "animate-spin" : ""}`} />
                <span>{syncing ? "Synchronizing..." : "Trigger Multi-Source Sync"}</span>
              </button>
            </div>
          </div>

          {syncResult && (
            <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs font-semibold flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 shrink-0" />
              <span>{syncResult}</span>
            </div>
          )}

          {/* Sources Status Cards Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {sources.map((src) => {
              const isHealthy = src.status === "HEALTHY";
              const isDegraded = src.status === "DEGRADED";
              const isNotConf = src.status === "NOT_CONFIGURED";

              return (
                <div
                  key={src.source}
                  className={`p-5 rounded-2xl bg-agni-card border transition-all space-y-3.5 shadow-xl ${
                    isHealthy
                      ? "border-emerald-500/30 hover:border-emerald-500/60"
                      : isDegraded
                      ? "border-amber-500/30 hover:border-amber-500/60"
                      : "border-slate-800 hover:border-slate-700"
                  }`}
                >
                  <div className="flex items-center justify-between border-b border-slate-800 pb-2.5">
                    <span className="font-mono text-xs font-bold text-white tracking-wide">
                      {src.source}
                    </span>
                    <span className={`text-[9px] uppercase font-mono px-2 py-0.5 rounded font-bold ${
                      isHealthy
                        ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                        : isDegraded
                        ? "bg-amber-500/20 text-amber-300 border border-amber-500/30"
                        : isNotConf
                        ? "bg-slate-800 text-slate-400 border border-slate-700"
                        : "bg-red-500/20 text-red-300 border border-red-500/30"
                    }`}>
                      {src.status}
                    </span>
                  </div>

                  <p className="text-xs text-slate-300 leading-relaxed min-h-[38px]">
                    {src.message}
                  </p>

                  <div className="p-3 rounded-xl bg-slate-900/90 border border-slate-800 grid grid-cols-2 gap-2 text-xs font-mono">
                    <div>
                      <div className="text-[10px] text-slate-500">AUTHENTICATION</div>
                      <div className={`font-bold mt-0.5 ${src.configured ? "text-emerald-400" : "text-slate-400"}`}>
                        {src.configured ? "CONFIGURED" : "OPTIONAL / DEMO"}
                      </div>
                    </div>
                    <div>
                      <div className="text-[10px] text-slate-500">API LATENCY</div>
                      <div className="font-bold text-white mt-0.5">
                        {src.latency_ms > 0 ? `${src.latency_ms} ms` : "Local / Offline"}
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </main>
      </div>
    </div>
  );
}
