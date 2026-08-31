import zipfile
import csv
import io

zips = [
    r"C:\Users\HP\Downloads\DL_FIRE_M-C61_794933.zip",
    r"C:\Users\HP\Downloads\DL_FIRE_SV-C2_794937.zip",
    r"C:\Users\HP\Downloads\DL_FIRE_J1V-C2_794935.zip",
    r"C:\Users\HP\Downloads\DL_FIRE_J2V-C2_794936.zip",
]

for zp in zips:
    print(f"\n==========================================")
    print(f"Checking: {zp}")
    with zipfile.ZipFile(zp, "r") as zf:
        for fname in zf.namelist():
            if fname.endswith(".csv"):
                print(f"  Inspecting CSV: {fname}")
                with zf.open(fname) as f:
                    ts = io.TextIOWrapper(f, encoding="utf-8")
                    reader = csv.DictReader(ts)
                    row_count = 0
                    min_date = None
                    max_date = None
                    years = set()
                    for row in reader:
                        row_count += 1
                        d = row.get("acq_date", "")
                        if d:
                            years.add(d[:4])
                            if min_date is None or d < min_date:
                                min_date = d
                            if max_date is None or d > max_date:
                                max_date = d
                        if row_count % 500000 == 0:
                            print(f"    ... read {row_count:,} rows (current years: {years})")
                    print(f"    Total Rows: {row_count:,} | Date Range: [{min_date} .. {max_date}] | Years: {sorted(list(years))}")
