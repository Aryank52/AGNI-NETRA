"""
AGNI-NETRA — Detailed Inspection & Completeness Audit for NASA FIRMS 2024 Archives
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.stdout.reconfigure(line_buffering=True)
import zipfile
import hashlib
import csv
import io
from collections import defaultdict

TARGET_DIR = r"E:\PROJECTS\AGNI-NETRA(DATABASE)\FIRMS\HISTORICAL\2024\full"

zips = [
    "DL_FIRE_J1V-C2_795861.zip",
    "DL_FIRE_SV-C2_795862.zip",
    "DL_FIRE_J2V-C2_795893.zip",
    "DL_FIRE_M-C61_795860.zip"
]

def calculate_sha256(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

print("=" * 85)
print("  AGNI-NETRA — PHASE 5D: NASA FIRMS 2024 ARCHIVE PRE-INGESTION AUDIT")
print("=" * 85)

overall_stats = {
    "total_files": len(zips),
    "total_source_rows": 0,
    "monthly_rows": defaultdict(int),
    "distinct_dates": set(),
    "file_reports": []
}

for zname in zips:
    zpath = os.path.join(TARGET_DIR, zname)
    if not os.path.exists(zpath):
        print(f"[ERROR] File not found: {zpath}")
        continue

    sz = os.path.getsize(zpath)
    sha = calculate_sha256(zpath)

    # Test ZIP integrity
    zip_ok = True
    try:
        with zipfile.ZipFile(zpath, "r") as zf:
            bad_file = zf.testzip()
            if bad_file:
                zip_ok = False
                print(f"[ERROR] Corrupted file in {zname}: {bad_file}")
    except Exception as e:
        zip_ok = False
        print(f"[ERROR] Invalid ZIP file {zname}: {e}")

    # Inspect contents
    with zipfile.ZipFile(zpath, "r") as zf:
        csv_files = [f for f in zf.namelist() if f.lower().endswith(".csv")]
        readme_files = [f for f in zf.namelist() if f.lower().endswith(".txt")]
        csv_name = csv_files[0] if csv_files else None

        row_count = 0
        min_date = None
        max_date = None
        min_lat, max_lat = float("inf"), float("-inf")
        min_lon, max_lon = float("inf"), float("-inf")
        distinct_dates = set()
        monthly_counts = defaultdict(int)

        if csv_name:
            with zf.open(csv_name) as cf:
                text_stream = io.TextIOWrapper(cf, encoding="utf-8", errors="replace")
                reader = csv.DictReader(text_stream)
                header = reader.fieldnames

                for row in reader:
                    row_count += 1
                    acq_date = row.get("acq_date", "").strip()
                    if acq_date:
                        distinct_dates.add(acq_date)
                        monthly_counts[acq_date[:7]] += 1
                        if min_date is None or acq_date < min_date:
                            min_date = acq_date
                        if max_date is None or acq_date > max_date:
                            max_date = acq_date

                    try:
                        lat = float(row["latitude"])
                        lon = float(row["longitude"])
                        if lat < min_lat: min_lat = lat
                        if lat > max_lat: max_lat = lat
                        if lon < min_lon: min_lon = lon
                        if lon > max_lon: max_lon = lon
                    except (ValueError, TypeError, KeyError):
                        pass

        # Identify product & satellite
        if "J1V-C2" in zname or "VJ114" in zname:
            prod = "VJ114IMGTDL"
            sat = "NOAA-20"
            sensor = "VIIRS"
            res = "375m"
            coll = "Collection 2"
        elif "J2V-C2" in zname or "VJ214" in zname:
            prod = "VJ214IMGTDL"
            sat = "NOAA-21"
            sensor = "VIIRS"
            res = "375m"
            coll = "Collection 2"
        elif "SV-C2" in zname or "VNP14" in zname:
            prod = "VNP14IMGTDL"
            sat = "Suomi-NPP"
            sensor = "VIIRS"
            res = "375m"
            coll = "Collection 2"
        elif "M-C61" in zname or "MCD14" in zname:
            prod = "MCD14DL"
            sat = "Terra/Aqua"
            sensor = "MODIS"
            res = "1km"
            coll = "Collection 6.1"
        else:
            prod, sat, sensor, res, coll = "UNKNOWN", "UNKNOWN", "UNKNOWN", "UNKNOWN", "UNKNOWN"

        file_rep = {
            "filename": zname,
            "filepath": zpath,
            "filesize_bytes": sz,
            "filesize_mb": round(sz / (1024 * 1024), 2),
            "sha256": sha,
            "zip_integrity": "OK" if zip_ok else "CORRUPTED",
            "internal_csv": csv_name,
            "csv_header": header,
            "product": prod,
            "satellite": sat,
            "sensor": sensor,
            "resolution": res,
            "collection": coll,
            "processing_type": "STANDARD_SCIENCE",
            "source_row_count": row_count,
            "min_date": min_date,
            "max_date": max_date,
            "distinct_days": len(distinct_dates),
            "coord_bounds": {
                "min_lat": min_lat,
                "max_lat": max_lat,
                "min_lon": min_lon,
                "max_lon": max_lon
            },
            "monthly_distribution": dict(sorted(monthly_counts.items()))
        }
        overall_stats["file_reports"].append(file_rep)
        overall_stats["total_source_rows"] += row_count
        overall_stats["distinct_dates"].update(distinct_dates)
        for m, c in monthly_counts.items():
            overall_stats["monthly_rows"][m] += c

        print(f"\nArchive: {zname}")
        print(f"  Path          : {zpath}")
        print(f"  Size          : {sz:,} bytes ({file_rep['filesize_mb']} MB)")
        print(f"  SHA-256       : {sha}")
        print(f"  ZIP Integrity : {file_rep['zip_integrity']}")
        print(f"  Internal CSV  : {csv_name}")
        print(f"  Product       : {prod} ({coll}) | Satellite: {sat} | Sensor: {sensor} ({res})")
        print(f"  Source Rows   : {row_count:,}")
        print(f"  Date Range    : [{min_date} .. {max_date}] ({len(distinct_dates)} distinct days)")
        print(f"  Lat Range     : [{min_lat:.4f} .. {max_lat:.4f}]")
        print(f"  Lon Range     : [{min_lon:.4f} .. {max_lon:.4f}]")
        print(f"  Monthly Counts: {dict(sorted(monthly_counts.items()))}")

print("\n" + "=" * 85)
print("  OVERALL 2024 ARCHIVE COMPLETENESS AUDIT")
print("=" * 85)
print(f"Total Source Rows Across Archives: {overall_stats['total_source_rows']:,}")
print(f"Total Distinct Acquisition Days  : {len(overall_stats['distinct_dates'])} / 366 days (2024 is a leap year)")
print(f"Monthly Aggregate Distribution   :")
for m, c in sorted(overall_stats["monthly_rows"].items()):
    print(f"  {m}: {c:,} rows")

all_months_present = len(overall_stats["monthly_rows"]) == 12
full_year_covered = min(overall_stats["distinct_dates"]) == "2024-01-01" and max(overall_stats["distinct_dates"]) == "2024-12-31"

if all_months_present and full_year_covered:
    completeness_status = "2024_COMPLETE"
else:
    completeness_status = "2024_PARTIAL"

print(f"\nCompleteness Evaluation: {completeness_status}")
print("=" * 85)
