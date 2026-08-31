"""
AGNI-NETRA — IBM National Mineral Inventory (NMI) 2020 Ingestion Pipeline
Extracts national mineral reserves and remaining resource statistics from Chapter 6 (Table 6)
into PostgreSQL staging (ibm_nmi_staging) and canonical context (ibm_mineral_resources).
"""

import sys
import os
import re
import hashlib
from typing import List, Dict, Any, Optional
import pdfplumber
from sqlalchemy import text

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend.app.core.database import engine

DEFAULT_DATA_DIR = r"E:\PROJECTS\AGNI-NETRA(DATABASE)\FACILITIES\IBM"
FALLBACK_DATA_DIR = r"E:\AGNI-NETRA-DATA\FACILITIES\IBM"
PDF_FILENAME = "11122022113003Res_All India Summary_2020.pdf"


def get_pdf_path() -> str:
    if os.path.exists(os.path.join(DEFAULT_DATA_DIR, PDF_FILENAME)):
        return os.path.join(DEFAULT_DATA_DIR, PDF_FILENAME)
    elif os.path.exists(os.path.join(FALLBACK_DATA_DIR, PDF_FILENAME)):
        return os.path.join(FALLBACK_DATA_DIR, PDF_FILENAME)
    raise FileNotFoundError(f"IBM NMI 2020 PDF not found in {DEFAULT_DATA_DIR} or {FALLBACK_DATA_DIR}")


def parse_number(val: Any) -> Optional[float]:
    if val is None:
        return None
    val_str = str(val).strip().replace(',', '').replace(' ', '')
    if val_str in ('', 'N.E.', '--', 'N.A.', '-'):
        return None
    try:
        return float(val_str)
    except ValueError:
        return None


def clean_text(val: Any) -> str:
    if not val:
        return ''
    return ' '.join(str(val).split())


def generate_record_id(commodity: str, mineral: str, unit: Optional[str]) -> str:
    key_str = f"IBM_NMI_2020_{clean_text(commodity).upper()}_{clean_text(mineral).upper()}_{clean_text(unit or 'NONE').upper()}"
    return hashlib.sha256(key_str.encode('utf-8')).hexdigest()[:32]


def clean_mineral_name(base_commodity: str, sub_name: Optional[str]) -> str:
    if not sub_name or sub_name == base_commodity:
        if "PGM" in base_commodity:
            return "Platinum Group of Metals (PGM)"
        return base_commodity
    
    # Sub-name normalization
    sub = clean_text(sub_name)
    if "Contained MoS" in sub:
        sub = "Contained MoS2"
    elif "Contained VO" in sub:
        sub = "Contained V2O5"
    elif "Ore(Primary)" in sub or "Ore (Primary)" in sub:
        sub = "Ore (Primary)"
    elif "Metal(Primary)" in sub or "Metal (Primary)" in sub:
        sub = "Metal (Primary)"
    elif "(PGM)" in sub:
        sub = "Contained Metal"
    
    return f"{base_commodity} ({sub})"


def clean_unit_name(unit_str: Optional[str]) -> Optional[str]:
    if not unit_str:
        return None
    u = clean_text(unit_str)
    if u in ('--', 'N.E.', 'None', ''):
        return None
    if 'Contained' in u and 'Metal' in u:
        return "Tonnes of Metal Contained"
    if u == "000Tonne" or u == "000 Tonnes" or u == "1000 Tonnes":
        return "'000 Tonnes"
    return u


def extract_table_6_nmi(pdf_path: str) -> List[Dict[str, Any]]:
    """
    Extracts Table 6: Reserves/Resources as on 1.04.2020 (P): All India Summary
    from NMI At a Glance - 2020(P), Chapter No. 6.
    """
    records = []
    with pdfplumber.open(pdf_path) as pdf:
        for p_idx, page in enumerate(pdf.pages):
            page_num = 89 + p_idx  # Published page numbers are 89 and 90
            tables = page.extract_tables()
            if not tables:
                continue
            table = tables[0]
            
            curr_sl_no = None
            curr_commodity = None
            
            i = 1  # Skip header row
            while i < len(table):
                row = table[i]
                sl_col = row[0]
                min_col = row[1]
                unit_col = row[2]
                res_col = row[3]
                rem_col = row[4]
                tot_col = row[5]

                if sl_col and sl_col.strip().isdigit():
                    curr_sl_no = int(sl_col.strip())
                    min_lines = [l.strip() for l in (min_col or '').split('\n') if l.strip()]
                    unit_lines = [l.strip() for l in (unit_col or '').split('\n') if l.strip()]
                    res_lines = [l.strip() for l in (res_col or '').split('\n') if l.strip()]
                    rem_lines = [l.strip() for l in (rem_col or '').split('\n') if l.strip()]
                    tot_lines = [l.strip() for l in (tot_col or '').split('\n') if l.strip()]
                    
                    curr_commodity = min_lines[0] if min_lines else ''

                    # Subcase 1: Multi-line in single cell with inline values (e.g. Antimony)
                    if len(min_lines) > 1 and len(res_lines) > 0 and len(min_lines) == len(res_lines) + 1:
                        for sub_idx in range(len(res_lines)):
                            sub_type = min_lines[sub_idx + 1]
                            mineral_title = clean_mineral_name(curr_commodity, sub_type)
                            u = unit_lines[sub_idx] if sub_idx < len(unit_lines) else (unit_lines[0] if unit_lines else None)
                            unit_clean = clean_unit_name(u)
                            res = parse_number(res_lines[sub_idx])
                            rem = parse_number(rem_lines[sub_idx])
                            tot = parse_number(tot_lines[sub_idx])
                            is_ne = (res is None and rem is None and tot is None)
                            rec_id = generate_record_id(curr_commodity, mineral_title, unit_clean)
                            records.append({
                                "record_id": rec_id,
                                "sl_no": curr_sl_no,
                                "commodity": curr_commodity,
                                "mineral": mineral_title,
                                "unit": unit_clean,
                                "reserves": res,
                                "remaining_resources": rem,
                                "total_resources": tot,
                                "not_estimated": is_ne,
                                "page_number": page_num,
                                "table_number": "Table 6",
                                "reference_year": 2020,
                                "reference_date": "2020-04-01",
                                "source_document": PDF_FILENAME,
                                "provisional_flag": True,
                                "raw_metadata": {
                                    "table_title": "Table 6: Reserves/Resources as on 1.04.2020 (P): All India Summary",
                                    "chapter": "Chapter No. 6",
                                    "raw_sub_type": sub_type,
                                    "raw_row": row
                                }
                            })
                        i += 1
                        continue

                    # Subcase 2: Multi-line in single cell with values in subsequent rows (e.g. Copper)
                    elif len(min_lines) > 1 and len(res_lines) == 0:
                        for sub_idx in range(1, len(min_lines)):
                            sub_type = min_lines[sub_idx]
                            mineral_title = clean_mineral_name(curr_commodity, sub_type)
                            u = unit_lines[sub_idx-1] if sub_idx-1 < len(unit_lines) else (unit_lines[0] if unit_lines else None)
                            unit_clean = clean_unit_name(u)
                            i += 1
                            val_row = table[i]
                            res = parse_number(val_row[3])
                            rem = parse_number(val_row[4])
                            tot = parse_number(val_row[5])
                            is_ne = (res is None and rem is None and tot is None)
                            rec_id = generate_record_id(curr_commodity, mineral_title, unit_clean)
                            records.append({
                                "record_id": rec_id,
                                "sl_no": curr_sl_no,
                                "commodity": curr_commodity,
                                "mineral": mineral_title,
                                "unit": unit_clean,
                                "reserves": res,
                                "remaining_resources": rem,
                                "total_resources": tot,
                                "not_estimated": is_ne,
                                "page_number": page_num,
                                "table_number": "Table 6",
                                "reference_year": 2020,
                                "reference_date": "2020-04-01",
                                "source_document": PDF_FILENAME,
                                "provisional_flag": True,
                                "raw_metadata": {
                                    "table_title": "Table 6: Reserves/Resources as on 1.04.2020 (P): All India Summary",
                                    "chapter": "Chapter No. 6",
                                    "raw_sub_type": sub_type,
                                    "raw_row": val_row
                                }
                            })
                        i += 1
                        continue

                    # Subcase 3: Commodity header with empty values, followed by sub-rows (e.g. Gold, Lead-Zinc, Silver, Tin, Tungsten, Vanadium)
                    elif len(min_lines) == 1 and (res_col is None or res_col.strip() == ''):
                        i += 1
                        while i < len(table) and (table[i][0] is None or table[i][0].strip() == ''):
                            sub_row = table[i]
                            sub_min_name = clean_text(sub_row[1])
                            mineral_title = clean_mineral_name(curr_commodity, sub_min_name)
                            unit_clean = clean_unit_name(sub_row[2])
                            res = parse_number(sub_row[3])
                            rem = parse_number(sub_row[4])
                            tot = parse_number(sub_row[5])
                            is_ne = (res is None and rem is None and tot is None)
                            rec_id = generate_record_id(curr_commodity, mineral_title, unit_clean)
                            records.append({
                                "record_id": rec_id,
                                "sl_no": curr_sl_no,
                                "commodity": curr_commodity,
                                "mineral": mineral_title,
                                "unit": unit_clean,
                                "reserves": res,
                                "remaining_resources": rem,
                                "total_resources": tot,
                                "not_estimated": is_ne,
                                "page_number": page_num,
                                "table_number": "Table 6",
                                "reference_year": 2020,
                                "reference_date": "2020-04-01",
                                "source_document": PDF_FILENAME,
                                "provisional_flag": True,
                                "raw_metadata": {
                                    "table_title": "Table 6: Reserves/Resources as on 1.04.2020 (P): All India Summary",
                                    "chapter": "Chapter No. 6",
                                    "raw_sub_type": sub_min_name,
                                    "raw_row": sub_row
                                }
                            })
                            i += 1
                        continue

                    # Subcase 4: Single line commodity row (e.g. Andalusite, Bauxite, Limestone, Marl, etc.)
                    else:
                        base_min = clean_text(min_col)
                        mineral_title = clean_mineral_name(base_min, None)
                        unit_clean = clean_unit_name(unit_col)
                        res = parse_number(res_col)
                        rem = parse_number(rem_col)
                        tot = parse_number(tot_col)
                        is_ne = (res is None and rem is None and tot is None)
                        rec_id = generate_record_id(base_min, mineral_title, unit_clean)
                        records.append({
                            "record_id": rec_id,
                            "sl_no": curr_sl_no,
                            "commodity": base_min,
                            "mineral": mineral_title,
                            "unit": unit_clean,
                            "reserves": res,
                            "remaining_resources": rem,
                            "total_resources": tot,
                            "not_estimated": is_ne,
                            "page_number": page_num,
                            "table_number": "Table 6",
                            "reference_year": 2020,
                            "reference_date": "2020-04-01",
                            "source_document": PDF_FILENAME,
                            "provisional_flag": True,
                            "raw_metadata": {
                                "table_title": "Table 6: Reserves/Resources as on 1.04.2020 (P): All India Summary",
                                "chapter": "Chapter No. 6",
                                "raw_row": row
                            }
                        })
                        i += 1
                        continue
                else:
                    i += 1

    return records


def ingest_ibm_nmi():
    pdf_path = get_pdf_path()
    print(f"[AGNI-NETRA] Opening IBM NMI 2020 PDF: {pdf_path}", flush=True)
    
    records = extract_table_6_nmi(pdf_path)
    print(f"[AGNI-NETRA] Extracted {len(records)} NMI mineral resource records across {len(set(r['commodity'] for r in records))} distinct commodities.", flush=True)

    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE ibm_nmi_staging;"))
        conn.execute(text("TRUNCATE TABLE ibm_mineral_resources;"))

    # 1. Populate ibm_nmi_staging
    print("[AGNI-NETRA] Writing records to PostgreSQL staging: ibm_nmi_staging...", flush=True)
    insert_staging_sql = text("""
        INSERT INTO ibm_nmi_staging (
            record_id, sl_no, commodity, mineral, unit,
            reserves, remaining_resources, total_resources, not_estimated,
            reference_year, reference_date, source_document, page_number,
            table_number, provisional_flag, raw_metadata
        ) VALUES (
            :record_id, :sl_no, :commodity, :mineral, :unit,
            :reserves, :remaining_resources, :total_resources, :not_estimated,
            :reference_year, :reference_date, :source_document, :page_number,
            :table_number, :provisional_flag, CAST(:raw_metadata AS jsonb)
        )
        ON CONFLICT (record_id) DO UPDATE SET
            reserves = EXCLUDED.reserves,
            remaining_resources = EXCLUDED.remaining_resources,
            total_resources = EXCLUDED.total_resources,
            not_estimated = EXCLUDED.not_estimated,
            raw_metadata = EXCLUDED.raw_metadata;
    """)

    import json
    with engine.begin() as conn:
        for r in records:
            conn.execute(insert_staging_sql, {
                "record_id": r["record_id"],
                "sl_no": r["sl_no"],
                "commodity": r["commodity"],
                "mineral": r["mineral"],
                "unit": r["unit"],
                "reserves": r["reserves"],
                "remaining_resources": r["remaining_resources"],
                "total_resources": r["total_resources"],
                "not_estimated": r["not_estimated"],
                "reference_year": r["reference_year"],
                "reference_date": r["reference_date"],
                "source_document": r["source_document"],
                "page_number": r["page_number"],
                "table_number": r["table_number"],
                "provisional_flag": r["provisional_flag"],
                "raw_metadata": json.dumps(r["raw_metadata"])
            })

    # 2. Populate canonical ibm_mineral_resources
    print("[AGNI-NETRA] Ingesting to canonical table: ibm_mineral_resources...", flush=True)
    insert_canonical_sql = text("""
        INSERT INTO ibm_mineral_resources (
            record_id, sl_no, commodity, mineral, unit,
            reserves, remaining_resources, total_resources, not_estimated,
            reference_year, reference_date, source, source_document,
            page_number, table_number, provisional_flag, raw_metadata
        )
        SELECT
            record_id, sl_no, commodity, mineral, unit,
            reserves, remaining_resources, total_resources, not_estimated,
            reference_year, reference_date, 'IBM', source_document,
            page_number, table_number, provisional_flag, raw_metadata
        FROM ibm_nmi_staging
        ON CONFLICT (record_id) DO UPDATE SET
            reserves = EXCLUDED.reserves,
            remaining_resources = EXCLUDED.remaining_resources,
            total_resources = EXCLUDED.total_resources,
            not_estimated = EXCLUDED.not_estimated,
            raw_metadata = EXCLUDED.raw_metadata,
            last_updated = NOW() AT TIME ZONE 'UTC';
    """)

    with engine.begin() as conn:
        conn.execute(insert_canonical_sql)

    with engine.connect() as conn:
        staging_cnt = conn.execute(text("SELECT count(*) FROM ibm_nmi_staging;")).scalar()
        canon_cnt = conn.execute(text("SELECT count(*) FROM ibm_mineral_resources;")).scalar()

    print(f"[AGNI-NETRA] NMI Ingestion Complete! Staging Rows: {staging_cnt} | Canonical Rows: {canon_cnt}", flush=True)


if __name__ == "__main__":
    ingest_ibm_nmi()
