"""
AGNI-NETRA — National Administrative Boundaries Ingestion Pipeline (Phase 2A)
High-performance ingestion of State/UT (ADM1: 36), District (ADM2: 735), and Sub-District (ADM3: 6,824)
boundaries into PostGIS admin_boundaries table with STRtree spatial hierarchy resolution.
"""

import sys
import os
import json
import unicodedata
import shapely.geometry
from shapely.strtree import STRtree
from typing import Dict, Any, List, Optional
from sqlalchemy import text

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend.app.core.database import engine

ADMIN_DIR = r"E:\PROJECTS\AGNI-NETRA(DATABASE)\ADMINISTRATIVE"

STATE_NORMALIZATIONS = {
    "andaman and nicobar": "Andaman and Nicobar Islands",
    "andaman and nicobar islands": "Andaman and Nicobar Islands",
    "jammu and kashmir": "Jammu and Kashmir",
    "the government of nct of delhi": "Delhi",
    "nct of delhi": "Delhi",
    "delhi": "Delhi",
    "dadra and nagar haveli and daman and diu": "Dadra and Nagar Haveli and Daman and Diu",
    "orissa": "Odisha",
    "uttaranchal": "Uttarakhand",
    "pondicherry": "Puducherry"
}


def normalize_admin_name(name: Optional[str]) -> str:
    if not name:
        return "UNKNOWN"
    nfkd = unicodedata.normalize('NFKD', name)
    ascii_name = nfkd.encode('ASCII', 'ignore').decode('utf-8').strip()
    clean = " ".join(ascii_name.split())
    clean_lower = clean.lower()
    if clean_lower in STATE_NORMALIZATIONS:
        return STATE_NORMALIZATIONS[clean_lower]
    return clean


def run_admin_boundaries_ingestion():
    print("=" * 95, flush=True)
    print("       AGNI-NETRA — CANONICAL NATIONAL ADMINISTRATIVE BOUNDARIES INGESTION       ", flush=True)
    print("=" * 95, flush=True)

    # 1. Truncate table
    print("\n[STEP 1: TRUNCATING ADMIN_BOUNDARIES TABLE]...", flush=True)
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE admin_boundaries CASCADE;"))

    # 2. Load ADM1 (States/UTs)
    print("\n[STEP 2: PREPARING LEVEL 1 — STATES & UNION TERRITORIES (ADM1)]...", flush=True)
    adm1_path = os.path.join(ADMIN_DIR, "geoBoundaries-IND-ADM1.geojson")
    with open(adm1_path, "r", encoding="utf-8") as f:
        adm1_data = json.load(f)

    adm1_features = adm1_data.get("features", [])
    adm1_shapes = []
    adm1_records = []
    for feat in adm1_features:
        props = feat.get("properties", {})
        raw_name = props.get("shapeName", "UNKNOWN")
        norm_name = normalize_admin_name(raw_name)
        shape_id = props.get("shapeID", f"ADM1_{norm_name}")
        geom_dict = feat.get("geometry")
        shp = shapely.geometry.shape(geom_dict)
        
        adm1_shapes.append(shp)
        adm1_records.append({
            "admin_level": 1,
            "admin_level_name": "STATE_UT",
            "admin_code": shape_id,
            "name": raw_name,
            "normalized_name": norm_name,
            "parent_code": "IND",
            "parent_name": "India",
            "state_code": props.get("shapeISO") or shape_id,
            "state_name": norm_name,
            "district_code": None,
            "district_name": None,
            "subdistrict_code": None,
            "geom_geojson": json.dumps(geom_dict),
            "source": "geoBoundaries / DataMeet India / Election Commission of India",
            "source_document": "geoBoundaries-IND-ADM1.geojson",
            "source_url": "https://www.geoboundaries.org/api/current/gbOpen/IND/ADM1/",
            "source_version": "2024",
            "crs": "EPSG:4326",
            "srid": 4326,
            "is_authoritative": True,
            "is_active": True,
            "raw_metadata": json.dumps(props)
        })

    adm1_tree = STRtree(adm1_shapes)
    print(f"  -> Prepared {len(adm1_records)} Level 1 features with STRtree index.", flush=True)

    # 3. Load ADM2 (Districts) and resolve parent state
    print("\n[STEP 3: PREPARING LEVEL 2 — DISTRICTS (ADM2) WITH PARENT STATE MAPPING]...", flush=True)
    adm2_path = os.path.join(ADMIN_DIR, "geoBoundaries-IND-ADM2.geojson")
    with open(adm2_path, "r", encoding="utf-8") as f:
        adm2_data = json.load(f)

    adm2_features = adm2_data.get("features", [])
    adm2_shapes = []
    adm2_records = []
    for feat in adm2_features:
        props = feat.get("properties", {})
        raw_name = props.get("shapeName", "UNKNOWN")
        norm_name = normalize_admin_name(raw_name)
        shape_id = props.get("shapeID", f"ADM2_{norm_name}")
        geom_dict = feat.get("geometry")
        shp = shapely.geometry.shape(geom_dict)
        
        # Resolve parent state via point-on-surface
        pt = shp.representative_point()
        candidate_idxs = adm1_tree.query(pt)
        parent_state = None
        for idx in candidate_idxs:
            if adm1_shapes[idx].contains(pt) or adm1_shapes[idx].intersects(pt):
                parent_state = adm1_records[idx]
                break
        if not parent_state and len(candidate_idxs) > 0:
            parent_state = adm1_records[candidate_idxs[0]]

        p_code = parent_state["admin_code"] if parent_state else "IND"
        p_name = parent_state["normalized_name"] if parent_state else "India"
        st_code = parent_state["state_code"] if parent_state else None
        st_name = parent_state["state_name"] if parent_state else None

        adm2_shapes.append(shp)
        adm2_records.append({
            "admin_level": 2,
            "admin_level_name": "DISTRICT",
            "admin_code": shape_id,
            "name": raw_name,
            "normalized_name": norm_name,
            "parent_code": p_code,
            "parent_name": p_name,
            "state_code": st_code,
            "state_name": st_name,
            "district_code": shape_id,
            "district_name": norm_name,
            "subdistrict_code": None,
            "geom_geojson": json.dumps(geom_dict),
            "source": "geoBoundaries / Local Government Directory (lgdirectory.gov.in)",
            "source_document": "geoBoundaries-IND-ADM2.geojson",
            "source_url": "https://www.geoboundaries.org/api/current/gbOpen/IND/ADM2/",
            "source_version": "2024",
            "crs": "EPSG:4326",
            "srid": 4326,
            "is_authoritative": True,
            "is_active": True,
            "raw_metadata": json.dumps(props)
        })

    adm2_tree = STRtree(adm2_shapes)
    print(f"  -> Prepared {len(adm2_records)} Level 2 features with parent State/UT mapping.", flush=True)

    # 4. Load ADM3 (Sub-Districts) and resolve parent district and state
    print("\n[STEP 4: PREPARING LEVEL 3 — SUB-DISTRICTS (ADM3) WITH PARENT HIERARCHY]...", flush=True)
    adm3_path = os.path.join(ADMIN_DIR, "geoBoundaries-IND-ADM3.geojson")
    with open(adm3_path, "r", encoding="utf-8") as f:
        adm3_data = json.load(f)

    adm3_features = adm3_data.get("features", [])
    adm3_records = []
    for i, feat in enumerate(adm3_features):
        props = feat.get("properties", {})
        raw_name = props.get("shapeName", "UNKNOWN")
        norm_name = normalize_admin_name(raw_name)
        shape_id = props.get("shapeID", f"ADM3_{i}")
        geom_dict = feat.get("geometry")
        shp = shapely.geometry.shape(geom_dict)

        pt = shp.representative_point()
        candidate_idxs = adm2_tree.query(pt)
        parent_dist = None
        for idx in candidate_idxs:
            if adm2_shapes[idx].contains(pt) or adm2_shapes[idx].intersects(pt):
                parent_dist = adm2_records[idx]
                break
        if not parent_dist and len(candidate_idxs) > 0:
            parent_dist = adm2_records[candidate_idxs[0]]

        p_code = parent_dist["admin_code"] if parent_dist else None
        p_name = parent_dist["normalized_name"] if parent_dist else None
        d_code = parent_dist["district_code"] if parent_dist else None
        d_name = parent_dist["district_name"] if parent_dist else None
        st_code = parent_dist["state_code"] if parent_dist else None
        st_name = parent_dist["state_name"] if parent_dist else None

        adm3_records.append({
            "admin_level": 3,
            "admin_level_name": "SUBDISTRICT",
            "admin_code": shape_id,
            "name": raw_name,
            "normalized_name": norm_name,
            "parent_code": p_code,
            "parent_name": p_name,
            "state_code": st_code,
            "state_name": st_name,
            "district_code": d_code,
            "district_name": d_name,
            "subdistrict_code": shape_id,
            "geom_geojson": json.dumps(geom_dict),
            "source": "geoBoundaries / Local Government Directory (lgdirectory.gov.in)",
            "source_document": "geoBoundaries-IND-ADM3.geojson",
            "source_url": "https://www.geoboundaries.org/api/current/gbOpen/IND/ADM3/",
            "source_version": "2024",
            "crs": "EPSG:4326",
            "srid": 4326,
            "is_authoritative": True,
            "is_active": True,
            "raw_metadata": json.dumps(props)
        })

    print(f"  -> Prepared {len(adm3_records)} Level 3 features with parent District/State hierarchy.", flush=True)

    # 5. Insert all into PostgreSQL
    print("\n[STEP 5: INSERTING CANONICAL ADMINISTRATIVE BOUNDARIES INTO POSTGIS]...", flush=True)
    insert_sql = text("""
        INSERT INTO admin_boundaries (
            admin_level, admin_level_name, admin_code, name, normalized_name,
            parent_code, parent_name, state_code, state_name,
            district_code, district_name, subdistrict_code, geom,
            source, source_document, source_url, source_version,
            crs, srid, is_authoritative, is_active, raw_metadata
        ) VALUES (
            :admin_level, :admin_level_name, :admin_code, :name, :normalized_name,
            :parent_code, :parent_name, :state_code, :state_name,
            :district_code, :district_name, :subdistrict_code,
            ST_SetSRID(ST_GeomFromGeoJSON(:geom_geojson), 4326),
            :source, :source_document, :source_url, :source_version,
            :crs, :srid, :is_authoritative, :is_active, CAST(:raw_metadata AS jsonb)
        );
    """)

    all_records = adm1_records + adm2_records + adm3_records
    batch_size = 200
    with engine.begin() as conn:
        for i in range(0, len(all_records), batch_size):
            batch = all_records[i:i + batch_size]
            conn.execute(insert_sql, batch)
            if (i + batch_size) % 1000 == 0 or (i + len(batch)) == len(all_records):
                print(f"    Inserted {min(i + len(batch), len(all_records)):,} / {len(all_records):,} boundary features...", flush=True)

    # 6. Post-Ingestion Quality Verification
    print("\n[STEP 6: POSTGIS GEOMETRY QUALITY & HIERARCHY VALIDATION]...", flush=True)
    with engine.connect() as conn:
        counts = conn.execute(text("""
            SELECT admin_level, admin_level_name, count(*),
                   SUM(CASE WHEN ST_IsValid(geom) THEN 1 ELSE 0 END) as valid_count,
                   SUM(CASE WHEN ST_IsEmpty(geom) THEN 1 ELSE 0 END) as empty_count,
                   SUM(CASE WHEN state_name IS NOT NULL THEN 1 ELSE 0 END) as with_state_count,
                   SUM(CASE WHEN admin_level >= 2 AND district_name IS NOT NULL THEN 1 ELSE 0 END) as with_district_count
            FROM admin_boundaries
            GROUP BY admin_level, admin_level_name
            ORDER BY admin_level;
        """)).fetchall()

        print("\n" + "=" * 95, flush=True)
        print("          ADMINISTRATIVE BOUNDARIES INGESTION & QUALITY REPORT          ", flush=True)
        print("=" * 95, flush=True)
        for r in counts:
            print(f"  • Level {r[0]} ({r[1]:<12}): Total = {r[2]:>5} | Valid = {r[3]:>5} | Empty = {r[4]} | State = {r[5]:>5} | District = {r[6]:>5}", flush=True)
        print("=" * 95, flush=True)


if __name__ == "__main__":
    run_admin_boundaries_ingestion()
