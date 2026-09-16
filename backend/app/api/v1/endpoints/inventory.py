"""
AGNI-NETRA — India Dataset Inventory & Quality Audit API Endpoints
Phase 18: Strict India-First Operating Scope
"""

from typing import Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.services.data_plane.india_dataset_inventory import india_dataset_inventory

router = APIRouter()


@router.get("/india-datasets")
def get_india_datasets_inventory(
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Returns canonical inventory of all India operational, derived, fixture,
    and unconfigured datasets with complete provenance and coverage scopes.
    """
    return india_dataset_inventory.get_canonical_dataset_inventory(db)


@router.get("/quality-audit")
def get_india_data_quality_audit(
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Returns rigorous data quality audit results across all active India datasets,
    evaluating coordinate validity, leakage, duplicates, and timestamp consistency.
    """
    return india_dataset_inventory.run_india_data_quality_audit(db)


@router.get("/coverage-scorecard")
def get_india_coverage_scorecard(
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Returns the authoritative 11-point India Coverage & Readiness Scorecard.
    """
    return india_dataset_inventory.get_india_coverage_scorecard(db)


@router.get("/coverage-registry")
def get_data_coverage_registry() -> Dict[str, Any]:
    """
    Returns Phase 25 full Data Coverage Registry across all 18+ satellite, terrestrial,
    geospatial, and administrative feeds with explicit statuses (AVAILABLE, DERIVED,
    UNAVAILABLE, NOT_CONFIGURED) and no synthetic mock numbers.
    """
    from backend.app.services.data_plane.data_coverage_registry import data_coverage_registry
    records = data_coverage_registry.get_coverage_registry()
    status_counts = {}
    for r in records:
        status_counts[r.current_status.value] = status_counts.get(r.current_status.value, 0) + 1
    return {
        "total_feeds": len(records),
        "summary": status_counts,
        "records": [r.model_dump() for r in records]
    }



