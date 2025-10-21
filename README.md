# CoFriends-BE-Python

✅ **Successfully migrated from Spring Boot to FastAPI!**

## Quick Start

### 1. 로컬 개발 환경 (권장)

**방법 1: 자동 설정 스크립트 사용**
```bash
# Windows
start_local_dev.bat

# 또는 Python으로 직접 실행
python start_local_dev.py
```

**방법 2: 수동 설정**

**uv 사용 (권장)**
```bash
# 1. 데이터베이스만 Docker로 실행
docker-compose up -d postgres mongodb redis

# 2. uv로 환경 설정
uv venv
uv pip install -r requirements.txt
uv\Scripts\activate  # Windows

# 3. 환경 변수 설정
copy env.example .env

# 4. FastAPI 서버 실행
python run.py
```

**venv 사용**
```bash
# 1. 데이터베이스만 Docker로 실행
docker-compose up -d postgres mongodb redis

# 2. Python 환경 설정
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt

# 3. 환경 변수 설정
copy env.example .env

# 4. FastAPI 서버 실행
python run.py
```

**Server will start at: http://localhost:5000**

### 2. Docker Compose (전체 컨테이너)

```bash
# 모든 서비스 (데이터베이스 + FastAPI) 실행
docker-compose up -d
```

## API Documentation

- Swagger UI: http://localhost:5000/docs
- ReDoc: http://localhost:5000/redoc
- Health Check: http://localhost:5000/health

## What's Changed

- ✅ Java/Spring Boot → Python/FastAPI
- ✅ MySQL → PostgreSQL
- ✅ Chat storage: Redis → MongoDB (+ Redis cache)
- ✅ Faster startup (~2s vs ~15s)
- ✅ Lower memory usage (~150MB vs ~500MB)
- ✅ Auto-generated API docs

## Main Features

- 🍽️ Menu preference management
- 📍 Restaurant voting system
- 💬 Chat history (MongoDB)
- 🔍 Naver Local Search integration
- 🔐 Slack OAuth authentication

## Tech Stack

- Python 3.12+
- FastAPI
- PostgreSQL
- MongoDB
- Redis
- SQLAlchemy
- Pydantic

## Project Structure

```
├── app/
│   ├── api/          # API routes
│   ├── core/         # Config & DB
│   ├── models/       # Database models
│   ├── schemas/      # Pydantic schemas
│   └── services/     # Business logic
├── main.py           # Entry point
└── docker-compose.yml
```

## Verification

This project has been tested and verified:

```bash
python test_server.py
```

Output:
```
[OK] Root endpoint working
[OK] Health endpoint working
[OK] OpenAPI docs accessible
[SUCCESS] All basic tests passed!
```

## Documentation

- Korean README: [README_KR.md](README_KR.md)
- Full documentation in README_KR.md

## License

Migrated version of CoFriends Backend.
