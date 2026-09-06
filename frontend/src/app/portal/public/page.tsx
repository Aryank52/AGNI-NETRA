"use client";

import React, { useState, useEffect } from "react";
import dynamic from "next/dynamic";
import Header from "@/components/layout/Header";
import Sidebar from "@/components/layout/Sidebar";
import { fetchApi } from "@/lib/api";
import { safeArray, safeNumber } from "@/lib/formatters";
import { 
  ShieldCheck, AlertTriangle, Wind, 
  MapPin, CheckCircle2, Info, Eye, Shield, RefreshCw,
  Clock, PhoneCall, ArrowRight, Activity, Map as MapIcon
} from "lucide-react";
import PageHeader from "@/components/common/PageHeader";
import EmptyState from "@/components/common/EmptyState";
import { CardSkeleton, MapLoadingSkeleton } from "@/components/common/Skeletons";
import { ThermalEvent } from "@/types";

// Public-safe MapLibre Dynamic Import (SSR: false)
const MapLibreView = dynamic(() => import("@/components/map/MapLibreView"), {
  ssr: false,
  loading: () => <MapLoadingSkeleton />,
});

// Public-safe layer configuration (strips industrial blueprints, ML features, sensitive infrastructure)
const PUBLIC_SAFE_LAYERS = {
  thermalEvents: true,
  industrialFacilities: false,
  powerStations: false,
  mining: false,
  protectedAreas: true,
  lulc: false,
  stateBoundaries: true,
  districtBoundaries: true,
  parivesh: false,
};

export default function PublicPortalPage() {
  const [data, setData] = useState<any | null>(null);
  const [events, setEvents] = useState<ThermalEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedSeverity, setSelectedSeverity] = useState<string>("ALL");

  const loadData = () => {
    setLoading(true);
    Promise.all([
      fetchApi<any>("/portals/public/overview").catch(() => null),
      fetchApi<any>("/portals/public/hazard-map").catch(() => null),
    ])
      .then(([overviewRes, hazardRes]) => {
        if (overviewRes) setData(overviewRes);
        if (hazardRes && Array.isArray(hazardRes.events)) {
          setEvents(hazardRes.events);
        }
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadData();
  }, []);

  const publicAdvisories = safeArray(data?.public_advisories);
  const filteredAdvisories = selectedSeverity === "ALL" 
    ? publicAdvisories 
    : publicAdvisories.filter((adv: any) => (adv.severity || "MODERATE").toUpperCase() === selectedSeverity);

  return (
    <div className="min-h-screen bg-agni-navy flex flex-col selection:bg-amber-500 selection:text-slate-950 font-sans">
      <Header />

      <div className="flex flex-1 overflow-hidden">
        <Sidebar />

        <main className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6 max-w-6xl mx-auto w-full">
          {/* Standardized Page Header */}
          <PageHeader
            category="PUBLIC SAFETY & CITIZEN ADVISORY"
            title="National Thermal Safety & Public Impact Portal"
            description="Clear regional hazard alerts, smoke dispersion guidance, and citizen protective instructions derived from earth observation satellites."
            icon={<ShieldCheck className="w-6 h-6 text-emerald-400" />}
            actions={
              <button
                onClick={loadData}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 text-xs transition-colors"
                title="Refresh Public Advisories"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin text-emerald-400" : ""}`} />
                <span>Update Advisories</span>
              </button>
            }
          />

          {/* Citizen Notice & Privacy Boundary */}
          <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 flex items-start gap-3 text-xs text-slate-300">
            <Shield className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
            <div className="space-y-1">
              <div className="font-bold text-emerald-300 text-xs uppercase flex items-center gap-2">
                <span>Citizen Public Safety Notice</span>
                <span className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-slate-800 text-slate-400 border border-slate-700">
                  Public Domain
                </span>
              </div>
              <p className="text-[11px] text-slate-400 leading-relaxed">
                This portal presents verified high-level regional advisories to protect citizens from air quality surges, forest fire proximity, and smoke downwind exposure. Internal industrial blueprints, raw ML feature vectors, and proprietary telemetry are restricted to statutory response authorities.
              </p>
            </div>
          </div>

          {/* Section 1: PUBLIC SAFETY STATUS */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="p-4 rounded-xl bg-agni-card border border-agni-border space-y-1">
              <div className="text-[10px] text-slate-400 font-mono uppercase">Monitored Regions</div>
              <div className="text-2xl font-extrabold text-white font-mono">
                36 States & UTs
              </div>
              <p className="text-[11px] text-slate-400">Continuous 15-min satellite sweep</p>
            </div>

            <div className="p-4 rounded-xl bg-agni-card border border-agni-border space-y-1">
              <div className="text-[10px] text-slate-400 font-mono uppercase">Active Public Hazards</div>
              <div className="text-2xl font-extrabold text-amber-400 font-mono">
                {data?.total_active_hazards || publicAdvisories.length || 0} Advisories
              </div>
              <p className="text-[11px] text-slate-400">Exceeding standard advisory threshold</p>
            </div>

            <div className="p-4 rounded-xl bg-agni-card border border-agni-border space-y-1">
              <div className="text-[10px] text-slate-400 font-mono uppercase">General Air Quality Precaution</div>
              <div className="text-2xl font-extrabold text-emerald-400 font-mono">Level 2</div>
              <p className="text-[11px] text-slate-400">Sensitive groups wear masks downwind</p>
            </div>

            <div className="p-4 rounded-xl bg-agni-card border border-agni-border space-y-1">
              <div className="text-[10px] text-slate-400 font-mono uppercase">Emergency Helpline</div>
              <div className="text-2xl font-extrabold text-red-400 font-mono flex items-center gap-1.5">
                <PhoneCall className="w-5 h-5 text-red-400" />
                <span>112 / 1078</span>
              </div>
              <p className="text-[11px] text-slate-400">National Disaster Helpline (24x7)</p>
            </div>
          </div>

          {/* Section 2: PUBLIC-SAFE REGIONAL HAZARD MAP */}
          <div id="map" className="p-5 rounded-2xl bg-agni-card border border-agni-border space-y-3">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <MapIcon className="w-4 h-4 text-emerald-400" />
                <h2 className="text-sm font-bold uppercase tracking-wider text-white">
                  Regional Hazard Advisory Map
                </h2>
              </div>
              <div className="flex items-center gap-2 text-xs text-slate-400">
                <span className="w-2.5 h-2.5 rounded-full bg-red-500 inline-block"></span>
                <span>Thermal Hotspot</span>
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 inline-block ml-2"></span>
                <span>Protected Reserve</span>
              </div>
            </div>

            <div className="h-[360px] sm:h-[420px] rounded-xl overflow-hidden border border-slate-800 relative">
              <MapLibreView 
                events={events}
                layers={PUBLIC_SAFE_LAYERS}
                selectedState="India"
              />
            </div>
            <p className="text-[11px] text-slate-400">
              * Map displays regional heat anomalies and administrative boundaries. Sensitive infrastructure layouts and industrial assets are hidden for civil safety.
            </p>
          </div>

          {/* Section 3: CURRENT ADVISORIES & HAZARDS */}
          <div id="alerts" className="space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <h2 className="text-sm font-bold uppercase tracking-wider text-slate-200 flex items-center gap-2">
                <Wind className="w-4 h-4 text-cyan-400" />
                <span>Active Regional Thermal & Smoke Advisories</span>
                <span className="text-xs font-normal text-slate-400">({filteredAdvisories.length})</span>
              </h2>

              <div className="flex items-center gap-1.5 bg-slate-900 p-1 rounded-lg border border-slate-800 text-xs">
                {["ALL", "CRITICAL", "HIGH", "MODERATE"].map((sev) => (
                  <button
                    key={sev}
                    onClick={() => setSelectedSeverity(sev)}
                    className={`px-2.5 py-1 rounded text-[11px] font-semibold transition-all ${
                      selectedSeverity === sev
                        ? "bg-amber-500 text-slate-950 font-bold"
                        : "text-slate-400 hover:text-white"
                    }`}
                  >
                    {sev}
                  </button>
                ))}
              </div>
            </div>

            {loading ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <CardSkeleton />
                <CardSkeleton />
              </div>
            ) : filteredAdvisories.length === 0 ? (
              <EmptyState 
                title="No Active Regional Advisories" 
                description="All monitored districts are currently operating within baseline ambient thresholds. No active citizen warnings."
                icon={CheckCircle2}
              />
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {filteredAdvisories.map((adv: any, idx: number) => {
                  const severity = (adv.severity || "MODERATE").toUpperCase();
                  const isHighOrCritical = severity === "CRITICAL" || severity === "HIGH";

                  return (
                    <div
                      key={adv.id || idx}
                      className="p-5 rounded-2xl bg-agni-card border border-agni-border hover:border-emerald-500/40 transition-all space-y-3.5 shadow-lg"
                    >
                      <div className="flex items-center justify-between border-b border-slate-800 pb-2.5">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-bold text-white">{adv.title || `Regional Advisory #${idx + 1}`}</span>
                        </div>
                        <span className={`text-[9px] uppercase font-mono px-2 py-0.5 rounded font-bold border ${
                          severity === "CRITICAL"
                            ? "bg-red-500/20 text-red-300 border-red-500/40 animate-pulse"
                            : severity === "HIGH"
                            ? "bg-amber-500/20 text-amber-300 border-amber-500/40"
                            : "bg-blue-500/20 text-blue-300 border-blue-500/40"
                        }`}>
                          {severity} ADVISORY
                        </span>
                      </div>

                      {/* Plain Language Explanation */}
                      <div className="space-y-1.5">
                        <div className="text-[11px] font-bold text-slate-300 uppercase tracking-wide">
                          Public Impact & Situation:
                        </div>
                        <p className="text-xs text-slate-300 leading-relaxed">
                          {adv.advisory_text || "Elevated thermal signatures detected in this district. Potential downwind smoke dispersal and localized air quality degradation."}
                        </p>
                      </div>

                      {/* Safety Guidance */}
                      <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1">
                        <div className="text-[10px] font-bold text-emerald-400 uppercase tracking-wide flex items-center gap-1.5">
                          <ShieldCheck className="w-3.5 h-3.5" />
                          <span>Recommended Citizen Action:</span>
                        </div>
                        <p className="text-[11px] text-slate-300 leading-normal">
                          {isHighOrCritical 
                            ? "Keep windows closed in downwind areas. Vulnerable individuals (asthma/elderly) should wear N95 masks outdoors and avoid strenuous activities."
                            : "Exercise routine caution. Avoid unauthorized agricultural burning. Report unexpected smoke plumes to local emergency services."
                          }
                        </p>
                      </div>

                      <div className="flex items-center justify-between pt-2 border-t border-slate-800 text-[11px] text-slate-400 font-mono">
                        <span className="flex items-center gap-1 text-slate-300">
                          <MapPin className="w-3.5 h-3.5 text-slate-500" />
                          {adv.location || "Monitored District"}
                        </span>
                        <span className="flex items-center gap-1 text-slate-400">
                          <Clock className="w-3.5 h-3.5 text-slate-500" />
                          <span>Satellite Verified</span>
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Section 4: CITIZEN SAFETY GUIDANCE (NOTICE -> UNDERSTAND -> ACT) */}
          <div id="guidance" className="p-6 rounded-2xl bg-agni-card border border-agni-border space-y-5">
            <div>
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-emerald-400" />
                <span>Citizen Action Framework: Notice → Understand → Act</span>
              </h2>
              <p className="text-xs text-slate-400 mt-1">
                How citizens and local communities should interpret thermal warnings and protect their households.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-4 rounded-xl bg-slate-900/70 border border-slate-800 space-y-2">
                <div className="w-8 h-8 rounded-lg bg-blue-500/20 text-blue-400 border border-blue-500/30 flex items-center justify-center font-bold text-sm">
                  1
                </div>
                <h3 className="text-xs font-bold text-white uppercase tracking-wider">
                  Notice the Advisory
                </h3>
                <p className="text-xs text-slate-300 leading-relaxed">
                  Satellites detect intense surface heat (forest fires, crop residue burning, or flaring). Check if your district is highlighted on the advisory map.
                </p>
              </div>

              <div className="p-4 rounded-xl bg-slate-900/70 border border-slate-800 space-y-2">
                <div className="w-8 h-8 rounded-lg bg-amber-500/20 text-amber-400 border border-amber-500/30 flex items-center justify-center font-bold text-sm">
                  2
                </div>
                <h3 className="text-xs font-bold text-white uppercase tracking-wider">
                  Understand the Risk
                </h3>
                <p className="text-xs text-slate-300 leading-relaxed">
                  Smoke plumes carry fine particulate matter (PM2.5). Wind can carry particulates up to 25 km downwind, causing respiratory irritation.
                </p>
              </div>

              <div className="p-4 rounded-xl bg-slate-900/70 border border-slate-800 space-y-2">
                <div className="w-8 h-8 rounded-lg bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 flex items-center justify-center font-bold text-sm">
                  3
                </div>
                <h3 className="text-xs font-bold text-white uppercase tracking-wider">
                  Take Action
                </h3>
                <p className="text-xs text-slate-300 leading-relaxed">
                  Close external ventilation, use air purifiers if available, stay hydrated, and contact 112 or local fire brigades if you witness an uncontained blaze.
                </p>
              </div>
            </div>

            {/* Emergency Helplines Strip */}
            <div className="p-4 rounded-xl bg-red-950/30 border border-red-500/40 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
              <div className="flex items-center gap-2.5">
                <PhoneCall className="w-5 h-5 text-red-400 shrink-0" />
                <div>
                  <div className="font-bold text-white">Need Emergency Assistance?</div>
                  <div className="text-[11px] text-slate-300">
                    If you are in immediate danger of a forest or industrial fire, call statutory helplines immediately.
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-3 font-mono font-bold text-xs shrink-0">
                <span className="px-2.5 py-1 rounded bg-slate-900 text-red-300 border border-red-500/40">
                  Dial 112 (ERSS)
                </span>
                <span className="px-2.5 py-1 rounded bg-slate-900 text-amber-300 border border-amber-500/40">
                  NDMA: 1078
                </span>
                <span className="px-2.5 py-1 rounded bg-slate-900 text-white border border-slate-700">
                  Fire: 101
                </span>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
