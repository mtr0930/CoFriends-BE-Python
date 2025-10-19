"""
MCP (Model Context Protocol) 툴 구현
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.services.vote_service import VoteService
from app.services.place_service import PlaceService
from app.services.menu_service import MenuService
from app.services.user_service import UserService


class MCPTools:
    """MCP 툴 모음 - AI가 호출할 수 있는 데이터 조회 툴들"""
    
    def __init__(self, db: Session):
        self.db = db
        self.vote_service = VoteService(db)
        self.place_service = PlaceService(db, None)
        self.menu_service = MenuService(db)
        self.user_service = UserService(db)
    
    def get_vote_results(self, month: str) -> Dict[str, Any]:
        """
        특정 월의 투표 결과 조회
        
        Args:
            month: 투표 월 (YYYY-MM 형식)
            
        Returns:
            투표 결과 데이터
        """
        try:
            vote_results = self.vote_service.get_vote_results(month)
            
            # 투표 통계 계산
            total_votes = sum(vote_results.get("menu_votes", {}).values())
            menu_ranking = sorted(
                vote_results.get("menu_votes", {}).items(),
                key=lambda x: x[1],
                reverse=True
            )
            
            return {
                "month": month,
                "total_votes": total_votes,
                "menu_ranking": menu_ranking,
                "vote_results": vote_results,
                "status": "success"
            }
            
        except Exception as e:
            return {
                "month": month,
                "error": str(e),
                "status": "error"
            }
    
    def get_user_vote_history(self, emp_no: str) -> Dict[str, Any]:
        """
        사용자의 투표 이력 조회
        
        Args:
            emp_no: 사용자 사번
            
        Returns:
            사용자 투표 이력 데이터
        """
        try:
            vote_history = self.vote_service.get_user_vote_history(emp_no)
            
            # 최근 투표 분석
            recent_votes = vote_history[-1] if vote_history else None
            
            return {
                "emp_no": emp_no,
                "vote_history": vote_history,
                "recent_votes": recent_votes,
                "total_votes": len(vote_history),
                "status": "success"
            }
            
        except Exception as e:
            return {
                "emp_no": emp_no,
                "error": str(e),
                "status": "error"
            }
    
    def get_past_dinner_info(self, emp_no: str, months: int = 3) -> Dict[str, Any]:
        """
        과거 회식 정보 조회
        
        Args:
            emp_no: 사용자 사번
            months: 조회할 개월 수
            
        Returns:
            과거 회식 정보 데이터
        """
        try:
            past_dinners = self.vote_service.get_past_dinner_history(emp_no, months)
            
            # 최근 회식 정보
            latest_dinner = past_dinners[0] if past_dinners else None
            
            return {
                "emp_no": emp_no,
                "past_dinners": past_dinners,
                "latest_dinner": latest_dinner,
                "total_dinners": len(past_dinners),
                "status": "success"
            }
            
        except Exception as e:
            return {
                "emp_no": emp_no,
                "error": str(e),
                "status": "error"
            }
    
    def get_restaurant_recommendations(self, emp_no: str, menu_types: List[str] = None) -> Dict[str, Any]:
        """
        식당 추천 조회
        
        Args:
            emp_no: 사용자 사번
            menu_types: 선호 메뉴 타입 리스트
            
        Returns:
            식당 추천 데이터
        """
        try:
            # 사용자 선호도 조회
            user_preferences = self.vote_service.get_user_preferences(emp_no)
            
            # 선호 메뉴 타입 설정
            if not menu_types:
                menu_types = user_preferences.get("menu_votes", [])
            
            # 메뉴 타입별 식당 추천
            recommendations = []
            for menu_type in menu_types:
                places = self.place_service.get_places_by_menu_type(menu_type)
                recommendations.extend(places)
            
            return {
                "emp_no": emp_no,
                "menu_types": menu_types,
                "recommendations": recommendations,
                "total_recommendations": len(recommendations),
                "status": "success"
            }
            
        except Exception as e:
            return {
                "emp_no": emp_no,
                "error": str(e),
                "status": "error"
            }
    
    def get_vote_status(self, month: str) -> Dict[str, Any]:
        """
        투표 상태 조회
        
        Args:
            month: 투표 월
            
        Returns:
            투표 상태 데이터
        """
        try:
            # 전체 사용자 수
            total_users = self.user_service.get_active_user_count()
            
            # 투표한 사용자 수
            voted_users = self.vote_service.get_voted_user_count(month)
            
            # 투표율 계산
            vote_rate = (voted_users / total_users * 100) if total_users > 0 else 0
            
            return {
                "month": month,
                "total_users": total_users,
                "voted_users": voted_users,
                "vote_rate": round(vote_rate, 1),
                "status": "success"
            }
            
        except Exception as e:
            return {
                "month": month,
                "error": str(e),
                "status": "error"
            }
    
    def get_menu_types(self) -> Dict[str, Any]:
        """
        사용 가능한 메뉴 타입 조회
        
        Returns:
            메뉴 타입 데이터
        """
        try:
            menu_types = self.menu_service.get_all_menu_types()
            
            return {
                "menu_types": menu_types,
                "total_types": len(menu_types),
                "status": "success"
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "status": "error"
            }
    
    def get_user_preferences(self, emp_no: str) -> Dict[str, Any]:
        """
        사용자 선호도 조회
        
        Args:
            emp_no: 사용자 사번
            
        Returns:
            사용자 선호도 데이터
        """
        try:
            preferences = self.vote_service.get_user_preferences(emp_no)
            
            return {
                "emp_no": emp_no,
                "preferences": preferences,
                "status": "success"
            }
            
        except Exception as e:
            return {
                "emp_no": emp_no,
                "error": str(e),
                "status": "error"
            }
