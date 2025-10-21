"""
Personalized Recommendation API - 개인화 추천 시스템
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.core.database import get_db
from app.services.vector_db_service import VectorDBService
from app.schemas.personalized_recommendation import PersonalizedRecommendationRequest, PersonalizedRecommendationResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/personalized", tags=["Personalized Recommendation"])

# VectorDBService 인스턴스 (싱글톤)
vector_db_service = None

def get_vector_db_service() -> VectorDBService:
    """VectorDBService 인스턴스 가져오기"""
    global vector_db_service
    if vector_db_service is None:
        vector_db_service = VectorDBService()
    return vector_db_service

@router.post("/recommendations", response_model=List[dict])
async def get_personalized_recommendations(
    request: PersonalizedRecommendationRequest,
    db: Session = Depends(get_db)
):
    """
    개인화된 추천 생성
    
    Args:
        request: 개인화 추천 요청
        db: 데이터베이스 세션
        
    Returns:
        개인화된 추천 리스트
    """
    try:
        vector_service = get_vector_db_service()
        
        # 개인화된 추천 생성
        recommendations = vector_service.get_personalized_recommendations(
            emp_no=request.emp_no,
            query_text=request.query_text
        )
        
        logger.info(f"Generated {len(recommendations)} personalized recommendations for user {request.emp_no}")
        
        return recommendations
        
    except Exception as e:
        logger.error(f"Error generating personalized recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/vote-embedding")
async def create_vote_embedding(
    vote_data: dict,
    db: Session = Depends(get_db)
):
    """
    투표 데이터를 벡터로 변환하여 저장
    
    Args:
        vote_data: 투표 데이터
        db: 데이터베이스 세션
        
    Returns:
        저장된 문서 ID
    """
    try:
        vector_service = get_vector_db_service()
        
        # 필수 필드 검증
        required_fields = ["emp_no", "place_name", "menu_type"]
        for field in required_fields:
            if field not in vote_data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        # 투표 임베딩 생성
        doc_id = vector_service.create_vote_embedding(vote_data)
        
        logger.info(f"Vote embedding created with ID: {doc_id}")
        
        return {
            "success": True,
            "doc_id": doc_id,
            "message": "Vote embedding created successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating vote embedding: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/restaurant-embedding")
async def create_restaurant_embedding(
    restaurant_data: dict,
    db: Session = Depends(get_db)
):
    """
    식당 정보를 벡터로 변환하여 저장
    
    Args:
        restaurant_data: 식당 데이터
        db: 데이터베이스 세션
        
    Returns:
        저장된 문서 ID
    """
    try:
        vector_service = get_vector_db_service()
        
        # 필수 필드 검증
        required_fields = ["place_id", "place_name"]
        for field in required_fields:
            if field not in restaurant_data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        # 식당 임베딩 생성
        doc_id = vector_service.create_restaurant_embedding(restaurant_data)
        
        logger.info(f"Restaurant embedding created with ID: {doc_id}")
        
        return {
            "success": True,
            "doc_id": doc_id,
            "message": "Restaurant embedding created successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating restaurant embedding: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/user-history/{emp_no}")
async def get_user_vote_history(
    emp_no: str,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    사용자의 투표 기록 조회
    
    Args:
        emp_no: 사용자 번호
        limit: 조회할 최대 개수
        db: 데이터베이스 세션
        
    Returns:
        사용자의 투표 기록
    """
    try:
        vector_service = get_vector_db_service()
        
        # 사용자 투표 기록 조회
        vote_history = vector_service.get_user_vote_history(emp_no, limit)
        
        logger.info(f"Retrieved {len(vote_history)} votes for user {emp_no}")
        
        return {
            "emp_no": emp_no,
            "vote_count": len(vote_history),
            "votes": vote_history
        }
        
    except Exception as e:
        logger.error(f"Error getting user vote history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/similar-votes/{emp_no}")
async def search_similar_votes(
    emp_no: str,
    query: str = Query(..., description="Search query"),
    n_results: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db)
):
    """
    유사한 투표 기록 검색
    
    Args:
        emp_no: 사용자 번호
        query: 검색 쿼리
        n_results: 반환할 결과 수
        db: 데이터베이스 세션
        
    Returns:
        유사한 투표 기록
    """
    try:
        vector_service = get_vector_db_service()
        
        # 유사한 투표 검색
        similar_votes = vector_service.search_similar_votes(emp_no, query, n_results)
        
        logger.info(f"Found {len(similar_votes)} similar votes for user {emp_no}")
        
        return {
            "emp_no": emp_no,
            "query": query,
            "result_count": len(similar_votes),
            "similar_votes": similar_votes
        }
        
    except Exception as e:
        logger.error(f"Error searching similar votes: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/similar-restaurants")
async def search_similar_restaurants(
    query: str = Query(..., description="Search query"),
    n_results: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """
    유사한 식당 검색
    
    Args:
        query: 검색 쿼리
        n_results: 반환할 결과 수
        db: 데이터베이스 세션
        
    Returns:
        유사한 식당 리스트
    """
    try:
        vector_service = get_vector_db_service()
        
        # 유사한 식당 검색
        similar_restaurants = vector_service.search_similar_restaurants(query, n_results)
        
        logger.info(f"Found {len(similar_restaurants)} similar restaurants")
        
        return {
            "query": query,
            "result_count": len(similar_restaurants),
            "restaurants": similar_restaurants
        }
        
    except Exception as e:
        logger.error(f"Error searching similar restaurants: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/user-data/{emp_no}")
async def delete_user_data(
    emp_no: str,
    db: Session = Depends(get_db)
):
    """
    사용자 데이터 삭제
    
    Args:
        emp_no: 사용자 번호
        db: 데이터베이스 세션
        
    Returns:
        삭제 결과
    """
    try:
        vector_service = get_vector_db_service()
        
        # 사용자 데이터 삭제
        success = vector_service.delete_user_data(emp_no)
        
        if success:
            logger.info(f"Successfully deleted data for user {emp_no}")
            return {
                "success": True,
                "message": f"User data deleted for {emp_no}"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to delete user data")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    """개인화 추천 서비스 상태 확인"""
    try:
        vector_service = get_vector_db_service()
        
        # 간단한 테스트 쿼리
        test_results = vector_service.search_similar_restaurants("테스트", n_results=1)
        
        return {
            "status": "healthy",
            "vector_db": "connected",
            "embedding_model": "loaded",
            "test_query": "successful"
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }
