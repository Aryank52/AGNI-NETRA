"""
AGNI-NETRA — High-Performance CEA Power Station Ingestion Pipeline
Extracts tabular power unit information from the official 24-page document:
`List_of_Power_Station_as_on_31.03.2025.pdf`
Loads unit-level records into `cea_power_stations_staging` and computes project-level aggregations.
"""

import os
import sys
import re
import json
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pdfplumber
from sqlalchemy import text
from backend.app.core.database import engine
from data_pipeline.osm_classifier import normalize_name, normalize_state


CANDIDATE_PDF_PATHS = [
    r"E:\PROJECTS\AGNI-NETRA(DATABASE)\FACILITIES\CEA\List_of_Power_Station_as_on_31.03.2025.pdf",
    r"C:\Users\HP\Downloads\List_of_Power_Station_as_on_31.03.2025.pdf"
]


def find_cea_pdf_file() -> str:
    for path in CANDIDATE_PDF_PATHS:
        if os.path.exists(path):
            return path
    raise FileNotFoundError(f"CEA Power Station PDF not found in paths: {CANDIDATE_PDF_PATHS}")


def clean_cea_state_and_sector(state_raw: str, sector_raw: str) -> Tuple[str, str]:
    """
    Cleans OCR/table border shifts between State and Sector columns.
    """
    st = state_raw.strip() if state_raw else ""
    sec = sector_raw.strip() if sector_raw else ""

    # Common OCR/Table artifacts in CEA PDF
    if "ePsh" in sec or "ePsh" in st:
        combined = (st + " " + sec).replace("ePsh", "").replace("rivate Sector", "").strip()
        st = combined
        sec = "Private Sector"
    elif "Private Sector" in st:
        st = st.replace("Private Sector", "").strip()
        sec = "Private Sector"
    elif "State Sector" in st:
        st = st.replace("State Sector", "").strip()
        sec = "State Sector"
    elif "Central Sector" in st:
        st = st.replace("Central Sector", "").strip()
        sec = "Central Sector"

    # Normalize state name
    norm_st = normalize_state(st) if st else "National / Unspecified"
    return norm_st, sec


def clean_prime_mover(pm_raw: Optional[str]) -> str:
    if not pm_raw:
        return "Thermal / Unspecified"
    pm = pm_raw.strip()
    if pm.lower() in ["steam", "coal", "lignite"]:
        return "Steam"
    elif "gt-gas" in pm.lower() or "gas" in pm.lower() or "ccpp" in pm.lower():
        return "GT-Gas"
    elif "hydro" in pm.lower() or "hydel" in pm.lower():
        return "Hydro"
    elif "nuclear" in pm.lower() or "atomic" in pm.lower():
        return "Nuclear"
    elif "diesel" in pm.lower():
        return "Diesel"
    return pm


def parse_cea_pdf(pdf_path: str) -> List[Dict[str, Any]]:
    """
    Parses all 24 pages of the CEA Power Station PDF.
    Returns structured unit-level dictionary records.
    """
    print(f"[AGNI-NETRA] Opening CEA PDF: {pdf_path}")
    unit_records = []

    current_region = None
    current_state = None
    current_sector = None
    current_org = None
    current_project = None
    current_prime_mover = None

    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        print(f"[AGNI-NETRA] Extracting tables across {total_pages} pages...")

        for page_num, page in enumerate(pdf.pages, 1):
            tables = page.extract_tables()
            if not tables or len(tables[0]) == 0:
                continue

            for row_idx, row in enumerate(tables[0]):
                if not row or len(row) < 9:
                    continue

                row_str = " ".join(str(c) for c in row if c)
                # Skip headers and subtotal rows
                if any(h in row_str for h in ["S.No.", "Name of Project", "Appendix", "Installed", "Capacity(MW)"]):
                    continue
                if "Total" in row_str or "TOTAL" in row_str:
                    continue

                s_no = str(row[0]).strip() if row[0] else ""
                region_val = str(row[1]).strip() if len(row) > 1 and row[1] else current_region
                if region_val:
                    current_region = region_val

                state_raw = str(row[2]).strip() if len(row) > 2 and row[2] else ""
                sector_raw = str(row[3]).strip() if len(row) > 3 and row[3] else ""

                if state_raw or sector_raw:
                    c_st, c_sec = clean_cea_state_and_sector(state_raw, sector_raw)
                    if state_raw:
                        current_state = c_st
                    if sector_raw:
                        current_sector = c_sec

                org_val = str(row[4]).strip() if len(row) > 4 and row[4] else ""
                if org_val:
                    current_org = org_val

                proj_val = str(row[5]).strip() if len(row) > 5 and row[5] else ""
                if proj_val:
                    current_project = proj_val

                pm_val = str(row[6]).strip() if len(row) > 6 and row[6] else ""
                if pm_val:
                    current_prime_mover = clean_prime_mover(pm_val)

                unit_no = str(row[7]).strip() if len(row) > 7 and row[7] else ""
                cap_str = str(row[8]).strip() if len(row) > 8 and row[8] else ""
                year_str = str(row[9]).strip() if len(row) > 9 and row[9] else ""

                if not unit_no and not cap_str and not year_str:
                    continue

                try:
                    cap_mw = float(cap_str.replace(",", "").replace("MW", "").strip())
                except ValueError:
                    cap_mw = None

                try:
                    year_comm = int(re.sub(r"\D", "", year_str)[:4])
                except (ValueError, IndexError):
                    year_comm = None

                if current_project and (unit_no or cap_mw is not None):
                    # Generate stable unique CEA Record ID
                    safe_proj = re.sub(r"[^a-zA-Z0-9]+", "_", current_project).strip("_")
                    safe_unit = re.sub(r"[^a-zA-Z0-9]+", "_", unit_no).strip("_") or f"U{row_idx}"
                    cea_record_id = f"CEA-P{page_num:02d}-R{row_idx:02d}-{safe_proj[:30]}-{safe_unit}"

                    unit_rec = {
                        "id": cea_record_id,
                        "cea_record_id": cea_record_id,
                        "source_document": os.path.basename(pdf_path),
                        "source_date": "2025-03-31",
                        "page_number": page_num,
                        "s_no": s_no,
                        "region": current_region,
                        "state": current_state,
                        "sector": current_sector,
                        "organisation": current_org,
                        "project_name": current_project,
                        "prime_mover": current_prime_mover,
                        "unit_no": unit_no,
                        "installed_capacity_mw": cap_mw,
                        "year_of_commissioning": year_comm,
                        "raw_row_text": row_str
                    }
                    unit_records.append(unit_rec)

    print(f"[AGNI-NETRA] Total valid unit records extracted: {len(unit_records):,}")
    return unit_records


def run_cea_ingestion() -> List[Dict[str, Any]]:
    """
    Executes CEA PDF parsing and database staging ingestion.
    """
    pdf_path = find_cea_pdf_file()
    start_time = time.time()
    unit_records = parse_cea_pdf(pdf_path)

    print(f"\n[AGNI-NETRA] Ingesting {len(unit_records):,} records into cea_power_stations_staging...")

    staging_insert_query = text("""
        INSERT INTO cea_power_stations_staging (
            id, cea_record_id, source_document, source_date, page_number,
            s_no, region, state, sector, organisation,
            project_name, prime_mover, unit_no,
            installed_capacity_mw, year_of_commissioning, raw_row_text
        ) VALUES (
            :id, :cea_record_id, :source_document, :source_date, :page_number,
            :s_no, :region, :state, :sector, :organisation,
            :project_name, :prime_mover, :unit_no,
            :installed_capacity_mw, :year_of_commissioning, :raw_row_text
        )
        ON CONFLICT (cea_record_id) DO UPDATE SET
            region = EXCLUDED.region,
            state = EXCLUDED.state,
            sector = EXCLUDED.sector,
            organisation = EXCLUDED.organisation,
            project_name = EXCLUDED.project_name,
            prime_mover = EXCLUDED.prime_mover,
            unit_no = EXCLUDED.unit_no,
            installed_capacity_mw = EXCLUDED.installed_capacity_mw,
            year_of_commissioning = EXCLUDED.year_of_commissioning,
            raw_row_text = EXCLUDED.raw_row_text;
    """)

    batch_size = 500
    with engine.begin() as conn:
        for i in range(0, len(unit_records), batch_size):
            batch = unit_records[i : i + batch_size]
            conn.execute(staging_insert_query, batch)
            print(f"  -> Staged: {min(i + batch_size, len(unit_records)):,} / {len(unit_records):,} units...")

    elapsed = time.time() - start_time
    print(f"[AGNI-NETRA] CEA staging ingestion completed in {elapsed:.2f} seconds.")
    return unit_records


if __name__ == "__main__":
    run_cea_ingestion()
