#!/usr/bin/env python3
"""
Personalized Recommendation System 테스트
"""
import requests
import json
import time

def test_personalized_recommendation():
    """개인화 추천 시스템 테스트"""
    
    print("Personalized Recommendation System 테스트")
    print("=" * 60)
    
    base_url = "http://localhost:5000"
    
    # 테스트 데이터
    test_votes = [
        {
            "emp_no": "84927",
            "place_name": "맛있는 한식당",
            "menu_type": "한식",
            "date": "2024-01-15",
            "preferences": "매운 음식 좋아함"
        },
        {
            "emp_no": "84927",
            "place_name": "이탈리안 레스토랑",
            "menu_type": "양식",
            "date": "2024-01-20",
            "preferences": "파스타 좋아함"
        },
        {
            "emp_no": "84927",
            "place_name": "일본식 라멘집",
            "menu_type": "일식",
            "date": "2024-01-25",
            "preferences": "라멘 좋아함"
        }
    ]
    
    test_restaurants = [
        {
            "place_id": "rest_001",
            "place_name": "맛있는 한식당",
            "menu_type": "한식",
            "address": "서울시 강남구",
            "category": "한식"
        },
        {
            "place_id": "rest_002",
            "place_name": "이탈리안 레스토랑",
            "menu_type": "양식",
            "address": "서울시 서초구",
            "category": "양식"
        },
        {
            "place_id": "rest_003",
            "place_name": "일본식 라멘집",
            "menu_type": "일식",
            "address": "서울시 홍대",
            "category": "일식"
        },
        {
            "place_id": "rest_004",
            "place_name": "중국집",
            "menu_type": "중식",
            "address": "서울시 명동",
            "category": "중식"
        }
    ]
    
    try:
        # 1. 헬스 체크
        print("\n1. 헬스 체크...")
        response = requests.get(f"{base_url}/api/personalized/health", timeout=10)
        if response.status_code == 200:
            print("SUCCESS: Personalized recommendation service is healthy")
            print(f"Response: {response.json()}")
        else:
            print(f"FAILED: Health check failed with status {response.status_code}")
            return False
        
        # 2. 투표 데이터 임베딩 생성
        print("\n2. 투표 데이터 임베딩 생성...")
        for i, vote in enumerate(test_votes):
            response = requests.post(
                f"{base_url}/api/personalized/vote-embedding",
                json=vote,
                timeout=10
            )
            if response.status_code == 200:
                print(f"SUCCESS: Vote embedding {i+1} created")
            else:
                print(f"FAILED: Vote embedding {i+1} failed: {response.text}")
        
        # 3. 식당 데이터 임베딩 생성
        print("\n3. 식당 데이터 임베딩 생성...")
        for i, restaurant in enumerate(test_restaurants):
            response = requests.post(
                f"{base_url}/api/personalized/restaurant-embedding",
                json=restaurant,
                timeout=10
            )
            if response.status_code == 200:
                print(f"SUCCESS: Restaurant embedding {i+1} created")
            else:
                print(f"FAILED: Restaurant embedding {i+1} failed: {response.text}")
        
        # 잠시 대기 (임베딩 처리 시간)
        print("\n잠시 대기 중... (임베딩 처리)")
        time.sleep(3)
        
        # 4. 사용자 투표 기록 조회
        print("\n4. 사용자 투표 기록 조회...")
        response = requests.get(
            f"{base_url}/api/personalized/user-history/84927",
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            print(f"SUCCESS: Found {data['vote_count']} votes for user 84927")
            print(f"Votes: {json.dumps(data['votes'], ensure_ascii=False, indent=2)}")
        else:
            print(f"FAILED: Get user history failed: {response.text}")
        
        # 5. 유사한 투표 검색
        print("\n5. 유사한 투표 검색...")
        response = requests.get(
            f"{base_url}/api/personalized/similar-votes/84927",
            params={"query": "한식 매운 음식", "n_results": 3},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            print(f"SUCCESS: Found {data['result_count']} similar votes")
            print(f"Similar votes: {json.dumps(data['similar_votes'], ensure_ascii=False, indent=2)}")
        else:
            print(f"FAILED: Similar votes search failed: {response.text}")
        
        # 6. 유사한 식당 검색
        print("\n6. 유사한 식당 검색...")
        response = requests.get(
            f"{base_url}/api/personalized/similar-restaurants",
            params={"query": "한식 매운 음식", "n_results": 3},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            print(f"SUCCESS: Found {data['result_count']} similar restaurants")
            print(f"Similar restaurants: {json.dumps(data['restaurants'], ensure_ascii=False, indent=2)}")
        else:
            print(f"FAILED: Similar restaurants search failed: {response.text}")
        
        # 7. 개인화된 추천 생성
        print("\n7. 개인화된 추천 생성...")
        recommendation_request = {
            "emp_no": "84927",
            "query_text": "한식 매운 음식 추천해주세요"
        }
        response = requests.post(
            f"{base_url}/api/personalized/recommendations",
            json=recommendation_request,
            timeout=15
        )
        if response.status_code == 200:
            recommendations = response.json()
            print(f"SUCCESS: Generated {len(recommendations)} personalized recommendations")
            for i, rec in enumerate(recommendations):
                print(f"\n추천 {i+1}:")
                print(f"  식당: {rec.get('metadata', {}).get('place_name', 'Unknown')}")
                print(f"  메뉴: {rec.get('metadata', {}).get('menu_type', 'Unknown')}")
                print(f"  개인화 점수: {rec.get('personalization_score', 0):.3f}")
                print(f"  추천 이유: {rec.get('recommendation_reason', 'Unknown')}")
        else:
            print(f"FAILED: Personalized recommendations failed: {response.text}")
        
        print("\n" + "=" * 60)
        print("Personalized Recommendation System 테스트 완료!")
        return True
        
    except requests.exceptions.ConnectionError:
        print("CONNECTION ERROR: 서버에 연결할 수 없습니다")
        return False
    except Exception as e:
        print(f"ERROR: 예상치 못한 오류: {str(e)}")
        return False

if __name__ == "__main__":
    print("Personalized Recommendation System 테스트 시작")
    print("=" * 60)
    
    success = test_personalized_recommendation()
    
    if success:
        print("\nSUCCESS! 모든 테스트가 통과했습니다!")
    else:
        print("\nFAILED! 일부 테스트가 실패했습니다.")
    
    print("=" * 60)
