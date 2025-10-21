"""
날짜 및 메뉴 추천 API 테스트
"""
import requests
import json
import time

def test_date_menu_recommendations():
    """날짜 및 메뉴 추천 API 테스트"""
    
    print("날짜 및 메뉴 추천 API 테스트")
    print("=" * 60)
    
    base_url = "http://localhost:5000"
    
    # 1. 서비스 헬스 체크
    print("\n1. 서비스 헬스 체크...")
    try:
        response = requests.get(f"{base_url}/api/date-menu-recommendations/health", timeout=10)
        if response.status_code == 200:
            health_data = response.json()
            print("SUCCESS: 서비스 정상")
            print(f"   상태: {health_data.get('status')}")
            print(f"   서비스: {health_data.get('service')}")
            print(f"   기능: {health_data.get('features')}")
        else:
            print(f"FAILED: 헬스 체크 실패 - {response.status_code}")
    except Exception as e:
        print(f"ERROR: 헬스 체크 실패 - {str(e)}")
    
    # 2. 날짜 추천 테스트
    print("\n2. 날짜 추천 테스트...")
    try:
        test_data = {
            "emp_no": "84927",
            "query_text": "회식 날짜 추천해주세요"
        }
        
        response = requests.post(
            f"{base_url}/api/date-menu-recommendations/dates",
            json=test_data,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print("SUCCESS: 날짜 추천 생성")
            print(f"   추천 개수: {data.get('count', 0)}")
            print("   추천 날짜:")
            for i, rec in enumerate(data.get('recommendations', [])[:3]):
                print(f"     {i+1}. {rec.get('date')} ({rec.get('day_of_week')}요일) - {rec.get('reason')} (점수: {rec.get('score', 0):.2f})")
        else:
            print(f"FAILED: 날짜 추천 실패 - {response.status_code}")
            print(f"   응답: {response.text}")
            
    except Exception as e:
        print(f"ERROR: 날짜 추천 오류 - {str(e)}")
    
    # 3. 메뉴 추천 테스트
    print("\n3. 메뉴 추천 테스트...")
    try:
        test_data = {
            "emp_no": "84927",
            "query_text": "메뉴 추천해주세요"
        }
        
        response = requests.post(
            f"{base_url}/api/date-menu-recommendations/menus",
            json=test_data,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print("SUCCESS: 메뉴 추천 생성")
            print(f"   추천 개수: {data.get('count', 0)}")
            print("   추천 메뉴:")
            for i, rec in enumerate(data.get('recommendations', [])[:5]):
                print(f"     {i+1}. {rec.get('name')} - {rec.get('reason')} (점수: {rec.get('score', 0):.2f})")
        else:
            print(f"FAILED: 메뉴 추천 실패 - {response.status_code}")
            print(f"   응답: {response.text}")
            
    except Exception as e:
        print(f"ERROR: 메뉴 추천 오류 - {str(e)}")
    
    # 4. 종합 추천 테스트
    print("\n4. 종합 추천 테스트...")
    try:
        test_data = {
            "emp_no": "84927",
            "query_text": "회식 날짜와 메뉴를 함께 추천해주세요"
        }
        
        response = requests.post(
            f"{base_url}/api/date-menu-recommendations/comprehensive",
            json=test_data,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print("SUCCESS: 종합 추천 생성")
            print(f"   날짜 추천: {len(data.get('date_recommendations', []))}개")
            print(f"   메뉴 추천: {len(data.get('menu_recommendations', []))}개")
            print(f"   조합 추천: {len(data.get('combinations', []))}개")
            print(f"   컨텍스트: {data.get('context', 'N/A')}")
            print(f"   계절: {data.get('season', 'N/A')}")
            
            # 상위 조합 추천 표시
            combinations = data.get('combinations', [])[:3]
            if combinations:
                print("   상위 조합 추천:")
                for i, combo in enumerate(combinations):
                    print(f"     {i+1}. {combo.get('date')} ({combo.get('day_of_week')}요일) + {combo.get('menu')} - {combo.get('reason')} (점수: {combo.get('score', 0):.2f})")
        else:
            print(f"FAILED: 종합 추천 실패 - {response.status_code}")
            print(f"   응답: {response.text}")
            
    except Exception as e:
        print(f"ERROR: 종합 추천 오류 - {str(e)}")
    
    print("\n" + "=" * 60)
    print("날짜 및 메뉴 추천 테스트 완료!")
    print("\n사용 방법:")
    print("1. 프론트엔드에서 '좋은 회식 날짜 추천해줘' 입력")
    print("2. 프론트엔드에서 '메뉴 추천해줘' 입력")
    print("3. 프론트엔드에서 '날짜와 메뉴 함께 추천해줘' 입력")

if __name__ == "__main__":
    test_date_menu_recommendations()
