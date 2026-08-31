"""
AGNI-NETRA — Local API Endpoint Verification for 2023 Historical Data
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.stdout.reconfigure(line_buffering=True)
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

print("=" * 85)
print("  AGNI-NETRA — 2023 LOCAL API ENDPOINTS VERIFICATION")
print("=" * 85)

# 1. Test /api/v1/historical/observations for 2023
resp_obs = client.get("/api/v1/historical/observations?start_date=2023-01-01&end_date=2023-12-31&limit=5")
print(f"GET /api/v1/historical/observations (2023): Status {resp_obs.status_code}")
if resp_obs.status_code == 200:
    data = resp_obs.json()
    items = data.get("items", []) if isinstance(data, dict) else data
    print(f"  Returned {len(items)} sample items")
    if items:
        first = items[0]
        print(f"  Sample 2023 Item: id={first.get('id')} | acq_date={first.get('acq_date')} | sat={first.get('satellite')} | conf={first.get('confidence')}")
else:
    print(f"  Response: {resp_obs.text[:300]}")

# 2. Test /api/v1/historical/timeline for 2023
resp_tl = client.get("/api/v1/historical/timeline?year=2023")
print(f"\nGET /api/v1/historical/timeline (2023): Status {resp_tl.status_code}")
if resp_tl.status_code == 200:
    tl_data = resp_tl.json()
    print(f"  Timeline summary keys/data: {list(tl_data.keys()) if isinstance(tl_data, dict) else len(tl_data)}")
    if isinstance(tl_data, dict):
        monthly = tl_data.get("monthly_distribution", {})
        print(f"  Monthly points in timeline: {len(monthly)}")
else:
    print(f"  Response: {resp_tl.text[:300]}")

print("=" * 85)
