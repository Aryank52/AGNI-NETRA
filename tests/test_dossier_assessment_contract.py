"""
Unit and Integration Tests for Event Investigation Dossier Assessment Normalization.
Verifies that all possible backend response shapes for `why_this_assessment` / `assessment`
are safely handled without throwing runtime TypeError (.map is not a function).
"""

import pytest
from typing import Any, List, Dict, Optional


def normalize_assessment_items(val: Any) -> List[str]:
    """
    Python equivalent of frontend/src/lib/formatters.ts: normalizeAssessmentItems
    Handles array, string, dict, None, and unexpected primitives safely.
    """
    if val is None:
        return []
    if isinstance(val, list):
        return [str(item) for item in val if item is not None and str(item).strip()]
    if isinstance(val, str):
        trimmed = val.strip()
        return [trimmed] if trimmed else []
    if isinstance(val, dict):
        # 1. Check for common array keys
        for key in ["items", "reasons", "points", "bullets", "findings"]:
            nested = val.get(key)
            if isinstance(nested, list) and nested:
                return [str(item) for item in nested if item is not None and str(item).strip()]

        # 2. Check for structured explanation
        struct = val.get("structured_explanation")
        if isinstance(struct, list) and struct:
            return [str(item) for item in struct if item is not None and str(item).strip()]
        if isinstance(struct, str) and struct.strip():
            return [struct.strip()]

        # 3. Check for single string text fields
        for key in ["summary", "text", "description", "assessment", "rationale"]:
            s = val.get(key)
            if isinstance(s, str) and s.strip():
                return [s.strip()]

        return []
    return [str(val)]


def normalize_assessment_summary(val: Any, default_text: str = "No structured assessment provided.") -> str:
    """
    Python equivalent of frontend/src/lib/formatters.ts: normalizeAssessmentSummary
    """
    if val is None:
        return default_text
    if isinstance(val, str):
        trimmed = val.strip()
        return trimmed if trimmed else default_text
    if isinstance(val, list):
        filtered = [str(item).strip() for item in val if item is not None and str(item).strip()]
        return " ".join(filtered) if filtered else default_text
    if isinstance(val, dict):
        for key in ["summary", "text", "description", "assessment", "title", "rationale"]:
            s = val.get(key)
            if isinstance(s, str) and s.strip():
                return s.strip()
        items = normalize_assessment_items(val)
        return " ".join(items) if items else default_text
    return str(val)


# ============================================================================
# Unit Tests for Normalization Contracts
# ============================================================================

def test_normalize_array_of_strings():
    data = ["High FRP observed", "Nearby refinery detected", "Risk tier critical"]
    res = normalize_assessment_items(data)
    assert res == data
    assert normalize_assessment_summary(data) == "High FRP observed Nearby refinery detected Risk tier critical"


def test_normalize_plain_string():
    data = "High FRP observed near petrochemical complex."
    res = normalize_assessment_items(data)
    assert res == [data]
    assert normalize_assessment_summary(data) == data


def test_normalize_dict_with_items_list():
    data = {
        "summary": "Industrial flare anomaly",
        "items": ["Peak FRP 285MW", "182m from refinery", "Candidate XGBoost prediction"]
    }
    items = normalize_assessment_items(data)
    assert len(items) == 3
    assert "Peak FRP 285MW" in items
    assert normalize_assessment_summary(data) == "Industrial flare anomaly"


def test_normalize_dict_with_reasons_list():
    data = {
        "reasons": ["Unusual persistence > 4 hours", "Exceeds 90-day baseline by 2.4 sigma"]
    }
    items = normalize_assessment_items(data)
    assert len(items) == 2
    assert "Unusual persistence > 4 hours" in items
    assert "Exceeds 90-day baseline by 2.4 sigma" in normalize_assessment_summary(data)


def test_normalize_dict_with_structured_explanation():
    data = {
        "structured_explanation": [
            "Thermal flux verified via VIIRS 375m",
            "No cloud cover obstruction detected"
        ]
    }
    items = normalize_assessment_items(data)
    assert len(items) == 2
    assert "Thermal flux verified via VIIRS 375m" in items


def test_normalize_dict_with_only_summary():
    data = {"summary": "Severe thermal signature in Jamnagar"}
    items = normalize_assessment_items(data)
    assert items == ["Severe thermal signature in Jamnagar"]
    assert normalize_assessment_summary(data) == "Severe thermal signature in Jamnagar"


def test_normalize_none_and_empty():
    assert normalize_assessment_items(None) == []
    assert normalize_assessment_items([]) == []
    assert normalize_assessment_items("") == []
    assert normalize_assessment_items({}) == []
    assert normalize_assessment_summary(None) == "No structured assessment provided."
    assert normalize_assessment_summary("") == "No structured assessment provided."
    assert normalize_assessment_summary({}) == "No structured assessment provided."


def test_normalize_numeric_or_unexpected_primitives():
    assert normalize_assessment_items(42) == ["42"]
    assert normalize_assessment_summary(42) == "42"


def test_normalize_nested_none_items():
    data = ["Valid item", None, "", "   ", "Another valid item"]
    items = normalize_assessment_items(data)
    assert items == ["Valid item", "Another valid item"]
