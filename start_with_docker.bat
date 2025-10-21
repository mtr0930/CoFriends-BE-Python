@echo off
echo 🐳 Docker를 사용한 CoFriends 환경 시작
echo ================================================

REM Docker가 실행 중인지 확인
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker가 설치되지 않았거나 실행되지 않고 있습니다.
    echo Docker Desktop을 설치하고 실행해주세요.
    pause
    exit /b 1
)

echo ✅ Docker가 실행 중입니다.

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

echo 🚀 Docker Compose로 모든 서비스를 시작합니다...
docker-compose up -d

echo ✅ 모든 서비스가 시작되었습니다!
echo 📍 서버 주소: http://localhost:5000
echo 📚 API 문서: http://localhost:5000/docs
echo 🔍 Health Check: http://localhost:5000/health

echo.
echo ⏹️  서비스를 중지하려면: docker-compose down
pause
