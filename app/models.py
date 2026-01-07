from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os
from urllib.parse import quote_plus
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# MySQL 数据库配置（从环境变量读取，如果没有则使用默认值）
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_USER = os.getenv("DB_USER", "appuser")
DB_PASSWORD = os.getenv("DB_PASSWORD", "App@12345678")
DB_NAME = os.getenv("DB_NAME", "appdb")

# MySQL 连接字符串（使用quote_plus编码密码中的特殊字符）
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{quote_plus(DB_PASSWORD)}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"

# 创建数据库引擎
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # 自动重连
    pool_recycle=3600,   # 连接回收时间
    echo=False  # 设置为True可以看到SQL语句
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关联关系
    profile = relationship("UserProfile", back_populates="user", uselist=False)
    practice_history = relationship("PracticeHistory", back_populates="user", cascade="all, delete-orphan")


class UserProfile(Base):
    __tablename__ = "user_profiles"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False, index=True)
    
    # 三个核心指标（0-100 分）
    ttr = Column(Float, default=0.0, comment="Type-Token Ratio: 词汇丰富度 (0-100)")
    mlu = Column(Float, default=0.0, comment="Mean Length of Utterance: 句法复杂度 (0-100)")
    logic_score = Column(Float, default=0.0, comment="Logic Score: 逻辑连贯性 (0-100)")
    
    # 完整的 profile 数据（JSON 格式存储）
    profile_data = Column(Text, comment="完整的用户画像数据（JSON格式）")
    
    # 时间戳
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联关系
    user = relationship("User", back_populates="profile")


class PracticeHistory(Base):
    __tablename__ = "practice_history"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # 每次练习的分数（0-100 分）
    logic_score = Column(Float, nullable=False, comment="Logic Score: 逻辑连贯性 (0-100)")
    ttr = Column(Float, nullable=False, comment="Type-Token Ratio: 词汇丰富度 (0-100)")
    mlu = Column(Float, nullable=False, comment="Mean Length of Utterance: 句法复杂度 (0-100)")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # 关联关系
    user = relationship("User", back_populates="practice_history")


class Essay(Base):
    __tablename__ = "essays"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    essay_number = Column(Integer, unique=True, index=True, nullable=False)
    title = Column(String(255), nullable=True)
    question = Column(Text, nullable=True)
    word_count_reported = Column(Integer, nullable=True)
    word_count_actual = Column(Integer, nullable=True)
    body_paragraphs = Column(Text, nullable=True)  # JSON list
    body_text = Column(Text, nullable=True)


# 创建数据库表
def init_db():
    Base.metadata.create_all(bind=engine)


# 获取数据库会话
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
