"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import Header from "@/components/layout/Header";
import Sidebar from "@/components/layout/Sidebar";
import { fetchApi } from "@/lib/api";
import { 
  Database, ArrowLeft, RefreshCw, CheckCircle2, 
  Layers, ShieldAlert, Sliders, Filter, Sparkles
} from "lucide-react";

interface DatasetRecord {
  id: string;
  name: string;
  version: string;
  dataset_type: "REAL" | "WEAKLY_LABELED" | "HUMAN_VERIFIED" | "SYNTHETIC" | "DEMO" | string;
  source: string;
  record_count: number;
  verified_count: number;
  class_distribution: Record<string, number>;
  training_eligible: boolean;
  manifest_path?: string;
  created_at: string;
  updated_at: string;
}

export default function DatasetControlCenterPage() {
  const [datasets, setDatasets] = useState<DatasetRecord[]>([]);
  const [loading, setLoading] = useState(true);

  const loadDatasets = async () => {
    setLoading(true);
    try {
      const data = await fetchApi<DatasetRecord[]>("/admin/datasets");
      setDatasets(data || []);
    } catch (err) {
      console.warn("Failed to load datasets:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDatasets();
  }, []);

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
                <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-purple-500/20 text-purple-300 border border-purple-500/30 font-bold">
                  DATA GOVERNANCE
                </span>
              </div>
              <h1 className="text-xl sm:text-2xl font-extrabold text-white flex items-center gap-2.5 mt-1">
                <Database className="w-6 h-6 text-purple-400" />
                Dataset Control Center & Label Provenance
              </h1>
              <p className="text-xs text-slate-400 mt-1">
                Manage partitioned training datasets with strict isolation across REAL, HUMAN_VERIFIED, and SYNTHETIC data.
              </p>
            </div>

            <button
              onClick={loadDatasets}
              className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700"
              title="Refresh Datasets"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin text-amber-400" : ""}`} />
            </button>
          </div>

          {/* Dataset Cards Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
            {datasets.map((d) => {
              const isReal = d.dataset_type === "REAL" || d.dataset_type === "HUMAN_VERIFIED";
              const isSynthetic = d.dataset_type === "SYNTHETIC";

              return (
                <div
                  key={d.id}
                  className={`p-5 rounded-2xl bg-agni-card border transition-all space-y-4 shadow-xl ${
                    isReal
                      ? "border-purple-500/40 bg-gradient-to-br from-agni-card to-purple-950/20"
                      : "border-slate-800"
                  }`}
                >
                  <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="font-extrabold text-base text-white">{d.name}</h3>
                      </div>
                      <div className="text-[11px] font-mono text-slate-400 mt-0.5">
                        Version: <strong className="text-amber-400">{d.version}</strong> • Source: <span className="text-cyan-400">{d.source}</span>
                      </div>
                    </div>

                    <span className={`text-[10px] uppercase font-mono px-2.5 py-1 rounded-lg font-bold border ${
                      isReal
                        ? "bg-purple-500/20 text-purple-300 border-purple-500/30"
                        : isSynthetic
                        ? "bg-amber-500/20 text-amber-300 border-amber-500/30"
                        : "bg-slate-800 text-slate-400 border-slate-700"
                    }`}>
                      {d.dataset_type}
                    </span>
                  </div>

                  <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 grid grid-cols-3 gap-3 text-xs font-mono text-center">
                    <div>
                      <div className="text-[10px] text-slate-500">TOTAL SAMPLES</div>
                      <div className="text-white font-bold mt-0.5 text-sm">{d.record_count}</div>
                    </div>
                    <div>
                      <div className="text-[10px] text-slate-500">HUMAN VERIFIED</div>
                      <div className="text-emerald-400 font-bold mt-0.5 text-sm">{d.verified_count}</div>
                    </div>
                    <div>
                      <div className="text-[10px] text-slate-500">TRAINING STATUS</div>
                      <div className={`font-bold mt-0.5 text-sm ${d.training_eligible ? "text-cyan-400" : "text-slate-500"}`}>
                        {d.training_eligible ? "ELIGIBLE" : "LOCKED"}
                      </div>
                    </div>
                  </div>

                  {/* Class Distribution Badges */}
                  <div>
                    <div className="text-[10px] font-mono text-slate-500 mb-1.5 uppercase font-bold">Class Distribution</div>
                    <div className="flex flex-wrap gap-1.5">
                      {Object.entries(d.class_distribution || {}).map(([clsName, count]) => (
                        <span key={clsName} className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-850 border border-slate-700 text-slate-300">
                          {clsName}: <strong className="text-amber-400">{count}</strong>
                        </span>
                      ))}
                    </div>
                  </div>

                  <div className="pt-2 border-t border-slate-800 flex items-center justify-between text-[10px] text-slate-500 font-mono">
                    <span>Registered: {new Date(d.created_at).toLocaleDateString()}</span>
                    <span className="text-emerald-400 flex items-center gap-1">
                      <CheckCircle2 className="w-3 h-3" /> Strict Provenance Locked
                    </span>
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
