# CoFriends FastAPI 로컬 개발 설정

## 🚀 빠른 시작

### 1. 의존성 설치
```bash
# 가상환경 생성 (선택사항)
python -m venv venv

# 가상환경 활성화 (Windows)
venv\Scripts\activate

# 가상환경 활성화 (Linux/Mac)
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt
```

### 2. 서버 실행

#### 방법 1: Python 스크립트 사용 (권장)
```bash
python start_local.py
```

#### 방법 2: Windows 배치 파일 사용
```cmd
start_local.bat
```

#### 방법 3: 직접 실행
```bash
python -m uvicorn main:app --host 0.0.0.0 --port 5000 --reload
```

### 3. 서버 확인
- **서버 주소**: http://localhost:5000
- **API 문서**: http://localhost:5000/docs
- **Health Check**: http://localhost:5000/health

## 📋 필요한 서비스

### 필수 서비스 (로컬에서 실행 필요)
1. **PostgreSQL** (포트 5432)
2. **MongoDB** (포트 27017) 
3. **Redis** (포트 6379)

### Docker로 서비스 실행 (권장)
```bash
# Docker Compose로 필요한 서비스들 실행
docker-compose up -d postgres mongodb redis
```

## ⚙️ 환경 설정

### .env 파일 설정
`env.example` 파일을 `.env`로 복사하고 다음 값들을 설정하세요:

```env
# 데이터베이스 설정
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=1234
POSTGRES_DB=cofriends

MONGODB_HOST=localhost
MONGODB_PORT=27017
MONGODB_USERNAME=mongo
MONGODB_PASSWORD=1234
MONGODB_DATABASE=cofriends_chat

REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=1234
```

## 🔧 문제 해결

### 1. 포트 충돌
- 5000번 포트가 사용 중인 경우, `start_local.py`에서 포트 번호를 변경하세요.

### 2. 데이터베이스 연결 오류
- PostgreSQL, MongoDB, Redis가 실행 중인지 확인하세요.
- Docker를 사용하는 경우: `docker-compose up -d`

### 3. 의존성 설치 오류
```bash
# pip 업그레이드
python -m pip install --upgrade pip

# 의존성 재설치
pip install -r requirements.txt --force-reinstall
```

## 📁 프로젝트 구조
```
CoFriends-BE-Python/
├── main.py              # FastAPI 메인 애플리케이션
├── start_local.py       # 로컬 개발용 실행 스크립트
├── start_local.bat      # Windows용 실행 배치 파일
├── requirements.txt     # Python 의존성
├── env.example         # 환경 변수 예시
├── app/                # 애플리케이션 코드
│   ├── api/           # API 라우터
│   ├── core/          # 핵심 설정
│   ├── models/        # 데이터 모델
│   └── services/      # 비즈니스 로직
└── venv/              # 가상환경 (선택사항)
```

## 🎯 API 엔드포인트

### 기본 엔드포인트
- `GET /` - 루트 정보
- `GET /health` - 헬스 체크
- `GET /docs` - Swagger UI 문서
- `GET /redoc` - ReDoc 문서

### API 엔드포인트
- `GET /api/` - API 정보
- `POST /api/chat` - 채팅 API
- `GET /sse/events` - SSE 이벤트 스트림

## 🚨 주의사항

1. **개발 환경 전용**: 이 설정은 로컬 개발용입니다.
2. **보안**: 프로덕션에서는 적절한 보안 설정이 필요합니다.
3. **데이터베이스**: 로컬 데이터베이스가 필요합니다.
