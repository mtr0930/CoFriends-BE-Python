"""
날짜 및 메뉴 추천 서비스
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import random
from sqlalchemy.orm import Session
from sqlalchemy import text, func, desc, and_
from app.models.postgres import User, Menu, Place, UserMenuVote, UserPlaceVote, UserDateVote, PlaceVote
from app.core.database import get_db
from app.utils.timezone_utils import get_korean_now, get_korean_date_str, get_korean_month_str

logger = logging.getLogger(__name__)

class DateMenuRecommendationService:
    """날짜 및 메뉴 추천 서비스"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def get_date_recommendations(self, emp_no: str, context: str = None) -> List[Dict[str, Any]]:
        """
        날짜 추천 생성 (실제 DB 데이터 기반)
        
        Args:
            emp_no: 사용자 사번
            context: 추천 컨텍스트 (예: "회식", "점심", "저녁")
            
        Returns:
            날짜 추천 리스트
        """
        try:
            db = next(get_db())
            
            # 한국 시간 기준으로 추천 날짜 생성
            today = get_korean_now()
            recommendations = []
            
            # 다음 2주간의 평일 추천
            for i in range(1, 15):  # 2주간
                date = today + timedelta(days=i)
                if date.weekday() < 5:  # 평일만
                    # 실제 DB에서 해당 날짜의 투표 데이터 조회
                    date_str = date.strftime("%Y-%m-%d")
                    db_score = self._get_date_score_from_db(db, date_str, emp_no)
                    
                    # 사용자 요일별 선호도 조회
                    months = self._get_recent_months(3)
                    user_weekday_prefs = self._get_user_weekday_preferences(db, emp_no, months)
                    user_weekday_score = user_weekday_prefs.get(date.weekday(), 0)
                    
                    # 날짜별 추천 점수 계산 (DB 데이터 + 사용자 선호도)
                    score = self._calculate_date_score(date, emp_no, context, db_score)
                    
                    # 사용자 요일별 선호도 가중치 적용
                    if user_weekday_score > 0:
                        score *= (1 + user_weekday_score * 0.2)  # 사용자 선호도 가중치
                    
                    recommendations.append({
                        "date": date_str,
                        "day_of_week": self._get_korean_day(date.weekday()),
                        "score": score,
                        "reason": self._get_date_reason(date, context),
                        "is_weekend": False,
                        "weather_forecast": self._get_weather_forecast(date),
                        "db_votes": db_score.get("vote_count", 0),
                        "popularity": db_score.get("popularity", 0.0),
                        "user_weekday_preference": user_weekday_score,
                        "is_holiday": db_score.get("is_holiday", False)
                    })
            
            # 점수 기준으로 정렬하고 상위 5개 반환
            recommendations.sort(key=lambda x: x["score"], reverse=True)
            return recommendations[:5]
            
        except Exception as e:
            self.logger.error(f"Error generating date recommendations: {str(e)}")
            return []
        finally:
            if 'db' in locals():
                db.close()
    
    def get_menu_recommendations(self, emp_no: str, context: str = None, season: str = None) -> List[Dict[str, Any]]:
        """
        메뉴 추천 생성 (실제 DB 데이터 기반)
        
        Args:
            emp_no: 사용자 사번
            context: 추천 컨텍스트
            season: 계절 정보
            
        Returns:
            메뉴 추천 리스트
        """
        try:
            db = next(get_db())
            
            # DB에서 실제 메뉴 데이터 조회
            db_menus = self._get_menus_from_db(db)
            
            # 계절별 메뉴 추천 (DB 데이터 기반)
            seasonal_menus = self._get_seasonal_menus_from_db(db, season)
            
            # 인기 메뉴 추천 (실제 투표 데이터 기반)
            popular_menus = self._get_popular_menus_from_db(db)
            
            # 사용자 맞춤 메뉴 추천 (사용자 히스토리 기반)
            personalized_menus = self._get_personalized_menus_from_db(db, emp_no)
            
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
        finally:
            if 'db' in locals():
                db.close()
    
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
    
    def _get_date_score_from_db(self, db: Session, date_str: str, emp_no: str) -> Dict[str, Any]:
        """DB에서 날짜별 투표 데이터 조회 (요일별 인기도 기반)"""
        try:
            # 현재 월과 이전 2개월 데이터 조회
            months = self._get_recent_months(3)
            
            # 해당 날짜의 요일 추출
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            weekday = date_obj.weekday()  # 0=월요일, 6=일요일
            
            # 공휴일 체크 (간단한 구현)
            is_holiday = self._is_holiday(date_obj)
            if is_holiday:
                return {"vote_count": 0, "user_voted": False, "popularity": 0.0, "weekday_popularity": 0.0, "is_holiday": True}
            
            # 해당 날짜의 총 투표 수 조회
            vote_count = db.query(func.count(UserDateVote.id)).filter(
                and_(
                    UserDateVote.preferred_date == date_str,
                    UserDateVote.vote_month.in_(months)
                )
            ).scalar() or 0
            
            # 해당 사용자의 해당 날짜 투표 여부
            user_voted = db.query(UserDateVote).filter(
                and_(
                    UserDateVote.emp_no == emp_no,
                    UserDateVote.preferred_date == date_str,
                    UserDateVote.vote_month.in_(months)
                )
            ).first() is not None
            
            # 요일별 인기도 계산 (사용자들이 많이 투표한 요일)
            weekday_popularity = self._get_weekday_popularity(db, weekday, months)
            
            return {
                "vote_count": vote_count,
                "user_voted": user_voted,
                "popularity": weekday_popularity,
                "weekday_popularity": weekday_popularity,
                "is_holiday": False
            }
        except Exception as e:
            self.logger.error(f"Error getting date score from DB: {str(e)}")
            return {"vote_count": 0, "user_voted": False, "popularity": 0.0, "weekday_popularity": 0.0, "is_holiday": False}
    
    def _get_menus_from_db(self, db: Session) -> List[Dict[str, Any]]:
        """DB에서 모든 메뉴 조회"""
        try:
            menus = db.query(Menu).all()
            return [
                {
                    "menu_id": menu.menu_id,
                    "menu_type": menu.menu_type,
                    "created_at": menu.created_at.isoformat() if menu.created_at else None
                }
                for menu in menus
            ]
        except Exception as e:
            self.logger.error(f"Error getting menus from DB: {str(e)}")
            return []
    
    def _get_seasonal_menus_from_db(self, db: Session, season: str) -> List[Dict[str, Any]]:
        """DB에서 계절별 메뉴 추천 (월별 선호도 + 이전달 가중치)"""
        try:
            # 최근 3개월 데이터 조회
            months = self._get_recent_months(3)
            current_month = months[0]  # 현재 월
            previous_month = months[1] if len(months) > 1 else None  # 이전 월
            
            # 월별 메뉴 투표 수 조회
            monthly_votes = {}
            for month in months:
                votes = db.query(
                    Menu.menu_type,
                    func.count(UserMenuVote.vote_id).label('vote_count')
                ).join(UserMenuVote, Menu.menu_id == UserMenuVote.menu_id).filter(
                    UserMenuVote.vote_month == month
                ).group_by(Menu.menu_type).all()
                
                monthly_votes[month] = {menu_type: count for menu_type, count in votes}
            
            # 모든 메뉴 타입 수집
            all_menu_types = set()
            for month_data in monthly_votes.values():
                all_menu_types.update(month_data.keys())
            
            menus = []
            for menu_type in all_menu_types:
                # 현재 월 투표 수
                current_votes = monthly_votes.get(current_month, {}).get(menu_type, 0)
                
                # 이전 달 투표 수 (가중치 감소)
                previous_votes = 0
                if previous_month and previous_month in monthly_votes:
                    previous_votes = monthly_votes[previous_month].get(menu_type, 0)
                
                # 투표 수 기반 점수 계산 (투표수가 더 강한 가중치)
                total_votes = current_votes + (previous_votes * 0.3)  # 이전달은 30% 가중치
                base_score = total_votes * 0.15  # 투표수 가중치 증가
                
                # 계절별 가중치 적용
                seasonal_weight = self._get_seasonal_weight(menu_type, season)
                score = base_score * seasonal_weight
                
                menus.append({
                    "name": menu_type,
                    "score": score,
                    "reason": f"{season}에 인기 있는 {menu_type} (투표: {current_votes}회)",
                    "sources": ["seasonal", "db"],
                    "vote_count": current_votes,
                    "previous_month_votes": previous_votes
                })
            
            return menus
        except Exception as e:
            self.logger.error(f"Error getting seasonal menus from DB: {str(e)}")
            return []
    
    def _get_popular_menus_from_db(self, db: Session) -> List[Dict[str, Any]]:
        """DB에서 인기 메뉴 조회 (월별 데이터 기반)"""
        try:
            # 최근 3개월 데이터 조회
            months = self._get_recent_months(3)
            
            popular_menus = db.query(
                Menu.menu_type,
                func.count(UserMenuVote.vote_id).label('vote_count')
            ).join(UserMenuVote, Menu.menu_id == UserMenuVote.menu_id).filter(
                UserMenuVote.vote_month.in_(months)
            ).group_by(Menu.menu_type).order_by(desc('vote_count')).limit(10).all()
            
            menus = []
            for menu_type, vote_count in popular_menus:
                score = vote_count * 0.1
                menus.append({
                    "name": menu_type,
                    "score": score,
                    "reason": f"최근 인기 있는 {menu_type} (투표: {vote_count}회)",
                    "sources": ["popular", "db"],
                    "vote_count": vote_count
                })
            
            return menus
        except Exception as e:
            self.logger.error(f"Error getting popular menus from DB: {str(e)}")
            return []
    
    def _get_personalized_menus_from_db(self, db: Session, emp_no: str) -> List[Dict[str, Any]]:
        """DB에서 사용자 맞춤 메뉴 추천 (사용자 투표 기록 기반 강화)"""
        try:
            # 최근 3개월 데이터 조회
            months = self._get_recent_months(3)
            
            # 사용자의 과거 메뉴 투표 이력 조회 (월별 데이터)
            user_votes = db.query(
                Menu.menu_type,
                func.count(UserMenuVote.vote_id).label('vote_count')
            ).join(UserMenuVote, Menu.menu_id == UserMenuVote.menu_id).join(
                User, UserMenuVote.user_id == User.user_id
            ).filter(
                and_(
                    User.emp_no == emp_no,
                    UserMenuVote.vote_month.in_(months)
                )
            ).group_by(Menu.menu_type).order_by(desc('vote_count')).all()
            
            # 사용자의 요일별 선호도 조회
            user_weekday_preferences = self._get_user_weekday_preferences(db, emp_no, months)
            
            menus = []
            for menu_type, vote_count in user_votes:
                # 개인화 가중치 강화 (사용자 투표 기록 기반)
                personalized_score = vote_count * 0.3  # 개인화 가중치 증가
                
                # 사용자 선호도 보너스 (자주 선택한 메뉴)
                if vote_count >= 3:  # 3회 이상 선택한 메뉴
                    personalized_score *= 1.5
                elif vote_count >= 2:  # 2회 이상 선택한 메뉴
                    personalized_score *= 1.2
                
                menus.append({
                    "name": menu_type,
                    "score": personalized_score,
                    "reason": f"자주 선택하시는 {menu_type} (선택: {vote_count}회)",
                    "sources": ["personalized", "db"],
                    "vote_count": vote_count,
                    "user_preference": True
                })
            
            return menus
        except Exception as e:
            self.logger.error(f"Error getting personalized menus from DB: {str(e)}")
            return []
    
    def _get_seasonal_weight(self, menu_type: str, season: str) -> float:
        """메뉴 타입별 계절 가중치"""
        seasonal_weights = {
            "한식": {"봄": 1.2, "여름": 0.8, "가을": 1.3, "겨울": 1.4},
            "일식": {"봄": 1.0, "여름": 1.3, "가을": 1.1, "겨울": 0.9},
            "중식": {"봄": 1.1, "여름": 1.2, "가을": 1.0, "겨울": 1.1},
            "양식": {"봄": 1.0, "여름": 1.1, "가을": 0.9, "겨울": 0.8}
        }
        
        return seasonal_weights.get(menu_type, {}).get(season, 1.0)
    
    def _get_recent_months(self, count: int) -> List[str]:
        """최근 N개월의 YYYYMM 형식 리스트 반환 (한국 시간 기준)"""
        months = []
        current = get_korean_now()
        
        for i in range(count):
            month = current - timedelta(days=30 * i)
            months.append(month.strftime("%Y%m"))
        
        return months
    
    def _get_monthly_vote_counts(self, db: Session, months: List[str]) -> Dict[str, int]:
        """월별 투표 수 조회"""
        try:
            monthly_counts = {}
            for month in months:
                count = db.query(func.count(UserDateVote.id)).filter(
                    UserDateVote.vote_month == month
                ).scalar() or 0
                monthly_counts[month] = count
            
            return monthly_counts
        except Exception as e:
            self.logger.error(f"Error getting monthly vote counts: {str(e)}")
            return {}
    
    def _calculate_monthly_popularity(self, vote_count: int, monthly_data: Dict[str, int]) -> float:
        """월별 데이터를 고려한 인기도 계산 (동일 가중치)"""
        try:
            if not monthly_data or sum(monthly_data.values()) == 0:
                return 0.0
            
            # 동일 가중치 적용 (데이터가 적을 때)
            total_votes = sum(monthly_data.values())
            return vote_count / total_votes if total_votes > 0 else 0.0
            
        except Exception as e:
            self.logger.error(f"Error calculating monthly popularity: {str(e)}")
            return 0.0

    def _calculate_date_score(self, date: datetime, emp_no: str, context: str, db_score: Dict[str, Any] = None) -> float:
        """날짜 추천 점수 계산 (요일별 인기도 + 사용자 선호도)"""
        score = 0.5  # 기본 점수
        
        # 공휴일 체크
        if db_score and db_score.get("is_holiday", False):
            return 0.0  # 공휴일은 추천하지 않음
        
        # 요일별 가중치 (기본)
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
        
        # DB 데이터 기반 가중치 적용
        if db_score:
            # 요일별 인기도 (사용자들이 많이 투표한 요일)
            weekday_popularity = db_score.get("weekday_popularity", 0.0)
            score *= (1 + weekday_popularity * 0.5)  # 요일 인기도 가중치
            
            # 투표 수에 따른 가중치
            vote_count = db_score.get("vote_count", 0)
            if vote_count > 0:
                score *= (1 + min(vote_count * 0.1, 0.3))  # 최대 30% 증가
            
            # 사용자가 이미 투표한 날짜는 가중치 감소
            if db_score.get("user_voted", False):
                score *= 0.8
        
        # 랜덤 요소 추가
        score += random.uniform(0, 0.1)
        
        return min(score, 1.0)
    
    def _is_holiday(self, date: datetime) -> bool:
        """공휴일 체크 (간단한 구현)"""
        # 한국 주요 공휴일 (간단한 구현)
        holidays = [
            (1, 1),   # 신정
            (3, 1),   # 삼일절
            (5, 5),   # 어린이날
            (6, 6),   # 현충일
            (8, 15),  # 광복절
            (10, 3),  # 개천절
            (10, 9),  # 한글날
            (12, 25), # 크리스마스
        ]
        
        return (date.month, date.day) in holidays
    
    def _get_weekday_popularity(self, db: Session, weekday: int, months: List[str]) -> float:
        """요일별 인기도 계산 (사용자들이 많이 투표한 요일)"""
        try:
            # 해당 요일의 총 투표 수 조회
            weekday_votes = 0
            for month in months:
                # 해당 월의 해당 요일 투표 수 조회
                month_votes = db.query(func.count(UserDateVote.id)).filter(
                    and_(
                        UserDateVote.vote_month == month,
                        func.extract('dow', func.to_date(UserDateVote.preferred_date, 'YYYY-MM-DD')) == weekday
                    )
                ).scalar() or 0
                weekday_votes += month_votes
            
            # 전체 요일별 투표 수 조회
            total_weekday_votes = 0
            for wd in range(7):  # 0~6 (월~일)
                for month in months:
                    votes = db.query(func.count(UserDateVote.id)).filter(
                        and_(
                            UserDateVote.vote_month == month,
                            func.extract('dow', func.to_date(UserDateVote.preferred_date, 'YYYY-MM-DD')) == wd
                        )
                    ).scalar() or 0
                    total_weekday_votes += votes
            
            # 요일별 인기도 계산
            if total_weekday_votes > 0:
                return weekday_votes / total_weekday_votes
            else:
                return 0.0
                
        except Exception as e:
            self.logger.error(f"Error calculating weekday popularity: {str(e)}")
            return 0.0
    
    def _get_user_weekday_preferences(self, db: Session, emp_no: str, months: List[str]) -> Dict[int, int]:
        """사용자의 요일별 선호도 조회"""
        try:
            user_weekday_votes = {}
            
            for weekday in range(7):  # 0~6 (월~일)
                votes = 0
                for month in months:
                    month_votes = db.query(func.count(UserDateVote.id)).filter(
                        and_(
                            UserDateVote.emp_no == emp_no,
                            UserDateVote.vote_month == month,
                            func.extract('dow', func.to_date(UserDateVote.preferred_date, 'YYYY-MM-DD')) == weekday
                        )
                    ).scalar() or 0
                    votes += month_votes
                
                user_weekday_votes[weekday] = votes
            
            return user_weekday_votes
            
        except Exception as e:
            self.logger.error(f"Error getting user weekday preferences: {str(e)}")
            return {}
    
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
        """현재 계절 반환 (한국 시간 기준)"""
        month = get_korean_now().month
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
    
    def create_sample_data(self, emp_no: str = "EMP001"):
        """테스트용 샘플 데이터 생성"""
        try:
            db = next(get_db())
            
            # 사용자 생성
            user = db.query(User).filter(User.emp_no == emp_no).first()
            if not user:
                user = User(emp_no=emp_no, emp_nm="테스트사용자")
                db.add(user)
                db.commit()
                db.refresh(user)
            
            # 메뉴 데이터 생성
            menu_types = ["한식", "일식", "중식", "양식", "분식", "치킨", "피자", "족발"]
            for menu_type in menu_types:
                existing_menu = db.query(Menu).filter(Menu.menu_type == menu_type).first()
                if not existing_menu:
                    menu = Menu(menu_type=menu_type)
                    db.add(menu)
            
            db.commit()
            
            # 샘플 투표 데이터 생성 (월별 데이터 포함, 한국 시간 기준)
            import random
            from datetime import datetime, timedelta
            
            # 최근 3개월간의 랜덤 투표 데이터 생성
            months = self._get_recent_months(3)
            current_month = get_korean_month_str()
            
            for month in months:
                # 각 월별로 10-20개의 투표 데이터 생성
                vote_count = random.randint(10, 20)
                
                for _ in range(vote_count):
                    # 랜덤 날짜 생성 (해당 월 내)
                    if month == current_month:
                        # 현재 월은 오늘까지
                        max_days = get_korean_now().day
                    else:
                        # 이전 월은 30일까지
                        max_days = 30
                    
                    day = random.randint(1, max_days)
                    date_str = f"{month[:4]}-{month[4:6]}-{day:02d}"
                    
                    # 날짜 투표 생성
                    if random.random() < 0.3:  # 30% 확률로 투표
                        date_vote = UserDateVote(
                            emp_no=emp_no,
                            preferred_date=date_str,
                            vote_month=month
                        )
                        db.add(date_vote)
                    
                    # 메뉴 투표 생성
                    if random.random() < 0.4:  # 40% 확률로 투표
                        menu = db.query(Menu).filter(Menu.menu_type == random.choice(menu_types)).first()
                        if menu:
                            menu_vote = UserMenuVote(
                                user_id=user.user_id,
                                menu_id=menu.menu_id,
                                vote_month=month
                            )
                            db.add(menu_vote)
            
            db.commit()
            self.logger.info(f"샘플 데이터가 생성되었습니다. 사용자: {emp_no}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating sample data: {str(e)}")
            return False
        finally:
            if 'db' in locals():
                db.close()
