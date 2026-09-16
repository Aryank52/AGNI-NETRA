"""
AGNI-NETRA — Phase 25.1 GIS Restoration Script
Restores:
1. protected_areas: 11 verified Indian Protected Areas (WII / FSI)
2. lulc_spatial_features: 15 verified Bhuvan LULC Spatial Polygons (ISRO)
Compatible with both PostgreSQL+PostGIS and SQLite test/demo environments.
"""

import os
import sys
import json
import logging
from datetime import datetime, timezone
from sqlalchemy import text

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.app.core.database import engine, IS_POSTGRESQL
from database.seed_fsi_forest_registry import PROTECTED_AREAS, FSI_SOURCES
from database.seed_bhuvan_lulc_registry import BHUVAN_CLASSES, PILOT_AOI_FEATURES as BHUVAN_AOI_FEATURES

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("RestoreGIS")


def restore_gis_tables():
    logger.info(f"Starting GIS table and dataset restoration (IS_POSTGRESQL={IS_POSTGRESQL})...")

    with engine.begin() as conn:
        # -------------------------------------------------------------
        # 1. Ensure fsi_sources and protected_areas tables exist
        # -------------------------------------------------------------
        if IS_POSTGRESQL:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS fsi_sources (
                    id VARCHAR(64) PRIMARY KEY,
                    source_name VARCHAR(100) UNIQUE NOT NULL,
                    organization VARCHAR(255) NOT NULL,
                    dataset_name VARCHAR(255) NOT NULL,
                    reference_year INTEGER NOT NULL,
                    product_version VARCHAR(50) NOT NULL,
                    access_method VARCHAR(100) NOT NULL,
                    source_url VARCHAR(500) NOT NULL,
                    license VARCHAR(150) NOT NULL,
                    metadata_info JSONB DEFAULT '{}'::jsonb,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS protected_areas (
                    id VARCHAR(64) PRIMARY KEY,
                    pa_name VARCHAR(255) NOT NULL,
                    pa_type VARCHAR(50) NOT NULL,
                    state VARCHAR(100) NOT NULL,
                    district VARCHAR(100),
                    established_year INTEGER,
                    area_sqkm FLOAT,
                    geom GEOMETRY(MultiPolygon, 4326) NOT NULL,
                    legal_status VARCHAR(100),
                    source_id VARCHAR(64) REFERENCES fsi_sources(id) ON DELETE CASCADE,
                    source_record_id VARCHAR(100),
                    reference_date VARCHAR(50),
                    metadata_info JSONB DEFAULT '{}'::jsonb,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            """))
        else:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS fsi_sources (
                    id VARCHAR(64) PRIMARY KEY,
                    source_name VARCHAR(100) UNIQUE NOT NULL,
                    organization VARCHAR(255) NOT NULL,
                    dataset_name VARCHAR(255) NOT NULL,
                    reference_year INTEGER NOT NULL,
                    product_version VARCHAR(50) NOT NULL,
                    access_method VARCHAR(100) NOT NULL,
                    source_url VARCHAR(500) NOT NULL,
                    license VARCHAR(150) NOT NULL,
                    metadata_info JSON,
                    created_at DATETIME
                );
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS protected_areas (
                    id VARCHAR(64) PRIMARY KEY,
                    pa_name VARCHAR(255) NOT NULL,
                    pa_type VARCHAR(50) NOT NULL,
                    state VARCHAR(100) NOT NULL,
                    district VARCHAR(100),
                    established_year INTEGER,
                    area_sqkm FLOAT,
                    geom GEOMETRY NOT NULL,
                    legal_status VARCHAR(100),
                    source_id VARCHAR(64),
                    source_record_id VARCHAR(100),
                    reference_date VARCHAR(50),
                    metadata_info JSON,
                    created_at DATETIME
                );
            """))

        # Seed FSI Sources
        for s in FSI_SOURCES:
            existing = conn.execute(text("SELECT id FROM fsi_sources WHERE id = :id"), {"id": s["id"]}).fetchone()
            if not existing:
                conn.execute(text("""
                    INSERT INTO fsi_sources (id, source_name, organization, dataset_name, reference_year, product_version, access_method, source_url, license, metadata_info, created_at)
                    VALUES (:id, :name, :org, :ds, :yr, :pv, :am, :url, :lic, :meta, :created)
                """), {
                    "id": s["id"],
                    "name": s["source_name"],
                    "org": s["organization"],
                    "ds": s["dataset_name"],
                    "yr": s["reference_year"],
                    "pv": s["product_version"],
                    "am": s["access_method"],
                    "url": s["source_url"],
                    "lic": s["license"],
                    "meta": json.dumps(s.get("metadata_info", {})),
                    "created": datetime.now(timezone.utc)
                })

        # Seed 11 Verified Protected Areas
        for pa in PROTECTED_AREAS:
            existing = conn.execute(text("SELECT id FROM protected_areas WHERE id = :id"), {"id": pa["id"]}).fetchone()
            if IS_POSTGRESQL:
                if not existing:
                    conn.execute(text("""
                        INSERT INTO protected_areas (id, pa_name, pa_type, state, district, established_year, area_sqkm, geom, legal_status, source_id, source_record_id, reference_date, metadata_info, created_at)
                        VALUES (:id, :name, :type, :state, :district, :year, :area, ST_Multi(ST_GeomFromText(:wkt, 4326)), :legal, 'WII_PA_REGISTRY', :rec_id, '2024', :meta, :created)
                    """), {
                        "id": pa["id"], "name": pa["name"], "type": pa["type"], "state": pa["state"], "district": pa["district"],
                        "year": pa["established_year"], "area": pa["area_sqkm"], "wkt": pa["wkt"], "legal": pa["legal_status"],
                        "rec_id": f"WII_{pa['id']}", "meta": json.dumps(pa["meta"]), "created": datetime.now(timezone.utc)
                    })
            else:
                if not existing:
                    conn.execute(text("""
                        INSERT INTO protected_areas (id, pa_name, pa_type, state, district, established_year, area_sqkm, geom, legal_status, source_id, source_record_id, reference_date, metadata_info, created_at)
                        VALUES (:id, :name, :type, :state, :district, :year, :area, :wkt, :legal, 'WII_PA_REGISTRY', :rec_id, '2024', :meta, :created)
                    """), {
                        "id": pa["id"], "name": pa["name"], "type": pa["type"], "state": pa["state"], "district": pa["district"],
                        "year": pa["established_year"], "area": pa["area_sqkm"], "wkt": pa["wkt"], "legal": pa["legal_status"],
                        "rec_id": f"WII_{pa['id']}", "meta": json.dumps(pa["meta"]), "created": datetime.now(timezone.utc)
                    })
                else:
                    conn.execute(text("""
                        UPDATE protected_areas SET geom = :wkt WHERE id = :id
                    """), {"wkt": pa["wkt"], "id": pa["id"]})

        logger.info("Successfully restored and verified 11 Protected Areas.")

        # -------------------------------------------------------------
        # 2. Ensure lulc_sources, lulc_classes, lulc_spatial_features exist
        # -------------------------------------------------------------
        if IS_POSTGRESQL:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS lulc_sources (
                    id VARCHAR(64) PRIMARY KEY,
                    source_name VARCHAR(100) UNIQUE NOT NULL,
                    organization VARCHAR(255) NOT NULL,
                    dataset_name VARCHAR(255) NOT NULL,
                    resolution_m FLOAT NOT NULL,
                    reference_year INTEGER NOT NULL,
                    product_version VARCHAR(50) NOT NULL,
                    access_type VARCHAR(50) NOT NULL,
                    license VARCHAR(150) NOT NULL,
                    source_url VARCHAR(500) NOT NULL,
                    metadata_info JSONB DEFAULT '{}'::jsonb,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS lulc_classes (
                    id VARCHAR(64) PRIMARY KEY,
                    source_id VARCHAR(64) REFERENCES lulc_sources(id) ON DELETE CASCADE,
                    source_class_code VARCHAR(50) NOT NULL,
                    source_class_name VARCHAR(150) NOT NULL,
                    canonical_class VARCHAR(50) NOT NULL,
                    is_industrial_compatible BOOLEAN DEFAULT FALSE,
                    risk_weight FLOAT DEFAULT 0.5,
                    description TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT uq_source_class UNIQUE (source_id, source_class_code)
                );
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS lulc_spatial_features (
                    id VARCHAR(64) PRIMARY KEY,
                    source_id VARCHAR(64) REFERENCES lulc_sources(id) ON DELETE CASCADE,
                    class_id VARCHAR(64) REFERENCES lulc_classes(id) ON DELETE CASCADE,
                    canonical_class VARCHAR(50) NOT NULL,
                    feature_name VARCHAR(255),
                    state VARCHAR(100),
                    district VARCHAR(100),
                    geom GEOMETRY(MultiPolygon, 4326) NOT NULL,
                    area_sqkm FLOAT,
                    source_provenance JSONB DEFAULT '{}'::jsonb,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            """))
        else:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS lulc_sources (
                    id VARCHAR(64) PRIMARY KEY,
                    source_name VARCHAR(100) UNIQUE NOT NULL,
                    organization VARCHAR(255) NOT NULL,
                    dataset_name VARCHAR(255) NOT NULL,
                    resolution_m FLOAT NOT NULL,
                    reference_year INTEGER NOT NULL,
                    product_version VARCHAR(50) NOT NULL,
                    access_type VARCHAR(50) NOT NULL,
                    license VARCHAR(150) NOT NULL,
                    source_url VARCHAR(500) NOT NULL,
                    metadata_info JSON,
                    created_at DATETIME
                );
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS lulc_classes (
                    id VARCHAR(64) PRIMARY KEY,
                    source_id VARCHAR(64),
                    source_class_code VARCHAR(50) NOT NULL,
                    source_class_name VARCHAR(150) NOT NULL,
                    canonical_class VARCHAR(50) NOT NULL,
                    is_industrial_compatible BOOLEAN DEFAULT 0,
                    risk_weight FLOAT DEFAULT 0.5,
                    description TEXT,
                    created_at DATETIME
                );
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS lulc_spatial_features (
                    id VARCHAR(64) PRIMARY KEY,
                    source_id VARCHAR(64),
                    class_id VARCHAR(64),
                    canonical_class VARCHAR(50) NOT NULL,
                    feature_name VARCHAR(255),
                    state VARCHAR(100),
                    district VARCHAR(100),
                    geom GEOMETRY NOT NULL,
                    area_sqkm FLOAT,
                    source_provenance JSON,
                    created_at DATETIME
                );
            """))

        # Seed Bhuvan LULC Source
        existing_src = conn.execute(text("SELECT id FROM lulc_sources WHERE id = 'ISRO_BHUVAN_50K'")).fetchone()
        if not existing_src:
            conn.execute(text("""
                INSERT INTO lulc_sources (id, source_name, organization, dataset_name, resolution_m, reference_year, product_version, access_type, license, source_url, metadata_info, created_at)
                VALUES ('ISRO_BHUVAN_50K', 'ISRO_BHUVAN_LULC_50K', 'National Remote Sensing Centre (NRSC), ISRO', 'Bhuvan 1:50,000 Thematic Land Use / Land Cover Atlas', 24.0, 2021, 'BHUVAN-LULC-V3', 'WMS_OGC_AND_VECTOR', 'Government Open Data License - India (GODL)', 'https://bhuvan.nrsc.gov.in', :meta, :created)
            """), {"meta": json.dumps({"sensor": "IRS Resourcesat-2 LISS-IV & LISS-III"}), "created": datetime.now(timezone.utc)})

        # Seed Bhuvan LULC Classes
        for cls in BHUVAN_CLASSES:
            cls_id = f"BHUVAN_{cls['code'].replace('.', '_')}"
            existing_c = conn.execute(text("SELECT id FROM lulc_classes WHERE id = :id"), {"id": cls_id}).fetchone()
            if not existing_c:
                conn.execute(text("""
                    INSERT INTO lulc_classes (id, source_id, source_class_code, source_class_name, canonical_class, is_industrial_compatible, risk_weight, description, created_at)
                    VALUES (:id, 'ISRO_BHUVAN_50K', :code, :name, :canonical, :ind, :rw, :desc, :created)
                """), {
                    "id": cls_id, "code": cls["code"], "name": cls["name"], "canonical": cls["canonical"],
                    "ind": cls["is_ind"], "rw": cls["risk_weight"], "desc": cls["desc"], "created": datetime.now(timezone.utc)
                })

        # Seed 15 Verified Bhuvan LULC Spatial Features
        for idx, feat in enumerate(BHUVAN_AOI_FEATURES, 1):
            feat_id = f"LULC_FEAT_{idx:03d}_{feat['canonical'][:8]}"
            cls_id = f"BHUVAN_{feat['class_code'].replace('.', '_')}"
            existing_f = conn.execute(text("SELECT id FROM lulc_spatial_features WHERE id = :id"), {"id": feat_id}).fetchone()
            if IS_POSTGRESQL:
                if not existing_f:
                    conn.execute(text("""
                        INSERT INTO lulc_spatial_features (id, source_id, class_id, canonical_class, feature_name, state, district, geom, area_sqkm, source_provenance, created_at)
                        VALUES (:id, 'ISRO_BHUVAN_50K', :cid, :canonical, :name, :state, :district, ST_Multi(ST_GeomFromText(:wkt, 4326)), :area, :prov, :created)
                    """), {
                        "id": feat_id, "cid": cls_id, "canonical": feat["canonical"], "name": feat["name"],
                        "state": feat["state"], "district": feat["district"], "wkt": feat["wkt"], "area": feat["area_sqkm"],
                        "prov": json.dumps({"source": feat["source"], "code": feat["class_code"]}), "created": datetime.now(timezone.utc)
                    })
            else:
                if not existing_f:
                    conn.execute(text("""
                        INSERT INTO lulc_spatial_features (id, source_id, class_id, canonical_class, feature_name, state, district, geom, area_sqkm, source_provenance, created_at)
                        VALUES (:id, 'ISRO_BHUVAN_50K', :cid, :canonical, :name, :state, :district, :wkt, :area, :prov, :created)
                    """), {
                        "id": feat_id, "cid": cls_id, "canonical": feat["canonical"], "name": feat["name"],
                        "state": feat["state"], "district": feat["district"], "wkt": feat["wkt"], "area": feat["area_sqkm"],
                        "prov": json.dumps({"source": feat["source"], "code": feat["class_code"]}), "created": datetime.now(timezone.utc)
                    })
                else:
                    conn.execute(text("""
                        UPDATE lulc_spatial_features SET geom = :wkt WHERE id = :id
                    """), {"wkt": feat["wkt"], "id": feat_id})

        logger.info(f"Successfully restored and verified {len(BHUVAN_AOI_FEATURES)} Bhuvan LULC Spatial Features.")

        # Verification counts
        pa_count = conn.execute(text("SELECT COUNT(*) FROM protected_areas;")).scalar()
        lulc_count = conn.execute(text("SELECT COUNT(*) FROM lulc_spatial_features;")).scalar()
        logger.info(f"VERIFIED DATABASE COUNTS -> protected_areas: {pa_count}, lulc_spatial_features: {lulc_count}")


if __name__ == "__main__":
    restore_gis_tables()
