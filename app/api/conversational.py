"""
대화형 질문 처리 API
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, Any
import asyncio
import json

from app.core.database import get_db
from app.services.conversational_service import ConversationalService
from app.services.bedrock_service import BedrockService

router = APIRouter(prefix="/conversational", tags=["Conversational"])


@router.get("/test")
async def test_conversational():
    """대화형 API 테스트 엔드포인트"""
    return {"status": "S", "message": "Conversational API is working"}

@router.get("/test-bedrock")
async def test_bedrock_connection():
    """AWS Bedrock 연결 테스트"""
    try:
        bedrock_service = BedrockService()
        result = bedrock_service.test_connection()
        
        if result["success"]:
            return {
                "status": "S",
                "message": "AWS Bedrock 연결 성공",
                "test_response": result.get("test_response", ""),
                "bedrock_status": "connected"
            }
        else:
            return {
                "status": "E",
                "message": f"AWS Bedrock 연결 실패: {result.get('message', 'Unknown error')}",
                "bedrock_status": "disconnected"
            }
    except Exception as e:
        return {
            "status": "E",
            "message": f"Bedrock 테스트 중 오류: {str(e)}",
            "bedrock_status": "error"
        }


class ConversationalQuery(BaseModel):
    """대화형 질문 요청 모델"""
    emp_no: str
    question: str
    context: Optional[Dict[str, Any]] = None


class ConversationalResponse(BaseModel):
    """대화형 질문 응답 모델"""
    status: str
    message: str
    response_text: str
    action_required: str = "none"
    data: Optional[Dict[str, Any]] = None
    suggested_actions: Optional[list] = None
    error: Optional[str] = None


@router.post("/query", response_model=ConversationalResponse)
async def process_conversational_query(
    request: ConversationalQuery,
    db: Session = Depends(get_db)
):
    """
    자연어 질문 처리 및 AI 응답 생성
    """
    try:
        conversational_service = ConversationalService(db)
        
        result = conversational_service.process_question(
            emp_no=request.emp_no,
            question=request.question,
            context=request.context
        )
        
        return ConversationalResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
async def stream_conversational_query(
    request: ConversationalQuery,
    db: Session = Depends(get_db)
):
    """
    SSE 스트리밍으로 자연어 질문 처리 및 AI 응답 생성
    """
    async def generate_response():
        try:
            conversational_service = ConversationalService(db)
            
            # 전체 응답 생성
            result = conversational_service.process_question(
                emp_no=request.emp_no,
                question=request.question,
                context=request.context
            )
            
            response_text = result.get("response_text", "")
            
            # 응답을 단어별로 분할하여 스트리밍
            words = response_text.split()
            
            # 시작 이벤트 전송
            yield f"data: {json.dumps({'type': 'start', 'message': 'AI가 답변을 생성하고 있습니다...'})}\n\n"
            
            # 단어별로 스트리밍 (타이핑 효과)
            current_text = ""
            for i, word in enumerate(words):
                current_text += word + " "
                
                # 각 단어마다 0.1초 지연
                await asyncio.sleep(0.1)
                
                # 진행률 계산
                progress = int((i + 1) / len(words) * 100)
                
                # 스트리밍 데이터 전송
                yield f"data: {json.dumps({'type': 'chunk', 'text': word, 'progress': progress, 'current_text': current_text.strip()})}\n\n"
            
            # 완료 이벤트 전송
            yield f"data: {json.dumps({'type': 'complete', 'final_text': response_text, 'status': result.get('status', 'S'), 'message': result.get('message', ''), 'action_required': result.get('action_required', 'none')})}\n\n"
            
        except Exception as e:
            # 에러 이벤트 전송
            yield f"data: {json.dumps({'type': 'error', 'message': f'오류가 발생했습니다: {str(e)}'})}\n\n"
    
    return StreamingResponse(
        generate_response(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )


@router.get("/my-vote-history/{emp_no}")
async def get_my_vote_history(
    emp_no: str,
    db: Session = Depends(get_db)
):
    """
    개인 투표 이력 조회
    """
    try:
        conversational_service = ConversationalService(db)
        
        # 직접 투표 이력 조회
        vote_history = conversational_service.vote_service.get_user_vote_history(emp_no)
        
        return {
            "emp_no": emp_no,
            "vote_history": vote_history,
            "total_votes": len(vote_history)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/past-dinner-history/{emp_no}")
async def get_past_dinner_history(
    emp_no: str,
    months: int = 3,
    db: Session = Depends(get_db)
):
    """
    과거 회식 이력 조회
    """
    try:
        conversational_service = ConversationalService(db)
        
        # 과거 회식 이력 조회
        past_dinners = conversational_service.vote_service.get_past_dinner_history(
            emp_no, months=months
        )
        
        return {
            "emp_no": emp_no,
            "past_dinners": past_dinners,
            "total_dinners": len(past_dinners)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/vote-results/{month}")
async def get_vote_results(
    month: str,
    db: Session = Depends(get_db)
):
    """
    특정 월 투표 결과 조회
    """
    try:
        conversational_service = ConversationalService(db)
        
        # 투표 결과 조회
        vote_results = conversational_service.vote_service.get_vote_results(month)
        
        return {
            "month": month,
            "vote_results": vote_results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test-conversational")
async def test_conversational_query(
    question: str,
    emp_no: str = "84927",
    db: Session = Depends(get_db)
):
    """
    테스트용 대화형 질문 처리
    """
    try:
        conversational_service = ConversationalService(db)
        
        result = conversational_service.process_question(
            emp_no=emp_no,
            question=question,
            context={"test": True}
        )
        
        return {
            "message": "테스트 대화형 질문이 처리되었습니다",
            "result": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
