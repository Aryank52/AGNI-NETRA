"use client";

import React from "react";
import { 
  CheckCircle2, XCircle, Shield, Database, 
  Layers, Factory, Zap, Pickaxe, Trees, MapPin, FileCheck 
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

export default function IntelligenceCoveragePanel({ coverage, eventCode }: CoverageProps) {
  const sources = [
    {
      key: "firms_telemetry",
      name: "NASA FIRMS Telemetry",
      subtitle: "VIIRS NOAA-20 / SNPP / MODIS",
      icon: Database,
      available: coverage?.firms_telemetry ?? true,
    },
    {
      key: "industrial_facility",
      name: "OSM Industrial Registry",
      subtitle: "35,684 Facilities + Baselines",
      icon: Factory,
      available: coverage?.industrial_facility ?? false,
    },
    {
      key: "cea_power_station",
      name: "CEA Power Utilities",
      subtitle: "Thermal & Hydro Generation",
      icon: Zap,
      available: coverage?.cea_power_station ?? false,
    },
    {
      key: "mining_intelligence",
      name: "IBM Mining Intelligence",
      subtitle: "Auction Blocks & Lease Context",
      icon: Pickaxe,
      available: coverage?.mining_intelligence ?? false,
    },
    {
      key: "bhuvan_lulc",
      name: "ISRO Bhuvan LULC",
      subtitle: "Thematic Land Use / Cover",
      icon: MapPin,
      available: coverage?.bhuvan_lulc ?? false,
    },
    {
      key: "forest_intelligence",
      name: "FSI Forest Coverage",
      subtitle: "ISFR District Canopy Density",
      icon: Trees,
      available: coverage?.forest_intelligence ?? false,
    },
    {
      key: "protected_area",
      name: "WII Protected Areas",
      subtitle: "National Parks & 10km ESZ",
      icon: Shield,
      available: coverage?.protected_area ?? false,
    },
    {
      key: "parivesh_regulatory",
      name: "MoEFCC PARIVESH",
      subtitle: "Environmental Clearances",
      icon: FileCheck,
      available: coverage?.parivesh_regulatory ?? false,
    },
  ];

  const activeCount = sources.filter((s) => s.available).length;

  return (
    <div className="bg-agni-card/90 border border-agni-border rounded-xl p-3.5 space-y-3 font-sans">
      <div className="flex items-center justify-between border-b border-slate-800 pb-2">
        <div className="flex items-center gap-2">
          <Layers className="w-4 h-4 text-cyan-400" />
          <span className="font-bold text-xs text-white tracking-wide">
            INTELLIGENCE PROVENANCE
          </span>
        </div>
        <div className="flex items-center gap-1.5 text-[11px] font-mono">
          <span className="text-slate-400">Fused:</span>
          <span className="px-2 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300 font-bold border border-cyan-500/30">
            {activeCount} / {sources.length} SOURCES
          </span>
        </div>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
        {sources.map((src) => {
          const Icon = src.icon;
          return (
            <div
              key={src.key}
              className={`p-2 rounded-lg border transition-all flex flex-col justify-between ${
                src.available
                  ? "bg-slate-900/80 border-emerald-500/30 text-slate-200"
                  : "bg-slate-950/40 border-slate-800/80 text-slate-500"
              }`}
            >
              <div className="flex items-start justify-between gap-1 mb-1">
                <Icon
                  className={`w-3.5 h-3.5 shrink-0 ${
                    src.available ? "text-emerald-400" : "text-slate-600"
                  }`}
                />
                {src.available ? (
                  <span className="flex items-center gap-1 text-[10px] font-mono font-bold text-emerald-400 bg-emerald-500/10 px-1 py-0.2 rounded">
                    <CheckCircle2 className="w-2.5 h-2.5" />
                    LIVE
                  </span>
                ) : (
                  <span className="text-[9px] font-mono text-slate-500 bg-slate-800/40 px-1 py-0.2 rounded">
                    NO_COVERAGE
                  </span>
                )}
              </div>
              <div>
                <div className="text-[11px] font-semibold truncate leading-tight">
                  {src.name}
                </div>
                <div className="text-[9px] text-slate-400 truncate mt-0.5">
                  {src.subtitle}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
