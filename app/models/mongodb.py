"""
MongoDB 모델 정의 - 채팅 이력 저장
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from bson import ObjectId


class ChatMessage(BaseModel):
    """개별 채팅 메시지"""
    id: Optional[str] = Field(default_factory=lambda: str(ObjectId()))
    role: str = Field(..., description="메시지 역할: user, assistant, system")
    content: str = Field(..., description="메시지 내용")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="추가 메타데이터")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            ObjectId: lambda v: str(v)
        }


class ChatSession(BaseModel):
    """채팅 세션 (대화 단위)"""
    id: Optional[str] = Field(default_factory=lambda: str(ObjectId()))
    user_id: str = Field(..., description="사용자 ID (emp_no)")
    session_name: Optional[str] = Field(None, description="세션 이름")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    messages: List[ChatMessage] = Field(default_factory=list, description="채팅 메시지 목록")
    is_active: bool = Field(default=True, description="활성 세션 여부")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="세션 메타데이터")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            ObjectId: lambda v: str(v)
        }


class ChatHistory(BaseModel):
    """사용자별 채팅 이력 (집계용)"""
    user_id: str = Field(..., description="사용자 ID")
    total_sessions: int = Field(default=0, description="총 세션 수")
    total_messages: int = Field(default=0, description="총 메시지 수")
    last_activity: Optional[datetime] = Field(None, description="마지막 활동 시간")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            ObjectId: lambda v: str(v)
        }


# MongoDB 컬렉션 인덱스 정의
CHAT_INDEXES = [
    # ChatSession 컬렉션 인덱스
    {"keys": [("user_id", 1), ("created_at", -1)]},  # 사용자별 최신 세션 조회
    {"keys": [("user_id", 1), ("is_active", 1)]},   # 활성 세션 조회
    {"keys": [("created_at", -1)]},                  # 전체 세션 시간순 조회
    
    # ChatMessage 컬렉션 인덱스 (임베디드 문서)
    {"keys": [("messages.timestamp", -1)]},          # 메시지 시간순 조회
    {"keys": [("messages.role", 1)]},                # 메시지 역할별 조회
]