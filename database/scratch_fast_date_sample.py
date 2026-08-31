import sys
sys.stdout.reconfigure(line_buffering=True)
import zipfile
import csv
import io

zips = [
    r"C:\Users\HP\Downloads\DL_FIRE_M-C61_794933.zip",
    r"C:\Users\HP\Downloads\DL_FIRE_SV-C2_794937.zip",
    r"C:\Users\HP\Downloads\DL_FIRE_J1V-C2_794935.zip",
    r"C:\Users\HP\Downloads\DL_FIRE_J2V-C2_794936.zip",
    r"C:\Users\HP\Downloads\DL_FIRE_LS_794934.zip"
]

for zp in zips:
    print(f"\n==========================================")
    print(f"Archive: {zp}")
    with zipfile.ZipFile(zp, "r") as zf:
        for fname in zf.namelist():
            if fname.endswith(".csv"):
                with zf.open(fname) as f:
                    ts = io.TextIOWrapper(f, encoding="utf-8")
                    reader = csv.reader(ts)
                    hdr = next(reader, None)
                    date_idx = -1
                    if hdr:
                        for idx, col in enumerate(hdr):
                            if "acq_date" in col.lower():
                                date_idx = idx
                                break
                    print(f"  File: {fname} | Header: {hdr}")
                    # sample first 5 and last 5 rows
                    first_dates = []
                    for _ in range(5):
                        r = next(reader, None)
                        if r and date_idx >= 0 and date_idx < len(r):
                            first_dates.append(r[date_idx])
                    print(f"  First 5 dates: {first_dates}")
