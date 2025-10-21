"""
Quick start script for local development
"""
import subprocess
import sys
import os
import shutil


def main():
    """Run the FastAPI application"""
    # Change to script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    print("🔧 CoFriends FastAPI 서버 시작")
    print("=" * 40)
    
    # Check if .env exists
    if not os.path.exists(".env"):
        print("⚠️  .env 파일을 찾을 수 없습니다. env.example에서 생성합니다...")
        if os.path.exists("env.example"):
            shutil.copy("env.example", ".env")
            print("✅ .env 파일이 생성되었습니다. 필요시 값을 수정하세요.")
        else:
            print("❌ env.example 파일을 찾을 수 없습니다!")
            sys.exit(1)
    else:
        print("✅ .env 파일이 존재합니다.")
    
    # Run uvicorn
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


if __name__ == "__main__":
    main()

