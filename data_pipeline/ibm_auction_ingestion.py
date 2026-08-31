"""
AGNI-NETRA — Ingestion & Entity Resolution Pipeline for IBM Table 15 Auctioned Mineral Blocks
Extracts 119 successful auctions from IBM Mining Lease Bulletin 2024 (Table 15),
resolves entities against canonical facilities, inherits OSM geometry, and computes FIRMS thermal telemetry.
"""

import sys
import os
import json
import pdfplumber
import re
from difflib import SequenceMatcher
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy import text

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend.app.core.database import engine

PDF_PATH = r"E:\PROJECTS\AGNI-NETRA(DATABASE)\FACILITIES\IBM\1763377395691b00f36d15cML_PL_2024.pdf"
SOURCE_DOC = "1763377395691b00f36d15cML_PL_2024.pdf"

STATE_MAP = {
    "maharash tra": "Maharashtra",
    "maharashtra": "Maharashtra",
    "chhattisg arh": "Chhattisgarh",
    "chhattisgarh": "Chhattisgarh",
    "andhra pradesh": "Andhra Pradesh",
    "arunachal pradesh": "Arunachal Pradesh",
    "assam": "Assam",
    "bihar": "Bihar",
    "goa": "Goa",
    "gujarat": "Gujarat",
    "karnataka": "Karnataka",
    "madhya pradesh": "Madhya Pradesh",
    "odisha": "Odisha",
    "rajasthan": "Rajasthan",
    "uttar pradesh": "Uttar Pradesh",
    "jharkhan d": "Jharkhand",
    "jharkhand": "Jharkhand",
    "tamil nadu": "Tamil Nadu",
    "telangana": "Telangana"
}

STOP_WORDS = {
    "block", "mine", "mines", "mining", "iron", "ore", "limestone", "bauxite", "manganese",
    "gold", "diamond", "graphite", "laterite", "cl", "n/v", "mineral", "minerals", "area",
    "north", "south", "east", "west", "extension", "part-a", "part-b", "part", "marl",
    "siliceous", "earth", "phosphorite", "composite", "licence", "pl", "rf", "ltd", "pvt",
    "limited", "private", "and", "the", "of", "in", "sector", "village", "taluk", "tehsil",
    "district", "state", "tksb", "tkb", "nb10", "nb", "gov", "govt"
}


def normalize_state(st: Optional[str]) -> str:
    if not st:
        return "National Territory"
    clean = st.replace("\n", " ").strip().lower()
    return STATE_MAP.get(clean, clean.title())


def clean_tokens(name: str) -> List[str]:
    tokens = re.findall(r'[a-zA-Z0-9]+', name.lower())
    return [t for t in tokens if t not in STOP_WORDS and len(t) >= 4]


def extract_table_15_records() -> List[Dict[str, Any]]:
    print(f"[EXTRACT] Reading Table 15 from {PDF_PATH}...", flush=True)
    raw_rows = []
    with pdfplumber.open(PDF_PATH) as pdf:
        for page_num in range(53, 58):  # pages 53 to 57
            page = pdf.pages[page_num - 1]
            tables = page.extract_tables()
            for table in tables:
                for r in table:
                    raw_rows.append((page_num, r))

    records = []
    for p_num, r in raw_rows:
        if not r or len(r) < 5:
            continue
        sl_str = str(r[0]).strip() if r[0] else ""
        if not sl_str.isdigit():
            continue

        sl_no = int(sl_str)
        state_raw = str(r[1]).replace("\n", " ").strip() if r[1] else ""
        block_name = str(r[2]).replace("\n", " ").strip() if r[2] else ""
        mineral = str(r[3]).replace("\n", " ").strip() if r[3] else ""
        bidder = str(r[4]).replace("\n", " ").strip() if r[4] else ""

        records.append({
            "sl_no": sl_no,
            "state_raw": state_raw,
            "state": normalize_state(state_raw),
            "block_name": block_name,
            "mineral": mineral,
            "preferred_bidder": bidder,
            "source_document": SOURCE_DOC,
            "page_number": p_num,
            "table_number": "Table 15",
            "auction_financial_year": "2024-25",
            "provisional_status": True
        })

    records.sort(key=lambda x: x["sl_no"])
    print(f"  -> Successfully extracted {len(records)} Table 15 records (SL NO {records[0]['sl_no']} to {records[-1]['sl_no']}).", flush=True)
    return records


def score_entity_match(block: Dict[str, Any], fac: Dict[str, Any]) -> Tuple[float, str]:
    """
    Computes match score between an auctioned block and a candidate industrial/mining facility.
    """
    block_name = block["block_name"]
    fac_name = fac["name"] or ""
    
    b_tokens = set(clean_tokens(block_name))
    f_tokens = set(clean_tokens(fac_name))

    if not b_tokens or not f_tokens:
        return 0.0, "NO_DISTINCT_TOKENS"

    intersection = b_tokens.intersection(f_tokens)
    if not intersection:
        return 0.0, "NO_COMMON_TOKENS"

    # State compatibility check
    b_st = (block.get("state") or "").strip().lower()
    f_st = (fac.get("state") or "").strip().lower()
    same_state = (b_st == f_st) or (f_st in ["national / unspecified", "national territory"])

    if not same_state:
        return 0.0, "STATE_MISMATCH"

    # Exact token overlap ratio
    token_score = len(intersection) / len(b_tokens)
    seq_score = SequenceMatcher(None, block_name.lower(), fac_name.lower()).ratio()

    # Operator / Bidder bonus
    bidder = (block.get("preferred_bidder") or "").lower()
    operator = (fac.get("operator") or "").lower()
    bidder_score = 0.0
    if bidder and operator:
        bidder_tokens = set(clean_tokens(bidder))
        operator_tokens = set(clean_tokens(operator))
        if bidder_tokens.intersection(operator_tokens):
            bidder_score = 0.25

    combined_score = (token_score * 0.5) + (seq_score * 0.3) + bidder_score
    if b_st == f_st and b_st not in ["national / unspecified", "national territory"]:
        combined_score += 0.20

    method = f"DISTINCT_TOKEN({','.join(intersection)})"
    return min(combined_score, 1.0), method


def run_ibm_auction_ingestion():
    print("=" * 90, flush=True)
    print("       AGNI-NETRA — IBM TABLE 15 AUCTIONED MINERAL BLOCKS INGESTION       ", flush=True)
    print("=" * 90, flush=True)

    # Step 1: Extract records
    records = extract_table_15_records()
    assert len(records) == 119, f"Expected exactly 119 records, got {len(records)}"

    print("\n[STEP 2: LOADING CANDIDATE MINING & INDUSTRIAL FACILITIES]...", flush=True)
    with engine.connect() as conn:
        fac_rows = conn.execute(text("""
            SELECT f.id, f.facility_name as name, f.facility_type, f.state, f.district,
                   f.operator, f.latitude, f.longitude, ST_AsText(f.geom) as geom_wkt
            FROM (
                SELECT e.facility_id as id, e.facility_name, e.facility_type, e.state, e.district,
                       e.operator, e.latitude, e.longitude, i.geom
                FROM facility_mining_evidence e
                JOIN industrial_facilities i ON e.facility_id = i.id
                UNION ALL
                SELECT id, name as facility_name, facility_type, state, district,
                       COALESCE(source_metadata->>'operator', company_name) as operator,
                       latitude, longitude, geom
                FROM industrial_facilities
                WHERE name IS NOT NULL
            ) f;
        """)).fetchall()

    facilities_by_state: Dict[str, List[Dict[str, Any]]] = {}
    for r in fac_rows:
        st_key = (r[3] or "").strip().lower()
        if st_key not in facilities_by_state:
            facilities_by_state[st_key] = []
        facilities_by_state[st_key].append({
            "id": r[0],
            "name": r[1],
            "facility_type": r[2],
            "state": r[3],
            "district": r[4],
            "operator": r[5],
            "lat": r[6],
            "lon": r[7],
            "geom_wkt": r[8]
        })

    print(f"  -> Indexed {len(fac_rows):,} candidate facilities across {len(facilities_by_state)} states.", flush=True)

    # Step 3: Clear staging and canonical tables
    print("\n[STEP 3: TRUNCATING STAGING & CANONICAL TABLES]...", flush=True)
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE ibm_auctioned_blocks_staging CASCADE;"))
        conn.execute(text("TRUNCATE TABLE ibm_auctioned_blocks CASCADE;"))

    # Step 4: Insert Staging Records
    print("\n[STEP 4: INSERTING STAGING RECORDS]...", flush=True)
    insert_staging_sql = text("""
        INSERT INTO ibm_auctioned_blocks_staging (
            sl_no, state, block_name, mineral, preferred_bidder,
            auction_financial_year, source_document, page_number,
            table_number, provisional_status, raw_metadata
        ) VALUES (
            :sl_no, :state, :block_name, :mineral, :preferred_bidder,
            :auction_financial_year, :source_document, :page_number,
            :table_number, :provisional_status, CAST(:raw_metadata AS jsonb)
        );
    """)

    with engine.begin() as conn:
        for r in records:
            conn.execute(insert_staging_sql, {
                "sl_no": r["sl_no"],
                "state": r["state"],
                "block_name": r["block_name"],
                "mineral": r["mineral"],
                "preferred_bidder": r["preferred_bidder"],
                "auction_financial_year": r["auction_financial_year"],
                "source_document": r["source_document"],
                "page_number": r["page_number"],
                "table_number": r["table_number"],
                "provisional_status": r["provisional_status"],
                "raw_metadata": json.dumps(r)
            })

    print("  -> Inserted 119 records into ibm_auctioned_blocks_staging.", flush=True)

    # Step 5: Entity Resolution & Canonical Population
    print("\n[STEP 5: RESOLVING ENTITIES & INHERITING GEOMETRY]...", flush=True)
    canonical_records = []
    match_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0, "UNMATCHED": 0}

    for r in records:
        sl_no = r["sl_no"]
        doc_id = f"IBM-2024-T15-{sl_no:03d}"
        state_key = r["state"].lower()

        # Gather candidates for the state plus national fallback
        candidates = facilities_by_state.get(state_key, []) + facilities_by_state.get("national / unspecified", []) + facilities_by_state.get("national territory", [])
        best_match = None
        best_score = 0.0
        best_method = "UNMATCHED"

        for fac in candidates:
            score, method = score_entity_match(r, fac)
            if score > best_score:
                best_score = score
                best_match = fac
                best_method = method

        # Classify match confidence
        if best_score >= 0.80 and best_match:
            conf = "HIGH"
            matched_id = best_match["id"]
            district = best_match["district"]
            geom_wkt = best_match["geom_wkt"]
            lat = best_match["lat"]
            lon = best_match["lon"]
        elif best_score >= 0.60 and best_match:
            conf = "MEDIUM"
            matched_id = best_match["id"]
            district = best_match["district"]
            geom_wkt = best_match["geom_wkt"]
            lat = best_match["lat"]
            lon = best_match["lon"]
        elif best_score >= 0.45 and best_match:
            conf = "LOW"
            matched_id = best_match["id"]
            district = None  # Do not inherit district on weak match
            geom_wkt = None  # Do not inherit geometry on weak match
            lat = None
            lon = None
        else:
            conf = "UNMATCHED"
            matched_id = None
            district = None
            geom_wkt = None
            lat = None
            lon = None

        match_counts[conf] += 1

        # FIRMS spatial association if geometry is present
        f_500m, f_1km, f_2km = 0, 0, 0
        if geom_wkt and lat is not None and lon is not None:
            with engine.connect() as conn:
                deg_buf = 0.022
                th_query = text("""
                    SELECT 
                        COUNT(CASE WHEN ST_DWithin(ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)::geography, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, 500) THEN 1 END),
                        COUNT(CASE WHEN ST_DWithin(ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)::geography, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, 1000) THEN 1 END),
                        COUNT(CASE WHEN ST_DWithin(ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)::geography, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, 2000) THEN 1 END)
                    FROM thermal_detections
                    WHERE latitude BETWEEN :min_lat AND :max_lat
                      AND longitude BETWEEN :min_lon AND :max_lon;
                """)
                res = conn.execute(th_query, {
                    "lon": lon, "lat": lat,
                    "min_lat": lat - deg_buf, "max_lat": lat + deg_buf,
                    "min_lon": lon - deg_buf, "max_lon": lon + deg_buf
                }).fetchone()
                if res:
                    f_500m, f_1km, f_2km = res[0] or 0, res[1] or 0, res[2] or 0

        raw_meta = {
            "sl_no": sl_no,
            "block_name": r["block_name"],
            "state_source": r["state_raw"],
            "mineral": r["mineral"],
            "preferred_bidder": r["preferred_bidder"],
            "match_confidence": conf,
            "match_score": round(best_score, 4),
            "match_method": best_method,
            "matched_facility_name": best_match["name"] if best_match else None,
            "geometry_source": "OSM_MATCHED" if geom_wkt else "NULL_NO_MATCH"
        }

        canonical_records.append({
            "source_doc_id": doc_id,
            "sl_no": sl_no,
            "block_name": r["block_name"],
            "state": r["state"],
            "district": district,
            "mineral": r["mineral"],
            "preferred_bidder": r["preferred_bidder"],
            "auction_financial_year": "2024-25",
            "matched_facility_id": matched_id,
            "match_confidence": conf,
            "match_score": round(best_score, 4) if best_score > 0 else None,
            "match_method": best_method if best_score > 0 else "UNMATCHED",
            "geom_wkt": geom_wkt,
            "firms_count_500m": f_500m,
            "firms_count_1km": f_1km,
            "firms_count_2km": f_2km,
            "source": "IBM",
            "source_document": r["source_document"],
            "page_number": r["page_number"],
            "table_number": "Table 15",
            "is_provisional": True,
            "raw_metadata": json.dumps(raw_meta)
        })

    # Step 6: Insert into ibm_auctioned_blocks
    print("\n[STEP 6: INSERTING CANONICAL AUCTIONED BLOCKS]...", flush=True)
    insert_canonical_sql = text("""
        INSERT INTO ibm_auctioned_blocks (
            source_doc_id, sl_no, block_name, state, district,
            mineral, preferred_bidder, auction_financial_year,
            matched_facility_id, match_confidence, match_score,
            match_method, geom, firms_count_500m, firms_count_1km,
            firms_count_2km, source, source_document, page_number,
            table_number, is_provisional, raw_metadata
        ) VALUES (
            :source_doc_id, :sl_no, :block_name, :state, :district,
            :mineral, :preferred_bidder, :auction_financial_year,
            :matched_facility_id, :match_confidence, :match_score,
            :match_method,
            CASE WHEN :geom_wkt IS NOT NULL THEN ST_GeomFromText(:geom_wkt, 4326) ELSE NULL END,
            :firms_count_500m, :firms_count_1km, :firms_count_2km,
            :source, :source_document, :page_number, :table_number,
            :is_provisional, CAST(:raw_metadata AS jsonb)
        );
    """)

    with engine.begin() as conn:
        for c in canonical_records:
            conn.execute(insert_canonical_sql, c)

    with_geom = sum(1 for c in canonical_records if c["geom_wkt"] is not None)
    without_geom = sum(1 for c in canonical_records if c["geom_wkt"] is None)

    print("\n" + "=" * 90, flush=True)
    print("        AGNI-NETRA — TABLE 15 AUCTIONED BLOCKS INGESTION COMPLETE         ", flush=True)
    print("=" * 90, flush=True)
    print(f"  • Total Extracted Rows   : {len(records)}", flush=True)
    print(f"  • Total Inserted Rows    : {len(canonical_records)}", flush=True)
    print(f"  • HIGH Matches           : {match_counts['HIGH']}", flush=True)
    print(f"  • MEDIUM Matches         : {match_counts['MEDIUM']}", flush=True)
    print(f"  • LOW Matches            : {match_counts['LOW']}", flush=True)
    print(f"  • UNMATCHED              : {match_counts['UNMATCHED']}", flush=True)
    print(f"  • Sum Matches Evaluated  : {sum(match_counts.values())} (Expected: 119)", flush=True)
    print(f"  • Records with Geometry  : {with_geom}", flush=True)
    print(f"  • Records without Geometry: {without_geom}", flush=True)
    print("=" * 90, flush=True)


if __name__ == "__main__":
    run_ibm_auction_ingestion()
