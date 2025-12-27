# app/services/rag_retriever.py
from app.data.writing_corpus import get_writing_corpus, get_ielts_essays
from typing import List, Optional


def retrieve_similar_continuations(context: str, top_k: int = 3, read_essay_ids: Optional[List[int]] = None) -> list:
    """
    Enhanced keyword-based RAG with IELTS real exam data.
    Retrieves similar sentence continuations from both original corpus and IELTS essays.
    If read_essay_ids is provided, prioritizes sentences from those essays.
    """
    corpus = get_writing_corpus()
    context_lower = context.lower()
    
    # Extract sentences from read essays if reading history is provided
    read_essay_sentences = []
    if read_essay_ids:
        all_essays = get_ielts_essays()
        for essay in all_essays:
            if essay.get("essay_number") in read_essay_ids:
                body_text = essay.get("body_text", "")
                if body_text:
                    # Split into sentences (simple approach: split by period followed by space)
                    sentences = [s.strip() for s in body_text.split(". ") if s.strip()]
                    # Filter meaningful sentences (8-30 words)
                    for sentence in sentences:
                        words = sentence.split()
                        if 8 <= len(words) <= 30:
                            read_essay_sentences.append(sentence)
    
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
    
    # Priority pass: if user has reading history, prioritize sentences from read essays
    if read_essay_sentences:
        for category, words in keywords.items():
            if any(w in context_lower for w in words):
                for sentence in read_essay_sentences:
                    sentence_lower = sentence.lower()
                    if any(kw in sentence_lower for kw in words):
                        if sentence not in matched:
                            matched.append(sentence)
                        if len(matched) >= top_k:
                            return matched[:top_k]
        
        # Second priority: word overlap with read essays
        if len(matched) < top_k:
            context_words = set(context_lower.split())
            scored_sentences = []
            for sentence in read_essay_sentences:
                if sentence in matched:
                    continue
                sentence_words = set(sentence.lower().split())
                overlap = len(context_words & sentence_words)
                if overlap > 0:
                    scored_sentences.append((overlap, sentence))
            
            scored_sentences.sort(reverse=True, key=lambda x: x[0])
            for _, sentence in scored_sentences[:top_k - len(matched)]:
                matched.append(sentence)
                if len(matched) >= top_k:
                    break
    
    # Fallback to original corpus if not enough matches from read essays
    if len(matched) < top_k:
        # First pass: exact keyword matching from corpus
        for category, words in keywords.items():
            if any(w in context_lower for w in words):
                for phrase in corpus:
                    phrase_lower = phrase.lower()
                    if any(kw in phrase_lower for kw in words):
                        if phrase not in matched:
                            matched.append(phrase)
                        if len(matched) >= top_k:
                            return matched[:top_k]

        # Second pass: semantic similarity (simple word overlap) from corpus
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