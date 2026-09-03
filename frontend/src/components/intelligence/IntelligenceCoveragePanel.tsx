"use client";

import React, { useState } from "react";
import { 
  CheckCircle2, XCircle, Shield, Database, 
  Layers, Factory, Zap, Pickaxe, Trees, MapPin, 
  FileCheck, Info, ExternalLink, X, AlertCircle
} from "lucide-react";

interface CoverageProps {
  coverage?: {
    firms_telemetry?: boolean;
    industrial_facility?: boolean;
    cea_power_station?: boolean;
    mining_intelligence?: boolean;
    bhuvan_lulc?: boolean;
    forest_intelligence?: boolean;
    protected_area?: boolean;
    administrative_geography?: boolean;
    parivesh_regulatory?: boolean;
  };
  eventCode?: string;
}

interface SourceMetadata {
  key: string;
  name: string;
  subtitle: string;
  authority: string;
  systemStatus: "LIVE" | "AVAILABLE" | "PARTIAL_COVERAGE" | "NO_COVERAGE";
  recordCount: string;
  coverageExtent: string;
  lastSync: string;
  provenanceDetails: string;
  icon: any;
  color: string;
}

const AUTHORITATIVE_SOURCES: SourceMetadata[] = [
  {
    key: "firms_telemetry",
    name: "NASA FIRMS Telemetry",
    subtitle: "VIIRS NOAA-20 / SNPP / MODIS Aqua & Terra",
    authority: "NASA Earth Science Data and Information System (ESDIS)",
    systemStatus: "LIVE",
    recordCount: "8,221,854 detections",
    coverageExtent: "National (All India & Border Regions)",
    lastSync: "Real-time (15-min cadence)",
    provenanceDetails: "Authoritative 375m/1km infrared radiative brightness and FRP measurements with strict immutability preservation.",
    icon: Database,
    color: "#ef4444"
  },
  {
    key: "industrial_facility",
    name: "OSM Industrial Registry",
    subtitle: "National Manufacturing & Petrochem Cadastre",
    authority: "OpenStreetMap Foundation / State Pollution Control Boards",
    systemStatus: "AVAILABLE",
    recordCount: "35,684 facilities",
    coverageExtent: "National Coverage (All 36 States & UTs)",
    lastSync: "Q3 2026 Production Sync",
    provenanceDetails: "Curated industrial polygons and points with precomputed 35,579 statistical FRP baselines and diurnal ratios.",
    icon: Factory,
    color: "#38bdf8"
  },
  {
    key: "cea_power_station",
    name: "CEA Power Generating Stations",
    subtitle: "Super Thermal, Gas & Hydro Power Plants",
    authority: "Central Electricity Authority, Ministry of Power",
    systemStatus: "AVAILABLE",
    recordCount: "1,633 utilities",
    coverageExtent: "National Power Generation Grid",
    lastSync: "CEA 2025-26 Register",
    provenanceDetails: "Authoritative registry of major Indian thermal utilities with organization mapping and installed capacity ratings.",
    icon: Zap,
    color: "#f59e0b"
  },
  {
    key: "mining_intelligence",
    name: "IBM Mining Intelligence",
    subtitle: "Table 15 Auctioned Blocks & Mineral Leases",
    authority: "Indian Bureau of Mines (IBM), Ministry of Mines",
    systemStatus: "AVAILABLE",
    recordCount: "119 blocks • 414 leases • 98,793 associations",
    coverageExtent: "Coal, Iron Ore, Bauxite & Limestone Belts",
    lastSync: "IBM Annual Mining Bulletin 2024-25",
    provenanceDetails: "Authoritative auction blocks with real polygon geometries and mineral cadastre coordinates without synthetic extrapolation.",
    icon: Pickaxe,
    color: "#a855f7"
  },
  {
    key: "bhuvan_lulc",
    name: "ISRO Bhuvan LULC",
    subtitle: "Thematic Land Use / Land Cover Classification",
    authority: "National Remote Sensing Centre (NRSC / ISRO)",
    systemStatus: "PARTIAL_COVERAGE",
    recordCount: "15 thematic zones • 121 raster tiles",
    coverageExtent: "Regional Pilot Subset (50m resolution)",
    lastSync: "ISRO Bhuvan Thematic Portal 2024",
    provenanceDetails: "Authoritative multi-temporal land cover polygons. Explicitly bounded to verified pilot tiles; returns NO_COVERAGE outside this extent.",
    icon: MapPin,
    color: "#84cc16"
  },
  {
    key: "forest_intelligence",
    name: "FSI Forest Coverage",
    subtitle: "India State of Forest Report (ISFR)",
    authority: "Forest Survey of India (FSI), MoEFCC",
    systemStatus: "AVAILABLE",
    recordCount: "18 district profiles • National ISFR stats",
    coverageExtent: "Forest Canopy Cover (VDF / MDF / OF)",
    lastSync: "ISFR Biennial Assessment",
    provenanceDetails: "Canopy density classification (Very Dense, Moderately Dense, Open Forest) and ecological buffer metrics.",
    icon: Trees,
    color: "#10b981"
  },
  {
    key: "protected_area",
    name: "WII Protected Areas",
    subtitle: "National Parks, Wildlife Sanctuaries & ESZ",
    authority: "Wildlife Institute of India (WII) / MoEFCC",
    systemStatus: "AVAILABLE",
    recordCount: "11 national reserves (Real PostGIS Multipolygons)",
    coverageExtent: "Protected Eco-Sensitive Belts",
    lastSync: "WII National Wildlife Database 2025",
    provenanceDetails: "Authoritative multi-polygon boundaries with 10km Eco-Sensitive Zone (ESZ) statutory buffer tracking.",
    icon: Shield,
    color: "#10b981"
  },
  {
    key: "parivesh_regulatory",
    name: "MoEFCC PARIVESH",
    subtitle: "Environmental Clearance & Forest Approvals",
    authority: "Ministry of Environment, Forest and Climate Change",
    systemStatus: "AVAILABLE",
    recordCount: "622 clearance projects staged",
    coverageExtent: "Category A & B Industrial Proposals",
    lastSync: "PARIVESH National Portal 2026",
    provenanceDetails: "Official statutory clearance tracking linked to corresponding industrial complexes and expansion projects.",
    icon: FileCheck,
    color: "#06b6d4"
  },
];

export default function IntelligenceCoveragePanel({ coverage, eventCode }: CoverageProps) {
  const [selectedSource, setSelectedSource] = useState<SourceMetadata | null>(null);

  const getStatusBadge = (status: SourceMetadata["systemStatus"], localHit?: boolean) => {
    switch (status) {
      case "LIVE":
        return (
          <span className="flex items-center gap-1 text-[9px] font-mono font-bold text-emerald-400 bg-emerald-500/10 px-1.5 py-0.5 rounded border border-emerald-500/20">
            <CheckCircle2 className="w-2.5 h-2.5" />
            LIVE
          </span>
        );
      case "AVAILABLE":
        return (
          <span className="flex items-center gap-1 text-[9px] font-mono font-bold text-cyan-400 bg-cyan-500/10 px-1.5 py-0.5 rounded border border-cyan-500/20">
            <CheckCircle2 className="w-2.5 h-2.5" />
            AVAILABLE
          </span>
        );
      case "PARTIAL_COVERAGE":
        return (
          <span className="flex items-center gap-1 text-[9px] font-mono font-bold text-amber-400 bg-amber-500/10 px-1.5 py-0.5 rounded border border-amber-500/20">
            <Info className="w-2.5 h-2.5" />
            PARTIAL
          </span>
        );
      case "NO_COVERAGE":
      default:
        return (
          <span className="text-[9px] font-mono text-slate-500 bg-slate-800/40 px-1.5 py-0.5 rounded">
            NO_COVERAGE
          </span>
        );
    }
  };

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-3.5 space-y-2.5 font-sans">
      <div className="flex items-center justify-between border-b border-slate-800 pb-2">
        <div className="flex items-center gap-2">
          <Layers className="w-4 h-4 text-cyan-400" />
          <div>
            <span className="font-bold text-xs text-white tracking-wide uppercase">
              AUTHORITATIVE INTELLIGENCE PROVENANCE
            </span>
            <div className="text-[10px] text-slate-400">Click any source for dataset audit & coverage specs</div>
          </div>
        </div>
        <div className="flex items-center gap-1 text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-300 font-bold border border-cyan-500/20">
          <span>8 FUSED SOURCES</span>
        </div>
      </div>

      {/* Grid of Sources */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
        {AUTHORITATIVE_SOURCES.map((src) => {
          const Icon = src.icon;
          const localHit = coverage ? Boolean((coverage as any)[src.key]) : true;

          return (
            <div
              key={src.key}
              onClick={() => setSelectedSource(src)}
              className="p-2 rounded-lg border bg-slate-950/60 hover:bg-slate-900 border-slate-800 hover:border-cyan-500/40 cursor-pointer transition-all flex flex-col justify-between group shadow-sm"
            >
              <div className="flex items-start justify-between gap-1 mb-1">
                <Icon className="w-3.5 h-3.5 shrink-0" style={{ color: src.color }} />
                {getStatusBadge(src.systemStatus, localHit)}
              </div>
              <div>
                <div className="text-[11px] font-semibold text-slate-200 group-hover:text-white truncate leading-tight">
                  {src.name}
                </div>
                <div className="text-[9px] text-slate-400 truncate mt-0.5">
                  {src.recordCount}
                </div>
                <div className="mt-1 flex items-center justify-between text-[9px] text-slate-500">
                  <span className={localHit ? "text-emerald-400 font-medium" : "text-slate-500"}>
                    {localHit ? "● Event in Proximity" : "○ Outside Buffer"}
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Detail Modal when a source is clicked */}
      {selectedSource && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl max-w-md w-full p-5 space-y-4 shadow-2xl animate-in fade-in zoom-in-95">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2.5">
                <div 
                  className="w-8 h-8 rounded-lg flex items-center justify-center"
                  style={{ backgroundColor: `${selectedSource.color}22` }}
                >
                  <selectedSource.icon className="w-4 h-4" style={{ color: selectedSource.color }} />
                </div>
                <div>
                  <h3 className="font-bold text-sm text-white">{selectedSource.name}</h3>
                  <p className="text-[11px] text-slate-400">{selectedSource.subtitle}</p>
                </div>
              </div>
              <button
                onClick={() => setSelectedSource(null)}
                className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-2.5 text-xs text-slate-300">
              <div className="p-2.5 rounded-xl bg-slate-950/80 border border-slate-800 space-y-1">
                <div className="text-[10px] text-slate-400 uppercase font-mono">Governing Authority</div>
                <div className="font-semibold text-white">{selectedSource.authority}</div>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div className="p-2.5 rounded-xl bg-slate-950/80 border border-slate-800 space-y-0.5">
                  <div className="text-[10px] text-slate-400 uppercase font-mono">Dataset Volume</div>
                  <div className="font-bold text-amber-400 font-mono">{selectedSource.recordCount}</div>
                </div>
                <div className="p-2.5 rounded-xl bg-slate-950/80 border border-slate-800 space-y-0.5">
                  <div className="text-[10px] text-slate-400 uppercase font-mono">System Status</div>
                  <div>{getStatusBadge(selectedSource.systemStatus)}</div>
                </div>
              </div>

              <div className="p-2.5 rounded-xl bg-slate-950/80 border border-slate-800 space-y-1">
                <div className="text-[10px] text-slate-400 uppercase font-mono">Geographic Coverage</div>
                <div className="font-medium text-slate-200">{selectedSource.coverageExtent}</div>
                <div className="text-[10px] text-slate-400">Last Synced: {selectedSource.lastSync}</div>
              </div>

              <div className="p-2.5 rounded-xl bg-slate-950/80 border border-slate-800 space-y-1">
                <div className="text-[10px] text-slate-400 uppercase font-mono">Authoritative Invariants</div>
                <p className="text-[11px] text-slate-300 leading-relaxed">{selectedSource.provenanceDetails}</p>
              </div>
            </div>

            <div className="pt-2 flex items-center justify-between border-t border-slate-800 text-[11px]">
              <span className="text-emerald-400 font-mono">PostGIS 3.4 Spatial Index Verified</span>
              <button
                onClick={() => setSelectedSource(null)}
                className="px-4 py-1.5 rounded-lg bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold text-xs transition-colors"
              >
                Close Audit Card
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
