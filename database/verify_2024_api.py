"""
AGNI-NETRA — Local API Endpoint Verification for 2024 Historical Data
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.stdout.reconfigure(line_buffering=True)
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

print("=" * 85)
print("  AGNI-NETRA — 2024 LOCAL API ENDPOINTS VERIFICATION")
print("=" * 85)

# 1. Test /api/v1/historical/observations for NOAA-21 in 2024
resp_obs = client.get("/api/v1/historical/observations?time_window=5Y&sensor=VIIRS_NOAA21&limit=5")
print(f"GET /api/v1/historical/observations (NOAA-21, 5Y): Status {resp_obs.status_code}")
if resp_obs.status_code == 200:
    data = resp_obs.json()
    items = data.get("items", []) if isinstance(data, dict) else data
    print(f"  Total count matching NOAA-21: {data.get('total_count', 0):,}")
    print(f"  Returned {len(items)} sample items")
    if items:
        first = items[0]
        print(f"  Sample 2024 NOAA-21 Item: id={first.get('id')} | acq_date={first.get('acq_date')} | sat={first.get('satellite')} | conf={first.get('confidence')}")
else:
    print(f"  Response: {resp_obs.text[:300]}")

# 2. Test /api/v1/historical/timeline for 2024
resp_tl = client.get("/api/v1/historical/timeline")
print(f"\nGET /api/v1/historical/timeline: Status {resp_tl.status_code}")
if resp_tl.status_code == 200:
    tl = resp_tl.json().get("timeline", [])
    print(f"  Total timeline periods: {len(tl)}")
    print("  2024 Monthly Timeline Breakdown:")
    for p in tl:
        if p["period"].startswith("2024"):
            print(f"    {p['period']}: {p['detection_count']:,} detections | avg FRP: {p['avg_frp']} MW | max FRP: {p['max_frp']} MW")
else:
    print(f"  Response: {resp_tl.text[:300]}")

print("=" * 85)
