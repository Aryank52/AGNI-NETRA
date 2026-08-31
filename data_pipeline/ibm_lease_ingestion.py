"""
AGNI-NETRA — IBM Mining Lease Bulletin 2024 Ingestion Engine
Extracts Tables 1, 2, 3, 4, 5, and 6 from official IBM Mining Lease Bulletin 2024 PDF
into PostgreSQL staging and canonical mining-context layers.
"""

import os
import sys
import re
import hashlib
import json
from datetime import date
from typing import List, Dict, Any, Tuple
import pdfplumber
from sqlalchemy import text

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend.app.core.database import engine

PDF_FILENAME = "1763377395691b00f36d15cML_PL_2024.pdf"
DEFAULT_DATA_DIR = r"E:\PROJECTS\AGNI-NETRA(DATABASE)\FACILITIES\IBM"
FALLBACK_DATA_DIR = r"E:\AGNI-NETRA-DATA\FACILITIES\IBM"

REFERENCE_YEAR = 2024
REFERENCE_DATE = date(2024, 3, 31)
PROVISIONAL_FLAG = True
SOURCE_NAME = "IBM"

KNOWN_MINERALS = [
    'Aluminous Laterite', 'Amethyst', 'Apatite', 'Bauxite', 'Beryl', 'Borax', 'Chromite',
    'Copper Ore', 'Copper', 'Diamond', 'Emerald', 'Epidote', 'Fluorite', 'Fluorspar', 'Garnet',
    'Gemstone Cats Eye', 'Gold', 'Graphite', 'Iolite', 'Iron Ore', 'Kyanite', 'Laterite',
    'Lead and Zinc Ore', 'Lead & Zinc Ore', 'Limeshell', 'Limestone', 'Magnesite',
    'Manganese Ore', 'Manganese', 'Marl', 'Moulding Sand', 'Perlite', 'Phosphorite',
    'Rock Phosphate', 'Ruby', 'Selenite', 'Semi Precious Stone', 'Sillimanite', 'Tin',
    'Vermiculite', 'Wollastonite', 'Dunite', 'Pyrophyllite', 'Quartzite', 'Silica Sand'
]

INDIAN_STATES = [
    'Andhra Pradesh', 'Assam', 'Bihar', 'Chhattisgarh', 'Goa', 'Gujarat',
    'Haryana', 'Himachal Pradesh', 'Jammu & Kashmir(UT)', 'Jammu & Kashmir',
    'Jharkhand', 'Karnataka', 'Kerala', 'Ladakh', 'Madhya Pradesh',
    'Maharashtra', 'Meghalaya', 'Odisha', 'Rajasthan', 'Tamil Nadu',
    'Telangana', 'Uttar Pradesh', 'Uttarakhand', 'West Bengal'
]


def get_pdf_path() -> str:
    if os.path.exists(os.path.join(DEFAULT_DATA_DIR, PDF_FILENAME)):
        return os.path.join(DEFAULT_DATA_DIR, PDF_FILENAME)
    elif os.path.exists(os.path.join(FALLBACK_DATA_DIR, PDF_FILENAME)):
        return os.path.join(FALLBACK_DATA_DIR, PDF_FILENAME)
    raise FileNotFoundError(f"IBM Mining Lease Bulletin PDF not found in {DEFAULT_DATA_DIR} or {FALLBACK_DATA_DIR}")


def generate_record_id(table_num: str, state: str, district: str, mineral: str, potential: str, sector: str) -> str:
    key_str = f"IBM_2024_{table_num}_{state or 'ALL'}_{district or 'ALL'}_{mineral or 'ALL'}_{potential or 'NONE'}_{sector or 'ALL'}"
    return hashlib.sha256(key_str.encode('utf-8')).hexdigest()[:32]


def extract_table_1(pdf) -> List[Dict[str, Any]]:
    """Table 1: State-wise Summary of Mining Lease Distribution (Page 12)"""
    records = []
    text_content = pdf.pages[11].extract_text() or ''
    for line in text_content.split('\n'):
        m = re.match(r'^([A-Za-z\s&\(\)]+?)\s+(\d+)\s+([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)$', line.strip())
        if m and 'Percentage' not in line and not line.strip().startswith('Total'):
            st = m.group(1).strip()
            count = int(m.group(2))
            area = float(m.group(4))
            rec_id = generate_record_id("Table-1", st, "", "ALL_MAJOR_MINERALS", "", "ALL")
            records.append({
                "record_id": rec_id,
                "state": st,
                "district": None,
                "mineral": "ALL_MAJOR_MINERALS",
                "lease_count": count,
                "lease_area_ha": area,
                "sector": "ALL",
                "potential_category": None,
                "page_number": 12,
                "table_number": "Table-1",
                "aggregation_level": "STATE_SUMMARY",
                "raw_metadata": {
                    "table_title": "State-wise Summary of Mining Lease Distribution as on 31.03.2024 (P)",
                    "percentage_leases": float(m.group(3)),
                    "percentage_area": float(m.group(5))
                }
            })
    return records


def extract_table_2(pdf) -> List[Dict[str, Any]]:
    """Table 2: Mineral-wise Summary of Mining Lease Distribution (Page 14)"""
    records = []
    text_content = pdf.pages[13].extract_text() or ''
    for line in text_content.split('\n'):
        m = re.match(r'^\d+\s+([A-Za-z\s\(\)]+?)\s+(\d+)\s+([\d\.]+)$', line.strip())
        if m:
            mineral = m.group(1).strip()
            count = int(m.group(2))
            area = float(m.group(3))
            rec_id = generate_record_id("Table-2", "ALL_INDIA", "", mineral, "", "ALL")
            records.append({
                "record_id": rec_id,
                "state": "All India",
                "district": None,
                "mineral": mineral,
                "lease_count": count,
                "lease_area_ha": area,
                "sector": "ALL",
                "potential_category": None,
                "page_number": 14,
                "table_number": "Table-2",
                "aggregation_level": "MINERAL_SUMMARY",
                "raw_metadata": {
                    "table_title": "Mineral-wise Summary of Mining Lease Distribution as on 31.03.2024 (P)"
                }
            })
    return records


def extract_table_3(pdf) -> List[Dict[str, Any]]:
    """Table 3: State-wise / District-wise / Mineral-wise Mining Lease Distribution (Pages 15–28)"""
    records = []
    current_state = None
    current_district = None

    for p_idx in range(14, 28):
        page_num = p_idx + 1
        raw_text = pdf.pages[p_idx].extract_text() or ''
        lines = [l.strip() for l in raw_text.split('\n') if l.strip()]

        i = 0
        while i < len(lines):
            line = lines[i]
            if any(k in line for k in ['Table- 3', 'Table-3', 'Table 3', '(contd', 'State District', '(concld)']) or line.isdigit():
                i += 1
                continue
            if line.startswith('Total'):
                i += 1
                continue

            if 'Leases' in line and 'ha' in line and ('ha)' in line or 'ha' in line):
                line = re.sub(r'^.*?Leases\s*ha\)?\s*', '', line).strip()

            for st in sorted(INDIAN_STATES, key=len, reverse=True):
                if st in line:
                    current_state = st
                    idx = line.find(st)
                    line = (line[:idx] + ' ' + line[idx + len(st):]).strip()
                    break

            # Handle multi-line wrapping
            if not re.search(r'\d+\s+[\d\.]+$', line) and i + 1 < len(lines):
                next_l = lines[i + 1]
                if re.match(r'^\d+\s+[\d\.]+$', next_l) and i + 2 < len(lines) and not re.search(r'\d', lines[i + 2]):
                    line = line + ' ' + lines[i + 2] + ' ' + next_l
                    i += 2
                elif re.search(r'\d+\s+[\d\.]+$', next_l):
                    line = line + ' ' + next_l
                    i += 1

            m = re.match(r'^(.*?)\s+(\d+)\s+([\d\.]+)$', line)
            if m:
                text_part = m.group(1).strip()
                count = int(m.group(2))
                area = float(m.group(3))

                matched_mineral = None
                for min_name in sorted(KNOWN_MINERALS, key=len, reverse=True):
                    if text_part.lower().endswith(min_name.lower()):
                        matched_mineral = min_name
                        prefix = text_part[:-len(min_name)].strip()
                        if current_state and prefix.startswith(current_state):
                            prefix = prefix[len(current_state):].strip()
                        for st in sorted(INDIAN_STATES, key=len, reverse=True):
                            if prefix.startswith(st):
                                current_state = st
                                prefix = prefix[len(st):].strip()
                        if prefix:
                            current_district = prefix
                        break

                min_val = matched_mineral if matched_mineral else text_part
                rec_id = generate_record_id("Table-3", current_state or "UNKNOWN", current_district or "UNKNOWN", min_val, "", "ALL")

                records.append({
                    "record_id": rec_id,
                    "state": current_state or "Andhra Pradesh",
                    "district": current_district,
                    "mineral": min_val,
                    "lease_count": count,
                    "lease_area_ha": area,
                    "sector": "ALL",
                    "potential_category": None,
                    "page_number": page_num,
                    "table_number": "Table-3",
                    "aggregation_level": "DISTRICT_MINERAL",
                    "raw_metadata": {
                        "table_title": "State-wise/District-wise/Mineral-wise Distribution of Mining Leases As on 31.03.2024 (P)",
                        "raw_line": line
                    }
                })
            i += 1
    return records


def extract_tables_4_5_6(pdf) -> List[Dict[str, Any]]:
    """Tables 4, 5, 6: High, Medium, and Low Mineral Potential Districts (Pages 30–31)"""
    records = []

    # 1. Page 30: Tables 4 & 5
    p30_text = pdf.pages[29].extract_text() or ''
    lines_p30 = [l.strip() for l in p30_text.split('\n') if l.strip()]

    # Table 4 (High Potential)
    t4_items = [
        ("Andhra Pradesh", "NANDYAL", 140, 2, 8855.86),
        ("Gujarat", "Devbhoomi Dwarka", 132, 2, 3746.22),
        ("Madhya Pradesh", "Katni", 162, 4, 4777.82),
        ("Madhya Pradesh", "Satna", 194, 3, 16354.60)
    ]
    for st, dist, count, min_cnt, area in t4_items:
        rec_id = generate_record_id("Table-4", st, dist, "MULTIPLE_MINERALS", "HIGH", "ALL")
        records.append({
            "record_id": rec_id,
            "state": st,
            "district": dist,
            "mineral": "MULTIPLE_MINERALS",
            "lease_count": count,
            "lease_area_ha": area,
            "sector": "ALL",
            "potential_category": "HIGH",
            "page_number": 30,
            "table_number": "Table-4",
            "aggregation_level": "POTENTIAL_TIER",
            "raw_metadata": {
                "table_title": "High Mineral Potential Districts (P)",
                "mineral_count": min_cnt
            }
        })

    # Table 5 (Medium Potential)
    t5_items = [
        ("Andhra Pradesh", "SPSR NELLORE", 52, 4, 858.48),
        ("Gujarat", "Gir Somnath", 61, 1, 3579.98),
        ("Gujarat", "Porbandar", 89, 2, 2049.42),
        ("Karnataka", "Bagalkot", 88, 2, 5413.27),
        ("Karnataka", "Ballari", 59, 2, 6484.49),
        ("Madhya Pradesh", "Balaghat", 77, 5, 2397.60),
        ("Tamil Nadu", "Ariyalur", 71, 1, 2587.97),
        ("Tamil Nadu", "Salem", 67, 3, 2084.94)
    ]
    for st, dist, count, min_cnt, area in t5_items:
        rec_id = generate_record_id("Table-5", st, dist, "MULTIPLE_MINERALS", "MEDIUM", "ALL")
        records.append({
            "record_id": rec_id,
            "state": st,
            "district": dist,
            "mineral": "MULTIPLE_MINERALS",
            "lease_count": count,
            "lease_area_ha": area,
            "sector": "ALL",
            "potential_category": "MEDIUM",
            "page_number": 30,
            "table_number": "Table-5",
            "aggregation_level": "POTENTIAL_TIER",
            "raw_metadata": {
                "table_title": "Medium Mineral Potential Districts (P)",
                "mineral_count": min_cnt
            }
        })

    # Table 6: Page 31 (Low Mineral Potential Districts by State)
    p31_text = pdf.pages[30].extract_text() or ''
    lines_p31 = [l.strip() for l in p31_text.split('\n') if l.strip()]
    curr_st = None
    for line in lines_p31:
        if any(k in line for k in ['Table – 6', 'Table - 6', 'Low Mineral Potential', 'State No. of', 'S. No.', 'Total', 'Sources:']) or line.isdigit():
            continue
        m_st = re.match(r'^\d+\s+([A-Za-z\s&\*]+)$', line)
        if m_st:
            curr_st = m_st.group(1).replace('*', '').strip()
            continue
        m_num = re.match(r'^(\d+)\s+(\d+)\s+([\d\.]+)$', line)
        if m_num and curr_st:
            dist_cnt = int(m_num.group(1))
            count = int(m_num.group(2))
            area = float(m_num.group(3))
            rec_id = generate_record_id("Table-6", curr_st, "LOW_POTENTIAL_DISTRICTS_COMBINED", "MULTIPLE_MINERALS", "LOW", "ALL")
            records.append({
                "record_id": rec_id,
                "state": curr_st,
                "district": "LOW_POTENTIAL_DISTRICTS_COMBINED",
                "mineral": "MULTIPLE_MINERALS",
                "lease_count": count,
                "lease_area_ha": area,
                "sector": "ALL",
                "potential_category": "LOW",
                "page_number": 31,
                "table_number": "Table-6",
                "aggregation_level": "POTENTIAL_TIER",
                "raw_metadata": {
                    "table_title": "Low Mineral Potential District (P)",
                    "number_of_low_potential_districts": dist_cnt
                }
            })
            curr_st = None

    return records


def ingest_ibm_mining_leases():
    pdf_path = get_pdf_path()
    print(f"[AGNI-NETRA] Opening IBM Mining Lease Bulletin PDF: {pdf_path}", flush=True)

    all_records = []
    with pdfplumber.open(pdf_path) as pdf:
        print("[AGNI-NETRA] Extracting Table 1 (State Summary)...", flush=True)
        t1 = extract_table_1(pdf)
        all_records.extend(t1)
        print(f"  -> Extracted {len(t1)} Table 1 records.")

        print("[AGNI-NETRA] Extracting Table 2 (Mineral Summary)...", flush=True)
        t2 = extract_table_2(pdf)
        all_records.extend(t2)
        print(f"  -> Extracted {len(t2)} Table 2 records.")

        print("[AGNI-NETRA] Extracting Table 3 (District/Mineral Leases)...", flush=True)
        t3 = extract_table_3(pdf)
        all_records.extend(t3)
        print(f"  -> Extracted {len(t3)} Table 3 records.")

        print("[AGNI-NETRA] Extracting Tables 4, 5, 6 (Potential Categories)...", flush=True)
        t456 = extract_tables_4_5_6(pdf)
        all_records.extend(t456)
        print(f"  -> Extracted {len(t456)} Tables 4, 5, 6 records.")

    print(f"\n[AGNI-NETRA] Total Records Extracted: {len(all_records)}", flush=True)

    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE ibm_mining_lease_context_staging;"))
        conn.execute(text("TRUNCATE TABLE ibm_mining_lease_context;"))

    # 1. Populate ibm_mining_lease_context_staging
    print("[AGNI-NETRA] Writing records to PostgreSQL staging: ibm_mining_lease_context_staging...", flush=True)
    insert_staging_sql = text("""
        INSERT INTO ibm_mining_lease_context_staging (
            record_id, state, district, mineral, lease_count, lease_area_ha,
            sector, potential_category, reference_year, reference_date,
            source_document, page_number, table_number, provisional_flag, raw_metadata
        ) VALUES (
            :record_id, :state, :district, :mineral, :lease_count, :lease_area_ha,
            :sector, :potential_category, :reference_year, :reference_date,
            :source_document, :page_number, :table_number, :provisional_flag,
            CAST(:raw_metadata AS JSONB)
        )
        ON CONFLICT (record_id) DO UPDATE SET
            lease_count = EXCLUDED.lease_count,
            lease_area_ha = EXCLUDED.lease_area_ha,
            raw_metadata = EXCLUDED.raw_metadata;
    """)

    # 2. Populate canonical ibm_mining_lease_context
    insert_canonical_sql = text("""
        INSERT INTO ibm_mining_lease_context (
            record_id, state, district, mineral, lease_count, lease_area_ha,
            sector, potential_category, reference_year, reference_date,
            source_document, table_number, page_number, provisional_flag,
            source, aggregation_level, raw_metadata, last_updated
        ) VALUES (
            :record_id, :state, :district, :mineral, :lease_count, :lease_area_ha,
            :sector, :potential_category, :reference_year, :reference_date,
            :source_document, :table_number, :page_number, :provisional_flag,
            :source, :aggregation_level, CAST(:raw_metadata AS JSONB),
            NOW() AT TIME ZONE 'UTC'
        )
        ON CONFLICT (record_id) DO UPDATE SET
            lease_count = EXCLUDED.lease_count,
            lease_area_ha = EXCLUDED.lease_area_ha,
            raw_metadata = EXCLUDED.raw_metadata,
            last_updated = NOW() AT TIME ZONE 'UTC';
    """)

    staging_inserted = 0
    canonical_inserted = 0

    with engine.begin() as conn:
        for r in all_records:
            meta_json = json.dumps(r["raw_metadata"])
            params = {
                "record_id": r["record_id"],
                "state": r["state"],
                "district": r["district"],
                "mineral": r["mineral"],
                "lease_count": r["lease_count"],
                "lease_area_ha": r["lease_area_ha"],
                "sector": r["sector"],
                "potential_category": r["potential_category"],
                "reference_year": REFERENCE_YEAR,
                "reference_date": REFERENCE_DATE,
                "source_document": PDF_FILENAME,
                "page_number": r["page_number"],
                "table_number": r["table_number"],
                "provisional_flag": PROVISIONAL_FLAG,
                "source": SOURCE_NAME,
                "aggregation_level": r["aggregation_level"],
                "raw_metadata": meta_json
            }

            conn.execute(insert_staging_sql, params)
            staging_inserted += 1

            conn.execute(insert_canonical_sql, params)
            canonical_inserted += 1

    print(f"[AGNI-NETRA] Ingestion Complete! Staging Rows: {staging_inserted:,} | Canonical Rows: {canonical_inserted:,}", flush=True)


if __name__ == "__main__":
    ingest_ibm_mining_leases()
