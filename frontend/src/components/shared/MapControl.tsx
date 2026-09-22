"use client";

import React, { useState } from "react";
import { 
  Layers, Compass, Maximize2, Minimize2, 
  MapPin, Eye, EyeOff, Sliders, Check
} from "lucide-react";

export interface MapControlLayers {
  thermalEvents: boolean;
  industrialFacilities: boolean;
  powerStations: boolean;
  mining: boolean;
  protectedAreas: boolean;
  lulc: boolean;
  stateBoundaries: boolean;
  districtBoundaries: boolean;
}

export interface MapControlProps {
  layers: MapControlLayers;
  onToggleLayer: (layerKey: keyof MapControlLayers) => void;
  onResetIndiaCenter?: () => void;
  onToggleFullscreen?: () => void;
  isFullscreen?: boolean;
  className?: string;
}

export default function MapControl({
  layers,
  onToggleLayer,
  onResetIndiaCenter,
  onToggleFullscreen,
  isFullscreen = false,
  className = "",
}: MapControlProps) {
  const [layersOpen, setLayersOpen] = useState(false);

  const layerItems: { key: keyof MapControlLayers; label: string; color: string }[] = [
    { key: "thermalEvents", label: "Thermal Hotspots (FIRMS)", color: "bg-red-500" },
    { key: "industrialFacilities", label: "Industrial Facilities (35.5k)", color: "bg-amber-400" },
    { key: "powerStations", label: "CEA Power (502 Stations / 1,633 Units)", color: "bg-cyan-400" },
    { key: "mining", label: "IBM Mining Leases", color: "bg-purple-400" },
    { key: "protectedAreas", label: "FSI Protected Forests", color: "bg-emerald-500" },
    { key: "lulc", label: "ISRO Bhuvan LULC", color: "bg-lime-400" },
    { key: "stateBoundaries", label: "State Borders (36 UT/States)", color: "bg-slate-300" },
    { key: "districtBoundaries", label: "District Borders (735 Districts)", color: "bg-slate-400" },
  ];

  return (
    <div className={`flex flex-col gap-2 select-none font-mono text-xs ${className}`}>
      {/* Action Buttons Strip */}
      <div className="flex items-center gap-1.5 p-1 bg-slate-950/90 backdrop-blur border border-slate-800 rounded-lg shadow-xl">
        <button
          type="button"
          onClick={() => setLayersOpen(!layersOpen)}
          title="Toggle Multi-Source GIS Layers"
          className={`p-2 rounded-md transition-all flex items-center gap-1.5 ${
            layersOpen
              ? "bg-amber-500 text-slate-950 font-bold"
              : "text-slate-300 hover:bg-slate-800 hover:text-white"
          }`}
        >
          <Layers className="w-3.5 h-3.5" />
          <span className="hidden sm:inline text-[11px]">GIS Layers</span>
        </button>

        {onResetIndiaCenter && (
          <button
            type="button"
            onClick={onResetIndiaCenter}
            title="Focus Sovereign Territory of India"
            className="p-2 rounded-md text-slate-300 hover:bg-slate-800 hover:text-amber-400 transition-all"
          >
            <Compass className="w-3.5 h-3.5" />
          </button>
        )}

        {onToggleFullscreen && (
          <button
            type="button"
            onClick={onToggleFullscreen}
            title={isFullscreen ? "Exit Fullscreen" : "Fullscreen View"}
            className="p-2 rounded-md text-slate-300 hover:bg-slate-800 hover:text-amber-400 transition-all"
          >
            {isFullscreen ? (
              <Minimize2 className="w-3.5 h-3.5" />
            ) : (
              <Maximize2 className="w-3.5 h-3.5" />
            )}
          </button>
        )}
      </div>

      {/* Layers Popover Menu */}
      {layersOpen && (
        <div className="w-64 p-3 rounded-xl bg-slate-950/95 backdrop-blur-md border border-slate-800 shadow-2xl space-y-2 animate-in fade-in slide-in-from-top-2">
          <div className="flex items-center justify-between pb-2 border-b border-slate-800">
            <span className="font-bold text-[11px] text-amber-300 tracking-wider">
              SOVEREIGN GIS LAYERS
            </span>
            <span className="text-[10px] text-slate-500 font-mono">PostGIS 3.4</span>
          </div>

          <div className="space-y-1">
            {layerItems.map((item) => {
              const active = layers[item.key];
              return (
                <button
                  key={item.key}
                  type="button"
                  onClick={() => onToggleLayer(item.key)}
                  className={`w-full px-2.5 py-1.5 rounded-lg text-left text-[11px] transition-all flex items-center justify-between ${
                    active
                      ? "bg-slate-900 text-slate-200"
                      : "text-slate-500 hover:bg-slate-900/50"
                  }`}
                >
                  <div className="flex items-center gap-2 truncate">
                    <span className={`w-2 h-2 rounded-full shrink-0 ${item.color} ${active ? "opacity-100 ring-2 ring-current/20" : "opacity-30"}`} />
                    <span className="truncate">{item.label}</span>
                  </div>
                  {active ? (
                    <Eye className="w-3.5 h-3.5 text-amber-400 shrink-0 ml-1.5" />
                  ) : (
                    <EyeOff className="w-3.5 h-3.5 text-slate-600 shrink-0 ml-1.5" />
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
