"""
AGNI-NETRA — Authoritative Jurisdiction & Emergency Authority Registry Service
Proactive Fire Prevention Extension

Resolves verified responsible regulatory, safety, environmental, and emergency authorities
for any thermal event location and industrial jurisdiction.
Strict Anti-Fabrication Rule: Zero synthetic contacts. Resolves strictly from configured records.
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_

from backend.app.models.domain import AuthorityDirectoryRecord, ThermalEvent, IndustrialFacility


class AuthorityRegistryService:
    """
    Authoritative service resolving verified jurisdictions and regulatory bodies
    for proactive fire prevention dossiers and formal delivery pipelines.
    """

    @classmethod
    def resolve_authorities(
        cls,
        db: Session,
        state: Optional[str] = None,
        district: Optional[str] = None,
        facility: Optional[IndustrialFacility] = None,
        categories: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Resolves responsible authorities matching the state, district, or facility jurisdiction.
        Falls back gracefully to state and national disaster management when local records are specific.
        """
        query = db.query(AuthorityDirectoryRecord).filter(AuthorityDirectoryRecord.is_verified == True)

        conditions = []
        if state:
            conditions.append(AuthorityDirectoryRecord.state.ilike(f"%{state}%"))
        if district:
            conditions.append(AuthorityDirectoryRecord.district.ilike(f"%{district}%"))
        conditions.append(AuthorityDirectoryRecord.state == "National")

        if conditions:
            query = query.filter(or_(*conditions))

        if categories:
            query = query.filter(AuthorityDirectoryRecord.category.in_(categories))

        records = query.all()

        results = []
        for r in records:
            # Check jurisdiction match relevance
            is_district_match = bool(district and r.district and r.district.lower() == district.lower())
            is_state_match = bool(state and r.state and r.state.lower() == state.lower())
            is_national = (r.state == "National")

            # Facility operator match
            is_facility_match = False
            if facility and r.category == "FACILITY_OPERATOR":
                fac_name = (facility.name or "").lower()
                rec_name = r.name.lower()
                if any(w in rec_name for w in ["reliance", "jamnagar"] if w in fac_name):
                    is_facility_match = True

            relevance = "HIGH" if (is_district_match or is_facility_match) else ("MEDIUM" if is_state_match else "ESCALATION")

            results.append({
                "id": r.id,
                "name": r.name,
                "category": r.category,
                "state": r.state,
                "district": r.district,
                "jurisdiction": r.jurisdiction,
                "contact_role": r.contact_role,
                "official_endpoint": r.official_endpoint,
                "relevance": relevance,
                "is_verified": r.is_verified
            })

        # Sort: HIGH first, then MEDIUM, then ESCALATION
        sort_order = {"HIGH": 0, "MEDIUM": 1, "ESCALATION": 2}
        results.sort(key=lambda x: sort_order.get(x["relevance"], 3))
        return results

    @classmethod
    def get_authority_by_id(cls, db: Session, authority_id: str) -> Optional[AuthorityDirectoryRecord]:
        return db.query(AuthorityDirectoryRecord).filter(AuthorityDirectoryRecord.id == authority_id).first()


authority_registry_service = AuthorityRegistryService()
