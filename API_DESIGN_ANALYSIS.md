# CoFriends FastAPI 서버 기능 설계 분석

## 📊 전체 API 구조

CoFriends는 **직원들의 식사 선호도 관리 및 투표 시스템**입니다.

```
CoFriends API
├── 채팅 API (/chat) - 메시지 저장 및 선호도 관리
├── 메뉴 API (/menu) - 메뉴 타입 관리
├── 장소 API (/places) - 식당 관리 및 투표
└── 인증 API (/auth/slack) - Slack OAuth
```

---

## 🔥 핵심 기능 분석

### 1. **채팅 API** (`/chat`)

#### 1.1 메뉴/날짜 선호도 저장
**POST** `/chat/menu-date-form`

**흐름도:**
```
사용자 → 메뉴 & 날짜 선택
    ↓
메뉴 타입 검증 (신규 메뉴 자동 추가)
    ↓
사용자 정보 확인/생성
    ↓
투표 데이터 저장 (기존 투표 덮어쓰기)
    ↓
월별 식당 정보 반환 (Redis 캐싱)
```

**데이터 흐름:**
- Input: `{ empNo, menuTypes[], preferredDates[] }`
- Process:
  1. 새로운 메뉴 타입이 있으면 `menu` 테이블에 자동 추가
  2. 사용자가 없으면 `users` 테이블에 생성
  3. 기존 투표 삭제 후 새 투표 저장:
     - `user_menu_vote`: 메뉴별 투표
     - `user_date_vote`: 날짜별 투표
  4. 현재 월의 식당 목록 조회 및 캐싱
- Output: `{ monthKey, placesByMenuType }`

#### 1.2 채팅 메시지 저장
**POST** `/chat/save`

**저장소:**
- **MongoDB**: 영구 저장소
- **Redis**: 빠른 조회를 위한 캐시 (30일 TTL)

**데이터 구조:**
```json
{
  "empNo": "12345",
  "messages": [
    {
      "role": "user | assistant",
      "content": "...",
      "messageId": "...",
      "timestamp": 1234567890
    }
  ]
}
```

#### 1.3 채팅 메시지 조회
**POST** `/chat/messages`

**조회 순서:**
1. Redis 캐시 먼저 확인 → 있으면 즉시 반환
2. 없으면 MongoDB에서 조회 → Redis에 캐싱 후 반환

#### 1.4 투표 이력 초기화
**DELETE** `/chat/reset?empNo=xxx`

**삭제 대상:**
- 메뉴 투표 (`user_menu_vote`)
- 날짜 투표 (`user_date_vote`)
- 식당 투표 (`user_place_vote`)

---

### 2. **메뉴 API** (`/menu`)

#### 2.1 메뉴 초기화
**POST** `/menu/init`

**기능:**
- 기본 메뉴 타입 초기화 (한식, 중식, 일식, 양식, 분식, 치킨, 피자, 햄버거, 아시안, 카페/디저트)
- 각 메뉴별 투표 수 집계

**응답:**
```json
{
  "status": "S",
  "message": "기본 메뉴 초기화 완료",
  "menuTypes": ["한식", "중식", ...],
  "voteCounts": {
    "한식": 5,
    "중식": 3,
    ...
  }
}
```

---

### 3. **장소(식당) API** (`/places`)

#### 3.1 식당 검색/조회
**POST** `/places/search`

**데이터 흐름:**
```
DB에서 메뉴별 식당 목록 조회
    ↓
각 식당의 투표 수 계산
    ↓
월별로 그룹핑 (monthKey: YYYYMM)
    ↓
Redis에 캐싱 (30일 TTL)
    ↓
클라이언트에 반환
```

**응답 구조:**
```json
{
  "monthKey": "202510",
  "placesByMenuType": {
    "한식": [
      {
        "placeId": 1,
        "place_nm": "백반집",
        "menu_type": "한식",
        "address": "서울시 강남구...",
        "contact_no": "02-1234-5678",
        "vote_cnt": 5
      }
    ],
    "중식": [...]
  }
}
```

#### 3.2 새 식당 추가
**POST** `/places/newPlace`

**Input:**
```json
{
  "placeName": "맛있는 집",
  "menuType": "한식"
}
```

**기능:**
- 중복 체크 (같은 이름 + 메뉴 타입)
- 없으면 새로 생성, 있으면 기존 ID 반환

#### 3.3 식당 투표
**POST** `/places/vote`

**Input:**
```json
{
  "empNo": "12345",
  "placeId": 1,
  "action": "like" | "unlike"
}
```

**로직:**
- `like`: 투표 추가 (중복 방지)
- `unlike`: 투표 삭제

**응답:**
```json
{
  "placeId": 1,
  "voteCount": 5,
  "isVoted": true
}
```

#### 3.4 식당 전체 삭제 (테스트용)
**POST** `/places/deleteAll`

---

### 4. **인증 API** (`/auth/slack`)

#### 4.1 Slack 로그인
**GET** `/auth/slack/login`
- Slack OAuth 페이지로 리다이렉트

#### 4.2 OAuth 콜백
**GET** `/auth/slack/callback?code=xxx`
- Authorization code → Access token 교환
- 사용자 정보 조회

---

## 🗄️ 데이터베이스 설계

### PostgreSQL (메인 DB)

```sql
-- 사용자 테이블
users (user_id, emp_no, emp_nm)

-- 메뉴 타입 테이블
menu (menu_id, menu_type, created_at, updated_at)

-- 식당 테이블
place (place_id, place_nm, menu_type, address, contact_no, naver_place_id)

-- 메뉴 투표 테이블
user_menu_vote (vote_id, user_id, menu_id, created_at, updated_at)

-- 식당 투표 테이블
user_place_vote (id, user_id, place_id, created_at, updated_at)

-- 날짜 투표 테이블
user_date_vote (id, emp_no, preferred_date, created_at)
```

**관계:**
- `users` 1:N `user_menu_vote`
- `users` 1:N `user_place_vote`
- `menu` 1:N `user_menu_vote`
- `place` 1:N `user_place_vote`

### MongoDB (채팅 DB)

```javascript
// chat_sessions 컬렉션
{
  "empNo": "12345",
  "messages": [
    {
      "role": "user | assistant",
      "content": "...",
      "messageId": "...",
      "timestamp": 1234567890,
      "menuTypes": [...],
      "preferredDates": [...],
      "votedPlaceIds": [...],
      "restaurantData": {...}
    }
  ],
  "createdAt": ISODate("..."),
  "updatedAt": ISODate("...")
}
```

### Redis (캐시)

```
Key 구조:
- chat:{empNo} → 채팅 메시지 (30일 TTL)
- places:{YYYYMM} → 월별 식당 목록 (30일 TTL)
```

---

## 🔄 주요 비즈니스 로직

### 1. **투표 시스템**
- **덮어쓰기 방식**: 새로운 투표 시 기존 투표 삭제 후 저장
- **중복 방지**: 같은 사용자의 같은 항목 중복 투표 불가
- **실시간 집계**: 투표 시마다 카운트 재계산

### 2. **캐싱 전략**
- **Read-Through Cache**: 조회 시 Redis → DB 순서
- **Write-Through Cache**: 저장 시 DB → Redis 동시 업데이트
- **TTL 관리**: 30일 자동 만료

### 3. **식당 관리**
- ~~**자동 수집**: 네이버 API 연동~~ (제거됨)
- **수동 추가**: 사용자가 직접 식당 등록
- **월별 분류**: YYYYMM 형식으로 그룹핑

---

## 🎯 API 사용 시나리오

### 시나리오 1: 사용자 선호도 등록
```
1. POST /menu/init (메뉴 초기화)
2. POST /chat/menu-date-form (선호도 저장)
   → 메뉴 타입: ["한식", "중식"]
   → 날짜: ["2025-10-20", "2025-10-21"]
3. 응답: 해당 월의 식당 목록
```

### 시나리오 2: 식당 투표
```
1. POST /places/search (식당 목록 조회)
2. POST /places/vote (식당에 좋아요)
   → empNo: "12345"
   → placeId: 1
   → action: "like"
3. 응답: 업데이트된 투표 수
```

### 시나리오 3: 채팅 히스토리 관리
```
1. POST /chat/save (메시지 저장)
2. POST /chat/messages (메시지 조회)
3. DELETE /chat/reset (투표 초기화)
```

---

## ⚡ 성능 최적화

1. **Redis 캐싱**: 자주 조회되는 데이터 캐싱
2. **Lazy Loading**: 필요할 때만 관계 데이터 로드
3. **Index 전략**: emp_no, menu_type 등 인덱스 설정
4. **MongoDB**: 채팅 메시지 빠른 조회

---

## 🔒 보안 고려사항

1. **SQL Injection**: SQLAlchemy ORM 사용으로 방지
2. **CORS**: 허용된 도메인만 접근 가능
3. **Input Validation**: Pydantic 스키마로 입력 검증
4. **Rate Limiting**: (추가 필요)

---

## 📈 확장 가능성

1. **실시간 알림**: WebSocket 추가
2. **추천 알고리즘**: 협업 필터링 기반 식당 추천
3. **통계 대시보드**: 메뉴별 인기도, 시간대별 분석
4. **그룹 투표**: 팀 단위 투표 기능

---

이제 네이버 API 의존성이 제거되어, 식당은 **수동으로만 추가**할 수 있습니다!


