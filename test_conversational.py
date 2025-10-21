#!/usr/bin/env python3
"""
Conversational API 테스트 - Bedrock 연결 확인
"""
import requests
import json

def test_conversational_api():
    """Conversational API 테스트"""
    
    print("Conversational API 테스트")
    print("=" * 50)
    
    base_url = "http://localhost:5000"
    
    # 테스트 데이터
    test_data = {
        "question": "안녕하세요! 간단한 인사말을 해주세요.",
        "emp_no": "84927"
    }
    
    try:
        print(f"요청 URL: {base_url}/api/conversational/query")
        print(f"요청 데이터: {json.dumps(test_data, ensure_ascii=False, indent=2)}")
        print("-" * 50)
        
        # POST 요청
        response = requests.post(
            f"{base_url}/api/conversational/query",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"응답 상태 코드: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("SUCCESS! Conversational API 응답:")
            print(f"응답: {result.get('response', 'No response')}")
            print(f"성공 여부: {result.get('success', False)}")
            
            if 'usage' in result:
                print(f"토큰 사용량: {result['usage']}")
            
            return True
        else:
            print(f"FAILED! HTTP {response.status_code}")
            print(f"응답 내용: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("TIMEOUT! 요청 시간 초과")
        return False
    except requests.exceptions.ConnectionError:
        print("CONNECTION ERROR! 서버에 연결할 수 없습니다")
        return False
    except Exception as e:
        print(f"ERROR! 예상치 못한 오류: {str(e)}")
        return False

if __name__ == "__main__":
    print("Conversational API Bedrock 연결 테스트")
    print("=" * 50)
    
    success = test_conversational_api()
    
    if success:
        print("\nSUCCESS! Bedrock이 정상적으로 작동하고 있습니다!")
    else:
        print("\nFAILED! Bedrock 연결에 문제가 있습니다.")
    
    print("=" * 50)
