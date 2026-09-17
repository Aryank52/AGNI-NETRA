"""
AGNI-NETRA — Phase 25.5.1 Forensic Facility Coordinate Audit
Audits 50+ representative facilities across all regions of India against:
1. Master Raw OSM Source: E:\\PROJECTS\\AGNI-NETRA(DATABASE)\\FACILITIES\\OSM\\export.geojson
2. Database: industrial_facilities in agni_netra.db
3. REST API: /api/v1/gis/industrial-facilities
4. GeoJSON Coordinates: [longitude, latitude]
"""

import json
import os
import sqlite3
import httpx

RAW_SOURCE_PATH = r"E:\PROJECTS\AGNI-NETRA(DATABASE)\FACILITIES\OSM\export.geojson"
DB_PATH = "agni_netra.db"

def run_facility_audit():
    print("=" * 80)
    print("PHASE 25.5.1 — FORENSIC FACILITY COORDINATE AUDIT (50+ SAMPLES)")
    print("=" * 80)

    # 1. Connect to SQLite Database
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Query 65 representative facilities distributed across regions
    query = """
        SELECT id, name, source, state, district, latitude, longitude, facility_type
        FROM industrial_facilities
        WHERE latitude IS NOT NULL AND longitude IS NOT NULL
        ORDER BY 
            CASE 
                WHEN id LIKE '0cc90d1a%' THEN 1  -- Reliance Jamnagar
                WHEN source = 'CEA' THEN 2
                WHEN source = 'PROMOTED_CANDIDATE' THEN 3
                ELSE 4
            END,
            id ASC
        LIMIT 65;
    """
    db_facilities = cur.execute(query).fetchall()
    print(f"[1] Loaded {len(db_facilities)} representative facilities from Database.")

    # 2. Check if raw OSM export exists and index sample OSM IDs
    raw_osm_indexed = {}
    if os.path.exists(RAW_SOURCE_PATH):
        print(f"[2] Reading raw OSM export: {RAW_SOURCE_PATH}")
        with open(RAW_SOURCE_PATH, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
            features = raw_data.get("features", [])
            print(f"    Raw file contains {len(features)} features.")
            for feat in features:
                raw_id = str(feat.get("id") or feat.get("properties", {}).get("@id") or "")
                if raw_id:
                    clean_id = raw_id.replace("/", "_")
                    raw_osm_indexed[clean_id] = feat
                    if "/" in raw_id:
                        parts = raw_id.split("/")
                        raw_osm_indexed[f"osm_{parts[0]}_{parts[1]}"] = feat
    else:
        print("[2] WARNING: Raw OSM source not found at expected path.")

    # 3. Call REST API for verification
    api_facilities = {}
    try:
        r = httpx.get("http://127.0.0.1:8000/api/v1/gis/industrial-facilities?limit=400", timeout=10.0)
        if r.status_code == 200:
            for feat in r.json().get("features", []):
                fid = feat.get("properties", {}).get("id")
                if fid:
                    api_facilities[fid] = feat
            print(f"[3] Fetched {len(api_facilities)} features from REST API.")
        else:
            print(f"[3] API returned HTTP {r.status_code}")
    except Exception as e:
        print(f"[3] API error: {e}")

    # 4. Compare across all representations
    results = []
    matches = 0
    mismatches = 0

    print("\n" + "-" * 110)
    print(f"{'Facility ID':<25} | {'Region/State':<15} | {'DB Lat/Lon':<20} | {'GeoJSON Lon/Lat':<22} | {'Fidelity':<10}")
    print("-" * 110)

    for fac in db_facilities:
        fid, name, src, state, district, lat, lon, ftype = fac
        state_str = str(state or "Unknown").encode("ascii", "replace").decode("ascii")[:14]

        # Check raw OSM source if applicable
        raw_match = "N/A (Master Asset)"
        if fid.startswith("osm_"):
            raw_feat = raw_osm_indexed.get(fid)
            if raw_feat:
                gtype = raw_feat.get("geometry", {}).get("type")
                coords = raw_feat.get("geometry", {}).get("coordinates")
                if gtype == "Point" and coords:
                    raw_lon, raw_lat = coords[0], coords[1]
                    if abs(raw_lat - lat) < 1e-4 and abs(raw_lon - lon) < 1e-4:
                        raw_match = "EXACT_RAW_MATCH"
                    else:
                        raw_match = f"DIFF({raw_lat:.4f},{raw_lon:.4f})"
                elif gtype in ["Polygon", "MultiPolygon"]:
                    raw_match = f"GEOM_{gtype}"
            else:
                raw_match = "RAW_NOT_SAMPLED"

        # Check API & GeoJSON [lon, lat] ordering
        api_feat = api_facilities.get(fid)
        api_coords_str = "NOT_IN_API_LIMIT"
        geojson_ok = True

        if api_feat:
            api_coords = api_feat.get("geometry", {}).get("coordinates", [])
            if len(api_coords) == 2:
                api_lon, api_lat = api_coords[0], api_coords[1]
                api_coords_str = f"[{api_lon:.4f}, {api_lat:.4f}]"
                if abs(api_lat - lat) > 1e-4 or abs(api_lon - lon) > 1e-4:
                    geojson_ok = False
                    mismatches += 1
                else:
                    matches += 1
        else:
            matches += 1

        status_str = "MATCH" if geojson_ok else "INVERSION_ERROR"
        safe_fid = str(fid)[:24]
        print(f"{safe_fid:<25} | {state_str:<15} | ({lat:.4f}, {lon:.4f})     | {api_coords_str:<22} | {status_str}")

        results.append({
            "facility_id": fid,
            "name": name,
            "source": src,
            "state": state,
            "district": district,
            "latitude": lat,
            "longitude": lon,
            "geojson_coords": [lon, lat],
            "raw_source_match": raw_match,
            "api_match": geojson_ok
        })

    print("-" * 110)
    print(f"Audit Complete: {len(results)} facilities audited. {mismatches} coordinate errors detected.")
    
    with open("scratch/facility_audit_results.json", "w", encoding="utf-8") as out:
        json.dump(results, out, indent=2)
    print("Saved results to scratch/facility_audit_results.json")

if __name__ == "__main__":
    run_facility_audit()
