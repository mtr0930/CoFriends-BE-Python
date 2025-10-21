"""
Collaborative Filtering Service - 협업 필터링 기반 추천 시스템
"""
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import TruncatedSVD
from typing import List, Dict, Any, Tuple, Optional
import logging
from sqlalchemy.orm import Session
from sqlalchemy import text
import implicit
from scipy.sparse import csr_matrix

logger = logging.getLogger(__name__)

class CollaborativeFilteringService:
    """협업 필터링 서비스"""
    
    def __init__(self):
        self.user_item_matrix = None
        self.user_similarity_matrix = None
        self.item_similarity_matrix = None
        self.user_factors = None
        self.item_factors = None
        self.model = None
        logger.info("CollaborativeFilteringService initialized")
    
    def build_user_item_matrix(self, db: Session) -> pd.DataFrame:
        """
        사용자-아이템 매트릭스 구축
        
        Args:
            db: 데이터베이스 세션
            
        Returns:
            사용자-아이템 매트릭스 DataFrame
        """
        try:
            # 투표 데이터 조회
            query = text("""
                SELECT 
                    emp_no as user_id,
                    place_id as item_id,
                    CASE 
                        WHEN action = 'like' THEN 1
                        WHEN action = 'unlike' THEN -1
                        ELSE 0
                    END as rating,
                    created_at
                FROM place_votes
                WHERE action IN ('like', 'unlike')
                UNION ALL
                SELECT 
                    emp_no as user_id,
                    menu_id as item_id,
                    CASE 
                        WHEN vote = true THEN 1
                        WHEN vote = false THEN -1
                        ELSE 0
                    END as rating,
                    created_at
                FROM user_date_votes
                WHERE vote IS NOT NULL
            """)
            
            result = db.execute(query)
            votes_data = result.fetchall()
            
            if not votes_data:
                logger.warning("No vote data found")
                return pd.DataFrame()
            
            # DataFrame 생성
            df = pd.DataFrame(votes_data, columns=['user_id', 'item_id', 'rating', 'created_at'])
            
            # 사용자-아이템 매트릭스 생성
            user_item_matrix = df.pivot_table(
                index='user_id', 
                columns='item_id', 
                values='rating', 
                fill_value=0,
                aggfunc='mean'  # 중복 투표가 있을 경우 평균값 사용
            )
            
            self.user_item_matrix = user_item_matrix
            logger.info(f"Built user-item matrix: {user_item_matrix.shape}")
            
            return user_item_matrix
            
        except Exception as e:
            logger.error(f"Error building user-item matrix: {str(e)}")
            return pd.DataFrame()
    
    def calculate_user_similarity(self, method: str = "cosine") -> np.ndarray:
        """
        사용자 유사도 계산
        
        Args:
            method: 유사도 계산 방법 ("cosine", "pearson")
            
        Returns:
            사용자 유사도 매트릭스
        """
        try:
            if self.user_item_matrix is None or self.user_item_matrix.empty:
                logger.error("User-item matrix not built")
                return np.array([])
            
            if method == "cosine":
                # 코사인 유사도
                self.user_similarity_matrix = cosine_similarity(self.user_item_matrix)
            elif method == "pearson":
                # 피어슨 상관계수
                self.user_similarity_matrix = self.user_item_matrix.T.corr().fillna(0).values
            else:
                raise ValueError(f"Unknown similarity method: {method}")
            
            logger.info(f"Calculated user similarity matrix: {self.user_similarity_matrix.shape}")
            return self.user_similarity_matrix
            
        except Exception as e:
            logger.error(f"Error calculating user similarity: {str(e)}")
            return np.array([])
    
    def calculate_item_similarity(self, method: str = "cosine") -> np.ndarray:
        """
        아이템 유사도 계산
        
        Args:
            method: 유사도 계산 방법 ("cosine", "pearson")
            
        Returns:
            아이템 유사도 매트릭스
        """
        try:
            if self.user_item_matrix is None or self.user_item_matrix.empty:
                logger.error("User-item matrix not built")
                return np.array([])
            
            if method == "cosine":
                # 코사인 유사도
                self.item_similarity_matrix = cosine_similarity(self.user_item_matrix.T)
            elif method == "pearson":
                # 피어슨 상관계수
                self.item_similarity_matrix = self.user_item_matrix.corr().fillna(0).values
            else:
                raise ValueError(f"Unknown similarity method: {method}")
            
            logger.info(f"Calculated item similarity matrix: {self.item_similarity_matrix.shape}")
            return self.item_similarity_matrix
            
        except Exception as e:
            logger.error(f"Error calculating item similarity: {str(e)}")
            return np.array([])
    
    def train_implicit_model(self, factors: int = 50, iterations: int = 20) -> bool:
        """
        Implicit 라이브러리를 사용한 협업 필터링 모델 훈련
        
        Args:
            factors: 잠재 요인 수
            iterations: 반복 횟수
            
        Returns:
            훈련 성공 여부
        """
        try:
            if self.user_item_matrix is None or self.user_item_matrix.empty:
                logger.error("User-item matrix not built")
                return False
            
            # Implicit 모델 초기화
            self.model = implicit.als.AlternatingLeastSquares(
                factors=factors,
                iterations=iterations,
                regularization=0.01,
                random_state=42
            )
            
            # 매트릭스를 CSR 형식으로 변환
            matrix = csr_matrix(self.user_item_matrix.values)
            
            # 모델 훈련
            self.model.fit(matrix)
            
            logger.info(f"Trained implicit model with {factors} factors")
            return True
            
        except Exception as e:
            logger.error(f"Error training implicit model: {str(e)}")
            return False
    
    def get_user_recommendations(self, user_id: str, n_recommendations: int = 10) -> List[Dict[str, Any]]:
        """
        사용자 기반 추천 생성
        
        Args:
            user_id: 사용자 ID
            n_recommendations: 추천할 아이템 수
            
        Returns:
            추천 아이템 리스트
        """
        try:
            if self.user_similarity_matrix is None:
                logger.error("User similarity matrix not calculated")
                return []
            
            if self.user_item_matrix is None or self.user_item_matrix.empty:
                logger.error("User-item matrix not built")
                return []
            
            # 사용자 인덱스 찾기
            if user_id not in self.user_item_matrix.index:
                logger.warning(f"User {user_id} not found in matrix")
                return []
            
            user_idx = self.user_item_matrix.index.get_loc(user_id)
            
            # 사용자가 이미 평가한 아이템들
            user_ratings = self.user_item_matrix.iloc[user_idx]
            rated_items = user_ratings[user_ratings != 0].index.tolist()
            
            # 유사한 사용자들 찾기
            user_similarities = self.user_similarity_matrix[user_idx]
            similar_users = np.argsort(user_similarities)[::-1][1:11]  # 자기 자신 제외, 상위 10명
            
            # 추천 점수 계산
            recommendations = {}
            
            for similar_user_idx in similar_users:
                similarity = user_similarities[similar_user_idx]
                if similarity <= 0:
                    continue
                
                similar_user_ratings = self.user_item_matrix.iloc[similar_user_idx]
                
                for item_id in similar_user_ratings.index:
                    if item_id in rated_items:
                        continue
                    
                    rating = similar_user_ratings[item_id]
                    if rating == 0:
                        continue
                    
                    if item_id not in recommendations:
                        recommendations[item_id] = 0
                    
                    recommendations[item_id] += similarity * rating
            
            # 추천 점수 순으로 정렬
            sorted_recommendations = sorted(
                recommendations.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:n_recommendations]
            
            # 결과 포맷팅
            result = []
            for item_id, score in sorted_recommendations:
                result.append({
                    "item_id": item_id,
                    "score": score,
                    "recommendation_type": "user_based"
                })
            
            logger.info(f"Generated {len(result)} user-based recommendations for user {user_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error generating user recommendations: {str(e)}")
            return []
    
    def get_item_recommendations(self, item_id: int, n_recommendations: int = 10) -> List[Dict[str, Any]]:
        """
        아이템 기반 추천 생성
        
        Args:
            item_id: 아이템 ID
            n_recommendations: 추천할 아이템 수
            
        Returns:
            추천 아이템 리스트
        """
        try:
            if self.item_similarity_matrix is None:
                logger.error("Item similarity matrix not calculated")
                return []
            
            if self.user_item_matrix is None or self.user_item_matrix.empty:
                logger.error("User-item matrix not built")
                return []
            
            # 아이템 인덱스 찾기
            if item_id not in self.user_item_matrix.columns:
                logger.warning(f"Item {item_id} not found in matrix")
                return []
            
            item_idx = self.user_item_matrix.columns.get_loc(item_id)
            
            # 유사한 아이템들 찾기
            item_similarities = self.item_similarity_matrix[item_idx]
            similar_items = np.argsort(item_similarities)[::-1][1:n_recommendations+1]  # 자기 자신 제외
            
            # 결과 포맷팅
            result = []
            for similar_item_idx in similar_items:
                similarity = item_similarities[similar_item_idx]
                if similarity <= 0:
                    continue
                
                similar_item_id = self.user_item_matrix.columns[similar_item_idx]
                result.append({
                    "item_id": similar_item_id,
                    "score": similarity,
                    "recommendation_type": "item_based"
                })
            
            logger.info(f"Generated {len(result)} item-based recommendations for item {item_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error generating item recommendations: {str(e)}")
            return []
    
    def get_implicit_recommendations(self, user_id: str, n_recommendations: int = 10) -> List[Dict[str, Any]]:
        """
        Implicit 모델을 사용한 추천 생성
        
        Args:
            user_id: 사용자 ID
            n_recommendations: 추천할 아이템 수
            
        Returns:
            추천 아이템 리스트
        """
        try:
            if self.model is None:
                logger.error("Implicit model not trained")
                return []
            
            if self.user_item_matrix is None or self.user_item_matrix.empty:
                logger.error("User-item matrix not built")
                return []
            
            # 사용자 인덱스 찾기
            if user_id not in self.user_item_matrix.index:
                logger.warning(f"User {user_id} not found in matrix")
                return []
            
            user_idx = self.user_item_matrix.index.get_loc(user_id)
            
            # Implicit 모델로 추천 생성
            recommendations = self.model.recommend(
                user_idx, 
                self.user_item_matrix.values, 
                N=n_recommendations
            )
            
            # 결과 포맷팅
            result = []
            for item_idx, score in recommendations:
                item_id = self.user_item_matrix.columns[item_idx]
                result.append({
                    "item_id": item_id,
                    "score": score,
                    "recommendation_type": "implicit"
                })
            
            logger.info(f"Generated {len(result)} implicit recommendations for user {user_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error generating implicit recommendations: {str(e)}")
            return []
    
    def get_hybrid_recommendations(self, user_id: str, n_recommendations: int = 10) -> List[Dict[str, Any]]:
        """
        하이브리드 추천 (사용자 기반 + 아이템 기반 + Implicit)
        
        Args:
            user_id: 사용자 ID
            n_recommendations: 추천할 아이템 수
            
        Returns:
            하이브리드 추천 리스트
        """
        try:
            # 각 방법으로 추천 생성
            user_based = self.get_user_recommendations(user_id, n_recommendations)
            item_based = self.get_item_recommendations(user_id, n_recommendations) if hasattr(self, 'item_similarity_matrix') else []
            implicit_recs = self.get_implicit_recommendations(user_id, n_recommendations)
            
            # 추천 점수 통합
            combined_scores = {}
            
            # 사용자 기반 추천 (가중치: 0.4)
            for rec in user_based:
                item_id = rec["item_id"]
                if item_id not in combined_scores:
                    combined_scores[item_id] = {"score": 0, "sources": []}
                combined_scores[item_id]["score"] += rec["score"] * 0.4
                combined_scores[item_id]["sources"].append("user_based")
            
            # 아이템 기반 추천 (가중치: 0.3)
            for rec in item_based:
                item_id = rec["item_id"]
                if item_id not in combined_scores:
                    combined_scores[item_id] = {"score": 0, "sources": []}
                combined_scores[item_id]["score"] += rec["score"] * 0.3
                combined_scores[item_id]["sources"].append("item_based")
            
            # Implicit 추천 (가중치: 0.3)
            for rec in implicit_recs:
                item_id = rec["item_id"]
                if item_id not in combined_scores:
                    combined_scores[item_id] = {"score": 0, "sources": []}
                combined_scores[item_id]["score"] += rec["score"] * 0.3
                combined_scores[item_id]["sources"].append("implicit")
            
            # 최종 추천 정렬
            final_recommendations = []
            for item_id, data in sorted(combined_scores.items(), key=lambda x: x[1]["score"], reverse=True):
                final_recommendations.append({
                    "item_id": item_id,
                    "score": data["score"],
                    "recommendation_type": "hybrid",
                    "sources": data["sources"]
                })
            
            logger.info(f"Generated {len(final_recommendations)} hybrid recommendations for user {user_id}")
            return final_recommendations[:n_recommendations]
            
        except Exception as e:
            logger.error(f"Error generating hybrid recommendations: {str(e)}")
            return []
    
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
            if self.user_similarity_matrix is None:
                logger.error("User similarity matrix not calculated")
                return []
            
            if self.user_item_matrix is None or self.user_item_matrix.empty:
                logger.error("User-item matrix not built")
                return []
            
            # 사용자 인덱스 찾기
            if user_id not in self.user_item_matrix.index:
                logger.warning(f"User {user_id} not found in matrix")
                return []
            
            user_idx = self.user_item_matrix.index.get_loc(user_id)
            
            # 유사한 사용자들 찾기
            user_similarities = self.user_similarity_matrix[user_idx]
            similar_users = np.argsort(user_similarities)[::-1][1:n_users+1]  # 자기 자신 제외
            
            # 결과 포맷팅
            result = []
            for similar_user_idx in similar_users:
                similarity = user_similarities[similar_user_idx]
                if similarity <= 0:
                    continue
                
                similar_user_id = self.user_item_matrix.index[similar_user_idx]
                result.append({
                    "user_id": similar_user_id,
                    "similarity": similarity
                })
            
            logger.info(f"Found {len(result)} similar users for user {user_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error finding similar users: {str(e)}")
            return []
    
    def get_model_performance_metrics(self) -> Dict[str, Any]:
        """
        모델 성능 메트릭 계산
        
        Returns:
            성능 메트릭 딕셔너리
        """
        try:
            if self.user_item_matrix is None or self.user_item_matrix.empty:
                return {"error": "No data available"}
            
            # 기본 통계
            total_users = len(self.user_item_matrix.index)
            total_items = len(self.user_item_matrix.columns)
            total_ratings = (self.user_item_matrix != 0).sum().sum()
            sparsity = 1 - (total_ratings / (total_users * total_items))
            
            # 평균 평점
            avg_rating = self.user_item_matrix[self.user_item_matrix != 0].mean().mean()
            
            # 사용자별 평점 수
            user_rating_counts = (self.user_item_matrix != 0).sum(axis=1)
            avg_ratings_per_user = user_rating_counts.mean()
            
            # 아이템별 평점 수
            item_rating_counts = (self.user_item_matrix != 0).sum(axis=0)
            avg_ratings_per_item = item_rating_counts.mean()
            
            metrics = {
                "total_users": total_users,
                "total_items": total_items,
                "total_ratings": total_ratings,
                "sparsity": sparsity,
                "avg_rating": avg_rating,
                "avg_ratings_per_user": avg_ratings_per_user,
                "avg_ratings_per_item": avg_ratings_per_item,
                "matrix_shape": self.user_item_matrix.shape
            }
            
            logger.info(f"Calculated performance metrics: {metrics}")
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating performance metrics: {str(e)}")
            return {"error": str(e)}
