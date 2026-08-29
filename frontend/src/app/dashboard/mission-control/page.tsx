"use client";

import React, { useEffect, useState, useRef } from "react";
import maplibregl from "maplibre-gl";
import { fetchApi } from "@/lib/api";
import { 
  Radio, Play, Crosshair, Cpu, Clock, ShieldAlert,
  Flame, CheckCircle2, AlertTriangle, Activity, Database,
  Layers, MapPin, BarChart3, RefreshCw, Eye, ArrowRight, Zap, Info, History
} from "lucide-react";

interface Scenario {
  id: string;
  name: string;
  scenario_type: string;
  description: string;
  target_state: string;
  target_district?: string;
  target_lat: number;
  target_lon: number;
  target_facility?: string | null;
  expected_class: string;
  expected_risk_level: string;
  parameters: {
    frp_mw: number;
    brightness_k: number;
    confidence: number;
    day_night: string;
    detection_count: number;
    anomaly_z_score: number;
  };
}

interface SatelliteInfo {
  satellite_id: string;
  name: string;
  orbit_type: string;
  altitude_km: number;
  inclination_deg: number;
  orbital_period_min: number;
  swath_width_km: number;
  ground_speed_km_s: number;
  subsatellite_latitude: number;
  subsatellite_longitude: number;
  telemetry_mode: string;
  mission_status: string;
  sensors: Array<{
    sensor_id: string;
    name: string;
    type: string;
    resolution_m: number;
    swath_width_km: number;
    status: string;
  }>;
}

interface BenchmarkData {
  observation_to_telemetry_ms: number;
  telemetry_to_ingestion_ms: number;
  clustering_ms: number;
  gis_enrichment_ms: number;
  ml_inference_ms: number;
  shap_explanation_ms: number;
  risk_evaluation_ms: number;
  total_processing_ms: number;
  target_fps_or_hz: number;
}

interface ScenarioExecutionResult {
  status: string;
  mode: string;
  scenario: {
    id: string;
    name: string;
    type: string;
    target: string;
    expected_class: string;
    expected_risk_level: string;
  };
  satellite: {
    id: string;
    sensor: string;
    observations_generated: number;
  };
  event?: {
    event_id: string;
    event_code: string;
    state: string;
    district?: string;
    avg_frp: number;
    max_frp: number;
    facility_status: string;
    predicted_class: string;
    confidence: number;
    risk_level: string;
    risk_score: number;
    shap_summary: string;
  };
  benchmark: BenchmarkData;
  validation: {
    expected_class: string;
    predicted_class: string;
    is_match: boolean;
  };
}

const PIPELINE_21_STEPS = [
  "1. Scenario Initiated", "2. Spacecraft Tasked", "3. Orbit Propagated", "4. Sensor Activated",
  "5. Observation Radiance Captured", "6. Telemetry Packet Formatted", "7. Downlink Ingested",
  "8. Normalized Thermal Observation", "9. Spatiotemporal DBSCAN", "10. PostGIS Spatial Indexing",
  "11. Bhuvan LULC Classified", "12. 18-D Feature Vector Assembled", "13. 7-Class XGBoost Inference",
  "14. Shannon Entropy Uncertainty", "15. Isolation Forest Anomaly Radar", "16. Empirical Baseline Surge Test",
  "17. SHAP TreeExplainer Waterfall", "18. Multi-Criteria Risk Matrix", "19. Incident Alert Dispatched",
  "20. HITL Verification Queue", "21. Intelligence Dossier Resolved"
];

export default function MissionControlPage() {
  const [satelliteInfo, setSatelliteInfo] = useState<SatelliteInfo | null>(null);
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [selectedScenarioId, setSelectedScenarioId] = useState<string>("scenario-01-industrial-surge");
  const [activeTab, setActiveTab] = useState<"SCENARIOS" | "TASKING" | "REPLAY">("SCENARIOS");
  
  // Execution & Simulation State
  const [isExecuting, setIsExecuting] = useState(false);
  const [executionStep, setExecutionStep] = useState(0);
  const [executionResult, setExecutionResult] = useState<ScenarioExecutionResult | null>(null);
  const [telemetryLogs, setTelemetryLogs] = useState<any[]>([]);
  const [activeDataMode, setActiveDataMode] = useState<"SIMULATION" | "LIVE" | "HISTORICAL">("SIMULATION");

  // Tasking Form
  const [taskName, setTaskName] = useState("Jamnagar Refinery Sector 4");
  const [taskLat, setTaskLat] = useState("22.3552");
  const [taskLon, setTaskLon] = useState("69.8654");
  const [taskSensor, setTaskSensor] = useState("THERMAL_MWIR");
  const [taskPriority, setTaskPriority] = useState("HIGH");
  const [taskFeedback, setTaskFeedback] = useState<any | null>(null);
  const [missionTasksList, setMissionTasksList] = useState<any[]>([]);

  // Historical Replay Form
  const [historicalHubs, setHistoricalHubs] = useState<any[]>([
    { name: "Jamnagar Refinery Flare Anomaly (Gujarat)", date: "2026-08-01", time: "1830", lat: 22.3552, lon: 69.8654, frp: 128.0, sensor: "VIIRS_NOAA21", type: "HISTORICAL_ARCHIVE" },
    { name: "Singrauli Super Thermal Surge (Madhya Pradesh)", date: "2026-07-15", time: "0215", lat: 24.1012, lon: 82.6841, frp: 195.0, sensor: "VIIRS_NOAA20", type: "HISTORICAL_ARCHIVE" },
    { name: "Korba Opencast Coal Seam (Chhattisgarh)", date: "2026-06-20", time: "1340", lat: 22.3485, lon: 82.7231, frp: 110.0, sensor: "MODIS_AQUA", type: "HISTORICAL_ARCHIVE" },
    { name: "Angul Smelter Furnace Emission (Odisha)", date: "2026-05-10", time: "2210", lat: 20.8521, lon: 85.1245, frp: 142.0, sensor: "VIIRS_NOAA21", type: "HISTORICAL_ARCHIVE" },
    { name: "Hazira Petrochemical Cluster (Gujarat)", date: "2026-04-18", time: "0150", lat: 21.1160, lon: 72.6510, frp: 165.0, sensor: "VIIRS_NOAA20", type: "HISTORICAL_ARCHIVE" }
  ]);
  const [selectedHistoricalIdx, setSelectedHistoricalIdx] = useState(0);
  const [replayResult, setReplayResult] = useState<any | null>(null);

  // MapLibre Reference
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<maplibregl.Map | null>(null);
  const markersRef = useRef<maplibregl.Marker[]>([]);

  // 1. Fetch System Data
  useEffect(() => {
    async function loadMissionData() {
      try {
        const sat = await fetchApi<SatelliteInfo>("/satellite/info");
        setSatelliteInfo(sat);
        const scList = await fetchApi<Scenario[]>("/satellite/scenarios");
        setScenarios(scList);
        const logs = await fetchApi<any[]>("/satellite/telemetry/logs?limit=10");
        setTelemetryLogs(logs);
        const tasks = await fetchApi<any[]>("/satellite/tasks?limit=10");
        setMissionTasksList(tasks);
      } catch (err) {
        console.error("Failed to load satellite mission data:", err);
      }
    }
    loadMissionData();
  }, []);

  // 2. Initialize Interactive Map
  useEffect(() => {
    if (!mapContainer.current || map.current) return;

    const m = new maplibregl.Map({
      container: mapContainer.current,
      style: "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
      center: [78.9629, 21.5937],
      zoom: 4.5,
      attributionControl: false,
    });

    m.addControl(new maplibregl.NavigationControl({ showCompass: true }), "top-left");
    m.addControl(new maplibregl.ScaleControl({ unit: "metric" }), "bottom-left");

    m.on("load", async () => {
      try {
        // Load orbital ground track
        const trackData = await fetchApi<any>("/satellite/ground-track?hours_ahead=3.0");
        if (m.getSource("ground-track")) return;

        m.addSource("ground-track", {
          type: "geojson",
          data: trackData
        });

        m.addLayer({
          id: "ground-track-line",
          type: "line",
          source: "ground-track",
          layout: {
            "line-join": "round",
            "line-cap": "round"
          },
          paint: {
            "line-color": "#38bdf8",
            "line-width": 2,
            "line-dasharray": [2, 1],
            "line-opacity": 0.85
          }
        });
      } catch (e) {
        console.error("Error adding ground track source:", e);
      }
    });

    map.current = m;

    return () => {
      m.remove();
      map.current = null;
    };
  }, []);

  // 3. Update Map Markers & Swath Polygon when scenario changes or executes
  const updateMapForScenario = (sc: Scenario) => {
    if (!map.current) return;

    // Fly to target
    map.current.flyTo({
      center: [sc.target_lon, sc.target_lat],
      zoom: 8.5,
      duration: 1800,
      essential: true
    });

    // Clear previous markers
    markersRef.current.forEach(m => m.remove());
    markersRef.current = [];

    // Add Hotspot Pulse Marker
    const el = document.createElement("div");
    el.className = "relative flex items-center justify-center";
    el.innerHTML = `
      <div class="absolute w-8 h-8 rounded-full bg-red-500/40 animate-ping"></div>
      <div class="relative w-4 h-4 rounded-full bg-red-500 border-2 border-white shadow-lg flex items-center justify-center">
        <div class="w-1.5 h-1.5 rounded-full bg-white"></div>
      </div>
    `;

    const marker = new maplibregl.Marker({ element: el })
      .setLngLat([sc.target_lon, sc.target_lat])
      .addTo(map.current);

    markersRef.current.push(marker);

    // Update Swath Footprint Polygon Layer
    fetchApi<any>(`/satellite/footprint?latitude=${sc.target_lat}&longitude=${sc.target_lon}&sensor_id=THERMAL_MWIR`)
      .then(footprintGeojson => {
        if (!map.current) return;
        if (map.current.getSource("sensor-swath")) {
          (map.current.getSource("sensor-swath") as maplibregl.GeoJSONSource).setData(footprintGeojson);
        } else if (map.current.isStyleLoaded()) {
          map.current.addSource("sensor-swath", {
            type: "geojson",
            data: footprintGeojson
          });
          map.current.addLayer({
            id: "sensor-swath-fill",
            type: "fill",
            source: "sensor-swath",
            paint: {
              "fill-color": "#38bdf8",
              "fill-opacity": 0.12
            }
          });
          map.current.addLayer({
            id: "sensor-swath-stroke",
            type: "line",
            source: "sensor-swath",
            paint: {
              "line-color": "#38bdf8",
              "line-width": 1.5,
              "line-dasharray": [3, 2]
            }
          });
        }
      })
      .catch(console.error);
  };

  // Trigger Scenario Execution
  const handleExecuteScenario = async () => {
    const sc = scenarios.find(s => s.id === selectedScenarioId);
    if (!sc) return;

    setIsExecuting(true);
    setExecutionStep(0);
    setExecutionResult(null);
    updateMapForScenario(sc);

    // Stepper Animation across 21 stages
    const stepInterval = setInterval(() => {
      setExecutionStep(prev => {
        if (prev < 20) return prev + 1;
        clearInterval(stepInterval);
        return 20;
      });
    }, 140);

    try {
      const res = await fetchApi<ScenarioExecutionResult>(`/satellite/scenarios/${sc.id}/run`, {
        method: "POST"
      });
      clearInterval(stepInterval);
      setExecutionStep(21);
      setExecutionResult(res);

      // Refresh telemetry logs & tasks
      const logs = await fetchApi<any[]>("/satellite/telemetry/logs?limit=10");
      setTelemetryLogs(logs);
    } catch (err: any) {
      clearInterval(stepInterval);
      alert(`Simulation execution failed: ${err.message}`);
    } finally {
      setIsExecuting(false);
    }
  };

  // Schedule Mission Task
  const handleScheduleTask = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await fetchApi<any>("/satellite/tasking", {
        method: "POST",
        body: JSON.stringify({
          satellite_id: "AGNI-SAT-01",
          target_name: taskName,
          target_lat: parseFloat(taskLat),
          target_lon: parseFloat(taskLon),
          sensor_id: taskSensor,
          priority: taskPriority
        })
      });
      setTaskFeedback(res);
      const tasks = await fetchApi<any[]>("/satellite/tasks?limit=10");
      setMissionTasksList(tasks);
    } catch (err: any) {
      alert(`Task scheduling failed: ${err.message}`);
    }
  };

  // Replay Historical Observation
  const handleReplayHistorical = async () => {
    const hub = historicalHubs[selectedHistoricalIdx];
    try {
      const res = await fetchApi<any>("/satellite/replay", {
        method: "POST",
        body: JSON.stringify({
          source: "NASA_FIRMS",
          sensor: hub.sensor,
          satellite: hub.sensor.includes("21") ? "NOAA-21" : "NOAA-20",
          latitude: hub.lat,
          longitude: hub.lon,
          acq_date: hub.date,
          acq_time: hub.time,
          acq_timestamp: `${hub.date}T${hub.time.slice(0, 2)}:${hub.time.slice(2)}:00+00:00`,
          brightness: 350.0,
          bright_t31: 320.0,
          frp: hub.frp,
          confidence: 95.0,
          day_night: "N"
        })
      });
      setReplayResult(res);
    } catch (err: any) {
      alert(`Historical replay failed: ${err.message}`);
    }
  };

  const selectedScenario = scenarios.find(s => s.id === selectedScenarioId) || scenarios[0];

  return (
    <div className="space-y-4">
      {/* Top Header Mission Telemetry & Mode Switcher */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 bg-agni-card p-4 rounded-xl border border-agni-border/80 shadow-md">
        <div>
          <div className="flex items-center gap-3">
            <span className="p-2 rounded-lg bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
              <Radio className="w-5 h-5 animate-pulse" />
            </span>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-lg font-bold text-white tracking-wide">
                  AGNI-SAT-01 • Digital Twin Mission Control
                </h1>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-purple-500/20 text-purple-300 border border-purple-500/30 uppercase">
                  SIMULATION ENGINE
                </span>
              </div>
              <p className="text-xs text-slate-400">
                End-to-End Synthetic Telemetry Generation, Orbit Swath Prediction & Deterministic Pipeline Testing
              </p>
            </div>
          </div>
        </div>

        {/* Orbit State Indicators */}
        <div className="flex flex-wrap items-center gap-2 text-xs font-mono">
          <div className="bg-slate-900/80 px-3 py-1.5 rounded-lg border border-slate-800 flex items-center gap-2">
            <span className="text-slate-400">ALT:</span>
            <strong className="text-cyan-400">{satelliteInfo?.altitude_km || 505} km</strong>
          </div>
          <div className="bg-slate-900/80 px-3 py-1.5 rounded-lg border border-slate-800 flex items-center gap-2">
            <span className="text-slate-400">INC:</span>
            <strong className="text-cyan-400">{satelliteInfo?.inclination_deg || 97.4}°</strong>
          </div>
          <div className="bg-slate-900/80 px-3 py-1.5 rounded-lg border border-slate-800 flex items-center gap-2">
            <span className="text-slate-400">SPEED:</span>
            <strong className="text-emerald-400">{satelliteInfo?.ground_speed_km_s || 7.6} km/s</strong>
          </div>
          <div className="bg-slate-900/80 px-3 py-1.5 rounded-lg border border-slate-800 flex items-center gap-2">
            <span className="text-slate-400">SWATH:</span>
            <strong className="text-amber-400">{satelliteInfo?.swath_width_km || 350} km</strong>
          </div>
        </div>
      </div>

      {/* Main 3-Column Layout: Left Controls | Center Tactical Map | Right AI Intelligence */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        
        {/* LEFT COLUMN: Scenarios, Tasking & Replay Tabs (4 cols) */}
        <div className="lg:col-span-4 space-y-4">
          <div className="bg-agni-card rounded-xl border border-agni-border overflow-hidden">
            {/* Tabs Header */}
            <div className="flex border-b border-agni-border text-xs font-medium bg-slate-900/50">
              <button
                onClick={() => setActiveTab("SCENARIOS")}
                className={`flex-1 py-3 text-center border-b-2 transition-all flex items-center justify-center gap-1.5 ${
                  activeTab === "SCENARIOS"
                    ? "border-cyan-500 text-cyan-400 bg-cyan-500/5"
                    : "border-transparent text-slate-400 hover:text-slate-200"
                }`}
              >
                <Zap className="w-3.5 h-3.5" />
                <span>12 Scenarios</span>
              </button>
              <button
                onClick={() => setActiveTab("TASKING")}
                className={`flex-1 py-3 text-center border-b-2 transition-all flex items-center justify-center gap-1.5 ${
                  activeTab === "TASKING"
                    ? "border-purple-500 text-purple-400 bg-purple-500/5"
                    : "border-transparent text-slate-400 hover:text-slate-200"
                }`}
              >
                <Crosshair className="w-3.5 h-3.5" />
                <span>Virtual Tasking</span>
              </button>
              <button
                onClick={() => setActiveTab("REPLAY")}
                className={`flex-1 py-3 text-center border-b-2 transition-all flex items-center justify-center gap-1.5 ${
                  activeTab === "REPLAY"
                    ? "border-amber-500 text-amber-400 bg-amber-500/5"
                    : "border-transparent text-slate-400 hover:text-slate-200"
                }`}
              >
                <History className="w-3.5 h-3.5" />
                <span>Archive Replay</span>
              </button>
            </div>

            {/* TAB CONTENT: 12 SCENARIOS */}
            {activeTab === "SCENARIOS" && (
              <div className="p-4 space-y-3 max-h-[580px] overflow-y-auto">
                <div className="space-y-2">
                  <label className="text-[11px] font-semibold text-slate-300 uppercase tracking-wider font-mono">
                    Select Standard Incident Template
                  </label>
                  <div className="space-y-2">
                    {scenarios.map((sc) => {
                      const isSelected = sc.id === selectedScenarioId;
                      return (
                        <div
                          key={sc.id}
                          onClick={() => {
                            setSelectedScenarioId(sc.id);
                            updateMapForScenario(sc);
                          }}
                          className={`p-3 rounded-lg border cursor-pointer transition-all ${
                            isSelected
                              ? "bg-cyan-500/10 border-cyan-500/50 shadow-sm"
                              : "bg-slate-900/50 border-slate-800 hover:border-slate-700 text-slate-300"
                          }`}
                        >
                          <div className="flex items-center justify-between gap-2">
                            <span className="text-xs font-bold text-white leading-tight">
                              {sc.name}
                            </span>
                            <span className={`text-[9px] font-mono font-bold px-1.5 py-0.5 rounded uppercase ${
                              sc.expected_risk_level === "CRITICAL"
                                ? "bg-red-500/20 text-red-300 border border-red-500/30"
                                : sc.expected_risk_level === "HIGH"
                                ? "bg-amber-500/20 text-amber-300 border border-amber-500/30"
                                : "bg-blue-500/20 text-blue-300 border border-blue-500/30"
                            }`}>
                              {sc.expected_risk_level}
                            </span>
                          </div>
                          <p className="text-[11px] text-slate-400 mt-1 line-clamp-2 leading-relaxed">
                            {sc.description}
                          </p>
                          <div className="mt-2 pt-2 border-t border-slate-800/80 flex items-center justify-between text-[10px] font-mono text-slate-400">
                            <span>Target: <strong className="text-slate-300">{sc.target_state}</strong></span>
                            <span>FRP: <strong className="text-amber-400">{sc.parameters.frp_mw} MW</strong></span>
                            <span>Z-Score: <strong className="text-cyan-400">+{sc.parameters.anomaly_z_score}σ</strong></span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Execute Button */}
                <div className="pt-2">
                  <button
                    disabled={isExecuting}
                    onClick={handleExecuteScenario}
                    className="w-full py-3 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-bold text-xs rounded-lg shadow-lg flex items-center justify-center gap-2 transition-all disabled:opacity-50"
                  >
                    {isExecuting ? (
                      <>
                        <RefreshCw className="w-4 h-4 animate-spin" />
                        <span>Simulating Sequence ({executionStep}/21)...</span>
                      </>
                    ) : (
                      <>
                        <Play className="w-4 h-4 fill-current" />
                        <span>Execute AGNI-SAT Simulation</span>
                      </>
                    )}
                  </button>
                </div>
              </div>
            )}

            {/* TAB CONTENT: VIRTUAL TASKING */}
            {activeTab === "TASKING" && (
              <div className="p-4 space-y-4">
                <form onSubmit={handleScheduleTask} className="space-y-3">
                  <div>
                    <label className="text-[10px] font-mono uppercase text-slate-400 block mb-1">Target Area of Interest (AOI)</label>
                    <input
                      type="text"
                      value={taskName}
                      onChange={e => setTaskName(e.target.value)}
                      className="w-full bg-slate-900 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-white"
                      required
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="text-[10px] font-mono uppercase text-slate-400 block mb-1">Latitude</label>
                      <input
                        type="number"
                        step="0.0001"
                        value={taskLat}
                        onChange={e => setTaskLat(e.target.value)}
                        className="w-full bg-slate-900 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-white"
                        required
                      />
                    </div>
                    <div>
                      <label className="text-[10px] font-mono uppercase text-slate-400 block mb-1">Longitude</label>
                      <input
                        type="number"
                        step="0.0001"
                        value={taskLon}
                        onChange={e => setTaskLon(e.target.value)}
                        className="w-full bg-slate-900 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-white"
                        required
                      />
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="text-[10px] font-mono uppercase text-slate-400 block mb-1">Sensor Payload</label>
                      <select
                        value={taskSensor}
                        onChange={e => setTaskSensor(e.target.value)}
                        className="w-full bg-slate-900 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-white"
                      >
                        <option value="THERMAL_MWIR">MWIR 3.9µm (350km)</option>
                        <option value="OPTICAL_RGB">RGB TrueColor (60km)</option>
                        <option value="SWIR_2200NM">SWIR 2.2µm (120km)</option>
                        <option value="MULTISPECTRAL">Multispectral (150km)</option>
                      </select>
                    </div>
                    <div>
                      <label className="text-[10px] font-mono uppercase text-slate-400 block mb-1">Priority</label>
                      <select
                        value={taskPriority}
                        onChange={e => setTaskPriority(e.target.value)}
                        className="w-full bg-slate-900 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-white"
                      >
                        <option value="NORMAL">Normal</option>
                        <option value="HIGH">High Priority</option>
                        <option value="CRITICAL">Emergency / Critical</option>
                      </select>
                    </div>
                  </div>

                  <button
                    type="submit"
                    className="w-full py-2.5 bg-purple-600 hover:bg-purple-500 text-white font-bold text-xs rounded shadow flex items-center justify-center gap-1.5 transition-all"
                  >
                    <Crosshair className="w-4 h-4" />
                    <span>Calculate Next Pass & Schedule</span>
                  </button>
                </form>

                {taskFeedback && (
                  <div className="p-3 bg-purple-500/10 border border-purple-500/30 rounded-lg text-xs space-y-1">
                    <div className="text-purple-300 font-bold">{taskFeedback.status}</div>
                    <div className="text-slate-300 text-[11px]">Task Code: <span className="font-mono text-white">{taskFeedback.task_code}</span></div>
                    <div className="text-slate-400 text-[10px]">Next Orbit Opportunity in <strong className="text-cyan-400">{taskFeedback.pass_delay_minutes} min</strong> ({new Date(taskFeedback.scheduled_pass_time).toLocaleTimeString()})</div>
                  </div>
                )}

                {/* Task History Table */}
                <div className="space-y-1.5">
                  <div className="text-[10px] font-mono uppercase text-slate-500 font-bold">Scheduled Mission Tasks</div>
                  <div className="max-h-36 overflow-y-auto space-y-1">
                    {missionTasksList.map((t, idx) => (
                      <div key={idx} className="p-2 bg-slate-900/60 border border-slate-800 rounded text-[10px] flex items-center justify-between">
                        <div>
                          <div className="font-bold text-slate-200">{t.target_name}</div>
                          <div className="text-slate-500 font-mono">{t.sensor_id} • {t.priority}</div>
                        </div>
                        <span className="px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono text-[9px]">
                          {t.status}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* TAB CONTENT: HISTORICAL REPLAY */}
            {activeTab === "REPLAY" && (
              <div className="p-4 space-y-3">
                <p className="text-xs text-slate-400 leading-relaxed">
                  Replays a real historical observation through AGNI-SAT virtual telemetry down into live processing, preserving original acquisition timestamps.
                </p>
                <div className="space-y-2">
                  {historicalHubs.map((hub, idx) => (
                    <div
                      key={idx}
                      onClick={() => setSelectedHistoricalIdx(idx)}
                      className={`p-2.5 rounded border cursor-pointer transition-all ${
                        selectedHistoricalIdx === idx
                          ? "bg-amber-500/10 border-amber-500/50"
                          : "bg-slate-900/50 border-slate-800 text-slate-300"
                      }`}
                    >
                      <div className="text-xs font-bold text-white">{hub.name}</div>
                      <div className="mt-1 flex items-center justify-between text-[10px] font-mono text-slate-400">
                        <span>Date: <strong className="text-slate-300">{hub.date} {hub.time}Z</strong></span>
                        <span>FRP: <strong className="text-amber-400">{hub.frp} MW</strong></span>
                        <span>{hub.sensor}</span>
                      </div>
                    </div>
                  ))}
                </div>

                <button
                  onClick={handleReplayHistorical}
                  className="w-full py-2.5 bg-amber-600 hover:bg-amber-500 text-white font-bold text-xs rounded shadow flex items-center justify-center gap-1.5 transition-all"
                >
                  <History className="w-4 h-4" />
                  <span>Execute Replay (Preserve Timestamps)</span>
                </button>

                {replayResult && (
                  <div className="p-3 bg-amber-500/10 border border-amber-500/30 rounded-lg text-xs space-y-1">
                    <div className="text-amber-300 font-bold">Historical Replay Processed</div>
                    <div className="text-[11px] text-slate-300">Original Acq Time: <span className="font-mono text-cyan-400">{replayResult.original_acquisition_timestamp}</span></div>
                    <div className="text-[10px] text-slate-400">Replay Executed At: <span className="font-mono text-slate-300">{replayResult.replay_execution_timestamp}</span></div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* CENTER COLUMN: Tactical GIS Ground Track Map (5 cols) */}
        <div className="lg:col-span-5 space-y-4">
          <div className="bg-agni-card rounded-xl border border-agni-border overflow-hidden h-[630px] flex flex-col relative shadow-lg">
            {/* Map Status Bar */}
            <div className="px-4 py-2 bg-slate-900/90 border-b border-slate-800 flex items-center justify-between text-xs z-10">
              <div className="flex items-center gap-2">
                <Crosshair className="w-3.5 h-3.5 text-cyan-400" />
                <span className="font-mono text-slate-200">Orbit Footprint & Thermal AOI Viewer</span>
              </div>
              <div className="flex items-center gap-2 text-[10px] font-mono text-slate-400">
                <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping"></span>
                <span>Swath Swp: 350 km</span>
              </div>
            </div>

            {/* Map Container */}
            <div ref={mapContainer} className="flex-1 w-full h-full" />

            {/* Floating Map Legend */}
            <div className="absolute bottom-3 left-3 bg-slate-900/90 backdrop-blur border border-slate-800 p-2.5 rounded-lg text-[10px] space-y-1.5 z-10 font-mono">
              <div className="flex items-center gap-2">
                <div className="w-4 h-0.5 border-b border-dashed border-cyan-400"></div>
                <span className="text-slate-300">Sun-Sync LEO Ground Track</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded bg-cyan-500/20 border border-cyan-400/50"></div>
                <span className="text-slate-300">Active Sensor Swath Width</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-2.5 h-2.5 rounded-full bg-red-500"></div>
                <span className="text-slate-300">Target Thermal Radiative Hotspot</span>
              </div>
            </div>
          </div>
        </div>

        {/* RIGHT COLUMN: Real-Time Incident Intelligence & Decision Support (3 cols) */}
        <div className="lg:col-span-3 space-y-4">
          <div className="bg-agni-card rounded-xl border border-agni-border p-4 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2">
              <div className="flex items-center gap-2">
                <Cpu className="w-4 h-4 text-cyan-400" />
                <h3 className="text-xs font-bold text-white uppercase tracking-wider font-mono">
                  Incident Intelligence
                </h3>
              </div>
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-300">
                AI + SHAP
              </span>
            </div>

            {executionResult ? (
              <div className="space-y-4">
                {/* AI Classification */}
                <div className="p-3 bg-slate-900/80 rounded-lg border border-slate-800 space-y-2">
                  <div className="text-[10px] font-mono uppercase text-slate-400">7-Class Primary Classifier</div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-bold text-white">
                      {executionResult.event?.predicted_class || "Analyzing..."}
                    </span>
                    <span className="text-xs font-mono font-bold text-emerald-400">
                      {Math.round((executionResult.event?.confidence || 0) * 100)}% Conf
                    </span>
                  </div>

                  {/* Expected vs Predicted Benchmark Comparison */}
                  <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-[10px] font-mono">
                    <span className="text-slate-400">Expected: {executionResult.validation.expected_class}</span>
                    <span className={`px-1.5 py-0.5 rounded font-bold ${
                      executionResult.validation.is_match
                        ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                        : "bg-red-500/20 text-red-300 border border-red-500/30"
                    }`}>
                      {executionResult.validation.is_match ? "BENCHMARK MATCH" : "MISMATCH"}
                    </span>
                  </div>
                </div>

                {/* Risk Level & Score */}
                <div className="p-3 bg-slate-900/80 rounded-lg border border-slate-800 space-y-2">
                  <div className="flex items-center justify-between text-[10px] font-mono text-slate-400">
                    <span>AGNI-NETRA Risk Level</span>
                    <span>Score: <strong className="text-white">{executionResult.event?.risk_score || 0} / 100</strong></span>
                  </div>
                  <div className={`p-2 rounded font-bold text-center text-xs tracking-wider uppercase border ${
                    executionResult.event?.risk_level === "CRITICAL"
                      ? "bg-red-500/20 text-red-300 border-red-500/40"
                      : executionResult.event?.risk_level === "HIGH"
                      ? "bg-amber-500/20 text-amber-300 border-amber-500/40"
                      : "bg-blue-500/20 text-blue-300 border-blue-500/40"
                  }`}>
                    {executionResult.event?.risk_level || "MODERATE"} RISK
                  </div>
                </div>

                {/* Explainable SHAP Attribution Summary */}
                <div className="p-3 bg-slate-900/80 rounded-lg border border-slate-800 space-y-1.5">
                  <div className="text-[10px] font-mono uppercase text-slate-400 flex items-center justify-between">
                    <span>SHAP TreeExplainer</span>
                    <span className="text-cyan-400">Feature Weights</span>
                  </div>
                  <p className="text-[11px] text-slate-300 leading-relaxed font-sans">
                    {executionResult.event?.shap_summary || "Feature vector attributions calculated across 18 thermal and spatial dimensions."}
                  </p>
                </div>
              </div>
            ) : (
              <div className="py-12 text-center text-slate-500 space-y-2">
                <Info className="w-8 h-8 mx-auto text-slate-600" />
                <p className="text-xs">No active scenario executed.</p>
                <p className="text-[10px]">Select a scenario and click &ldquo;Execute AGNI-SAT Simulation&rdquo;.</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* BOTTOM SECTION: 21-Step Pipeline Tracker & Measured Stage Latency Benchmark */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* 21-Step Stepper (7 cols) */}
        <div className="lg:col-span-7 bg-agni-card p-4 rounded-xl border border-agni-border space-y-3">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-cyan-400" />
              <h3 className="text-xs font-bold text-white uppercase tracking-wider font-mono">
                10-Stage Lineage & Execution Timeline (21 Milestones)
              </h3>
            </div>
            <span className="text-[10px] font-mono text-slate-400">
              Stage {executionStep} of 21
            </span>
          </div>

          {/* Stepper Grid */}
          <div className="grid grid-cols-3 sm:grid-cols-7 gap-1.5 text-[9px] font-mono">
            {PIPELINE_21_STEPS.map((step, idx) => {
              const isPassed = executionStep > idx;
              const isCurrent = executionStep === idx && isExecuting;

              return (
                <div
                  key={idx}
                  className={`p-1.5 rounded border flex flex-col justify-between h-14 transition-all ${
                    isCurrent
                      ? "bg-cyan-500/20 border-cyan-400 text-cyan-300 animate-pulse font-bold"
                      : isPassed
                      ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400"
                      : "bg-slate-900/40 border-slate-800 text-slate-600"
                  }`}
                >
                  <span className="truncate">{step}</span>
                  <div className="flex justify-end">
                    {isPassed ? (
                      <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                    ) : isCurrent ? (
                      <RefreshCw className="w-3 h-3 text-cyan-400 animate-spin" />
                    ) : (
                      <span className="text-[8px] text-slate-700">#{idx + 1}</span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Real Measured Latency Benchmark (5 cols) */}
        <div className="lg:col-span-5 bg-agni-card p-4 rounded-xl border border-agni-border space-y-3">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <div className="flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-emerald-400" />
              <h3 className="text-xs font-bold text-white uppercase tracking-wider font-mono">
                Actual Measured Stage Latency Benchmark
              </h3>
            </div>
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-300 border border-emerald-500/20">
              time.perf_counter()
            </span>
          </div>

          {executionResult?.benchmark ? (
            <div className="space-y-2 text-xs font-mono">
              <div className="grid grid-cols-2 gap-2 text-[11px]">
                <div className="p-2 bg-slate-900/80 rounded border border-slate-800">
                  <div className="text-slate-400 text-[10px]">Telemetry Packet Formatted</div>
                  <div className="text-cyan-400 font-bold">{executionResult.benchmark.observation_to_telemetry_ms} ms</div>
                </div>
                <div className="p-2 bg-slate-900/80 rounded border border-slate-800">
                  <div className="text-slate-400 text-[10px]">DBSCAN Spatiotemporal Cluster</div>
                  <div className="text-cyan-400 font-bold">{executionResult.benchmark.clustering_ms} ms</div>
                </div>
                <div className="p-2 bg-slate-900/80 rounded border border-slate-800">
                  <div className="text-slate-400 text-[10px]">GIS & LULC Point-in-Poly</div>
                  <div className="text-cyan-400 font-bold">{executionResult.benchmark.gis_enrichment_ms} ms</div>
                </div>
                <div className="p-2 bg-slate-900/80 rounded border border-slate-800">
                  <div className="text-slate-400 text-[10px]">XGBoost Inference (18-D)</div>
                  <div className="text-cyan-400 font-bold">{executionResult.benchmark.ml_inference_ms} ms</div>
                </div>
                <div className="p-2 bg-slate-900/80 rounded border border-slate-800">
                  <div className="text-slate-400 text-[10px]">SHAP TreeExplainer Tree Attrib</div>
                  <div className="text-purple-400 font-bold">{executionResult.benchmark.shap_explanation_ms} ms</div>
                </div>
                <div className="p-2 bg-slate-900/80 rounded border border-slate-800">
                  <div className="text-slate-400 text-[10px]">Risk Matrix & Anomaly Baseline</div>
                  <div className="text-amber-400 font-bold">{executionResult.benchmark.risk_evaluation_ms} ms</div>
                </div>
              </div>

              <div className="p-2.5 bg-gradient-to-r from-emerald-950/40 to-slate-900 rounded border border-emerald-500/30 flex items-center justify-between">
                <div>
                  <div className="text-[10px] text-slate-400">Total End-to-End Pipeline Latency</div>
                  <div className="text-sm font-bold text-emerald-400 font-mono">
                    {executionResult.benchmark.total_processing_ms} ms
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-[10px] text-slate-400">Real-Time Throughput</div>
                  <div className="text-sm font-bold text-white font-mono">
                    {executionResult.benchmark.target_fps_or_hz} Hz
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="py-8 text-center text-slate-500 text-xs">
              Execute a scenario to measure actual stage durations and throughput.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
