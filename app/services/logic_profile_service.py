from app.services.llm_client import client, OPENAI_MODEL
from app.data.writing_corpus import get_ielts_essays
from app.services.text_metrics import calculate_ttr, calculate_mlu
from app.models import get_db, UserProfile, PracticeHistory, init_db
from sqlalchemy.orm import Session
from typing import List
import json
import os


def _load_user_profile(user_id: int, db: Session) -> dict:
    """Load existing user profile from database."""
    try:
        profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        if profile and profile.profile_data:
            return json.loads(profile.profile_data)
        return {}
    except Exception as e:
        print(f"Failed to load user profile from database: {e}")
        return {}


def _save_user_profile(user_id: int, profile_data: dict, logic_score: float, text: str, db: Session) -> None:
    """Save user profile to database with metrics and practice history."""
    try:
        # 计算 TTR 和 MLU
        ttr_score = calculate_ttr(text)
        mlu_score = calculate_mlu(text)
        
        # 查找或创建用户画像
        profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        
        if profile:
            # 更新现有画像
            profile.profile_data = json.dumps(profile_data, ensure_ascii=False)
            profile.ttr = ttr_score
            profile.mlu = mlu_score
            profile.logic_score = logic_score
        else:
            # 创建新画像
            profile = UserProfile(
                user_id=user_id,
                profile_data=json.dumps(profile_data, ensure_ascii=False),
                ttr=ttr_score,
                mlu=mlu_score,
                logic_score=logic_score
            )
            db.add(profile)
        
        # 保存练习历史记录
        history = PracticeHistory(
            user_id=user_id,
            logic_score=logic_score,
            ttr=ttr_score,
            mlu=mlu_score
        )
        db.add(history)
        
        db.commit()
    except Exception as e:
        print(f"Failed to save user profile to database: {e}")
        db.rollback()


def analyze_logic_with_profile(text: str, user_id: int = None, db: Session = None) -> str:
    """
    Analyze article logic and update a multi-dimensional user profile.
    This function does NOT generate practice tasks (tasks are generated separately on demand).
    """
    if not text.strip():
        return json.dumps({
            "error": "Empty content",
            "issues": [],
        })

    existing_profile = {}
    if user_id and db:
        existing_profile = _load_user_profile(user_id, db)
    existing_profile_json = json.dumps(existing_profile, ensure_ascii=False)
    
    # Load IELTS reference essays for comparison and examples
    ielts_essays = get_ielts_essays()
    # Select 5-7 relevant essays as reference (provide more examples for better matching)
    reference_essays = ielts_essays[:7] if len(ielts_essays) >= 7 else ielts_essays
    reference_text = ""
    if reference_essays:
        reference_text = "\n\n=== Reference: High-scoring IELTS Model Essays (use these as examples when analyzing) ===\n"
        reference_text += "When you identify a problem in the student's article, you MUST cite a specific example from these essays showing the CORRECT approach.\n\n"
        for i, essay in enumerate(reference_essays, 1):
            reference_text += f"\n【Essay {i}】{essay.get('title', 'Untitled')}\n"
            reference_text += f"Question: {essay.get('question', '')}\n"
            # Show full paragraphs for better reference (truncate only if very long)
            body_paragraphs = essay.get('body_paragraphs', [])
            if body_paragraphs:
                reference_text += "Body paragraphs:\n"
                for j, para in enumerate(body_paragraphs, 1):
                    # Show up to 300 chars per paragraph for better context
                    if len(para) > 300:
                        para_preview = para[:300] + "..."
                    else:
                        para_preview = para
                    reference_text += f"  Para {j}: {para_preview}\n"
            reference_text += "\n"

    prompt = f"""You are a professional academic writing and logic analysis expert and learning coach.
Please carefully analyze the logical structure and language of the following ENGLISH article, 
identify logical flaws, argumentative weaknesses, vocabulary/grammar issues, and areas for improvement.

=== Article content ===
{text}

=== Existing student profile (may be empty on first use) ===
{existing_profile_json}
{reference_text}

Please do THREE things:

1) LOGIC ANALYSIS (article-level)
Analyze from the following aspects:
- Logical Coherence: whether the logical connections between paragraphs and sentences are smooth
- Argument Structure: whether the thesis, evidence, and argumentation process are clear and effective
- Causality: whether causal relationships are reasonable, and whether there are reversed or false causalities
- Evidence Support: whether evidence sufficiently supports the thesis, and whether there is insufficient or irrelevant evidence
- Logical Fallacies: whether there are logical jumps, circular reasoning, hasty generalizations, and other common logical errors

CRITICAL: For EACH identified issue, you MUST provide a concrete example from the IELTS reference essays above that demonstrates the CORRECT way to handle that aspect. This helps the student understand how to improve by seeing real high-scoring examples.

2) USER PROFILE (multi-dimensional, cumulative, CONCRETE)
Based on THIS article and the EXISTING profile, update a concise but SPECIFIC student writing profile from multiple dimensions:
- logic: overall level AND 2–4 typical weak patterns (e.g., "often omits topic sentences in body paragraphs", "frequently confuses cause and effect", NOT just 'weak logic')
- vocabulary: range, precision, AND concrete mistakes (e.g., "overuses basic verbs like 'do/make', rarely uses academic collocations such as 'play a pivotal role in'")
- grammar & sentence structure: concrete recurring problems (e.g., "subject–verb disagreement in third-person singular", "run-on sentences when linking reasons with 'and'")
- structure & coherence: paragraphing and transitions with examples (e.g., "rarely uses contrast transitions such as 'however', 'on the other hand'")

The profile should be stable across sessions: do NOT only describe this one essay, but summarize the student's CURRENT habits and weaknesses.
Use SPECIFIC descriptions and examples instead of vague words like "good/bad/normal". Each *_weak_points field should contain short, concrete bullet points that a student can directly understand.

Return a STRICT JSON object in this format:
{{
  "overall_score": 85,
  "issues": [
    {{
      "type": "Type of logical flaw",
      "location": "Location of the problem (paragraph/sentence description)",
      "description": "Detailed description of the problem",
      "severity": "high",  // or "medium" or "low"
      "example_from_ielts": "A concrete example from the IELTS reference essays showing how this aspect is handled CORRECTLY. Include the essay title and the relevant sentence/paragraph excerpt."
    }}
  ],
  "summary": "Overall logic analysis summary (2–4 sentences).",
  "profile": {{
    "logic_level": "short, concrete description of current logic level",
    "logic_weak_points": ["list of concrete weak patterns"],
    "vocabulary_level": "short, concrete description of vocabulary level",
    "vocabulary_weak_points": ["list of concrete weak patterns"],
    "grammar_level": "short, concrete description of grammar/sentence level",
    "grammar_weak_points": ["list of concrete weak patterns"],
    "structure_level": "short, concrete description of structure & coherence",
    "structure_weak_points": ["list of concrete weak patterns"]
  }}
}}

IMPORTANT RULES:
- Return EXACTLY 3 items in the "issues" array: select the 3 most critical and representative logical flaws.
- For EACH issue, the "example_from_ielts" field MUST contain a real example from the reference essays above. 
  Format: "From [Essay X: Essay Title]: [完整的相关句子或段落，展示正确的处理方式]"
  Example: "From Essay 1: The Purpose of Science: 'In the most obvious sense, science improves lives when it targets urgent human needs. Medical research has reduced suffering through vaccines, antibiotics and safer surgery, while public health science has delivered clean water and better sanitation.'"
- The example should directly demonstrate how to CORRECTLY handle the aspect that the student's article failed at.
- If you cannot find a perfect match, choose the closest relevant example and briefly explain why it's relevant.
- Do NOT include any field named "suggestions" or "tasks" in the response.
- The JSON must be valid and must NOT contain markdown code blocks or comments."""

    try:
        completion = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a professional academic writing and logic analysis expert "
                        "and also a patient writing coach for English learners. "
                        "You ALWAYS return a single JSON object following the requested schema."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            max_completion_tokens=2000,
        )

        result = completion.choices[0].message.content.strip()

        try:
            data = json.loads(result)
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            return json.dumps({
                "error": "Server response format error",
                "issues": [],
                "summary": "Unable to parse analysis results, please try again later.",
            })

        new_profile = data.get("profile")
        logic_score = data.get("overall_score", 0.0)
        
        # 保存到数据库（如果提供了 user_id）
        if isinstance(new_profile, dict) and user_id and db:
            _save_user_profile(user_id, new_profile, logic_score, text, db)

        return json.dumps(data, ensure_ascii=False)

    except Exception as e:
        print(f"Logic analysis error: {e}")
        return json.dumps({
            "error": str(e),
            "issues": [],
            "summary": "An error occurred during analysis, please try again later.",
        })

def analyze_logic_breaks(sentences: List[str]) -> str:
    """
    Analyze sentence-to-sentence logical coherence and return breakpoints.
    Each breakpoint refers to the sentence index that feels disconnected from its previous sentence.
    """
    if not sentences or len(sentences) < 2:
        return json.dumps({"breaks": []}, ensure_ascii=False)

    prompt = f"""You are a professional academic writing and logic analysis expert.
Given the ordered list of sentences below, identify where the logical connection between consecutive sentences is weak or missing.
Return ONLY a JSON object with an array named "breaks".

Each break must use:
- index: 0-based index of the sentence that feels disconnected from the previous sentence
- reason: short explanation of why the connection is weak

Limit to the most important 1-5 breakpoints. If everything is coherent, return an empty list.

Sentences:
{json.dumps(sentences, ensure_ascii=False)}
"""

    try:
        completion = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a professional academic writing and logic analysis expert. "
                        "You ALWAYS return a single JSON object following the requested schema."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            max_completion_tokens=800,
        )

        result = completion.choices[0].message.content.strip()
        try:
            data = json.loads(result)
        except json.JSONDecodeError as e:
            print(f"JSON decode error (logic breaks): {e}")
            return json.dumps({"breaks": []}, ensure_ascii=False)

        breaks = data.get("breaks", [])
        if not isinstance(breaks, list):
            breaks = []
        return json.dumps({"breaks": breaks}, ensure_ascii=False)

    except Exception as e:
        print(f"Logic breaks analysis error: {e}")
        return json.dumps({"breaks": []}, ensure_ascii=False)


def generate_tasks_for_profile(text: str, user_id: int = None, db: Session = None) -> str:
    """
    Generate EXACTLY 3 targeted practice tasks based on the CURRENT user profile
    (and optionally the latest article text). This is called only when the user
    explicitly asks for practice tasks.
    """
    # 从数据库加载用户画像（如果提供了 user_id）
    existing_profile = {}
    if user_id and db:
        existing_profile = _load_user_profile(user_id, db)
    existing_profile_json = json.dumps(existing_profile, ensure_ascii=False)

    prompt = f"""You are an academic writing coach.

Here is the CURRENT student writing profile (may be empty or partial):
{existing_profile_json}

Here is the student's latest article (optional context, may be empty):
{text}

Based on the PROFILE (and using the article only as additional evidence), design EXACTLY 3 highly specific writing practice tasks.

Rules for tasks:
- Each task focuses on ONE clear weakness from the profile (logic / vocabulary / grammar / structure).
- Each task is small and doable: 3–5 sentences or 1 short paragraph.
- Instructions must be concrete and student-friendly (avoid vague advice like "improve grammar").
- Include ONE short example or pattern for the student to imitate.

Return a STRICT JSON object:
{{
  "tasks": [
    {{
      "title": "Short, student-facing title of the task",
      "dimension": "logic"  // or "vocabulary" or "grammar" or "structure"
      "target_issue": "the specific weakness this task targets",
      "exercise": "concrete instruction for a small writing exercise",
      "example": "one short model example or pattern they can imitate"
    }}
  ]
}}

IMPORTANT:
- Return EXACTLY 3 items in "tasks".
- Do NOT include any analysis fields like score, issues, or summary.
- Do NOT include markdown code blocks."""

    try:
        completion = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a focused academic writing coach. "
                        "You only design concrete, short, targeted practice tasks."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            max_completion_tokens=1000,
        )

        result = completion.choices[0].message.content.strip()
        # Validate JSON
        json.loads(result)
        return result

    except Exception as e:
        print(f"Task generation error: {e}")
        return json.dumps({
            "tasks": []
        })
