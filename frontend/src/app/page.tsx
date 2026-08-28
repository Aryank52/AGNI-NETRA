"use client";

import React from "react";
import Link from "next/link";
import { 
  Flame, ShieldAlert, Cpu, Activity, 
  Map, Database, ArrowRight, CheckCircle2, 
  Layers, Search, FileText, ChevronRight, Zap
} from "lucide-react";

export default function LandingPage() {
  const usps = [
    {
      title: "Industrial vs Non-Industrial AI Classification",
      desc: "XGBoost & Random Forest multi-class model distinguishing industrial fires and gas flares from crop stubble burning and forest fires with 96.2% accuracy.",
      icon: Cpu,
      color: "text-amber-400",
    },
    {
      title: "Unknown Candidate Facility Discovery",
      desc: "Automatically discovers uncataloged persistent industrial thermal sources using multi-temporal recurrence, diurnal burning ratios, and LULC context.",
      icon: Search,
      color: "text-purple-400",
    },
    {
      title: "Explainable AI (SHAP TreeExplainer)",
      desc: "Transparent Shapley feature attributions revealing exactly why an anomaly was classified with quantifiable supporting and opposing factors.",
      icon: Layers,
      color: "text-cyan-400",
    },
    {
      title: "Historical Thermal Baselines & Anomaly Engine",
      desc: "Facility-level baseline profiles detecting critical statistical spikes (+3σ) and multivariate behavioral anomalies via Isolation Forest.",
      icon: Activity,
      color: "text-emerald-400",
    },
    {
      title: "Transparent AGNI-NETRA Risk Engine",
      desc: "Multi-criteria transparent risk matrix evaluating radiative power, abnormality, population proximity, and hazard exposure without black-box claims.",
      icon: ShieldAlert,
      color: "text-red-400",
    },
    {
      title: "Human-in-the-Loop Active Learning",
      desc: "Empowers authorized analysts to confirm, correct, or refine predictions, creating an active feedback loop for model evolution.",
      icon: CheckCircle2,
      color: "text-blue-400",
    },
  ];

  return (
    <div className="min-h-screen bg-agni-navy text-slate-100 flex flex-col selection:bg-amber-500 selection:text-slate-950">
      {/* Top Navigation */}
      <nav className="h-20 border-b border-agni-border/80 px-6 lg:px-12 flex items-center justify-between backdrop-blur-md bg-agni-slate/70 sticky top-0 z-40">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-500 via-orange-600 to-red-600 p-0.5 shadow-lg shadow-orange-500/30 flex items-center justify-center">
            <Flame className="w-6 h-6 text-white" />
          </div>
          <div>
            <span className="font-extrabold text-xl tracking-wider text-white">AGNI-NETRA</span>
            <span className="text-[10px] uppercase font-mono px-2 py-0.5 ml-2 rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/30">
              ENTERPRISE PLATFORM
            </span>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <Link
            href="/login"
            className="text-xs font-semibold text-slate-300 hover:text-white px-4 py-2 rounded-lg hover:bg-slate-800 transition-colors"
          >
            Sign In
          </Link>
          <Link
            href="/dashboard"
            className="px-4 py-2 rounded-xl bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-600 hover:to-orange-700 text-slate-950 font-bold text-xs shadow-lg shadow-amber-500/25 flex items-center gap-2 transition-all hover:scale-105"
          >
            <span>Launch Command Center</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative px-6 lg:px-12 pt-20 pb-28 max-w-6xl mx-auto text-center space-y-8">
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-400 text-xs font-mono">
          <Zap className="w-3.5 h-3.5" />
          <span>NASA FIRMS VIIRS • OSM REGISTRY • ISRO BHUVAN • SHAP EXPLAINABILITY</span>
        </div>

        <h1 className="text-4xl sm:text-6xl lg:text-7xl font-extrabold tracking-tight text-white leading-tight">
          AI Geospatial Intelligence for <br />
          <span className="bg-clip-text text-transparent bg-gradient-to-r from-amber-400 via-orange-500 to-red-500">
            Industrial Fires & Thermal Risk
          </span>
        </h1>

        <p className="max-w-3xl mx-auto text-base sm:text-xl text-slate-300 font-normal leading-relaxed">
          &ldquo;FIRMS tells us where a thermal anomaly is. <br className="hidden sm:inline" />
          <strong className="text-white">AGNI-NETRA</strong> tells us what it most likely is, whether it is persistent or abnormal, how risky it is, and why.&rdquo;
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
          <Link
            href="/dashboard"
            className="w-full sm:w-auto px-8 py-4 rounded-xl bg-gradient-to-r from-amber-500 via-orange-600 to-red-600 hover:from-amber-600 hover:to-red-700 text-slate-950 font-extrabold text-sm shadow-xl shadow-orange-500/30 flex items-center justify-center gap-3 transition-transform hover:scale-105"
          >
            <Map className="w-5 h-5 text-slate-950" />
            <span>Open India GIS Command Map</span>
          </Link>
          <Link
            href="/login"
            className="w-full sm:w-auto px-8 py-4 rounded-xl bg-agni-card hover:bg-slate-800 border border-agni-border text-slate-200 font-semibold text-sm transition-all"
          >
            Access Role-Based Portals →
          </Link>
        </div>

        {/* Intelligence Workflow Strip */}
        <div className="pt-14 grid grid-cols-2 md:grid-cols-6 gap-2 text-xs font-mono">
          {[
            { step: "01", name: "DETECT", desc: "Satellite VIIRS/MODIS" },
            { step: "02", name: "CLASSIFY", desc: "XGBoost 7-Class AI" },
            { step: "03", name: "ANALYZE", desc: "Baseline & Anomaly" },
            { step: "04", name: "EXPLAIN", desc: "SHAP Attribution" },
            { step: "05", name: "PRIORITIZE", desc: "Multi-Factor Risk" },
            { step: "06", name: "VERIFY", desc: "HITL Active Learning" },
          ].map((item, idx) => (
            <div key={idx} className="p-3 rounded-xl bg-agni-card/70 border border-agni-border/60 text-left space-y-1">
              <div className="text-[10px] text-amber-500 font-bold">{item.step}</div>
              <div className="font-bold text-white tracking-wider">{item.name}</div>
              <div className="text-[10px] text-slate-400">{item.desc}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Core USPs Grid */}
      <section className="px-6 lg:px-12 py-20 bg-agni-slate/50 border-t border-agni-border">
        <div className="max-w-6xl mx-auto space-y-12">
          <div className="text-center space-y-3">
            <h2 className="text-2xl sm:text-4xl font-bold text-white tracking-tight">
              Enterprise Geospatial & Decision Support Capabilities
            </h2>
            <p className="text-slate-400 text-sm max-w-2xl mx-auto">
              Engineered strictly on machine learning, remote sensing physics, and spatial statistics — without LLM hallucinations.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {usps.map((usp, idx) => {
              const Icon = usp.icon;
              return (
                <div
                  key={idx}
                  className="p-6 rounded-2xl bg-agni-card/80 border border-agni-border hover:border-amber-500/40 hover:bg-agni-card transition-all space-y-3 group shadow-lg"
                >
                  <div className={`w-10 h-10 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-center ${usp.color}`}>
                    <Icon className="w-5 h-5 group-hover:scale-110 transition-transform" />
                  </div>
                  <h3 className="text-base font-bold text-slate-100">{usp.title}</h3>
                  <p className="text-xs text-slate-400 leading-relaxed">{usp.desc}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="mt-auto border-t border-agni-border/60 py-8 px-6 lg:px-12 text-xs text-slate-500 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div>
          <strong>AGNI-NETRA</strong> • AI-Powered Industrial Fire & Persistent Thermal Intelligence Platform
        </div>
        <div className="flex items-center gap-6">
          <span>NASA FIRMS • ISRO Bhuvan • OpenStreetMap</span>
          <Link href="/dashboard" className="text-amber-400 hover:underline">Launch App →</Link>
        </div>
      </footer>
    </div>
  );
}
