"use client";

import React, { useEffect, useRef, useState, useCallback } from "react";
import maplibregl from "maplibre-gl";
import { ThermalEvent } from "@/types";
import { GISLayerState } from "./LayerControl";
import { fetchApi } from "@/lib/api";

interface MapLibreViewProps {
  events: ThermalEvent[];
  selectedEventId?: string | null;
  onSelectEvent?: (event: ThermalEvent) => void;
  selectedState?: string;
  layers?: GISLayerState;
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
  Rajasthan: { center: [74.2179, 27.0238], zoom: 6.2 },
  "Tamil Nadu": { center: [78.6569, 11.1271], zoom: 6.8 },
  "Uttar Pradesh": { center: [80.9462, 26.8467], zoom: 6.5 },
  "West Bengal": { center: [87.855, 22.9868], zoom: 6.8 },
  Karnataka: { center: [75.7139, 15.3173], zoom: 6.8 },
  Telangana: { center: [79.0193, 18.1124], zoom: 7.0 },
  Bihar: { center: [85.3131, 25.0961], zoom: 7.0 },
  Assam: { center: [92.9376, 26.2006], zoom: 7.0 },
  Haryana: { center: [76.0856, 29.0588], zoom: 7.2 },
  India: { center: [79.5, 22.0], zoom: 4.6 },
  ALL: { center: [79.5, 22.0], zoom: 4.6 },
};

export default function MapLibreView({
  events,
  selectedEventId,
  onSelectEvent,
  selectedState = "India",
  layers = {
    thermalEvents: true,
    industrialFacilities: true,
    powerStations: true,
    mining: true,
    protectedAreas: true,
    lulc: true,
    stateBoundaries: true,
    districtBoundaries: true,
  },
}: MapLibreViewProps) {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<maplibregl.Map | null>(null);
  const [mapLoaded, setMapLoaded] = useState<boolean>(false);
  const selectedMarkerRef = useRef<maplibregl.Marker | null>(null);
  const debounceTimerRef = useRef<any>(null);

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
      setupGisLayers(m);
    });

    map.current = m;

    return () => {
      m.remove();
      map.current = null;
    };
  }, []);

  // 2. Setup PostGIS GeoJSON Sources & Layers
  const setupGisLayers = (m: maplibregl.Map) => {
    // A. State Boundaries
    m.addSource("admin_states", {
      type: "geojson",
      data: { type: "FeatureCollection", features: [] },
    });
    m.addLayer({
      id: "admin-states-line",
      type: "line",
      source: "admin_states",
      paint: {
        "line-color": "#94a3b8",
        "line-width": 1.2,
        "line-opacity": 0.6,
      },
    });

    // B. District Boundaries
    m.addSource("admin_districts", {
      type: "geojson",
      data: { type: "FeatureCollection", features: [] },
    });
    m.addLayer({
      id: "admin-districts-line",
      type: "line",
      source: "admin_districts",
      minzoom: 6.5,
      paint: {
        "line-color": "#64748b",
        "line-width": 0.8,
        "line-dasharray": [2, 2],
        "line-opacity": 0.5,
      },
    });

    // C. Protected Areas (WII / FSI)
    m.addSource("protected_areas", {
      type: "geojson",
      data: { type: "FeatureCollection", features: [] },
    });
    m.addLayer({
      id: "protected-areas-fill",
      type: "fill",
      source: "protected_areas",
      paint: {
        "fill-color": "#10b981",
        "fill-opacity": 0.18,
      },
    });
    m.addLayer({
      id: "protected-areas-line",
      type: "line",
      source: "protected_areas",
      paint: {
        "line-color": "#10b981",
        "line-width": 1.5,
        "line-opacity": 0.7,
      },
    });

    // D. Bhuvan LULC
    m.addSource("lulc", {
      type: "geojson",
      data: { type: "FeatureCollection", features: [] },
    });
    m.addLayer({
      id: "lulc-fill",
      type: "fill",
      source: "lulc",
      paint: {
        "fill-color": "#84cc16",
        "fill-opacity": 0.15,
      },
    });
    m.addLayer({
      id: "lulc-line",
      type: "line",
      source: "lulc",
      paint: {
        "line-color": "#84cc16",
        "line-width": 1,
        "line-opacity": 0.5,
      },
    });

    // E. IBM Mining Blocks
    m.addSource("mining", {
      type: "geojson",
      data: { type: "FeatureCollection", features: [] },
    });
    m.addLayer({
      id: "mining-point",
      type: "circle",
      source: "mining",
      paint: {
        "circle-radius": 5,
        "circle-color": "#a855f7",
        "circle-stroke-width": 1.5,
        "circle-stroke-color": "#ffffff",
        "circle-opacity": 0.85,
      },
    });

    // F. CEA Power Stations
    m.addSource("power_stations", {
      type: "geojson",
      data: { type: "FeatureCollection", features: [] },
    });
    m.addLayer({
      id: "power-stations-point",
      type: "circle",
      source: "power_stations",
      paint: {
        "circle-radius": 6,
        "circle-color": "#f59e0b",
        "circle-stroke-width": 1.8,
        "circle-stroke-color": "#ffffff",
        "circle-opacity": 0.9,
      },
    });

    // G. Industrial Facilities (35k+)
    m.addSource("industrial_facilities", {
      type: "geojson",
      data: { type: "FeatureCollection", features: [] },
    });
    m.addLayer({
      id: "industrial-facilities-point",
      type: "circle",
      source: "industrial_facilities",
      paint: {
        "circle-radius": [
          "interpolate",
          ["linear"],
          ["zoom"],
          4,
          2.5,
          8,
          4.5,
          12,
          7,
        ],
        "circle-color": "#38bdf8",
        "circle-stroke-width": 1,
        "circle-stroke-color": "#0284c7",
        "circle-opacity": 0.75,
      },
    });

    // H. Thermal Events & Hotspots
    m.addSource("thermal_events", {
      type: "geojson",
      data: { type: "FeatureCollection", features: [] },
    });
    m.addLayer({
      id: "thermal-events-glow",
      type: "circle",
      source: "thermal_events",
      paint: {
        "circle-radius": [
          "interpolate",
          ["linear"],
          ["zoom"],
          4,
          8,
          8,
          14,
          12,
          22,
        ],
        "circle-color": [
          "match",
          ["get", "risk_level"],
          "CRITICAL",
          "#ef4444",
          "HIGH",
          "#f97316",
          "MODERATE",
          "#eab308",
          "#10b981",
        ],
        "circle-opacity": 0.35,
        "circle-blur": 0.8,
      },
    });
    m.addLayer({
      id: "thermal-events-point",
      type: "circle",
      source: "thermal_events",
      paint: {
        "circle-radius": [
          "interpolate",
          ["linear"],
          ["zoom"],
          4,
          4.5,
          8,
          7.5,
          12,
          11,
        ],
        "circle-color": [
          "match",
          ["get", "risk_level"],
          "CRITICAL",
          "#ef4444",
          "HIGH",
          "#f97316",
          "MODERATE",
          "#eab308",
          "#10b981",
        ],
        "circle-stroke-width": 2,
        "circle-stroke-color": "#ffffff",
        "circle-opacity": 0.95,
      },
    });

    // Click Popups & Feature Selection
    setupLayerClickHandlers(m);

    // Initial Static Boundary Loading
    fetchApi<any>("/gis/admin/states?simplify=0.01")
      .then((data) => {
        if (m.getSource("admin_states")) {
          (m.getSource("admin_states") as maplibregl.GeoJSONSource).setData(data);
        }
      })
      .catch(() => {});

    fetchApi<any>("/gis/protected-areas")
      .then((data) => {
        if (m.getSource("protected_areas")) {
          (m.getSource("protected_areas") as maplibregl.GeoJSONSource).setData(data);
        }
      })
      .catch(() => {});

    fetchApi<any>("/gis/lulc")
      .then((data) => {
        if (m.getSource("lulc")) {
          (m.getSource("lulc") as maplibregl.GeoJSONSource).setData(data);
        }
      })
      .catch(() => {});
  };

  // 3. Interactive Click Popups
  const setupLayerClickHandlers = (m: maplibregl.Map) => {
    // Thermal Event Click
    m.on("click", "thermal-events-point", (e) => {
      if (!e.features || e.features.length === 0) return;
      const feat = e.features[0];
      const p = feat.properties as any;

      const popupHtml = `
        <div class="p-2 space-y-2 text-slate-100 font-sans min-w-[210px]">
          <div class="flex items-center justify-between border-b border-slate-700 pb-1">
            <span class="font-mono text-xs font-bold text-amber-400">${p.event_code}</span>
            <span class="text-[10px] font-mono px-1.5 py-0.2 rounded font-bold" style="background: ${
              p.risk_level === "CRITICAL" ? "#ef444433" : "#f9731633"
            }; color: ${p.risk_level === "CRITICAL" ? "#ef4444" : "#f97316"};">
              ${p.risk_level}
            </span>
          </div>
          <div class="space-y-1 text-xs">
            <div><strong>Predicted:</strong> <span class="text-amber-300 font-semibold">${p.predicted_class}</span></div>
            <div><strong>Peak FRP:</strong> <span class="font-mono font-bold text-white">${p.max_frp} MW</span></div>
            <div><strong>Confidence:</strong> <span class="font-mono text-emerald-400">${((p.confidence || 0.8) * 100).toFixed(0)}%</span></div>
            <div><strong>State:</strong> ${p.state} (${p.district || ""})</div>
          </div>
          <div class="pt-1.5">
            <button id="btn-select-${p.id}" class="w-full py-1 rounded bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold text-[11px] uppercase tracking-wide transition-colors">
              Inspect 7-Layer Dossier →
            </button>
          </div>
        </div>
      `;

      new maplibregl.Popup({ offset: 12 })
        .setLngLat(e.lngLat)
        .setHTML(popupHtml)
        .addTo(m);

      // Find matched event object
      const matched = events.find((ev) => ev.id === p.id);
      if (matched && onSelectEvent) {
        onSelectEvent(matched);
      }

      setTimeout(() => {
        const btn = document.getElementById(`btn-select-${p.id}`);
        if (btn && matched && onSelectEvent) {
          btn.onclick = () => onSelectEvent(matched);
        }
      }, 100);
    });

    // Facility Click
    m.on("click", "industrial-facilities-point", (e) => {
      if (!e.features || e.features.length === 0) return;
      const p = e.features[0].properties as any;
      new maplibregl.Popup({ offset: 10 })
        .setLngLat(e.lngLat)
        .setHTML(`
          <div class="p-2 space-y-1 text-xs text-slate-100 font-sans min-w-[190px]">
            <div class="font-bold text-cyan-300 text-xs">${p.name}</div>
            <div class="text-[11px] text-slate-300">${p.facility_type}</div>
            <div class="text-[10px] text-slate-400 font-mono">Sector: ${p.master_sector}</div>
            <div class="text-[10px] text-slate-400">Location: ${p.state}, ${p.district}</div>
            <div class="text-[10px] text-amber-400 font-mono">FIRMS 1km Hits: ${p.firms_detections_1km}</div>
          </div>
        `)
        .addTo(m);
    });

    // Power Station Click
    m.on("click", "power-stations-point", (e) => {
      if (!e.features || e.features.length === 0) return;
      const p = e.features[0].properties as any;
      new maplibregl.Popup({ offset: 10 })
        .setLngLat(e.lngLat)
        .setHTML(`
          <div class="p-2 space-y-1 text-xs text-slate-100 font-sans min-w-[190px]">
            <div class="font-bold text-amber-400 text-xs">${p.name}</div>
            <div class="text-[10px] text-slate-300">Org: ${p.cea_organisation}</div>
            <div class="text-[10px] text-slate-300">Prime Mover: ${p.prime_mover}</div>
            <div class="text-[10px] text-slate-400">State: ${p.state}</div>
          </div>
        `)
        .addTo(m);
    });

    // Mining Click
    m.on("click", "mining-point", (e) => {
      if (!e.features || e.features.length === 0) return;
      const p = e.features[0].properties as any;
      new maplibregl.Popup({ offset: 10 })
        .setLngLat(e.lngLat)
        .setHTML(`
          <div class="p-2 space-y-1 text-xs text-slate-100 font-sans min-w-[180px]">
            <div class="font-bold text-purple-300 text-xs">${p.name}</div>
            <div class="text-[10px] text-amber-300 font-mono">Mineral: ${p.mineral}</div>
            <div class="text-[10px] text-slate-400">${p.state}, ${p.district}</div>
            <div class="text-[10px] text-slate-400 font-mono">FIRMS 2km: ${p.firms_count_2km}</div>
          </div>
        `)
        .addTo(m);
    });

    // Cursor pointer triggers
    const layerNames = [
      "thermal-events-point",
      "industrial-facilities-point",
      "power-stations-point",
      "mining-point",
    ];
    layerNames.forEach((layer) => {
      m.on("mouseenter", layer, () => (m.getCanvas().style.cursor = "pointer"));
      m.on("mouseleave", layer, () => (m.getCanvas().style.cursor = ""));
    });
  };

  // 4. Viewport-Aware Dynamic PostGIS Querying
  const refreshViewportLayers = useCallback(() => {
    if (!map.current || !mapLoaded) return;
    const m = map.current;
    const bounds = m.getBounds();
    const zoom = m.getZoom();
    const bboxStr = `${bounds.getWest().toFixed(4)},${bounds.getSouth().toFixed(4)},${bounds.getEast().toFixed(4)},${bounds.getNorth().toFixed(4)}`;

    // Query Facilities in current bbox
    if (layers.industrialFacilities && m.getSource("industrial_facilities")) {
      fetchApi<any>(`/gis/industrial-facilities?bbox=${bboxStr}&limit=400`)
        .then((data) => {
          if (m.getSource("industrial_facilities")) {
            (m.getSource("industrial_facilities") as maplibregl.GeoJSONSource).setData(data);
          }
        })
        .catch(() => {});
    }

    // Query Power Stations
    if (layers.powerStations && m.getSource("power_stations")) {
      fetchApi<any>(`/gis/power-stations?bbox=${bboxStr}&limit=200`)
        .then((data) => {
          if (m.getSource("power_stations")) {
            (m.getSource("power_stations") as maplibregl.GeoJSONSource).setData(data);
          }
        })
        .catch(() => {});
    }

    // Query Mining
    if (layers.mining && m.getSource("mining")) {
      fetchApi<any>(`/gis/mining?bbox=${bboxStr}&limit=200`)
        .then((data) => {
          if (m.getSource("mining")) {
            (m.getSource("mining") as maplibregl.GeoJSONSource).setData(data);
          }
        })
        .catch(() => {});
    }
  }, [mapLoaded, layers]);

  // Debounced Map Movement Listener
  useEffect(() => {
    if (!map.current || !mapLoaded) return;
    const m = map.current;

    const onMove = () => {
      if (debounceTimerRef.current) clearTimeout(debounceTimerRef.current);
      debounceTimerRef.current = setTimeout(() => {
        refreshViewportLayers();
      }, 400);
    };

    m.on("moveend", onMove);
    m.on("zoomend", onMove);

    // Initial load
    refreshViewportLayers();

    return () => {
      m.off("moveend", onMove);
      m.off("zoomend", onMove);
    };
  }, [mapLoaded, refreshViewportLayers]);

  // 5. Update Thermal Events GeoJSON Source from Prop
  useEffect(() => {
    if (!map.current || !mapLoaded) return;
    const m = map.current;

    const features = events.map((e) => ({
      type: "Feature",
      geometry: {
        type: "Point",
        coordinates: [e.longitude, e.latitude],
      },
      properties: {
        id: e.id,
        event_code: e.event_code,
        state: e.state,
        district: e.district,
        max_frp: e.max_frp,
        predicted_class: e.prediction?.predicted_class || "Uncertain",
        confidence: e.prediction?.confidence || 0.8,
        risk_level: e.risk?.risk_level || "LOW",
        risk_score: e.risk?.risk_score || 35.0,
      },
    }));

    if (m.getSource("thermal_events")) {
      (m.getSource("thermal_events") as maplibregl.GeoJSONSource).setData({
        type: "FeatureCollection",
        features,
      } as any);
    }
  }, [events, mapLoaded]);

  // 6. Camera Flying on State Selection Change
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

  // 7. Layer Visibility Toggle Updates
  useEffect(() => {
    if (!map.current || !mapLoaded) return;
    const m = map.current;

    const setVis = (layerId: string, isVis: boolean) => {
      if (m.getLayer(layerId)) {
        m.setLayoutProperty(layerId, "visibility", isVis ? "visible" : "none");
      }
    };

    setVis("thermal-events-point", layers.thermalEvents);
    setVis("thermal-events-glow", layers.thermalEvents);
    setVis("industrial-facilities-point", layers.industrialFacilities);
    setVis("power-stations-point", layers.powerStations);
    setVis("mining-point", layers.mining);
    setVis("protected-areas-fill", layers.protectedAreas);
    setVis("protected-areas-line", layers.protectedAreas);
    setVis("lulc-fill", layers.lulc);
    setVis("lulc-line", layers.lulc);
    setVis("admin-states-line", layers.stateBoundaries);
    setVis("admin-districts-line", layers.districtBoundaries);
  }, [layers, mapLoaded]);

  // 8. Highlight Selected Event with Pulsing Marker
  useEffect(() => {
    if (!map.current || !mapLoaded) return;

    if (selectedMarkerRef.current) {
      selectedMarkerRef.current.remove();
      selectedMarkerRef.current = null;
    }

    if (!selectedEventId) return;
    const sel = events.find((e) => e.id === selectedEventId);
    if (!sel) return;

    const el = document.createElement("div");
    el.className = "relative flex items-center justify-center pointer-events-none";
    el.innerHTML = `
      <div class="absolute w-10 h-10 rounded-full bg-amber-400/40 animate-ping"></div>
      <div class="w-6 h-6 rounded-full border-2 border-white bg-amber-500 shadow-xl flex items-center justify-center">
        <span class="text-[10px] font-black text-slate-950">★</span>
      </div>
    `;

    selectedMarkerRef.current = new maplibregl.Marker({ element: el })
      .setLngLat([sel.longitude, sel.latitude])
      .addTo(map.current);
  }, [selectedEventId, events, mapLoaded]);

  return (
    <div className="relative w-full h-full bg-slate-950 overflow-hidden">
      <div ref={mapContainer} className="w-full h-full" />
    </div>
  );
}
