"use client";

import React, { useState, useEffect, useMemo } from "react";
import Link from "next/link";
import Header from "@/components/layout/Header";
import Sidebar from "@/components/layout/Sidebar";
import { IndustrialFacility } from "@/types";
import { fetchApi } from "@/lib/api";
import { formatNumber, formatFrp, formatCoord, safeArray } from "@/lib/formatters";
import { 
  Factory, Search, MapPin, Clock, 
  Activity, Shield, ChevronRight, CheckCircle2, RefreshCw,
  Flame, ArrowUpRight, Filter, X
} from "lucide-react";
import PageHeader from "@/components/common/PageHeader";
import EmptyState from "@/components/common/EmptyState";
import { CardSkeleton } from "@/components/common/Skeletons";

export default function FacilitiesPage() {
  const [facilities, setFacilities] = useState<IndustrialFacility[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [typeFilter, setTypeFilter] = useState("ALL");

  const loadFacilities = async () => {
    setLoading(true);
    try {
      const data = await fetchApi<IndustrialFacility[]>("/facilities");
      setFacilities(data);
    } catch (err) {
      console.warn("Failed to load facilities:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
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
          {/* Standardized Page Header */}
          <PageHeader
            category="NATIONAL INDUSTRIAL REGISTRY"
            title="Industrial Facility Registry & 90-Day Baselines"
            description="Canonical multi-source industrial registry (OpenStreetMap, State Pollution Control Boards, Central Electricity Authority) with precomputed thermal baselines."
            icon={<Factory className="w-6 h-6 text-amber-400" />}
            actions={
              <div className="flex items-center gap-3">
                <span className="text-xs font-mono px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-slate-300 font-bold">
                  {facilities.length} Facilities Monitored
                </span>
                <button
                  onClick={loadFacilities}
                  className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-colors"
                  title="Refresh Facilities"
                >
                  <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin text-amber-400" : ""}`} />
                </button>
              </div>
            }
          />

          {/* Filters Bar */}
          <div className="flex flex-wrap items-center justify-between gap-3 p-3.5 rounded-2xl bg-agni-card border border-agni-border text-xs">
            <div className="flex items-center gap-2 flex-1 min-w-[240px]">
              <Search className="w-4 h-4 text-slate-400" />
              <input
                type="text"
                placeholder="Search facility by name, state, or district..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-white placeholder:text-slate-500 focus:outline-none focus:border-amber-500 text-xs"
              />
            </div>

            <div className="flex items-center gap-2 font-mono">
              <span className="font-semibold text-slate-400">Type:</span>
              <select
                value={typeFilter}
                onChange={(e) => setTypeFilter(e.target.value)}
                className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-white focus:outline-none focus:border-amber-500 text-xs"
              >
                <option value="ALL">All Categories</option>
                <option value="REFINERY">Refinery / Petrochemical</option>
                <option value="POWER_PLANT">Thermal Power Plant</option>
                <option value="STEEL_PLANT">Integrated Steel Mill</option>
                <option value="MINING">Mining & Coal Cadastre</option>
              </select>
            </div>
          </div>

          {/* Active Filter Chips Tray */}
          {(typeFilter !== "ALL" || searchQuery.trim().length > 0) && (
            <div className="flex flex-wrap items-center gap-1.5 px-3.5 py-1.5 bg-slate-950/90 border border-slate-800 rounded-xl text-xs font-mono">
              <span className="text-[10px] text-amber-400 font-bold uppercase tracking-wider flex items-center gap-1">
                <Filter className="w-3 h-3 text-amber-500" />
                Active Filters:
              </span>
              {typeFilter !== "ALL" && (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-200 text-[11px]">
                  Category: {typeFilter}
                  <button onClick={() => setTypeFilter("ALL")} className="text-slate-400 hover:text-white">
                    <X className="w-3 h-3" />
                  </button>
                </span>
              )}
              {searchQuery.trim().length > 0 && (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-200 text-[11px]">
                  Query: "{searchQuery}"
                  <button onClick={() => setSearchQuery("")} className="text-slate-400 hover:text-white">
                    <X className="w-3 h-3" />
                  </button>
                </span>
              )}
              <button
                onClick={() => { setTypeFilter("ALL"); setSearchQuery(""); }}
                className="ml-auto text-[10px] text-amber-400 hover:text-amber-300 font-bold hover:underline"
              >
                Clear All
              </button>
            </div>
          )}

          {/* Facilities Cards Grid */}
          {loading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <CardSkeleton />
              <CardSkeleton />
              <CardSkeleton />
              <CardSkeleton />
            </div>
          ) : filtered.length === 0 ? (
            <EmptyState
              title="No Industrial Facilities Found"
              description="No facilities match your search query or selected industry category."
              actionLabel="Reset Search & Filters"
              onAction={() => {
                setSearchQuery("");
                setTypeFilter("ALL");
              }}
            />
          ) : (
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
                        {formatFrp(baseline?.mean_frp, "110.0 MW")}
                      </div>
                    </div>
                    <div>
                      <div className="text-[10px] text-slate-500">STD DEV (σ)</div>
                      <div className="font-bold text-slate-300">
                        {baseline?.std_frp !== undefined && baseline?.std_frp !== null ? `±${formatNumber(baseline.std_frp, 1)}` : "±22.0"}
                      </div>
                    </div>
                    <div>
                      <div className="text-[10px] text-slate-500">DAY/NIGHT</div>
                      <div className="font-bold text-emerald-400">
                        {formatNumber(baseline?.day_night_ratio, 2, "1.10")}x
                      </div>
                    </div>
                  </div>

                  <div className="pt-2 border-t border-slate-800/80 flex flex-wrap items-center justify-between gap-2 text-xs font-mono">
                    <span className="text-slate-500 text-[11px]">
                      Source: {fac.source} • Coords: {formatCoord(fac.latitude, fac.longitude, 3)}
                    </span>
                    <div className="flex items-center gap-1.5">
                      <Link
                        href={`/dashboard?lat=${fac.latitude}&lon=${fac.longitude}`}
                        className="px-2.5 py-1 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-[11px] flex items-center gap-1 transition-colors"
                        title="Fly directly to facility coordinates on Tactical Map"
                      >
                        <MapPin className="w-3 h-3" />
                        <span>Locate</span>
                      </Link>
                      <Link
                        href={`/dashboard/atlas?search=${encodeURIComponent(fac.name)}`}
                        className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-[11px] flex items-center gap-1 transition-colors"
                        title="Open Facility Intelligence in Atlas"
                      >
                        <Factory className="w-3 h-3 text-cyan-400" />
                        <span>Atlas</span>
                      </Link>
                      <Link
                        href={`/dashboard/events?state=${encodeURIComponent(fac.state)}`}
                        className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-[11px] flex items-center gap-1 transition-colors"
                        title="View Thermal Events in this State"
                      >
                        <Flame className="w-3 h-3 text-orange-400" />
                        <span>Events</span>
                      </Link>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
          )}
        </main>
      </div>
    </div>
  );
}
