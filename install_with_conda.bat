@echo off
echo 🔧 Conda를 사용한 CoFriends 환경 설정
echo ================================================

REM Conda가 설치되어 있는지 확인
conda --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Conda가 설치되지 않았습니다.
    echo Miniconda를 설치해주세요: https://docs.conda.io/en/latest/miniconda.html
    pause
    exit /b 1
)

echo ✅ Conda가 설치되어 있습니다.

REM Python 3.11 환경 생성
echo 📦 Python 3.11 환경을 생성합니다...
conda create -n cofriends python=3.11 -y

REM 환경 활성화
echo 🔄 환경을 활성화합니다...
call conda activate cofriends

REM 기본 패키지 설치
echo 📥 기본 패키지들을 설치합니다...
conda install -c conda-forge fastapi uvicorn sqlalchemy psycopg2 pymongo redis pandas scikit-learn -y

REM implicit 패키지 설치 (conda-forge에서 미리 컴파일된 버전)
echo 📥 implicit 패키지를 설치합니다...
conda install -c conda-forge implicit -y

REM 나머지 패키지들 pip로 설치
echo 📥 나머지 패키지들을 설치합니다...
pip install motor pydantic pydantic-settings python-dotenv httpx python-multipart boto3 botocore chromadb sentence-transformers neo4j langchain langchain-openai langchain-community

echo ✅ 설치가 완료되었습니다!
echo 🚀 서버를 실행하려면: python run.py
pause
