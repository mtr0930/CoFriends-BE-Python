# 대화형 투표 시스템 API 설계

## 1. 자동 투표 요청 시스템

### 1.1 매달 1일 자동 투표 요청
**POST** `/chat/auto-vote-request`

**기능:**
- 매달 1일 자동으로 모든 사용자에게 투표 요청
- SSE를 통한 실시간 알림 전송
- 투표 기간 설정 (예: 1일~7일)

**요청:**
```json
{
  "month": "2025-10",
  "vote_period_days": 7,
  "message": "이번 달 회식 투표를 시작합니다!"
}
```

**응답:**
```json
{
  "status": "S",
  "message": "투표 요청이 모든 사용자에게 전송되었습니다",
  "sent_to_users": 150,
  "vote_deadline": "2025-10-07T23:59:59Z"
}
```

### 1.2 투표 상태 조회
**GET** `/chat/vote-status/{month}`

**응답:**
```json
{
  "month": "2025-10",
  "total_users": 150,
  "voted_users": 45,
  "vote_rate": 30.0,
  "deadline": "2025-10-07T23:59:59Z",
  "remaining_days": 3
}
```

## 2. 대화형 질문 처리 시스템

### 2.1 자연어 질문 처리
**POST** `/chat/conversational-query`

**요청:**
```json
{
  "emp_no": "84927",
  "question": "이번달 투표 결과 알려줘",
  "context": {
    "current_month": "2025-10",
    "user_preferences": ["한식", "중식"]
  }
}
```

**응답:**
```json
{
  "status": "S",
  "answer": "이번 달 투표 결과를 알려드리겠습니다. 현재까지 45명이 투표했으며, 한식이 15표로 1위입니다.",
  "data": {
    "vote_results": {
      "한식": 15,
      "중식": 12,
      "일식": 8
    },
    "total_votes": 45
  },
  "suggested_actions": [
    "투표하기",
    "식당 추천 받기"
  ]
}
```

### 2.2 개인 투표 이력 조회
**GET** `/chat/my-vote-history/{emp_no}`

**응답:**
```json
{
  "emp_no": "84927",
  "vote_history": [
    {
      "month": "2025-10",
      "menu_votes": ["한식", "중식"],
      "date_votes": ["2025-10-15", "2025-10-16"],
      "place_votes": [1, 3, 5],
      "voted_at": "2025-10-01T09:30:00Z"
    }
  ]
}
```

### 2.3 과거 회식 이력 조회
**GET** `/chat/past-dinner-history/{month}`

**응답:**
```json
{
  "month": "2025-09",
  "dinner_info": {
    "place_name": "맛있는 한식당",
    "address": "서울시 강남구",
    "menu_type": "한식",
    "participants": 25,
    "date": "2025-09-15",
    "satisfaction_score": 4.2
  }
}
```

## 3. MCP 툴 통합

### 3.1 투표 데이터 조회 툴
```python
@mcp_tool
def get_vote_results(month: str) -> dict:
    """특정 월의 투표 결과 조회"""
    pass

@mcp_tool  
def get_user_vote_history(emp_no: str) -> dict:
    """사용자의 투표 이력 조회"""
    pass

@mcp_tool
def get_past_dinner_info(month: str) -> dict:
    """과거 회식 정보 조회"""
    pass
```

### 3.2 AI 응답 생성 툴
```python
@mcp_tool
def generate_vote_summary(vote_data: dict) -> str:
    """투표 결과 요약 생성"""
    pass

@mcp_tool
def generate_recommendation(user_preferences: dict) -> str:
    """개인화된 추천 생성"""
    pass
```

## 4. SSE 이벤트 확장

### 4.1 새로운 SSE 이벤트 타입
```typescript
interface SSEEvent {
  type: 'auto_vote_request' | 'vote_reminder' | 'vote_deadline' | 'conversational_response';
  data: any;
  timestamp: string;
}
```

### 4.2 자동 투표 요청 SSE 이벤트
```json
{
  "type": "auto_vote_request",
  "data": {
    "message": "이번 달 회식 투표를 시작합니다!",
    "deadline": "2025-10-07T23:59:59Z",
    "vote_url": "/chat?auto_vote=true"
  }
}
```

## 5. 프론트엔드 대화형 UI

### 5.1 채팅 인터페이스 확장
- 자연어 질문 입력
- AI 응답 표시
- 투표 결과 시각화
- 개인화된 추천

### 5.2 자동 투표 요청 UI
- 투표 요청 알림
- 투표 진행률 표시
- 마감일 카운트다운
- 원클릭 투표 버튼
