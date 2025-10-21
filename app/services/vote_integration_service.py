"""
Vote Integration Service - 기존 투표 시스템과 벡터 DB 통합
"""
from typing import Dict, Any, List, Optional
import logging
from sqlalchemy.orm import Session

from app.services.vector_db_service import VectorDBService
from app.models.postgres import UserDateVote, PlaceVote
# from app.services.place_service import PlaceService  # 임시 주석 처리

logger = logging.getLogger(__name__)

class VoteIntegrationService:
    """투표 시스템 통합 서비스"""
    
    def __init__(self):
        self.vector_service = VectorDBService()
        # self.place_service = PlaceService()  # 임시 주석 처리
        logger.info("VoteIntegrationService initialized")
    
    def sync_vote_to_vector_db(self, vote_data: Dict[str, Any]) -> bool:
        """
        투표 데이터를 벡터 DB에 동기화
        
        Args:
            vote_data: 투표 데이터
            
        Returns:
            동기화 성공 여부
        """
        try:
            # 투표 데이터를 벡터로 변환하여 저장
            doc_id = self.vector_service.create_vote_embedding(vote_data)
            
            logger.info(f"Vote synced to vector DB: {doc_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error syncing vote to vector DB: {str(e)}")
            return False
    
    def sync_restaurant_to_vector_db(self, restaurant_data: Dict[str, Any]) -> bool:
        """
        식당 데이터를 벡터 DB에 동기화
        
        Args:
            restaurant_data: 식당 데이터
            
        Returns:
            동기화 성공 여부
        """
        try:
            # 식당 데이터를 벡터로 변환하여 저장
            doc_id = self.vector_service.create_restaurant_embedding(restaurant_data)
            
            logger.info(f"Restaurant synced to vector DB: {doc_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error syncing restaurant to vector DB: {str(e)}")
            return False
    
    def get_user_vote_history_from_db(self, emp_no: str, db: Session) -> List[Dict[str, Any]]:
        """
        데이터베이스에서 사용자 투표 기록 조회
        
        Args:
            emp_no: 사용자 번호
            db: 데이터베이스 세션
            
        Returns:
            사용자 투표 기록 리스트
        """
        try:
            # UserDateVote에서 사용자 투표 기록 조회
            user_votes = db.query(UserDateVote).filter(
                UserDateVote.emp_no == emp_no
            ).all()
            
            vote_history = []
            for vote in user_votes:
                vote_data = {
                    "emp_no": vote.emp_no,
                    "place_name": vote.place_nm,
                    "menu_type": vote.menu_type,
                    "date": vote.vote_date.strftime("%Y-%m-%d") if vote.vote_date else None,
                    "vote_type": "date_vote",
                    "created_at": vote.created_at.isoformat() if vote.created_at else None
                }
                vote_history.append(vote_data)
            
            # PlaceVote에서 사용자 투표 기록 조회
            place_votes = db.query(PlaceVote).filter(
                PlaceVote.emp_no == emp_no
            ).all()
            
            for vote in place_votes:
                vote_data = {
                    "emp_no": vote.emp_no,
                    "place_name": vote.place_nm,
                    "menu_type": vote.menu_type,
                    "date": vote.vote_date.strftime("%Y-%m-%d") if vote.vote_date else None,
                    "vote_type": "place_vote",
                    "created_at": vote.created_at.isoformat() if vote.created_at else None
                }
                vote_history.append(vote_data)
            
            logger.info(f"Retrieved {len(vote_history)} votes from database for user {emp_no}")
            return vote_history
            
        except Exception as e:
            logger.error(f"Error getting user vote history from DB: {str(e)}")
            return []
    
    def sync_user_votes_to_vector_db(self, emp_no: str, db: Session) -> int:
        """
        사용자의 모든 투표 기록을 벡터 DB에 동기화
        
        Args:
            emp_no: 사용자 번호
            db: 데이터베이스 세션
            
        Returns:
            동기화된 투표 수
        """
        try:
            # 데이터베이스에서 사용자 투표 기록 조회
            vote_history = self.get_user_vote_history_from_db(emp_no, db)
            
            synced_count = 0
            for vote_data in vote_history:
                if self.sync_vote_to_vector_db(vote_data):
                    synced_count += 1
            
            logger.info(f"Synced {synced_count} votes to vector DB for user {emp_no}")
            return synced_count
            
        except Exception as e:
            logger.error(f"Error syncing user votes to vector DB: {str(e)}")
            return 0
    
    def get_personalized_recommendations_for_user(self, emp_no: str, query_text: str = None) -> List[Dict[str, Any]]:
        """
        사용자에게 개인화된 추천 생성
        
        Args:
            emp_no: 사용자 번호
            query_text: 검색 쿼리
            
        Returns:
            개인화된 추천 리스트
        """
        try:
            # 벡터 DB에서 개인화된 추천 생성
            recommendations = self.vector_service.get_personalized_recommendations(
                emp_no=emp_no,
                query_text=query_text
            )
            
            logger.info(f"Generated {len(recommendations)} personalized recommendations for user {emp_no}")
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating personalized recommendations: {str(e)}")
            return []
    
    def analyze_user_preferences(self, emp_no: str, db: Session) -> Dict[str, Any]:
        """
        사용자 선호도 분석
        
        Args:
            emp_no: 사용자 번호
            db: 데이터베이스 세션
            
        Returns:
            사용자 선호도 분석 결과
        """
        try:
            # 사용자 투표 기록 조회
            vote_history = self.get_user_vote_history_from_db(emp_no, db)
            
            if not vote_history:
                return {
                    "emp_no": emp_no,
                    "total_votes": 0,
                    "preferences": {},
                    "message": "No vote history found"
                }
            
            # 선호도 분석
            preferences = {
                "favorite_menu_types": {},
                "favorite_places": {},
                "vote_frequency": len(vote_history),
                "recent_votes": vote_history[-5:] if len(vote_history) > 5 else vote_history
            }
            
            for vote in vote_history:
                # 메뉴 타입 선호도
                menu_type = vote.get("menu_type")
                if menu_type:
                    preferences["favorite_menu_types"][menu_type] = preferences["favorite_menu_types"].get(menu_type, 0) + 1
                
                # 장소 선호도
                place_name = vote.get("place_name")
                if place_name:
                    preferences["favorite_places"][place_name] = preferences["favorite_places"].get(place_name, 0) + 1
            
            # 가장 선호하는 메뉴 타입과 장소 찾기
            if preferences["favorite_menu_types"]:
                preferences["top_menu_type"] = max(preferences["favorite_menu_types"], key=preferences["favorite_menu_types"].get)
                preferences["top_menu_type_count"] = preferences["favorite_menu_types"][preferences["top_menu_type"]]
            
            if preferences["favorite_places"]:
                preferences["top_place"] = max(preferences["favorite_places"], key=preferences["favorite_places"].get)
                preferences["top_place_count"] = preferences["favorite_places"][preferences["top_place"]]
            
            logger.info(f"Analyzed preferences for user {emp_no}: {preferences['vote_frequency']} votes")
            return {
                "emp_no": emp_no,
                "total_votes": len(vote_history),
                "preferences": preferences
            }
            
        except Exception as e:
            logger.error(f"Error analyzing user preferences: {str(e)}")
            return {
                "emp_no": emp_no,
                "total_votes": 0,
                "preferences": {},
                "error": str(e)
            }
    
    def get_similar_users(self, emp_no: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        유사한 사용자 찾기
        
        Args:
            emp_no: 사용자 번호
            limit: 반환할 최대 사용자 수
            
        Returns:
            유사한 사용자 리스트
        """
        try:
            # 사용자의 투표 기록을 기반으로 유사한 사용자 찾기
            user_votes = self.vector_service.get_user_vote_history(emp_no, limit=50)
            
            if not user_votes:
                return []
            
            # 사용자의 선호도 텍스트 생성
            user_preferences = self.vector_service._analyze_user_preferences(user_votes)
            preference_text = f"선호 메뉴: {list(user_preferences.get('favorite_menu_types', {}).keys())}"
            
            # 유사한 투표 기록 검색
            similar_votes = self.vector_service.search_similar_votes(emp_no, preference_text, limit * 2)
            
            # 다른 사용자들의 투표 기록 수집
            similar_users = {}
            for vote in similar_votes:
                vote_emp_no = vote.get("metadata", {}).get("emp_no")
                if vote_emp_no and vote_emp_no != emp_no:
                    if vote_emp_no not in similar_users:
                        similar_users[vote_emp_no] = {
                            "emp_no": vote_emp_no,
                            "similarity_score": 0,
                            "common_preferences": []
                        }
                    
                    # 유사도 점수 계산
                    distance = vote.get("distance", 1.0)
                    similarity_score = 1.0 - distance
                    similar_users[vote_emp_no]["similarity_score"] += similarity_score
                    
                    # 공통 선호도 추가
                    menu_type = vote.get("metadata", {}).get("menu_type")
                    if menu_type and menu_type not in similar_users[vote_emp_no]["common_preferences"]:
                        similar_users[vote_emp_no]["common_preferences"].append(menu_type)
            
            # 유사도 점수 순으로 정렬
            similar_users_list = list(similar_users.values())
            similar_users_list.sort(key=lambda x: x["similarity_score"], reverse=True)
            
            logger.info(f"Found {len(similar_users_list)} similar users for {emp_no}")
            return similar_users_list[:limit]
            
        except Exception as e:
            logger.error(f"Error finding similar users: {str(e)}")
            return []
