"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { 
  Flame, ShieldAlert, Cpu, Activity, 
  Map, Database, ArrowRight, CheckCircle2, 
  Layers, Lock, Globe, ShieldCheck,
  Radio, HardDrive, Server, FileCheck,
  ChevronRight, Zap, Wind, Users, BarChart3,
  ExternalLink
} from "lucide-react";
import AgniNetraLogo from "@/components/common/AgniNetraLogo";
import ObservationQuickExplorer from "@/components/common/ObservationQuickExplorer";
import { fetchApi } from "@/lib/api";

export default function LandingPage() {
  const [dbHealth, setDbHealth] = useState<{ status?: string; database?: string; engine?: string; spatial?: string; postgis_version?: string } | null>(null);
  const [dbLoading, setDbLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;
    fetchApi<{ status?: string; database?: string; engine?: string; spatial?: string; postgis_version?: string }>("/health/db")
      .then((data) => {
        if (isMounted) {
          setDbHealth(data);
          setDbLoading(false);
        }
      })
      .catch(() => {
        if (isMounted) {
          setDbHealth(null);
          setDbLoading(false);
        }
      });
    return () => {
      isMounted = false;
    };
  }, []);

  const primaryStats = [
    {
      metric: "375m",
      title: "Detection Precision",
      subtext: "VIIRS I-Band sub-pixel spatial resolution",
      badge: "NASA FIRMS",
      badgeColor: "bg-emerald-500/20 text-emerald-300 border-emerald-500/40",
    },
    {
      metric: "15 min",
      title: "Telemetry Ingestion",
      subtext: "Automated near-real-time orbit sweep cycles",
      badge: "NEAR-REAL-TIME",
      badgeColor: "bg-cyan-500/20 text-cyan-300 border-cyan-500/40",
    },
    {
      metric: "35,570+",
      title: "Industrial Cadastre",
      subtext: "Authoritative geocoded industrial facilities",
      badge: "OSM CADASTRE",
      badgeColor: "bg-amber-500/20 text-amber-300 border-amber-500/40",
    },
    {
      metric: "6.45M+",
      title: "Baseline Records",
      subtext: "Immutable historical telemetry archive (2022–2025)",
      badge: "HISTORICAL ARCHIVE",
      badgeColor: "bg-blue-500/20 text-blue-300 border-blue-500/40",
    },
  ];

  const pipelineSteps = [
    {
      step: "01",
      title: "DETECT",
      subtitle: "Spaceborne Observation & Radiometry",
      desc: "Continuous ingestion of NASA FIRMS VIIRS (375m) and MODIS (1km) earth observation passes. Radiometric Fire Radiative Power (FRP) thresholding, spatiotemporal DBSCAN clustering, and PostGIS boundary validation across all 36 Indian States & UTs.",
      icon: Flame,
      color: "from-amber-500/20 to-orange-500/10 border-amber-500/40 text-amber-400",
      bullets: [
        "15-minute automated orbital sweep cycle",
        "Sub-pixel radiometric thermal anomaly filtering",
        "Spatial indexing against 36 Indian States & UTs",
      ],
    },
    {
      step: "02",
      title: "UNDERSTAND",
      subtitle: "Deterministic Reasoning & Explainable ML",
      desc: "Deterministic analytical orchestration through JARVIS Master Observer. 18-feature remote sensing XGBoost classifier with TreeExplainer SHAP local attributions, historical baseline deviations (Z-score surge over 4-year seasonal cycles), and 5-factor risk scoring.",
      icon: Cpu,
      color: "from-blue-500/20 to-cyan-500/10 border-blue-500/40 text-cyan-400",
      bullets: [
        "Single-Master deterministic reasoning engine",
        "SHAP feature contribution waterfalls",
        "Transparent 5-factor risk formula",
      ],
    },
    {
      step: "03",
      title: "PREVENT",
      subtitle: "Proactive Prevention & Root Cause Analysis",
      desc: "Deterministic 13-hypothesis root-cause evaluation engine, longitudinal spatial persistence tracking, prioritized prevention recommendations, and Human-in-the-Loop review before controlled agency reporting.",
      icon: ShieldAlert,
      color: "from-emerald-500/20 to-teal-500/10 border-emerald-500/40 text-emerald-400",
      bullets: [
        "13 deterministic root-cause hypotheses",
        "Targeted agency prevention dossiers",
        "Cryptographically audited record trails",
      ],
    },
  ];

  const capabilities = [
    {
      title: "Continuous Satellite Telemetry",
      desc: "Automated orbit polling across VIIRS and MODIS instruments with sub-pixel Fire Radiative Power calculations.",
      icon: Radio,
      badge: "SATELLITE",
    },
    {
      title: "Industrial Cadastre Matching",
      desc: "Spatial fusion with 35,570+ geocoded industrial complexes and 502 Central Electricity Authority (CEA) power stations.",
      icon: Database,
      badge: "SPATIAL FUSION",
    },
    {
      title: "Air Quality & Smoke Modeling",
      desc: "Downwind smoke dispersal projections and atmospheric particulate tracking for surrounding civilian zones.",
      icon: Wind,
      badge: "DISPERSION",
    },
    {
      title: "Deterministic Root Cause Engine",
      desc: "13-hypothesis automated causal inference testing flaring, biomass burning, and industrial thermal deviations.",
      icon: Cpu,
      badge: "JARVIS ML",
    },
    {
      title: "Emergency Response Coordination",
      desc: "Structured triage consoles and incident verification workflows for disaster management authorities.",
      icon: ShieldCheck,
      badge: "DISPATCH READY",
    },
    {
      title: "Public Safety & Advisory System",
      desc: "Privacy-preserving public domain advisories, regional safety maps, and citizen protective guidance.",
      icon: Globe,
      badge: "PUBLIC ADVISORY",
    },
  ];

  const portals = [
    {
      title: "ANALYST PORTAL",
      badge: "INTELLIGENCE WORKSTATION",
      badgeColor: "bg-cyan-500/20 text-cyan-300 border-cyan-500/40",
      desc: "Full geospatial intelligence workstation with live thermal streams, JARVIS reasoning console, and satellite inspection.",
      icon: Map,
      href: "/login?redirect=%2Fdashboard",
      cta: "Access Analyst Portal",
      publicAccess: false,
    },
    {
      title: "AGENCY PORTAL",
      badge: "EMERGENCY RESPONSE",
      badgeColor: "bg-red-500/20 text-red-300 border-red-500/40",
      desc: "Emergency response coordination, incident verification, dispatch tracking, and regulatory reporting.",
      icon: ShieldAlert,
      href: "/login?redirect=%2Fportal%2Fagency",
      cta: "Access Agency Portal",
      publicAccess: false,
    },
    {
      title: "PUBLIC SAFETY PORTAL",
      badge: "CITIZEN ADVISORY",
      badgeColor: "bg-emerald-500/20 text-emerald-300 border-emerald-500/40",
      desc: "Citizen advisory, regional hazard maps, air quality context, and protective safety guidance.",
      icon: Globe,
      href: "/portal/public",
      cta: "View Public Advisories",
      publicAccess: true,
    },
  ];

  const techStack = [
    {
      title: "NASA FIRMS Telemetry",
      desc: "Direct integration with NASA Earthdata for VIIRS 375m and MODIS 1km calibrated thermal anomalies.",
      icon: Radio,
    },
    {
      title: "PostGIS 3.4 Spatial Database",
      desc: "Enterprise spatial indexing (GiST) and high-speed ST_DWithin clustering across 35k+ cadastral records.",
      icon: Database,
    },
    {
      title: "Celery Distributed Pipeline",
      desc: "Asynchronous task workers for high-frequency telemetry ingestion and spatial geometry extraction.",
      icon: Server,
    },
    {
      title: "Sovereign Deployment Ready",
      desc: "Engineered for secure government cloud deployments (NIC, ISRO Bhuvan) with complete air-gap readiness.",
      icon: ShieldCheck,
    },
    {
      title: "Backblaze B2 Evidence Storage",
      desc: "Zero-egress immutable object storage for satellite imagery tiles and cryptographic audit evidence.",
      icon: HardDrive,
    },
    {
      title: "Statutory Policy Governance",
      desc: "Human-in-the-loop validation enforcement with cryptographically sealed immutable audit logs.",
      icon: FileCheck,
    },
  ];

  return (
    <div className="min-h-screen bg-agni-navy text-slate-100 flex flex-col selection:bg-amber-500 selection:text-slate-950 font-sans">
      {/* 1. TOP NAVBAR */}
      <nav className="h-16 border-b border-agni-border px-4 lg:px-10 flex items-center justify-between backdrop-blur-md bg-slate-950/90 sticky top-0 z-40">
        <div className="flex items-center gap-8">
          <Link href="/" className="inline-block transition-transform hover:scale-105">
            <AgniNetraLogo size={36} subtext="NATIONAL GEOSPATIAL INTELLIGENCE" />
          </Link>

          <div className="hidden lg:flex items-center gap-6 text-xs font-mono text-slate-400">
            <a href="#pipeline" className="hover:text-amber-400 transition-colors">Pipeline</a>
            <a href="#capabilities" className="hover:text-amber-400 transition-colors">Capabilities</a>
            <a href="#demo" className="hover:text-amber-400 transition-colors">Interactive Demo</a>
            <a href="#portals" className="hover:text-amber-400 transition-colors">Portals</a>
            <a href="#trust" className="hover:text-amber-400 transition-colors">Trust & Safety</a>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* Live Telemetry Indicator */}
          <div className="hidden md:flex items-center gap-2 text-xs text-slate-400 mr-2 font-mono">
            <span className="inline-block w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            <span className="text-[11px] tracking-wide text-slate-300">
              TELEMETRY ACTIVE — 15 MIN SWEEP
            </span>
          </div>

          <Link
            href="/login"
            className="text-xs font-semibold text-slate-300 hover:text-white px-3.5 py-1.5 rounded-lg hover:bg-slate-800 transition-colors font-mono"
          >
            Sign In
          </Link>
          <Link
            href="/login"
            className="px-4 py-2 rounded-xl bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-600 hover:to-orange-700 text-slate-950 font-extrabold text-xs shadow-md shadow-amber-500/20 flex items-center gap-1.5 transition-all hover:scale-105 font-mono"
          >
            <span>Access Portal</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </nav>

      {/* 2. HERO SECTION */}
      <section className="relative px-4 lg:px-10 pt-16 pb-14 max-w-6xl mx-auto text-center space-y-6">
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-slate-900/90 border border-slate-700 text-slate-300 text-xs font-mono">
          <Zap className="w-3.5 h-3.5 text-amber-400" />
          <span>SPACEBORNE THERMAL SURVEILLANCE & EARLY RISK INTELLIGENCE</span>
        </div>

        <h1 className="text-4xl sm:text-6xl font-black tracking-tight text-white leading-tight">
          Real-Time Thermal Intelligence for <br className="hidden sm:inline" />
          <span className="bg-gradient-to-r from-amber-400 via-orange-500 to-amber-200 bg-clip-text text-transparent">
            Industrial & Wildfire Defense
          </span>
        </h1>

        <p className="max-w-3xl mx-auto text-sm sm:text-base text-slate-300 font-normal leading-relaxed">
          Continuous satellite radiometry, deterministic root-cause reasoning, and operational risk intelligence for industrial complexes, critical infrastructure, and emergency response across India.
        </p>

        {/* 3-Phase Narrative Pill */}
        <div className="inline-flex items-center justify-center gap-2 sm:gap-4 px-5 py-2.5 rounded-2xl bg-slate-900/80 border border-slate-800 font-mono font-bold text-xs sm:text-sm tracking-wider">
          <span className="text-amber-400">DETECT</span>
          <span className="text-slate-600">→</span>
          <span className="text-cyan-400">UNDERSTAND</span>
          <span className="text-slate-600">→</span>
          <span className="text-emerald-400">PREVENT</span>
        </div>

        {/* Primary CTA Row */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-3.5 pt-2">
          <Link
            href="/login"
            className="w-full sm:w-auto px-8 py-3.5 rounded-xl bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-600 hover:to-orange-700 text-slate-950 font-extrabold text-xs tracking-wider font-mono shadow-xl shadow-amber-500/20 flex items-center justify-center gap-2 transition-all hover:scale-105 cursor-pointer"
          >
            <Lock className="w-4 h-4" />
            <span>ACCESS PLATFORM</span>
          </Link>
          <Link
            href="/portal/public"
            className="w-full sm:w-auto px-8 py-3.5 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-200 font-semibold text-xs tracking-wider font-mono transition-all flex items-center justify-center gap-2 cursor-pointer"
          >
            <Globe className="w-4 h-4 text-emerald-400" />
            <span>EXPLORE PUBLIC ADVISORIES</span>
          </Link>
          <Link
            href="/register"
            className="text-xs font-mono text-amber-400 hover:text-amber-300 underline underline-offset-4 px-3 py-2 transition-colors"
          >
            Register for Portal Access
          </Link>
        </div>

        {/* Live Telemetry Ticker */}
        <div className="pt-6 grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3 max-w-5xl mx-auto text-left">
          <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800/80">
            <div className="text-[10px] font-mono text-slate-400 uppercase">Industrial Cadastre</div>
            <div className="text-base font-mono font-bold text-white">35,570+ Facilities</div>
          </div>
          <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800/80">
            <div className="text-[10px] font-mono text-slate-400 uppercase">Power Infrastructure</div>
            <div className="text-base font-mono font-bold text-amber-400">502 Power Stations</div>
          </div>
          <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800/80">
            <div className="text-[10px] font-mono text-slate-400 uppercase">Spatial Resolution</div>
            <div className="text-base font-mono font-bold text-cyan-400">375m (VIIRS I-Band)</div>
          </div>
          <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800/80">
            <div className="text-[10px] font-mono text-slate-400 uppercase">Sweep Frequency</div>
            <div className="text-base font-mono font-bold text-emerald-400">15-Minute Cycle</div>
          </div>
          <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800/80 col-span-2 sm:col-span-1">
            <div className="text-[10px] font-mono text-slate-400 uppercase">Sovereign Scope</div>
            <div className="text-base font-mono font-bold text-white">36 States & UTs</div>
          </div>
        </div>
      </section>

      {/* 3. KEY METRICS STRIP (4-column responsive grid) */}
      <section className="px-4 lg:px-10 py-10 bg-slate-900/40 border-y border-agni-border">
        <div className="max-w-6xl mx-auto space-y-4">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {primaryStats.map((stat, idx) => (
              <div key={idx} className="bg-slate-900/90 border border-slate-800 p-4 rounded-xl space-y-1.5">
                <span className={`text-[9px] font-mono uppercase px-2 py-0.5 rounded border font-bold ${stat.badgeColor}`}>
                  {stat.badge}
                </span>
                <div className="text-2xl sm:text-3xl font-black text-white font-mono tracking-tight pt-1">
                  {stat.metric}
                </div>
                <div className="text-xs font-semibold text-slate-200">{stat.title}</div>
                <div className="text-[10px] text-slate-400">{stat.subtext}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* 4. HOW IT WORKS / PIPELINE (3-step visual cards) */}
      <section id="pipeline" className="px-4 lg:px-10 py-16 bg-slate-950/90 border-b border-agni-border scroll-mt-16">
        <div className="max-w-6xl mx-auto space-y-8">
          <div className="text-center space-y-1.5">
            <span className="text-xs font-mono uppercase text-amber-400 tracking-wider font-semibold">
              End-to-End Operational Pipeline
            </span>
            <h2 className="text-2xl sm:text-3xl font-extrabold text-white">
              From Raw Satellite Radiometry to Verified Prevention
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            {pipelineSteps.map((step) => {
              const Icon = step.icon;
              return (
                <div
                  key={step.step}
                  className={`p-6 rounded-2xl bg-gradient-to-b ${step.color} border space-y-4 relative`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-2xl font-black opacity-40">{step.step}</span>
                    <div className="p-2.5 rounded-xl bg-slate-900/80 border border-slate-800">
                      <Icon className="w-5 h-5" />
                    </div>
                  </div>
                  <div>
                    <h3 className="font-mono font-black text-lg text-white">{step.title}</h3>
                    <p className="text-xs text-slate-300 font-medium">{step.subtitle}</p>
                  </div>
                  <p className="text-xs text-slate-400 leading-relaxed">
                    {step.desc}
                  </p>
                  <ul className="space-y-1.5 pt-2 border-t border-slate-800/80 text-[11px] text-slate-300 font-mono">
                    {step.bullets.map((b, i) => (
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

      {/* 5. CORE CAPABILITIES (6-card grid) */}
      <section id="capabilities" className="px-4 lg:px-10 py-16 bg-slate-900/30 border-b border-agni-border scroll-mt-16">
        <div className="max-w-6xl mx-auto space-y-8">
          <div className="text-center space-y-1.5">
            <span className="text-xs font-mono uppercase text-amber-400 tracking-wider font-semibold">
              Mission-Critical Features
            </span>
            <h2 className="text-2xl sm:text-3xl font-extrabold text-white">
              Core Capabilities for National Thermal Safety
            </h2>
            <p className="text-xs text-slate-400 max-w-xl mx-auto">
              Combining earth observation with machine learning models and spatial databases for instant threat triage.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {capabilities.map((cap) => {
              const Icon = cap.icon;
              return (
                <div key={cap.title} className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-3 hover:border-slate-700 transition-colors">
                  <div className="flex items-center justify-between">
                    <div className="p-2.5 rounded-xl bg-slate-800 border border-slate-700">
                      <Icon className="w-5 h-5 text-amber-400" />
                    </div>
                    <span className="text-[9px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700 font-bold uppercase">
                      {cap.badge}
                    </span>
                  </div>
                  <h3 className="text-sm font-bold text-white">{cap.title}</h3>
                  <p className="text-xs text-slate-400 leading-relaxed">{cap.desc}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* INTERACTIVE DEMONSTRATION SECTION */}
      <section id="demo" className="px-4 lg:px-10 py-14 bg-slate-950/80 border-b border-agni-border scroll-mt-16">
        <div className="max-w-6xl mx-auto space-y-6">
          <div className="text-center space-y-1.5">
            <span className="text-xs font-mono uppercase text-amber-400 tracking-wider font-semibold">
              Technology Demonstration
            </span>
            <h2 className="text-2xl sm:text-3xl font-extrabold text-white">
              Synthetic Thermal Telemetry Inspection
            </h2>
            <p className="text-xs text-slate-400 max-w-2xl mx-auto">
              Inspect how AGNI-NETRA combines radiative telemetry, Platt-calibrated ML inference, and spatial enrichment. Live operational data requires authenticated clearance.
            </p>
          </div>

          <ObservationQuickExplorer />
        </div>
      </section>

      {/* 6. ROLE-BASED PORTALS SECTION (THE KEY PORTALS — NO ADMIN) */}
      <section id="portals" className="px-4 lg:px-10 py-16 bg-slate-900/40 border-b border-agni-border scroll-mt-16">
        <div className="max-w-6xl mx-auto space-y-8">
          <div className="text-center space-y-1.5">
            <span className="text-xs font-mono uppercase text-amber-400 tracking-wider font-semibold">
              Operational Workspaces
            </span>
            <h2 className="text-2xl sm:text-3xl font-extrabold text-white">
              Dedicated Portals for Every Operational Role
            </h2>
            <p className="text-xs text-slate-400 max-w-xl mx-auto">
              Purpose-built workspaces tailored to the needs of analysts, agencies, and the public.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {portals.map((p) => {
              const Icon = p.icon;
              return (
                <div key={p.title} className="p-6 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-4 flex flex-col justify-between hover:border-slate-700 transition-all shadow-xl">
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="p-2.5 rounded-xl bg-slate-800 border border-slate-700">
                        <Icon className="w-5 h-5 text-amber-400" />
                      </div>
                      <span className={`text-[9px] font-mono font-bold px-2 py-0.5 rounded border uppercase ${p.badgeColor}`}>
                        {p.badge}
                      </span>
                    </div>
                    <h3 className="text-sm font-bold text-white tracking-wide">{p.title}</h3>
                    <p className="text-xs text-slate-400 leading-relaxed">{p.desc}</p>
                  </div>
                  <Link
                    href={p.href}
                    className={`w-full mt-4 py-2.5 px-4 rounded-xl font-bold text-xs flex items-center justify-between transition-all cursor-pointer ${
                      p.publicAccess
                        ? "bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 border border-emerald-500/40"
                        : "bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-white border border-slate-700"
                    }`}
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

      {/* 7. TECHNOLOGY & TRUST */}
      <section id="trust" className="px-4 lg:px-10 py-16 bg-slate-950/90 border-b border-agni-border scroll-mt-16">
        <div className="max-w-6xl mx-auto space-y-8">
          {/* Statutory Security Invariant Banner */}
          <div className="p-5 rounded-2xl bg-slate-900/90 border border-amber-500/40 space-y-2">
            <div className="flex items-center gap-2 text-amber-400 font-mono font-bold text-xs uppercase tracking-wider">
              <Lock className="w-4 h-4 shrink-0" />
              <span>Statutory Policy Invariant: ENABLE_OPERATIONAL_DISPATCH_GATE = False</span>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed font-sans">
              Autonomous emergency dispatch is permanently blocked by statutory policy. Human verification is legally authoritative. Spaceborne observations and root-cause hypotheses serve strictly as decision support for accredited personnel.
            </p>
          </div>

          <div className="text-center space-y-1.5 pt-4">
            <span className="text-xs font-mono uppercase text-amber-400 tracking-wider font-semibold">
              Platform Architecture & Trust
            </span>
            <h2 className="text-2xl sm:text-3xl font-extrabold text-white">
              Enterprise Governance & Technical Verification
            </h2>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {techStack.map((tech) => {
              const Icon = tech.icon;
              return (
                <div key={tech.title} className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2">
                  <div className="flex items-center gap-2 text-white font-semibold text-xs">
                    <Icon className="w-4 h-4 text-amber-400 shrink-0" />
                    <span>{tech.title}</span>
                  </div>
                  <p className="text-[11px] text-slate-400 leading-relaxed">{tech.desc}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* 8. FINAL CALL TO ACTION */}
      <section className="px-4 lg:px-10 py-16 bg-gradient-to-b from-slate-950 to-agni-navy text-center border-b border-agni-border">
        <div className="max-w-3xl mx-auto space-y-6">
          <div className="w-12 h-12 mx-auto rounded-2xl bg-amber-500/20 border border-amber-500/40 flex items-center justify-center">
            <Flame className="w-6 h-6 text-amber-400" />
          </div>
          <div className="space-y-2">
            <h2 className="text-2xl sm:text-4xl font-black text-white">
              Equip Your Organization with Spaceborne Thermal Intelligence
            </h2>
            <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
              Join emergency response agencies, state disaster authorities, and geospatial analysts operating with near-real-time satellite observation and deterministic root-cause prevention.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-3.5 pt-2">
            <Link
              href="/login"
              className="w-full sm:w-auto px-8 py-3.5 rounded-xl bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-600 hover:to-orange-700 text-slate-950 font-extrabold text-xs tracking-wider font-mono shadow-xl shadow-amber-500/20 flex items-center justify-center gap-2 transition-all hover:scale-105 cursor-pointer"
            >
              <Lock className="w-4 h-4" />
              <span>Sign In to Workspace</span>
            </Link>
            <Link
              href="/register"
              className="w-full sm:w-auto px-8 py-3.5 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-200 font-semibold text-xs tracking-wider font-mono transition-all flex items-center justify-center gap-2 cursor-pointer"
            >
              <span>Register for Access</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
            <Link
              href="/portal/public"
              className="w-full sm:w-auto px-8 py-3.5 rounded-xl bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/40 text-emerald-300 font-semibold text-xs tracking-wider font-mono transition-all flex items-center justify-center gap-2 cursor-pointer"
            >
              <Globe className="w-4 h-4" />
              <span>View Public Safety Advisories</span>
            </Link>
          </div>
        </div>
      </section>

      {/* 9. FOOTER */}
      <footer className="border-t border-agni-border bg-slate-950 px-4 lg:px-10 py-10 text-xs text-slate-500 font-mono">
        <div className="max-w-6xl mx-auto space-y-6">
          <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
            <div className="space-y-2 max-w-md">
              <AgniNetraLogo size={32} subtext="NATIONAL GEOSPATIAL INTELLIGENCE" />
              <p className="text-[11px] text-slate-400 font-sans leading-relaxed">
                Automated spaceborne thermal observation, deterministic root-cause reasoning, and operational hazard management across the Republic of India.
              </p>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 gap-6 text-xs font-mono">
              <div className="space-y-2">
                <div className="text-white font-bold uppercase tracking-wider text-[11px]">Workspaces</div>
                <ul className="space-y-1 text-slate-400">
                  <li><Link href="/login?redirect=%2Fdashboard" className="hover:text-amber-400">Analyst Portal</Link></li>
                  <li><Link href="/login?redirect=%2Fportal%2Fagency" className="hover:text-amber-400">Agency Portal</Link></li>
                  <li><Link href="/portal/public" className="hover:text-emerald-400">Public Advisories</Link></li>
                </ul>
              </div>

              <div className="space-y-2">
                <div className="text-white font-bold uppercase tracking-wider text-[11px]">Account</div>
                <ul className="space-y-1 text-slate-400">
                  <li><Link href="/login" className="hover:text-amber-400">Sign In</Link></li>
                  <li><Link href="/register" className="hover:text-amber-400">Register</Link></li>
                  <li><Link href="/forgot-password" className="hover:text-amber-400">Passcode Recovery</Link></li>
                </ul>
              </div>

              <div className="space-y-2 col-span-2 sm:col-span-1">
                <div className="text-white font-bold uppercase tracking-wider text-[11px]">Statutory Policy</div>
                <div className="text-[10px] text-amber-500/90 font-mono">
                  DISPATCH_GATE = False
                </div>
                <div className="text-[10px] text-slate-500">
                  Correlation ≠ Causation. Human review authoritative.
                </div>
              </div>
            </div>
          </div>

          <div className="pt-6 border-t border-slate-900 flex flex-col sm:flex-row items-center justify-between gap-3 text-[10px] text-slate-600">
            <div>
              NASA FIRMS • OpenStreetMap Cadastre • CEA Power Grid • ISRO Bhuvan
            </div>
            <div>
              © 2026 AGNI-NETRA. Sovereign Spaceborne Intelligence Architecture.
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
