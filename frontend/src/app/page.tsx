"use client";

import React from "react";
import Link from "next/link";
import { 
  Flame, ShieldAlert, Cpu, Activity, 
  Map, Database, ArrowRight, CheckCircle2, 
  Layers, Search, FileText, ChevronRight, Zap,
  Building2, Globe, ShieldCheck, Lock,
  BarChart3, Eye, Settings, Compass, Radio
} from "lucide-react";
import ObservationQuickExplorer from "@/components/common/ObservationQuickExplorer";
import SystemStatusBanner from "@/components/common/SystemStatusBanner";

export default function LandingPage() {
  const primaryStats = [
    {
      label: "Active Facilities",
      value: "35,570",
      subtext: "Authoritative geocoded industrial cadastre",
      badge: "OSM CADASTRE",
      badgeColor: "bg-cyan-500/20 text-cyan-300 border-cyan-500/40",
    },
    {
      label: "Power Stations",
      value: "502",
      subtext: "1,633 CEA power generation units",
      badge: "CEA NATIONAL",
      badgeColor: "bg-amber-500/20 text-amber-300 border-amber-500/40",
    },
    {
      label: "Operational Events",
      value: "88",
      subtext: "82 active, 6 verified ground incidents",
      badge: "DBSCAN CLUSTERS",
      badgeColor: "bg-emerald-500/20 text-emerald-300 border-emerald-500/40",
    },
    {
      label: "Total Historical Baseline",
      value: "6.45M",
      subtext: "Sealed immutable FIRMS records (2022–2025)",
      badge: "HISTORICAL",
      badgeColor: "bg-blue-500/20 text-blue-300 border-blue-500/40",
    },
  ];

  const pillars = [
    {
      step: "01",
      title: "DETECT",
      subtitle: "Near-Real-Time Thermal Observation",
      desc: "Direct ingestion of NASA FIRMS VIIRS (375m) and MODIS (1km) earth observation passes. Radiometric FRP thresholding, spatiotemporal DBSCAN clustering, and geographic boundary validation across all 36 Indian States & UTs.",
      icon: Flame,
      color: "from-amber-500/20 to-orange-500/10 border-amber-500/40 text-amber-400",
      bullets: [
        "15-minute ingestion pipeline cycle",
        "Point-in-polygon PostGIS indexing",
        "Dynamic sensor swath projection",
      ],
    },
    {
      step: "02",
      title: "UNDERSTAND",
      subtitle: "JARVIS Single-Master Reasoning & ML",
      desc: "Automated analytical orchestration through JARVIS Master Observer. 18-feature remote sensing XGBoost classifier with TreeExplainer SHAP attributions, historical recurrence baselines, and multi-criteria risk scoring.",
      icon: Cpu,
      color: "from-blue-500/20 to-cyan-500/10 border-blue-500/40 text-cyan-400",
      bullets: [
        "Single-Master deterministic reasoning",
        "SHAP feature contribution waterfalls",
        "Transparent 5-factor risk formula",
      ],
    },
    {
      step: "03",
      title: "PREVENT",
      subtitle: "Proactive Fire Prevention & Root Cause",
      desc: "Deterministic 13-hypothesis root-cause engine, longitudinal spatial persistence tracking, prioritized prevention recommendations, and Human-in-the-Loop review before controlled agency reporting.",
      icon: ShieldAlert,
      color: "from-emerald-500/20 to-teal-500/10 border-emerald-500/40 text-emerald-400",
      bullets: [
        "13 deterministic root-cause hypotheses",
        "Targeted agency prevention dossiers",
        "Immutable cryptographically signed audit",
      ],
    },
  ];

  const portals = [
    {
      title: "Analyst Workstation",
      badge: "INTELLIGENCE",
      badgeColor: "bg-blue-500/20 text-blue-300 border-blue-500/40",
      desc: "National GIS command center, live thermal hotspot streams, JARVIS investigation, and human-in-the-loop incident verification.",
      icon: Map,
      href: "/dashboard",
      cta: "Open Command Center",
    },
    {
      title: "Agency Response Portal",
      badge: "EMERGENCY & NDMA",
      badgeColor: "bg-red-500/20 text-red-300 border-red-500/40",
      desc: "Role-authorized alert triage, regional baselines, priority incident monitoring, and authorized regulatory report review.",
      icon: ShieldAlert,
      href: "/portal/agency",
      cta: "Launch Agency Portal",
    },
    {
      title: "Public Safety Portal",
      badge: "CITIZEN ADVISORY",
      badgeColor: "bg-emerald-500/20 text-emerald-300 border-emerald-500/40",
      desc: "Privacy-preserving regional advisories, generalized hazard boundaries, air quality context, and citizen safety guidance.",
      icon: Eye,
      href: "/portal/public",
      cta: "View Safety Advisories",
    },
    {
      title: "AGNI-SAT Digital Twin",
      badge: "SIMULATION",
      badgeColor: "bg-purple-500/20 text-purple-300 border-purple-500/40",
      desc: "Synthetic telemetry digital twin, 10-stage execution pipeline benchmark, orbital swath viewer, and 12 standard incident scenarios.",
      icon: Radio,
      href: "/dashboard/mission-control",
      cta: "Open Mission Control",
    },
  ];

  return (
    <div className="min-h-screen bg-agni-navy text-slate-100 flex flex-col selection:bg-amber-500 selection:text-slate-950 font-sans">
      {/* Top Header Navigation */}
      <nav className="h-16 border-b border-agni-border px-4 lg:px-10 flex items-center justify-between backdrop-blur-md bg-slate-950/90 sticky top-0 z-40">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-amber-500 via-orange-600 to-red-600 p-0.5 shadow-md flex items-center justify-center">
            <Flame className="w-5 h-5 text-white" />
          </div>
          <div className="flex items-center gap-2">
            <span className="font-extrabold text-lg tracking-wider text-white font-mono">AGNI-NETRA</span>
            <span className="hidden sm:inline-block text-[9px] uppercase font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
              NATIONAL GEOSPATIAL PLATFORM
            </span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="hidden md:flex items-center gap-2 text-xs text-slate-400 mr-2 font-mono">
            <span className="inline-block w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            <span>PostGIS 16 Connected</span>
          </div>
          <Link
            href="/login"
            className="text-xs font-semibold text-slate-300 hover:text-white px-3.5 py-1.5 rounded-lg hover:bg-slate-800 transition-colors"
          >
            Sign In
          </Link>
          <Link
            href="/dashboard"
            className="px-4 py-2 rounded-xl bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-600 hover:to-orange-700 text-slate-950 font-bold text-xs shadow-md flex items-center gap-1.5 transition-all hover:scale-105"
          >
            <span>Explore Platform</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </nav>

      {/* Hero Section: DETECT -> UNDERSTAND -> PREVENT */}
      <section className="relative px-4 lg:px-10 pt-16 pb-14 max-w-6xl mx-auto text-center space-y-6">
        <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-slate-900/90 border border-slate-700 text-slate-300 text-xs font-mono">
          <Zap className="w-3.5 h-3.5 text-amber-400" />
          <span>AI-Enabled Geospatial Thermal Intelligence & Fire Prevention Platform</span>
        </div>

        <h1 className="text-4xl sm:text-6xl font-black tracking-tight text-white leading-tight">
          AGNI<span className="text-amber-400 font-mono">-NETRA</span>
        </h1>

        {/* Narrative Core: DETECT -> UNDERSTAND -> PREVENT */}
        <div className="flex items-center justify-center gap-3 sm:gap-6 font-mono font-black text-sm sm:text-xl tracking-wider text-slate-300">
          <span className="text-amber-400">DETECT</span>
          <span className="text-slate-600">→</span>
          <span className="text-cyan-400">UNDERSTAND</span>
          <span className="text-slate-600">→</span>
          <span className="text-emerald-400">PREVENT</span>
        </div>

        <p className="max-w-2xl mx-auto text-sm sm:text-base text-slate-300 font-normal leading-relaxed">
          National satellite-derived thermal observation, deterministic root-cause intelligence, and proactive fire prevention for critical infrastructure, power stations, and industrial complexes.
        </p>

        {/* Primary CTAs */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-3.5 pt-2">
          <Link
            href="/dashboard"
            className="w-full sm:w-auto px-8 py-3.5 rounded-xl bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-600 hover:to-orange-700 text-slate-950 font-extrabold text-sm shadow-xl shadow-amber-500/20 flex items-center justify-center gap-2 transition-all hover:scale-105 cursor-pointer"
          >
            <Map className="w-4 h-4" />
            <span>Explore Platform</span>
          </Link>
          <Link
            href="/login"
            className="w-full sm:w-auto px-8 py-3.5 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-200 font-semibold text-sm transition-all flex items-center justify-center gap-2 cursor-pointer"
          >
            <ShieldCheck className="w-4 h-4 text-amber-400" />
            <span>Sign In to Portal</span>
          </Link>
        </div>

        {/* Operational Safety Invariant Notice */}
        <div className="mt-8 max-w-3xl mx-auto p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 text-left flex items-start gap-3 text-xs">
          <Lock className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
          <div className="space-y-0.5">
            <div className="font-bold text-amber-300 font-mono text-[11px] uppercase flex items-center gap-2">
              <span>Operational Safety Invariant (ENABLE_OPERATIONAL_DISPATCH_GATE = False)</span>
            </div>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              Human verification remains authoritative. Autonomous emergency dispatch and automated model activation are permanently blocked by statutory safety policy. Satellite detections and root-cause hypotheses serve purely as decision support.
            </p>
          </div>
        </div>
      </section>

      {/* 3 Pillars: DETECT, UNDERSTAND, PREVENT */}
      <section className="px-4 lg:px-10 py-12 bg-slate-950/90 border-y border-agni-border">
        <div className="max-w-6xl mx-auto space-y-8">
          <div className="text-center space-y-1.5">
            <span className="text-xs font-mono uppercase text-amber-400 tracking-wider font-semibold">
              End-to-End Operational Architecture
            </span>
            <h2 className="text-xl sm:text-2xl font-bold text-white">
              From Raw Satellite Radiometry to Verified Prevention
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            {pillars.map((pillar) => {
              const Icon = pillar.icon;
              return (
                <div
                  key={pillar.step}
                  className={`p-6 rounded-2xl bg-gradient-to-b ${pillar.color} border space-y-4 relative`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-2xl font-black opacity-40">{pillar.step}</span>
                    <div className="p-2.5 rounded-xl bg-slate-900/80 border border-slate-800">
                      <Icon className="w-5 h-5" />
                    </div>
                  </div>
                  <div>
                    <h3 className="font-mono font-black text-lg text-white">{pillar.title}</h3>
                    <p className="text-xs text-slate-300 font-medium">{pillar.subtitle}</p>
                  </div>
                  <p className="text-xs text-slate-400 leading-relaxed">
                    {pillar.desc}
                  </p>
                  <ul className="space-y-1.5 pt-2 border-t border-slate-800/80 text-[11px] text-slate-300 font-mono">
                    {pillar.bullets.map((b, i) => (
                      <li key={i} className="flex items-center gap-2">
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                        <span>{b}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Authoritative Inventory Ribbon */}
      <section className="px-4 lg:px-10 py-10 bg-slate-900/40 border-b border-agni-border">
        <div className="max-w-6xl mx-auto space-y-6">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div>
              <h2 className="text-sm font-bold uppercase tracking-wider text-white font-mono flex items-center gap-2">
                <Database className="w-4 h-4 text-amber-400" />
                Authoritative Infrastructure & Baseline Inventory
              </h2>
              <p className="text-xs text-slate-400">Canonical statistics across PostgreSQL 16 & PostGIS 3.4 spatial indices</p>
            </div>
            <span className="text-[10px] font-mono text-slate-400 hidden sm:inline">
              Republic of India
            </span>
          </div>

          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {primaryStats.map((stat, idx) => (
              <div key={idx} className="bg-slate-900/90 border border-slate-800 p-4 rounded-xl space-y-1.5">
                <span className={`text-[9px] font-mono uppercase px-2 py-0.5 rounded border font-bold ${stat.badgeColor}`}>
                  {stat.badge}
                </span>
                <div className="text-2xl font-black text-white font-mono tracking-tight pt-1">{stat.value}</div>
                <div className="text-xs font-semibold text-slate-200">{stat.label}</div>
                <div className="text-[10px] text-slate-400">{stat.subtext}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Observation Explorer Component */}
      <section className="px-4 lg:px-10 py-12 bg-slate-950/80 border-b border-agni-border">
        <div className="max-w-6xl mx-auto space-y-4">
          <div className="text-left space-y-1">
            <h2 className="text-base font-bold text-white font-mono uppercase tracking-wider flex items-center gap-2">
              <Compass className="w-4 h-4 text-amber-400" />
              Live Hotspot Explorer & Canonical Events
            </h2>
            <p className="text-xs text-slate-400">Directly inspect geocoded thermal observations, FRP values, and facility proximity</p>
          </div>
          <ObservationQuickExplorer />
        </div>
      </section>

      {/* System Governance Banner */}
      <section className="px-4 lg:px-10 py-6 bg-slate-900/30 border-b border-agni-border">
        <div className="max-w-6xl mx-auto">
          <SystemStatusBanner variant="compact" />
        </div>
      </section>

      {/* Differentiated Role Portals */}
      <section className="px-4 lg:px-10 py-12 bg-slate-950/90 border-b border-agni-border">
        <div className="max-w-6xl mx-auto space-y-6">
          <div className="text-center space-y-1">
            <span className="text-xs font-mono uppercase text-amber-400 tracking-wider font-semibold">
              Target User Portals
            </span>
            <h2 className="text-xl font-bold text-white">
              Role-Aware Decision Support Workstations
            </h2>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {portals.map((p) => {
              const Icon = p.icon;
              return (
                <div key={p.title} className="p-5 rounded-xl bg-slate-900/80 border border-slate-800 space-y-3 flex flex-col justify-between">
                  <div className="space-y-2.5">
                    <div className="flex items-center justify-between">
                      <div className="p-2 rounded-lg bg-slate-800 border border-slate-700">
                        <Icon className="w-4 h-4 text-amber-400" />
                      </div>
                      <span className={`text-[8px] font-mono font-bold px-1.5 py-0.5 rounded border uppercase ${p.badgeColor}`}>
                        {p.badge}
                      </span>
                    </div>
                    <h3 className="text-xs font-bold text-white">{p.title}</h3>
                    <p className="text-[11px] text-slate-400 leading-relaxed">{p.desc}</p>
                  </div>
                  <Link
                    href={p.href}
                    className="w-full mt-2 py-2 px-3 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-white font-semibold text-xs flex items-center justify-between transition-colors cursor-pointer"
                  >
                    <span>{p.cta}</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </Link>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-agni-border bg-slate-950 px-4 lg:px-10 py-8 text-xs text-slate-500 font-mono">
        <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="space-y-1 text-center sm:text-left">
            <div className="text-slate-300 font-bold">AGNI-NETRA — Geospatial Thermal Intelligence & Fire Prevention</div>
            <div className="text-[10px] text-slate-500">
              NASA FIRMS • OpenStreetMap • CEA • IBM • ISRO Bhuvan • CPCB / SPCB Alignment
            </div>
          </div>
          <div className="text-center sm:text-right text-[10px] space-y-1">
            <div className="text-amber-500/80 font-bold">ENABLE_OPERATIONAL_DISPATCH_GATE = False</div>
            <div>Correlation does not imply causation • Human verification authoritative</div>
          </div>
        </div>
      </footer>
    </div>
  );
}
