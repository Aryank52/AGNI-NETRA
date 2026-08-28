"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import Header from "@/components/layout/Header";
import Sidebar from "@/components/layout/Sidebar";
import { fetchApi } from "@/lib/api";
import { 
  Globe, Flame, Layers, MapPin, Activity, 
  BarChart2, RefreshCw, Compass, ArrowUpRight,
  Shield, Sliders, Radio, Sparkles
} from "lucide-react";

interface StateDensity {
  state: string;
  total_events: number;
  total_frp: number;
  persistent_count: number;
  critical_count: number;
  primary_industry: string;
}

const STATE_ATLAS_DATA: StateDensity[] = [
  {
    state: "Gujarat",
    total_events: 28,
    total_frp: 3420.5,
    persistent_count: 6,
    critical_count: 2,
    primary_industry: "Petrochemicals & Refineries (Jamnagar, Dahej, Hazira)"
  },
  {
    state: "Odisha",
    total_events: 24,
    total_frp: 2890.0,
    persistent_count: 5,
    critical_count: 1,
    primary_industry: "Integrated Steel & Smelters (Angul, Jharsuguda, Kalinganagar)"
  },
  {
    state: "Chhattisgarh",
    total_events: 19,
    total_frp: 2150.4,
    persistent_count: 4,
    critical_count: 1,
    primary_industry: "Thermal Power & Coal Mining (Korba, Bilaspur)"
  },
  {
    state: "Madhya Pradesh",
    total_events: 16,
    total_frp: 1840.2,
    persistent_count: 3,
    critical_count: 1,
    primary_industry: "Super Thermal Power Utilities (Singrauli Belt)"
  },
  {
    state: "Jharkhand",
    total_events: 15,
    total_frp: 1620.8,
    persistent_count: 3,
    critical_count: 0,
    primary_industry: "Steel & Coking Coal (Jamshedpur, Bokaro, Dhanbad)"
  },
  {
    state: "Andhra Pradesh",
    total_events: 11,
    total_frp: 1120.0,
    persistent_count: 2,
    critical_count: 0,
    primary_industry: "Gas Processing & Power (KG Basin, Tatipaka, Vizag)"
  },
  {
    state: "Punjab",
    total_events: 14,
    total_frp: 890.5,
    persistent_count: 1,
    critical_count: 0,
    primary_industry: "Refineries (Bathinda) & Seasonal Agricultural Residue"
  }
];

export default function IndiaThermalAtlasPage() {
  const [selectedState, setSelectedState] = useState<string>("ALL");
  const [activeTab, setActiveTab] = useState<"DENSITY" | "PERSISTENT" | "EMERGING">("DENSITY");

  const filteredStates = STATE_ATLAS_DATA.filter((s) => {
    if (selectedState === "ALL") return true;
    return s.state.toLowerCase() === selectedState.toLowerCase();
  });

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
                <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30 font-bold">
                  NATIONAL GEOSPATIAL SPATIAL CLIMATOLOGY
                </span>
                <span className="text-xs text-slate-400">Multi-Year Satellite Thermal Climatology</span>
              </div>
              <h1 className="text-xl sm:text-2xl font-extrabold text-white flex items-center gap-2.5 mt-1">
                <Globe className="w-6 h-6 text-amber-400" />
                India Industrial Thermal Atlas
              </h1>
              <p className="text-xs text-slate-400 mt-1">
                Spatial density, persistent industrial combustion belts, and emerging uncataloged emitters across Indian states.
              </p>
            </div>

            <div className="flex items-center gap-2">
              <select
                value={selectedState}
                onChange={(e) => setSelectedState(e.target.value)}
                className="p-2 rounded-xl bg-slate-900 border border-slate-700 text-white font-medium text-xs focus:outline-none focus:border-amber-500"
              >
                <option value="ALL">All India (National Atlas)</option>
                {STATE_ATLAS_DATA.map((s) => (
                  <option key={s.state} value={s.state}>{s.state}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Atlas View Tabs */}
          <div className="flex items-center gap-2 border-b border-slate-800 pb-2 text-xs font-semibold">
            <button
              onClick={() => setActiveTab("DENSITY")}
              className={`px-3.5 py-1.5 rounded-xl transition-all ${
                activeTab === "DENSITY"
                  ? "bg-amber-500 text-slate-950 font-bold"
                  : "bg-slate-850 text-slate-400 hover:text-white"
              }`}
            >
              State Thermal Density
            </button>
            <button
              onClick={() => setActiveTab("PERSISTENT")}
              className={`px-3.5 py-1.5 rounded-xl transition-all ${
                activeTab === "PERSISTENT"
                  ? "bg-amber-500 text-slate-950 font-bold"
                  : "bg-slate-850 text-slate-400 hover:text-white"
              }`}
            >
              Persistent Industrial Belts
            </button>
            <button
              onClick={() => setActiveTab("EMERGING")}
              className={`px-3.5 py-1.5 rounded-xl transition-all ${
                activeTab === "EMERGING"
                  ? "bg-amber-500 text-slate-950 font-bold"
                  : "bg-slate-850 text-slate-400 hover:text-white"
              }`}
            >
              Emerging Hotspots (Candidates)
            </button>
          </div>

          {/* State Density Cards Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {filteredStates.map((s) => (
              <div
                key={s.state}
                className="p-5 rounded-2xl bg-agni-card border border-agni-border hover:border-amber-500/40 transition-all space-y-3.5 shadow-xl"
              >
                <div className="flex items-center justify-between border-b border-slate-800 pb-2.5">
                  <h3 className="font-extrabold text-base text-white flex items-center gap-2">
                    <MapPin className="w-4 h-4 text-amber-400" />
                    <span>{s.state}</span>
                  </h3>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 font-bold">
                    {s.total_events} Hotspot Belts
                  </span>
                </div>

                <div className="text-xs text-slate-300">
                  <strong className="text-amber-400">Primary Core:</strong> {s.primary_industry}
                </div>

                <div className="p-3 rounded-xl bg-slate-900/90 border border-slate-800 grid grid-cols-3 gap-2 text-xs font-mono text-center">
                  <div>
                    <div className="text-[10px] text-slate-500">CUMULATIVE FRP</div>
                    <div className="text-amber-400 font-bold mt-0.5">{s.total_frp.toFixed(0)} MW</div>
                  </div>
                  <div>
                    <div className="text-[10px] text-slate-500">PERSISTENT</div>
                    <div className="text-emerald-400 font-bold mt-0.5">{s.persistent_count} Belts</div>
                  </div>
                  <div>
                    <div className="text-[10px] text-slate-500">CRITICAL</div>
                    <div className="text-red-400 font-bold mt-0.5">{s.critical_count} Sites</div>
                  </div>
                </div>

                <div className="pt-2 flex items-center justify-between text-xs">
                  <Link
                    href={`/dashboard?state=${s.state}`}
                    className="text-amber-400 hover:text-amber-300 font-semibold flex items-center gap-1"
                  >
                    <span>Launch State Tactical View</span>
                    <ArrowUpRight className="w-3.5 h-3.5" />
                  </Link>
                </div>
              </div>
            ))}
          </div>
        </main>
      </div>
    </div>
  );
}
