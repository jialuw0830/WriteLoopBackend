from fastapi import FastAPI
from pydantic import BaseModel
from app.services.suggest_service import generate_suggestions
from app.services.rewrite_service import rewrite_sentence
from app.services.logic_analysis_service import analyze_logic
from fastapi.middleware.cors import CORSMiddleware
import json
from typing import Optional, Any

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

class RewriteRequest(BaseModel):
    sentence: str

class LogicAnalysisRequest(BaseModel):
    text: str

def parse_json_response(result: str, default_key: str = "data"):
    """Parse JSON response with error handling."""
    try:
        return json.loads(result)
    except json.JSONDecodeError:
        return {default_key: []}

@app.post("/suggest")
async def get_suggestions(request: SuggestionRequest):
    result = generate_suggestions(request.text, request.cursor)
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
    result = analyze_logic(request.text)
    return parse_json_response(result)
