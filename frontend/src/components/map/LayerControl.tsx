"use client";

import React, { useState } from "react";
import { 
  Layers, Eye, EyeOff, Factory, Zap, 
  Pickaxe, Trees, MapPin, Flame, CheckSquare, Square
} from "lucide-react";

export interface GISLayerState {
  thermalEvents: boolean;
  industrialFacilities: boolean;
  powerStations: boolean;
  mining: boolean;
  protectedAreas: boolean;
  lulc: boolean;
  stateBoundaries: boolean;
  districtBoundaries: boolean;
}

interface LayerControlProps {
  layers: GISLayerState;
  onToggleLayer: (layerKey: keyof GISLayerState) => void;
  onToggleAll?: (enable: boolean) => void;
  counts?: Record<string, number>;
}

export default function LayerControl({ 
  layers, 
  onToggleLayer, 
  onToggleAll,
  counts 
}: LayerControlProps) {
  const [isOpen, setIsOpen] = useState(false);

  const layerItems: Array<{
    key: keyof GISLayerState;
    label: string;
    sublabel: string;
    icon: any;
    color: string;
    countKey?: string;
  }> = [
    {
      key: "thermalEvents",
      label: "Thermal Events & Risk",
      sublabel: "VIIRS / MODIS Live",
      icon: Flame,
      color: "#ef4444",
      countKey: "thermal_events"
    },
    {
      key: "industrialFacilities",
      label: "Industrial Facilities",
      sublabel: "35,684 OSM Plants",
      icon: Factory,
      color: "#38bdf8",
      countKey: "industrial_facilities"
    },
    {
      key: "powerStations",
      label: "CEA Power Stations",
      sublabel: "Thermal / Hydro / Gas",
      icon: Zap,
      color: "#f59e0b",
      countKey: "power_stations"
    },
    {
      key: "mining",
      label: "IBM Mining Leases",
      sublabel: "Mineral Blocks",
      icon: Pickaxe,
      color: "#a855f7",
      countKey: "mining"
    },
    {
      key: "protectedAreas",
      label: "Protected Areas (WII)",
      sublabel: "National Parks & ESZ",
      icon: Trees,
      color: "#10b981",
      countKey: "protected_areas"
    },
    {
      key: "lulc",
      label: "Bhuvan LULC Cover",
      sublabel: "ISRO Land Use Classes",
      icon: MapPin,
      color: "#84cc16",
      countKey: "lulc"
    },
    {
      key: "stateBoundaries",
      label: "State Boundaries",
      sublabel: "36 States & UTs",
      icon: Layers,
      color: "#94a3b8",
      countKey: "admin_states"
    },
    {
      key: "districtBoundaries",
      label: "District Boundaries",
      sublabel: "736 Districts",
      icon: Layers,
      color: "#64748b",
      countKey: "admin_districts"
    },
  ];

  const activeCount = Object.values(layers).filter(Boolean).length;

  return (
    <div className="absolute top-4 right-4 z-20 font-sans">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-agni-card/95 hover:bg-slate-800 border border-agni-border text-xs font-semibold text-slate-100 shadow-2xl backdrop-blur-md transition-all hover:scale-105"
      >
        <Layers className="w-4 h-4 text-amber-400" />
        <span>MAP LAYERS</span>
        <span className="px-1.5 py-0.2 rounded-full bg-amber-500/20 text-amber-300 font-mono text-[10px] font-bold border border-amber-500/30">
          {activeCount} / 8
        </span>
      </button>

      {isOpen && (
        <div className="mt-2 w-72 bg-agni-card/95 border border-agni-border rounded-xl shadow-2xl p-3 backdrop-blur-xl animate-in fade-in slide-in-from-top-2 text-xs">
          <div className="flex items-center justify-between pb-2 mb-2 border-b border-slate-800">
            <div className="font-bold text-slate-200 tracking-wider text-[11px] uppercase">
              Tactical PostGIS Overlays
            </div>
            {onToggleAll && (
              <div className="flex items-center gap-1.5 text-[10px]">
                <button
                  onClick={() => onToggleAll(true)}
                  className="text-amber-400 hover:underline"
                >
                  All
                </button>
                <span className="text-slate-600">•</span>
                <button
                  onClick={() => onToggleAll(false)}
                  className="text-slate-400 hover:underline"
                >
                  None
                </button>
              </div>
            )}
          </div>

          <div className="space-y-1 max-h-80 overflow-y-auto pr-1">
            {layerItems.map((item) => {
              const active = layers[item.key];
              const Icon = item.icon;
              return (
                <button
                  key={item.key}
                  onClick={() => onToggleLayer(item.key)}
                  className={`w-full flex items-center justify-between p-2 rounded-lg text-left transition-all ${
                    active
                      ? "bg-slate-800/80 text-white border border-slate-700/60"
                      : "text-slate-400 hover:bg-slate-900/60 border border-transparent"
                  }`}
                >
                  <div className="flex items-center gap-2.5">
                    <div
                      className="w-6 h-6 rounded-md flex items-center justify-center shrink-0"
                      style={{ backgroundColor: `${item.color}22` }}
                    >
                      <Icon className="w-3.5 h-3.5" style={{ color: item.color }} />
                    </div>
                    <div>
                      <div className="font-semibold text-xs text-slate-200 leading-tight">
                        {item.label}
                      </div>
                      <div className="text-[10px] text-slate-400 leading-tight">
                        {item.sublabel}
                      </div>
                    </div>
                  </div>

                  <div>
                    {active ? (
                      <Eye className="w-4 h-4 text-emerald-400" />
                    ) : (
                      <EyeOff className="w-4 h-4 text-slate-600" />
                    )}
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
