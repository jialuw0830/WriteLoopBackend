"""
Essay service for IELTS essay reading
"""
import json
from typing import List, Dict, Any
from app.data.writing_corpus import get_ielts_essays


def get_all_essays() -> List[Dict[str, Any]]:
    """Get all IELTS essays."""
    return get_ielts_essays()


def get_essay_by_id(essay_id: int) -> Dict[str, Any] | None:
    """Get a specific essay by ID."""
    essays = get_ielts_essays()
    for essay in essays:
        if essay.get("essay_number") == essay_id:
            return essay
    return None



