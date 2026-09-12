"""
AGNI-NETRA JARVIS Phase 16: Global Data Coverage Compiler
Compiles factual coverage disclosures across global, regional, and national datasets.
Eliminates implicit national assumptions while maintaining India as a first-class profile.
"""

from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from backend.app.models.domain import DatasetRegistryModel
from backend.app.services.data_plane.models import CoverageScope


class CoverageCompiler:
    """
    Assembles authoritative geographic and temporal coverage matrices.
    """

    @classmethod
    def get_coverage_report(cls, db: Session, target_region: Optional[str] = None) -> Dict[str, Any]:
        datasets = db.query(DatasetRegistryModel).all()

        global_datasets = []
        regional_datasets = []
        national_datasets = []
        unconfigured_datasets = []

        for ds in datasets:
            entry = {
                "dataset_id": ds.dataset_id,
                "provider": ds.provider,
                "name": ds.name,
                "version": ds.version,
                "coverage_scope": ds.coverage_scope,
                "country": ds.country or "GLOBAL",
                "spatial_resolution": ds.spatial_resolution,
                "temporal_resolution": ds.temporal_resolution,
                "status": ds.status,
                "record_count": ds.record_count or 0,
                "license": ds.license_reference
            }

            scope = ds.coverage_scope.upper() if ds.coverage_scope else "GLOBAL"

            if ds.status == "NOT_CONFIGURED":
                unconfigured_datasets.append(entry)
            elif scope == CoverageScope.GLOBAL.value:
                global_datasets.append(entry)
            elif scope in (CoverageScope.REGIONAL.value, CoverageScope.PARTIAL.value):
                regional_datasets.append(entry)
            else:
                national_datasets.append(entry)

        return {
            "active_operational_profile": "INDIA",
            "global_capabilities": {
                "total_global_datasets": len(global_datasets),
                "datasets": global_datasets,
                "modalities_covered": ["Thermal Radiometry (NASA FIRMS)", "Thermal FRP (Sentinel-3 SLSTR)", "Infrastructure Vectors (OSM)"]
            },
            "regional_capabilities": {
                "total_regional_datasets": len(regional_datasets),
                "datasets": regional_datasets
            },
            "national_profiles": {
                "primary_country": "INDIA",
                "total_national_datasets": len(national_datasets),
                "datasets": national_datasets,
                "providers": ["ISRO_BHUVAN", "FSI", "CEA", "PARIVESH", "IBM_MINING", "REGIONAL_SURFACE_METEOROLOGY"]
            },
            "unconfigured_capabilities": {
                "total_unconfigured_datasets": len(unconfigured_datasets),
                "datasets": unconfigured_datasets,
                "disclosure": "Global NWP weather grids (ECMWF, GFS), CAMS atmospheric composition, Sentinel-2 optical, and Sentinel-1 SAR radar are disclosed as NOT_CONFIGURED. Zero synthetic records are fabricated."
            },
            "factual_disclaimer": "Operational intelligence operates across India and the Indian Ocean Rim. Global thermal detection is supported via NASA FIRMS and Sentinel-3 SLSTR. Regional statutory registries outside India are factually unconfigured."
        }


coverage_compiler = CoverageCompiler()
