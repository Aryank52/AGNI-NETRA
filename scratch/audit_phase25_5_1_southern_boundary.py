"""
AGNI-NETRA — Phase 25.5.1 Southern India & Sri Lanka Boundary Audit
Audits:
1. Southern tip facilities (Kanniyakumari, Tirunelveli, Tuticorin, Kerala coast)
2. Sri Lanka bounding box (5.9N - 9.9N, 79.5E - 82.0E)
3. Coordinate validity, administrative jurisdiction, and GeoJSON serialization
"""

import sqlite3
import json

DB_PATH = "agni_netra.db"

def run_boundary_audit():
    print("=" * 80)
    print("PHASE 25.5.1 — SOUTHERN INDIA & SRI LANKA BOUNDARY FORENSIC AUDIT")
    print("=" * 80)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # 1. Check for ANY records inside Sri Lanka bounding box
    # Sri Lanka: Lat 5.9°N to 9.85°N, Lon 79.6°E to 81.9°E
    print("\n[1] Checking for points inside Sri Lanka geographic bounding box [5.9N - 9.85N, 79.6E - 81.9E]...")
    sl_facs = cur.execute("""
        SELECT count(*) FROM industrial_facilities
        WHERE latitude BETWEEN 5.9 AND 9.85 AND longitude BETWEEN 79.6 AND 81.9;
    """).fetchone()[0]
    sl_evts = cur.execute("""
        SELECT count(*) FROM thermal_events
        WHERE latitude BETWEEN 5.9 AND 9.85 AND longitude BETWEEN 79.6 AND 81.9;
    """).fetchone()[0]
    sl_dets = cur.execute("""
        SELECT count(*) FROM thermal_detections
        WHERE latitude BETWEEN 5.9 AND 9.85 AND longitude BETWEEN 79.6 AND 81.9;
    """).fetchone()[0]

    print(f"    Industrial facilities in Sri Lanka box: {sl_facs}")
    print(f"    Thermal events in Sri Lanka box:        {sl_evts}")
    print(f"    Thermal detections in Sri Lanka box:    {sl_dets}")

    if sl_facs == 0 and sl_evts == 0 and sl_dets == 0:
        print("    --> ZERO LEAKAGE: Sovereign boundary strictly enforced.")
    else:
        print("    --> WARNING: Points detected within Sri Lanka boundary!")

    # 2. Sample Southernmost Indian facilities (lat < 8.8°N)
    print("\n[2] Sampling Southernmost Indian Facilities (lat < 8.8°N)...")
    southern_facs = cur.execute("""
        SELECT id, name, state, district, latitude, longitude, facility_type
        FROM industrial_facilities
        WHERE latitude < 8.8 AND latitude >= 8.0
        ORDER BY latitude ASC
        LIMIT 20;
    """).fetchall()

    print(f"    Found {len(southern_facs)} southern mainland facilities:")
    print("-" * 105)
    print(f"{'Facility Name':<40} | {'State':<12} | {'District':<15} | {'Latitude':<9} | {'Longitude':<9}")
    print("-" * 105)
    for fac in southern_facs:
        fid, name, state, district, lat, lon, ftype = fac
        s_name = str(name or fid)[:38].encode('ascii', 'replace').decode('ascii')
        s_state = str(state or '')[:12].encode('ascii', 'replace').decode('ascii')
        s_dist = str(district or '')[:15].encode('ascii', 'replace').decode('ascii')
        print(f"{s_name:<40} | {s_state:<12} | {s_dist:<15} | {lat:<9.4f} | {lon:<9.4f}")
    print("-" * 105)

    # 3. Verify territorial jurisdiction of southern facilities
    districts = set([f[3] for f in southern_facs if f[3]])
    states = set([f[2] for f in southern_facs if f[2]])
    print(f"\n[3] Territorial Jurisdiction Check:")
    clean_states = {str(s).encode('ascii', 'replace').decode('ascii') for s in states}
    print(f"    States:    {clean_states}")
    clean_districts = {str(d).encode('ascii', 'replace').decode('ascii') for d in districts}
    print(f"    Districts: {clean_districts}")

    # 4. Save audit summary
    boundary_results = {
        "sri_lanka_leakage": {
            "facilities": sl_facs,
            "events": sl_evts,
            "detections": sl_dets,
            "status": "PASS" if (sl_facs == 0 and sl_evts == 0 and sl_dets == 0) else "FAIL"
        },
        "southern_samples": [
            {
                "name": str(f[1] or f[0]),
                "state": f[2],
                "district": f[3],
                "latitude": f[4],
                "longitude": f[5]
            }
            for f in southern_facs
        ]
    }
    with open("scratch/southern_boundary_results.json", "w", encoding="utf-8") as out:
        json.dump(boundary_results, out, indent=2)
    print("Saved boundary results to scratch/southern_boundary_results.json")

if __name__ == "__main__":
    run_boundary_audit()
