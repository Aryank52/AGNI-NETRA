import os
import zipfile
import csv
import io
import hashlib

downloads_dir = r"C:\Users\HP\Downloads"
zips = [
    "DL_FIRE_M-C61_794933.zip",
    "DL_FIRE_SV-C2_794937.zip",
    "DL_FIRE_J1V-C2_794935.zip",
    "DL_FIRE_J2V-C2_794936.zip",
    "DL_FIRE_LS_794934.zip",
    "DL_FIRE_J1V-C2_795685.zip",
    "DL_FIRE_SV-C2_795686.zip",
    "DL_FIRE_M-C61_795684.zip"
]

print("Scanning ZIP files in Downloads:")
for zname in zips:
    zpath = os.path.join(downloads_dir, zname)
    if not os.path.exists(zpath):
        print(f"File {zname}: NOT FOUND")
        continue
    sz = os.path.getsize(zpath)
    print(f"\n==========================================")
    print(f"File: {zname} ({sz:,} bytes)")
    
    with zipfile.ZipFile(zpath, "r") as zf:
        for info in zf.infolist():
            print(f"  Inner entry: {info.filename} ({info.file_size:,} bytes)")
            if info.filename.endswith(".csv") or info.filename.endswith(".txt"):
                with zf.open(info.filename) as f:
                    ts = io.TextIOWrapper(f, encoding="utf-8", errors="replace")
                    reader = csv.reader(ts)
                    header = next(reader, None)
                    row_first = next(reader, None)
                    print(f"    Header: {header}")
                    if row_first:
                        print(f"    First row: {row_first[:6]}")
