"""
Hybrid Recommendation API - 하이브리드 AI 추천 시스템 API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.core.database import get_db
from app.services.hybrid_recommendation_service import HybridRecommendationService
from app.schemas.personalized_recommendation import PersonalizedRecommendationRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/hybrid", tags=["Hybrid Recommendation"])

# HybridRecommendationService 인스턴스 (싱글톤)
hybrid_service = None

def get_hybrid_service() -> HybridRecommendationService:
    """HybridRecommendationService 인스턴스 가져오기"""
    global hybrid_service
    if hybrid_service is None:
        hybrid_service = HybridRecommendationService()
    return hybrid_service

@router.post("/recommendations", response_model=List[dict])
async def get_hybrid_recommendations(
    request: PersonalizedRecommendationRequest,
    db: Session = Depends(get_db)
):
    """
    하이브리드 추천 생성 (CF + Embedding + LightRAG)
    
    Args:
        request: 추천 요청
        db: 데이터베이스 세션
        
    Returns:
        하이브리드 추천 리스트
    """
    try:
        service = get_hybrid_service()
        
        # 모델 초기화 (필요한 경우)
        if not hasattr(service, '_initialized'):
            service.initialize_models(db)
            service._initialized = True
        
        # 하이브리드 추천 생성
        recommendations = service.get_hybrid_recommendations(
            emp_no=request.emp_no,
            query_text=request.query_text
        )
        
        logger.info(f"Generated {len(recommendations)} hybrid recommendations for user {request.emp_no}")
        
        return recommendations
        
    except Exception as e:
        logger.error(f"Error generating hybrid recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/explanation/{user_id}/{item_id}")
async def get_recommendation_explanation(
    user_id: str,
    item_id: str,
    db: Session = Depends(get_db)
):
    """
    추천 설명 생성
    
    Args:
        user_id: 사용자 ID
        item_id: 아이템 ID
        db: 데이터베이스 세션
        
    Returns:
        추천 설명
    """
    try:
        service = get_hybrid_service()
        
        # 추천 설명 생성
        explanation = service.get_recommendation_explanation(user_id, item_id)
        
        return {
            "user_id": user_id,
            "item_id": item_id,
            "explanation": explanation,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error generating explanation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/similar-users/{user_id}")
async def get_similar_users(
    user_id: str,
    n_users: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db)
):
    """
    유사한 사용자 찾기
    
    Args:
        user_id: 사용자 ID
        n_users: 반환할 사용자 수
        db: 데이터베이스 세션
        
    Returns:
        유사한 사용자 리스트
    """
    try:
        service = get_hybrid_service()
        
        # 유사한 사용자 찾기
        similar_users = service.get_similar_users(user_id, n_users)
        
        return {
            "user_id": user_id,
            "similar_users": similar_users,
            "count": len(similar_users)
        }
        
    except Exception as e:
        logger.error(f"Error finding similar users: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/performance-metrics")
async def get_performance_metrics(db: Session = Depends(get_db)):
    """
    시스템 성능 메트릭 조회
    
    Args:
        db: 데이터베이스 세션
        
    Returns:
        성능 메트릭
    """
    try:
        service = get_hybrid_service()
        
        # 성능 메트릭 조회
        metrics = service.get_system_performance_metrics()
        
        return metrics
        
    except Exception as e:
        logger.error(f"Error getting performance metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/update-preferences/{user_id}")
async def update_user_preferences(
    user_id: str,
    vote_data: dict,
    db: Session = Depends(get_db)
):
    """
    사용자 선호도 업데이트
    
    Args:
        user_id: 사용자 ID
        vote_data: 투표 데이터
        db: 데이터베이스 세션
        
    Returns:
        업데이트 결과
    """
    try:
        service = get_hybrid_service()
        
        # 투표 데이터에 사용자 ID 추가
        vote_data["emp_no"] = user_id
        
        # 선호도 업데이트
        success = service.update_user_preferences(user_id, vote_data)
        
        if success:
            return {
                "success": True,
                "message": f"Preferences updated for user {user_id}",
                "updated_at": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to update preferences")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating preferences: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    """하이브리드 추천 서비스 상태 확인"""
    try:
        service = get_hybrid_service()
        
        # 각 서비스 상태 확인
        cf_status = "active" if service.cf_service else "inactive"
        vector_status = "active" if service.vector_service else "inactive"
        lightrag_status = "active" if service.lightrag_service else "inactive"
        
        return {
            "status": "healthy",
            "services": {
                "collaborative_filtering": cf_status,
                "vector_db": vector_status,
                "lightrag": lightrag_status
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }

@router.post("/initialize-models")
async def initialize_models(db: Session = Depends(get_db)):
    """
    모든 모델 초기화
    
    Args:
        db: 데이터베이스 세션
        
    Returns:
        초기화 결과
    """
    try:
        service = get_hybrid_service()
        
        # 모델 초기화
        success = service.initialize_models(db)
        
        if success:
            return {
                "success": True,
                "message": "All models initialized successfully",
                "initialized_at": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to initialize models")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error initializing models: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
