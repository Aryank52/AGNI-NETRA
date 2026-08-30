"""
AGNI-NETRA — High-Performance OSM Ingestion Pipeline
Extracts, normalizes, classifies, maps NIC-2008 codes, creates PostGIS geometries,
and loads OpenStreetMap data into PostGIS osm_staging_facilities and canonical industrial_facilities registry.
"""

import os
import sys
import json
import uuid
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import text
from backend.app.core.database import engine
from data_pipeline.nic_mapping import resolve_nic_mapping
from data_pipeline.osm_classifier import (
    classify_osm_entity,
    normalize_name,
    normalize_state,
    assess_quality_and_confidence
)


DATA_PATHS = [
    r"E:\PROJECTS\AGNI-NETRA(DATABASE)\FACILITIES\OSM\export.geojson",
    r"E:\AGNI-NETRA-DATA\FACILITIES\OSM\export.geojson"
]


def find_osm_geojson_file() -> str:
    for path in DATA_PATHS:
        if os.path.exists(path):
            return path
    raise FileNotFoundError(f"OSM export.geojson not found in known paths: {DATA_PATHS}")


def parse_osm_identifier(feat: Dict[str, Any]) -> Tuple[str, int, str]:
    """
    Parses OSM type ('node', 'way', 'relation'), OSM ID (integer), and composite ID.
    """
    props = feat.get("properties", {})
    raw_id = str(props.get("@id") or feat.get("id") or "")
    
    if "/" in raw_id:
        parts = raw_id.split("/")
        osm_type = parts[0].lower()
        try:
            osm_id = int(parts[1])
        except ValueError:
            osm_id = 0
    else:
        osm_type = "node" if feat.get("geometry", {}).get("type") == "Point" else "way"
        try:
            osm_id = int(raw_id) if raw_id.isdigit() else 0
        except ValueError:
            osm_id = 0

    composite_id = f"osm_{osm_type}_{osm_id}"
    return osm_type, osm_id, composite_id


def process_osm_feature(feat: Dict[str, Any], filename: str) -> Optional[Dict[str, Any]]:
    """
    Transforms a single GeoJSON feature into normalized staging & canonical record format.
    """
    geom = feat.get("geometry")
    if not geom or not geom.get("coordinates"):
        return None

    coords = geom.get("coordinates")
    if len(coords) < 2:
        return None

    lon, lat = float(coords[0]), float(coords[1])
    if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
        return None

    props = feat.get("properties", {})
    osm_type, osm_id, composite_id = parse_osm_identifier(feat)
    if osm_id == 0:
        return None

    # Classification & Mapping
    entity_class = classify_osm_entity(props)
    nic_code, master_sector, sub_sector, industry_type = resolve_nic_mapping(props, entity_class)
    confidence, verification_status = assess_quality_and_confidence(props, entity_class, nic_code)

    raw_name = props.get("name")
    norm_name = normalize_name(raw_name)
    raw_operator = props.get("operator")
    norm_operator = normalize_name(raw_operator)

    # Address attributes - extracted strictly from tags (never fabricated)
    raw_state = props.get("addr:state") or props.get("is_in:state") or props.get("state")
    state = normalize_state(raw_state)
    district = props.get("addr:district") or props.get("is_in:district") or props.get("district")
    city = (props.get("addr:city") or props.get("is_in:city") or props.get("city") or 
            props.get("addr:town") or props.get("addr:village"))
    industrial_area = props.get("addr:place") or props.get("addr:suburb") or props.get("industrial_area")

    # Specific tags
    industrial_tag = props.get("industrial")
    landuse_tag = props.get("landuse")
    man_made_tag = props.get("man_made")
    power_tag = props.get("power")
    amenity_tag = props.get("amenity")
    plant_source = props.get("plant:source")
    plant_output = props.get("plant:output:electricity") or props.get("plant:output")
    plant_method = props.get("plant:method")
    product = props.get("product")
    resource = props.get("resource")

    website = props.get("website") or props.get("contact:website")
    phone = props.get("phone") or props.get("contact:phone")

    # Display / Search name
    if norm_name:
        display_name = norm_name
    elif norm_operator:
        display_name = f"{norm_operator} Facility"
    elif industry_type:
        display_name = f"{industry_type} ({osm_type.capitalize()} #{osm_id})"
    else:
        display_name = f"Industrial Site ({osm_type.capitalize()} #{osm_id})"

    return {
        "id": composite_id,
        "osm_type": osm_type,
        "osm_id": osm_id,
        "name": display_name,
        "operator": norm_operator,
        "entity_classification": entity_class,
        "industrial_tag": industrial_tag,
        "landuse_tag": landuse_tag,
        "man_made_tag": man_made_tag,
        "power_tag": power_tag,
        "amenity_tag": amenity_tag,
        "plant_source": plant_source,
        "plant_output": plant_output,
        "plant_method": plant_method,
        "product": product,
        "resource": resource,
        "nic_code": nic_code,
        "master_sector": master_sector,
        "sub_sector": sub_sector,
        "industry_type": industry_type,
        "state": state,
        "district": district,
        "city": city,
        "industrial_area": industrial_area,
        "latitude": lat,
        "longitude": lon,
        "confidence": confidence,
        "verification_status": verification_status,
        "source": "OSM",
        "source_record_id": composite_id,
        "source_file": filename,
        "source_metadata": json.dumps(props),
        "website": website,
        "phone": phone
    }


def run_osm_ingestion():
    geojson_path = find_osm_geojson_file()
    filename = os.path.basename(geojson_path)
    print(f"[AGNI-NETRA] Reading OSM GeoJSON file from: {geojson_path}")

    start_time = time.time()
    with open(geojson_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    features = data.get("features", [])
    total_features = len(features)
    print(f"[AGNI-NETRA] Total features loaded: {total_features:,}")

    processed_records = []
    skipped_count = 0
    seen_ids = set()
    duplicate_count = 0

    for feat in features:
        rec = process_osm_feature(feat, filename)
        if not rec:
            skipped_count += 1
            continue

        if rec["id"] in seen_ids:
            duplicate_count += 1
            continue

        seen_ids.add(rec["id"])
        processed_records.append(rec)

    print(f"[AGNI-NETRA] Successfully processed {len(processed_records):,} valid unique OSM records.")
    print(f"[AGNI-NETRA] Skipped: {skipped_count}, In-file Duplicates: {duplicate_count}")

    # 1. Batch Insert into osm_staging_facilities
    print("\n[AGNI-NETRA] [Step 1/2] Ingesting records into osm_staging_facilities...")
    batch_size = 1000
    staging_insert_query = text("""
        INSERT INTO osm_staging_facilities (
            id, osm_type, osm_id, name, operator, entity_classification,
            industrial_tag, landuse_tag, man_made_tag, power_tag, amenity_tag,
            plant_source, plant_output, plant_method, product, resource,
            nic_code, master_sector, sub_sector, industry_type,
            state, district, city, industrial_area,
            latitude, longitude, geom, geom_point,
            confidence, verification_status, source, source_record_id, source_file, source_metadata
        ) VALUES (
            :id, :osm_type, :osm_id, :name, :operator, :entity_classification,
            :industrial_tag, :landuse_tag, :man_made_tag, :power_tag, :amenity_tag,
            :plant_source, :plant_output, :plant_method, :product, :resource,
            :nic_code, :master_sector, :sub_sector, :industry_type,
            :state, :district, :city, :industrial_area,
            :latitude, :longitude,
            ST_SetSRID(ST_MakePoint(:longitude, :latitude), 4326),
            ST_SetSRID(ST_MakePoint(:longitude, :latitude), 4326),
            :confidence, :verification_status, :source, :source_record_id, :source_file, CAST(:source_metadata AS JSONB)
        )
        ON CONFLICT (id) DO UPDATE SET
            name = EXCLUDED.name,
            operator = EXCLUDED.operator,
            entity_classification = EXCLUDED.entity_classification,
            nic_code = EXCLUDED.nic_code,
            master_sector = EXCLUDED.master_sector,
            sub_sector = EXCLUDED.sub_sector,
            industry_type = EXCLUDED.industry_type,
            confidence = EXCLUDED.confidence,
            verification_status = EXCLUDED.verification_status,
            source_metadata = EXCLUDED.source_metadata;
    """)

    with engine.begin() as conn:
        for i in range(0, len(processed_records), batch_size):
            batch = processed_records[i : i + batch_size]
            conn.execute(staging_insert_query, batch)
            if (i + batch_size) % 5000 < batch_size or (i + len(batch)) == len(processed_records):
                print(f"  -> Staging: {min(i + batch_size, len(processed_records)):,} / {len(processed_records):,} records...")

    # 2. Batch Sync into canonical industrial_facilities (Without overwriting existing records)
    print("\n[AGNI-NETRA] [Step 2/2] Synchronizing into canonical industrial_facilities registry...")
    
    canonical_sync_query = text("""
        INSERT INTO industrial_facilities (
            id, name, facility_type, status, source, source_id,
            state, district, latitude, longitude,
            confidence_score, operating_hours, contact_info,
            industry_id, industry_name, nic_code, master_sector, sub_sector,
            industry_type, company_name, facility_name, plant_name,
            city, industrial_area, geom,
            operating_status, data_source, source_record_id, source_file,
            source_metadata, verification_status, confidence, last_updated
        )
        SELECT
            gen_random_uuid()::varchar(36) AS id,
            s.name,
            s.entity_classification AS facility_type,
            CASE WHEN s.verification_status = 'VERIFIED' THEN 'KNOWN' ELSE 'PROVISIONAL' END AS status,
            'OSM' AS source,
            s.source_record_id AS source_id,
            COALESCE(s.state, 'National / Unspecified') AS state,
            s.district,
            s.latitude,
            s.longitude,
            CASE WHEN s.confidence = 'HIGH' THEN 1.0 WHEN s.confidence = 'MEDIUM' THEN 0.75 ELSE 0.5 END AS confidence_score,
            '24x7' AS operating_hours,
            jsonb_build_object(
                'city', s.city,
                'district', s.district,
                'state', s.state,
                'osm_id', s.osm_id,
                'osm_type', s.osm_type
            ) AS contact_info,
            ('FAC-OSM-' || UPPER(s.osm_type) || '-' || s.osm_id::text) AS industry_id,
            s.name AS industry_name,
            s.nic_code,
            s.master_sector,
            s.sub_sector,
            s.industry_type,
            s.operator AS company_name,
            s.name AS facility_name,
            CASE WHEN s.entity_classification IN ('POWER_PLANT', 'REFINERY', 'FACILITY') THEN s.name ELSE NULL END AS plant_name,
            s.city,
            s.industrial_area,
            s.geom,
            'OPERATIONAL' AS operating_status,
            'OSM' AS data_source,
            s.source_record_id,
            s.source_file,
            s.source_metadata,
            s.verification_status,
            s.confidence,
            NOW() AT TIME ZONE 'UTC' AS last_updated
        FROM osm_staging_facilities s
        WHERE NOT EXISTS (
            SELECT 1 FROM industrial_facilities f
            WHERE f.source_id = s.source_record_id OR f.source_record_id = s.source_record_id
        );
    """)

    with engine.begin() as conn:
        res = conn.execute(canonical_sync_query)
        print(f"  -> Canonical Registry: {res.rowcount:,} new facility records inserted.")

    elapsed = time.time() - start_time
    print(f"\n[AGNI-NETRA] Ingestion completed successfully in {elapsed:.2f} seconds.")


if __name__ == "__main__":
    run_osm_ingestion()
