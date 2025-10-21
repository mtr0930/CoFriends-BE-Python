"""
Vector Database Service - Chroma DB를 사용한 개인화 추천 시스템
"""
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Optional
import json
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class VectorDBService:
    """벡터 데이터베이스 서비스"""
    
    def __init__(self, persist_directory: str = "./chroma_db"):
        """
        VectorDBService 초기화
        
        Args:
            persist_directory: Chroma DB 데이터 저장 디렉토리
        """
        self.persist_directory = persist_directory
        
        # Chroma DB 클라이언트 초기화
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # 임베딩 모델 초기화 (한국어 지원 모델)
        self.embedding_model = SentenceTransformer('jhgan/ko-sroberta-multitask')
        
        # 컬렉션 초기화
        self.vote_collection = self._get_or_create_collection("user_votes")
        self.restaurant_collection = self._get_or_create_collection("restaurants")
        
        logger.info("VectorDBService initialized successfully")
    
    def _get_or_create_collection(self, name: str):
        """컬렉션 가져오기 또는 생성"""
        try:
            return self.client.get_collection(name)
        except:
            return self.client.create_collection(
                name=name,
                metadata={"description": f"Collection for {name}"}
            )
    
    def create_vote_embedding(self, vote_data: Dict[str, Any]) -> str:
        """
        투표 데이터를 벡터로 변환하여 저장
        
        Args:
            vote_data: 투표 데이터 (emp_no, place_name, menu_type, date, etc.)
            
        Returns:
            저장된 문서 ID
        """
        try:
            # 투표 데이터를 텍스트로 변환
            text_content = self._create_vote_text(vote_data)
            
            # 임베딩 생성
            embedding = self.embedding_model.encode(text_content).tolist()
            
            # 메타데이터 준비
            metadata = {
                "emp_no": vote_data.get("emp_no"),
                "place_name": vote_data.get("place_name"),
                "menu_type": vote_data.get("menu_type"),
                "date": vote_data.get("date"),
                "vote_type": vote_data.get("vote_type", "restaurant"),
                "created_at": datetime.now().isoformat(),
                "text_content": text_content
            }
            
            # 고유 ID 생성
            doc_id = f"vote_{vote_data.get('emp_no')}_{vote_data.get('place_name')}_{vote_data.get('date')}"
            
            # Chroma DB에 저장
            self.vote_collection.add(
                embeddings=[embedding],
                documents=[text_content],
                metadatas=[metadata],
                ids=[doc_id]
            )
            
            logger.info(f"Vote embedding created for user {vote_data.get('emp_no')}")
            return doc_id
            
        except Exception as e:
            logger.error(f"Error creating vote embedding: {str(e)}")
            raise
    
    def _create_vote_text(self, vote_data: Dict[str, Any]) -> str:
        """투표 데이터를 텍스트로 변환"""
        text_parts = []
        
        if vote_data.get("place_name"):
            text_parts.append(f"식당: {vote_data['place_name']}")
        
        if vote_data.get("menu_type"):
            text_parts.append(f"메뉴: {vote_data['menu_type']}")
        
        if vote_data.get("date"):
            text_parts.append(f"날짜: {vote_data['date']}")
        
        if vote_data.get("preferences"):
            text_parts.append(f"선호사항: {vote_data['preferences']}")
        
        return " ".join(text_parts)
    
    def search_similar_votes(self, emp_no: str, query_text: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """
        유사한 투표 기록 검색
        
        Args:
            emp_no: 사용자 번호
            query_text: 검색 쿼리
            n_results: 반환할 결과 수
            
        Returns:
            유사한 투표 기록 리스트
        """
        try:
            # 쿼리 임베딩 생성
            query_embedding = self.embedding_model.encode(query_text).tolist()
            
            # Chroma DB에서 검색
            results = self.vote_collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where={"emp_no": emp_no}  # 해당 사용자의 투표만 검색
            )
            
            # 결과 포맷팅
            similar_votes = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    similar_votes.append({
                        "id": results['ids'][0][i],
                        "document": doc,
                        "metadata": results['metadatas'][0][i],
                        "distance": results['distances'][0][i] if 'distances' in results else 0
                    })
            
            logger.info(f"Found {len(similar_votes)} similar votes for user {emp_no}")
            return similar_votes
            
        except Exception as e:
            logger.error(f"Error searching similar votes: {str(e)}")
            return []
    
    def get_user_vote_history(self, emp_no: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        사용자의 투표 기록 조회
        
        Args:
            emp_no: 사용자 번호
            limit: 조회할 최대 개수
            
        Returns:
            사용자의 투표 기록 리스트
        """
        try:
            results = self.vote_collection.get(
                where={"emp_no": emp_no},
                limit=limit
            )
            
            vote_history = []
            if results['documents']:
                for i, doc in enumerate(results['documents']):
                    vote_history.append({
                        "id": results['ids'][i],
                        "document": doc,
                        "metadata": results['metadatas'][i]
                    })
            
            logger.info(f"Retrieved {len(vote_history)} votes for user {emp_no}")
            return vote_history
            
        except Exception as e:
            logger.error(f"Error getting user vote history: {str(e)}")
            return []
    
    def create_restaurant_embedding(self, restaurant_data: Dict[str, Any]) -> str:
        """
        식당 정보를 벡터로 변환하여 저장
        
        Args:
            restaurant_data: 식당 데이터
            
        Returns:
            저장된 문서 ID
        """
        try:
            # 식당 정보를 텍스트로 변환
            text_content = self._create_restaurant_text(restaurant_data)
            
            # 임베딩 생성
            embedding = self.embedding_model.encode(text_content).tolist()
            
            # 메타데이터 준비
            metadata = {
                "place_id": restaurant_data.get("place_id"),
                "place_name": restaurant_data.get("place_name"),
                "menu_type": restaurant_data.get("menu_type"),
                "address": restaurant_data.get("address"),
                "category": restaurant_data.get("category"),
                "created_at": datetime.now().isoformat(),
                "text_content": text_content
            }
            
            # 고유 ID 생성
            doc_id = f"restaurant_{restaurant_data.get('place_id')}"
            
            # Chroma DB에 저장
            self.restaurant_collection.add(
                embeddings=[embedding],
                documents=[text_content],
                metadatas=[metadata],
                ids=[doc_id]
            )
            
            logger.info(f"Restaurant embedding created for {restaurant_data.get('place_name')}")
            return doc_id
            
        except Exception as e:
            logger.error(f"Error creating restaurant embedding: {str(e)}")
            raise
    
    def _create_restaurant_text(self, restaurant_data: Dict[str, Any]) -> str:
        """식당 데이터를 텍스트로 변환"""
        text_parts = []
        
        if restaurant_data.get("place_name"):
            text_parts.append(f"식당명: {restaurant_data['place_name']}")
        
        if restaurant_data.get("menu_type"):
            text_parts.append(f"메뉴타입: {restaurant_data['menu_type']}")
        
        if restaurant_data.get("address"):
            text_parts.append(f"주소: {restaurant_data['address']}")
        
        if restaurant_data.get("category"):
            text_parts.append(f"카테고리: {restaurant_data['category']}")
        
        return " ".join(text_parts)
    
    def search_similar_restaurants(self, query_text: str, n_results: int = 10) -> List[Dict[str, Any]]:
        """
        유사한 식당 검색
        
        Args:
            query_text: 검색 쿼리
            n_results: 반환할 결과 수
            
        Returns:
            유사한 식당 리스트
        """
        try:
            # 쿼리 임베딩 생성
            query_embedding = self.embedding_model.encode(query_text).tolist()
            
            # Chroma DB에서 검색
            results = self.restaurant_collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results
            )
            
            # 결과 포맷팅
            similar_restaurants = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    similar_restaurants.append({
                        "id": results['ids'][0][i],
                        "document": doc,
                        "metadata": results['metadatas'][0][i],
                        "distance": results['distances'][0][i] if 'distances' in results else 0
                    })
            
            logger.info(f"Found {len(similar_restaurants)} similar restaurants")
            return similar_restaurants
            
        except Exception as e:
            logger.error(f"Error searching similar restaurants: {str(e)}")
            return []
    
    def get_personalized_recommendations(self, emp_no: str, query_text: str = None) -> List[Dict[str, Any]]:
        """
        개인화된 추천 생성
        
        Args:
            emp_no: 사용자 번호
            query_text: 검색 쿼리 (선택사항)
            
        Returns:
            개인화된 추천 리스트
        """
        try:
            # 사용자의 투표 기록 가져오기
            user_votes = self.get_user_vote_history(emp_no, limit=50)
            
            if not user_votes:
                logger.info(f"No vote history found for user {emp_no}")
                return []
            
            # 사용자의 선호도 분석
            user_preferences = self._analyze_user_preferences(user_votes)
            
            # 쿼리 텍스트가 없으면 사용자 선호도 기반으로 생성
            if not query_text:
                query_text = f"사용자 선호도: {user_preferences}"
            
            # 유사한 식당 검색
            recommendations = self.search_similar_restaurants(query_text, n_results=10)
            
            # 사용자 투표 기록과 매칭하여 개인화 점수 계산
            personalized_recommendations = []
            for rec in recommendations:
                personalization_score = self._calculate_personalization_score(
                    rec, user_votes, user_preferences
                )
                
                personalized_recommendations.append({
                    **rec,
                    "personalization_score": personalization_score,
                    "recommendation_reason": self._get_recommendation_reason(rec, user_preferences)
                })
            
            # 개인화 점수 순으로 정렬
            personalized_recommendations.sort(
                key=lambda x: x["personalization_score"], 
                reverse=True
            )
            
            logger.info(f"Generated {len(personalized_recommendations)} personalized recommendations for user {emp_no}")
            return personalized_recommendations[:5]  # 상위 5개만 반환
            
        except Exception as e:
            logger.error(f"Error generating personalized recommendations: {str(e)}")
            return []
    
    def _analyze_user_preferences(self, user_votes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """사용자 선호도 분석"""
        preferences = {
            "favorite_menu_types": {},
            "favorite_places": {},
            "preferred_categories": {},
            "vote_frequency": len(user_votes)
        }
        
        for vote in user_votes:
            metadata = vote.get("metadata", {})
            
            # 메뉴 타입 선호도
            menu_type = metadata.get("menu_type")
            if menu_type:
                preferences["favorite_menu_types"][menu_type] = preferences["favorite_menu_types"].get(menu_type, 0) + 1
            
            # 장소 선호도
            place_name = metadata.get("place_name")
            if place_name:
                preferences["favorite_places"][place_name] = preferences["favorite_places"].get(place_name, 0) + 1
        
        return preferences
    
    def _calculate_personalization_score(self, restaurant: Dict[str, Any], user_votes: List[Dict[str, Any]], user_preferences: Dict[str, Any]) -> float:
        """개인화 점수 계산"""
        score = 0.0
        metadata = restaurant.get("metadata", {})
        
        # 메뉴 타입 매칭 점수
        restaurant_menu_type = metadata.get("menu_type")
        if restaurant_menu_type in user_preferences.get("favorite_menu_types", {}):
            score += user_preferences["favorite_menu_types"][restaurant_menu_type] * 0.3
        
        # 장소 매칭 점수
        restaurant_name = metadata.get("place_name")
        if restaurant_name in user_preferences.get("favorite_places", {}):
            score += user_preferences["favorite_places"][restaurant_name] * 0.5
        
        # 기본 점수 (거리 기반)
        distance = restaurant.get("distance", 1.0)
        score += (1.0 - distance) * 0.2
        
        return min(score, 1.0)  # 최대 1.0으로 제한
    
    def _get_recommendation_reason(self, restaurant: Dict[str, Any], user_preferences: Dict[str, Any]) -> str:
        """추천 이유 생성"""
        metadata = restaurant.get("metadata", {})
        reasons = []
        
        restaurant_menu_type = metadata.get("menu_type")
        if restaurant_menu_type in user_preferences.get("favorite_menu_types", {}):
            reasons.append(f"선호하는 {restaurant_menu_type} 메뉴")
        
        restaurant_name = metadata.get("place_name")
        if restaurant_name in user_preferences.get("favorite_places", {}):
            reasons.append(f"이전에 투표한 {restaurant_name}")
        
        if not reasons:
            reasons.append("새로운 추천")
        
        return ", ".join(reasons)
    
    def delete_user_data(self, emp_no: str) -> bool:
        """사용자 데이터 삭제"""
        try:
            # 사용자의 모든 투표 기록 삭제
            user_votes = self.vote_collection.get(where={"emp_no": emp_no})
            if user_votes['ids']:
                self.vote_collection.delete(ids=user_votes['ids'])
            
            logger.info(f"Deleted all data for user {emp_no}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting user data: {str(e)}")
            return False
