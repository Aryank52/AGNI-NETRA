import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import inspect, text
from backend.app.core.database import engine

inspector = inspect(engine)
tables_to_check = [
    'thermal_detections',
    'thermal_history',
    'thermal_events',
    'historical_baselines',
    'facility_baselines'
]

for t in tables_to_check:
    print('=' * 60)
    print(f'TABLE: {t}')
    print('=' * 60)
    cols = inspector.get_columns(t)
    for c in cols:
        print(f"  {c['name']:<25} : {str(c['type']):<20} | Nullable: {c['nullable']}")
    
    # Check indexes
    indexes = inspector.get_indexes(t)
    if indexes:
        print("  Indexes:")
        for idx in indexes:
            col_names = [c for c in idx['column_names'] if c]
            print(f"    - {idx['name']} ({', '.join(col_names)})")
    print()
