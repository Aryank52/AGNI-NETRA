"use client";

import React, { useEffect, useRef, useState } from "react";
import maplibregl from "maplibre-gl";
import { ThermalEvent } from "@/types";

interface MapLibreViewProps {
  events: ThermalEvent[];
  selectedEventId?: string | null;
  onSelectEvent?: (event: ThermalEvent) => void;
  selectedState?: string;
  layers?: {
    thermalHotspots: boolean;
    riskHeatmap: boolean;
    facilities: boolean;
    candidates: boolean;
    stateBoundaries: boolean;
  };
}

// State Centroids and Zooms for Quick Focus
const STATE_CENTROIDS: Record<string, { center: [number, number]; zoom: number }> = {
  Gujarat: { center: [71.1924, 22.2587], zoom: 6.8 },
  "Madhya Pradesh": { center: [78.6569, 23.4733], zoom: 6.5 },
  Chhattisgarh: { center: [81.8661, 21.2787], zoom: 6.8 },
  Odisha: { center: [84.8035, 20.9517], zoom: 6.8 },
  Punjab: { center: [75.3412, 31.1471], zoom: 7.2 },
  "Andhra Pradesh": { center: [80.5167, 15.9129], zoom: 6.5 },
  Jharkhand: { center: [85.2799, 23.6102], zoom: 7.0 },
  Maharashtra: { center: [75.7139, 19.7515], zoom: 6.5 },
  India: { center: [79.5, 22.0], zoom: 4.6 },
  ALL: { center: [79.5, 22.0], zoom: 4.6 },
};

export default function MapLibreView({
  events,
  selectedEventId,
  onSelectEvent,
  selectedState = "India",
  layers = {
    thermalHotspots: true,
    riskHeatmap: true,
    facilities: true,
    candidates: true,
    stateBoundaries: true,
  },
}: MapLibreViewProps) {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<maplibregl.Map | null>(null);
  const [mapLoaded, setMapLoaded] = useState(false);
  const markersRef = useRef<maplibregl.Marker[]>([]);

  // 1. Initialize MapLibre GL
  useEffect(() => {
    if (!mapContainer.current || map.current) return;

    const initial = STATE_CENTROIDS[selectedState] || STATE_CENTROIDS.India;

    const m = new maplibregl.Map({
      container: mapContainer.current,
      style: "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
      center: initial.center,
      zoom: initial.zoom,
      attributionControl: false,
    });

    m.addControl(new maplibregl.NavigationControl({ showCompass: true }), "top-left");
    m.addControl(new maplibregl.ScaleControl({ unit: "metric" }), "bottom-left");

    m.on("load", () => {
      setMapLoaded(true);
    });

    map.current = m;

    return () => {
      m.remove();
      map.current = null;
    };
  }, []);

  // 2. Handle State Change / Camera Movement
  useEffect(() => {
    if (!map.current) return;
    const target = STATE_CENTROIDS[selectedState] || STATE_CENTROIDS.India;
    map.current.flyTo({
      center: target.center,
      zoom: target.zoom,
      essential: true,
      duration: 1600,
    });
  }, [selectedState]);

  // 3. Render Tactical Dynamic Markers
  useEffect(() => {
    if (!map.current || !mapLoaded) return;

    // Clear previous markers
    markersRef.current.forEach((m) => m.remove());
    markersRef.current = [];

    events.forEach((evt) => {
      const riskLevel = evt.risk?.risk_level || "LOW";
      const isSelected = evt.id === selectedEventId;
      const isCandidate = evt.facility_status === "CANDIDATE";

      // Color mapping
      let markerColor = "#10b981"; // Low
      if (riskLevel === "CRITICAL") markerColor = "#ef4444";
      else if (riskLevel === "HIGH") markerColor = "#f97316";
      else if (riskLevel === "MODERATE") markerColor = "#eab308";

      // Custom HTML Marker Element
      const el = document.createElement("div");
      el.className = "cursor-pointer group";

      el.innerHTML = `
        <div class="relative flex items-center justify-center">
          ${
            riskLevel === "CRITICAL" || isSelected
              ? `<div class="absolute w-8 h-8 rounded-full animate-ping opacity-75" style="background-color: ${markerColor};"></div>`
              : ""
          }
          <div class="w-6 h-6 rounded-full flex items-center justify-center shadow-lg border-2 ${
            isSelected ? "scale-125 border-white ring-4 ring-amber-400/50" : "border-slate-900"
          }" style="background-color: ${markerColor};">
            <span class="text-[9px] font-bold text-slate-950">${isCandidate ? "C" : "⚡"}</span>
          </div>
        </div>
      `;

      // Popup Content
      const popupHtml = `
        <div class="p-2 space-y-2 text-slate-100 font-sans min-w-[200px]">
          <div class="flex items-center justify-between border-b border-slate-700 pb-1.5">
            <span class="font-mono text-xs font-bold text-amber-400">${evt.event_code}</span>
            <span class="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded font-bold" style="background: ${markerColor}33; color: ${markerColor};">
              ${riskLevel} RISK
            </span>
          </div>
          <div class="space-y-1 text-xs">
            <div><strong>Classification:</strong> <span class="text-amber-300">${evt.prediction?.predicted_class || "Uncertain"}</span></div>
            <div><strong>Peak FRP:</strong> <span class="font-mono text-white">${evt.max_frp.toFixed(1)} MW</span></div>
            <div><strong>Confidence:</strong> <span class="font-mono text-emerald-400">${((evt.prediction?.confidence || 0.8) * 100).toFixed(0)}%</span></div>
            <div><strong>Location:</strong> ${evt.state} (${evt.latitude.toFixed(3)}°N, ${evt.longitude.toFixed(3)}°E)</div>
            <div><strong>Context:</strong> ${evt.facility_status === "KNOWN" ? "Known Facility" : (isCandidate ? "Candidate Discovery (USP)" : "Uncataloged")}</div>
          </div>
          <div class="pt-2">
            <button id="btn-${evt.id}" class="w-full py-1 rounded bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold text-[11px] uppercase tracking-wide transition-colors">
              Inspect Dossier →
            </button>
          </div>
        </div>
      `;

      const popup = new maplibregl.Popup({ offset: 18, closeButton: false }).setHTML(popupHtml);

      const marker = new maplibregl.Marker({ element: el })
        .setLngLat([evt.longitude, evt.latitude])
        .setPopup(popup)
        .addTo(map.current!);

      el.addEventListener("click", () => {
        if (onSelectEvent) {
          onSelectEvent(evt);
        }
        setTimeout(() => {
          const btn = document.getElementById(`btn-${evt.id}`);
          if (btn && onSelectEvent) {
            btn.onclick = () => onSelectEvent(evt);
          }
        }, 100);
      });

      markersRef.current.push(marker);
    });
  }, [events, selectedEventId, mapLoaded, onSelectEvent]);

  return (
    <div className="relative w-full h-full bg-slate-950 overflow-hidden">
      <div ref={mapContainer} className="w-full h-full" />
    </div>
  );
}
