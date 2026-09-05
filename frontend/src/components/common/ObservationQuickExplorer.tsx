"use client";

import React, { useState } from "react";
import Link from "next/link";
import { 
  Flame, MapPin, Factory, ShieldCheck, 
  ExternalLink, Layers, ArrowUpRight, Clock,
  Cpu, Activity, CheckCircle2, ChevronRight, Zap
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

const SAMPLE_OBSERVATIONS: SampleObservation[] = [
  {
    id: "EVT-20260905-GUJ01",
    code: "EVT-GUJ-JAM-0842",
    name: "Petrochemical Refining Complex",
    sector: "Oil Refining & Hydrocarbon Processing",
    state: "Gujarat",
    district: "Jamnagar",
    coords: "22.4715° N, 69.8320° E",
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
    id: "EVT-20260904-MAH02",
    code: "EVT-MAH-TRO-1109",
    name: "Thermal Power Station & Utility Stack",
    sector: "Central Electricity Authority (CEA) Power Grid",
    state: "Maharashtra",
    district: "Mumbai Suburban",
    coords: "19.0028° N, 72.8942° E",
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
    id: "EVT-20260902-ODI03",
    code: "EVT-ODI-ANG-3901",
    name: "Integrated Metallurgical Smelter Complex",
    sector: "Steel & Primary Metals Manufacturing",
    state: "Odisha",
    district: "Angul",
    coords: "20.8350° N, 85.1520° E",
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
    id: "EVT-20260829-CHH04",
    code: "EVT-CHH-KOR-5520",
    name: "Open-Cast Coal Seam Mine",
    sector: "Indian Bureau of Mines (IBM) Leasehold",
    state: "Chhattisgarh",
    district: "Korba",
    coords: "22.3595° N, 82.7501° E",
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
  const current = SAMPLE_OBSERVATIONS[selectedIdx];

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
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-400 animate-pulse"></span>
            <span className="text-xs font-mono uppercase text-amber-400 font-bold tracking-wider">
              INTERACTIVE GEOSPATIAL EXPLORER
            </span>
            <span className="px-2 py-0.5 rounded-full bg-purple-500/20 border border-purple-500/30 text-purple-300 text-[10px] font-mono font-bold">
              REFERENCE OBSERVATION / FIELD BENCHMARK
            </span>
          </div>
          <h2 className="text-xl sm:text-2xl font-extrabold text-white mt-1">
            Real-World Observation Inspection Dossier
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Select an authoritative reference observation to inspect how AGNI-NETRA combines raw remote sensing telemetry with PostGIS cadastre spatial enrichment and calibrated ML inference.
          </p>
        </div>

        <Link
          href="/dashboard"
          className="self-start sm:self-auto px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700 text-xs font-mono font-bold flex items-center gap-1.5 transition-colors"
        >
          <span>Open Tactical Map</span>
          <ArrowUpRight className="w-3.5 h-3.5" />
        </Link>
      </div>

      {/* Observation Selector Tabs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-2.5">
        {SAMPLE_OBSERVATIONS.map((obs, idx) => {
          const isSelected = idx === selectedIdx;
          return (
            <button
              key={obs.id}
              onClick={() => setSelectedIdx(idx)}
              className={`p-3 rounded-xl border text-left transition-all ${
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
              <span className="text-[10px] font-mono text-slate-500 uppercase">EVENT CODE</span>
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
                Geographic Anchor:
              </span>
              <span className="font-mono font-bold text-white">{current.district}, {current.state}</span>
            </div>
            <div className="flex items-center justify-between text-xs font-mono">
              <span className="text-slate-500">WGS84 Coordinates:</span>
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
              Intelligence Brief & Physical Interpretation
            </div>
            <p>{current.summary}</p>
          </div>

          {/* Bottom Action Dock with Cross-Navigation */}
          <div className="pt-2 border-t border-slate-800 flex flex-wrap items-center justify-between gap-3">
            <span className="text-[11px] font-mono text-slate-400">
              Target Asset: <strong className="text-white">{current.nearestAsset}</strong>
            </span>
            <div className="flex items-center gap-2">
              <Link
                href={`/dashboard?lat=${current.lat}&lon=${current.lon}&state=${encodeURIComponent(current.state)}`}
                className="px-3 py-1.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-amber-400 border border-slate-700 text-xs font-mono font-bold flex items-center gap-1 transition-colors"
              >
                <span>Fly on Map</span>
                <ArrowUpRight className="w-3.5 h-3.5" />
              </Link>
              <Link
                href={`/dashboard/baselines?state=${encodeURIComponent(current.state)}`}
                className="px-3 py-1.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-700 text-xs font-mono font-bold flex items-center gap-1 transition-colors"
              >
                <span>Historical Baseline</span>
              </Link>
              <Link
                href={`/dashboard/events?state=${encodeURIComponent(current.state)}`}
                className="px-3.5 py-1.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-mono font-bold text-xs flex items-center gap-1 transition-colors shadow-md"
              >
                <span>Events in {current.state}</span>
                <ChevronRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
