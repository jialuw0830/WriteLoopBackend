# app/data/writing_corpus.py
"""
Mock corpus of IELTS / CET-6 high-scoring sentence continuations.
Each entry is a natural phrase that commonly follows certain contexts.
Now enhanced with IELTS real exam data.
"""
import json
import os

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
    """Load IELTS real exam essays and extract sentence fragments."""
    ielts_file = os.path.join(
        os.path.dirname(__file__),
        "IELTS_data.json"
    )
    
    if not os.path.exists(ielts_file):
        return []
    
    try:
        with open(ielts_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        phrases = []
        essays = data.get("essays", [])
        
        for essay in essays:
            # Extract sentences from body paragraphs
            body_text = essay.get("body_text", "")
            if body_text:
                # Split by sentences (simple approach: split by period followed by space)
                sentences = [s.strip() for s in body_text.split(". ") if s.strip()]
                # Take meaningful sentence fragments (8-30 words)
                for sentence in sentences:
                    words = sentence.split()
                    if 8 <= len(words) <= 30:
                        phrases.append(sentence)
        
        return phrases
    except Exception as e:
        print(f"Failed to load IELTS data: {e}")
        return []


def get_writing_corpus():
    """Get combined corpus: original phrases + IELTS real exam sentences."""
    ielts_phrases = _load_ielts_data()
    return WRITING_CORPUS + ielts_phrases


# Cache for IELTS essays to avoid repeated file reads
_ielts_essays_cache = None

def get_ielts_essays():
    """Get full IELTS essays for reference in logic analysis. Uses caching for performance."""
    global _ielts_essays_cache
    
    # Return cached data if available
    if _ielts_essays_cache is not None:
        return _ielts_essays_cache
    
    ielts_file = os.path.join(
        os.path.dirname(__file__),
        "IELTS_data.json"
    )
    
    if not os.path.exists(ielts_file):
        _ielts_essays_cache = []
        return []
    
    try:
        with open(ielts_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        _ielts_essays_cache = data.get("essays", [])
        return _ielts_essays_cache
    except Exception as e:
        print(f"Failed to load IELTS essays: {e}")
        _ielts_essays_cache = []
        return []