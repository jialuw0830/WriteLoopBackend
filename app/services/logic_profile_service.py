from app.services.llm_client import client
import json
import os


PROFILE_FILE = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "data",
    "user_profile.json",
)


def _load_user_profile() -> dict:
    """Load existing user profile from JSON file (if any)."""
    try:
        if not os.path.exists(PROFILE_FILE):
            return {}
        with open(PROFILE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Failed to load user profile: {e}")
        return {}


def _save_user_profile(profile: dict) -> None:
    """Persist user profile to JSON file."""
    try:
        os.makedirs(os.path.dirname(PROFILE_FILE), exist_ok=True)
        with open(PROFILE_FILE, "w", encoding="utf-8") as f:
            json.dump(profile, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Failed to save user profile: {e}")


def analyze_logic_with_profile(text: str) -> str:
    """
    Analyze article logic and update a multi-dimensional user profile.
    This function does NOT generate practice tasks (tasks are generated separately on demand).
    """
    if not text.strip():
        return json.dumps({
            "error": "Empty content",
            "issues": [],
        })

    existing_profile = _load_user_profile()
    existing_profile_json = json.dumps(existing_profile, ensure_ascii=False)

    prompt = f"""You are a professional academic writing and logic analysis expert and learning coach.
Please carefully analyze the logical structure and language of the following ENGLISH article, 
identify logical flaws, argumentative weaknesses, vocabulary/grammar issues, and areas for improvement.

=== Article content ===
{text}

=== Existing student profile (may be empty on first use) ===
{existing_profile_json}

Please do THREE things:

1) LOGIC ANALYSIS (article-level)
Analyze from the following aspects:
- Logical Coherence: whether the logical connections between paragraphs and sentences are smooth
- Argument Structure: whether the thesis, evidence, and argumentation process are clear and effective
- Causality: whether causal relationships are reasonable, and whether there are reversed or false causalities
- Evidence Support: whether evidence sufficiently supports the thesis, and whether there is insufficient or irrelevant evidence
- Logical Fallacies: whether there are logical jumps, circular reasoning, hasty generalizations, and other common logical errors

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
      "severity": "high"  // or "medium" or "low"
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
- Do NOT include any field named "suggestions" or "tasks" in the response.
- The JSON must be valid and must NOT contain markdown code blocks or comments."""

    try:
        completion = client.chat.completions.create(
            model="gpt-4o",
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
            temperature=0.3,
            max_tokens=2000,
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
        if isinstance(new_profile, dict):
            _save_user_profile(new_profile)

        return json.dumps(data, ensure_ascii=False)

    except Exception as e:
        print(f"Logic analysis error: {e}")
        return json.dumps({
            "error": str(e),
            "issues": [],
            "summary": "An error occurred during analysis, please try again later.",
        })


def generate_tasks_for_profile(text: str) -> str:
    """
    Generate EXACTLY 3 targeted practice tasks based on the CURRENT user profile
    (and optionally the latest article text). This is called only when the user
    explicitly asks for practice tasks.
    """
    existing_profile = _load_user_profile()
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
            model="gpt-4o",
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
            temperature=0.5,
            max_tokens=1000,
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


