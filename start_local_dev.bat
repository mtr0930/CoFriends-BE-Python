@echo off
echo 🔧 CoFriends 로컬 개발 환경 시작
echo ================================================

REM 스크립트 디렉토리로 이동
cd /d "%~dp0"

REM Python 가상환경 확인
if not exist "venv" (
    echo 📦 가상환경을 생성합니다...
    python -m venv venv
)

REM 가상환경 활성화
echo 🔄 가상환경을 활성화합니다...
call venv\Scripts\activate.bat

REM 의존성 설치
echo 📥 의존성을 설치합니다...
pip install -r requirements.txt

REM 환경 변수 파일 확인
if not exist ".env" (
    if exist "env.example" (
        echo 📋 환경 변수 파일을 생성합니다...
        copy env.example .env
    ) else (
        echo ❌ env.example 파일을 찾을 수 없습니다!
        pause
        exit /b 1
    )
)

REM 로컬 개발 환경 시작
echo 🚀 로컬 개발 환경을 시작합니다...
python start_local_dev.py

pause
