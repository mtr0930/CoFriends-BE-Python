#!/usr/bin/env python3
"""
로컬 개발용 FastAPI 서버 시작 스크립트
간단한 설정으로 로컬에서 바로 실행 가능
"""
import os
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Python 버전 확인"""
    if sys.version_info < (3, 11):
        print("❌ Python 3.11 이상이 필요합니다.")
        print(f"현재 버전: {sys.version}")
        sys.exit(1)
    print(f"✅ Python 버전 확인: {sys.version}")

def check_dependencies():
    """필수 패키지 설치 확인"""
    try:
        import fastapi
        import uvicorn
        print("✅ FastAPI 및 Uvicorn 설치 확인")
    except ImportError:
        print("❌ 필수 패키지가 설치되지 않았습니다.")
        print("다음 명령어로 설치하세요:")
        print("pip install -r requirements.txt")
        sys.exit(1)

def setup_environment():
    """환경 설정"""
    # 프로젝트 루트로 이동
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # .env 파일 확인 및 생성
    env_file = script_dir / ".env"
    env_example = script_dir / "env.example"
    
    if not env_file.exists():
        if env_example.exists():
            print("📝 .env 파일을 생성합니다...")
            with open(env_example, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 로컬 개발용 설정으로 수정
            content = content.replace("MONGODB_HOST=mongodb", "MONGODB_HOST=localhost")
            content = content.replace("MONGODB_USER=mongo", "MONGODB_USERNAME=mongo")
            content = content.replace("MONGODB_DB=cofriends_chat", "MONGODB_DATABASE=cofriends_chat")
            
            with open(env_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print("✅ .env 파일이 생성되었습니다.")
        else:
            print("❌ env.example 파일을 찾을 수 없습니다.")
            sys.exit(1)
    else:
        print("✅ .env 파일이 존재합니다.")

def start_server():
    """서버 시작"""
    print("\n🚀 CoFriends FastAPI 서버를 시작합니다...")
    print("📍 서버 주소: http://localhost:5000")
    print("📚 API 문서: http://localhost:5000/docs")
    print("🔍 Health Check: http://localhost:5000/health")
    print("\n⏹️  서버를 중지하려면 Ctrl+C를 누르세요.\n")
    
    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "main:app",
            "--host", "0.0.0.0",
            "--port", "5000",
            "--reload",
            "--log-level", "info"
        ])
    except KeyboardInterrupt:
        print("\n👋 서버가 중지되었습니다.")

def main():
    """메인 함수"""
    print("🔧 CoFriends FastAPI 로컬 개발 서버")
    print("=" * 50)
    
    # 1. Python 버전 확인
    check_python_version()
    
    # 2. 의존성 확인
    check_dependencies()
    
    # 3. 환경 설정
    setup_environment()
    
    # 4. 서버 시작
    start_server()

if __name__ == "__main__":
    main()
