# AGNI-NETRA — AGNI-SAT Software Satellite Digital Twin Specification

## 1. Digital Twin Overview

**AGNI-SAT** is a high-fidelity **Software Satellite / Digital Twin** subsystem embedded directly within AGNI-NETRA.

> **CRITICAL ARCHITECTURAL DISTINCTION**:
> AGNI-SAT is a software mission simulation environment, not a physical hardware satellite. It generates normalized synthetic and replayed satellite observations that pass through the **EXACT SAME** ingestion interface (`NormalizedThermalObservation`) and 10-stage processing pipeline (`pipeline_service`) as real-world satellite constellations.

---

## 2. Spacecraft Parameters (AGNI-SAT-01)

| Parameter | Specification | Purpose |
|---|---|---|
| **Satellite ID** | `AGNI-SAT-01` | Virtual satellite identification |
| **Orbit Type** | Sun-Synchronous Low Earth Orbit (SSO LEO) | Deterministic global overpass cycle |
| **Altitude** | $505\text{ km}$ | Geometric resolution scaling |
| **Inclination** | $97.4^\circ$ | Near-polar orbital coverage |
| **Orbital Period** | $94.6\text{ minutes}$ | Revisit and overpass opportunity propagation |
| **Ground Track Speed** | $7.6\text{ km/s}$ | Footprint scanning velocity |
| **Sensor Swath Width** | $350\text{ km}$ (MWIR) / $60\text{ km}$ (Optical) / $120\text{ km}$ (SWIR) | Dynamic polygon ground footprint geometry |

---

## 3. Sensor Payload Digital Twin

1. **`THERMAL_MWIR`**: Mid-Wave Infrared (3.9 µm), 375m spatial resolution, 350 km swath width. Primary active thermal detection channel.
2. **`OPTICAL_RGB`**: TrueColor RGB (0.4 - 0.7 µm), 10m spatial resolution, 60 km swath width. High-resolution facility verification.
3. **`SWIR_2200NM`**: Short-Wave Infrared (2.2 µm), 20m spatial resolution, 120 km swath width. High-temperature gas flare and smelter signature.
4. **`MULTISPECTRAL`**: 8-band multispectral payload, 15m spatial resolution, 150 km swath width. LULC context and vegetation stress index.

---

## 4. Standard Incident Simulation Catalog (12 Templates)

1. `scenario-01-industrial-surge`: Jamnagar Refinery flare surge (+3.5σ FRP surge)
2. `scenario-02-gas-flare`: Kakinada KG-Basin continuous industrial gas flaring
3. `scenario-03-forest-fire`: Simlipal Biosphere Reserve forest wildfire
4. `scenario-04-agricultural-burning`: Sangrur paddy stubble burning in agrarian zone
5. `scenario-05-mining-activity`: Korba Gevra opencast coal seam fire
6. `scenario-06-unknown-persistent`: Raigarh persistent thermal anomaly lacking known facility
7. `scenario-07-multi-event`: Hazira multi-facility industrial incident
8. `scenario-08-missing-facility`: Angul smelter candidate emergence and discovery
9. `scenario-09-delayed-telemetry`: Jaisalmer telemetry downlink latency recovery
10. `scenario-10-sensor-dropout`: Singrauli optical dropout with MWIR fail-safe
11. `scenario-11-cloud-obscured`: Western Ghats optical cloud penetration
12. `scenario-12-high-thermal-anomaly`: Nagothane extreme petrochemical thermal surge
