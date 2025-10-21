"""
Hybrid Recommendation Service - 하이브리드 AI 추천 시스템
"""
from typing import List, Dict, Any, Optional
import logging
from sqlalchemy.orm import Session

from app.services.collaborative_filtering_service import CollaborativeFilteringService
from app.services.vector_db_service import VectorDBService
from app.services.lightrag_service import LightRAGService
from app.services.vote_integration_service import VoteIntegrationService

logger = logging.getLogger(__name__)

class HybridRecommendationService:
    """하이브리드 추천 서비스"""
    
    def __init__(self):
        self.cf_service = CollaborativeFilteringService()
        self.vector_service = VectorDBService()
        self.lightrag_service = LightRAGService()
        self.integration_service = VoteIntegrationService()
        
        logger.info("HybridRecommendationService initialized")
    
    def initialize_models(self, db: Session) -> bool:
        """
        모든 모델 초기화
        
        Args:
            db: 데이터베이스 세션
            
        Returns:
            초기화 성공 여부
        """
        try:
            # 1. 협업 필터링 모델 초기화
            logger.info("Initializing collaborative filtering model...")
            self.cf_service.build_user_item_matrix(db)
            self.cf_service.calculate_user_similarity()
            self.cf_service.calculate_item_similarity()
            self.cf_service.train_implicit_model()
            
            # 2. 벡터 DB 초기화 (이미 초기화됨)
            logger.info("Vector DB service ready")
            
            # 3. LightRAG 그래프 구축
            logger.info("Building LightRAG graph...")
            votes_data = self.integration_service.get_user_vote_history_from_db("84927", db)  # 예시
            if votes_data:
                self.lightrag_service.build_vote_graph(votes_data)
            
            logger.info("All models initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing models: {str(e)}")
            return False
    
    def get_hybrid_recommendations(self, user_id: str, query_text: str = None, n_recommendations: int = 10) -> List[Dict[str, Any]]:
        """
        하이브리드 추천 생성
        
        Args:
            user_id: 사용자 ID
            query_text: 검색 쿼리 (선택사항)
            n_recommendations: 추천할 아이템 수
            
        Returns:
            하이브리드 추천 리스트
        """
        try:
            # 1. 협업 필터링 추천
            cf_recommendations = self.cf_service.get_hybrid_recommendations(user_id, n_recommendations)
            
            # 2. 벡터 기반 추천
            vector_recommendations = self.vector_service.get_personalized_recommendations(
                emp_no=user_id,
                query_text=query_text
            )
            
            # 3. 추천 통합 및 점수 계산
            combined_recommendations = self._combine_recommendations(
                cf_recommendations, 
                vector_recommendations, 
                n_recommendations
            )
            
            # 4. LightRAG 설명 생성
            final_recommendations = []
            for rec in combined_recommendations:
                # 추천 컨텍스트 생성
                context = self.lightrag_service.get_recommendation_context(
                    user_id, 
                    str(rec.get("item_id", ""))
                )
                
                # 설명 생성
                explanation = self.lightrag_service.generate_explanation(
                    user_id,
                    str(rec.get("item_id", "")),
                    context
                )
                
                # 최종 추천 객체 생성
                final_rec = {
                    **rec,
                    "explanation": explanation,
                    "context": context,
                    "recommendation_type": "hybrid"
                }
                
                final_recommendations.append(final_rec)
            
            logger.info(f"Generated {len(final_recommendations)} hybrid recommendations for user {user_id}")
            return final_recommendations
            
        except Exception as e:
            logger.error(f"Error generating hybrid recommendations: {str(e)}")
            return []
    
    def _combine_recommendations(self, cf_recs: List[Dict], vector_recs: List[Dict], n_recommendations: int) -> List[Dict[str, Any]]:
        """
        협업 필터링과 벡터 기반 추천 통합
        
        Args:
            cf_recs: 협업 필터링 추천
            vector_recs: 벡터 기반 추천
            n_recommendations: 최종 추천 수
            
        Returns:
            통합된 추천 리스트
        """
        try:
            combined_scores = {}
            
            # 협업 필터링 추천 (가중치: 0.6)
            for rec in cf_recs:
                item_id = rec.get("item_id")
                score = rec.get("score", 0)
                
                if item_id not in combined_scores:
                    combined_scores[item_id] = {
                        "item_id": item_id,
                        "score": 0,
                        "sources": [],
                        "metadata": {}
                    }
                
                combined_scores[item_id]["score"] += score * 0.6
                combined_scores[item_id]["sources"].append("collaborative_filtering")
                combined_scores[item_id]["metadata"]["cf_score"] = score
            
            # 벡터 기반 추천 (가중치: 0.4)
            for rec in vector_recs:
                item_id = rec.get("metadata", {}).get("place_id")
                if not item_id:
                    continue
                
                score = rec.get("personalization_score", 0)
                
                if item_id not in combined_scores:
                    combined_scores[item_id] = {
                        "item_id": item_id,
                        "score": 0,
                        "sources": [],
                        "metadata": {}
                    }
                
                combined_scores[item_id]["score"] += score * 0.4
                combined_scores[item_id]["sources"].append("vector_similarity")
                combined_scores[item_id]["metadata"]["vector_score"] = score
                combined_scores[item_id]["metadata"]["vector_metadata"] = rec.get("metadata", {})
            
            # 최종 추천 정렬
            final_recommendations = []
            for item_id, data in sorted(combined_scores.items(), key=lambda x: x[1]["score"], reverse=True):
                final_recommendations.append({
                    "item_id": item_id,
                    "score": data["score"],
                    "sources": data["sources"],
                    "metadata": data["metadata"],
                    "recommendation_type": "hybrid"
                })
            
            return final_recommendations[:n_recommendations]
            
        except Exception as e:
            logger.error(f"Error combining recommendations: {str(e)}")
            return []
    
    def get_recommendation_explanation(self, user_id: str, item_id: str) -> str:
        """
        특정 추천에 대한 설명 생성
        
        Args:
            user_id: 사용자 ID
            item_id: 아이템 ID
            
        Returns:
            추천 설명
        """
        try:
            # 추천 컨텍스트 생성
            context = self.lightrag_service.get_recommendation_context(user_id, item_id)
            
            # 설명 생성
            explanation = self.lightrag_service.generate_explanation(user_id, item_id, context)
            
            return explanation
            
        except Exception as e:
            logger.error(f"Error generating recommendation explanation: {str(e)}")
            return f"추천 설명을 생성할 수 없습니다: {str(e)}"
    
    def get_similar_users(self, user_id: str, n_users: int = 5) -> List[Dict[str, Any]]:
        """
        유사한 사용자 찾기
        
        Args:
            user_id: 사용자 ID
            n_users: 반환할 사용자 수
            
        Returns:
            유사한 사용자 리스트
        """
        try:
            # 협업 필터링 기반 유사 사용자
            cf_similar = self.cf_service.get_similar_users(user_id, n_users)
            
            # 벡터 기반 유사 사용자
            vector_similar = self.vector_service.get_similar_users(user_id, n_users)
            
            # 통합
            combined_similar = self._combine_similar_users(cf_similar, vector_similar, n_users)
            
            return combined_similar
            
        except Exception as e:
            logger.error(f"Error finding similar users: {str(e)}")
            return []
    
    def _combine_similar_users(self, cf_similar: List[Dict], vector_similar: List[Dict], n_users: int) -> List[Dict[str, Any]]:
        """
        유사 사용자 통합
        
        Args:
            cf_similar: 협업 필터링 유사 사용자
            vector_similar: 벡터 기반 유사 사용자
            n_users: 최종 사용자 수
            
        Returns:
            통합된 유사 사용자 리스트
        """
        try:
            combined_scores = {}
            
            # 협업 필터링 유사 사용자 (가중치: 0.7)
            for user in cf_similar:
                user_id = user.get("user_id")
                similarity = user.get("similarity", 0)
                
                if user_id not in combined_scores:
                    combined_scores[user_id] = {
                        "user_id": user_id,
                        "score": 0,
                        "sources": []
                    }
                
                combined_scores[user_id]["score"] += similarity * 0.7
                combined_scores[user_id]["sources"].append("collaborative_filtering")
            
            # 벡터 기반 유사 사용자 (가중치: 0.3)
            for user in vector_similar:
                user_id = user.get("emp_no")
                similarity = user.get("similarity_score", 0)
                
                if user_id not in combined_scores:
                    combined_scores[user_id] = {
                        "user_id": user_id,
                        "score": 0,
                        "sources": []
                    }
                
                combined_scores[user_id]["score"] += similarity * 0.3
                combined_scores[user_id]["sources"].append("vector_similarity")
            
            # 최종 유사 사용자 정렬
            final_similar = []
            for user_id, data in sorted(combined_scores.items(), key=lambda x: x[1]["score"], reverse=True):
                final_similar.append({
                    "user_id": user_id,
                    "similarity": data["score"],
                    "sources": data["sources"]
                })
            
            return final_similar[:n_users]
            
        except Exception as e:
            logger.error(f"Error combining similar users: {str(e)}")
            return []
    
    def get_system_performance_metrics(self) -> Dict[str, Any]:
        """
        시스템 성능 메트릭 조회
        
        Returns:
            성능 메트릭
        """
        try:
            metrics = {
                "collaborative_filtering": self.cf_service.get_model_performance_metrics(),
                "vector_db": {
                    "status": "active",
                    "collections": ["user_votes", "restaurants"]
                },
                "lightrag": self.lightrag_service.get_graph_statistics(),
                "timestamp": datetime.now().isoformat()
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting performance metrics: {str(e)}")
            return {"error": str(e)}
    
    def update_user_preferences(self, user_id: str, new_vote: Dict[str, Any]) -> bool:
        """
        사용자 선호도 업데이트
        
        Args:
            user_id: 사용자 ID
            new_vote: 새로운 투표 데이터
            
        Returns:
            업데이트 성공 여부
        """
        try:
            # 1. 벡터 DB 업데이트
            self.vector_service.create_vote_embedding(new_vote)
            
            # 2. 협업 필터링 모델 재훈련 (선택사항)
            # self.cf_service.build_user_item_matrix(db)
            
            # 3. LightRAG 그래프 업데이트
            self.lightrag_service.create_entity_node("User", user_id, {"updated_at": datetime.now().isoformat()})
            self.lightrag_service.create_relationship(
                user_id,
                str(new_vote.get("place_id", "")),
                "VOTED",
                {"action": new_vote.get("action", "like"), "updated_at": datetime.now().isoformat()}
            )
            
            logger.info(f"Updated preferences for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating user preferences: {str(e)}")
            return False
