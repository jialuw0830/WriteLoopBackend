from fastapi import FastAPI, HTTPException, Depends, status, Query
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from app.services.suggest_service import generate_suggestions
from app.services.rewrite_service import rewrite_sentence
from app.services.logic_profile_service import (
    analyze_logic_with_profile,
    analyze_logic_breaks,
    generate_tasks_for_profile,
    generate_logic_tree,
)
from app.services.essay_service import get_all_essays, get_essay_by_id, seed_essays_if_empty
from fastapi.middleware.cors import CORSMiddleware
from app.models import init_db, get_db, User, UserProfile, PracticeHistory, SessionLocal
from app.auth import (
    authenticate_user, get_password_hash, create_access_token,
    get_user_by_username, get_current_user
)
from sqlalchemy.orm import Session
from datetime import timedelta
import json
from typing import Optional, Any, List

app = FastAPI()

# 初始化数据库
init_db()

@app.on_event("startup")
def seed_data_on_startup():
    db = SessionLocal()
    try:
        seed_essays_if_empty(db)
    finally:
        db.close()

# CORS configuration
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:8080",
    "http://47.237.161.90",
    "http://localhost",
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

class LogicBreaksRequest(BaseModel):
    sentences: List[str]


class TaskRequest(BaseModel):
    # Latest article text, optional; tasks are mainly based on saved user_profile
    text: str = ""


class UserRegister(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


def parse_json_response(result: str, default_key: str = "data"):
    """Parse JSON response with error handling."""
    try:
        return json.loads(result)
    except json.JSONDecodeError:
        return {default_key: []}

def to_user_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        username=user.username,
        created_at=user.created_at.isoformat() if user.created_at else None,
    )

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
async def analyze_logic_endpoint(
    request: LogicAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Logic analysis endpoint.
    Receives complete article content, uses GPT-4o to analyze logical flaws and provide improvement suggestions.
    """
    # use enhanced logic analysis that also updates user profile
    result = analyze_logic_with_profile(request.text, user_id=current_user.id, db=db)
    return parse_json_response(result)

@app.post("/analyze-breaks")
async def analyze_breaks_endpoint(
    request: LogicBreaksRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Analyze sentence-to-sentence logical coherence and return breakpoints.
    """
    result = analyze_logic_breaks(request.sentences)
    return parse_json_response(result, default_key="breaks")


@app.post("/generate-tasks")
async def generate_tasks_endpoint(
    request: TaskRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate personalized practice tasks based on the current user profile.
    Called only when user explicitly requests tasks.
    """
    result = generate_tasks_for_profile(request.text, user_id=current_user.id, db=db)
    # this already returns {"tasks": [...]}
    return parse_json_response(result, default_key="tasks")


@app.post("/analyze-logic-tree")
async def analyze_logic_tree_endpoint(
    request: LogicAnalysisRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Generate a logic tree structure from the user's text.
    Shows thesis, main points, evidence, relationships, and conclusion.
    """
    result = generate_logic_tree(request.text)
    return parse_json_response(result, default_key="tree")


# IELTS Essay Reading APIs
@app.get("/essays")
async def get_essays(
    brief: bool = Query(False, description="Return lightweight summaries only."),
    preview_len: int = Query(200, ge=0, le=1000, description="Preview length for brief mode."),
    db: Session = Depends(get_db),
):
    """Get all IELTS essays."""
    essays = get_all_essays(db, brief=brief, preview_len=preview_len)
    return {"essays": essays, "total": len(essays)}


@app.get("/essays/{essay_id}")
async def get_essay(essay_id: int, db: Session = Depends(get_db)):
    """Get a specific essay by ID."""
    essay = get_essay_by_id(db, essay_id)
    if essay is None:
        raise HTTPException(status_code=404, detail="Essay not found")
    return {"essay": essay}


# 用户认证相关API
@app.post("/register", response_model=Token)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """用户注册"""
    # 检查用户名是否已存在
    if get_user_by_username(db, user_data.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )
    # 创建新用户
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        username=user_data.username,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    # 生成token
    access_token_expires = timedelta(minutes=30 * 24 * 60)
    access_token = create_access_token(
        data={"sub": db_user.username}, expires_delta=access_token_expires
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": to_user_response(db_user)
    }


@app.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """用户登录"""
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=30 * 24 * 60)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": to_user_response(user)
    }


@app.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """获取当前登录用户信息"""
    return to_user_response(current_user)


@app.get("/profile")
async def get_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取当前用户的画像数据（包括 TTR, MLU, Logic Score）"""
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    
    if not profile:
        # 如果没有画像，返回默认值
        return {
            "ttr": 0.0,
            "mlu": 0.0,
            "logic_score": 0.0,
            "profile_data": {},
            "has_data": False
        }
    
    # 解析 profile_data
    profile_data = {}
    if profile.profile_data:
        try:
            profile_data = json.loads(profile.profile_data)
        except:
            profile_data = {}
    
    return {
        "ttr": profile.ttr or 0.0,
        "mlu": profile.mlu or 0.0,
        "logic_score": profile.logic_score or 0.0,
        "profile_data": profile_data,
        "has_data": True,
        "updated_at": profile.updated_at.isoformat() if profile.updated_at else None
    }


@app.get("/practice-history")
async def get_practice_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(100, ge=1, le=1000, description="返回的最大记录数")
):
    """获取用户的练习历史记录，用于绘制趋势折线图"""
    history_records = db.query(PracticeHistory)\
        .filter(PracticeHistory.user_id == current_user.id)\
        .order_by(PracticeHistory.created_at.asc())\
        .limit(limit)\
        .all()
    
    # 转换为前端需要的格式
    history_data = []
    for record in history_records:
        history_data.append({
            "id": record.id,
            "logic_score": record.logic_score,
            "ttr": record.ttr,
            "mlu": record.mlu,
            "created_at": record.created_at.isoformat() if record.created_at else None,
            # 计算综合分数（可选，用于折线图）
            "overall_score": (record.logic_score + record.ttr + record.mlu) / 3.0
        })
    
    return {
        "history": history_data,
        "total": len(history_data)
    }


@app.get("/users")
async def get_all_users(db: Session = Depends(get_db)):
    """获取所有用户列表（仅用于开发调试）"""
    users = db.query(User).all()
    return {
        "total": len(users),
        "users": [
            {
                "id": user.id,
                "username": user.username,
                "created_at": user.created_at.isoformat() if user.created_at else None
            }
            for user in users
        ]
    }
