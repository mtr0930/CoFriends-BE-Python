#!/usr/bin/env python3
"""
로컬 서버 테스트 스크립트
"""
import requests
import time
import sys

def test_server():
    """서버 연결 테스트"""
    base_url = "http://localhost:5000"
    
    print("🧪 CoFriends FastAPI 서버 테스트")
    print("=" * 40)
    
    # 1. 루트 엔드포인트 테스트
    try:
        print("1️⃣ 루트 엔드포인트 테스트...")
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code == 200:
            print("✅ 루트 엔드포인트 정상")
            print(f"   응답: {response.json()}")
        else:
            print(f"❌ 루트 엔드포인트 오류: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ 루트 엔드포인트 연결 실패: {e}")
        return False
    
    # 2. 헬스 체크 테스트
    try:
        print("\n2️⃣ 헬스 체크 테스트...")
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ 헬스 체크 정상")
            print(f"   응답: {response.json()}")
        else:
            print(f"❌ 헬스 체크 오류: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ 헬스 체크 연결 실패: {e}")
        return False
    
    # 3. API 문서 접근 테스트
    try:
        print("\n3️⃣ API 문서 접근 테스트...")
        response = requests.get(f"{base_url}/docs", timeout=5)
        if response.status_code == 200:
            print("✅ API 문서 접근 정상")
        else:
            print(f"❌ API 문서 접근 오류: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ API 문서 접근 실패: {e}")
        return False
    
    print("\n🎉 모든 테스트가 성공했습니다!")
    print(f"📚 API 문서: {base_url}/docs")
    print(f"🔍 Health Check: {base_url}/health")
    return True

def main():
    """메인 함수"""
    print("서버가 실행 중인지 확인합니다...")
    print("서버가 실행되지 않은 경우 먼저 다음 명령어로 서버를 시작하세요:")
    print("python start_local.py")
    print()
    
    # 잠시 대기
    time.sleep(1)
    
    if test_server():
        sys.exit(0)
    else:
        print("\n❌ 서버 테스트 실패")
        print("서버가 실행 중인지 확인하세요.")
        sys.exit(1)

if __name__ == "__main__":
    main()
