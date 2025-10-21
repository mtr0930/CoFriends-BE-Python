#!/usr/bin/env python3
"""
웹 인터페이스 테스트 - 실무 최적화 하이브리드 구조
"""
import requests
import json
import time
import asyncio
import aiohttp

def test_web_interface():
    """웹 인터페이스 테스트"""
    
    print("웹 인터페이스 테스트")
    print("=" * 60)
    
    base_url = "http://localhost:5000"
    
    # 1. API 문서 확인
    print("\n1. API 문서 확인...")
    try:
        response = requests.get(f"{base_url}/docs", timeout=10)
        if response.status_code == 200:
            print("SUCCESS: API 문서 접근 가능")
            print(f"   Swagger UI: {base_url}/docs")
            print(f"   ReDoc: {base_url}/redoc")
        else:
            print(f"FAILED: API 문서 접근 실패 - {response.status_code}")
    except Exception as e:
        print(f"ERROR: API 문서 확인 실패 - {str(e)}")
    
    # 2. 하이브리드 채팅 헬스 체크
    print("\n2. 하이브리드 채팅 서비스 헬스 체크...")
    try:
        response = requests.get(f"{base_url}/api/hybrid-chat/health", timeout=10)
        if response.status_code == 200:
            health_data = response.json()
            print("SUCCESS: 하이브리드 채팅 서비스 정상")
            print(f"   상태: {health_data.get('status')}")
            print(f"   컴포넌트: {health_data.get('components')}")
        else:
            print(f"FAILED: 헬스 체크 실패 - {response.status_code}")
    except Exception as e:
        print(f"ERROR: 헬스 체크 실패 - {str(e)}")
    
    # 3. 파이프라인 테스트
    print("\n3. 파이프라인 분석 테스트...")
    test_messages = [
        "한식 추천해주세요",
        "왜 이 식당을 추천했나요?",
        "안녕하세요",
        "매운 음식 어디가 좋을까요?"
    ]
    
    for i, message in enumerate(test_messages, 1):
        try:
            test_data = {
                "message": message,
                "emp_no": "84927",
                "client_id": f"test_client_{i}"
            }
            
            response = requests.post(
                f"{base_url}/api/hybrid-chat/test-pipeline",
                json=test_data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"SUCCESS 메시지 {i}: '{message}'")
                print(f"   분석된 작업 타입: {result.get('analyzed_task_type')}")
            else:
                print(f"FAILED 메시지 {i} 실패: {response.status_code}")
                
        except Exception as e:
            print(f"ERROR 메시지 {i} 오류: {str(e)}")
    
    print("\n" + "=" * 60)
    print("웹 인터페이스 테스트 완료!")
    print("\n테스트 방법:")
    print("1. 브라우저에서 http://localhost:5000/docs 접속")
    print("2. '/api/hybrid-chat/message' 엔드포인트 찾기")
    print("3. 'Try it out' 버튼 클릭")
    print("4. 다음 JSON 데이터로 테스트:")
    print("""
    {
        "message": "한식 추천해주세요",
        "emp_no": "84927",
        "client_id": "test_client"
    }
    """)
    print("5. 'Execute' 버튼 클릭하여 SSE 스트림 확인")

def test_sse_stream():
    """SSE 스트림 테스트"""
    
    print("\nSSE 스트림 테스트")
    print("=" * 60)
    
    base_url = "http://localhost:5000"
    
    try:
        # SSE 스트림 요청
        test_data = {
            "message": "한식 추천해주세요",
            "emp_no": "84927", 
            "client_id": "sse_test_client"
        }
        
        print("SSE 스트림 요청 중...")
        response = requests.post(
            f"{base_url}/api/hybrid-chat/message",
            json=test_data,
            stream=True,
            timeout=30
        )
        
        if response.status_code == 200:
            print("SUCCESS: SSE 스트림 연결 성공")
            print("스트림 데이터:")
            print("-" * 40)
            
            # 스트림 데이터 읽기
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        data_str = line_str[6:]  # 'data: ' 제거
                        try:
                            data = json.loads(data_str)
                            print(f"DATA {data.get('type', 'unknown')}: {data.get('data', {})}")
                        except json.JSONDecodeError:
                            print(f"RAW: {data_str}")
        else:
            print(f"FAILED: SSE 스트림 실패: {response.status_code}")
            
    except Exception as e:
        print(f"ERROR: SSE 스트림 오류: {str(e)}")

def show_usage_guide():
    """사용 가이드 표시"""
    
    print("\n실무 최적화 하이브리드 구조 사용 가이드")
    print("=" * 60)
    
    print("\n아키텍처 구조:")
    print("""
    [Chat UI] CoFriends-FE 
       ↓ (user message)
    [FastAPI]
       ├─ if task == "reason_explanation":
       │       → MCP tool 직접 호출 (LightRAG)
       │
       ├─ if task == "recommendation":
       │       → CF + Embedding 추천 파이프라인 실행
       │
       └─ return SSE stream to FE
    """)
    
    print("\nAPI 엔드포인트:")
    print("• POST /api/hybrid-chat/message - 메인 채팅 API")
    print("• GET  /api/hybrid-chat/health - 서비스 상태 확인")
    print("• POST /api/hybrid-chat/test-pipeline - 파이프라인 테스트")
    
    print("\n메시지 타입별 처리:")
    print("• '한식 추천해주세요' → recommendation 파이프라인")
    print("• '왜 이 식당을 추천했나요?' → reason_explanation 파이프라인")
    print("• '안녕하세요' → general_chat 파이프라인")
    
    print("\n웹 테스트 방법:")
    print("1. http://localhost:5000/docs 접속")
    print("2. '/api/hybrid-chat/message' 선택")
    print("3. JSON 데이터 입력 후 실행")
    print("4. SSE 스트림 응답 확인")

if __name__ == "__main__":
    print("실무 최적화 하이브리드 구조 테스트")
    print("=" * 60)
    
    # 웹 인터페이스 테스트
    test_web_interface()
    
    # SSE 스트림 테스트
    test_sse_stream()
    
    # 사용 가이드
    show_usage_guide()
    
    print("\n모든 테스트 완료!")
    print("=" * 60)
