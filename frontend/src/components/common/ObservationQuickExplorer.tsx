"use client";

import React, { useState } from "react";
import Link from "next/link";
import { 
  Flame, MapPin, Factory, ShieldCheck, 
  ExternalLink, Layers, ArrowRight, Clock,
  Cpu, Activity, CheckCircle2, ChevronRight, Zap,
  AlertTriangle, Lock, ShieldAlert
} from "lucide-react";

interface SampleObservation {
  id: string;
  code: string;
  name: string;
  sector: string;
  state: string;
  district: string;
  coords: string;
  lat: number;
  lon: number;
  satellite: string;
  peakFrp: number;
  brightness: number;
  mlClass: string;
  confidence: number;
  riskLevel: "CRITICAL" | "HIGH" | "MODERATE" | "LOW";
  riskScore: number;
  nearestAsset: string;
  distToAsset: number;
  distToSettlement: number;
  dayNightRatio: string;
  baselineDeviation: string;
  summary: string;
}

const SYNTHETIC_DEMO_SCENARIOS: SampleObservation[] = [
  {
    id: "SYN-GUJ-01",
    code: "SYN-GUJ-JAM-0842",
    name: "Petrochemical Refining Complex",
    sector: "Oil Refining & Hydrocarbon Processing",
    state: "Gujarat",
    district: "Jamnagar Region",
    coords: "22.4715° N, 69.8320° E [SYNTHETIC]",
    lat: 22.4715,
    lon: 69.8320,
    satellite: "VIIRS NOAA-20 (375m)",
    peakFrp: 165.2,
    brightness: 367.4,
    mlClass: "Industrial Kiln / Flare",
    confidence: 0.992,
    riskLevel: "HIGH",
    riskScore: 78.4,
    nearestAsset: "Petroleum Refining Cadastre",
    distToAsset: 142,
    distToSettlement: 3100,
    dayNightRatio: "0.94x (24x7 Continuity)",
    baselineDeviation: "+2.8σ Elevated Surge",
    summary: "High-temperature elevated thermal signature matching regulated flaring stacks within the industrial perimeter. Close proximity to hydrocarbon processing cadastre."
  },
  {
    id: "SYN-MAH-02",
    code: "SYN-MAH-TRO-1109",
    name: "Thermal Power Station & Utility Stack",
    sector: "Central Electricity Authority (CEA) Power Grid",
    state: "Maharashtra",
    district: "Mumbai Suburban",
    coords: "19.0028° N, 72.8942° E [SYNTHETIC]",
    lat: 19.0028,
    lon: 72.8942,
    satellite: "VIIRS Suomi-NPP (375m)",
    peakFrp: 92.6,
    brightness: 348.1,
    mlClass: "Power Plant Emission",
    confidence: 0.984,
    riskLevel: "MODERATE",
    riskScore: 54.2,
    nearestAsset: "CEA Utility Thermal Unit 5",
    distToAsset: 85,
    distToSettlement: 1850,
    dayNightRatio: "1.02x (Continuous Generation)",
    baselineDeviation: "+0.4σ Nominal Baseline",
    summary: "Consistent radiative thermal signature conforming to routine baseload power generation. Low baseline variance with established 4-year seasonal recurrence."
  },
  {
    id: "SYN-ODI-03",
    code: "SYN-ODI-ANG-3901",
    name: "Integrated Metallurgical Smelter Complex",
    sector: "Steel & Primary Metals Manufacturing",
    state: "Odisha",
    district: "Angul Region",
    coords: "20.8350° N, 85.1520° E [SYNTHETIC]",
    lat: 20.8350,
    lon: 85.1520,
    satellite: "MODIS Terra (1km)",
    peakFrp: 214.0,
    brightness: 382.5,
    mlClass: "Blast Furnace / Smelting",
    confidence: 0.976,
    riskLevel: "HIGH",
    riskScore: 74.8,
    nearestAsset: "Steel Melting Shop & Caster",
    distToAsset: 210,
    distToSettlement: 4200,
    dayNightRatio: "0.88x (Industrial Regime)",
    baselineDeviation: "+3.1σ Anomaly Spike",
    summary: "Acute radiant energy spike recorded during daytime satellite overpass. Validated against registered blast furnace cadastre with valid consent-to-operate clearance."
  },
  {
    id: "SYN-CHH-04",
    code: "SYN-CHH-KOR-5520",
    name: "Open-Cast Coal Seam Mine",
    sector: "Indian Bureau of Mines (IBM) Leasehold",
    state: "Chhattisgarh",
    district: "Korba Region",
    coords: "22.3595° N, 82.7501° E [SYNTHETIC]",
    lat: 22.3595,
    lon: 82.7501,
    satellite: "VIIRS NOAA-20 (375m)",
    peakFrp: 148.8,
    brightness: 356.2,
    mlClass: "Coal Seam / Mining Fire",
    confidence: 0.968,
    riskLevel: "CRITICAL",
    riskScore: 86.5,
    nearestAsset: "IBM Auctioned Coal Block #414",
    distToAsset: 120,
    distToSettlement: 980,
    dayNightRatio: "0.45x (Sub-surface Smoldering)",
    baselineDeviation: "+3.8σ Severe Outlier",
    summary: "Persistent abnormal heat accumulation situated 980m from local settlement boundaries within active open-pit leasehold. Flagged for Tier 1 analyst triage."
  }
];

export default function ObservationQuickExplorer() {
  const [selectedIdx, setSelectedIdx] = useState<number>(0);
  const current = SYNTHETIC_DEMO_SCENARIOS[selectedIdx];

  const getRiskBadge = (level: string) => {
    switch (level) {
      case "CRITICAL":
        return "bg-red-500/20 text-red-300 border-red-500/40";
      case "HIGH":
        return "bg-amber-500/20 text-amber-300 border-amber-500/40";
      case "MODERATE":
        return "bg-cyan-500/20 text-cyan-300 border-cyan-500/40";
      default:
        return "bg-emerald-500/20 text-emerald-300 border-emerald-500/40";
    }
  };

  return (
    <div className="w-full max-w-6xl mx-auto p-6 rounded-3xl bg-slate-900/90 border border-slate-800 shadow-2xl space-y-6">
      {/* Synthetic Demonstration Watermark / Banner */}
      <div className="p-3.5 rounded-2xl bg-amber-500/10 border border-amber-500/30 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <ShieldAlert className="w-5 h-5 text-amber-400 shrink-0" />
          <div className="space-y-0.5">
            <div className="text-xs font-mono font-black text-amber-300 tracking-wider">
              SYNTHETIC DEMONSTRATION — NOT LIVE OPERATIONAL DATA
            </div>
            <p className="text-[11px] text-slate-300">
              The scenarios below demonstrate AGNI-NETRA&apos;s analytical classification and reasoning capabilities using simulated spaceborne telemetry. Live satellite feeds, operational coordinates, and real-time dossiers require authenticated access.
            </p>
          </div>
        </div>

        <Link
          href="/login"
          className="shrink-0 px-3.5 py-1.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 text-xs font-mono font-bold flex items-center gap-1.5 transition-colors shadow-sm"
        >
          <Lock className="w-3.5 h-3.5" />
          <span>Sign In for Live Data</span>
        </Link>
      </div>

      {/* Observation Selector Tabs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-2.5">
        {SYNTHETIC_DEMO_SCENARIOS.map((obs, idx) => {
          const isSelected = idx === selectedIdx;
          return (
            <button
              key={obs.id}
              onClick={() => setSelectedIdx(idx)}
              className={`p-3 rounded-xl border text-left transition-all cursor-pointer ${
                isSelected
                  ? "bg-slate-800/90 border-amber-500/60 shadow-lg shadow-amber-500/10"
                  : "bg-slate-950/60 border-slate-800 hover:border-slate-700 hover:bg-slate-900/60"
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-mono text-slate-400 font-bold">
                  {obs.state}
                </span>
                <span className={`text-[9px] font-mono px-1.5 py-0.2 rounded border font-bold ${getRiskBadge(obs.riskLevel)}`}>
                  {obs.riskLevel}
                </span>
              </div>
              <div className="text-xs font-bold text-white truncate mt-1">{obs.name}</div>
              <div className="text-[11px] font-mono text-amber-400 mt-0.5">{obs.peakFrp} MW Peak</div>
            </button>
          );
        })}
      </div>

      {/* Observation Inspection Workspace */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Left Column: Spatial & Sensor Anchor (5 cols) */}
        <div className="lg:col-span-5 bg-slate-950/90 border border-slate-800/80 rounded-2xl p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div>
              <span className="text-[10px] font-mono text-slate-500 uppercase">SIMULATED EVENT ID</span>
              <div className="text-sm font-mono font-extrabold text-amber-400">{current.code}</div>
            </div>
            <div className="text-right">
              <span className="text-[10px] font-mono text-slate-500 uppercase">SENSOR PLATFORM</span>
              <div className="text-xs font-mono text-slate-300">{current.satellite}</div>
            </div>
          </div>

          {/* Coordinates & Location Card */}
          <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 space-y-2">
            <div className="flex items-center justify-between text-xs">
              <span className="text-slate-400 flex items-center gap-1.5 font-medium">
                <MapPin className="w-3.5 h-3.5 text-amber-400" />
                Regional Anchor:
              </span>
              <span className="font-mono font-bold text-white">{current.district}, {current.state}</span>
            </div>
            <div className="flex items-center justify-between text-xs font-mono">
              <span className="text-slate-500">Spatial Telemetry:</span>
              <span className="text-amber-400 font-bold">{current.coords}</span>
            </div>
            <div className="flex items-center justify-between text-xs font-mono">
              <span className="text-slate-500">Cadastre Proximity:</span>
              <span className="text-cyan-400 font-bold">{current.distToAsset}m to Plant</span>
            </div>
            <div className="flex items-center justify-between text-xs font-mono">
              <span className="text-slate-500">Settlement Buffer:</span>
              <span className="text-slate-300 font-bold">{current.distToSettlement}m Distance</span>
            </div>
          </div>

          {/* Physical Radiative Telemetry */}
          <div className="grid grid-cols-2 gap-3 font-mono text-center">
            <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
              <div className="text-[10px] text-slate-500 uppercase">FIRE RADIATIVE POWER</div>
              <div className="text-lg font-black text-orange-400 mt-0.5">{current.peakFrp} MW</div>
              <div className="text-[10px] text-slate-400">Peak Overpass FRP</div>
            </div>
            <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
              <div className="text-[10px] text-slate-500 uppercase">4µm BRIGHTNESS</div>
              <div className="text-lg font-black text-amber-300 mt-0.5">{current.brightness} K</div>
              <div className="text-[10px] text-slate-400">Planck Radiative Temp</div>
            </div>
          </div>
        </div>

        {/* Right Column: ML Inference, Risk Decomposition & Summary (7 cols) */}
        <div className="lg:col-span-7 bg-slate-950/90 border border-slate-800/80 rounded-2xl p-5 space-y-4">
          {/* Top Classification Row */}
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
            <div>
              <div className="flex items-center gap-2">
                <Cpu className="w-4 h-4 text-indigo-400" />
                <span className="text-xs font-mono text-slate-400 uppercase font-bold">ML CLASSIFICATION</span>
              </div>
              <div className="text-base font-extrabold text-white mt-0.5">{current.mlClass}</div>
            </div>

            <div className="text-right">
              <span className="text-[10px] font-mono text-slate-500 uppercase">CALIBRATED CONFIDENCE</span>
              <div className="text-base font-mono font-extrabold text-emerald-400">
                {(current.confidence * 100).toFixed(1)}% (Platt-Calibrated)
              </div>
            </div>
          </div>

          {/* Multi-Factor Evidence Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5 font-mono text-xs">
            <div className="p-2.5 rounded-xl bg-slate-900 border border-slate-800">
              <div className="text-[10px] text-slate-500 uppercase">TEMPORAL CONTINUITY</div>
              <div className="text-slate-200 font-bold mt-0.5">{current.dayNightRatio}</div>
            </div>
            <div className="p-2.5 rounded-xl bg-slate-900 border border-slate-800">
              <div className="text-[10px] text-slate-500 uppercase">BASELINE SURGE</div>
              <div className="text-amber-400 font-bold mt-0.5">{current.baselineDeviation}</div>
            </div>
            <div className="p-2.5 rounded-xl bg-slate-900 border border-slate-800">
              <div className="text-[10px] text-slate-500 uppercase">DETERMINISTIC RISK</div>
              <div className="text-red-400 font-bold mt-0.5">{current.riskScore}/100 ({current.riskLevel})</div>
            </div>
          </div>

          {/* Analyst Summary Narrative */}
          <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 text-xs text-slate-300 leading-relaxed space-y-1.5">
            <div className="text-[10px] font-mono uppercase text-slate-400 font-bold flex items-center gap-1.5">
              <Activity className="w-3.5 h-3.5 text-cyan-400" />
              Simulated Intelligence Brief & Physical Interpretation
            </div>
            <p>{current.summary}</p>
          </div>

          {/* Bottom Action Dock with Gated Navigation */}
          <div className="pt-2 border-t border-slate-800 flex flex-wrap items-center justify-between gap-3">
            <span className="text-[11px] font-mono text-slate-400">
              Cadastre Target: <strong className="text-white">{current.nearestAsset}</strong>
            </span>
            <div className="flex items-center gap-2">
              <Link
                href="/login?redirect=/dashboard"
                className="px-3.5 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-amber-400 border border-amber-500/30 text-xs font-mono font-bold flex items-center gap-1.5 transition-colors"
              >
                <Lock className="w-3 h-3 text-amber-400" />
                <span>Verify in Command Center</span>
              </Link>
              <Link
                href="/register"
                className="px-3.5 py-1.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-700 text-xs font-mono font-bold flex items-center gap-1 transition-colors"
              >
                <span>Request Clearance</span>
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
