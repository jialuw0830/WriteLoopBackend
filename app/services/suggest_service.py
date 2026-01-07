# app/services/suggest_service.py
import json
import re
from app.services.llm_client import client, OPENAI_MODEL
from app.services.rag_retriever import retrieve_similar_continuations


def generate_suggestions(text: str, cursor: dict, read_essay_ids: list = None) -> str:
    """
    Generate 3 high-quality, academically appropriate ENGLISH PHRASES 
    that can naturally follow the user's current text.

    - Input: full text (we use last ~100 chars as context)
    - Output: 3 phrases (2-8 words), with explanations, in JSON
    """
    if not text.strip():
        return json.dumps({"suggestions": []})

    # Use last 100 characters as context to avoid token overflow
    context = text[-100:].strip()
    
    # 检测当前文本是否以句号结尾（可能是新句子的开始）
    ends_with_period = context.rstrip().endswith('.') or context.rstrip().endswith('。')
    # 也检测是否是句子中间（包含句号但后面还有内容）
    has_period_in_middle = '.' in context[:-10] or '。' in context[:-10]

    # Retrieve relevant examples based on reading history for RAG enhancement
    retrieved_examples = retrieve_similar_continuations(context, top_k=3, read_essay_ids=read_essay_ids)

    # Build strong-constraint prompt
    if ends_with_period:
        # 如果以句号结尾，应该生成完整的新句子
        sentence_type_instruction = """
    SITUATION: The current text ends with a period (.), meaning the student has just finished a sentence.
    Your suggestions should be COMPLETE NEW SENTENCES (with subject-verb-object structure), not continuations.
    
    RULES FOR NEW SENTENCES:
    1. Each suggestion must be a COMPLETE SENTENCE with clear subject-verb-object structure.
    2. Sentence length: 6-15 words (not just phrases).
    3. Start with varied sentence structures:
       - Some can start with subjects: "This approach offers several advantages."
       - Some can start with transitional phrases: "Furthermore, evidence suggests that..."
       - Some can start with participial phrases: "Examining this issue reveals..."
       - Some can start with prepositional phrases: "In contrast, alternative methods..."
    4. DO NOT always use relative clauses (which/that) — diversify the sentence structures.
    5. Ensure each sentence has a clear subject and predicate."""
    else:
        # 如果不在句号后，可以继续当前句子，但要多样化
        sentence_type_instruction = """
    SITUATION: The student is in the middle of writing a sentence.
    Your suggestions should CONTINUE the current sentence, but DIVERSIFY the structures.
    
    RULES FOR CONTINUATIONS:
    1. Each phrase should be 2-8 words long.
    2. DO NOT always use relative clauses (which/that) — provide variety:
       - Verb phrases: "significantly impacts public health"
       - Prepositional phrases: "through sustainable practices"
       - Infinitive phrases: "to address this challenge"
       - Participial phrases: "leading to better outcomes"
       - Relative clauses (only when grammatically necessary): "which demonstrates the effectiveness"
    3. Ensure at least one suggestion is NOT a relative clause.
    4. Be grammatically compatible with the current sentence structure."""

    prompt = f"""
    You are an IELTS writing coach. The student is composing an academic English essay.

    Current text they have written:
    "{context}"

    They are about to continue writing. Your task is to suggest EXACTLY 3 natural, advanced, and exam-appropriate ENGLISH suggestions 
    that can LOGICALLY and GRAMMATICALLY FOLLOW this text.
    
    {sentence_type_instruction}

    GENERAL RULES (apply to all suggestions):
    1. Use formal, academic vocabulary (Band 7+ or CET-6 level).
    2. NEVER use: "and", "but", "so", "I think", "very", "good", "bad", "help", "make", "thing", "stuff".
    3. If possible, echo the style of these real examples:
    {chr(10).join([f' - "{ex}"' for ex in retrieved_examples])}

    Return a STRICT JSON object with this structure:
    {{
      "suggestions": [
        {{
          "text": "exact suggestion here (complete sentence if after period, or phrase if continuing)",
          "explain": "1-sentence teaching note: why this suggestion is strong AND grammatically correct in context"
        }},
        ...
      ]
    }}
    
    IMPORTANT: Ensure the suggestions are DIVERSIFIED:
    - Do NOT always start with "which" or "that" (relative clauses)
    - Mix different sentence structures (subject-verb-object, participial phrases, transitional phrases, etc.)
    - If after a period, provide complete sentences with clear subject-verb-object structure
    
    DO NOT add any other text, markdown, or explanation outside the JSON.
    """
    try:
        completion = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},  # Enforce JSON
            max_completion_tokens=2000
        )
        result = completion.choices[0].message.content or ""
        result = result.strip()
        if not result:
            raise ValueError("Empty LLM response")

        try:
            parsed = json.loads(result)
        except json.JSONDecodeError:
            # Some models may wrap JSON in extra text; try to extract the JSON object.
            match = re.search(r"\{.*\}", result, re.DOTALL)
            if not match:
                raise
            parsed = json.loads(match.group(0))

        return json.dumps(parsed, ensure_ascii=False)
    except Exception as e:
        print(f"Suggestion generation error: {e}")
        # Fallback: return safe empty response
        return json.dumps({"suggestions": []})
