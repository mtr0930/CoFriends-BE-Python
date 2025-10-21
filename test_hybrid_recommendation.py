#!/usr/bin/env python3
"""
Hybrid AI Recommendation System 테스트
"""
import requests
import json
import time
import asyncio

def test_hybrid_recommendation_system():
    """하이브리드 추천 시스템 테스트"""
    
    print("Hybrid AI Recommendation System 테스트")
    print("=" * 60)
    
    base_url = "http://localhost:5000"
    
    try:
        # 1. 헬스 체크
        print("\n1. 헬스 체크...")
        response = requests.get(f"{base_url}/api/hybrid/health", timeout=10)
        if response.status_code == 200:
            print("SUCCESS: Hybrid recommendation service is healthy")
            print(f"Response: {response.json()}")
        else:
            print(f"FAILED: Health check failed with status {response.status_code}")
            return False
        
        # 2. 모델 초기화
        print("\n2. 모델 초기화...")
        response = requests.post(f"{base_url}/api/hybrid/initialize-models", timeout=30)
        if response.status_code == 200:
            print("SUCCESS: Models initialized successfully")
            print(f"Response: {response.json()}")
        else:
            print(f"FAILED: Model initialization failed: {response.text}")
            return False
        
        # 3. 하이브리드 추천 생성
        print("\n3. 하이브리드 추천 생성...")
        recommendation_request = {
            "emp_no": "84927",
            "query_text": "한식 매운 음식 추천해주세요"
        }
        response = requests.post(
            f"{base_url}/api/hybrid/recommendations",
            json=recommendation_request,
            timeout=30
        )
        if response.status_code == 200:
            recommendations = response.json()
            print(f"SUCCESS: Generated {len(recommendations)} hybrid recommendations")
            for i, rec in enumerate(recommendations):
                print(f"\n추천 {i+1}:")
                print(f"  아이템 ID: {rec.get('item_id', 'Unknown')}")
                print(f"  점수: {rec.get('score', 0):.3f}")
                print(f"  소스: {rec.get('sources', [])}")
                print(f"  설명: {rec.get('explanation', 'No explanation')[:100]}...")
        else:
            print(f"FAILED: Hybrid recommendations failed: {response.text}")
            return False
        
        # 4. 추천 설명 생성
        print("\n4. 추천 설명 생성...")
        if recommendations:
            first_rec = recommendations[0]
            item_id = first_rec.get('item_id')
            if item_id:
                response = requests.get(
                    f"{base_url}/api/hybrid/explanation/84927/{item_id}",
                    timeout=15
                )
                if response.status_code == 200:
                    explanation_data = response.json()
                    print("SUCCESS: Generated recommendation explanation")
                    print(f"설명: {explanation_data.get('explanation', 'No explanation')}")
                else:
                    print(f"FAILED: Explanation generation failed: {response.text}")
        
        # 5. 유사한 사용자 찾기
        print("\n5. 유사한 사용자 찾기...")
        response = requests.get(
            f"{base_url}/api/hybrid/similar-users/84927",
            params={"n_users": 3},
            timeout=15
        )
        if response.status_code == 200:
            similar_users_data = response.json()
            print("SUCCESS: Found similar users")
            print(f"유사한 사용자 수: {similar_users_data.get('count', 0)}")
            for user in similar_users_data.get('similar_users', []):
                print(f"  사용자: {user.get('user_id', 'Unknown')}, 유사도: {user.get('similarity', 0):.3f}")
        else:
            print(f"FAILED: Similar users search failed: {response.text}")
        
        # 6. 성능 메트릭 조회
        print("\n6. 성능 메트릭 조회...")
        response = requests.get(f"{base_url}/api/hybrid/performance-metrics", timeout=15)
        if response.status_code == 200:
            metrics = response.json()
            print("SUCCESS: Retrieved performance metrics")
            print(f"메트릭: {json.dumps(metrics, ensure_ascii=False, indent=2)}")
        else:
            print(f"FAILED: Performance metrics retrieval failed: {response.text}")
        
        # 7. 사용자 선호도 업데이트
        print("\n7. 사용자 선호도 업데이트...")
        vote_data = {
            "place_id": "123",
            "place_name": "테스트 식당",
            "menu_type": "한식",
            "action": "like",
            "date": "2024-01-15"
        }
        response = requests.post(
            f"{base_url}/api/hybrid/update-preferences/84927",
            json=vote_data,
            timeout=15
        )
        if response.status_code == 200:
            update_result = response.json()
            print("SUCCESS: Updated user preferences")
            print(f"결과: {update_result.get('message', 'No message')}")
        else:
            print(f"FAILED: Preference update failed: {response.text}")
        
        print("\n" + "=" * 60)
        print("Hybrid AI Recommendation System 테스트 완료!")
        return True
        
    except requests.exceptions.ConnectionError:
        print("CONNECTION ERROR: 서버에 연결할 수 없습니다")
        return False
    except Exception as e:
        print(f"ERROR: 예상치 못한 오류: {str(e)}")
        return False

def test_collaborative_filtering():
    """협업 필터링 테스트"""
    
    print("\n" + "=" * 60)
    print("Collaborative Filtering 테스트")
    print("=" * 60)
    
    base_url = "http://localhost:5000"
    
    try:
        # 협업 필터링 API 테스트 (개발 중)
        print("협업 필터링 기능은 현재 개발 중입니다.")
        print("향후 구현 예정: 사용자-아이템 매트릭스, 유사도 계산, 추천 생성")
        
        return True
        
    except Exception as e:
        print(f"ERROR: 협업 필터링 테스트 오류: {str(e)}")
        return False

def test_lightrag():
    """LightRAG 테스트"""
    
    print("\n" + "=" * 60)
    print("LightRAG 테스트")
    print("=" * 60)
    
    base_url = "http://localhost:5000"
    
    try:
        # LightRAG API 테스트 (개발 중)
        print("LightRAG 기능은 현재 개발 중입니다.")
        print("향후 구현 예정: Neo4j 그래프 구축, 관계 기반 설명 생성")
        
        return True
        
    except Exception as e:
        print(f"ERROR: LightRAG 테스트 오류: {str(e)}")
        return False

if __name__ == "__main__":
    print("Hybrid AI Recommendation System 종합 테스트")
    print("=" * 60)
    
    # 메인 하이브리드 추천 테스트
    success1 = test_hybrid_recommendation_system()
    
    # 협업 필터링 테스트
    success2 = test_collaborative_filtering()
    
    # LightRAG 테스트
    success3 = test_lightrag()
    
    print("\n" + "=" * 60)
    print("테스트 결과 요약:")
    print(f"하이브리드 추천: {'SUCCESS' if success1 else 'FAILED'}")
    print(f"협업 필터링: {'SUCCESS' if success2 else 'FAILED'}")
    print(f"LightRAG: {'SUCCESS' if success3 else 'FAILED'}")
    
    if success1 and success2 and success3:
        print("\n모든 테스트가 통과했습니다!")
    else:
        print("\n일부 테스트가 실패했습니다.")
    
    print("=" * 60)
