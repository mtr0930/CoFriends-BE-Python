"""
날짜 및 메뉴 추천 서비스
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import random
from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger(__name__)

class DateMenuRecommendationService:
    """날짜 및 메뉴 추천 서비스"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def get_date_recommendations(self, emp_no: str, context: str = None) -> List[Dict[str, Any]]:
        """
        날짜 추천 생성
        
        Args:
            emp_no: 사용자 사번
            context: 추천 컨텍스트 (예: "회식", "점심", "저녁")
            
        Returns:
            날짜 추천 리스트
        """
        try:
            # 현재 날짜 기준으로 추천 날짜 생성
            today = datetime.now()
            recommendations = []
            
            # 다음 2주간의 평일 추천
            for i in range(1, 15):  # 2주간
                date = today + timedelta(days=i)
                if date.weekday() < 5:  # 평일만
                    # 날짜별 추천 점수 계산
                    score = self._calculate_date_score(date, emp_no, context)
                    
                    recommendations.append({
                        "date": date.strftime("%Y-%m-%d"),
                        "day_of_week": self._get_korean_day(date.weekday()),
                        "score": score,
                        "reason": self._get_date_reason(date, context),
                        "is_weekend": False,
                        "weather_forecast": self._get_weather_forecast(date)
                    })
            
            # 점수 기준으로 정렬하고 상위 5개 반환
            recommendations.sort(key=lambda x: x["score"], reverse=True)
            return recommendations[:5]
            
        except Exception as e:
            self.logger.error(f"Error generating date recommendations: {str(e)}")
            return []
    
    def get_menu_recommendations(self, emp_no: str, context: str = None, season: str = None) -> List[Dict[str, Any]]:
        """
        메뉴 추천 생성
        
        Args:
            emp_no: 사용자 사번
            context: 추천 컨텍스트
            season: 계절 정보
            
        Returns:
            메뉴 추천 리스트
        """
        try:
            # 계절별 메뉴 추천
            seasonal_menus = self._get_seasonal_menus(season)
            
            # 인기 메뉴 추천
            popular_menus = self._get_popular_menus()
            
            # 사용자 맞춤 메뉴 추천
            personalized_menus = self._get_personalized_menus(emp_no)
            
            # 추천 통합
            all_menus = seasonal_menus + popular_menus + personalized_menus
            
            # 중복 제거 및 점수 계산
            unique_menus = {}
            for menu in all_menus:
                menu_name = menu["name"]
                if menu_name not in unique_menus:
                    unique_menus[menu_name] = menu
                else:
                    # 점수 합산
                    unique_menus[menu_name]["score"] += menu["score"]
                    unique_menus[menu_name]["sources"].extend(menu["sources"])
            
            # 점수 기준으로 정렬하고 상위 8개 반환
            recommendations = list(unique_menus.values())
            recommendations.sort(key=lambda x: x["score"], reverse=True)
            return recommendations[:8]
            
        except Exception as e:
            self.logger.error(f"Error generating menu recommendations: {str(e)}")
            return []
    
    def get_comprehensive_recommendations(self, emp_no: str, query: str = None) -> Dict[str, Any]:
        """
        종합 추천 (날짜 + 메뉴 + 식당)
        
        Args:
            emp_no: 사용자 사번
            query: 사용자 쿼리
            
        Returns:
            종합 추천 결과
        """
        try:
            # 컨텍스트 분석
            context = self._analyze_context(query) if query else None
            season = self._get_current_season()
            
            # 각각의 추천 생성
            date_recs = self.get_date_recommendations(emp_no, context)
            menu_recs = self.get_menu_recommendations(emp_no, context, season)
            
            # 추천 조합 생성
            combinations = self._generate_recommendation_combinations(date_recs, menu_recs)
            
            return {
                "date_recommendations": date_recs,
                "menu_recommendations": menu_recs,
                "combinations": combinations,
                "context": context,
                "season": season,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error generating comprehensive recommendations: {str(e)}")
            return {
                "date_recommendations": [],
                "menu_recommendations": [],
                "combinations": [],
                "error": str(e)
            }
    
    def _calculate_date_score(self, date: datetime, emp_no: str, context: str) -> float:
        """날짜 추천 점수 계산"""
        score = 0.5  # 기본 점수
        
        # 요일별 가중치
        weekday_weights = {0: 0.8, 1: 0.9, 2: 1.0, 3: 1.0, 4: 0.9}  # 월~금
        score *= weekday_weights.get(date.weekday(), 0.5)
        
        # 컨텍스트별 가중치
        if context:
            if "회식" in context or "저녁" in context:
                if date.weekday() in [1, 2, 3]:  # 화, 수, 목
                    score *= 1.2
            elif "점심" in context:
                if date.weekday() in [0, 1, 2, 3, 4]:  # 평일
                    score *= 1.1
        
        # 랜덤 요소 추가
        score += random.uniform(0, 0.3)
        
        return min(score, 1.0)
    
    def _get_date_reason(self, date: datetime, context: str) -> str:
        """날짜 추천 이유 생성"""
        day_name = self._get_korean_day(date.weekday())
        
        if context and "회식" in context:
            if date.weekday() in [1, 2, 3]:  # 화, 수, 목
                return f"{day_name}은 회식하기 좋은 날입니다."
            else:
                return f"{day_name}도 좋은 선택입니다."
        else:
            return f"{day_name} 추천입니다."
    
    def _get_korean_day(self, weekday: int) -> str:
        """요일을 한국어로 변환"""
        days = ["월", "화", "수", "목", "금", "토", "일"]
        return days[weekday]
    
    def _get_weather_forecast(self, date: datetime) -> str:
        """날씨 예보 (더미 데이터)"""
        forecasts = ["맑음", "흐림", "비", "눈"]
        return random.choice(forecasts)
    
    def _get_seasonal_menus(self, season: str) -> List[Dict[str, Any]]:
        """계절별 메뉴 추천"""
        seasonal_menu_data = {
            "봄": [
                {"name": "한식", "score": 0.9, "reason": "봄에는 따뜻한 한식이 좋습니다"},
                {"name": "일식", "score": 0.8, "reason": "봄철 신선한 회가 맛있습니다"},
                {"name": "중식", "score": 0.7, "reason": "봄에는 중식도 좋습니다"}
            ],
            "여름": [
                {"name": "일식", "score": 0.9, "reason": "여름에는 시원한 회가 좋습니다"},
                {"name": "중식", "score": 0.8, "reason": "여름에는 시원한 중식이 좋습니다"},
                {"name": "양식", "score": 0.7, "reason": "여름에는 가벼운 양식이 좋습니다"}
            ],
            "가을": [
                {"name": "한식", "score": 0.9, "reason": "가을에는 따뜻한 한식이 좋습니다"},
                {"name": "중식", "score": 0.8, "reason": "가을에는 중식이 좋습니다"},
                {"name": "일식", "score": 0.7, "reason": "가을에는 일식도 좋습니다"}
            ],
            "겨울": [
                {"name": "한식", "score": 0.9, "reason": "겨울에는 따뜻한 한식이 좋습니다"},
                {"name": "중식", "score": 0.8, "reason": "겨울에는 뜨거운 중식이 좋습니다"},
                {"name": "양식", "score": 0.6, "reason": "겨울에는 양식도 좋습니다"}
            ]
        }
        
        menus = seasonal_menu_data.get(season, [])
        for menu in menus:
            menu["sources"] = ["seasonal"]
        return menus
    
    def _get_popular_menus(self) -> List[Dict[str, Any]]:
        """인기 메뉴 추천"""
        popular_menus = [
            {"name": "한식", "score": 0.8, "reason": "항상 인기 있는 한식", "sources": ["popular"]},
            {"name": "중식", "score": 0.7, "reason": "많이 선택하는 중식", "sources": ["popular"]},
            {"name": "일식", "score": 0.6, "reason": "인기 있는 일식", "sources": ["popular"]},
            {"name": "양식", "score": 0.5, "reason": "선호하는 양식", "sources": ["popular"]}
        ]
        return popular_menus
    
    def _get_personalized_menus(self, emp_no: str) -> List[Dict[str, Any]]:
        """개인화 메뉴 추천 (사용자 히스토리 기반)"""
        # 실제로는 사용자의 과거 선택 이력을 분석
        personalized_menus = [
            {"name": "한식", "score": 0.9, "reason": "자주 선택하시는 한식", "sources": ["personalized"]},
            {"name": "중식", "score": 0.7, "reason": "선호하시는 중식", "sources": ["personalized"]}
        ]
        return personalized_menus
    
    def _analyze_context(self, query: str) -> str:
        """쿼리 컨텍스트 분석"""
        if not query:
            return None
        
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["회식", "저녁", "밤"]):
            return "회식"
        elif any(word in query_lower for word in ["점심", "낮"]):
            return "점심"
        elif any(word in query_lower for word in ["아침", "모닝"]):
            return "아침"
        
        return None
    
    def _get_current_season(self) -> str:
        """현재 계절 반환"""
        month = datetime.now().month
        if month in [3, 4, 5]:
            return "봄"
        elif month in [6, 7, 8]:
            return "여름"
        elif month in [9, 10, 11]:
            return "가을"
        else:
            return "겨울"
    
    def _generate_recommendation_combinations(self, date_recs: List[Dict], menu_recs: List[Dict]) -> List[Dict[str, Any]]:
        """추천 조합 생성"""
        combinations = []
        
        # 상위 3개 날짜와 상위 3개 메뉴 조합
        for i, date_rec in enumerate(date_recs[:3]):
            for j, menu_rec in enumerate(menu_recs[:3]):
                combination_score = (date_rec["score"] + menu_rec["score"]) / 2
                
                combinations.append({
                    "date": date_rec["date"],
                    "day_of_week": date_rec["day_of_week"],
                    "menu": menu_rec["name"],
                    "score": combination_score,
                    "reason": f"{date_rec['reason']} {menu_rec['reason']}",
                    "weather": date_rec.get("weather_forecast", "맑음")
                })
        
        # 점수 기준으로 정렬
        combinations.sort(key=lambda x: x["score"], reverse=True)
        return combinations[:5]
