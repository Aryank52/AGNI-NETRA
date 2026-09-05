"use client";

import React from "react";
import Link from "next/link";
import { 
  Flame, ShieldAlert, Cpu, Activity, 
  Map, Database, ArrowRight, CheckCircle2, 
  Layers, Search, FileText, ChevronRight, Zap,
  Building2, GraduationCap, Globe, ShieldCheck, BarChart3
} from "lucide-react";

export default function LandingPage() {
  const telemetryStats = [
    { label: "Thermal Detections", value: "8,221,894", subtext: "6.45M Historical + 1.77M Live" },
    { label: "Industrial Facilities", value: "35,684", subtext: "OSM & Regulated Registries" },
    { label: "Administrative Units", value: "7,595", subtext: "All India Districts & Sub-Districts" },
    { label: "Power Stations", value: "1,633", subtext: "Thermal Generation Catalog" },
    { label: "Mining Leases", value: "414", subtext: "Active Open-Cast & Mineral Blocks" },
    { label: "Operational Safety", value: "0 False Dispatches", subtext: "HITL Safe Operational Gate" },
  ];

  const portals = [
    {
      title: "Mission Control Center",
      badge: "ANALYST & COMMAND",
      badgeColor: "bg-amber-500/20 text-amber-300 border-amber-500/40",
      desc: "Comprehensive 9-layer GIS mapping, live satellite detection triage, SHAP explainability waterfall, and HITL verification workbench.",
      icon: Map,
      href: "/dashboard",
      cta: "Launch Command Center",
      highlight: true,
    },
    {
      title: "Public Safety Portal",
      badge: "CITIZEN & MUNICIPAL",
      badgeColor: "bg-blue-500/20 text-blue-300 border-blue-500/40",
      desc: "Transparent public advisories, smoke dispersion exposure alerts, district-level safety ratings, and citizen incident reporting.",
      icon: Globe,
      href: "/portal/public",
      cta: "View Public Advisories",
      highlight: false,
    },
    {
      title: "Industry Compliance Portal",
      badge: "PLANT OPERATORS",
      badgeColor: "bg-emerald-500/20 text-emerald-300 border-emerald-500/40",
      desc: "Automated flare schedule logging, maintenance exemption reporting, CPCB emission compliance self-auditing, and facility verification.",
      icon: Building2,
      href: "/portal/industry",
      cta: "Access Industry Portal",
      highlight: false,
    },
    {
      title: "Research & Academic Portal",
      badge: "SCIENTIFIC OPEN DATA",
      badgeColor: "bg-purple-500/20 text-purple-300 border-purple-500/40",
      desc: "Temporal baseline data exports, diurnal cycle curves, multi-sensor cross-calibration benchmarks, and reproducible notebooks.",
      icon: GraduationCap,
      href: "/portal/research",
      cta: "Explore Research Data",
      highlight: false,
    },
  ];

  const usps = [
    {
      title: "Calibrated 7-Class AI Segregation",
      desc: "XGBoost classifier distinguishing industrial fires and gas flares from crop stubble burning and forest fires. 97.2% Tier 1 selective accuracy, 94.3% spatial validation, and 69.9% out-of-sample temporal holdout.",
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
      title: "Transparent Multi-Factor Risk Engine",
      desc: "Standardized risk formula: 0.30×Intensity + 0.25×Abnormality + 0.20×Exposure + 0.15×Persistence + 0.10×Context without black-box scores.",
      icon: ShieldAlert,
      color: "text-red-400",
    },
    {
      title: "Human-in-the-Loop Active Learning",
      desc: "Tier-based routing (Tier 1 automated alert, Tier 2 analyst review, Tier 3 queue) ensuring reliable triage and zero unverified dispatches.",
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
              NATIONAL GEOSPATIAL INTELLIGENCE
            </span>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="hidden md:flex items-center gap-2 text-xs text-slate-400 mr-2">
            <span className="inline-block w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            <span className="font-mono">Live PostGIS Ingestion Active</span>
          </div>
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
            <span>Command Center</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative px-6 lg:px-12 pt-16 pb-20 max-w-6xl mx-auto text-center space-y-8">
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-400 text-xs font-mono">
          <Zap className="w-3.5 h-3.5" />
          <span>NASA FIRMS VIIRS/MODIS • POSTGIS 8.22M+ RECORDS • SHAP EXPLAINABILITY • 7-CLASS ML</span>
        </div>

        <h1 className="text-4xl sm:text-6xl lg:text-7xl font-extrabold tracking-tight text-white leading-tight">
          AI Geospatial Intelligence for <br />
          <span className="bg-clip-text text-transparent bg-gradient-to-r from-amber-400 via-orange-500 to-red-500">
            Industrial Fires & Thermal Anomalies
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
            <span>Open National GIS Command Map</span>
          </Link>
          <Link
            href="#portals"
            className="w-full sm:w-auto px-8 py-4 rounded-xl bg-agni-card hover:bg-slate-800 border border-agni-border text-slate-200 font-semibold text-sm transition-all flex items-center justify-center gap-2"
          >
            <span>Explore Role Portals</span>
            <ChevronRight className="w-4 h-4 text-slate-400" />
          </Link>
        </div>

        {/* Intelligence Workflow Strip */}
        <div className="pt-10 grid grid-cols-2 md:grid-cols-6 gap-2 text-xs font-mono">
          {[
            { step: "01", name: "DETECT", desc: "VIIRS/MODIS 375m" },
            { step: "02", name: "CLASSIFY", desc: "XGBoost 7-Class AI" },
            { step: "03", name: "ANALYZE", desc: "Baseline & +3σ Spikes" },
            { step: "04", name: "EXPLAIN", desc: "SHAP TreeExplainer" },
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

      {/* Live National Telemetry Ribbon */}
      <section className="border-y border-agni-border bg-slate-900/80 backdrop-blur-md px-6 lg:px-12 py-8">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-6">
            <span className="text-[11px] font-mono uppercase text-amber-400 tracking-widest font-semibold">
              Live National Spatial Telemetry (PostgreSQL 16 / PostGIS 3.4)
            </span>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            {telemetryStats.map((stat, idx) => (
              <div key={idx} className="bg-agni-card/60 border border-agni-border/60 p-4 rounded-xl text-center space-y-1">
                <div className="text-2xl font-black text-white font-mono tracking-tight">{stat.value}</div>
                <div className="text-xs font-semibold text-slate-300">{stat.label}</div>
                <div className="text-[10px] text-slate-500 font-mono">{stat.subtext}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Dedicated Role Portals Section */}
      <section id="portals" className="px-6 lg:px-12 py-20 bg-agni-slate/30">
        <div className="max-w-6xl mx-auto space-y-12">
          <div className="text-center space-y-3">
            <h2 className="text-2xl sm:text-4xl font-bold text-white tracking-tight">
              Multi-Stakeholder Operational Portals
            </h2>
            <p className="text-slate-400 text-sm max-w-2xl mx-auto">
              Dedicated interfaces tailored for operational analysts, plant managers, research scientists, and the public.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {portals.map((portal, idx) => {
              const Icon = portal.icon;
              return (
                <div
                  key={idx}
                  className={`p-6 rounded-2xl border transition-all flex flex-col justify-between space-y-4 ${
                    portal.highlight
                      ? "bg-gradient-to-br from-slate-900 to-amber-950/30 border-amber-500/50 shadow-lg shadow-amber-500/10"
                      : "bg-agni-card/80 border-agni-border hover:border-slate-600"
                  }`}
                >
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="w-10 h-10 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-center text-amber-400">
                        <Icon className="w-5 h-5" />
                      </div>
                      <span className={`text-[10px] font-mono px-2.5 py-1 rounded-full border ${portal.badgeColor}`}>
                        {portal.badge}
                      </span>
                    </div>
                    <h3 className="text-lg font-bold text-white">{portal.title}</h3>
                    <p className="text-xs text-slate-300 leading-relaxed">{portal.desc}</p>
                  </div>
                  <Link
                    href={portal.href}
                    className={`mt-4 px-4 py-2.5 rounded-xl font-bold text-xs flex items-center justify-between transition-colors ${
                      portal.highlight
                        ? "bg-amber-500 hover:bg-amber-600 text-slate-950"
                        : "bg-slate-800 hover:bg-slate-700 text-slate-200"
                    }`}
                  >
                    <span>{portal.cta}</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </Link>
                </div>
              );
            })}
          </div>
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

      {/* Institutional Framework Alignment */}
      <section className="px-6 lg:px-12 py-12 bg-slate-950/80 border-t border-agni-border">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-6 text-center md:text-left">
          <div className="space-y-1">
            <div className="text-xs font-mono text-amber-400 uppercase tracking-wider font-semibold">
              Standards & Regulatory Framework Alignment
            </div>
            <p className="text-xs text-slate-400 max-w-xl">
              Compatible with MoEFCC Environmental Impact Assessment norms, CPCB flare monitoring protocols, ISRO Bhuvan OGC standards, and NDMA disaster response guidelines.
            </p>
          </div>
          <div className="flex flex-wrap items-center justify-center gap-3 text-[11px] font-mono text-slate-400">
            <span className="px-3 py-1 rounded-lg bg-slate-900 border border-slate-800">MoEFCC EIA</span>
            <span className="px-3 py-1 rounded-lg bg-slate-900 border border-slate-800">CPCB Flaring</span>
            <span className="px-3 py-1 rounded-lg bg-slate-900 border border-slate-800">ISRO Bhuvan OGC</span>
            <span className="px-3 py-1 rounded-lg bg-slate-900 border border-slate-800">NDMA Standard</span>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="mt-auto border-t border-agni-border/60 py-8 px-6 lg:px-12 text-xs text-slate-500 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="space-y-1 text-center sm:text-left">
          <div>
            <strong>AGNI-NETRA</strong> • AI-Powered Industrial Fire & Persistent Thermal Intelligence Platform
          </div>
          <div className="text-[10px] text-slate-600">
            Statutory Notice: Autonomous dispatch is gated under human-in-the-loop validation (ENABLE_OPERATIONAL_DISPATCH_GATE = False).
          </div>
        </div>
        <div className="flex items-center gap-6">
          <span>NASA FIRMS • ISRO Bhuvan • OpenStreetMap</span>
          <Link href="/dashboard" className="text-amber-400 hover:underline">Launch App →</Link>
        </div>
      </footer>
    </div>
  );
}
