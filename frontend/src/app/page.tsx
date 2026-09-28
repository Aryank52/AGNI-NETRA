"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  Flame, ShieldAlert, Cpu, ArrowRight,
  Map, Globe, Eye, Zap, Radio, Database,
  Activity, ShieldCheck, ChevronRight, Sparkles
} from "lucide-react";
import AgniNetraLogo from "@/components/common/AgniNetraLogo";

export default function LandingPage() {
  const [selectedDemoIdx, setSelectedDemoIdx] = useState(0);

  const demoScenarios = [
    {
      title: "Industrial Petrochemical Complex",
      location: "Jamnagar District, Gujarat",
      signal: "165.2 MW Fire Radiative Power (VIIRS 375m)",
      riskLevel: "HIGH RISK",
      riskColor: "text-amber-400 bg-amber-500/10 border-amber-500/30",
      summary: "High-temperature thermal anomaly detected within registered refining perimeter. Baseline deviation indicates active flaring stack.",
    },
    {
      title: "Forest Canopy Hotspot Cluster",
      location: "Similipal Tiger Reserve, Odisha",
      signal: "84.7 MW Fire Radiative Power (MODIS 1km)",
      riskLevel: "CRITICAL RISK",
      riskColor: "text-red-400 bg-red-500/10 border-red-500/30",
      summary: "Rapid thermal surge detected in dry deciduous woodland. Proximity to protected wildlife corridor warrants immediate verification.",
    },
    {
      title: "Thermal Power Station Flue",
      location: "Singrauli Region, Madhya Pradesh",
      signal: "210.4 MW Radiative Output (VIIRS 375m)",
      riskLevel: "MODERATE RISK",
      riskColor: "text-cyan-400 bg-cyan-500/10 border-cyan-500/30",
      summary: "Steady baseline thermal emissions matching licensed generation units with no downwind civilian boundary infringement.",
    },
  ];

  const activeDemo = demoScenarios[selectedDemoIdx];

  const productValues = [
    {
      step: "01",
      name: "OBSERVE",
      headline: "Monitor thermal activity.",
      description: "Continuous spaceborne sweeps scan vast geographies, capturing heat signatures and infrared radiometry at sub-kilometer resolution.",
      icon: Eye,
      border: "hover:border-amber-500/40",
      badgeColor: "text-amber-400 bg-amber-500/10 border-amber-500/30",
    },
    {
      step: "02",
      name: "ANALYZE",
      headline: "Turn thermal observations into intelligence.",
      description: "Automated causal reasoning cross-references satellite detections against historical baselines, terrain features, and industrial infrastructure.",
      icon: Cpu,
      border: "hover:border-cyan-500/40",
      badgeColor: "text-cyan-400 bg-cyan-500/10 border-cyan-500/30",
    },
    {
      step: "03",
      name: "RESPOND",
      headline: "Provide actionable situational awareness.",
      description: "Deliver targeted operational intelligence to authorized responders, enabling coordinated containment and decisive public safety precautions.",
      icon: ShieldAlert,
      border: "hover:border-emerald-500/40",
      badgeColor: "text-emerald-400 bg-emerald-500/10 border-emerald-500/30",
    },
  ];

  const portals = [
    {
      role: "ANALYST",
      title: "Analyst Workspace",
      desc: "Operational intelligence, live telemetry sweeps, and anomaly investigation.",
      icon: Activity,
      href: "/login",
      btnText: "Enter Analyst",
      badgeColor: "text-cyan-400 bg-cyan-500/10 border-cyan-500/30",
      btnClass: "bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-300 border border-cyan-500/40",
    },
    {
      role: "AGENCY",
      title: "Agency Workspace",
      desc: "Response-oriented situational intelligence, triage alerts, and containment coordination.",
      icon: ShieldAlert,
      href: "/login",
      btnText: "Enter Agency",
      badgeColor: "text-rose-400 bg-rose-500/10 border-rose-500/30",
      btnClass: "bg-rose-500/20 hover:bg-rose-500/30 text-rose-300 border border-rose-500/40",
    },
    {
      role: "PUBLIC",
      title: "Public Portal",
      desc: "Public safety advisories, regional hazard indicators, and community guidance.",
      icon: Globe,
      href: "/login",
      btnText: "Enter Public",
      badgeColor: "text-emerald-400 bg-emerald-500/10 border-emerald-500/30",
      btnClass: "bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 border border-emerald-500/40",
    },
  ];

  return (
    <div className="min-h-screen bg-agni-navy text-slate-100 flex flex-col selection:bg-amber-500 selection:text-slate-950 font-sans">
      {/* NAVBAR */}
      <header className="h-16 border-b border-agni-border px-4 lg:px-10 flex items-center justify-between backdrop-blur-md bg-slate-950/90 sticky top-0 z-40">
        <div className="flex items-center gap-6">
          <Link href="/" className="inline-block transition-transform hover:scale-105">
            <AgniNetraLogo size={34} subtext="NATIONAL GEOSPATIAL INTELLIGENCE" />
          </Link>
          <span className="py-0.5 px-2 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-400 font-mono text-[10px] font-bold tracking-widest uppercase hidden sm:inline-flex items-center gap-1">
            <Sparkles className="w-2.5 h-2.5" />
            PROTOTYPE
          </span>
        </div>

        <nav className="hidden md:flex items-center gap-6 text-xs font-mono text-slate-400">
          <a href="#hero" className="hover:text-amber-400 transition-colors">Home</a>
          <a href="#product" className="hover:text-amber-400 transition-colors">How It Works</a>
          <a href="#portals" className="hover:text-amber-400 transition-colors">Workspaces</a>
        </nav>

        <div className="flex items-center gap-3 font-mono text-xs">
          <Link
            href="/login"
            className="px-3.5 py-1.5 rounded-xl bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-600 hover:to-orange-700 text-slate-950 font-extrabold shadow-sm transition flex items-center gap-1.5"
          >
            <span>Enter Prototype</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </header>

      {/* HERO SECTION */}
      <section id="hero" className="relative px-4 lg:px-10 pt-20 pb-16 max-w-5xl mx-auto text-center space-y-6">
        {/* Prototype Header Badge */}
        <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-slate-900 border border-slate-700 text-[11px] font-mono text-slate-300">
          <span className="font-bold text-white tracking-wider">AGNI-NETRA</span>
          <span className="text-slate-600">|</span>
          <span className="text-amber-400 font-bold uppercase tracking-widest text-[10px] flex items-center gap-1">
            <Sparkles className="w-3 h-3 text-amber-400" />
            PROTOTYPE
          </span>
        </div>

        {/* Primary Heading */}
        <h1 className="text-4xl sm:text-6xl font-black tracking-tight text-white leading-tight">
          See thermal risk <br className="hidden sm:inline" />
          <span className="bg-gradient-to-r from-amber-400 via-orange-500 to-amber-200 bg-clip-text text-transparent">
            before it becomes a crisis.
          </span>
        </h1>

        {/* Short Description */}
        <p className="max-w-2xl mx-auto text-sm sm:text-base text-slate-300 font-normal leading-relaxed">
          Satellite-powered geospatial intelligence for wildfire and industrial thermal risk monitoring.
        </p>

        {/* Primary and Secondary CTA */}
        <div className="flex flex-col sm:row items-center justify-center gap-3.5 pt-2">
          <a
            href="#product"
            className="w-full sm:w-auto px-7 py-3 rounded-xl bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-600 hover:to-orange-700 text-slate-950 font-extrabold text-xs tracking-wider font-mono shadow-lg shadow-amber-500/20 flex items-center justify-center gap-2 transition-all hover:scale-105 cursor-pointer"
          >
            <span>Explore AGNI-NETRA</span>
            <ChevronRight className="w-4 h-4" />
          </a>
          <Link
            href="/login"
            className="w-full sm:w-auto px-7 py-3 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-200 font-semibold text-xs tracking-wider font-mono transition-all flex items-center justify-center gap-2 cursor-pointer"
          >
            <span>Enter Prototype</span>
            <ArrowRight className="w-4 h-4 text-amber-400" />
          </Link>
        </div>
      </section>

      {/* THREE SIMPLE PRODUCT CARDS (OBSERVE, ANALYZE, RESPOND) */}
      <section id="product" className="px-4 lg:px-10 py-16 bg-slate-950/80 border-y border-agni-border">
        <div className="max-w-5xl mx-auto space-y-10">
          <div className="text-center space-y-1.5">
            <span className="text-xs font-mono uppercase text-amber-400 tracking-wider font-semibold">
              Operational Intelligence Cycle
            </span>
            <h2 className="text-2xl sm:text-3xl font-extrabold text-white">
              From Observation to Timely Action
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {productValues.map((card) => {
              const Icon = card.icon;
              return (
                <div
                  key={card.step}
                  className={`p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4 transition ${card.border}`}
                >
                  <div className="flex items-center justify-between">
                    <span className={`text-[10px] font-mono px-2 py-0.5 rounded border font-bold ${card.badgeColor}`}>
                      {card.name}
                    </span>
                    <span className="font-mono text-xl font-black text-slate-600">
                      {card.step}
                    </span>
                  </div>
                  <h3 className="text-base font-bold text-white leading-snug">
                    {card.headline}
                  </h3>
                  <p className="text-xs text-slate-400 leading-relaxed">
                    {card.description}
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* PORTALS SECTION (CHOOSE YOUR WORKSPACE) */}
      <section id="portals" className="px-4 lg:px-10 py-16 bg-slate-900/40 border-b border-agni-border">
        <div className="max-w-5xl mx-auto space-y-10">
          <div className="text-center space-y-1.5">
            <span className="text-xs font-mono uppercase text-amber-400 tracking-wider font-semibold">
              Workspaces
            </span>
            <h2 className="text-2xl sm:text-3xl font-extrabold text-white">
              Choose Your Workspace
            </h2>
            <p className="text-xs text-slate-400 max-w-md mx-auto">
              Dedicated prototype gateways purpose-built for operational analysts, response agencies, and public citizens.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {portals.map((portal) => {
              const Icon = portal.icon;
              return (
                <div
                  key={portal.role}
                  className="p-6 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-4 flex flex-col justify-between hover:border-slate-700 transition shadow-lg"
                >
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="p-2.5 rounded-xl bg-slate-800 border border-slate-700">
                        <Icon className="w-5 h-5 text-amber-400" />
                      </div>
                      <span className={`text-[9px] font-mono font-bold px-2 py-0.5 rounded border ${portal.badgeColor}`}>
                        {portal.role}
                      </span>
                    </div>
                    <h3 className="text-base font-bold text-white">{portal.title}</h3>
                    <p className="text-xs text-slate-400 leading-relaxed">{portal.desc}</p>
                  </div>

                  {/* Every main portal CTA points to /login */}
                  <Link
                    href={portal.href}
                    className={`w-full py-2.5 px-4 rounded-xl text-xs font-bold font-mono transition flex items-center justify-between ${portal.btnClass}`}
                  >
                    <span>{portal.btnText}</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </Link>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* INTERACTIVE DEMONSTRATION SECTION */}
      <section id="demo" className="px-4 lg:px-10 py-16 bg-slate-950/90 border-b border-agni-border">
        <div className="max-w-4xl mx-auto space-y-8">
          <div className="text-center space-y-2">
            <span className="text-xs font-mono uppercase text-amber-400 tracking-wider font-semibold">
              Interactive Preview
            </span>
            <h2 className="text-2xl sm:text-3xl font-extrabold text-white">
              Synthetic Thermal Telemetry Inspection
            </h2>
            <div className="pt-1 flex justify-center">
              <span className="inline-flex items-center gap-1.5 py-1 px-3 rounded-full bg-slate-900 border border-slate-700 text-slate-400 font-mono text-[10px] font-bold tracking-wider">
                SYNTHETIC DEMONSTRATION — NOT LIVE OPERATIONAL DATA
              </span>
            </div>
          </div>

          <div className="flex flex-wrap items-center justify-center gap-2">
            {demoScenarios.map((sc, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => setSelectedDemoIdx(idx)}
                className={`py-1.5 px-3.5 rounded-lg text-xs font-mono transition cursor-pointer ${
                  selectedDemoIdx === idx
                    ? "bg-amber-500/20 text-amber-300 border border-amber-500/40 font-bold"
                    : "bg-slate-900 text-slate-400 border border-slate-800 hover:text-white"
                }`}
              >
                Scenario 0{idx + 1}
              </button>
            ))}
          </div>

          <div className="p-6 rounded-2xl bg-slate-900/90 border border-slate-800 shadow-xl space-y-5">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
              <div>
                <span className="text-[10px] font-mono text-slate-500 uppercase">Scenario</span>
                <h3 className="text-base font-bold text-white">{activeDemo.title}</h3>
              </div>
              <span className={`text-[10px] font-mono font-bold px-2.5 py-1 rounded-md border w-fit ${activeDemo.riskColor}`}>
                {activeDemo.riskLevel}
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs font-mono">
              <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 space-y-1">
                <span className="text-[10px] text-slate-500 uppercase">Location</span>
                <div className="text-slate-200 font-sans font-medium">{activeDemo.location}</div>
              </div>

              <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 space-y-1">
                <span className="text-[10px] text-slate-500 uppercase">Thermal Signal</span>
                <div className="text-amber-400 font-sans font-medium">{activeDemo.signal}</div>
              </div>
            </div>

            <div className="space-y-1.5">
              <span className="text-[10px] font-mono text-slate-500 uppercase">Intelligence Summary</span>
              <p className="text-xs text-slate-300 leading-relaxed font-sans">
                {activeDemo.summary}
              </p>
            </div>

            <div className="pt-2 flex justify-end">
              <Link
                href="/login"
                className="py-2 px-4 rounded-xl bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 border border-amber-500/40 text-xs font-mono font-bold transition flex items-center gap-1.5"
              >
                <span>Launch Prototype</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* FOOTER */}
      <footer className="border-t border-agni-border bg-slate-950 px-4 lg:px-10 py-8 text-xs text-slate-500 font-mono">
        <div className="max-w-5xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="space-y-1 text-center sm:text-left">
            <div className="text-slate-300 font-bold flex items-center gap-2">
              <span>AGNI-NETRA</span>
              <span className="text-[9px] text-amber-400 border border-amber-500/30 bg-amber-500/10 px-1.5 py-0.5 rounded">
                PROTOTYPE
              </span>
            </div>
            <div className="text-[11px] text-slate-500">Geospatial Thermal Intelligence</div>
          </div>

          <div className="flex items-center gap-5 text-slate-400 text-xs">
            <a href="#product" className="hover:text-amber-400 transition-colors">How It Works</a>
            <a href="#portals" className="hover:text-amber-400 transition-colors">Portals</a>
            <Link href="/login" className="hover:text-amber-400 transition-colors">Sign In</Link>
            <Link href="/register" className="hover:text-amber-400 transition-colors">Register</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
