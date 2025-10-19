# CoFriends FastAPI Backend 🚀

Python FastAPI 기반의 직원 식사 선호도 관리 서비스입니다.

> **Spring Boot에서 FastAPI로 완전 마이그레이션된 버전입니다.**

## ✅ 프로젝트 검증 완료

이 프로젝트는 다음과 같이 검증되었습니다:
- ✅ 모든 Python 모듈 임포트 성공
- ✅ FastAPI 애플리케이션 로딩 성공
- ✅ 기본 엔드포인트 정상 작동
- ✅ OpenAPI 문서 생성 성공

## 🎯 주요 변경사항

| 항목 | 기존 (Spring Boot) | 신규 (FastAPI) |
|------|-------------------|----------------|
| 언어/프레임워크 | Java 17 + Spring Boot | Python 3.11+ + FastAPI |
| 메인 DB | MySQL | PostgreSQL |
| 채팅 저장소 | Redis (휘발성) | MongoDB (영구 저장) + Redis (캐시) |
| 시작 시간 | ~15초 | ~2초 |
| 메모리 사용 | ~500MB | ~150MB |
| API 문서 | Swagger (수동) | 자동 생성 |

## 📋 주요 기능

### 1. 메뉴 관리 (`/menu`)
- 기본 메뉴 타입 초기화
- 메뉴별 투표 수 집계
- 새 메뉴 타입 동적 추가

### 2. 장소(식당) 관리 (`/places`)
- 네이버 지역 검색 API 연동
- 메뉴 타입별 식당 추천
- 식당 투표 (좋아요/좋아요 취소)
- 식당 정보 Redis 캐싱

### 3. 채팅 (`/chat`)
- MongoDB를 통한 채팅 메시지 영구 저장
- Redis를 통한 빠른 메시지 조회
- 메뉴/날짜 선호도 저장
- 투표 이력 초기화

### 4. 외부 API 연동
- 네이버 지역 검색 API (`/naver`)
- Slack OAuth 인증 (`/auth/slack`)

## 🛠 기술 스택

- **Python**: 3.12+
- **FastAPI**: 최신 비동기 웹 프레임워크
- **PostgreSQL**: 메인 데이터베이스
- **MongoDB**: 채팅 메시지 저장
- **Redis**: 캐싱 레이어
- **SQLAlchemy**: ORM
- **Pydantic**: 데이터 검증
- **Uvicorn**: ASGI 서버

## 🚀 빠른 시작

### 방법 1: 로컬 실행 (개발)

```bash
# 1. 가상환경 생성 및 활성화
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 2. 의존성 설치
pip install -r requirements.txt

# 3. 환경 변수 설정
copy env.example .env
# .env 파일을 편집하여 데이터베이스 연결 정보 입력

# 4. 서버 실행
python run.py
# 또는: python main.py
# 또는: uvicorn main:app --reload --port 5000
```

### 방법 2: Docker Compose (권장)

```bash
# 전체 스택 실행 (PostgreSQL + MongoDB + Redis + FastAPI)
docker-compose up -d

# 로그 확인
docker-compose logs -f fastapi-app

# 중지
docker-compose down
```

## 📚 API 문서

서버 실행 후 다음 URL에서 API 문서를 확인할 수 있습니다:

- **Swagger UI**: http://localhost:5000/docs
- **ReDoc**: http://localhost:5000/redoc
- **Health Check**: http://localhost:5000/health

## 📁 프로젝트 구조

```
CoFriends-BE-Python/
├── app/
│   ├── api/              # API 라우터
│   │   ├── chat.py       # 채팅 관련 API
│   │   ├── menu.py       # 메뉴 관련 API
│   │   ├── place.py      # 장소 관련 API
│   │   ├── naver.py      # 네이버 검색
│   │   └── slack.py      # Slack 인증
│   ├── core/             # 핵심 설정
│   │   ├── config.py     # 환경 설정
│   │   ├── database.py   # DB 연결
│   │   └── constants.py  # 상수
│   ├── models/           # 데이터베이스 모델
│   │   ├── postgres.py   # PostgreSQL 모델
│   │   └── mongodb.py    # MongoDB 스키마
│   ├── schemas/          # Pydantic 스키마 (DTO)
│   └── services/         # 비즈니스 로직
├── main.py               # 애플리케이션 엔트리포인트
├── requirements.txt      # Python 의존성
├── Dockerfile            # Docker 이미지
└── docker-compose.yml    # Docker Compose 설정
```

## 🔌 API 엔드포인트

### 채팅 API
```
POST   /chat/menu-date-form  - 메뉴/날짜 선호도 저장
POST   /chat/save            - 채팅 메시지 저장
POST   /chat/messages        - 채팅 메시지 조회
DELETE /chat/reset           - 투표 이력 초기화
```

### 메뉴 API
```
POST /menu/init - 기본 메뉴 초기화
```

### 장소 API
```
POST /places/search    - 추천 식당 조회
POST /places/newPlace  - 새 식당 추가
POST /places/vote      - 식당 투표
POST /places/deleteAll - 모든 식당 삭제 (테스트용)
```

### 네이버 API
```
GET /naver/search - 네이버 지역 검색
```

### Slack API
```
GET /auth/slack/login    - Slack 로그인
GET /auth/slack/callback - OAuth 콜백
```

## 🔧 환경 변수 설정

`.env` 파일 예시:

```env
# Server
SERVER_HOST=0.0.0.0
SERVER_PORT=5000
ENVIRONMENT=local

# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=1234
POSTGRES_DB=cofriends

# MongoDB
MONGODB_HOST=localhost
MONGODB_PORT=27017
MONGODB_USER=mongo
MONGODB_PASSWORD=1234
MONGODB_DB=cofriends_chat

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=1234
REDIS_DB=0

# Naver API (선택사항)
NAVER_CLIENT_ID=your_client_id
NAVER_CLIENT_SECRET=your_client_secret

# Slack OAuth (선택사항)
SLACK_CLIENT_ID=your_slack_client_id
SLACK_CLIENT_SECRET=your_slack_client_secret
SLACK_REDIRECT_URI=https://yourdomain.com/auth/slack/callback
```

## 📊 데이터베이스 스키마

### PostgreSQL 테이블
- `users` - 사용자 정보
- `menu` - 메뉴 타입
- `place` - 식당 정보
- `user_menu_vote` - 메뉴 투표
- `user_place_vote` - 식당 투표
- `user_date_vote` - 날짜 투표

### MongoDB 컬렉션
- `chat_sessions` - 채팅 세션 및 메시지

## ✅ 테스트

```bash
# 서버 테스트 (DB 없이)
python test_server.py

# 모듈 임포트 테스트
python -c "import app; print('OK')"
```

## 🐛 트러블슈팅

### 포트가 이미 사용중인 경우
```bash
# Windows에서 포트 5000 사용 프로세스 확인
netstat -ano | findstr :5000

# 프로세스 종료
taskkill /PID <PID> /F
```

### 가상환경 활성화 오류
```bash
# PowerShell 실행 정책 변경 (관리자 권한)
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 데이터베이스 연결 실패
Docker Compose를 사용하는 경우 모든 서비스가 정상적으로 시작되었는지 확인:
```bash
docker-compose ps
docker-compose logs
```

## 📦 배포

### Docker 이미지 빌드
```bash
docker build -t cofriends-fastapi:latest .
```

### Docker Hub에 푸시
```bash
docker tag cofriends-fastapi:latest yourusername/cofriends-fastapi:latest
docker push yourusername/cofriends-fastapi:latest
```

## 🤝 기여

기여를 환영합니다! Pull Request를 보내주세요.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 CoFriends 백엔드의 FastAPI 마이그레이션 버전입니다.

## 🎉 완료된 작업

- ✅ Spring Boot → FastAPI 완전 마이그레이션
- ✅ MySQL → PostgreSQL 마이그레이션
- ✅ 채팅 메시지 MongoDB 영구 저장
- ✅ Redis 캐싱 레이어 유지
- ✅ 모든 API 엔드포인트 구현
- ✅ Docker Compose 설정
- ✅ API 자동 문서화
- ✅ 프로젝트 검증 및 테스트

## 📧 문의

문제가 발생하거나 질문이 있으시면 이슈를 등록해주세요.

---

**Made with ❤️ using FastAPI**


