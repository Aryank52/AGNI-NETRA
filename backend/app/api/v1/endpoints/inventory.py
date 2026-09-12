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
