"""
AI 채팅 API for GPT-style streaming responses
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Optional
import json
import asyncio
from datetime import datetime

from app.core.database import get_db
# SSE 매니저 제거 - 단순한 SSE 구현 사용

router = APIRouter(prefix="/ai", tags=["AI Chat"])


@router.post("/chat")
async def chat_with_ai(
    question: str,
    client_id: str,
    db: Session = Depends(get_db)
):
    """
    AI와 채팅 (GPT 스타일 스트리밍)
    
    실제 AI API 연동 예시:
    - OpenAI GPT
    - Claude
    - Google Gemini
    """
    try:
        # 🔥 AI 응답 시뮬레이션 (실제로는 AI API 호출)
        ai_response = await simulate_ai_response(question, client_id)
        return {"message": "AI response streaming started", "client_id": client_id}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def simulate_ai_response(question: str, client_id: str):
    """
    AI 응답 시뮬레이션 (실제 AI API 연동 시 교체)
    """
    # SSE 매니저 제거 - 단순한 SSE 구현 사용
    print(f"🤖 AI 시작: {client_id} - {question}")
    
    # 시뮬레이션된 AI 응답 (실제로는 AI API에서 스트리밍)
    response_chunks = [
        "안녕하세요! ",
        "CoFriends AI 어시스턴트입니다. ",
        f"'{question}'에 대해 답변드리겠습니다. ",
        "\n\n",
        "투표 시스템에 대한 질문이시군요. ",
        "현재 실시간으로 투표 현황을 확인할 수 있습니다. ",
        "어떤 식당이나 메뉴에 투표하고 싶으신가요? ",
        "\n\n",
        "추가로 궁금한 점이 있으시면 언제든 말씀해주세요!"
    ]
    
    # 스트리밍 응답 전송
    for i, chunk in enumerate(response_chunks):
        # SSE 매니저 제거 - 단순한 SSE 구현 사용
        print(f"🤖 AI 응답: {client_id} - {chunk}")
        
        # 실제 AI API처럼 지연시간 추가
        await asyncio.sleep(0.5)
    
    # SSE 매니저 제거 - 단순한 SSE 구현 사용
    print(f"🤖 AI 완료: {client_id}")
    
    print(f"🤖 AI response completed for {client_id}")


@router.post("/chat/stream")
async def stream_ai_chat(
    question: str,
    client_id: str,
    db: Session = Depends(get_db)
):
    """
    실시간 AI 채팅 스트리밍 (GPT 스타일)
    """
    try:
        # 백그라운드에서 AI 응답 처리
        asyncio.create_task(simulate_ai_response(question, client_id))
        
        return {
            "message": "AI streaming started",
            "client_id": client_id,
            "question": question
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
