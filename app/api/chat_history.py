"""
채팅 이력 관리 API
World Best Practice 적용:
1. RESTful API 설계
2. 비동기 처리
3. 에러 핸들링
4. 데이터 검증
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from app.services.chat_history_service import chat_history_service
from app.models.mongodb import ChatSession, ChatMessage

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat-history", tags=["chat-history"])

# 서비스 초기화
@router.on_event("startup")
async def startup_event():
    """서비스 시작 시 MongoDB 연결"""
    try:
        await chat_history_service.connect()
        logger.info("✅ Chat history service initialized")
    except Exception as e:
        logger.error(f"❌ Chat history service initialization failed: {str(e)}")

@router.on_event("shutdown")
async def shutdown_event():
    """서비스 종료 시 MongoDB 연결 해제"""
    try:
        await chat_history_service.disconnect()
        logger.info("Chat history service disconnected")
    except Exception as e:
        logger.error(f"Chat history service disconnect failed: {str(e)}")


@router.post("/sessions")
async def create_chat_session(
    user_id: str,
    session_name: Optional[str] = None
):
    """새 채팅 세션 생성"""
    try:
        session_id = await chat_history_service.create_session(user_id, session_name)
        return {
            "status": "S",
            "message": "채팅 세션이 생성되었습니다",
            "session_id": session_id
        }
    except Exception as e:
        logger.error(f"세션 생성 실패: {str(e)}")
        raise HTTPException(status_code=500, detail="세션 생성에 실패했습니다")


@router.post("/sessions/{session_id}/messages")
async def add_message(
    session_id: str,
    role: str,
    content: str,
    metadata: Optional[Dict[str, Any]] = None
):
    """메시지 추가"""
    try:
        # 역할 검증
        if role not in ["user", "assistant", "system"]:
            raise HTTPException(status_code=400, detail="유효하지 않은 메시지 역할입니다")
        
        message_id = await chat_history_service.add_message(
            session_id, role, content, metadata
        )
        
        return {
            "status": "S",
            "message": "메시지가 추가되었습니다",
            "message_id": message_id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"메시지 추가 실패: {str(e)}")
        raise HTTPException(status_code=500, detail="메시지 추가에 실패했습니다")


@router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """세션 조회"""
    try:
        session = await chat_history_service.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")
        
        return {
            "status": "S",
            "message": "세션 조회 성공",
            "session": session
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"세션 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail="세션 조회에 실패했습니다")


@router.get("/users/{user_id}/sessions")
async def get_user_sessions(
    user_id: str,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """사용자 세션 목록 조회"""
    try:
        sessions = await chat_history_service.get_user_sessions(user_id, limit, offset)
        
        return {
            "status": "S",
            "message": "사용자 세션 목록 조회 성공",
            "sessions": sessions,
            "pagination": {
                "limit": limit,
                "offset": offset,
                "total": len(sessions)
            }
        }
    except Exception as e:
        logger.error(f"사용자 세션 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail="사용자 세션 조회에 실패했습니다")


@router.get("/users/{user_id}/active-session")
async def get_active_session(user_id: str):
    """사용자의 활성 세션 조회"""
    try:
        # MongoDB 연결 확인
        if chat_history_service.db is None:
            await chat_history_service.connect()
        
        session = await chat_history_service.get_active_session(user_id)
        print(f"🔍 활성 세션 조회 결과: {session}")
        
        if not session:
            print(f"🆕 새 세션 생성: {user_id}")
            # 활성 세션이 없으면 새로 생성
            session_id = await chat_history_service.create_session(user_id)
            session = await chat_history_service.get_session(session_id)
            print(f"✅ 새 세션 생성 완료: {session_id}")
        else:
            print(f"✅ 기존 세션 사용: {session.get('id', 'Unknown')}")
        
        return {
            "status": "S",
            "message": "활성 세션 조회 성공",
            "session": session
        }
    except Exception as e:
        logger.error(f"활성 세션 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail="활성 세션 조회에 실패했습니다")


@router.post("/sessions/{session_id}/messages")
async def add_message_to_session(
    session_id: str,
    role: str = Query(...),
    content: str = Query(...),
    metadata: Optional[Dict[str, Any]] = None
):
    """세션에 메시지 추가"""
    try:
        message = await chat_history_service.add_message(
            session_id, role, content, metadata
        )
        
        return {
            "status": "S",
            "message": "메시지 저장 성공",
            "message_id": str(message.id)
        }
    except Exception as e:
        logger.error(f"메시지 저장 실패: {str(e)}")
        raise HTTPException(status_code=500, detail="메시지 저장에 실패했습니다")


@router.get("/sessions/{session_id}/messages")
async def get_session_messages(
    session_id: str,
    limit: int = Query(50, ge=1, le=200)
):
    """세션 메시지 조회"""
    try:
        messages = await chat_history_service.get_session_messages(session_id, limit)
        
        return {
            "status": "S",
            "message": "세션 메시지 조회 성공",
            "messages": messages
        }
    except Exception as e:
        logger.error(f"세션 메시지 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail="세션 메시지 조회에 실패했습니다")


@router.get("/users/{user_id}/history")
async def get_user_history(user_id: str):
    """사용자 채팅 이력 통계 조회"""
    try:
        history = await chat_history_service.get_user_history(user_id)
        
        return {
            "status": "S",
            "message": "사용자 이력 조회 성공",
            "history": history
        }
    except Exception as e:
        logger.error(f"사용자 이력 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail="사용자 이력 조회에 실패했습니다")


@router.post("/archive")
async def archive_old_sessions(days: int = Query(30, ge=1, le=365)):
    """오래된 세션 아카이빙"""
    try:
        archived_count = await chat_history_service.archive_old_sessions(days)
        
        return {
            "status": "S",
            "message": f"{archived_count}개 세션이 아카이빙되었습니다",
            "archived_count": archived_count
        }
    except Exception as e:
        logger.error(f"세션 아카이빙 실패: {str(e)}")
        raise HTTPException(status_code=500, detail="세션 아카이빙에 실패했습니다")


@router.get("/health")
async def health_check():
    """채팅 이력 서비스 상태 확인"""
    try:
        # MongoDB 연결 상태 확인
        await chat_history_service.db.command("ping")
        
        return {
            "status": "S",
            "message": "채팅 이력 서비스가 정상 작동 중입니다",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"헬스 체크 실패: {str(e)}")
        raise HTTPException(status_code=503, detail="채팅 이력 서비스에 문제가 있습니다")
