"""
Migration script for Phase 16: Global Data Ingestion, Normalization & Data Governance
Creates normalized data-plane tables:
- ingestion_batches (tracks ingestion execution, status, and checksums)
- ingestion_records (canonical record lifecycle with recoverable source identity)
- ingestion_quarantine (quarantine isolation for rejected / malformed payloads)
- dataset_registry (governed dataset registry with coverage, retention, and freshness SLA)
- ingestion_checkpoints (deterministic restart / cursor checkpoints)
"""

import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from backend.app.core.database import engine, IS_SQLITE_TEST


def migrate():
    print(f"[*] Starting Phase 16 Data Governance Migration (Database Engine: {'SQLite' if IS_SQLITE_TEST else 'PostgreSQL'})...")

    with engine.begin() as conn:
        # 1. Ingestion Batches Table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS ingestion_batches (
                id VARCHAR(36) PRIMARY KEY,
                batch_id VARCHAR(64) UNIQUE NOT NULL,
                provider VARCHAR(100) NOT NULL,
                dataset VARCHAR(100) NOT NULL,
                mode VARCHAR(32) DEFAULT 'INCREMENTAL' NOT NULL,
                started_at TIMESTAMP NOT NULL,
                completed_at TIMESTAMP,
                records_received INTEGER DEFAULT 0,
                records_accepted INTEGER DEFAULT 0,
                records_rejected INTEGER DEFAULT 0,
                records_quarantined INTEGER DEFAULT 0,
                records_duplicated INTEGER DEFAULT 0,
                records_failed INTEGER DEFAULT 0,
                schema_version VARCHAR(32) DEFAULT '1.0.0',
                normalization_version VARCHAR(32) DEFAULT '1.0.0',
                checksum VARCHAR(64),
                status VARCHAR(32) DEFAULT 'RUNNING',
                error_message TEXT,
                checkpoint JSON DEFAULT '{}',
                metadata_payload JSON DEFAULT '{}'
            );
        """))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_ingest_batch_id ON ingestion_batches(batch_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_ingest_batch_provider ON ingestion_batches(provider);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_ingest_batch_started ON ingestion_batches(started_at);"))

        # 2. Ingestion Records Table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS ingestion_records (
                id VARCHAR(36) PRIMARY KEY,
                ingestion_id VARCHAR(64) UNIQUE NOT NULL,
                batch_id VARCHAR(64) NOT NULL,
                provider VARCHAR(100) NOT NULL,
                dataset VARCHAR(100) NOT NULL,
                source_record_id VARCHAR(255),
                received_at TIMESTAMP NOT NULL,
                observation_time TIMESTAMP,
                country VARCHAR(100) DEFAULT 'GLOBAL',
                jurisdiction VARCHAR(100),
                latitude FLOAT,
                longitude FLOAT,
                geometry JSON,
                schema_version VARCHAR(32) DEFAULT '1.0.0',
                source_type VARCHAR(50) DEFAULT 'REAL_PROVIDER',
                quality_status VARCHAR(32) DEFAULT 'PASS',
                quality_reasons JSON DEFAULT '[]',
                dedup_status VARCHAR(50) DEFAULT 'UNIQUE',
                duplicate_of_id VARCHAR(64),
                provenance_id VARCHAR(64),
                processing_status VARCHAR(32) DEFAULT 'RECEIVED',
                lifecycle_state VARCHAR(32) DEFAULT 'ORIGINAL',
                error_code VARCHAR(64),
                error_message_safe TEXT,
                raw_payload JSON DEFAULT '{}',
                normalized_payload JSON DEFAULT '{}'
            );
        """))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_ingest_rec_id ON ingestion_records(ingestion_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_ingest_rec_batch ON ingestion_records(batch_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_ingest_rec_provider ON ingestion_records(provider);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_ingest_rec_src_id ON ingestion_records(source_record_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_ingest_rec_obs_time ON ingestion_records(observation_time);"))

        # 3. Ingestion Quarantine Table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS ingestion_quarantine (
                id VARCHAR(36) PRIMARY KEY,
                quarantine_id VARCHAR(64) UNIQUE NOT NULL,
                batch_id VARCHAR(64),
                provider VARCHAR(100) NOT NULL,
                dataset VARCHAR(100) NOT NULL,
                source_record_id VARCHAR(255),
                reason TEXT NOT NULL,
                error_code VARCHAR(64) DEFAULT 'VALIDATION_FAILURE',
                raw_safe_reference JSON DEFAULT '{}',
                detected_at TIMESTAMP NOT NULL,
                resolved_at TIMESTAMP,
                resolution VARCHAR(50) DEFAULT 'UNRESOLVED',
                resolved_by VARCHAR(64)
            );
        """))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_quarantine_id ON ingestion_quarantine(quarantine_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_quarantine_provider ON ingestion_quarantine(provider);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_quarantine_detected ON ingestion_quarantine(detected_at);"))

        # 4. Dataset Registry Table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS governed_dataset_registry (
                id VARCHAR(36) PRIMARY KEY,
                dataset_id VARCHAR(100) UNIQUE NOT NULL,
                provider VARCHAR(100) NOT NULL,
                name VARCHAR(255) NOT NULL,
                version VARCHAR(50) DEFAULT 'v1.0',
                license_reference VARCHAR(255) DEFAULT 'LICENSE_INFO_UNVERIFIED',
                coverage_scope VARCHAR(50) DEFAULT 'GLOBAL',
                country VARCHAR(100),
                spatial_resolution VARCHAR(100),
                temporal_resolution VARCHAR(100),
                retention_policy VARCHAR(100) DEFAULT 'INDEFINITE',
                schema_version VARCHAR(32) DEFAULT '1.0.0',
                quality_policy VARCHAR(255) DEFAULT 'STANDARD_RANGE_AND_GEO_VALIDATION',
                provenance_policy VARCHAR(255) DEFAULT 'IMMUTABLE_SOURCE_LINEAGE',
                status VARCHAR(50) DEFAULT 'AVAILABLE',
                freshness_threshold_seconds INTEGER DEFAULT 86400,
                last_observation_time TIMESTAMP,
                last_ingestion_time TIMESTAMP,
                record_count BIGINT DEFAULT 0,
                spatial_extent JSON DEFAULT '{}',
                temporal_extent JSON DEFAULT '{}',
                metadata_info JSON DEFAULT '{}'
            );
        """))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_gov_dataset_reg_id ON governed_dataset_registry(dataset_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_gov_dataset_reg_provider ON governed_dataset_registry(provider);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_gov_dataset_reg_status ON governed_dataset_registry(status);"))

        # 5. Ingestion Checkpoints Table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS ingestion_checkpoints (
                id VARCHAR(36) PRIMARY KEY,
                checkpoint_key VARCHAR(128) UNIQUE NOT NULL,
                provider VARCHAR(100) NOT NULL,
                dataset VARCHAR(100) NOT NULL,
                last_successful_observation_time TIMESTAMP,
                last_successful_source_record_id VARCHAR(255),
                last_successful_batch_id VARCHAR(64),
                cursor_state JSON DEFAULT '{}',
                updated_at TIMESTAMP NOT NULL
            );
        """))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_checkpoint_key ON ingestion_checkpoints(checkpoint_key);"))

        # 6. Seed Authoritative Dataset Registry
        seed_datasets = [
            {
                "dataset_id": "NASA_FIRMS_VIIRS_NRT",
                "provider": "NASA_FIRMS",
                "name": "NASA FIRMS VIIRS Near-Real-Time Active Fire Detections",
                "version": "NRT v2.0",
                "license_reference": "NASA Open Data Policy (Public Domain)",
                "coverage_scope": "GLOBAL",
                "country": "GLOBAL",
                "spatial_resolution": "375m (I-Band 375m / M-Band 750m)",
                "temporal_resolution": "12-hour orbital revisit (Suomi-NPP, NOAA-20, NOAA-21)",
                "retention_policy": "INDEFINITE",
                "quality_policy": "FRP_RANGE_AND_GEO_VALIDATION",
                "provenance_policy": "IMMUTABLE_SOURCE_LINEAGE",
                "status": "AVAILABLE",
                "freshness_threshold_seconds": 43200,  # 12 hours
                "metadata_info": '{"sensors": ["VIIRS_NOAA20", "VIIRS_NOAA21", "VIIRS_SNPP"], "orbit": "POLAR"}'
            },
            {
                "dataset_id": "NASA_FIRMS_MODIS_NRT",
                "provider": "NASA_FIRMS",
                "name": "NASA FIRMS MODIS Thermal Anomalies",
                "version": "Collection 6.1",
                "license_reference": "NASA Open Data Policy (Public Domain)",
                "coverage_scope": "GLOBAL",
                "country": "GLOBAL",
                "spatial_resolution": "1000m nadir",
                "temporal_resolution": "12-hour orbital revisit (Terra / Aqua)",
                "retention_policy": "INDEFINITE",
                "quality_policy": "STANDARD_MODIS_QUALITY_FLAGS",
                "provenance_policy": "IMMUTABLE_SOURCE_LINEAGE",
                "status": "AVAILABLE",
                "freshness_threshold_seconds": 43200,
                "metadata_info": '{"sensors": ["MODIS_TERRA", "MODIS_AQUA"], "orbit": "POLAR"}'
            },
            {
                "dataset_id": "COPERNICUS_SENTINEL3_SLSTR_FRP",
                "provider": "COPERNICUS_SLSTR",
                "name": "Copernicus Sentinel-3 SLSTR NRT Fire Radiative Power",
                "version": "SLSTR L2 FRP v2.1",
                "license_reference": "Copernicus Open Access Policy",
                "coverage_scope": "GLOBAL",
                "country": "GLOBAL",
                "spatial_resolution": "1000m SLSTR nadir",
                "temporal_resolution": "Daily dual-satellite revisit (Sentinel-3A/3B)",
                "retention_policy": "INDEFINITE",
                "quality_policy": "COPERNICUS_L2_QUALITY_SCREENING",
                "provenance_policy": "IMMUTABLE_SOURCE_LINEAGE",
                "status": "AVAILABLE",
                "freshness_threshold_seconds": 86400,
                "metadata_info": '{"satellites": ["Sentinel-3A", "Sentinel-3B"]}'
            },
            {
                "dataset_id": "MOSDAC_INSAT3D_TIR_HOTSPOT",
                "provider": "ISRO_MOSDAC",
                "name": "ISRO MOSDAC INSAT-3D/3DR Geostationary Thermal Hotspots",
                "version": "MOSDAC FIR v1.0",
                "license_reference": "ISRO MOSDAC Data Policy",
                "coverage_scope": "REGIONAL",
                "country": "INDIA_OCEAN_RIM",
                "spatial_resolution": "4000m TIR Geostationary",
                "temporal_resolution": "15-minute rapid scan cadence",
                "retention_policy": "INDEFINITE",
                "quality_policy": "MOSDAC_HOTSPOT_FLAG_VALIDATION",
                "provenance_policy": "IMMUTABLE_SOURCE_LINEAGE",
                "status": "AVAILABLE",
                "freshness_threshold_seconds": 7200,  # 2 hours
                "metadata_info": '{"satellites": ["INSAT-3D", "INSAT-3DR"], "orbit": "GEOSTATIONARY"}'
            },
            {
                "dataset_id": "NOAA_GOES_ABI_FDCA",
                "provider": "NOAA_GOES",
                "name": "NOAA GOES-16/18 ABI Fire/Hotspot Characterization (FDCA)",
                "version": "ABI L2 FDCA v2.0",
                "license_reference": "NOAA Open Data Policy",
                "coverage_scope": "REGIONAL",
                "country": "AMERICAS",
                "spatial_resolution": "2000m nadir",
                "temporal_resolution": "5-10 minute cadence",
                "retention_policy": "INDEFINITE",
                "quality_policy": "NOAA_FDCA_QUALITY_MASKS",
                "provenance_policy": "IMMUTABLE_SOURCE_LINEAGE",
                "status": "NOT_CONFIGURED",
                "freshness_threshold_seconds": 3600,
                "metadata_info": '{"orbit": "GEOSTATIONARY", "note": "Restricted to Western Hemisphere; not configured for Indian subcontinent"}'
            },
            {
                "dataset_id": "OPENSTREETMAP_INDUSTRIAL_REGISTRY",
                "provider": "OSM",
                "name": "OpenStreetMap Industrial Facilities & Infrastructure",
                "version": "OSM Planet Snapshot",
                "license_reference": "Open Database License (ODbL 1.0)",
                "coverage_scope": "GLOBAL",
                "country": "GLOBAL",
                "spatial_resolution": "Vector (Points / Polygons)",
                "temporal_resolution": "Continuous Crowdsourced / Quarterly Snapshot",
                "retention_policy": "INDEFINITE",
                "quality_policy": "TOPOLOGY_AND_TAG_VALIDATION",
                "provenance_policy": "IMMUTABLE_SOURCE_LINEAGE",
                "status": "AVAILABLE",
                "freshness_threshold_seconds": 7776000,  # 90 days
                "metadata_info": '{"tags": ["industrial", "power", "refinery", "chemical"]}'
            },
            {
                "dataset_id": "CENTRAL_ELECTRICITY_AUTHORITY_POWER_REGISTRY",
                "provider": "CEA",
                "name": "Central Electricity Authority (CEA) Power Station Database",
                "version": "CEA 2024-2025",
                "license_reference": "National Data Sharing and Accessibility Policy (NDSAP)",
                "coverage_scope": "NATIONAL",
                "country": "INDIA",
                "spatial_resolution": "Plant / Sub-district Coordinate Vectors",
                "temporal_resolution": "Annual Survey",
                "retention_policy": "INDEFINITE",
                "quality_policy": "OFFICIAL_SURVEY_CROSS_VERIFICATION",
                "provenance_policy": "IMMUTABLE_SOURCE_LINEAGE",
                "status": "AVAILABLE",
                "freshness_threshold_seconds": 31536000,  # 1 year
                "metadata_info": '{"jurisdiction": "National Purview", "coverage": "Utilities and thermal stations"}'
            },
            {
                "dataset_id": "MOEFCC_PARIVESH_ENVIRONMENTAL_CLEARANCES",
                "provider": "PARIVESH",
                "name": "MoEFCC PARIVESH Environmental & CRZ Clearances",
                "version": "MoEFCC Portal 2024",
                "license_reference": "MoEFCC Public Regulatory Filings",
                "coverage_scope": "PARTIAL",
                "country": "INDIA",
                "spatial_resolution": "Project Site Centroids",
                "temporal_resolution": "Event-driven filings",
                "retention_policy": "INDEFINITE",
                "quality_policy": "STATUTORY_PROPOSAL_VERIFICATION",
                "provenance_policy": "IMMUTABLE_SOURCE_LINEAGE",
                "status": "PARTIAL",
                "freshness_threshold_seconds": 2592000,  # 30 days
                "metadata_info": '{"limitations": "Partial coverage; statutory filings only; pre-2006 clearances excluded"}'
            },
            {
                "dataset_id": "INDIAN_BUREAU_OF_MINES_LEASE_BULLETIN",
                "provider": "IBM",
                "name": "Indian Bureau of Mines (IBM) Mining Leases & Minerals",
                "version": "IBM Bulletin 2024",
                "license_reference": "NDSAP / Ministry of Mines Publications",
                "coverage_scope": "NATIONAL",
                "country": "INDIA",
                "spatial_resolution": "District / Mineral Aggregate Vectors",
                "temporal_resolution": "Annual Bulletin",
                "retention_policy": "INDEFINITE",
                "quality_policy": "MINES_BULLETIN_AUDIT",
                "provenance_policy": "IMMUTABLE_SOURCE_LINEAGE",
                "status": "AVAILABLE",
                "freshness_threshold_seconds": 31536000,
                "metadata_info": '{"scope": "Major and minor mineral lease inventories"}'
            },
            {
                "dataset_id": "BHUVAN_LULC_THEMATIC_MAPS",
                "provider": "ISRO_BHUVAN",
                "name": "ISRO Bhuvan Thematic Land Use / Land Cover (LULC)",
                "version": "ISRO LULC Cycle 4",
                "license_reference": "Bhuvan Open Data Services",
                "coverage_scope": "NATIONAL",
                "country": "INDIA",
                "spatial_resolution": "30m Grid (1:50,000)",
                "temporal_resolution": "Multi-year Land Use Cycle",
                "retention_policy": "INDEFINITE",
                "quality_policy": "REMOTE_SENSING_ACCURACY_ASSESSMENT",
                "provenance_policy": "IMMUTABLE_SOURCE_LINEAGE",
                "status": "AVAILABLE",
                "freshness_threshold_seconds": 94608000,  # 3 years
                "metadata_info": '{"classes": 25, "raster_grid": "30m"}'
            },
            {
                "dataset_id": "FSI_ISFR_PROTECTED_AREAS",
                "provider": "FSI",
                "name": "Forest Survey of India (FSI) State of Forest & Protected Areas",
                "version": "ISFR 2023-2024",
                "license_reference": "Ministry of Environment, Forest and Climate Change (NDSAP)",
                "coverage_scope": "NATIONAL",
                "country": "INDIA",
                "spatial_resolution": "Vector Gazette Boundaries / ESZ Zones",
                "temporal_resolution": "Biennial Survey",
                "retention_policy": "INDEFINITE",
                "quality_policy": "GAZETTE_NOTIFICATION_VERIFICATION",
                "provenance_policy": "IMMUTABLE_SOURCE_LINEAGE",
                "status": "AVAILABLE",
                "freshness_threshold_seconds": 63072000,  # 2 years
                "metadata_info": '{"categories": ["National Park", "Wildlife Sanctuary", "Tiger Reserve", "ESZ"]}'
            },
            {
                "dataset_id": "IMD_GROUND_MESONET_ARCHIVE",
                "provider": "REGIONAL_SURFACE_METEOROLOGY",
                "name": "Regional Surface Meteorological Mesonet Stations",
                "version": "DEMO_FIXTURE_v1.0",
                "license_reference": "LICENSE_INFO_UNVERIFIED",
                "coverage_scope": "PARTIAL",
                "country": "INDIA",
                "spatial_resolution": "Point Observation Stations",
                "temporal_resolution": "Hourly",
                "retention_policy": "INDEFINITE",
                "quality_policy": "STATION_SENSOR_QUALITY_BOUNDS",
                "provenance_policy": "IMMUTABLE_SOURCE_LINEAGE",
                "status": "PARTIAL",
                "freshness_threshold_seconds": 86400,
                "metadata_info": '{"fixture": true, "note": "Regional ground stations active; broader grid unconfigured"}'
            },
            {
                "dataset_id": "ECMWF_ERA5_ATMOSPHERIC_REANALYSIS",
                "provider": "ECMWF_WEATHER",
                "name": "ECMWF ERA5 Atmospheric Reanalysis Grids",
                "version": "ERA5 HRES",
                "license_reference": "Copernicus Climate Change Service License",
                "coverage_scope": "GLOBAL",
                "country": "GLOBAL",
                "spatial_resolution": "31km Grid / 0.25 deg",
                "temporal_resolution": "Hourly Reanalysis",
                "retention_policy": "INDEFINITE",
                "quality_policy": "ECMWF_DATA_ASSIMILATION_QUALITY",
                "provenance_policy": "IMMUTABLE_SOURCE_LINEAGE",
                "status": "NOT_CONFIGURED",
                "freshness_threshold_seconds": 43200,
                "metadata_info": '{"status": "NOT_CONFIGURED", "note": "Pipeline not configured in active environment. Zero synthetic data fabricated."}'
            },
            {
                "dataset_id": "NOAA_GFS_GLOBAL_METEOROLOGY",
                "provider": "NOAA_GFS",
                "name": "NOAA Global Forecast System (GFS) Numerical Weather Prediction",
                "version": "GFS v16",
                "license_reference": "NOAA Open Data Policy",
                "coverage_scope": "GLOBAL",
                "country": "GLOBAL",
                "spatial_resolution": "28km Grid / 0.25 deg",
                "temporal_resolution": "6-hour forecast cycle",
                "retention_policy": "INDEFINITE",
                "quality_policy": "NCEP_MODEL_CONVERGENCE_CHECKS",
                "provenance_policy": "IMMUTABLE_SOURCE_LINEAGE",
                "status": "NOT_CONFIGURED",
                "freshness_threshold_seconds": 21600,
                "metadata_info": '{"status": "NOT_CONFIGURED", "note": "Pipeline not configured in active environment. Zero synthetic data fabricated."}'
            },
            {
                "dataset_id": "CAMS_GLOBAL_ATMOSPHERIC_COMPOSITION",
                "provider": "COPERNICUS_ATMOSPHERIC",
                "name": "Copernicus Atmosphere Monitoring Service (CAMS) Atmospheric Composition",
                "version": "CAMS NRT L4",
                "license_reference": "Copernicus Atmosphere Monitoring Service License",
                "coverage_scope": "GLOBAL",
                "country": "GLOBAL",
                "spatial_resolution": "40km Grid / 0.4 deg",
                "temporal_resolution": "3-hour forecast",
                "retention_policy": "INDEFINITE",
                "quality_policy": "CAMS_COMPOSITION_QUALITY",
                "provenance_policy": "IMMUTABLE_SOURCE_LINEAGE",
                "status": "NOT_CONFIGURED",
                "freshness_threshold_seconds": 43200,
                "metadata_info": '{"status": "NOT_CONFIGURED", "note": "Pipeline not configured in active environment. Zero synthetic data fabricated."}'
            },
            {
                "dataset_id": "COPERNICUS_SENTINEL2_MSI_L2A",
                "provider": "SENTINEL2_OPTICAL",
                "name": "Copernicus Sentinel-2 MSI Multi-Spectral Surface Reflectance",
                "version": "Sentinel-2 L2A",
                "license_reference": "Copernicus Open Access Policy",
                "coverage_scope": "GLOBAL",
                "country": "GLOBAL",
                "spatial_resolution": "10m, 20m, 60m bands",
                "temporal_resolution": "5-day revisit (2A / 2B)",
                "retention_policy": "INDEFINITE",
                "quality_policy": "SCENE_CLASSIFICATION_AND_CLOUD_MASK",
                "provenance_policy": "IMMUTABLE_SOURCE_LINEAGE",
                "status": "NOT_CONFIGURED",
                "freshness_threshold_seconds": 432000,  # 5 days
                "metadata_info": '{"status": "NOT_CONFIGURED", "note": "High-resolution optical pipeline unconfigured. Zero synthetic imagery fabricated."}'
            },
            {
                "dataset_id": "COPERNICUS_SENTINEL1_GRD_CSAR",
                "provider": "SENTINEL1_SAR",
                "name": "Copernicus Sentinel-1 C-SAR Ground Range Detected (GRD)",
                "version": "Sentinel-1 GRD L1",
                "license_reference": "Copernicus Open Access Policy",
                "coverage_scope": "GLOBAL",
                "country": "GLOBAL",
                "spatial_resolution": "10m SAR resolution",
                "temporal_resolution": "6-12 day revisit",
                "retention_policy": "INDEFINITE",
                "quality_policy": "SAR_RADIOMETRIC_CALIBRATION",
                "provenance_policy": "IMMUTABLE_SOURCE_LINEAGE",
                "status": "NOT_CONFIGURED",
                "freshness_threshold_seconds": 518400,  # 6 days
                "metadata_info": '{"status": "NOT_CONFIGURED", "note": "Cloud-penetrating SAR radar pipeline unconfigured. Zero synthetic radar backscatter fabricated."}'
            },
            {
                "dataset_id": "PLANET_WORLDVIEW_SUBMETER_CONSTELLATION",
                "provider": "PLANET_WORLDVIEW_HIGH_RES",
                "name": "Commercial Sub-Meter High-Resolution Optical Tasking",
                "version": "Commercial Optical v1",
                "license_reference": "LICENSE_INFO_UNVERIFIED",
                "coverage_scope": "GLOBAL",
                "country": "GLOBAL",
                "spatial_resolution": "Sub-meter (< 0.5m)",
                "temporal_resolution": "Tasking on-demand",
                "retention_policy": "COMMERCIAL_RESTRICTED",
                "quality_policy": "STEREO_ORTHORECTIFICATION_QUALITY",
                "provenance_policy": "IMMUTABLE_SOURCE_LINEAGE",
                "status": "NOT_CONFIGURED",
                "freshness_threshold_seconds": 86400,
                "metadata_info": '{"status": "NOT_CONFIGURED", "note": "Commercial high-resolution satellite tasking not configured."}'
            }
        ]

        import uuid
        for ds in seed_datasets:
            check_sql = text("SELECT id FROM governed_dataset_registry WHERE dataset_id = :d_id;")
            existing = conn.execute(check_sql, {"d_id": ds["dataset_id"]}).first()
            if not existing:
                insert_sql = text("""
                    INSERT INTO governed_dataset_registry (
                        id, dataset_id, provider, name, version, license_reference,
                        coverage_scope, country, spatial_resolution, temporal_resolution,
                        retention_policy, quality_policy, provenance_policy, status,
                        freshness_threshold_seconds, metadata_info
                    ) VALUES (
                        :id, :dataset_id, :provider, :name, :version, :license_reference,
                        :coverage_scope, :country, :spatial_resolution, :temporal_resolution,
                        :retention_policy, :quality_policy, :provenance_policy, :status,
                        :freshness_threshold_seconds, :metadata_info
                    );
                """)
                conn.execute(insert_sql, {
                    "id": str(uuid.uuid4()),
                    "dataset_id": ds["dataset_id"],
                    "provider": ds["provider"],
                    "name": ds["name"],
                    "version": ds["version"],
                    "license_reference": ds["license_reference"],
                    "coverage_scope": ds["coverage_scope"],
                    "country": ds["country"],
                    "spatial_resolution": ds["spatial_resolution"],
                    "temporal_resolution": ds["temporal_resolution"],
                    "retention_policy": ds["retention_policy"],
                    "quality_policy": ds["quality_policy"],
                    "provenance_policy": ds["provenance_policy"],
                    "status": ds["status"],
                    "freshness_threshold_seconds": ds["freshness_threshold_seconds"],
                    "metadata_info": ds["metadata_info"]
                })

    print("[+] Phase 16 Data Governance Migration completed successfully.")


if __name__ == "__main__":
    migrate()
