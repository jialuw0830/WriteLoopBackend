from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.services.suggest_service import generate_suggestions
from app.services.rewrite_service import rewrite_sentence
from app.services.logic_profile_service import analyze_logic_with_profile, generate_tasks_for_profile
from app.services.essay_service import get_all_essays, get_essay_by_id
from fastapi.middleware.cors import CORSMiddleware
import json
from typing import Optional, Any, List

app = FastAPI()

# CORS configuration
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

class SuggestionRequest(BaseModel):
    text: str
    cursor: Optional[Any] = None
    read_essay_ids: Optional[List[int]] = None  # Reading history for RAG enhancement

class RewriteRequest(BaseModel):
    sentence: str

class LogicAnalysisRequest(BaseModel):
    text: str


class TaskRequest(BaseModel):
    # Latest article text, optional; tasks are mainly based on saved user_profile
    text: str = ""


def parse_json_response(result: str, default_key: str = "data"):
    """Parse JSON response with error handling."""
    try:
        return json.loads(result)
    except json.JSONDecodeError:
        return {default_key: []}

@app.post("/suggest")
async def get_suggestions(request: SuggestionRequest):
    result = generate_suggestions(request.text, request.cursor, request.read_essay_ids)
    parsed = parse_json_response(result, "suggestions")
    return {"suggestions": parsed.get("suggestions", [])}

@app.post("/rewrite")
async def rewrite_sentence_endpoint(request: RewriteRequest):
    result = rewrite_sentence(request.sentence)
    return parse_json_response(result)

@app.post("/analyze-logic")
async def analyze_logic_endpoint(request: LogicAnalysisRequest):
    """
    Logic analysis endpoint.
    Receives complete article content, uses GPT-4o to analyze logical flaws and provide improvement suggestions.
    """
    # use enhanced logic analysis that also updates user profile
    result = analyze_logic_with_profile(request.text)
    return parse_json_response(result)


@app.post("/generate-tasks")
async def generate_tasks_endpoint(request: TaskRequest):
    """
    Generate personalized practice tasks based on the current user profile.
    Called only when user explicitly requests tasks.
    """
    result = generate_tasks_for_profile(request.text)
    # this already returns {"tasks": [...]}
    return parse_json_response(result, default_key="tasks")


# IELTS Essay Reading APIs
@app.get("/essays")
async def get_essays():
    """Get all IELTS essays."""
    essays = get_all_essays()
    return {"essays": essays, "total": len(essays)}


@app.get("/essays/{essay_id}")
async def get_essay(essay_id: int):
    """Get a specific essay by ID."""
    essay = get_essay_by_id(essay_id)
    if essay is None:
        raise HTTPException(status_code=404, detail="Essay not found")
    return {"essay": essay}


