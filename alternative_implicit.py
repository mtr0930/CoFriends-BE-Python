"""
implicit 패키지 대신 사용할 수 있는 대안들
"""
import numpy as np
from sklearn.decomposition import NMF
from sklearn.metrics.pairwise import cosine_similarity

class AlternativeImplicit:
    """implicit 패키지 대신 사용할 수 있는 협업 필터링 구현"""
    
    def __init__(self):
        self.model = None
        self.user_factors = None
        self.item_factors = None
    
    def fit(self, user_item_matrix):
        """
        사용자-아이템 행렬로 모델 학습
        
        Args:
            user_item_matrix: scipy.sparse.csr_matrix 형태의 사용자-아이템 상호작용 행렬
        """
        # NMF (Non-negative Matrix Factorization) 사용
        self.model = NMF(n_components=50, random_state=42)
        self.user_factors = self.model.fit_transform(user_item_matrix)
        self.item_factors = self.model.components_
    
    def recommend(self, user_id, n_recommendations=10):
        """
        사용자에게 아이템 추천
        
        Args:
            user_id: 사용자 ID
            n_recommendations: 추천할 아이템 수
            
        Returns:
            추천 아이템 ID 리스트
        """
        if self.user_factors is None:
            raise ValueError("모델이 학습되지 않았습니다. fit()을 먼저 호출하세요.")
        
        # 사용자의 선호도 점수 계산
        user_preferences = np.dot(self.user_factors[user_id], self.item_factors)
        
        # 상위 n_recommendations개 아이템 반환
        top_items = np.argsort(user_preferences)[-n_recommendations:][::-1]
        return top_items.tolist()
    
    def similar_items(self, item_id, n_similar=10):
        """
        특정 아이템과 유사한 아이템들 찾기
        
        Args:
            item_id: 아이템 ID
            n_similar: 유사한 아이템 수
            
        Returns:
            유사한 아이템 ID 리스트
        """
        if self.item_factors is None:
            raise ValueError("모델이 학습되지 않았습니다. fit()을 먼저 호출하세요.")
        
        # 코사인 유사도 계산
        similarities = cosine_similarity([self.item_factors[item_id]], self.item_factors)[0]
        
        # 자기 자신 제외하고 상위 n_similar개 반환
        similar_items = np.argsort(similarities)[-n_similar-1:-1][::-1]
        return similar_items.tolist()

# 사용 예시
if __name__ == "__main__":
    # 예시 데이터
    from scipy.sparse import csr_matrix
    
    # 사용자-아이템 행렬 (예시)
    data = np.array([1, 1, 1, 1, 1, 1, 1, 1, 1, 1])
    row_indices = np.array([0, 0, 1, 1, 2, 2, 3, 3, 4, 4])
    col_indices = np.array([0, 1, 0, 2, 1, 3, 2, 4, 3, 4])
    
    user_item_matrix = csr_matrix((data, (row_indices, col_indices)), shape=(5, 5))
    
    # 모델 학습
    model = AlternativeImplicit()
    model.fit(user_item_matrix)
    
    # 추천 생성
    recommendations = model.recommend(user_id=0, n_recommendations=3)
    print(f"사용자 0에게 추천: {recommendations}")
    
    # 유사 아이템 찾기
    similar = model.similar_items(item_id=0, n_similar=3)
    print(f"아이템 0과 유사한 아이템: {similar}")
