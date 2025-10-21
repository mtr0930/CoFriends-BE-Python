"""
Hybrid Chat API - 실무 최적화 하이브리드 채팅 시스템
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Dict, Any
import json
import logging
from datetime import datetime

from app.core.database import get_db
from app.services.hybrid_pipeline_service import HybridPipelineService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/hybrid-chat", tags=["Hybrid Chat"])

# HybridPipelineService 인스턴스 (싱글톤)
pipeline_service = None

def get_pipeline_service() -> HybridPipelineService:
    """HybridPipelineService 인스턴스 가져오기"""
    global pipeline_service
    if pipeline_service is None:
        pipeline_service = HybridPipelineService()
    return pipeline_service

@router.post("/message")
async def process_message(
    request: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """
    사용자 메시지 처리 (실무 최적화 하이브리드 구조)
    
    Args:
        request: {
            "message": "사용자 메시지",
            "emp_no": "사용자 사번",
            "client_id": "SSE 클라이언트 ID"
        }
        db: 데이터베이스 세션
        
    Returns:
        SSE 스트림 응답
    """
    try:
        message = request.get("message", "")
        emp_no = request.get("emp_no", "84927")
        client_id = request.get("client_id", "default_client")
        
        if not message:
            raise HTTPException(status_code=400, detail="Message is required")
        
        # 파이프라인 서비스 가져오기
        service = get_pipeline_service()
        
        # SSE 스트림 생성
        async def generate_stream():
            try:
                async for result in service.process_user_message(message, emp_no, client_id):
                    yield f"data: {json.dumps(result, ensure_ascii=False)}\n\n"
                    
                # 스트림 종료
                yield f"data: {json.dumps({'type': 'stream_end', 'data': {'message': '스트림이 종료되었습니다.'}}, ensure_ascii=False)}\n\n"
                
            except Exception as e:
                logger.error(f"Error in stream generation: {str(e)}")
                yield f"data: {json.dumps({'type': 'error', 'data': {'error': str(e)}}, ensure_ascii=False)}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream"
            }
        )
        
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    """하이브리드 채팅 서비스 상태 확인"""
    try:
        service = get_pipeline_service()
        
        return {
            "status": "healthy",
            "service": "hybrid_chat",
            "components": {
                "collaborative_filtering": "active",
                "vector_db": "active", 
                "lightrag": "active",
                "sse": "active"
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }

@router.post("/test-pipeline")
async def test_pipeline(
    request: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """
    파이프라인 테스트 (개발용)
    
    Args:
        request: 테스트 요청 데이터
        db: 데이터베이스 세션
        
    Returns:
        테스트 결과
    """
    try:
        message = request.get("message", "한식 추천해주세요")
        emp_no = request.get("emp_no", "84927")
        
        service = get_pipeline_service()
        
        # 메시지 분석
        task_type = await service._analyze_message(message)
        
        return {
            "message": message,
            "emp_no": emp_no,
            "analyzed_task_type": task_type,
            "pipeline_status": "ready",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in pipeline test: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
