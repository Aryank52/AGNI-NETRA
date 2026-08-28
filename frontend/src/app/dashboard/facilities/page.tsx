"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import Header from "@/components/layout/Header";
import Sidebar from "@/components/layout/Sidebar";
import { IndustrialFacility } from "@/types";
import { fetchApi } from "@/lib/api";
import { 
  Factory, Search, MapPin, Clock, 
  Activity, Shield, ChevronRight, CheckCircle2
} from "lucide-react";

export default function FacilitiesPage() {
  const [facilities, setFacilities] = useState<IndustrialFacility[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [typeFilter, setTypeFilter] = useState("ALL");

  useEffect(() => {
    const loadFacilities = async () => {
      try {
        const data = await fetchApi<IndustrialFacility[]>("/facilities");
        setFacilities(data);
      } catch (err) {
        console.warn("Failed to load facilities:", err);
      } finally {
        setLoading(false);
      }
    };
    loadFacilities();
  }, []);

  const filtered = facilities.filter((f) => {
    if (typeFilter !== "ALL" && f.facility_type !== typeFilter) return false;
    if (searchQuery && !f.name.toLowerCase().includes(searchQuery.toLowerCase()) && !f.state.toLowerCase().includes(searchQuery.toLowerCase())) {
      return false;
    }
    return true;
  });

  return (
    <div className="min-h-screen bg-agni-navy flex flex-col selection:bg-amber-500 selection:text-slate-950">
      <Header />

      <div className="flex flex-1 overflow-hidden">
        <Sidebar />

        <main className="flex-1 overflow-y-auto p-6 space-y-6 max-w-6xl mx-auto">
          {/* Header Strip */}
          <div className="flex flex-wrap items-center justify-between gap-4 border-b border-agni-border pb-4">
            <div>
              <h1 className="text-xl sm:text-2xl font-extrabold text-white flex items-center gap-2.5">
                <Factory className="w-6 h-6 text-amber-400" />
                Industrial Facility Registry & Baselines
              </h1>
              <p className="text-xs text-slate-400 mt-1">
                Canonical multi-source industrial registry (OSM, State Pollution Boards, Central Electricity Authority).
              </p>
            </div>

            <div className="flex items-center gap-3">
              <span className="text-xs font-mono px-3 py-1 rounded-lg bg-agni-card border border-agni-border text-slate-300">
                {facilities.length} Facilities Monitored
              </span>
            </div>
          </div>

          {/* Filters Bar */}
          <div className="flex flex-wrap items-center justify-between gap-3 p-3 rounded-xl bg-agni-slate border border-agni-border text-xs">
            <div className="flex items-center gap-2 flex-1 min-w-[240px]">
              <Search className="w-4 h-4 text-slate-400" />
              <input
                type="text"
                placeholder="Search facility by name, state, or district..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-white placeholder:text-slate-500 focus:outline-none focus:border-amber-500"
              />
            </div>

            <div className="flex items-center gap-2">
              <span className="font-semibold text-slate-400">Type:</span>
              <select
                value={typeFilter}
                onChange={(e) => setTypeFilter(e.target.value)}
                className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-white focus:outline-none focus:border-amber-500"
              >
                <option value="ALL">All Categories</option>
                <option value="REFINERY">Refinery / Petrochemical</option>
                <option value="POWER_PLANT">Thermal Power Plant</option>
                <option value="STEEL_PLANT">Integrated Steel Mill</option>
                <option value="MINING">Mining & Coal Cadastre</option>
              </select>
            </div>
          </div>

          {/* Facilities Cards Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {filtered.map((fac) => {
              const baseline = fac.baselines?.[0];
              return (
                <div
                  key={fac.id}
                  className="p-5 rounded-2xl bg-agni-card border border-agni-border hover:border-amber-500/40 transition-all space-y-3.5 shadow-lg"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-slate-800 text-amber-400 font-bold border border-slate-700">
                        {fac.facility_type}
                      </span>
                      <h3 className="text-base font-bold text-white mt-1.5 leading-snug">
                        {fac.name}
                      </h3>
                    </div>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 shrink-0">
                      {fac.status}
                    </span>
                  </div>

                  <div className="flex items-center gap-4 text-xs text-slate-400 font-mono">
                    <div className="flex items-center gap-1.5">
                      <MapPin className="w-3.5 h-3.5 text-amber-400" />
                      <span>{fac.state} {fac.district ? `(${fac.district})` : ""}</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <Clock className="w-3.5 h-3.5 text-cyan-400" />
                      <span>{fac.operating_hours || "24x7"}</span>
                    </div>
                  </div>

                  {/* Baseline Intelligence Strip */}
                  <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 grid grid-cols-3 gap-2 text-xs font-mono text-center">
                    <div>
                      <div className="text-[10px] text-slate-500">BASELINE MEAN</div>
                      <div className="font-bold text-amber-400">
                        {baseline?.mean_frp ? `${baseline.mean_frp.toFixed(1)} MW` : "110 MW"}
                      </div>
                    </div>
                    <div>
                      <div className="text-[10px] text-slate-500">STD DEV (σ)</div>
                      <div className="font-bold text-slate-300">
                        {baseline?.std_frp ? `±${baseline.std_frp.toFixed(1)}` : "±22.0"}
                      </div>
                    </div>
                    <div>
                      <div className="text-[10px] text-slate-500">DAY/NIGHT</div>
                      <div className="font-bold text-emerald-400">
                        {baseline?.day_night_ratio ? `${baseline.day_night_ratio.toFixed(2)}x` : "1.1x"}
                      </div>
                    </div>
                  </div>

                  <div className="pt-1 flex items-center justify-between text-xs">
                    <span className="text-slate-500 text-[11px]">
                      Source: {fac.source} • Coords: {fac.latitude.toFixed(4)}°N, {fac.longitude.toFixed(4)}°E
                    </span>
                    <Link
                      href={`/dashboard?state=${fac.state}`}
                      className="text-amber-400 hover:text-amber-300 font-semibold flex items-center gap-1"
                    >
                      <span>Locate on Map</span>
                      <ChevronRight className="w-3.5 h-3.5" />
                    </Link>
                  </div>
                </div>
              );
            })}
          </div>
        </main>
      </div>
    </div>
  );
}
