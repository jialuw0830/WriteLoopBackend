"""
Essay service for IELTS essay reading
"""
import json
import os
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models import Essay


def _essay_to_dict(essay: Essay) -> Dict[str, Any]:
    body_paragraphs = []
    if essay.body_paragraphs:
        try:
            body_paragraphs = json.loads(essay.body_paragraphs)
        except json.JSONDecodeError:
            body_paragraphs = []

    return {
        "essay_number": essay.essay_number,
        "title": essay.title,
        "question": essay.question,
        "word_count_reported": essay.word_count_reported,
        "word_count_actual": essay.word_count_actual,
        "body_paragraphs": body_paragraphs,
        "body_text": essay.body_text or "",
    }


def get_all_essays(db: Session, brief: bool = False, preview_len: int = 200) -> List[Dict[str, Any]]:
    """Get all IELTS essays from DB. Use brief mode to avoid heavy payloads."""
    essays = db.query(Essay).order_by(Essay.essay_number.asc()).all()
    if not brief:
        return [_essay_to_dict(e) for e in essays]

    summaries: List[Dict[str, Any]] = []
    for essay in essays:
        body_text = essay.body_text or ""
        preview = body_text[:preview_len]
        if len(body_text) > preview_len:
            preview += "..."
        summaries.append(
            {
                "essay_number": essay.essay_number,
                "title": essay.title,
                "question": essay.question,
                "word_count_reported": essay.word_count_reported,
                "word_count_actual": essay.word_count_actual,
                "preview": preview,
            }
        )
    return summaries


def get_essay_by_id(db: Session, essay_id: int) -> Dict[str, Any] | None:
    """Get a specific essay by ID from DB."""
    essay = db.query(Essay).filter(Essay.essay_number == essay_id).first()
    return _essay_to_dict(essay) if essay else None


def seed_essays_if_empty(db: Session) -> None:
    """Seed IELTS essays into DB if table is empty."""
    if db.query(Essay).count() > 0:
        return

    data_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "data",
        "IELTS_data.json",
    )
    if not os.path.exists(data_path):
        return

    try:
        with open(data_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return

    essays = data.get("essays", [])
    for essay in essays:
        db.add(
            Essay(
                essay_number=essay.get("essay_number"),
                title=essay.get("title"),
                question=essay.get("question"),
                word_count_reported=essay.get("word_count_reported"),
                word_count_actual=essay.get("word_count_actual"),
                body_paragraphs=json.dumps(essay.get("body_paragraphs", []), ensure_ascii=False),
                body_text=essay.get("body_text", ""),
            )
        )

    db.commit()

