"use client";

import React, { useState, useEffect, useMemo } from "react";
import Link from "next/link";
import Header from "@/components/layout/Header";
import Sidebar from "@/components/layout/Sidebar";
import RiskBadge from "@/components/intelligence/RiskBadge";
import { ThermalEvent } from "@/types";
import { fetchApi, API_BASE_URL } from "@/lib/api";
import { formatNumber, formatFrp, formatPercent, formatCoord, formatDistance } from "@/lib/formatters";
import { 
  Flame, Filter, Search, ChevronRight, Activity, 
  MapPin, ShieldAlert, Sparkles, Download, Layers,
  Calendar, RefreshCw, Radio, CheckCircle2, SlidersHorizontal,
  ArrowUpDown, ExternalLink, X, ShieldCheck, ArrowUpRight
} from "lucide-react";
import PageHeader from "@/components/common/PageHeader";
import { TableSkeleton } from "@/components/common/Skeletons";
import EmptyState from "@/components/common/EmptyState";

export default function EventsInventoryPage() {
  const [events, setEvents] = useState<ThermalEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [selectedState, setSelectedState] = useState("ALL");
  const [selectedClass, setSelectedClass] = useState("ALL");
  const [selectedRisk, setSelectedRisk] = useState("ALL");
  const [minFrp, setMinFrp] = useState<number>(0);
  const [page, setPage] = useState(1);
  const [limit, setLimit] = useState(15);
  const [totalCount, setTotalCount] = useState(0);
  const [sortBy, setSortBy] = useState("max_frp");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");

  const loadEvents = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (selectedState !== "ALL") params.append("state", selectedState);
      if (selectedClass !== "ALL") params.append("event_type", selectedClass);
      if (selectedRisk !== "ALL") params.append("risk_level", selectedRisk);
      if (minFrp > 0) params.append("min_frp", minFrp.toString());
      params.append("page", page.toString());
      params.append("limit", limit.toString());

      const data = await fetchApi<any>(`/events?${params.toString()}`);
      if (data && data.items) {
        setEvents(data.items);
        setTotalCount(data.total_count);
      } else if (Array.isArray(data)) {
        setEvents(data);
        setTotalCount(data.length);
      }
    } catch (err) {
      console.warn("Failed to fetch events:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadEvents();
  }, [selectedState, selectedClass, selectedRisk, minFrp, page, limit]);

  const filteredEvents = events.filter((e) => {
    if (!search) return true;
    const term = search.toLowerCase();
    return (
      e.event_code.toLowerCase().includes(term) ||
      e.state.toLowerCase().includes(term) ||
      (e.district && e.district.toLowerCase().includes(term)) ||
      (e.prediction?.predicted_class && e.prediction.predicted_class.toLowerCase().includes(term))
    );
  });

  const sortedEvents = [...filteredEvents].sort((a, b) => {
    let valA = (a as any)[sortBy] || 0;
    let valB = (b as any)[sortBy] || 0;
    if (sortBy === "risk_score") {
      valA = a.risk?.risk_score || 0;
      valB = b.risk?.risk_score || 0;
    }
    return sortOrder === "desc" ? valB - valA : valA - valB;
  });

  const resetFilters = () => {
    setSearch("");
    setSelectedState("ALL");
    setSelectedClass("ALL");
    setSelectedRisk("ALL");
    setMinFrp(0);
    setPage(1);
  };

  const activeFiltersCount = useMemo(() => {
    let count = 0;
    if (selectedState !== "ALL") count++;
    if (selectedClass !== "ALL") count++;
    if (selectedRisk !== "ALL") count++;
    if (minFrp > 0) count++;
    if (search.trim().length > 0) count++;
    return count;
  }, [selectedState, selectedClass, selectedRisk, minFrp, search]);

  return (
    <div className="min-h-screen bg-agni-navy flex flex-col selection:bg-amber-500 selection:text-slate-950">
      <Header />

      <div className="flex flex-1 overflow-hidden">
        <Sidebar />

        <main className="flex-1 overflow-y-auto p-6 space-y-6 max-w-7xl mx-auto">
          {/* Standardized Page Header */}
          <PageHeader
            category="SATELLITE THERMAL INVENTORY"
            title="Thermal Events & Clusters Inventory"
            description="Classified spatiotemporal thermal clusters across India with peak radiative power, calibrated ML classification, 5-factor risk scores, and evidence dossiers."
            icon={<Flame className="w-6 h-6 text-amber-500" />}
            actions={
              <div className="flex items-center gap-2.5">
                <a
                  href={`${API_BASE_URL}/reports/export/csv`}
                  target="_blank"
                  rel="noreferrer"
                  className="px-3.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 flex items-center gap-1.5 transition-all font-mono"
                >
                  <Download className="w-3.5 h-3.5 text-amber-400" />
                  <span>Export CSV</span>
                </a>
                <button
                  onClick={loadEvents}
                  className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-colors"
                  title="Refresh Inventory"
                >
                  <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin text-amber-400" : ""}`} />
                </button>
              </div>
            }
          />

          {/* Filters Bar */}
          <div className="p-4 rounded-2xl bg-agni-card border border-agni-border grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 text-xs">
            {/* Search Input */}
            <div className="relative">
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-3" />
              <input
                type="text"
                placeholder="Search event code, state..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full pl-9 pr-3 py-2 rounded-xl bg-slate-900 border border-slate-700 text-white placeholder:text-slate-500 focus:outline-none focus:border-amber-500"
              />
            </div>

            {/* State Filter */}
            <div>
              <select
                value={selectedState}
                onChange={(e) => {
                  setSelectedState(e.target.value);
                  setPage(1);
                }}
                className="w-full p-2 rounded-xl bg-slate-900 border border-slate-700 text-white font-medium focus:outline-none focus:border-amber-500"
              >
                <option value="ALL">All States (National)</option>
                <option value="Gujarat">Gujarat (Petro/Chemical)</option>
                <option value="Odisha">Odisha (Steel/Smelters)</option>
                <option value="Jharkhand">Jharkhand (Mining/Metals)</option>
                <option value="Chhattisgarh">Chhattisgarh (Power/Coal)</option>
                <option value="Madhya Pradesh">Madhya Pradesh</option>
                <option value="Maharashtra">Maharashtra</option>
                <option value="Punjab">Punjab (Agricultural)</option>
                <option value="Andhra Pradesh">Andhra Pradesh</option>
              </select>
            </div>

            {/* Class Filter */}
            <div>
              <select
                value={selectedClass}
                onChange={(e) => {
                  setSelectedClass(e.target.value);
                  setPage(1);
                }}
                className="w-full p-2 rounded-xl bg-slate-900 border border-slate-700 text-white font-medium focus:outline-none focus:border-amber-500"
              >
                <option value="ALL">All AI Categories</option>
                <option value="Industrial Fire">Industrial Fire</option>
                <option value="Gas Flare">Gas Flare</option>
                <option value="Forest Fire">Forest Fire</option>
                <option value="Agricultural Burning">Agricultural Burning</option>
                <option value="Mining Activity">Mining Activity</option>
                <option value="Other Thermal Source">Other Thermal Source</option>
                <option value="Uncertain">Uncertain</option>
              </select>
            </div>

            {/* Risk Level Filter */}
            <div>
              <select
                value={selectedRisk}
                onChange={(e) => {
                  setSelectedRisk(e.target.value);
                  setPage(1);
                }}
                className="w-full p-2 rounded-xl bg-slate-900 border border-slate-700 text-white font-medium focus:outline-none focus:border-amber-500"
              >
                <option value="ALL">All Risk Levels</option>
                <option value="CRITICAL">Critical Risk</option>
                <option value="HIGH">High Risk</option>
                <option value="MODERATE">Moderate Risk</option>
                <option value="LOW">Low Risk</option>
              </select>
            </div>

            {/* Min FRP Threshold */}
            <div className="flex items-center gap-2 px-2 bg-slate-900 rounded-xl border border-slate-700">
              <span className="text-slate-400 shrink-0 font-mono">Min FRP:</span>
              <input
                type="range"
                min="0"
                max="200"
                step="10"
                value={minFrp}
                onChange={(e) => setMinFrp(Number(e.target.value))}
                className="w-full accent-amber-500 cursor-pointer"
              />
              <span className="font-mono text-amber-400 font-bold w-12 text-right">{minFrp} MW</span>
            </div>
          </div>

          {/* Active Filter Chips Tray */}
          {activeFiltersCount > 0 && (
            <div className="flex flex-wrap items-center gap-1.5 px-4 py-2 rounded-xl bg-slate-950/90 border border-agni-border text-xs font-mono">
              <span className="text-[10px] text-amber-400 font-bold uppercase tracking-wider flex items-center gap-1">
                <Filter className="w-3 h-3 text-amber-500" />
                {activeFiltersCount} Filter{activeFiltersCount > 1 ? "s" : ""} Active:
              </span>
              {search.trim().length > 0 && (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-200 text-[11px]">
                  Search: "{search}"
                  <button onClick={() => setSearch("")} className="text-slate-400 hover:text-white">
                    <X className="w-3 h-3" />
                  </button>
                </span>
              )}
              {selectedState !== "ALL" && (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-200 text-[11px]">
                  State: {selectedState}
                  <button onClick={() => setSelectedState("ALL")} className="text-slate-400 hover:text-white">
                    <X className="w-3 h-3" />
                  </button>
                </span>
              )}
              {selectedClass !== "ALL" && (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-200 text-[11px]">
                  Class: {selectedClass}
                  <button onClick={() => setSelectedClass("ALL")} className="text-slate-400 hover:text-white">
                    <X className="w-3 h-3" />
                  </button>
                </span>
              )}
              {selectedRisk !== "ALL" && (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-200 text-[11px]">
                  Risk: {selectedRisk}
                  <button onClick={() => setSelectedRisk("ALL")} className="text-slate-400 hover:text-white">
                    <X className="w-3 h-3" />
                  </button>
                </span>
              )}
              {minFrp > 0 && (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-200 text-[11px]">
                  Min FRP: {minFrp} MW
                  <button onClick={() => setMinFrp(0)} className="text-slate-400 hover:text-white">
                    <X className="w-3 h-3" />
                  </button>
                </span>
              )}
              <button
                onClick={resetFilters}
                className="ml-auto text-[10px] text-amber-400 hover:text-amber-300 font-bold hover:underline"
              >
                Clear All
              </button>
            </div>
          )}

          {/* Events Inventory Table */}
          <div className="p-4 rounded-2xl bg-agni-card border border-agni-border shadow-xl overflow-hidden">
            <div className="flex items-center justify-between mb-3 text-xs text-slate-400">
              <span>Showing {sortedEvents.length} of {totalCount} thermal events</span>
              <div className="flex items-center gap-2">
                <span>Sort by:</span>
                <button
                  onClick={() => {
                    if (sortBy === "max_frp") setSortOrder(sortOrder === "desc" ? "asc" : "desc");
                    else { setSortBy("max_frp"); setSortOrder("desc"); }
                  }}
                  className={`px-2.5 py-1 rounded-lg border text-xs font-mono flex items-center gap-1 ${
                    sortBy === "max_frp" ? "bg-amber-500/20 text-amber-300 border-amber-500/40" : "bg-slate-900 border-slate-700"
                  }`}
                >
                  <span>Peak FRP</span>
                  <ArrowUpDown className="w-3 h-3" />
                </button>
                <button
                  onClick={() => {
                    if (sortBy === "risk_score") setSortOrder(sortOrder === "desc" ? "asc" : "desc");
                    else { setSortBy("risk_score"); setSortOrder("desc"); }
                  }}
                  className={`px-2.5 py-1 rounded-lg border text-xs font-mono flex items-center gap-1 ${
                    sortBy === "risk_score" ? "bg-red-500/20 text-red-300 border-red-500/40" : "bg-slate-900 border-slate-700"
                  }`}
                >
                  <span>Risk Score</span>
                  <ArrowUpDown className="w-3 h-3" />
                </button>
              </div>
            </div>

            {loading ? (
              <TableSkeleton rows={8} cols={8} />
            ) : sortedEvents.length === 0 ? (
              <EmptyState
                title="No Thermal Events Found"
                description="No thermal hotspot records or spatiotemporal clusters match your active filters or query parameters."
                actionLabel="Clear Filter Matrix"
                onAction={() => {
                  setSearch("");
                  setSelectedState("ALL");
                  setSelectedClass("ALL");
                  setSelectedRisk("ALL");
                  setMinFrp(0);
                }}
              />
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs font-mono">
                  <thead className="bg-slate-900/80 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800">
                    <tr>
                      <th className="p-3">Event Code</th>
                      <th className="p-3">Location</th>
                      <th className="p-3">ML Classification</th>
                      <th className="p-3">Peak FRP</th>
                      <th className="p-3">Persistence</th>
                      <th className="p-3">Facility Context</th>
                      <th className="p-3">Risk Level</th>
                      <th className="p-3 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 font-sans">
                    {sortedEvents.map((evt) => {
                      const pClass = evt.prediction?.predicted_class || "Uncertain";
                      const conf = evt.prediction?.confidence || 0.85;
                      const isCandidate = evt.facility_status === "CANDIDATE";

                      return (
                        <tr key={evt.id} className="hover:bg-slate-800/40 transition-colors">
                          <td className="p-3 font-mono font-bold text-amber-400">
                            {evt.event_code}
                            {evt.is_demo && (
                              <span className="block text-[9px] text-slate-500 font-sans">DEMO SAMPLE</span>
                            )}
                          </td>
                          <td className="p-3 text-slate-300">
                            <div className="font-semibold text-white">{evt.state}</div>
                            <div className="text-[11px] text-slate-400">{evt.district || formatCoord(evt.latitude, evt.longitude, 2)}</div>
                          </td>
                          <td className="p-3">
                            <div className="font-bold text-amber-300">{pClass}</div>
                            <div className="text-[10px] text-emerald-400 font-mono">{formatPercent(conf, 0)} Conf</div>
                          </td>
                          <td className="p-3 font-mono font-bold text-white">
                            <div>{formatFrp(evt.max_frp)}</div>
                            <div className="text-[10px] text-slate-400 font-sans">Mean: {formatFrp(evt.avg_frp)}</div>
                          </td>
                          <td className="p-3">
                            <span className="font-mono text-emerald-400 font-bold">
                              {formatNumber(evt.features?.persistence_score, 1, "5.0")}/10
                            </span>
                            <div className="text-[10px] text-slate-400">{evt.detection_count} Passes</div>
                          </td>
                          <td className="p-3">
                            <span className={`text-[10px] font-mono px-2 py-0.5 rounded ${
                              isCandidate
                                ? "bg-purple-500/20 text-purple-300 border border-purple-500/30"
                                : evt.facility_status === "KNOWN"
                                ? "bg-blue-500/20 text-blue-300 border border-blue-500/30"
                                : "bg-slate-800 text-slate-400"
                            }`}>
                              {isCandidate ? "CANDIDATE DISCOVERY" : evt.facility_status}
                            </span>
                            <div className="text-[10px] text-slate-400 mt-0.5">
                              {evt.nearest_facility_distance_m !== undefined && evt.nearest_facility_distance_m !== null ? `${formatDistance(evt.nearest_facility_distance_m)} to plant` : "No plant near"}
                            </div>
                          </td>
                          <td className="p-3">
                            <RiskBadge level={evt.risk?.risk_level || "LOW"} score={evt.risk?.risk_score} />
                          </td>
                          <td className="p-3 text-right">
                            <div className="flex items-center justify-end gap-1.5 font-mono">
                              <Link
                                href={`/dashboard/events/${evt.id}`}
                                className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs shadow-sm transition-all"
                              >
                                <span>OPEN EVENT</span>
                                <ArrowUpRight className="w-3.5 h-3.5" />
                              </Link>
                              <Link
                                href={`/dashboard?lat=${evt.latitude}&lon=${evt.longitude}&event_id=${evt.id}`}
                                className="inline-flex items-center gap-1 px-2 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs transition-all"
                                title="Fly to Hotspot on Tactical Map"
                              >
                                <MapPin className="w-3.5 h-3.5 text-amber-400" />
                                <span className="hidden sm:inline">MAP</span>
                              </Link>
                              <Link
                                href={`/dashboard/verification?event_id=${evt.id}`}
                                className="inline-flex items-center gap-1 px-2 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-amber-300 border border-slate-700 text-xs transition-all"
                                title="Verify in HITL Workstation"
                              >
                                <ShieldCheck className="w-3.5 h-3.5 text-amber-400" />
                                <span className="hidden sm:inline">VERIFY</span>
                              </Link>
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}

            {/* Pagination Controls */}
            <div className="flex items-center justify-between pt-4 mt-3 border-t border-slate-800 text-xs">
              <button
                disabled={page <= 1}
                onClick={() => setPage(page - 1)}
                className="px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 disabled:opacity-40 text-slate-300"
              >
                ← Previous Page
              </button>
              <span className="font-mono text-slate-400">
                Page {page} of {Math.ceil(totalCount / limit) || 1}
              </span>
              <button
                disabled={page * limit >= totalCount}
                onClick={() => setPage(page + 1)}
                className="px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 disabled:opacity-40 text-slate-300"
              >
                Next Page →
              </button>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
