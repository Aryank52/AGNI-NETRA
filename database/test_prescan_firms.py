import os
import sys
import csv
from datetime import datetime, timezone
from shapely.geometry import Point, Polygon

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from data_pipeline.adapters.firms_adapter import INDIA_BBOX, INDIA_TERRITORIAL_POLYGON

CSV_PATH = r"E:\PROJECTS\AGNI-NETRA(DATABASE)\FIRMS\Extracted files\fire_archive_J1V-C2_794935.csv"

print(f"Scanning {CSV_PATH} for India boundaries...")
total_rows = 0
inside_bbox = 0
inside_polygon = 0
outside_india = 0

min_date = "9999-99-99"
max_date = "0000-00-00"

with open(CSV_PATH, "r", encoding="utf-8", errors="replace") as f:
    reader = csv.DictReader(f)
    for row in reader:
        total_rows += 1
        lat = float(row["latitude"])
        lon = float(row["longitude"])
        d = row["acq_date"]
        
        if (INDIA_BBOX[0] <= lat <= INDIA_BBOX[2]) and (INDIA_BBOX[1] <= lon <= INDIA_BBOX[3]):
            inside_bbox += 1
            pt = Point(lon, lat)
            if INDIA_TERRITORIAL_POLYGON.contains(pt):
                inside_polygon += 1
                if d < min_date:
                    min_date = d
                if d > max_date:
                    max_date = d
            else:
                outside_india += 1
        else:
            outside_india += 1
            
        if total_rows % 1000000 == 0:
            print(f"Progress: {total_rows:,} rows scanned... (India polygon matches: {inside_polygon:,})")

print("=" * 60)
print(f"Total Rows in File        : {total_rows:,}")
print(f"Inside India Bounding Box : {inside_bbox:,}")
print(f"Inside India Polygon      : {inside_polygon:,}")
print(f"Outside India             : {outside_india:,}")
print(f"Date Range in India       : {min_date} to {max_date}")
print("=" * 60)
