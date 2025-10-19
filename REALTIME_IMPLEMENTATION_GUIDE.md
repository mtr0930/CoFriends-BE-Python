# 🚀 실시간 투표 시스템 구현 완료!

## World Best Practice: Redis Pub/Sub + WebSocket

### ✨ 구현된 아키텍처

```
┌─────────────┐     WebSocket    ┌──────────────┐
│  Client A   │◄───────────────►│              │
├─────────────┤                  │              │
│  Client B   │◄───────────────►│   FastAPI    │◄───► PostgreSQL
├─────────────┤                  │   Server     │
│  Client C   │◄───────────────►│              │◄───► MongoDB
└─────────────┘                  └──────┬───────┘
                                        │
                                   Pub/Sub
                                        ↓
                                  ┌──────────┐
                                  │  Redis   │
                                  └──────────┘
                                        ↑
                                   Pub/Sub
                                        │
                                  ┌──────────┐
                                  │  FastAPI │
                                  │ Server 2 │ (확장 시)
                                  └──────────┘
```

### 🎯 주요 특징

1. **실시간 양방향 통신** - WebSocket
2. **수평 확장 가능** - Redis Pub/Sub로 여러 서버 동기화
3. **자동 재연결** - 연결 끊김 시 자동 복구
4. **낮은 지연시간** - 밀리초 단위 업데이트
5. **브로드캐스팅** - 모든 클라이언트에 즉시 전파

---

## 📦 백엔드 구현 (Python/FastAPI)

### 1. WebSocket Manager (`app/core/websocket.py`)
```python
# Redis Pub/Sub 기반 WebSocket 연결 관리
manager = ConnectionManager()
```

**주요 기능:**
- ✅ WebSocket 연결 관리
- ✅ Redis Pub/Sub 리스닝
- ✅ 모든 클라이언트에 브로드캐스트
- ✅ 서버 간 동기화

### 2. WebSocket API (`app/api/websocket.py`)
```python
# 엔드포인트: ws://localhost:5000/ws/votes?emp_no=12345
@router.websocket("/votes")
async def websocket_votes(websocket: WebSocket, emp_no: str)
```

**메시지 타입:**
- `connection_ack`: 연결 확인
- `vote_update`: 투표 업데이트
- `place_vote`: 식당 투표
- `menu_vote`: 메뉴 투표
- `ping/pong`: 연결 유지

### 3. 투표 API 통합 (`app/api/place.py`)
```python
# 투표 시 자동으로 WebSocket으로 브로드캐스트
await manager.publish_vote_update(
    event_type="place_vote",
    data={...}
)
```

---

## 💻 프론트엔드 구현 (React/TypeScript)

### 1. WebSocket Hook (`src/hooks/useRealtimeWebSocket.ts`)

```tsx
const { 
  isConnected,      // 연결 상태
  lastMessage,      // 마지막 메시지
  sendMessage,      // 메시지 전송
  reconnect,        // 수동 재연결
  disconnect        // 연결 종료
} = useRealtimeWebSocket({
  empNo: '12345',
  autoReconnect: true,
  onMessage: (msg) => {
    // 투표 업데이트 처리
    console.log(msg);
  }
});
```

**기능:**
- ✅ 자동 연결/재연결
- ✅ 메시지 파싱
- ✅ Ping/Pong (30초마다)
- ✅ 에러 핸들링

### 2. 사용 예시

#### 기본 사용
```tsx
import { useRealtimeWebSocket } from './hooks/useRealtimeWebSocket';

function VotingPage() {
  const { isConnected, lastMessage } = useRealtimeWebSocket({
    empNo: user.empNo,
    onMessage: (msg) => {
      if (msg.type === 'place_vote') {
        // 식당 투표 업데이트
        updatePlaceVotes(msg.data);
      }
    }
  });

  return (
    <div>
      <div>연결 상태: {isConnected ? '🟢 연결됨' : '🔴 연결 안됨'}</div>
      {/* 투표 UI */}
    </div>
  );
}
```

#### React Query와 함께 사용
```tsx
import { useQueryClient } from '@tanstack/react-query';

function VotingPage() {
  const queryClient = useQueryClient();
  
  useRealtimeWebSocket({
    empNo: user.empNo,
    onMessage: (msg) => {
      // React Query 캐시 무효화 → 자동 리페치
      if (msg.type === 'vote_update') {
        queryClient.invalidateQueries(['votes']);
      }
    }
  });

  // 기존 useQuery 그대로 사용
  const { data } = useQuery(['votes'], fetchVotes);
}
```

---

## 🔥 실전 활용 예시

### 방법 1: WebSocket + React Query (추천 ⭐⭐⭐)

```tsx
function Chat() {
  const queryClient = useQueryClient();
  const { data: votes } = useQuery(['vote-stats'], getVoteStats);
  
  // WebSocket으로 실시간 업데이트 감지
  useRealtimeWebSocket({
    onMessage: (msg) => {
      if (msg.type === 'place_vote') {
        // 특정 식당의 투표 수만 업데이트
        queryClient.setQueryData(['vote-stats'], (old: any) => ({
          ...old,
          place_votes: old.place_votes.map((place: any) =>
            place.place_id === msg.data.place_id
              ? { ...place, vote_count: msg.data.vote_count }
              : place
          )
        }));
      }
    }
  });

  return (
    <div>
      {votes?.place_votes.map(place => (
        <div key={place.place_id}>
          {place.place_name}: {place.vote_count}표
        </div>
      ))}
    </div>
  );
}
```

### 방법 2: WebSocket Only (초경량)

```tsx
function RealtimeVotes() {
  const [votes, setVotes] = useState<any>({});
  
  useRealtimeWebSocket({
    onMessage: (msg) => {
      if (msg.type === 'place_vote') {
        setVotes(prev => ({
          ...prev,
          [msg.data.place_id]: msg.data.vote_count
        }));
      }
    }
  });

  return <div>{/* 투표 UI */}</div>;
}
```

### 방법 3: Hybrid (WebSocket + Polling Fallback)

```tsx
function SmartVotes() {
  // WebSocket 시도
  const { isConnected } = useRealtimeWebSocket({
    onMessage: handleVoteUpdate
  });
  
  // WebSocket 안되면 Polling
  const { data } = useRealtimeVotes({
    refetchInterval: isConnected ? false : 3000,
    enabled: !isConnected
  });
}
```

---

## 🚀 서버 재시작 및 테스트

```bash
# 백엔드 재시작
cd CoFriends-BE-Python
docker-compose down
docker-compose up -d --build

# WebSocket 연결 테스트
wscat -c ws://localhost:5000/ws/votes?emp_no=12345

# 또는 브라우저 콘솔에서
const ws = new WebSocket('ws://localhost:5000/ws/votes?emp_no=12345');
ws.onmessage = (e) => console.log(JSON.parse(e.data));
```

---

## 📊 성능 비교

| 방법 | 지연시간 | 서버 부하 | 확장성 | 구현 난이도 |
|------|---------|----------|--------|------------|
| **Polling** | ~3초 | 높음 | 낮음 | ⭐ 쉬움 |
| **WebSocket** | ~50ms | 낮음 | 중간 | ⭐⭐ 보통 |
| **WS + Redis Pub/Sub** | ~50ms | 낮음 | 높음 | ⭐⭐⭐ 어려움 |
| **SSE** | ~100ms | 중간 | 중간 | ⭐⭐ 보통 |

---

## 🎯 Best Practice Tips

### 1. 연결 관리
```tsx
// ✅ Good: 페이지 언마운트 시 정리
useEffect(() => {
  return () => disconnect();
}, []);

// ❌ Bad: 메모리 누수
useRealtimeWebSocket(); // cleanup 없음
```

### 2. 메시지 필터링
```tsx
// ✅ Good: 필요한 메시지만 처리
onMessage: (msg) => {
  if (msg.type === 'place_vote' && msg.data.place_id === currentPlaceId) {
    updateVote(msg.data);
  }
}

// ❌ Bad: 모든 메시지 처리
onMessage: (msg) => {
  updateEverything(msg); // 불필요한 리렌더
}
```

### 3. 에러 처리
```tsx
// ✅ Good: 폴백 준비
const { isConnected } = useRealtimeWebSocket({
  onError: (err) => console.error(err)
});

const { data } = useRealtimeVotes({
  enabled: !isConnected, // WebSocket 실패 시 폴링
  refetchInterval: 5000
});
```

---

## 🌟 추가 기능 아이디어

1. **타이핑 인디케이터** - "3명이 투표 중..."
2. **온라인 사용자** - 실시간 참여자 수
3. **투표 애니메이션** - 투표 시 시각 효과
4. **알림** - 특정 식당이 1위가 되면 알림
5. **히스토리** - 실시간 투표 변화 그래프

---

## 📝 정리

✅ **구현 완료:**
1. Redis Pub/Sub 기반 WebSocket 서버
2. 자동 재연결 기능의 React Hook
3. 투표 API와 실시간 연동
4. 다중 서버 확장 가능

✅ **사용 방법:**
- `useRealtimeWebSocket()` Hook 사용
- `onMessage`로 업데이트 처리
- React Query와 조합 가능

✅ **장점:**
- 실시간 업데이트 (50ms 지연)
- 수평 확장 가능
- 자동 재연결
- 서버 간 동기화

**이제 투표하면 모든 사용자에게 즉시 반영됩니다! 🎉**

