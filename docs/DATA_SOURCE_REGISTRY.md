# AGNI-NETRA — Data Source Registry

## Canonical Registry Overview

AGNI-NETRA integrates real-world satellite constellations, cadastral infrastructure registers, land-cover cartography, and digital twin simulation engines.

| Source ID | Provider / Constellation | Category | Primary Products / Bands | Ingestion Interface | Provenance Level |
|---|---|---|---|---|---|
| **`NASA_FIRMS`** | NASA / NOAA / LANCE | Satellite Active Fire | VIIRS 375m (NOAA-21, NOAA-20, SNPP), MODIS 1km (Terra/Aqua) | REST API / CSV / GeoJSON | REAL (NRT & Science Quality) |
| **`OSM_OVERPASS`** | OpenStreetMap Foundation | Cadastral & Infrastructure | Industrial polygons, power plants, refineries, smelters | Overpass QL REST API | REAL (Crowdsourced Verified) |
| **`CEA_REGISTRY`** | Central Electricity Authority | Indian Energy Infrastructure | Thermal power plants, capacity, coordinates, ownership | Canonical Cadastral Ingestion | REAL (Official Government) |
| **`ISRO_BHUVAN`** | ISRO / NRSC | Land Use / Land Cover (LULC) | 24m 1:50,000 Scale 8-class thematic classification | OGC WMS/WFS / Vector Point-in-Poly | REAL (National Cartography) |
| **`COPERNICUS_SENTINEL`** | European Space Agency (ESA) | Optical & SWIR Imagery | Sentinel-2 MSI RGB (10m), SWIR B11/B12 (20m) | STAC API (Element84 / Planetary Computer) | REAL (Event-Driven STAC) |
| **`USGS_LANDSAT`** | USGS / NASA | Thermal Infrared & Multispectral | Landsat 8/9 TIRS Band 10 (100m resampled to 30m) | STAC API / EarthExplorer | REAL (Archive Thermal Context) |
| **`MOSDAC`** | ISRO Meteorological & Oceanographic | Geostationary Thermal | INSAT-3D / 3DR Imager & Sounder | OGC / FTP Data Access | REAL (Conditional / Configurable) |
| **`AGNI_SAT_SIMULATION`** | AGNI-NETRA Digital Twin Engine | Spacecraft Simulation | Synthetic 4-Band Telemetry (`THERMAL_MWIR`, `OPTICAL_RGB`, `SWIR`, `MULTISPECTRAL`) | Internal Service Pipeline | SIMULATION (Digital Twin) |

---

## Ingestion Policies & Data Governance

1. **Bounding Box & India Polygon Clipping**: All remote sensing data retrieved via bounding box queries is strictly clipped against the official Sovereign Territory of India polygon geometry (`database/india_states.geojson`).
2. **Deduplication & Provenance**: Hotspots arriving from multiple sensors within a 2-hour window and 1.5 km distance are merged during spatiotemporal DBSCAN clustering while preserving individual detection record IDs and sensor metadata.
3. **Graceful Fail-Safe**: If external network access is unavailable or API tokens are unconfigured, adapters transition to `OFFLINE_FALLBACK` / `NOT_CONFIGURED` without raising fatal runtime errors or fabricating live fake data.
