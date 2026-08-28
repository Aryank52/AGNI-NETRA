"use client";

import React from "react";
import { Layers, Eye, EyeOff } from "lucide-react";

interface LayerControlProps {
  layers: {
    thermalHotspots: boolean;
    riskHeatmap: boolean;
    facilities: boolean;
    candidates: boolean;
    stateBoundaries: boolean;
  };
  onToggleLayer: (layerKey: keyof LayerControlProps["layers"]) => void;
}

export default function LayerControl({ layers, onToggleLayer }: LayerControlProps) {
  const [isOpen, setIsOpen] = React.useState(false);

  const layerItems = [
    { key: "thermalHotspots" as const, label: "Active Thermal Hotspots", color: "#f97316" },
    { key: "riskHeatmap" as const, label: "Risk Density Heatmap", color: "#ef4444" },
    { key: "facilities" as const, label: "Known Industrial Facilities", color: "#3b82f6" },
    { key: "candidates" as const, label: "Discovered Candidate Sources", color: "#a855f7" },
    { key: "stateBoundaries" as const, label: "State & District Boundaries", color: "#64748b" },
  ];

  return (
    <div className="absolute top-4 right-4 z-20">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-agni-card/90 hover:bg-slate-800 border border-agni-border text-xs font-semibold text-slate-200 shadow-xl backdrop-blur-md transition-all"
      >
        <Layers className="w-4 h-4 text-amber-400" />
        <span>Map Layers</span>
      </button>

      {isOpen && (
        <div className="mt-2 w-64 bg-agni-card/95 border border-agni-border rounded-xl shadow-2xl p-3 backdrop-blur-lg animate-in fade-in slide-in-from-top-2">
          <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-2.5 pb-1.5 border-b border-slate-800">
            Geospatial Overlays
          </div>
          <div className="space-y-1.5">
            {layerItems.map((item) => {
              const active = layers[item.key];
              return (
                <button
                  key={item.key}
                  onClick={() => onToggleLayer(item.key)}
                  className={`w-full flex items-center justify-between px-2.5 py-2 rounded-lg text-xs transition-colors ${
                    active ? "bg-slate-800/80 text-white" : "text-slate-400 hover:bg-slate-900"
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <span
                      className="w-2.5 h-2.5 rounded-full"
                      style={{ backgroundColor: item.color }}
                    />
                    <span className="truncate">{item.label}</span>
                  </div>
                  {active ? (
                    <Eye className="w-3.5 h-3.5 text-emerald-400" />
                  ) : (
                    <EyeOff className="w-3.5 h-3.5 text-slate-500" />
                  )}
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
