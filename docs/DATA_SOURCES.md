# AGNI-NETRA — Data Source Adapters & Integration

## 1. Supported Data Providers

1. **NASA FIRMS (Fire Information for Resource Management System)**
   - *Sensors*: VIIRS 375m (NOAA-20, Suomi-NPP) & MODIS 1km (Aqua, Terra)
   - *Products*: Active Fire / Thermal Anomaly NRT CSV & GeoJSON
   - *Adapter*: `FIRMSAdapter`

2. **OpenStreetMap (OSM)**
   - *Attributes*: Industrial polygons, power plants, refineries, metallurgy, mining cadastre
   - *Protocol*: Overpass API QL / PBF ingestion
   - *Adapter*: `OSMIndustrialAdapter`

3. **Land Use / Land Cover (LULC)**
   - *Sources*: ISRO Bhuvan 1:50,000 / ESA WorldCover 10m
   - *Categories*: Industrial, Mining, Urban, Agriculture, Forest, Barren, Water
   - *Adapter*: `LULCAdapter`

4. **Copernicus Sentinel-2**
   - *Bands*: B11, B12 (Shortwave Infrared / SWIR) & B8 (Near Infrared) for industrial flare validation
   - *Adapter*: `SentinelAdapter`

5. **USGS / NASA Landsat 8/9**
   - *Bands*: Band 10/11 Thermal Infrared Sensor (TIRS) for long-term historical baseline verification
   - *Adapter*: `LandsatAdapter`

---

## 2. Sensor-Agnostic Normalization

All external feeds map to a unified domain structure:
```python
class NormalizedThermalObservation(BaseModel):
    source_record_id: Optional[str]
    source: str          # FIRMS, SENTINEL, LANDSAT, OSM, DEMO
    sensor: str          # VIIRS_NOAA20, VIIRS_SNPP, MODIS_AQUA, MSI_S2, TIRS_L8
    latitude: float
    longitude: float
    acq_timestamp: datetime
    brightness: Optional[float]
    bright_t31: Optional[float]
    frp: float           # Fire Radiative Power (MW)
    confidence: float    # 0 - 100%
    day_night: str       # 'D' or 'N'
    metadata: Dict[str, Any]
```
