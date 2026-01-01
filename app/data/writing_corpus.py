# app/data/writing_corpus.py
"""
Mock corpus of IELTS / CET-6 high-scoring sentence continuations.
Each entry is a natural phrase that commonly follows certain contexts.
Now enhanced with IELTS real exam data.
"""
import json
from app.models import SessionLocal, Essay

WRITING_CORPUS = [
    # Technology
    "has revolutionized the way we communicate and work",
    "brings both unprecedented opportunities and significant challenges",
    "can lead to social isolation if not used responsibly",
    "enhances learning efficiency through personalized content",

    # Environment
    "requires immediate action from governments and individuals alike",
    "is a pressing global issue that demands collective efforts",
    "can be mitigated through sustainable practices and innovation",
    "poses a serious threat to biodiversity and ecosystem stability",

    # Education
    "fosters critical thinking and independent learning skills",
    "should emphasize practical application over rote memorization",
    "plays a pivotal role in shaping future societal leaders",
    "must be accessible to all regardless of socioeconomic background",

    # Society / Policy
    "calls for comprehensive legislation and public awareness campaigns",
    "is instrumental in promoting social equity and justice",
    "can significantly reduce inequality if properly implemented",
    "demands a balanced approach between freedom and regulation",

    # General Academic
    "is supported by a growing body of empirical evidence",
    "remains a subject of intense debate among scholars",
    "can be attributed to a confluence of historical and economic factors",
    "warrants further investigation to fully understand its implications",
    "is widely regarded as a cornerstone of modern society"
]


def _load_ielts_data():
    """Load IELTS real exam essays from DB and extract sentence fragments."""
    db = SessionLocal()
    try:
        essays = db.query(Essay).order_by(Essay.essay_number.asc()).all()
        phrases = []
        for essay in essays:
            body_text = essay.body_text or ""
            if body_text:
                sentences = [s.strip() for s in body_text.split(". ") if s.strip()]
                for sentence in sentences:
                    words = sentence.split()
                    if 8 <= len(words) <= 30:
                        phrases.append(sentence)
        return phrases
    except Exception as e:
        print(f"Failed to load IELTS data from DB: {e}")
        return []
    finally:
        db.close()


# Cache for combined writing corpus to avoid repeated file reads
_writing_corpus_cache = None

def get_writing_corpus():
    """Get combined corpus: original phrases + IELTS real exam sentences. Uses caching for performance."""
    global _writing_corpus_cache

    # Return cached data if available
    if _writing_corpus_cache is not None:
        return _writing_corpus_cache

    ielts_phrases = _load_ielts_data()
    _writing_corpus_cache = WRITING_CORPUS + ielts_phrases
    return _writing_corpus_cache


# Cache for IELTS essays to avoid repeated file reads
_ielts_essays_cache = None

def get_ielts_essays():
    """Get full IELTS essays for reference in logic analysis. Uses caching for performance."""
    global _ielts_essays_cache
    
    # Return cached data if available
    if _ielts_essays_cache is not None:
        return _ielts_essays_cache
    
    db = SessionLocal()
    try:
        essays = db.query(Essay).order_by(Essay.essay_number.asc()).all()
        results = []
        for essay in essays:
            body_paragraphs = []
            if essay.body_paragraphs:
                try:
                    body_paragraphs = json.loads(essay.body_paragraphs)
                except json.JSONDecodeError:
                    body_paragraphs = []
            results.append(
                {
                    "essay_number": essay.essay_number,
                    "title": essay.title,
                    "question": essay.question,
                    "word_count_reported": essay.word_count_reported,
                    "word_count_actual": essay.word_count_actual,
                    "body_paragraphs": body_paragraphs,
                    "body_text": essay.body_text or "",
                }
            )
        _ielts_essays_cache = results
        return _ielts_essays_cache
    except Exception as e:
        print(f"Failed to load IELTS essays from DB: {e}")
        _ielts_essays_cache = []
        return []
    finally:
        db.close()
