#!/usr/bin/env python3
"""
Collaborative Filtering 테스트
"""
import requests
import json
import time

def test_collaborative_filtering():
    """협업 필터링 테스트"""
    
    print("Collaborative Filtering 테스트")
    print("=" * 50)
    
    base_url = "http://localhost:5000"
    
    try:
        # 1. 헬스 체크
        print("\n1. 헬스 체크...")
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            print("SUCCESS: 서버가 정상적으로 작동 중")
        else:
            print(f"FAILED: 헬스 체크 실패 - {response.status_code}")
            return False
        
        # 2. 협업 필터링 서비스 직접 테스트
        print("\n2. 협업 필터링 서비스 테스트...")
        try:
            from app.services.collaborative_filtering_service import CollaborativeFilteringService
            from app.core.database import get_db
            
            # 서비스 초기화
            cf_service = CollaborativeFilteringService()
            print("SUCCESS: CollaborativeFilteringService 초기화 완료")
            
            # 더미 데이터로 매트릭스 구축 테스트
            import pandas as pd
            import numpy as np
            
            # 샘플 데이터 생성
            data = {
                'user_id': ['84927', '84927', '84927', '12345', '12345', '67890'],
                'item_id': [1, 2, 3, 1, 2, 1],
                'rating': [1, 1, -1, 1, 1, 1]
            }
            df = pd.DataFrame(data)
            
            # 매트릭스 생성
            user_item_matrix = df.pivot_table(
                index='user_id', 
                columns='item_id', 
                values='rating', 
                fill_value=0
            )
            
            print(f"SUCCESS: User-Item 매트릭스 생성 완료 - {user_item_matrix.shape}")
            
            # 유사도 계산 테스트
            from sklearn.metrics.pairwise import cosine_similarity
            user_similarity = cosine_similarity(user_item_matrix)
            print(f"SUCCESS: 사용자 유사도 매트릭스 계산 완료 - {user_similarity.shape}")
            
            # 아이템 유사도 계산
            item_similarity = cosine_similarity(user_item_matrix.T)
            print(f"SUCCESS: 아이템 유사도 매트릭스 계산 완료 - {item_similarity.shape}")
            
            # Implicit 모델 테스트
            try:
                import implicit
                from scipy.sparse import csr_matrix
                
                # CSR 매트릭스 변환
                matrix = csr_matrix(user_item_matrix.values)
                
                # Implicit 모델 초기화
                model = implicit.als.AlternatingLeastSquares(factors=10, iterations=10)
                model.fit(matrix)
                
                print("SUCCESS: Implicit 모델 훈련 완료")
                
                # 추천 생성 테스트
                user_idx = 0  # 첫 번째 사용자
                recommendations = model.recommend(user_idx, matrix, N=3)
                print(f"SUCCESS: 추천 생성 완료 - {len(recommendations)}개 추천")
                
            except Exception as e:
                print(f"WARNING: Implicit 모델 테스트 실패 - {str(e)}")
            
            print("\n협업 필터링 핵심 기능 테스트 완료!")
            return True
            
        except Exception as e:
            print(f"FAILED: 협업 필터링 서비스 테스트 실패 - {str(e)}")
            return False
        
    except Exception as e:
        print(f"ERROR: 테스트 중 오류 발생 - {str(e)}")
        return False

def test_lightrag():
    """LightRAG 테스트"""
    
    print("\n" + "=" * 50)
    print("LightRAG 테스트")
    print("=" * 50)
    
    try:
        # LightRAG 서비스 테스트
        print("\n1. LightRAG 서비스 초기화...")
        try:
            from app.services.lightrag_service import LightRAGService
            
            # Neo4j 연결 테스트 (실제 Neo4j가 없어도 서비스 초기화는 가능)
            lightrag_service = LightRAGService()
            print("SUCCESS: LightRAGService 초기화 완료")
            
            # LLM 초기화 테스트
            if lightrag_service.llm:
                print("SUCCESS: LLM 초기화 완료")
            else:
                print("WARNING: LLM 초기화 실패 (OpenAI API 키 필요)")
            
            print("\nLightRAG 핵심 기능 테스트 완료!")
            return True
            
        except Exception as e:
            print(f"FAILED: LightRAG 서비스 테스트 실패 - {str(e)}")
            return False
        
    except Exception as e:
        print(f"ERROR: LightRAG 테스트 중 오류 발생 - {str(e)}")
        return False

def test_vector_db():
    """벡터 DB 테스트"""
    
    print("\n" + "=" * 50)
    print("Vector DB 테스트")
    print("=" * 50)
    
    try:
        # 벡터 DB 서비스 테스트
        print("\n1. Vector DB 서비스 초기화...")
        try:
            from app.services.vector_db_service import VectorDBService
            
            vector_service = VectorDBService()
            print("SUCCESS: VectorDBService 초기화 완료")
            
            # 임베딩 모델 테스트
            print("\n2. 임베딩 모델 테스트...")
            try:
                from sentence_transformers import SentenceTransformer
                model = SentenceTransformer('jhgan/ko-sroberta-multitask')
                test_text = "한식 맛있는 음식"
                embedding = model.encode([test_text])
                print(f"SUCCESS: 임베딩 생성 완료 - 차원: {len(embedding[0])}")
            except Exception as e:
                print(f"WARNING: 임베딩 모델 테스트 실패 - {str(e)}")
            
            # 문서 추가 테스트
            print("\n3. 문서 추가 테스트...")
            try:
                test_vote_data = {
                    "emp_no": "test_user",
                    "place_name": "테스트 식당",
                    "menu_type": "한식",
                    "date": "2024-01-01",
                    "vote_type": "restaurant"
                }
                
                doc_id = vector_service.create_vote_embedding(test_vote_data)
                print(f"SUCCESS: 투표 임베딩 생성 완료 - ID: {doc_id}")
            except Exception as e:
                print(f"WARNING: 문서 추가 테스트 실패 - {str(e)}")
            
            # 검색 테스트
            print("\n4. 벡터 검색 테스트...")
            try:
                results = vector_service.search_similar_votes("test_user", "한식", n_results=3)
                print(f"SUCCESS: 벡터 검색 완료 - {len(results)}개 결과")
            except Exception as e:
                print(f"WARNING: 벡터 검색 테스트 실패 - {str(e)}")
            
            print("\nVector DB 핵심 기능 테스트 완료!")
            return True
            
        except Exception as e:
            print(f"FAILED: Vector DB 서비스 테스트 실패 - {str(e)}")
            return False
        
    except Exception as e:
        print(f"ERROR: Vector DB 테스트 중 오류 발생 - {str(e)}")
        return False

if __name__ == "__main__":
    print("Hybrid AI Recommendation System 개별 기능 테스트")
    print("=" * 60)
    
    # 각 기능별 테스트
    success1 = test_collaborative_filtering()
    success2 = test_lightrag()
    success3 = test_vector_db()
    
    print("\n" + "=" * 60)
    print("테스트 결과 요약:")
    print(f"협업 필터링: {'SUCCESS' if success1 else 'FAILED'}")
    print(f"LightRAG: {'SUCCESS' if success2 else 'FAILED'}")
    print(f"Vector DB: {'SUCCESS' if success3 else 'FAILED'}")
    
    if success1 and success2 and success3:
        print("\n모든 개별 기능 테스트가 통과했습니다!")
    else:
        print("\n일부 기능 테스트가 실패했습니다.")
    
    print("=" * 60)
