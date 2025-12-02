from app.services.llm_client import client
import json

def analyze_logic(text: str) -> str:
    """
    Analyze article logic using GPT-4o to identify logical flaws and provide improvement suggestions.
    Focuses on: logical coherence, argument structure, causality, evidence support, logical fallacies.
    """
    if not text.strip():
        return json.dumps({
            "error": "Empty content",
            "issues": []
        })
    
    prompt = f"""You are a professional academic writing and logic analysis expert. Please carefully analyze the logical structure of the following English article, identify logical flaws, argumentative weaknesses, and areas for improvement.

Article content:
{text}

Please analyze from the following aspects:
1. **Logical Coherence**: Whether the logical connections between paragraphs and sentences are smooth
2. **Argument Structure**: Whether the thesis, evidence, and argumentation process are clear and effective
3. **Causality**: Whether causal relationships are reasonable, and whether there are reversed causality or false causality
4. **Evidence Support**: Whether evidence sufficiently supports the thesis, and whether there is insufficient or irrelevant evidence
5. **Logical Fallacies**: Whether there are logical jumps, circular reasoning, hasty generalizations, and other common logical errors

Please return the analysis results in JSON format as follows:
{{
  "overall_score": 85,  // Logic quality score (0-100)
  "issues": [
    {{
      "type": "Type of logical flaw",
      "location": "Location of the problem (paragraph/sentence description)",
      "description": "Detailed description of the problem",
      "severity": "high/medium/low"  // Severity level
    }}
  ],
  "summary": "Overall logic analysis summary"
}}

IMPORTANT: Return EXACTLY 3 issues in the "issues" array. Select the 3 most critical and representative logical flaws. Do not return more than 3 issues. Do NOT include a "suggestions" field in the response.

Please ensure the return is valid JSON format without any markdown code block markers."""

    try:
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a professional academic writing and logic analysis expert. You excel at identifying logical flaws in articles and providing constructive improvement suggestions. You always return analysis results in JSON format."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
            max_tokens=2000
        )
        
        result = completion.choices[0].message.content.strip()
        json.loads(result)
        return result
        
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        return json.dumps({
            "error": "Server response format error",
            "issues": [],
            "summary": "Unable to parse analysis results, please try again later."
        })
    except Exception as e:
        print(f"Logic analysis error: {e}")
        return json.dumps({
            "error": str(e),
            "issues": [],
            "summary": "An error occurred during analysis, please try again later."
        })
