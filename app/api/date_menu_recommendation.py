"""
날짜 및 메뉴 추천 API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import logging

from app.core.database import get_db
from app.services.date_menu_recommendation_service import DateMenuRecommendationService
from app.schemas.personalized_recommendation import PersonalizedRecommendationRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/date-menu-recommendations", tags=["Date Menu Recommendations"])

@router.post("/dates")
async def get_date_recommendations(
    request: PersonalizedRecommendationRequest,
    db: Session = Depends(get_db)
):
    """
    날짜 추천 생성
    
    Args:
        request: 추천 요청 (emp_no, query_text)
        db: 데이터베이스 세션
        
    Returns:
        날짜 추천 리스트
    """
    try:
        service = DateMenuRecommendationService()
        
        recommendations = service.get_date_recommendations(
            emp_no=request.emp_no,
            context=request.query_text
        )
        
        logger.info(f"Generated {len(recommendations)} date recommendations for user {request.emp_no}")
        
        return {
            "recommendations": recommendations,
            "count": len(recommendations),
            "generated_at": service._get_current_season()
        }
        
    except Exception as e:
        logger.error(f"Error generating date recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/menus")
async def get_menu_recommendations(
    request: PersonalizedRecommendationRequest,
    db: Session = Depends(get_db)
):
    """
    메뉴 추천 생성
    
    Args:
        request: 추천 요청 (emp_no, query_text)
        db: 데이터베이스 세션
        
    Returns:
        메뉴 추천 리스트
    """
    try:
        service = DateMenuRecommendationService()
        
        recommendations = service.get_menu_recommendations(
            emp_no=request.emp_no,
            context=request.query_text
        )
        
        logger.info(f"Generated {len(recommendations)} menu recommendations for user {request.emp_no}")
        
        return {
            "recommendations": recommendations,
            "count": len(recommendations),
            "generated_at": service._get_current_season()
        }
        
    except Exception as e:
        logger.error(f"Error generating menu recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/comprehensive")
async def get_comprehensive_recommendations(
    request: PersonalizedRecommendationRequest,
    db: Session = Depends(get_db)
):
    """
    종합 추천 (날짜 + 메뉴 + 조합)
    
    Args:
        request: 추천 요청 (emp_no, query_text)
        db: 데이터베이스 세션
        
    Returns:
        종합 추천 결과
    """
    try:
        service = DateMenuRecommendationService()
        
        recommendations = service.get_comprehensive_recommendations(
            emp_no=request.emp_no,
            query=request.query_text
        )
        
        logger.info(f"Generated comprehensive recommendations for user {request.emp_no}")
        
        return recommendations
        
    except Exception as e:
        logger.error(f"Error generating comprehensive recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    """
    서비스 헬스 체크
    """
    try:
        service = DateMenuRecommendationService()
        return {
            "status": "healthy",
            "service": "date_menu_recommendation",
            "features": [
                "date_recommendations",
                "menu_recommendations", 
                "comprehensive_recommendations"
            ]
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
