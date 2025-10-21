@echo off
echo 🔧 CoFriends FastAPI 로컬 개발 서버
echo ================================================

REM Python 가상환경 활성화 (venv가 있는 경우)
if exist "venv\Scripts\activate.bat" (
    echo 📦 가상환경을 활성화합니다...
    call venv\Scripts\activate.bat
)

REM Python 스크립트 실행
python start_local.py

pause
