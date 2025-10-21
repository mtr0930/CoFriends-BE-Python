"""
로컬 개발 환경 시작 스크립트
데이터베이스는 Docker로, FastAPI 앱은 로컬에서 실행
"""
import subprocess
import sys
import os
import shutil
import time
import requests
from pathlib import Path


def check_docker():
    """Docker가 실행 중인지 확인"""
    try:
        subprocess.run(["docker", "--version"], check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def start_databases():
    """데이터베이스 컨테이너들 시작"""
    print("🐳 데이터베이스 컨테이너들을 시작합니다...")
    
    # 데이터베이스만 시작 (FastAPI 앱 제외)
    result = subprocess.run([
        "docker-compose", "up", "-d", "postgres", "mongodb", "redis"
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ 데이터베이스 시작 실패: {result.stderr}")
        return False
    
    print("✅ 데이터베이스 컨테이너들이 시작되었습니다.")
    return True


def wait_for_databases():
    """데이터베이스들이 준비될 때까지 대기"""
    print("⏳ 데이터베이스 연결을 확인하는 중...")
    
    # PostgreSQL 확인
    for i in range(30):
        try:
            import psycopg2
            conn = psycopg2.connect(
                host="localhost",
                port=5432,
                user="postgres",
                password="1234",
                database="cofriends"
            )
            conn.close()
            print("✅ PostgreSQL 연결 성공")
            break
        except:
            time.sleep(1)
    else:
        print("❌ PostgreSQL 연결 실패")
        return False
    
    # Redis 확인
    for i in range(30):
        try:
            import redis
            r = redis.Redis(host="localhost", port=6379, password="1234", db=0)
            r.ping()
            print("✅ Redis 연결 성공")
            break
        except:
            time.sleep(1)
    else:
        print("❌ Redis 연결 실패")
        return False
    
    # MongoDB 확인
    for i in range(30):
        try:
            import pymongo
            client = pymongo.MongoClient(
                "mongodb://mongo:1234@localhost:27017/cofriends_chat"
            )
            client.admin.command('ping')
            print("✅ MongoDB 연결 성공")
            break
        except:
            time.sleep(1)
    else:
        print("❌ MongoDB 연결 실패")
        return False
    
    return True


def setup_environment():
    """환경 설정"""
    print("🔧 환경 설정을 확인합니다...")
    
    # .env 파일 확인
    if not os.path.exists(".env"):
        if os.path.exists("env.example"):
            shutil.copy("env.example", ".env")
            print("✅ .env 파일이 생성되었습니다.")
        else:
            print("❌ env.example 파일을 찾을 수 없습니다!")
            return False
    else:
        print("✅ .env 파일이 존재합니다.")
    
    return True


def start_fastapi():
    """FastAPI 서버 시작"""
    print("\n🚀 FastAPI 서버를 시작합니다...")
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


def stop_databases():
    """데이터베이스 컨테이너들 중지"""
    print("\n🛑 데이터베이스 컨테이너들을 중지합니다...")
    subprocess.run(["docker-compose", "down"], capture_output=True)
    print("✅ 데이터베이스 컨테이너들이 중지되었습니다.")


def main():
    """메인 실행 함수"""
    print("🔧 CoFriends 로컬 개발 환경 시작")
    print("=" * 50)
    
    # 스크립트 디렉토리로 이동
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Docker 확인
    if not check_docker():
        print("❌ Docker가 설치되지 않았거나 실행되지 않고 있습니다.")
        print("Docker Desktop을 설치하고 실행해주세요.")
        sys.exit(1)
    
    try:
        # 환경 설정
        if not setup_environment():
            sys.exit(1)
        
        # 데이터베이스 시작
        if not start_databases():
            sys.exit(1)
        
        # 데이터베이스 연결 확인
        if not wait_for_databases():
            print("❌ 데이터베이스 연결에 실패했습니다.")
            sys.exit(1)
        
        # FastAPI 서버 시작
        start_fastapi()
        
    except KeyboardInterrupt:
        print("\n👋 개발 환경을 종료합니다...")
    finally:
        # 정리 작업
        stop_databases()


if __name__ == "__main__":
    main()
