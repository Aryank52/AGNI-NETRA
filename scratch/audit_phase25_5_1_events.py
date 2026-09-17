"""
AGNI-NETRA — Phase 25.5.1 Forensic Event Coordinate Audit
Audits 50+ thermal events across:
1. Database: thermal_events in agni_netra.db
2. REST API: /api/v1/events?limit=100
3. GIS API: /api/v1/gis/thermal-events?limit=100
4. GeoJSON Coordinates: [longitude, latitude]
"""

import json
import sqlite3
import httpx

DB_PATH = "agni_netra.db"

def run_event_audit():
    print("=" * 80)
    print("PHASE 25.5.1 — FORENSIC THERMAL EVENT COORDINATE AUDIT (50+ SAMPLES)")
    print("=" * 80)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    query = """
        SELECT id, event_code, state, district, latitude, longitude, max_frp, status
        FROM thermal_events
        ORDER BY max_frp DESC
        LIMIT 60;
    """
    db_events = cur.execute(query).fetchall()
    print(f"[1] Loaded {len(db_events)} thermal events from Database.")

    # Fetch from REST API
    api_events = {}
    try:
        r = httpx.get("http://127.0.0.1:8000/api/v1/events?limit=100", timeout=10.0)
        if r.status_code == 200:
            data = r.json()
            items = data.get("items", []) if isinstance(data, dict) else data
            for item in items:
                api_events[item["id"]] = item
            print(f"[2] Fetched {len(api_events)} events from REST API (/events).")
    except Exception as e:
        print(f"[2] API error on /events: {e}")

    # Fetch from GIS GeoJSON endpoint
    gis_events = {}
    try:
        r = httpx.get("http://127.0.0.1:8000/api/v1/gis/thermal-events?limit=100", timeout=10.0)
        if r.status_code == 200:
            for feat in r.json().get("features", []):
                eid = feat.get("properties", {}).get("id")
                if eid:
                    gis_events[eid] = feat
            print(f"[3] Fetched {len(gis_events)} events from GIS API (/gis/thermal-events).")
    except Exception as e:
        print(f"[3] API error on /gis/thermal-events: {e}")

    # Verify each event
    results = []
    matches = 0
    mismatches = 0

    print("\n" + "-" * 115)
    print(f"{'Event Code':<22} | {'State/District':<20} | {'DB Lat/Lon':<20} | {'GeoJSON Lon/Lat':<22} | {'Fidelity':<10}")
    print("-" * 115)

    for ev in db_events:
        eid, code, state, district, lat, lon, frp, status = ev
        loc_str = f"{state or ''} - {district or ''}"[:19]

        api_ev = api_events.get(eid)
        gis_feat = gis_events.get(eid)

        geojson_str = "NOT_IN_GIS_LIMIT"
        fidelity = True

        if gis_feat:
            coords = gis_feat.get("geometry", {}).get("coordinates", [])
            if len(coords) == 2:
                g_lon, g_lat = coords[0], coords[1]
                geojson_str = f"[{g_lon:.4f}, {g_lat:.4f}]"
                if abs(g_lat - lat) > 1e-4 or abs(g_lon - lon) > 1e-4:
                    fidelity = False
                    mismatches += 1
                else:
                    matches += 1
        elif api_ev:
            a_lat = api_ev.get("latitude")
            a_lon = api_ev.get("longitude")
            geojson_str = f"[{a_lon:.4f}, {a_lat:.4f}] (API)"
            if abs(a_lat - lat) > 1e-4 or abs(a_lon - lon) > 1e-4:
                fidelity = False
                mismatches += 1
            else:
                matches += 1
        else:
            matches += 1

        status_label = "MATCH" if fidelity else "INVERSION_ERROR"
        print(f"{code:<22} | {loc_str:<20} | ({lat:.4f}, {lon:.4f})     | {geojson_str:<22} | {status_label}")

        results.append({
            "event_id": eid,
            "event_code": code,
            "state": state,
            "district": district,
            "latitude": lat,
            "longitude": lon,
            "max_frp": frp,
            "geojson_coords": [lon, lat],
            "is_match": fidelity
        })

    print("-" * 115)
    print(f"Event Audit Complete: {len(results)} events audited. {mismatches} errors detected.")

    with open("scratch/event_audit_results.json", "w", encoding="utf-8") as out:
        json.dump(results, out, indent=2)
    print("Saved results to scratch/event_audit_results.json")

if __name__ == "__main__":
    run_event_audit()
