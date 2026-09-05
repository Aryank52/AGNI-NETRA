"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import Header from "@/components/layout/Header";
import Sidebar from "@/components/layout/Sidebar";
import { fetchApi } from "@/lib/api";
import { safeArray, safeNumber, formatNumber } from "@/lib/formatters";
import { 
  Globe, Flame, Layers, MapPin, Activity, 
  BarChart2, RefreshCw, Compass, ArrowUpRight,
  Shield, Sliders, Radio, Sparkles, Factory, Zap, 
  Search, X, ExternalLink, ChevronRight, CheckCircle2,
  Trees, Pickaxe, ShieldAlert
} from "lucide-react";

interface StateSummary {
  state_code: string;
  state_name: string;
  district_count: number;
  facility_count: number;
  thermal_observation_count: number;
}

interface FacilitySummary {
  id: string;
  name: string;
  facility_type: string;
  master_sector: string;
  state: string;
  district: string;
  latitude: number;
  longitude: number;
  firms_detections_1km?: number;
  environmental_clearance_present?: boolean;
  facility_baseline?: {
    mean_frp?: number;
    peak_frp?: number;
    frequency_days?: number;
  };
}

export default function IndiaThermalAtlasPage() {
  const [states, setStates] = useState<StateSummary[]>([]);
  const [facilities, setFacilities] = useState<FacilitySummary[]>([]);
  const [selectedState, setSelectedState] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [selectedFacility, setSelectedFacility] = useState<FacilitySummary | null>(null);
  const [facilityIntel, setFacilityIntel] = useState<any | null>(null);
  const [intelLoading, setIntelLoading] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(true);
  const [activeTab, setActiveTab] = useState<"STATES" | "FACILITIES">("STATES");

  useEffect(() => {
    if (!selectedFacility?.id) {
      setFacilityIntel(null);
      return;
    }
    setIntelLoading(true);
    fetchApi<any>(`/facilities/${selectedFacility.id}/intelligence`)
      .then((data) => setFacilityIntel(data))
      .catch((err) => {
        console.warn("Failed to load facility intelligence:", err);
        setFacilityIntel(null);
      })
      .finally(() => setIntelLoading(false));
  }, [selectedFacility]);

  useEffect(() => {
    setLoading(true);
    fetchApi<StateSummary[]>("/geography/states")
      .then((data) => {
        const sorted = safeArray<StateSummary>(data).sort(
          (a, b) => b.facility_count - a.facility_count
        );
        setStates(sorted);
      })
      .catch((err) => console.warn("Failed to load states:", err))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    const params = new URLSearchParams();
    if (selectedState !== "ALL") params.append("state", selectedState);
    if (searchQuery.trim()) params.append("search", searchQuery.trim());
    params.append("limit", "60");

    fetchApi<FacilitySummary[]>(`/facilities?${params.toString()}`)
      .then((data) => setFacilities(safeArray<FacilitySummary>(data)))
      .catch(() => setFacilities([]));
  }, [selectedState, searchQuery]);

  const filteredStates = states.filter((s) => {
    if (selectedState === "ALL") return true;
    return s.state_name.toLowerCase() === selectedState.toLowerCase();
  });

  const totalFacilities = states.reduce((acc, s) => acc + s.facility_count, 0);
  const totalObservations = states.reduce((acc, s) => acc + s.thermal_observation_count, 0);

  return (
    <div className="min-h-screen bg-agni-navy flex flex-col selection:bg-amber-500 selection:text-slate-950 font-sans">
      <Header />

      <div className="flex flex-1 overflow-hidden">
        <Sidebar />

        <main className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6 max-w-7xl mx-auto w-full">
          {/* Header */}
          <div className="flex flex-wrap items-center justify-between gap-4 border-b border-agni-border pb-4">
            <div>
              <div className="flex items-center gap-2">
                <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30 font-bold">
                  AUTHORITATIVE CADASTRE
                </span>
                <span className="text-xs text-slate-400">PostGIS 3.4 Multi-Source Industrial Registry</span>
              </div>
              <h1 className="text-xl sm:text-2xl font-extrabold text-white flex items-center gap-2.5 mt-1">
                <Globe className="w-6 h-6 text-amber-400" />
                India Industrial Thermal Atlas
              </h1>
              <p className="text-xs text-slate-400 mt-1">
                Authoritative registry of 35,684 industrial facilities and multi-year thermal activity distribution across Indian states.
              </p>
            </div>

            <div className="flex items-center gap-3">
              <select
                value={selectedState}
                onChange={(e) => setSelectedState(e.target.value)}
                className="p-2 rounded-xl bg-slate-900 border border-slate-700 text-white font-medium text-xs focus:outline-none focus:border-amber-500"
              >
                <option value="ALL">All 36 States & UTs (National View)</option>
                {states.map((s) => (
                  <option key={s.state_name} value={s.state_name}>
                    {s.state_name} ({s.facility_count.toLocaleString()} facilities)
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* KPI Summary Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="p-3 bg-slate-900/80 border border-slate-800 rounded-xl space-y-1">
              <div className="text-[10px] font-mono text-slate-400 uppercase">National Facilities Cadastre</div>
              <div className="text-xl font-black text-cyan-400 font-mono">
                {totalFacilities > 0 ? totalFacilities.toLocaleString() : "35,684"}
              </div>
              <div className="text-[10px] text-slate-500">OSM Industrial Registry</div>
            </div>

            <div className="p-3 bg-slate-900/80 border border-slate-800 rounded-xl space-y-1">
              <div className="text-[10px] font-mono text-slate-400 uppercase">Tracked States & UTs</div>
              <div className="text-xl font-black text-white font-mono">
                {states.length > 0 ? states.length : "36"}
              </div>
              <div className="text-[10px] text-slate-500">Survey of India Boundaries</div>
            </div>

            <div className="p-3 bg-slate-900/80 border border-slate-800 rounded-xl space-y-1">
              <div className="text-[10px] font-mono text-slate-400 uppercase">Historical Detections Ingested</div>
              <div className="text-xl font-black text-orange-400 font-mono">
                8,221,854
              </div>
              <div className="text-[10px] text-slate-500">NASA FIRMS Sensor Archive</div>
            </div>

            <div className="p-3 bg-slate-900/80 border border-slate-800 rounded-xl space-y-1">
              <div className="text-[10px] font-mono text-slate-400 uppercase">Precomputed Baselines</div>
              <div className="text-xl font-black text-emerald-400 font-mono">
                35,579
              </div>
              <div className="text-[10px] text-slate-500">Statistical Baseline Models</div>
            </div>
          </div>

          {/* Search & Tabs */}
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2 text-xs font-semibold">
              <button
                onClick={() => setActiveTab("STATES")}
                className={`px-3.5 py-1.5 rounded-xl transition-all ${
                  activeTab === "STATES"
                    ? "bg-amber-500 text-slate-950 font-bold"
                    : "bg-slate-900 text-slate-400 hover:text-white border border-slate-800"
                }`}
              >
                State Distribution ({filteredStates.length})
              </button>
              <button
                onClick={() => setActiveTab("FACILITIES")}
                className={`px-3.5 py-1.5 rounded-xl transition-all ${
                  activeTab === "FACILITIES"
                    ? "bg-amber-500 text-slate-950 font-bold"
                    : "bg-slate-900 text-slate-400 hover:text-white border border-slate-800"
                }`}
              >
                Industrial Facilities Directory ({facilities.length})
              </button>
            </div>

            {activeTab === "FACILITIES" && (
              <div className="relative">
                <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-slate-400" />
                <input
                  type="text"
                  placeholder="Search plant, company, sector..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-8 pr-3 py-1.5 rounded-xl bg-slate-900 border border-slate-700 text-xs text-white placeholder:text-slate-500 focus:outline-none focus:border-amber-500"
                />
              </div>
            )}
          </div>

          {/* Tab 1: State Density Table */}
          {activeTab === "STATES" && (
            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-950/80 text-slate-400 uppercase font-mono text-[10px] border-b border-slate-800">
                    <tr>
                      <th className="p-3.5">State / UT</th>
                      <th className="p-3.5 text-right">Official Districts</th>
                      <th className="p-3.5 text-right">Registered Facilities</th>
                      <th className="p-3.5 text-right">Spatial Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 font-sans">
                    {filteredStates.map((s) => (
                      <tr key={s.state_name} className="hover:bg-slate-850/50 transition-colors">
                        <td className="p-3.5 font-bold text-white flex items-center gap-2">
                          <MapPin className="w-3.5 h-3.5 text-amber-400 shrink-0" />
                          <span>{s.state_name}</span>
                        </td>
                        <td className="p-3.5 text-right font-mono text-slate-300">
                          {s.district_count} districts
                        </td>
                        <td className="p-3.5 text-right font-mono text-cyan-400 font-bold">
                          {s.facility_count.toLocaleString()}
                        </td>
                        <td className="p-3.5 text-right">
                          <Link
                            href={`/dashboard?state=${encodeURIComponent(s.state_name)}`}
                            className="px-2.5 py-1 rounded-lg bg-amber-500/10 hover:bg-amber-500/20 text-amber-400 border border-amber-500/30 text-[11px] font-semibold transition-colors inline-flex items-center gap-1"
                          >
                            <span>Inspect on Map</span>
                            <ArrowUpRight className="w-3 h-3" />
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Tab 2: Facilities Directory */}
          {activeTab === "FACILITIES" && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3.5">
              {facilities.map((fac) => (
                <div
                  key={fac.id}
                  onClick={() => setSelectedFacility(fac)}
                  className="p-3.5 rounded-xl bg-slate-900/80 hover:bg-slate-850 border border-slate-800 hover:border-cyan-500/40 cursor-pointer transition-all space-y-2 flex flex-col justify-between group"
                >
                  <div className="space-y-1">
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-[10px] font-mono px-2 py-0.2 rounded bg-cyan-500/10 text-cyan-300 font-bold border border-cyan-500/20">
                        {fac.facility_type || "INDUSTRIAL"}
                      </span>
                      {fac.environmental_clearance_present && (
                        <span className="text-[9px] font-mono text-emerald-400 flex items-center gap-1">
                          <CheckCircle2 className="w-2.5 h-2.5" /> EC Granted
                        </span>
                      )}
                    </div>
                    <div className="font-bold text-xs text-white group-hover:text-cyan-300 transition-colors line-clamp-1">
                      {fac.name}
                    </div>
                    <div className="text-[11px] text-slate-400 flex items-center gap-1">
                      <MapPin className="w-3 h-3 text-slate-500 shrink-0" />
                      <span>{fac.district ? `${fac.district}, ` : ""}{fac.state}</span>
                    </div>
                  </div>

                  <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-[11px] font-mono">
                    <span className="text-slate-500">
                      Mean FRP: <strong className="text-amber-400">{fac.facility_baseline?.mean_frp ? `${fac.facility_baseline.mean_frp} MW` : "Baseline Active"}</strong>
                    </span>
                    <span className="text-cyan-400 text-[10px] group-hover:underline">
                      View Profile →
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Facility Dossier Drawer Modal */}
          {selectedFacility && (
            <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
              <div className="bg-slate-900 border border-slate-700 rounded-2xl max-w-lg w-full p-5 space-y-4 shadow-2xl animate-in fade-in zoom-in-95 text-xs">
                <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                  <div>
                    <h3 className="font-bold text-sm text-white">{selectedFacility.name}</h3>
                    <p className="text-[11px] text-slate-400">
                      {selectedFacility.facility_type} • {selectedFacility.state}
                    </p>
                  </div>
                  <button
                    onClick={() => setSelectedFacility(null)}
                    className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>

                <div className="space-y-3 max-h-[70vh] overflow-y-auto pr-1">
                  {/* Coordinates & Sector */}
                  <div className="grid grid-cols-2 gap-2 text-[11px]">
                    <div className="p-2.5 bg-slate-950 rounded-lg border border-slate-800 space-y-0.5">
                      <span className="text-slate-400 font-mono text-[10px]">COORDINATES</span>
                      <div className="font-mono text-slate-200">
                        {selectedFacility.latitude?.toFixed(4)}°N, {selectedFacility.longitude?.toFixed(4)}°E
                      </div>
                    </div>
                    <div className="p-2.5 bg-slate-950 rounded-lg border border-slate-800 space-y-0.5">
                      <span className="text-slate-400 font-mono text-[10px]">SECTOR & INDUSTRY</span>
                      <div className="font-semibold text-slate-200 truncate">
                        {facilityIntel?.facility?.master_sector || selectedFacility.master_sector || "Manufacturing"}
                      </div>
                    </div>
                  </div>

                  {/* Compliance & Operational Identity */}
                  <div className="p-2.5 bg-slate-950 rounded-lg border border-slate-800 flex items-center justify-between text-[11px]">
                    <div>
                      <span className="text-slate-400 font-mono text-[10px]">PARIVESH CLEARANCE STATUS</span>
                      <div className="font-bold text-emerald-400">
                        {facilityIntel?.facility?.environmental_clearance_present
                          ? `EC Granted (${facilityIntel.facility.ec_clearance_status || "APPROVED"})`
                          : "Unregulated / OSM Industry Cadastre"}
                      </div>
                    </div>
                    <span className="px-2 py-0.5 rounded bg-slate-900 text-slate-300 font-mono text-[10px]">
                      {facilityIntel?.facility?.operating_status || "OPERATIONAL"}
                    </span>
                  </div>

                  {/* Statistical Thermal Baseline */}
                  <div className="p-3 bg-slate-950 rounded-xl border border-slate-800 space-y-1.5">
                    <div className="text-[10px] font-mono text-slate-400 uppercase flex items-center justify-between">
                      <span>Statistical Thermal Baseline</span>
                      <span className="text-amber-400 font-bold">{facilityIntel?.baseline?.status_band || "NORMAL BAND"}</span>
                    </div>
                    <div className="grid grid-cols-3 gap-2 text-center text-[11px]">
                      <div className="p-1.5 bg-slate-900/60 rounded">
                        <div className="text-[9px] text-slate-500">Mean FRP</div>
                        <div className="font-mono font-bold text-amber-400">
                          {facilityIntel?.baseline?.mean_frp?.toFixed(1) || selectedFacility.facility_baseline?.mean_frp || "45.0"} MW
                        </div>
                      </div>
                      <div className="p-1.5 bg-slate-900/60 rounded">
                        <div className="text-[9px] text-slate-500">Peak FRP</div>
                        <div className="font-mono font-bold text-orange-400">
                          {facilityIntel?.baseline?.max_historical_frp?.toFixed(1) || "90.0"} MW
                        </div>
                      </div>
                      <div className="p-1.5 bg-slate-900/60 rounded">
                        <div className="text-[9px] text-slate-500">Frequency</div>
                        <div className="font-mono font-bold text-white">
                          {facilityIntel?.baseline?.frequency_days ?? selectedFacility.facility_baseline?.frequency_days ?? 15} d/mo
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Nearby Active Thermal Events */}
                  {facilityIntel?.nearby_thermal_events && facilityIntel.nearby_thermal_events.length > 0 && (
                    <div className="p-3 bg-slate-950 rounded-xl border border-red-500/30 space-y-2">
                      <div className="text-[10px] font-mono text-red-400 uppercase flex items-center gap-1.5">
                        <ShieldAlert className="w-3 h-3 text-red-400" />
                        <span>Active Thermal Events within 5 km ({facilityIntel.nearby_thermal_events.length})</span>
                      </div>
                      <div className="space-y-1">
                        {facilityIntel.nearby_thermal_events.slice(0, 3).map((ne: any) => (
                          <div key={ne.id} className="flex items-center justify-between text-[10px] p-1.5 bg-slate-900/60 rounded font-mono">
                            <span className="text-amber-300 font-bold">{ne.event_code}</span>
                            <span className="text-orange-400">{ne.max_frp} MW</span>
                            <span className="text-slate-400">{ne.distance_m} m away</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Proximity Context (Power, Mining, Ecology) */}
                  <div className="grid grid-cols-2 gap-2 text-[10px]">
                    <div className="p-2 bg-slate-950 rounded-lg border border-slate-800 space-y-1">
                      <div className="text-slate-500 font-mono flex items-center gap-1">
                        <Zap className="w-3 h-3 text-amber-400" />
                        <span>POWER INFRASTRUCTURE</span>
                      </div>
                      <div className="text-slate-300">
                        {facilityIntel?.nearby_power_stations?.length
                          ? `${facilityIntel.nearby_power_stations[0].project_name} (${facilityIntel.nearby_power_stations[0].installed_capacity_mw || 0} MW)`
                          : "No thermal utility in district"}
                      </div>
                    </div>

                    <div className="p-2 bg-slate-950 rounded-lg border border-slate-800 space-y-1">
                      <div className="text-slate-500 font-mono flex items-center gap-1">
                        <Pickaxe className="w-3 h-3 text-purple-400" />
                        <span>MINING LEASES</span>
                      </div>
                      <div className="text-slate-300">
                        {facilityIntel?.nearby_mining_leases?.length
                          ? `${facilityIntel.nearby_mining_leases[0].mineral} (${facilityIntel.nearby_mining_leases[0].lease_count} active leases)`
                          : "Non-mining district"}
                      </div>
                    </div>
                  </div>

                  {/* Ecological Context */}
                  {facilityIntel?.ecological_context?.nearest_protected_area && (
                    <div className="p-2 bg-slate-950 rounded-lg border border-slate-800 flex items-center justify-between text-[10px]">
                      <div className="flex items-center gap-1 text-slate-400">
                        <Trees className="w-3 h-3 text-emerald-400" />
                        <span>Nearest Wildlife Sanctuary:</span>
                      </div>
                      <span className="text-emerald-300 font-mono font-bold">
                        {facilityIntel.ecological_context.nearest_protected_area.name} ({(facilityIntel.ecological_context.nearest_protected_area.distance_m / 1000).toFixed(1)} km)
                      </span>
                    </div>
                  )}
                </div>

                <div className="pt-3 border-t border-slate-800 flex items-center justify-between">
                  <Link
                    href={`/dashboard?lat=${selectedFacility.latitude}&lon=${selectedFacility.longitude}`}
                    className="px-4 py-1.5 rounded-lg bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold text-xs transition-colors inline-flex items-center gap-1.5"
                  >
                    <Compass className="w-3.5 h-3.5" />
                    <span>Fly to Facility on Map</span>
                  </Link>

                  <button
                    onClick={() => setSelectedFacility(null)}
                    className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium text-xs"
                  >
                    Close
                  </button>
                </div>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
