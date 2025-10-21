#!/usr/bin/env python3
"""
모든 엔드포인트 테스트 스크립트
"""
import requests
import json
import sys

def test_endpoint(method, url, data=None, headers=None):
    """엔드포인트 테스트"""
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=5)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers, timeout=5)
        else:
            return False, f"Unsupported method: {method}"
        
        return response.status_code == 200, f"Status: {response.status_code}"
    except requests.exceptions.RequestException as e:
        return False, f"Request error: {e}"

def main():
    """메인 테스트 함수"""
    base_url = "http://localhost:5000"
    
    print("CoFriends API 엔드포인트 테스트")
    print("=" * 50)
    
    # 테스트할 엔드포인트들
    endpoints = [
        # 기본 엔드포인트
        ("GET", f"{base_url}/", "루트 엔드포인트"),
        ("GET", f"{base_url}/health", "헬스 체크"),
        ("GET", f"{base_url}/docs", "API 문서"),
        
        # API 엔드포인트들
        ("GET", f"{base_url}/api/", "API 정보"),
        ("GET", f"{base_url}/api/chat-history/health", "채팅 히스토리 헬스 체크"),
        ("GET", f"{base_url}/api/chat-history/users/84927/active-session", "활성 세션 조회"),
        
        # SSE 엔드포인트들
        ("GET", f"{base_url}/sse/events?client_id=test&channels=votes", "SSE 이벤트"),
    ]
    
    success_count = 0
    total_count = len(endpoints)
    
    for method, url, description in endpoints:
        print(f"\n테스트: {description}")
        print(f"   URL: {url}")
        
        success, message = test_endpoint(method, url)
        
        if success:
            print(f"   SUCCESS: {message}")
            success_count += 1
        else:
            print(f"   FAILED: {message}")
    
    print(f"\n테스트 결과: {success_count}/{total_count} 성공")
    
    if success_count == total_count:
        print("모든 엔드포인트가 정상 작동합니다!")
        return True
    else:
        print("일부 엔드포인트에 문제가 있습니다.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
