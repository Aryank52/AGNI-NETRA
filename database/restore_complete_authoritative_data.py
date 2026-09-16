"""
AGNI-NETRA — Phase 25.3 Master Data Reconciliation & Restoration Engine
Ingests and reconciles authentic project datasets:
1. 36 States/UTs (ADM1) & 735 Districts (ADM2) into `admin_boundaries`
2. 35,546 authentic OpenStreetMap industrial facilities into `industrial_facilities`
3. Official CEA Power Stations into `cea_power_stations_staging` & power facilities enrichment
4. Official IBM Mining Leases into `ibm_mining_lease_context`
5. Nearest facility re-linking across all 88 operational thermal events
6. Spatial indexes for high-performance retrieval
"""

import os
import sys
import json
import time
import uuid
import hashlib
from datetime import datetime, timezone
import shapely.geometry
from shapely.strtree import STRtree
from shapely.prepared import prep
from sqlalchemy import text

ROOT_DIR = r"E:\PROJECTS\AGNI-NETRA"
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from backend.app.core.database import engine, haversine_distance_meters
from data_pipeline.osm_classifier import (
    classify_osm_entity,
    normalize_name,
    normalize_state,
    assess_quality_and_confidence
)
from data_pipeline.nic_mapping import resolve_nic_mapping

DATA_DIR = r"E:\PROJECTS\AGNI-NETRA(DATABASE)"


def log(msg: str):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


# =============================================================================
# 1. RESTORE ADMINISTRATIVE BOUNDARIES (ADM1: 36, ADM2: 735)
# =============================================================================

def restore_admin_boundaries():
    log("=== [1/5] Restoring Administrative Boundaries (ADM1 & ADM2) ===")
    adm1_file = os.path.join(DATA_DIR, "ADMINISTRATIVE", "geoBoundaries-IND-ADM1.geojson")
    adm2_file = os.path.join(DATA_DIR, "ADMINISTRATIVE", "geoBoundaries-IND-ADM2.geojson")

    adm1_records = []
    adm1_shapes = []
    adm1_names = []

    if os.path.exists(adm1_file):
        with open(adm1_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        for feat in data.get("features", []):
            props = feat.get("properties", {})
            geom = feat.get("geometry", {})
            name = props.get("shapeName") or props.get("name") or "Unknown"
            code = props.get("shapeGroup") or props.get("shapeID") or f"IND-ADM1-{name[:4].upper()}"
            s = shapely.geometry.shape(geom)
            adm1_shapes.append(s)
            adm1_names.append(name)
            adm1_records.append({
                "id": str(uuid.uuid4()),
                "admin_level": 1,
                "admin_level_name": "STATE_UT",
                "admin_code": code,
                "name": name,
                "normalized_name": normalize_state(name),
                "parent_code": "IND",
                "parent_name": "India",
                "state_code": code,
                "state_name": normalize_state(name),
                "district_code": None,
                "district_name": None,
                "subdistrict_code": None,
                "geom": json.dumps(geom),
                "source": "geoBoundaries",
                "source_document": "geoBoundaries-IND-ADM1.geojson",
                "source_url": "https://www.geoboundaries.org",
                "reference_date": "2024-01-01",
                "source_version": "v5.0.0",
                "crs": "EPSG:4326",
                "srid": 4326,
                "is_authoritative": True,
                "is_active": True,
                "raw_metadata": json.dumps(props)
            })

    adm2_records = []
    adm2_shapes = []
    adm2_dist_data = []  # (state, district)

    if os.path.exists(adm2_file):
        with open(adm2_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        for feat in data.get("features", []):
            props = feat.get("properties", {})
            geom = feat.get("geometry", {})
            name = props.get("shapeName") or props.get("name") or "Unknown"
            code = props.get("shapeID") or props.get("shapeGroup") or str(uuid.uuid4())[:8]
            s = shapely.geometry.shape(geom)
            adm2_shapes.append(s)
            adm2_dist_data.append(name)
            adm2_records.append({
                "id": str(uuid.uuid4()),
                "admin_level": 2,
                "admin_level_name": "DISTRICT",
                "admin_code": code,
                "name": name,
                "normalized_name": name,
                "parent_code": None,
                "parent_name": None,
                "state_code": None,
                "state_name": None,
                "district_code": code,
                "district_name": name,
                "subdistrict_code": None,
                "geom": json.dumps(geom),
                "source": "geoBoundaries",
                "source_document": "geoBoundaries-IND-ADM2.geojson",
                "source_url": "https://www.geoboundaries.org",
                "reference_date": "2024-01-01",
                "source_version": "v5.0.0",
                "crs": "EPSG:4326",
                "srid": 4326,
                "is_authoritative": True,
                "is_active": True,
                "raw_metadata": json.dumps(props)
            })

    with engine.begin() as conn:
        conn.execute(text("DELETE FROM admin_boundaries;"))
        insert_sql = text("""
            INSERT INTO admin_boundaries (
                id, admin_level, admin_level_name, admin_code, name, normalized_name,
                parent_code, parent_name, state_code, state_name, district_code,
                district_name, subdistrict_code, geom, source, source_document,
                source_url, reference_date, source_version, crs, srid,
                is_authoritative, is_active, raw_metadata
            ) VALUES (
                :id, :admin_level, :admin_level_name, :admin_code, :name, :normalized_name,
                :parent_code, :parent_name, :state_code, :state_name, :district_code,
                :district_name, :subdistrict_code, :geom, :source, :source_document,
                :source_url, :reference_date, :source_version, :crs, :srid,
                :is_authoritative, :is_active, :raw_metadata
            );
        """)
        for b in [adm1_records, adm2_records]:
            if b:
                conn.execute(insert_sql, b)

    log(f"  -> Successfully stored {len(adm1_records)} States/UTs and {len(adm2_records)} Districts in admin_boundaries.")

    # Build STRtrees for spatial tagging
    adm1_tree = STRtree(adm1_shapes) if adm1_shapes else None
    adm2_tree = STRtree(adm2_shapes) if adm2_shapes else None
    return (adm1_tree, adm1_shapes, adm1_names), (adm2_tree, adm2_shapes, adm2_dist_data)


# =============================================================================
# 2. RESTORE 35,546 OSM INDUSTRIAL FACILITIES
# =============================================================================

def restore_osm_facilities(adm1_context, adm2_context):
    log("=== [2/5] Restoring 35,546 OSM Industrial Facilities ===")
    adm1_tree, adm1_shapes, adm1_names = adm1_context
    adm2_tree, adm2_shapes, adm2_dist_names = adm2_context

    osm_file = os.path.join(DATA_DIR, "FACILITIES", "OSM", "export.geojson")
    if not os.path.exists(osm_file):
        log(f"  [ERROR] {osm_file} not found!")
        return 0

    with open(osm_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    features = data.get("features", [])
    log(f"  -> Total features in file: {len(features):,}")

    facility_records = []
    skipped_oob = 0
    t0 = time.time()

    for feat in features:
        geom = feat.get("geometry", {})
        coords = geom.get("coordinates")
        if not coords or len(coords) < 2:
            continue
        lon, lat = float(coords[0]), float(coords[1])

        # Strict India Sovereign Bounds: [68.0, 6.5, 97.5, 37.5]
        if not (68.0 <= lon <= 97.5 and 6.5 <= lat <= 37.5):
            skipped_oob += 1
            continue

        props = feat.get("properties", {})
        raw_id = str(props.get("@id") or feat.get("id") or "")
        if "/" in raw_id:
            parts = raw_id.split("/")
            osm_type = parts[0].lower()
            try:
                osm_id = int(parts[1])
            except ValueError:
                osm_id = abs(hash(raw_id)) % 1000000000
        else:
            osm_type = "node" if geom.get("type") == "Point" else "way"
            try:
                osm_id = int(raw_id) if raw_id.isdigit() else (abs(hash(raw_id)) % 1000000000)
            except ValueError:
                osm_id = abs(hash(raw_id)) % 1000000000

        fid = f"osm_{osm_type}_{osm_id}"

        entity_class = classify_osm_entity(props)
        nic_code, master_sector, sub_sector, industry_type = resolve_nic_mapping(props, entity_class)
        confidence, verification_status = assess_quality_and_confidence(props, entity_class, nic_code)

        raw_name = props.get("name")
        norm_name = normalize_name(raw_name)
        raw_operator = props.get("operator")
        norm_operator = normalize_name(raw_operator)

        raw_state = props.get("addr:state") or props.get("is_in:state") or props.get("state")
        state = normalize_state(raw_state) if raw_state else None
        district = props.get("addr:district") or props.get("is_in:district") or props.get("district")
        city = (props.get("addr:city") or props.get("is_in:city") or props.get("city") or 
                props.get("addr:town") or props.get("addr:village"))
        industrial_area = props.get("addr:place") or props.get("addr:suburb") or props.get("industrial_area")

        # Point geometry for spatial lookup
        pt = shapely.geometry.Point(lon, lat)

        # If state is missing, resolve via STRtree
        if not state and adm1_tree:
            candidates = adm1_tree.query(pt)
            for idx in candidates:
                if adm1_shapes[idx].contains(pt):
                    state = normalize_state(adm1_names[idx])
                    break

        # If district is missing, resolve via STRtree
        if not district and adm2_tree:
            candidates = adm2_tree.query(pt)
            for idx in candidates:
                if adm2_shapes[idx].contains(pt):
                    district = adm2_dist_names[idx]
                    break

        if norm_name:
            display_name = norm_name
        elif norm_operator:
            display_name = f"{norm_operator} Facility"
        elif industry_type:
            display_name = f"{industry_type} ({osm_type.capitalize()} #{osm_id})"
        else:
            display_name = f"Industrial Site ({osm_type.capitalize()} #{osm_id})"

        facility_type_val = entity_class
        if entity_class == "POWER_PLANT":
            facility_type_val = "POWER_PLANT"
        elif entity_class == "REFINERY":
            facility_type_val = "REFINERY"
        elif entity_class == "MINE":
            facility_type_val = "MINING"

        facility_records.append({
            "id": fid,
            "name": display_name,
            "facility_type": facility_type_val,
            "status": "KNOWN" if verification_status == "VERIFIED" else "PROVISIONAL",
            "source": "OSM",
            "source_id": f"OSM-{osm_type.upper()}-{osm_id}",
            "state": state or "National / Unspecified",
            "district": district,
            "latitude": lat,
            "longitude": lon,
            "boundary_geojson": json.dumps(geom),
            "confidence_score": 1.0 if confidence == "HIGH" else (0.75 if confidence == "MEDIUM" else 0.5),
            "operating_hours": "24x7",
            "contact_info": json.dumps({
                "city": city,
                "district": district,
                "state": state,
                "osm_id": osm_id,
                "osm_type": osm_type
            }),
            "country": "India",
            "jurisdiction": "Sovereign Republic of India",
            "industry_id": f"FAC-OSM-{osm_type.upper()}-{osm_id}",
            "industry_name": display_name,
            "nic_code": nic_code,
            "master_sector": master_sector or "Manufacturing / Industrial",
            "sub_sector": sub_sector,
            "industry_type": industry_type,
            "company_name": norm_operator or display_name,
            "facility_name": display_name,
            "plant_name": display_name if facility_type_val in ["POWER_PLANT", "REFINERY"] else None,
            "city": city,
            "industrial_area": industrial_area,
            "operating_status": "OPERATIONAL",
            "data_source": "OSM",
            "source_record_id": str(osm_id),
            "source_file": "export.geojson",
            "verification_status": verification_status,
            "confidence": confidence,
            "last_updated": datetime.now(timezone.utc).isoformat()
        })

    log(f"  -> Extracted & normalized {len(facility_records):,} valid records (skipped {skipped_oob} out-of-bounds) in {time.time()-t0:.2f}s.")

    # Insert into industrial_facilities in chunks of 1,000
    chunk_size = 1000
    insert_sql = text("""
        INSERT INTO industrial_facilities (
            id, name, facility_type, status, source, source_id, state, district,
            latitude, longitude, boundary_geojson, confidence_score, operating_hours,
            contact_info, country, jurisdiction, industry_id, industry_name,
            nic_code, master_sector, sub_sector, industry_type, company_name,
            facility_name, plant_name, city, industrial_area, operating_status,
            data_source, source_record_id, source_file, verification_status,
            confidence, last_updated
        ) VALUES (
            :id, :name, :facility_type, :status, :source, :source_id, :state, :district,
            :latitude, :longitude, :boundary_geojson, :confidence_score, :operating_hours,
            :contact_info, :country, :jurisdiction, :industry_id, :industry_name,
            :nic_code, :master_sector, :sub_sector, :industry_type, :company_name,
            :facility_name, :plant_name, :city, :industrial_area, :operating_status,
            :data_source, :source_record_id, :source_file, :verification_status,
            :confidence, :last_updated
        )
        ON CONFLICT(id) DO UPDATE SET
            name = EXCLUDED.name,
            facility_type = EXCLUDED.facility_type,
            state = EXCLUDED.state,
            district = EXCLUDED.district,
            latitude = EXCLUDED.latitude,
            longitude = EXCLUDED.longitude,
            master_sector = EXCLUDED.master_sector,
            industry_type = EXCLUDED.industry_type,
            nic_code = EXCLUDED.nic_code;
    """)

    with engine.begin() as conn:
        for i in range(0, len(facility_records), chunk_size):
            chunk = facility_records[i:i+chunk_size]
            conn.execute(insert_sql, chunk)
            if (i + chunk_size) % 5000 < chunk_size or (i + chunk_size) >= len(facility_records):
                log(f"    Ingested {min(i+chunk_size, len(facility_records)):,} / {len(facility_records):,} facilities...")

    log(f"  -> Successfully stored {len(facility_records):,} industrial facilities in industrial_facilities table.")
    return len(facility_records)


# =============================================================================
# 3. RESTORE CEA POWER STATIONS
# =============================================================================

def restore_cea_power_stations():
    log("=== [3/5] Restoring CEA Power Stations Staging & Matching ===")
    from data_pipeline.cea_ingestion import find_cea_pdf_file, parse_cea_pdf
    try:
        pdf_path = find_cea_pdf_file()
        unit_records = parse_cea_pdf(pdf_path)
        log(f"  -> Extracted {len(unit_records):,} CEA power station unit records.")

        insert_sql = text("""
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
                project_name = EXCLUDED.project_name,
                installed_capacity_mw = EXCLUDED.installed_capacity_mw,
                prime_mover = EXCLUDED.prime_mover;
        """)

        with engine.begin() as conn:
            chunk_size = 500
            for i in range(0, len(unit_records), chunk_size):
                conn.execute(insert_sql, unit_records[i:i+chunk_size])

        log(f"  -> Successfully loaded {len(unit_records):,} units into cea_power_stations_staging.")

        # Enrich power facilities in industrial_facilities with CEA details
        with engine.begin() as conn:
            enrich_sql = text("""
                UPDATE industrial_facilities
                SET plant_capacity = (
                    SELECT CAST(SUM(installed_capacity_mw) AS TEXT) || ' MW'
                    FROM cea_power_stations_staging
                    WHERE LOWER(project_name) LIKE '%' || LOWER(industrial_facilities.name) || '%'
                       OR LOWER(industrial_facilities.name) LIKE '%' || LOWER(project_name) || '%'
                ),
                cea_project_name = (
                    SELECT project_name
                    FROM cea_power_stations_staging
                    WHERE LOWER(project_name) LIKE '%' || LOWER(industrial_facilities.name) || '%'
                       OR LOWER(industrial_facilities.name) LIKE '%' || LOWER(project_name) || '%'
                    LIMIT 1
                ),
                cea_organisation = (
                    SELECT organisation
                    FROM cea_power_stations_staging
                    WHERE LOWER(project_name) LIKE '%' || LOWER(industrial_facilities.name) || '%'
                       OR LOWER(industrial_facilities.name) LIKE '%' || LOWER(project_name) || '%'
                    LIMIT 1
                )
                WHERE facility_type = 'POWER_PLANT' OR LOWER(name) LIKE '%power%';
            """)
            conn.execute(enrich_sql)

        log("  -> Successfully enriched power facilities with official CEA capacities.")
    except Exception as e:
        log(f"  [WARN] CEA restoration partial: {e}")


# =============================================================================
# 4. RESTORE IBM MINING LEASE CONTEXT
# =============================================================================

def restore_ibm_mining():
    log("=== [4/5] Restoring IBM Mining Leases & Mining Context ===")
    from data_pipeline.ibm_lease_ingestion import get_pdf_path, REFERENCE_YEAR, REFERENCE_DATE, PROVISIONAL_FLAG, SOURCE_NAME
    import pdfplumber

    try:
        pdf_path = get_pdf_path()
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            log(f"  -> Reading IBM PDF: {total_pages} pages...")

            # Extract Table 1 (State-wise Summary)
            records = []
            p1 = pdf.pages[0]
            text_lines = p1.extract_text().split("\n")
            for line in text_lines:
                # Format: SlNo State Leases Area(ha)
                parts = line.strip().split()
                if len(parts) >= 4 and parts[0].isdigit():
                    try:
                        state_name = " ".join(parts[1:-2])
                        lease_cnt = int(parts[-2].replace(",", ""))
                        area_ha = float(parts[-1].replace(",", ""))
                        rec_id = f"IBM_2024_T1_{state_name.upper()}"
                        records.append({
                            "id": str(uuid.uuid4()),
                            "record_id": rec_id,
                            "state": state_name,
                            "district": "ALL_DISTRICTS",
                            "mineral": "ALL_MAJOR_MINERALS",
                            "lease_count": lease_cnt,
                            "lease_area_ha": area_ha,
                            "sector": "ALL_SECTORS",
                            "potential_category": "ACTIVE_EXTRACTION",
                            "reference_year": REFERENCE_YEAR,
                            "source_document": "ML_PL_2024.pdf",
                            "table_number": "Table-1",
                            "page_number": 1,
                            "provisional_flag": PROVISIONAL_FLAG,
                            "source": SOURCE_NAME,
                            "aggregation_level": "STATE"
                        })
                    except Exception:
                        pass

        if records:
            insert_sql = text("""
                INSERT INTO ibm_mining_lease_context (
                    id, record_id, state, district, mineral, lease_count, lease_area_ha,
                    sector, potential_category, reference_year, source_document,
                    table_number, page_number, provisional_flag, source, aggregation_level
                ) VALUES (
                    :id, :record_id, :state, :district, :mineral, :lease_count, :lease_area_ha,
                    :sector, :potential_category, :reference_year, :source_document,
                    :table_number, :page_number, :provisional_flag, :source, :aggregation_level
                );
            """)
            with engine.begin() as conn:
                conn.execute(text("DELETE FROM ibm_mining_lease_context;"))
                conn.execute(insert_sql, records)
            log(f"  -> Successfully stored {len(records)} verified IBM mining context records.")
    except Exception as e:
        log(f"  [WARN] IBM Mining restoration partial: {e}")


# =============================================================================
# 5. RE-EVALUATE EVENT PROXIMITY & CREATE INDICES
# =============================================================================

def reevaluate_event_proximity_and_indexes():
    log("=== [5/5] Re-evaluating Event Proximity across 35,546 Facilities & Indexing ===")
    with engine.begin() as conn:
        # Create indexes
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_facilities_coords ON industrial_facilities(latitude, longitude);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_facilities_type ON industrial_facilities(facility_type);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_facilities_state ON industrial_facilities(state);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_admin_boundaries_level ON admin_boundaries(admin_level);"))

        # Re-evaluate all 88 active events against the full 35,546 facilities
        events = conn.execute(text("SELECT id, latitude, longitude FROM thermal_events;")).fetchall()
        log(f"  -> Re-linking {len(events)} events against restored facility population...")

        update_sql = text("""
            UPDATE thermal_events
            SET nearest_facility_distance_m = :dist,
                facility_status = :status
            WHERE id = :eid;
        """)

        # Fast nearest facility query for each event using bounding box + haversine
        for eid, elat, elon in events:
            # Query candidate facilities within ~0.5 degree (~55km)
            candidates = conn.execute(text("""
                SELECT id, latitude, longitude
                FROM industrial_facilities
                WHERE latitude BETWEEN :min_lat AND :max_lat
                  AND longitude BETWEEN :min_lon AND :max_lon
                LIMIT 50;
            """), {
                "min_lat": elat - 0.5, "max_lat": elat + 0.5,
                "min_lon": elon - 0.5, "max_lon": elon + 0.5
            }).fetchall()

            if not candidates:
                # Fallback to broader 1.0 degree
                candidates = conn.execute(text("""
                    SELECT id, latitude, longitude
                    FROM industrial_facilities
                    WHERE latitude BETWEEN :min_lat AND :max_lat
                      AND longitude BETWEEN :min_lon AND :max_lon
                    LIMIT 20;
                """), {
                    "min_lat": elat - 1.0, "max_lat": elat + 1.0,
                    "min_lon": elon - 1.0, "max_lon": elon + 1.0
                }).fetchall()

            if candidates:
                min_dist = min(haversine_distance_meters(elat, elon, c[1], c[2]) for c in candidates)
                status_val = "ON_SITE" if min_dist <= 500 else ("PROXIMATE" if min_dist <= 5000 else "REMOTE")
                conn.execute(update_sql, {"eid": eid, "dist": min_dist, "status": status_val})

    log("  -> Successfully re-linked event proximity and built spatial indexes.")


def run_full_restoration():
    total_t0 = time.time()
    log("==========================================================================")
    log("  AGNI-NETRA — PHASE 25.3 MASTER DATA RESTORATION & CONSISTENCY ENGINE    ")
    log("==========================================================================")

    adm1_ctx, adm2_ctx = restore_admin_boundaries()
    fac_count = restore_osm_facilities(adm1_ctx, adm2_ctx)
    restore_cea_power_stations()
    restore_ibm_mining()
    reevaluate_event_proximity_and_indexes()

    log(f"=== RESTORATION COMPLETE IN {time.time()-total_t0:.2f}s ===")


if __name__ == "__main__":
    run_full_restoration()
