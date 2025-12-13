# app/services/rag_retriever.py
from app.data.writing_corpus import get_writing_corpus


def retrieve_similar_continuations(context: str, top_k: int = 3) -> list:
    """
    Enhanced keyword-based RAG with IELTS real exam data.
    Retrieves similar sentence continuations from both original corpus and IELTS essays.
    """
    corpus = get_writing_corpus()
    context_lower = context.lower()

    # Enhanced keyword matching with more categories
    keywords = {
        'technology': ['technology', 'internet', 'digital', 'online', 'ai', 'app', 'smartphone', 'computer', 'software'],
        'environment': ['environment', 'pollution', 'climate', 'carbon', 'eco', 'green', 'biodiversity', 'species', 'extinction'],
        'education': ['education', 'school', 'student', 'learn', 'teach', 'academic', 'university', 'degree', 'qualification'],
        'society': ['society', 'government', 'policy', 'law', 'people', 'social', 'population', 'community', 'citizen'],
        'health': ['health', 'medical', 'doctor', 'treatment', 'disease', 'healthcare', 'medicine'],
        'economy': ['economy', 'economic', 'business', 'work', 'employment', 'job', 'income', 'money', 'financial'],
        'general': ['important', 'issue', 'problem', 'solution', 'study', 'research', 'benefit', 'advantage', 'disadvantage']
    }

    matched = []
    # First pass: exact keyword matching
    for category, words in keywords.items():
        if any(w in context_lower for w in words):
            for phrase in corpus:
                phrase_lower = phrase.lower()
                # Check if phrase contains relevant keywords
                if any(kw in phrase_lower for kw in words):
                    if phrase not in matched:
                        matched.append(phrase)
                    if len(matched) >= top_k:
                        return matched[:top_k]

    # Second pass: semantic similarity (simple word overlap)
    if len(matched) < top_k:
        context_words = set(context_lower.split())
        scored_phrases = []
        for phrase in corpus:
            if phrase in matched:
                continue
            phrase_words = set(phrase.lower().split())
            # Calculate simple word overlap score
            overlap = len(context_words & phrase_words)
            if overlap > 0:
                scored_phrases.append((overlap, phrase))
        
        # Sort by overlap score and add top matches
        scored_phrases.sort(reverse=True, key=lambda x: x[0])
        for _, phrase in scored_phrases[:top_k - len(matched)]:
            matched.append(phrase)
            if len(matched) >= top_k:
                break

    # Fallback: return general academic phrases
    if len(matched) < top_k:
        general_phrases = [p for p in corpus if any(word in p.lower() for word in ['empirical', 'debate', 'warrants', 'evidence', 'argue', 'conclude'])]
        for phrase in general_phrases:
            if phrase not in matched:
                matched.append(phrase)
                if len(matched) >= top_k:
                    break

    return matched[:top_k]