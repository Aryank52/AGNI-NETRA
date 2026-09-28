"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { 
  Flame, ShieldAlert, Cpu, Activity, 
  Map, Database, ArrowRight, CheckCircle2, 
  Layers, Lock, Building2, Globe, ShieldCheck,
  Radio, HardDrive, Server, FileCheck, KeyRound,
  ExternalLink, ChevronRight, Zap
} from "lucide-react";
import AgniNetraLogo from "@/components/common/AgniNetraLogo";
import ObservationQuickExplorer from "@/components/common/ObservationQuickExplorer";
import SystemStatusBanner from "@/components/common/SystemStatusBanner";
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
      label: "Thermal Detection Precision",
      value: "375m",
      subtext: "VIIRS I-Band sub-pixel spatial resolution",
      badge: "NASA FIRMS",
      badgeColor: "bg-emerald-500/20 text-emerald-300 border-emerald-500/40",
    },
    {
      label: "Historical Baseline",
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
      subtitle: "Near-Real-Time Spaceborne Observation",
      desc: "Continuous ingestion of NASA FIRMS VIIRS (375m) and MODIS (1km) earth observation passes. Radiometric FRP thresholding, spatiotemporal DBSCAN clustering, and geographic boundary validation across all 36 Indian States & UTs.",
      icon: Flame,
      color: "from-amber-500/20 to-orange-500/10 border-amber-500/40 text-amber-400",
      bullets: [
        "15-minute automated ingestion cycle",
        "Point-in-polygon PostGIS indexing",
        "Dynamic sensor swath projection",
      ],
    },
    {
      step: "02",
      title: "UNDERSTAND",
      subtitle: "JARVIS Master Observer & Explainable ML",
      desc: "Deterministic analytical orchestration through JARVIS Master Observer. 18-feature remote sensing XGBoost classifier with TreeExplainer SHAP local attributions, historical baseline deviations (Z-score surge over 4-year seasonal cycles), and 5-factor risk scoring.",
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
      subtitle: "Proactive Prevention & Deterministic Root Cause",
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

  const architectureStack = [
    {
      title: "Spaceborne Telemetry Ingestion",
      icon: Radio,
      badge: "SATELLITE TELEMETRY",
      badgeColor: "text-amber-400 border-amber-500/30 bg-amber-500/10",
      desc: "NASA FIRMS (VIIRS 375m & MODIS 1km) automated 15-minute telemetry polling. Sub-pixel radiometric filtering, daytime/nighttime overpass calibration, and geographic boundary enforcement across Indian territory.",
    },
    {
      title: "Spatial Intelligence Core",
      icon: Database,
      badge: "POSTGIS 3.4 & POSTGRESQL 16",
      badgeColor: "text-cyan-400 border-cyan-500/30 bg-cyan-500/10",
      desc: "High-performance spatial indexing (GiST), ST_DWithin spatiotemporal clustering, and spatial fusion with OpenStreetMap 35,570+ industrial cadastre and Central Electricity Authority (CEA) 502 power stations.",
    },
    {
      title: "Distributed Pipeline Execution",
      icon: Server,
      badge: "CELERY & UPSTASH REDIS",
      badgeColor: "text-emerald-400 border-emerald-500/30 bg-emerald-500/10",
      desc: "Asynchronous task queue processing, distributed ingestion workers, background satellite swath geometry generation, and high-frequency analytical task execution.",
    },
    {
      title: "Immutable Evidence & Storage",
      icon: HardDrive,
      badge: "BACKBLAZE B2 & S3 API",
      badgeColor: "text-purple-400 border-purple-500/30 bg-purple-500/10",
      desc: "Zero-egress object storage for satellite imagery tiles, investigation dossiers, and immutable SHA-256 evidence archives adhering to national compliance standards.",
    },
  ];

  const portals = [
    {
      title: "Geospatial Analyst Workstation",
      badge: "OPERATIONAL INTELLIGENCE",
      badgeColor: "bg-blue-500/20 text-blue-300 border-blue-500/40",
      desc: "National GIS command center, live thermal hotspot streams, JARVIS reasoning console, and human-in-the-loop incident verification.",
      icon: Map,
      href: "/login?redirect=/dashboard",
      cta: "Sign In as Analyst",
      authRequired: true,
    },
    {
      title: "Emergency Response Portal",
      badge: "AGENCY & NDMA",
      badgeColor: "bg-red-500/20 text-red-300 border-red-500/40",
      desc: "Role-authorized alert triage, regional baselines, priority incident monitoring, and authorized regulatory report review.",
      icon: ShieldAlert,
      href: "/login?redirect=/portal/agency",
      cta: "Sign In as Agency",
      authRequired: true,
    },
    {
      title: "Industry & Research Portals",
      badge: "COMPLIANCE & ACADEMIA",
      badgeColor: "bg-purple-500/20 text-purple-300 border-purple-500/40",
      desc: "Industrial facility emissions self-reporting, consent tracking, environmental research data access, and analytical geojson exports.",
      icon: Building2,
      href: "/login?redirect=/portal/industry",
      cta: "Sign In to Portal",
      authRequired: true,
    },
    {
      title: "Citizen Public Safety Portal",
      badge: "PUBLIC ADVISORY",
      badgeColor: "bg-emerald-500/20 text-emerald-300 border-emerald-500/40",
      desc: "Privacy-preserving regional advisories, generalized hazard boundaries, air quality context, and citizen safety guidance.",
      icon: Globe,
      href: "/portal/public",
      cta: "View Public Advisories",
      authRequired: false,
    },
  ];

  const securityFeatures = [
    {
      title: "Operational Dispatch Invariant",
      desc: "Autonomous emergency dispatch is permanently blocked by statutory software policy (ENABLE_OPERATIONAL_DISPATCH_GATE = False). Human review is mandatory for all dispatches.",
      icon: Lock,
    },
    {
      title: "Role-Based Access Enforcement",
      desc: "Strictly partitioned access tiers: Analyst, Agency, Administrator, Industry, Researcher, and Public Viewer. Operational endpoints require authenticated credentials.",
      icon: KeyRound,
    },
    {
      title: "Cryptographic Audit Trail",
      desc: "Every verification decision, triage state transition, and hypothesis update is recorded in append-only audit tables with cryptographic hash seals.",
      icon: FileCheck,
    },
    {
      title: "Sovereign Deployment Architecture",
      desc: "Designed to operate in secure government cloud environments (NIC, ISRO Bhuvan) or air-gapped sovereign installations with zero external data leakage.",
      icon: ShieldCheck,
    },
  ];

  return (
    <div className="min-h-screen bg-agni-navy text-slate-100 flex flex-col selection:bg-amber-500 selection:text-slate-950 font-sans">
      {/* Top Header Navigation */}
      <nav className="h-16 border-b border-agni-border px-4 lg:px-10 flex items-center justify-between backdrop-blur-md bg-slate-950/90 sticky top-0 z-40">
        <div className="flex items-center gap-6">
          <Link href="/" className="inline-block">
            <AgniNetraLogo size={36} subtext="NATIONAL GEOSPATIAL INTELLIGENCE" />
          </Link>

          <div className="hidden lg:flex items-center gap-5 text-xs font-mono text-slate-400">
            <a href="#pipeline" className="hover:text-amber-400 transition-colors">Pipeline</a>
            <a href="#architecture" className="hover:text-amber-400 transition-colors">Architecture</a>
            <a href="#demo" className="hover:text-amber-400 transition-colors">Synthetic Demo</a>
            <a href="#security" className="hover:text-amber-400 transition-colors">Security</a>
            <a href="#portals" className="hover:text-amber-400 transition-colors">Portals</a>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="hidden md:flex items-center gap-2 text-xs text-slate-400 mr-2 font-mono">
            {dbLoading ? (
              <>
                <span className="inline-block w-2 h-2 rounded-full bg-slate-500 animate-pulse"></span>
                <span>Connecting telemetry...</span>
              </>
            ) : dbHealth && (dbHealth.status === "HEALTHY" || dbHealth.database === "CONNECTED") ? (
              <>
                <span className="inline-block w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                <span>
                  {dbHealth.spatial === "PostGIS"
                    ? `PostGIS ${dbHealth.postgis_version ? `${dbHealth.postgis_version} ` : ""}Active`
                    : "Spatial Index Connected"}
                </span>
              </>
            ) : (
              <>
                <span className="inline-block w-2 h-2 rounded-full bg-emerald-500"></span>
                <span>Spatial Index Ready</span>
              </>
            )}
          </div>

          <Link
            href="/login"
            className="text-xs font-semibold text-slate-300 hover:text-white px-3.5 py-1.5 rounded-lg hover:bg-slate-800 transition-colors font-mono"
          >
            Sign In
          </Link>
          <Link
            href="/login"
            className="px-4 py-2 rounded-xl bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-600 hover:to-orange-700 text-slate-950 font-bold text-xs shadow-md flex items-center gap-1.5 transition-all hover:scale-105 font-mono"
          >
            <span>Access Platform</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative px-4 lg:px-10 pt-16 pb-14 max-w-6xl mx-auto text-center space-y-6">
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-slate-900/90 border border-slate-700 text-slate-300 text-xs font-mono">
          <Zap className="w-3.5 h-3.5 text-amber-400" />
          <span>Spaceborne Thermal Intelligence & Proactive Industrial Fire Prevention</span>
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

        <p className="max-w-3xl mx-auto text-sm sm:text-base text-slate-300 font-normal leading-relaxed">
          National satellite-derived thermal observation, deterministic root-cause reasoning, and operational risk intelligence for industrial complexes, power stations, and critical infrastructure across the Republic of India.
        </p>

        {/* Primary CTAs */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-3.5 pt-2">
          <Link
            href="/login"
            className="w-full sm:w-auto px-8 py-3.5 rounded-xl bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-600 hover:to-orange-700 text-slate-950 font-extrabold text-xs tracking-wider font-mono shadow-xl shadow-amber-500/20 flex items-center justify-center gap-2 transition-all hover:scale-105 cursor-pointer"
          >
            <Lock className="w-4 h-4" />
            <span>ACCESS INTELLIGENCE PLATFORM</span>
          </Link>
          <a
            href="#pipeline"
            className="w-full sm:w-auto px-8 py-3.5 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-200 font-semibold text-xs tracking-wider font-mono transition-all flex items-center justify-center gap-2 cursor-pointer"
          >
            <span>EXPLORE TECHNOLOGY</span>
            <ChevronRight className="w-4 h-4 text-amber-400" />
          </a>
        </div>

        {/* Operational Safety Invariant Notice */}
        <div className="mt-8 max-w-3xl mx-auto p-4 rounded-xl bg-slate-900/90 border border-slate-800 text-left flex items-start gap-3.5 text-xs">
          <Lock className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <div className="font-bold text-amber-300 font-mono text-[11px] uppercase flex items-center gap-2">
              <span>Operational Safety Invariant (ENABLE_OPERATIONAL_DISPATCH_GATE = False)</span>
            </div>
            <p className="text-[11px] text-slate-400 leading-relaxed font-sans">
              Human verification is legally authoritative. Autonomous emergency dispatch is permanently blocked by statutory safety policy. Spaceborne observations and root-cause hypotheses serve strictly as decision support for accredited personnel.
            </p>
          </div>
        </div>
      </section>

      {/* 3 Pillars: DETECT, UNDERSTAND, PREVENT */}
      <section id="pipeline" className="px-4 lg:px-10 py-14 bg-slate-950/90 border-y border-agni-border scroll-mt-16">
        <div className="max-w-6xl mx-auto space-y-8">
          <div className="text-center space-y-1.5">
            <span className="text-xs font-mono uppercase text-amber-400 tracking-wider font-semibold">
              End-to-End Operational Pipeline
            </span>
            <h2 className="text-xl sm:text-3xl font-extrabold text-white">
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

      {/* Technology Architecture Section */}
      <section id="architecture" className="px-4 lg:px-10 py-14 bg-slate-950/80 border-b border-agni-border scroll-mt-16">
        <div className="max-w-6xl mx-auto space-y-8">
          <div className="text-center space-y-1.5">
            <span className="text-xs font-mono uppercase text-amber-400 tracking-wider font-semibold">
              System Engineering Architecture
            </span>
            <h2 className="text-xl sm:text-3xl font-extrabold text-white">
              Enterprise Geospatial & Machine Learning Stack
            </h2>
            <p className="text-xs text-slate-400 max-w-2xl mx-auto">
              Engineered with modern distributed components capable of ingesting high-volume satellite telemetries with sub-second geospatial querying.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {architectureStack.map((tech) => {
              const Icon = tech.icon;
              return (
                <div
                  key={tech.title}
                  className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-3"
                >
                  <div className="flex items-center justify-between">
                    <div className="p-2.5 rounded-xl bg-slate-800 border border-slate-700">
                      <Icon className="w-5 h-5 text-amber-400" />
                    </div>
                    <span className={`text-[9px] font-mono font-bold px-2 py-0.5 rounded border uppercase ${tech.badgeColor}`}>
                      {tech.badge}
                    </span>
                  </div>
                  <h3 className="text-base font-bold text-white">{tech.title}</h3>
                  <p className="text-xs text-slate-300 leading-relaxed">{tech.desc}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Synthetic Demonstration Section */}
      <section id="demo" className="px-4 lg:px-10 py-14 bg-slate-900/30 border-b border-agni-border scroll-mt-16">
        <div className="max-w-6xl mx-auto space-y-6">
          <div className="text-center space-y-1.5">
            <span className="text-xs font-mono uppercase text-amber-400 tracking-wider font-semibold">
              Interactive Technology Demonstration
            </span>
            <h2 className="text-xl sm:text-3xl font-extrabold text-white">
              Synthetic Thermal Telemetry Inspection
            </h2>
            <p className="text-xs text-slate-400 max-w-2xl mx-auto">
              Inspect how AGNI-NETRA combines radiative telemetry, Platt-calibrated ML inference, and spatial enrichment. Live operational data requires authenticated clearance.
            </p>
          </div>

          <ObservationQuickExplorer />
        </div>
      </section>

      {/* Security & Sovereign Governance Section */}
      <section id="security" className="px-4 lg:px-10 py-14 bg-slate-950/90 border-b border-agni-border scroll-mt-16">
        <div className="max-w-6xl mx-auto space-y-8">
          <div className="text-center space-y-1.5">
            <span className="text-xs font-mono uppercase text-amber-400 tracking-wider font-semibold">
              Security, Governance & Sovereignty
            </span>
            <h2 className="text-xl sm:text-3xl font-extrabold text-white">
              Enterprise Governance & Statutory Compliance
            </h2>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {securityFeatures.map((feat) => {
              const Icon = feat.icon;
              return (
                <div key={feat.title} className="p-5 rounded-xl bg-slate-900/80 border border-slate-800 space-y-2.5">
                  <div className="p-2 rounded-lg bg-slate-800 border border-slate-700 w-fit">
                    <Icon className="w-4 h-4 text-amber-400" />
                  </div>
                  <h3 className="text-xs font-bold text-white">{feat.title}</h3>
                  <p className="text-[11px] text-slate-400 leading-relaxed">{feat.desc}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Role-Aware User Portals */}
      <section id="portals" className="px-4 lg:px-10 py-14 bg-slate-900/40 border-b border-agni-border scroll-mt-16">
        <div className="max-w-6xl mx-auto space-y-8">
          <div className="text-center space-y-1.5">
            <span className="text-xs font-mono uppercase text-amber-400 tracking-wider font-semibold">
              Operational Workstations
            </span>
            <h2 className="text-xl sm:text-3xl font-extrabold text-white">
              Role-Partitioned Decision Support Portals
            </h2>
            <p className="text-xs text-slate-400 max-w-xl mx-auto">
              Access is strictly governed by organizational verification and role-based permissions.
            </p>
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

      {/* Final Call to Action */}
      <section className="px-4 lg:px-10 py-16 bg-gradient-to-b from-slate-950 to-agni-navy text-center border-b border-agni-border">
        <div className="max-w-3xl mx-auto space-y-6">
          <div className="w-12 h-12 mx-auto rounded-2xl bg-amber-500/20 border border-amber-500/40 flex items-center justify-center">
            <Flame className="w-6 h-6 text-amber-400" />
          </div>
          <div className="space-y-2">
            <h2 className="text-2xl sm:text-4xl font-black text-white">
              Equip Your Organization with National Geospatial Thermal Intelligence
            </h2>
            <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
              Join emergency response agencies, state pollution control boards, and industrial complexes operating with near-real-time satellite observation and proactive root-cause prevention.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-3.5 pt-2">
            <Link
              href="/login"
              className="w-full sm:w-auto px-8 py-3.5 rounded-xl bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-600 hover:to-orange-700 text-slate-950 font-extrabold text-xs tracking-wider font-mono shadow-xl shadow-amber-500/20 flex items-center justify-center gap-2 transition-all hover:scale-105 cursor-pointer"
            >
              <Lock className="w-4 h-4" />
              <span>Sign In to Portal</span>
            </Link>
            <Link
              href="/register"
              className="w-full sm:w-auto px-8 py-3.5 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-200 font-semibold text-xs tracking-wider font-mono transition-all flex items-center justify-center gap-2 cursor-pointer"
            >
              <span>Request Operational Access</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-agni-border bg-slate-950 px-4 lg:px-10 py-8 text-xs text-slate-500 font-mono">
        <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="space-y-1 text-center sm:text-left">
            <div className="text-slate-300 font-bold">AGNI-NETRA — Geospatial Thermal Intelligence & Fire Prevention Platform</div>
            <div className="text-[10px] text-slate-500">
              NASA FIRMS • OpenStreetMap Cadastre • CEA Power Grid • ISRO Bhuvan • CPCB / SPCB Alignment
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
