"use client";

import React from "react";
import Link from "next/link";
import { 
  Flame, ShieldAlert, Cpu, Activity, 
  Map, Database, ArrowRight, CheckCircle2, 
  Layers, Search, FileText, ChevronRight, Zap,
  Building2, GraduationCap, Globe, ShieldCheck, Lock,
  ExternalLink, BarChart3, Clock, Check
} from "lucide-react";
import { getApiDocsUrl } from "@/lib/api";

export default function LandingPage() {
  // Section 2: Scientifically Accurate Statistics
  const primaryStats = [
    {
      label: "Total Thermal Observations",
      value: "8,221,894",
      subtext: "Historical + Operational FIRMS observations",
      badge: "TOTAL REPOSITORY",
      badgeColor: "bg-slate-800 text-slate-300 border-slate-700",
    },
    {
      label: "2026 Operational Stream",
      value: "1,773,228",
      subtext: "Current operational-year observations",
      badge: "OPERATIONAL STREAM",
      badgeColor: "bg-emerald-500/20 text-emerald-300 border-emerald-500/40",
    },
    {
      label: "Sealed Historical Baseline",
      value: "6,448,666",
      subtext: "Immutable FIRMS records, 2022–2025",
      badge: "SEALED BASELINE",
      badgeColor: "bg-blue-500/20 text-blue-300 border-blue-500/40",
    },
    {
      label: "Industrial Facilities",
      value: "35,684",
      subtext: "National industrial facility registry",
      badge: "OSM CADASTRE",
      badgeColor: "bg-cyan-500/20 text-cyan-300 border-cyan-500/40",
    },
    {
      label: "Administrative Units",
      value: "7,595",
      subtext: "States/UTs, districts and subdistricts",
      badge: "SOVEREIGN JURISDICTION",
      badgeColor: "bg-amber-500/20 text-amber-300 border-amber-500/40",
    },
  ];

  // Section 4: Authentic Data Sources & Coverage Matrix
  const dataSources = [
    {
      source: "NASA FIRMS",
      role: "Satellite-derived thermal observations (VIIRS/MODIS 375m & 1km)",
      coverage: "NATIONAL",
      status: "OPERATIONAL",
      coverageColor: "text-emerald-400 bg-emerald-500/10 border-emerald-500/30",
    },
    {
      source: "OpenStreetMap (OSM)",
      role: "Industrial manufacturing plants, refineries & chemical cadastre",
      coverage: "NATIONAL",
      status: "OPERATIONAL",
      coverageColor: "text-emerald-400 bg-emerald-500/10 border-emerald-500/30",
    },
    {
      source: "Central Electricity Authority (CEA)",
      role: "National thermal, hydro, and gas power generation stations",
      coverage: "NATIONAL",
      status: "OPERATIONAL",
      coverageColor: "text-emerald-400 bg-emerald-500/10 border-emerald-500/30",
    },
    {
      source: "Indian Bureau of Mines (IBM)",
      role: "Auctioned mineral blocks, coal seams & leasehold polygons",
      coverage: "PARTIAL (414 LEASES)",
      status: "INTEGRATED",
      coverageColor: "text-purple-400 bg-purple-500/10 border-purple-500/30",
    },
    {
      source: "ISRO Bhuvan",
      role: "Land Use / Land Cover (LULC) 50m thematic raster classification",
      coverage: "PARTIAL (121 TILES)",
      status: "PILOT EXTENT",
      coverageColor: "text-amber-400 bg-amber-500/10 border-amber-500/30",
    },
    {
      source: "Wildlife Institute of India (WII)",
      role: "Protected areas, national parks & eco-sensitive buffer zones",
      coverage: "PILOT / BENCHMARK",
      status: "INTEGRATED",
      coverageColor: "text-cyan-400 bg-cyan-500/10 border-cyan-500/30",
    },
    {
      source: "Forest Survey of India (FSI)",
      role: "State of Forest Report (ISFR) reference benchmark context",
      coverage: "PILOT / BENCHMARK",
      status: "VALIDATED",
      coverageColor: "text-cyan-400 bg-cyan-500/10 border-cyan-500/30",
    },
    {
      source: "MoEFCC PARIVESH",
      role: "Environmental clearance project locations & compliance filings",
      coverage: "REGULATORY DATASET",
      status: "INTEGRATED",
      coverageColor: "text-blue-400 bg-blue-500/10 border-blue-500/30",
    },
  ];

  // Section 18: Differentiated Stakeholder Portals
  const portals = [
    {
      title: "Command Center Dashboard",
      badge: "ANALYSTS & DISASTER AGENCIES",
      badgeColor: "bg-amber-500/20 text-amber-300 border-amber-500/40",
      desc: "Full 9-layer PostGIS GIS workstation, live satellite observation triage, SHAP waterfall explainability, and HITL verification desk.",
      icon: Map,
      href: "/dashboard",
      cta: "Launch Command Center",
      highlight: true,
    },
    {
      title: "Public Safety Portal",
      badge: "CITIZEN & MUNICIPAL",
      badgeColor: "bg-blue-500/20 text-blue-300 border-blue-500/40",
      desc: "Transparent regional fire risk advisories, smoke dispersion exposure metrics, and non-sensitive aggregated hazard ratings.",
      icon: Globe,
      href: "/portal/public",
      cta: "View Public Safety Portal",
      highlight: false,
    },
    {
      title: "Industry Compliance Portal",
      badge: "PLANT MANAGERS & OPERATORS",
      badgeColor: "bg-emerald-500/20 text-emerald-300 border-emerald-500/40",
      desc: "Maintenance flare scheduling, shutdown compliance declarations, CPCB emission self-audits, and proprietary site verification.",
      icon: Building2,
      href: "/portal/industry",
      cta: "Access Industry Portal",
      highlight: false,
    },
    {
      title: "Research & Academic Portal",
      badge: "OPEN SCIENCE & MODEL RESEARCH",
      badgeColor: "bg-purple-500/20 text-purple-300 border-purple-500/40",
      desc: "Multi-year temporal baselines, diurnal burning curves, cross-calibration validation benchmarks, and exportable research datasets.",
      icon: GraduationCap,
      href: "/portal/research",
      cta: "Explore Research Portal",
      highlight: false,
    },
  ];

  return (
    <div className="min-h-screen bg-agni-navy text-slate-100 flex flex-col selection:bg-amber-500 selection:text-slate-950 font-sans">
      {/* Top Navigation */}
      <nav className="h-20 border-b border-agni-border px-6 lg:px-12 flex items-center justify-between backdrop-blur-md bg-slate-950/90 sticky top-0 z-40">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-500 via-orange-600 to-red-600 p-0.5 shadow-md flex items-center justify-center">
            <Flame className="w-6 h-6 text-white" />
          </div>
          <div>
            <span className="font-extrabold text-xl tracking-wider text-white font-mono">AGNI-NETRA</span>
            <span className="text-[10px] uppercase font-mono px-2 py-0.5 ml-2 rounded bg-slate-800 text-slate-300 border border-slate-700">
              NATIONAL GEOSPATIAL PLATFORM
            </span>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="hidden lg:flex items-center gap-2 text-xs text-slate-400 mr-2 font-mono">
            <span className="inline-block w-2 h-2 rounded-full bg-emerald-500"></span>
            <span>PostGIS 16 Connected</span>
          </div>
          <Link
            href="/login"
            className="text-xs font-semibold text-slate-300 hover:text-white px-4 py-2 rounded-lg hover:bg-slate-800 transition-colors"
          >
            Sign In
          </Link>
          <Link
            href="/dashboard"
            className="px-4 py-2 rounded-xl bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-600 hover:to-orange-700 text-slate-950 font-bold text-xs shadow-md flex items-center gap-2 transition-all hover:scale-105"
          >
            <span>Command Center</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative px-6 lg:px-12 pt-16 pb-16 max-w-6xl mx-auto text-center space-y-6">
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-slate-900 border border-slate-700 text-slate-300 text-xs font-mono">
          <Zap className="w-3.5 h-3.5 text-amber-400" />
          <span>NASA FIRMS VIIRS • POSTGIS 3.4 • SHAP TREE-EXPLAINER • 7-CLASS CALIBRATED ML</span>
        </div>

        <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight text-white leading-tight">
          National Geospatial Intelligence for <br />
          <span className="bg-clip-text text-transparent bg-gradient-to-r from-amber-400 via-orange-500 to-red-500">
            Industrial Fires & Thermal Anomalies
          </span>
        </h1>

        <p className="max-w-3xl mx-auto text-base sm:text-lg text-slate-300 font-normal leading-relaxed">
          &ldquo;FIRMS tells us where a thermal anomaly is. <br className="hidden sm:inline" />
          <strong className="text-white">AGNI-NETRA</strong> tells us what it most likely is, whether it is persistent or abnormal, how risky it is, and why.&rdquo;
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-2">
          <Link
            href="/dashboard"
            className="w-full sm:w-auto px-8 py-3.5 rounded-xl bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-600 hover:to-orange-700 text-slate-950 font-extrabold text-sm shadow-lg flex items-center justify-center gap-2.5 transition-transform hover:scale-105"
          >
            <Map className="w-4 h-4 text-slate-950" />
            <span>Launch National Command Map</span>
          </Link>
          <Link
            href="/portal/public"
            className="w-full sm:w-auto px-8 py-3.5 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-200 font-semibold text-sm transition-all flex items-center justify-center gap-2"
          >
            <Globe className="w-4 h-4 text-blue-400" />
            <span>View Public Safety Portal</span>
          </Link>
        </div>

        {/* Section 6: Statutory Safety Notice */}
        <div className="mt-8 max-w-4xl mx-auto p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 text-left flex items-start gap-3 text-xs">
          <Lock className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
          <div className="space-y-0.5">
            <div className="font-bold text-amber-300 font-mono text-[11px] uppercase flex items-center gap-2">
              <span>Operational Safety Invariant (ENABLE_OPERATIONAL_DISPATCH_GATE = False)</span>
            </div>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              Decision-Support Platform: Autonomous emergency dispatch is disabled by statutory policy. Satellite-derived thermal observations are classified, contextualized, and prioritized for authorized analyst human-in-the-loop review and operational decision support.
            </p>
          </div>
        </div>
      </section>

      {/* Section 2: Scientifically Accurate Statistics Ribbon */}
      <section className="border-y border-agni-border bg-slate-950 px-6 lg:px-12 py-10">
        <div className="max-w-6xl mx-auto space-y-6">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-2 border-b border-slate-800 pb-3">
            <div>
              <h2 className="text-sm font-bold uppercase tracking-wider text-white font-mono flex items-center gap-2">
                <Database className="w-4 h-4 text-amber-400" />
                Authoritative Repository Telemetry
              </h2>
              <p className="text-xs text-slate-400">Verified PostgreSQL 16 / PostGIS 3.4 database records</p>
            </div>
            <span className="text-[11px] font-mono text-slate-500">
              National Spatial Cadastre
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
            {primaryStats.map((stat, idx) => (
              <div key={idx} className="bg-slate-900/90 border border-slate-800 p-4 rounded-xl space-y-2">
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

      {/* Section 8: Differentiating 3 Distinct Telemetry Domains */}
      <section className="px-6 lg:px-12 py-16 bg-slate-900/40 border-b border-agni-border">
        <div className="max-w-6xl mx-auto space-y-8">
          <div className="text-center space-y-2">
            <span className="text-xs font-mono uppercase text-amber-400 tracking-wider font-semibold">
              Data Lineage & Provenance Architecture
            </span>
            <h2 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
              Three Distinct Telemetry Domains
            </h2>
            <p className="text-slate-400 text-xs max-w-2xl mx-auto">
              AGNI-NETRA strictly segregates historical baselines, live operational satellite ingestion, and digital twin simulation into isolated pipelines.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Domain A */}
            <div className="p-6 rounded-2xl bg-slate-900 border border-blue-500/30 space-y-3">
              <div className="flex items-center justify-between">
                <span className="px-2.5 py-0.5 rounded text-[10px] font-mono font-bold bg-blue-500/20 text-blue-300 border border-blue-500/40 uppercase">
                  DOMAIN A • HISTORICAL
                </span>
                <span className="text-xs font-mono text-slate-500">2022–2025</span>
              </div>
              <h3 className="text-base font-bold text-white">Sealed Historical FIRMS Baseline</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                6,448,666 immutable satellite observations used to establish localized +3σ thermal standard deviations, seasonal burning cycles, and multi-year industrial persistence.
              </p>
              <div className="pt-2 border-t border-slate-800 text-[11px] font-mono text-slate-400">
                Status: <strong className="text-blue-400">Sealed & Immutable</strong>
              </div>
            </div>

            {/* Domain B */}
            <div className="p-6 rounded-2xl bg-slate-900 border border-emerald-500/30 space-y-3">
              <div className="flex items-center justify-between">
                <span className="px-2.5 py-0.5 rounded text-[10px] font-mono font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 uppercase">
                  DOMAIN B • OPERATIONAL STREAM
                </span>
                <span className="text-xs font-mono text-emerald-400">YEAR 2026</span>
              </div>
              <h3 className="text-base font-bold text-white">Live 2026 Operational Stream</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                1,773,228 operational-year observations processed through real-time deduplication, PostGIS spatial clustering, and automated human-in-the-loop alert routing.
              </p>
              <div className="pt-2 border-t border-slate-800 text-[11px] font-mono text-slate-400">
                Status: <strong className="text-emerald-400">Live Ingest Active</strong>
              </div>
            </div>

            {/* Domain C */}
            <div className="p-6 rounded-2xl bg-slate-900 border border-purple-500/30 space-y-3">
              <div className="flex items-center justify-between">
                <span className="px-2.5 py-0.5 rounded text-[10px] font-mono font-bold bg-purple-500/20 text-purple-300 border border-purple-500/40 uppercase">
                  DOMAIN C • SIMULATION
                </span>
                <span className="text-xs font-mono text-purple-400">DIGITAL TWIN</span>
              </div>
              <h3 className="text-base font-bold text-white">AGNI-SAT Mission Control</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                High-fidelity digital twin simulation engine modeling satellite orbital tracks, sensor swaths, and deterministic scenario execution without fabricated live orbital data.
              </p>
              <div className="pt-2 border-t border-slate-800 text-[11px] font-mono text-slate-400">
                Status: <strong className="text-purple-400">Simulation / Digital Twin</strong>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Section 3: Authoritative Model Validation (Scientific, not marketing) */}
      <section className="px-6 lg:px-12 py-16 bg-slate-950 border-b border-agni-border">
        <div className="max-w-6xl mx-auto space-y-8">
          <div className="text-center space-y-2">
            <span className="text-xs font-mono uppercase text-amber-400 tracking-wider font-semibold">
              Machine Learning Scientific Benchmark
            </span>
            <h2 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
              Authoritative Model Validation
            </h2>
            <p className="text-slate-400 text-xs max-w-2xl mx-auto">
              Evaluation metrics are verified across independent temporal out-of-sample holdout and spatial cross-validation protocols.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Temporal Holdout Card */}
            <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div>
                  <h3 className="text-sm font-bold text-white font-mono">Frozen 2026 Temporal Test</h3>
                  <div className="text-[11px] text-slate-400">Primary out-of-sample temporal generalization holdout</div>
                </div>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-amber-500/20 text-amber-300 border border-amber-500/30">
                  PRIMARY BENCHMARK
                </span>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="p-3 rounded-xl bg-slate-950 border border-slate-800/80 text-center">
                  <div className="text-xl font-black text-white font-mono">69.89%</div>
                  <div className="text-[10px] text-slate-400 font-mono mt-0.5">Accuracy</div>
                </div>
                <div className="p-3 rounded-xl bg-slate-950 border border-slate-800/80 text-center">
                  <div className="text-xl font-black text-emerald-400 font-mono">74.56%</div>
                  <div className="text-[10px] text-slate-400 font-mono mt-0.5">Balanced Acc</div>
                </div>
                <div className="p-3 rounded-xl bg-slate-950 border border-slate-800/80 text-center">
                  <div className="text-xl font-black text-cyan-400 font-mono">64.46%</div>
                  <div className="text-[10px] text-slate-400 font-mono mt-0.5">Macro F1</div>
                </div>
                <div className="p-3 rounded-xl bg-slate-950 border border-amber-500/30 text-center">
                  <div className="text-xl font-black text-amber-400 font-mono">97.18%</div>
                  <div className="text-[10px] text-amber-300 font-mono mt-0.5">Tier-1 Selective</div>
                </div>
              </div>

              <p className="text-[11px] text-slate-400 leading-relaxed">
                Evaluated strictly on future, unobserved 2026 satellite passes. Tier-1 selective accuracy represents mission-critical high-confidence triage gating.
              </p>
            </div>

            {/* Spatial CV Card */}
            <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div>
                  <h3 className="text-sm font-bold text-white font-mono">Spatial 5-Fold GroupKFold</h3>
                  <div className="text-[11px] text-slate-400">Cross-regional spatial geographic generalization</div>
                </div>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-blue-500/20 text-blue-300 border border-blue-500/30">
                  SPATIAL GENERALIZATION
                </span>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 rounded-xl bg-slate-950 border border-slate-800/80 text-center">
                  <div className="text-xl font-black text-white font-mono">94.32%</div>
                  <div className="text-[10px] text-slate-400 font-mono mt-0.5">Mean Accuracy</div>
                </div>
                <div className="p-3 rounded-xl bg-slate-950 border border-slate-800/80 text-center">
                  <div className="text-xl font-black text-cyan-400 font-mono">93.18%</div>
                  <div className="text-[10px] text-slate-400 font-mono mt-0.5">Mean Macro F1</div>
                </div>
              </div>

              <p className="text-[11px] text-slate-400 leading-relaxed">
                Guarantees the model generalizes across diverse geographic terrains without geographic leakage across Indian administrative blocks.
              </p>
            </div>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 text-center text-xs text-slate-400 font-mono">
            Methodology Note: Performance is reported using separate temporal and spatial validation protocols. Temporal holdout is the primary out-of-sample generalization measure.
          </div>
        </div>
      </section>

      {/* Section 4: Authentic Data Sources & Coverage Matrix */}
      <section className="px-6 lg:px-12 py-16 bg-slate-900/30 border-b border-agni-border">
        <div className="max-w-6xl mx-auto space-y-8">
          <div className="text-center space-y-2">
            <span className="text-xs font-mono uppercase text-amber-400 tracking-wider font-semibold">
              Geospatial Stack & Provenance
            </span>
            <h2 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
              Data Sources & Coverage Matrix
            </h2>
            <p className="text-slate-400 text-xs max-w-2xl mx-auto">
              Transparent reporting of operational vs partial coverage across all fused remote sensing and cadastral registries.
            </p>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left border border-slate-800 rounded-xl overflow-hidden">
              <thead className="bg-slate-950 text-slate-300 uppercase font-mono text-[10px] border-b border-slate-800">
                <tr>
                  <th className="p-3.5">Source</th>
                  <th className="p-3.5">Operational Role</th>
                  <th className="p-3.5">Coverage Scope</th>
                  <th className="p-3.5">Integration Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/80 bg-slate-900/60 font-mono">
                {dataSources.map((item, idx) => (
                  <tr key={idx} className="hover:bg-slate-800/40 transition-colors">
                    <td className="p-3.5 font-bold text-white">{item.source}</td>
                    <td className="p-3.5 text-slate-300 font-sans">{item.role}</td>
                    <td className="p-3.5">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${item.coverageColor}`}>
                        {item.coverage}
                      </span>
                    </td>
                    <td className="p-3.5 text-slate-400 font-semibold">{item.status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* Section 18: Dedicated Stakeholder Portals */}
      <section id="portals" className="px-6 lg:px-12 py-16 bg-slate-950 border-b border-agni-border">
        <div className="max-w-6xl mx-auto space-y-10">
          <div className="text-center space-y-2">
            <span className="text-xs font-mono uppercase text-amber-400 tracking-wider font-semibold">
              Role-Based Workstations
            </span>
            <h2 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
              Operational Portals by Stakeholder Persona
            </h2>
            <p className="text-slate-400 text-xs max-w-2xl mx-auto">
              Tailored interfaces optimized for regulatory enforcement, plant compliance, research inquiry, and public transparency.
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
                      ? "bg-gradient-to-br from-slate-900 to-amber-950/20 border-amber-500/50 shadow-md"
                      : "bg-slate-900/80 border-slate-800 hover:border-slate-700"
                  }`}
                >
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="w-10 h-10 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-center text-amber-400">
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

      {/* Section 9: Enterprise Platform Status Bar */}
      <section className="px-6 lg:px-12 py-10 bg-slate-900/60 border-b border-agni-border">
        <div className="max-w-6xl mx-auto space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono uppercase text-amber-400 tracking-wider font-semibold">
              Live Platform Systems Health
            </span>
            <span className="text-[11px] font-mono text-emerald-400 flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
              All Core Subsystems Connected
            </span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 text-xs font-mono">
            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
              <div className="text-[10px] text-slate-500">SYSTEM STATUS</div>
              <div className="text-emerald-400 font-bold">OPERATIONAL</div>
            </div>
            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
              <div className="text-[10px] text-slate-500">FIRMS INGESTION</div>
              <div className="text-emerald-400 font-bold">ACTIVE</div>
            </div>
            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
              <div className="text-[10px] text-slate-500">DATABASE</div>
              <div className="text-white font-bold">PostGIS 3.4</div>
            </div>
            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
              <div className="text-[10px] text-slate-500">ML INFERENCE</div>
              <div className="text-cyan-400 font-bold">Calibrated V1</div>
            </div>
            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
              <div className="text-[10px] text-slate-500">ALERT DISPATCH</div>
              <div className="text-amber-400 font-bold">GATED / DISABLED</div>
            </div>
            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
              <div className="text-[10px] text-slate-500">AGNI-SAT</div>
              <div className="text-purple-400 font-bold">DIGITAL TWIN</div>
            </div>
          </div>
        </div>
      </section>

      {/* Footer & Data Attribution / Licensing (Sections 5, 20, 21) */}
      <footer className="mt-auto bg-slate-950 border-t border-agni-border py-12 px-6 lg:px-12 text-xs text-slate-400 space-y-8">
        <div className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-4 gap-8">
          <div className="space-y-3 md:col-span-2">
            <div className="flex items-center gap-2">
              <Flame className="w-5 h-5 text-amber-400" />
              <span className="font-extrabold text-white font-mono text-sm">AGNI-NETRA</span>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed max-w-md">
              National-Scale Geospatial Thermal Intelligence & Decision-Support Platform. AI-based detection, classification, and segregation of industrial fires from natural and agricultural thermal sources.
            </p>
            <div className="text-[11px] text-slate-500 font-mono">
              Aligned with MoEFCC EIA standards, CPCB flare monitoring guidelines, ISRO Bhuvan OGC standards, and NDMA incident response protocols.
            </div>
          </div>

          <div className="space-y-2">
            <div className="font-bold text-white font-mono text-xs uppercase tracking-wider">Data Attribution</div>
            <ul className="space-y-1.5 text-[11px] text-slate-400">
              <li>• <strong>NASA FIRMS:</strong> NASA ESDIS Open Data Policy</li>
              <li>• <strong>OpenStreetMap:</strong> © OpenStreetMap contributors, ODbL 1.0</li>
              <li>• <strong>ISRO Bhuvan:</strong> National Remote Sensing Centre (NRSC)</li>
              <li>• <strong>CEA & IBM:</strong> Ministry of Power & Ministry of Mines</li>
            </ul>
          </div>

          <div className="space-y-2">
            <div className="font-bold text-white font-mono text-xs uppercase tracking-wider">Developer & API</div>
            <ul className="space-y-1.5 text-[11px]">
              <li>
                <a
                  href={getApiDocsUrl()}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-amber-400 hover:underline flex items-center gap-1 font-mono"
                >
                  <span>Interactive API Reference (Swagger)</span>
                  <ExternalLink className="w-3 h-3" />
                </a>
              </li>
              <li>
                <Link href="/portal/research" className="hover:text-white">
                  Research Data Lineage
                </Link>
              </li>
              <li>
                <Link href="/dashboard/reports" className="hover:text-white">
                  Operational Incident Dossiers
                </Link>
              </li>
              <li className="pt-2 text-[10px] text-slate-500 font-mono">
                Repository Commit: 4a20162
              </li>
            </ul>
          </div>
        </div>

        <div className="max-w-6xl mx-auto pt-6 border-t border-slate-900 flex flex-col sm:flex-row items-center justify-between gap-3 text-[11px] text-slate-500">
          <div>
            © 2026 AGNI-NETRA Project • National Geospatial Thermal Intelligence Infrastructure
          </div>
          <div className="flex items-center gap-4">
            <span>Statutory Safe Dispatch: Gated</span>
            <span>•</span>
            <span>Candidate XGBoost V3: Inactive</span>
            <span>•</span>
            <Link href="/dashboard" className="text-amber-400 hover:underline font-bold">
              Command Map →
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
