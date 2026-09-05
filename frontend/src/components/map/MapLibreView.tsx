"use client";

import React, { useEffect, useRef, useState, useCallback } from "react";
import maplibregl from "maplibre-gl";
import { ThermalEvent } from "@/types";
import { GISLayerState, LayerOpacityState, DEFAULT_LAYER_OPACITIES } from "./LayerControl";
import { fetchApi } from "@/lib/api";
import { formatNumber, formatFrp, formatPercent } from "@/lib/formatters";

interface MapLibreViewProps {
  events: ThermalEvent[];
  selectedEventId?: string | null;
  onSelectEvent?: (event: ThermalEvent) => void;
  selectedState?: string;
  selectedDistrict?: string;
  layers?: GISLayerState;
  opacities?: LayerOpacityState;
  onNavigateEntity?: (entity: { lat: number; lon: number; zoom?: number }) => void;
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
  selectedDistrict = "ALL",
  layers = {
    thermalEvents: true,
    industrialFacilities: true,
    powerStations: true,
    mining: true,
    protectedAreas: true,
    lulc: true,
    stateBoundaries: true,
    districtBoundaries: true,
    parivesh: true,
  },
  opacities = DEFAULT_LAYER_OPACITIES,
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
        "line-opacity": opacities.stateBoundaries ?? 0.6,
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
      minzoom: 6.0,
      paint: {
        "line-color": "#64748b",
        "line-width": 0.8,
        "line-dasharray": [2, 2],
        "line-opacity": opacities.districtBoundaries ?? 0.5,
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
        "fill-opacity": (opacities.protectedAreas ?? 0.7) * 0.25,
      },
    });
    m.addLayer({
      id: "protected-areas-line",
      type: "line",
      source: "protected_areas",
      paint: {
        "line-color": "#10b981",
        "line-width": 1.5,
        "line-opacity": opacities.protectedAreas ?? 0.7,
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
        "fill-opacity": (opacities.lulc ?? 0.65) * 0.25,
      },
    });
    m.addLayer({
      id: "lulc-line",
      type: "line",
      source: "lulc",
      paint: {
        "line-color": "#84cc16",
        "line-width": 1.2,
        "line-opacity": opacities.lulc ?? 0.65,
      },
    });

    // E. IBM Mining Blocks & Mineral Points
    m.addSource("mining", {
      type: "geojson",
      data: { type: "FeatureCollection", features: [] },
    });
    m.addLayer({
      id: "mining-fill",
      type: "fill",
      source: "mining",
      filter: ["==", "$type", "Polygon"],
      paint: {
        "fill-color": "#a855f7",
        "fill-opacity": (opacities.mining ?? 0.85) * 0.3,
      },
    });
    m.addLayer({
      id: "mining-line",
      type: "line",
      source: "mining",
      filter: ["==", "$type", "Polygon"],
      paint: {
        "line-color": "#c084fc",
        "line-width": 1.8,
        "line-opacity": opacities.mining ?? 0.85,
      },
    });
    m.addLayer({
      id: "mining-point",
      type: "circle",
      source: "mining",
      filter: ["==", "$type", "Point"],
      paint: {
        "circle-radius": 5.5,
        "circle-color": "#a855f7",
        "circle-stroke-width": 1.5,
        "circle-stroke-color": "#ffffff",
        "circle-opacity": opacities.mining ?? 0.85,
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
        "circle-radius": 6.5,
        "circle-color": "#f59e0b",
        "circle-stroke-width": 1.8,
        "circle-stroke-color": "#ffffff",
        "circle-opacity": opacities.powerStations ?? 0.9,
      },
    });

    // G. PARIVESH Environmental Clearances (Layer 8)
    m.addSource("parivesh", {
      type: "geojson",
      data: { type: "FeatureCollection", features: [] },
    });
    m.addLayer({
      id: "parivesh-point",
      type: "circle",
      source: "parivesh",
      paint: {
        "circle-radius": 5,
        "circle-color": "#06b6d4",
        "circle-stroke-width": 1.5,
        "circle-stroke-color": "#ffffff",
        "circle-opacity": opacities.parivesh ?? 0.85,
      },
    });

    // H. Industrial Facilities (35k+)
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
          7.5,
        ],
        "circle-color": "#38bdf8",
        "circle-stroke-width": 1,
        "circle-stroke-color": "#0284c7",
        "circle-opacity": opacities.industrialFacilities ?? 0.85,
      },
    });

    // I. Thermal Events & Hotspots
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
          16,
          12,
          24,
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
        "circle-opacity": opacities.thermalEvents ?? 0.95,
      },
    });

    // Click Popups & Feature Selection
    setupLayerClickHandlers(m);

    // Initial Static Boundary & Multi-Layer Loading
    fetchApi<any>("/gis/admin/states?simplify=0.01")
      .then((data) => {
        if (m.getSource("admin_states")) {
          (m.getSource("admin_states") as maplibregl.GeoJSONSource).setData(data);
        }
      })
      .catch(() => {});

    fetchApi<any>("/gis/admin/districts?simplify=0.008&limit=800")
      .then((data) => {
        if (m.getSource("admin_districts")) {
          (m.getSource("admin_districts") as maplibregl.GeoJSONSource).setData(data);
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
        <div class="p-2 space-y-2 text-slate-100 font-sans min-w-[220px]">
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
            <div><strong>Peak FRP:</strong> <span class="font-mono font-bold text-white">${formatNumber(p.max_frp)} MW</span></div>
            <div><strong>Confidence:</strong> <span class="font-mono text-emerald-400">${formatPercent(p.confidence, 0, "80%")}</span></div>
            <div><strong>Location:</strong> ${p.state || ""} ${p.district ? `(${p.district})` : ""}</div>
          </div>
          <div class="pt-1.5">
            <button id="btn-select-${p.id}" class="w-full py-1.5 rounded bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold text-[11px] uppercase tracking-wide transition-colors shadow">
              Open 7-Layer Dossier →
            </button>
          </div>
        </div>
      `;

      new maplibregl.Popup({ offset: 12 })
        .setLngLat(e.lngLat)
        .setHTML(popupHtml)
        .addTo(m);

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
          <div class="p-2 space-y-1.5 text-xs text-slate-100 font-sans min-w-[210px]">
            <div class="font-bold text-cyan-300 text-xs">${p.name}</div>
            <div class="text-[11px] text-slate-300">${p.facility_type || "Industrial Plant"}</div>
            <div class="text-[10px] text-slate-400 font-mono">Sector: ${p.master_sector || "Manufacturing"}</div>
            <div class="text-[10px] text-slate-400">Location: ${p.state || ""}, ${p.district || ""}</div>
            <div class="text-[10px] text-amber-400 font-mono">FIRMS 1km Hits: ${p.firms_detections_1km || 0}</div>
            <div class="pt-1 border-t border-slate-700/80 text-[10px]">
              <span class="text-emerald-400">● Real PostGIS Cadastre</span>
            </div>
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
          <div class="p-2 space-y-1 text-xs text-slate-100 font-sans min-w-[210px]">
            <div class="font-bold text-amber-400 text-xs">${p.name}</div>
            <div class="text-[10px] text-slate-300">Org: ${p.cea_organisation || "CEA Utility"}</div>
            <div class="text-[10px] text-slate-300">Prime Mover: ${p.prime_mover || "Thermal"}</div>
            <div class="text-[10px] text-slate-400">State: ${p.state || ""}, ${p.district || ""}</div>
            <div class="text-[10px] text-cyan-400 font-mono">Capacity: ${p.installed_capacity_mw || "Variable"} MW</div>
          </div>
        `)
        .addTo(m);
    });

    // Mining Click
    const handleMiningClick = (e: any) => {
      if (!e.features || e.features.length === 0) return;
      const p = e.features[0].properties as any;
      new maplibregl.Popup({ offset: 10 })
        .setLngLat(e.lngLat)
        .setHTML(`
          <div class="p-2 space-y-1 text-xs text-slate-100 font-sans min-w-[200px]">
            <div class="font-bold text-purple-300 text-xs">${p.name}</div>
            <div class="text-[10px] text-amber-300 font-mono">Mineral: ${p.mineral || "Mineral Resource"}</div>
            <div class="text-[10px] text-slate-400">Location: ${p.state || ""}, ${p.district || ""}</div>
            <div class="text-[10px] text-slate-400 font-mono">FIRMS 2km: ${p.firms_count_2km || 0} detections</div>
            <div class="text-[10px] text-purple-400">${p.preferred_bidder ? `Bidder: ${p.preferred_bidder}` : "IBM Auction Block"}</div>
          </div>
        `)
        .addTo(m);
    };
    m.on("click", "mining-point", handleMiningClick);
    m.on("click", "mining-fill", handleMiningClick);

    // PARIVESH Click
    m.on("click", "parivesh-point", (e) => {
      if (!e.features || e.features.length === 0) return;
      const p = e.features[0].properties as any;
      new maplibregl.Popup({ offset: 10 })
        .setLngLat(e.lngLat)
        .setHTML(`
          <div class="p-2 space-y-1 text-xs text-slate-100 font-sans min-w-[210px]">
            <div class="font-bold text-cyan-400 text-xs">${p.name}</div>
            <div class="text-[10px] text-slate-300">Proponent: ${p.proponent || "Industrial Proponent"}</div>
            <div class="text-[10px] text-slate-400">Type: ${p.project_type || "Clearance"} • Cat ${p.category || "A"}</div>
            <div class="text-[10px] text-slate-400">Location: ${p.state || ""}, ${p.district || ""}</div>
            <div class="text-[10px] text-emerald-400 font-mono font-bold">Status: ${p.clearance_status || "GRANTED"}</div>
          </div>
        `)
        .addTo(m);
    });

    // Protected Area Click
    m.on("click", "protected-areas-fill", (e) => {
      if (!e.features || e.features.length === 0) return;
      const p = e.features[0].properties as any;
      new maplibregl.Popup({ offset: 10 })
        .setLngLat(e.lngLat)
        .setHTML(`
          <div class="p-2 space-y-1 text-xs text-slate-100 font-sans min-w-[190px]">
            <div class="font-bold text-emerald-400 text-xs">${p.name}</div>
            <div class="text-[10px] text-slate-300">${p.pa_type || "Protected Reserve"}</div>
            <div class="text-[10px] text-slate-400">State: ${p.state || ""}, ${p.district || ""}</div>
            <div class="text-[10px] text-slate-400 font-mono">Area: ${formatNumber(p.area_sqkm)} sq km</div>
          </div>
        `)
        .addTo(m);
    });

    // Cursor pointer triggers
    const interactiveLayers = [
      "thermal-events-point",
      "industrial-facilities-point",
      "power-stations-point",
      "mining-point",
      "mining-fill",
      "parivesh-point",
      "protected-areas-fill",
    ];
    interactiveLayers.forEach((layer) => {
      m.on("mouseenter", layer, () => (m.getCanvas().style.cursor = "pointer"));
      m.on("mouseleave", layer, () => (m.getCanvas().style.cursor = ""));
    });
  };

  // 4. Viewport-Aware Dynamic PostGIS Querying (Debounced)
  const refreshViewportLayers = useCallback(() => {
    if (!map.current || !mapLoaded) return;
    const m = map.current;
    const bounds = m.getBounds();
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

    // Query PARIVESH Clearances
    if (layers.parivesh && m.getSource("parivesh")) {
      fetchApi<any>(`/gis/parivesh?bbox=${bboxStr}&limit=250`)
        .then((data) => {
          if (m.getSource("parivesh")) {
            (m.getSource("parivesh") as maplibregl.GeoJSONSource).setData(data);
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
        max_frp: typeof e.max_frp === "number" ? e.max_frp : 0,
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

  // 6. Camera Flying on State or District Selection Change
  useEffect(() => {
    if (!map.current || !mapLoaded) return;

    if (selectedDistrict && selectedDistrict !== "ALL") {
      // Query exact PostGIS Bounding Box for District
      const stateParam = selectedState && selectedState !== "ALL" && selectedState !== "India"
        ? `&state=${encodeURIComponent(selectedState)}`
        : "";
      fetchApi<{ bbox: [number, number, number, number]; centroid: [number, number] }>(
        `/geography/district-bounds?district=${encodeURIComponent(selectedDistrict)}${stateParam}`
      )
        .then((data) => {
          if (data && data.bbox && map.current) {
            const [minLon, minLat, maxLon, maxLat] = data.bbox;
            map.current.fitBounds(
              [[minLon, minLat], [maxLon, maxLat]],
              { padding: 60, duration: 1800, maxZoom: 11 }
            );
          }
        })
        .catch(() => {
          // Fallback to state centroid
          const target = STATE_CENTROIDS[selectedState] || STATE_CENTROIDS.India;
          map.current?.flyTo({ center: target.center, zoom: target.zoom, duration: 1600 });
        });
    } else if (selectedState) {
      const target = STATE_CENTROIDS[selectedState] || STATE_CENTROIDS.India;
      map.current.flyTo({
        center: target.center,
        zoom: target.zoom,
        essential: true,
        duration: 1600,
      });
    }
  }, [selectedDistrict, selectedState, mapLoaded]);

  // 7. Layer Visibility & Opacity Toggle Updates
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
    setVis("mining-fill", layers.mining);
    setVis("mining-line", layers.mining);
    setVis("parivesh-point", layers.parivesh);
    setVis("protected-areas-fill", layers.protectedAreas);
    setVis("protected-areas-line", layers.protectedAreas);
    setVis("lulc-fill", layers.lulc);
    setVis("lulc-line", layers.lulc);
    setVis("admin-states-line", layers.stateBoundaries);
    setVis("admin-districts-line", layers.districtBoundaries);

    // Apply Opacities
    if (m.getLayer("thermal-events-point")) {
      m.setPaintProperty("thermal-events-point", "circle-opacity", opacities.thermalEvents ?? 0.95);
    }
    if (m.getLayer("industrial-facilities-point")) {
      m.setPaintProperty("industrial-facilities-point", "circle-opacity", opacities.industrialFacilities ?? 0.85);
    }
    if (m.getLayer("power-stations-point")) {
      m.setPaintProperty("power-stations-point", "circle-opacity", opacities.powerStations ?? 0.9);
    }
    if (m.getLayer("mining-point")) {
      m.setPaintProperty("mining-point", "circle-opacity", opacities.mining ?? 0.85);
    }
    if (m.getLayer("mining-fill")) {
      m.setPaintProperty("mining-fill", "fill-opacity", (opacities.mining ?? 0.85) * 0.3);
    }
    if (m.getLayer("parivesh-point")) {
      m.setPaintProperty("parivesh-point", "circle-opacity", opacities.parivesh ?? 0.85);
    }
    if (m.getLayer("protected-areas-fill")) {
      m.setPaintProperty("protected-areas-fill", "fill-opacity", (opacities.protectedAreas ?? 0.7) * 0.25);
    }
    if (m.getLayer("lulc-fill")) {
      m.setPaintProperty("lulc-fill", "fill-opacity", (opacities.lulc ?? 0.65) * 0.25);
    }
  }, [layers, opacities, mapLoaded]);

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
