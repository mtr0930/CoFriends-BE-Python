# Hybrid AI Recommendation System Architecture

## 🎯 시스템 개요

회식 투표/댓글 데이터를 기반으로 개인화된 추천을 제공하고, LightRAG을 이용해 "추천 이유"를 자연어로 설명하는 Hybrid Recommendation System입니다.

## 🏗️ 아키텍처 다이어그램

```
[User → Web/Slack Chatbot]
        ↓
[FastAPI SSE Backend]
 ├─ 투표/댓글 이벤트 수집
 ├─ 실시간 추천 스트림 (SSE)
 └─ Slack OAuth 연동
        ↓
[Hybrid Recommendation Engine]
 ├─ Collaborative Filtering (행동 기반)
 ├─ Text Embedding Similarity (의미 기반)
 └─ LightRAG Explanation (추천 근거 생성)
        ↓
[Data Layer]
 ├─ PostgreSQL (투표/댓글/메뉴 메타)
 ├─ Redis (실시간 캐시)
 ├─ Chroma DB (임베딩 저장)
 └─ Neo4j (LightRAG 관계 그래프)
```

## 🧠 핵심 구성 요소

### 1️⃣ 협업 필터링 (Collaborative Filtering)

**목적**: 사용자의 투표/선호도를 기반으로 유사 사용자 그룹을 계산

**구현**:
- **User-Item Matrix**: 사용자-아이템 매트릭스 구축
- **Similarity Calculation**: 코사인 유사도, 피어슨 상관계수
- **Implicit Feedback**: Implicit 라이브러리 사용
- **Hybrid Approach**: 사용자 기반 + 아이템 기반 + Implicit

**코드 예시**:
```python
# 사용자-아이템 매트릭스 구축
user_item_matrix = votes.pivot_table(
    index="user_id", 
    columns="item_id", 
    values="rating", 
    fill_value=0
)

# 유사도 계산
similarity_matrix = cosine_similarity(user_item_matrix)

# Implicit 모델 훈련
model = implicit.als.AlternatingLeastSquares(factors=50)
model.fit(csr_matrix(user_item_matrix.values))
```

### 2️⃣ 임베딩 기반 추천 (Embedding-based Similarity)

**목적**: 댓글/설명문 임베딩 후, 의미적 유사도 기반으로 추천

**구현**:
- **Embedding Model**: `jhgan/ko-sroberta-multitask` (한국어 지원)
- **Vector Store**: Chroma DB
- **Similarity Search**: 벡터 유사도 검색
- **Personalization**: 사용자별 선호도 분석

**코드 예시**:
```python
# 임베딩 모델 초기화
model = SentenceTransformer('jhgan/ko-sroberta-multitask')

# 벡터 변환
embedding = model.encode(text_content).tolist()

# Chroma DB 저장
collection.add(
    embeddings=[embedding],
    documents=[text_content],
    metadatas=[metadata],
    ids=[doc_id]
)
```

### 3️⃣ LightRAG Explanation Layer

**목적**: 메뉴, 분위기, 지역 등 엔티티 간 관계를 그래프로 구축하여 추천 이유 생성

**구현**:
- **Graph Database**: Neo4j
- **Entity Relationships**: 사용자-식당-메뉴타입 관계
- **LLM Integration**: GPT-4o-mini를 통한 설명 생성
- **Context Retrieval**: 관계 기반 컨텍스트 검색

**코드 예시**:
```python
# 관계 그래프 구축
CREATE (u:User {id: $user_id})
CREATE (r:Restaurant {id: $place_id})
CREATE (m:MenuType {name: $menu_type})
CREATE (u)-[:VOTED {action: $action}]->(r)
CREATE (r)-[:SERVES]->(m)

# LLM을 통한 설명 생성
prompt = f"사용자 투표 이력: {user_history}\n추천 아이템: {item_info}"
explanation = llm.invoke(prompt)
```

## 📊 데이터 모델

### PostgreSQL Tables
| Table | 주요 컬럼 | 설명 |
|-------|-----------|------|
| votes | user_id, menu_id, vote, timestamp | 투표 내역 |
| comments | user_id, menu_id, content, sentiment | 댓글 내용 |
| menus | menu_id, category, location, embedding | 메뉴 메타데이터 |

### Chroma DB Collections
| Collection | 설명 | 임베딩 차원 |
|------------|------|-------------|
| user_votes | 사용자 투표 임베딩 | 768 |
| restaurants | 식당 정보 임베딩 | 768 |

### Neo4j Graph
| Node Type | Properties | Relationships |
|-----------|------------|---------------|
| User | id, name, created_at | -[:VOTED]-> Restaurant |
| Restaurant | id, name, menu_type | -[:SERVES]-> MenuType |
| MenuType | name, category | -[:SIMILAR_TO]-> MenuType |

## 🧩 기술 스택

### 계층별 기술
| 계층 | 기술 | 설명 |
|------|------|------|
| Frontend | React (Vite) + SSE | 실시간 투표 결과 표시 |
| Backend | FastAPI + Uvicorn | SSE, 추천 API, Slack OAuth |
| Database | PostgreSQL + Redis | 영속 데이터 + 캐시 |
| Vector DB | Chroma DB | 임베딩 검색 |
| Graph DB | Neo4j | LightRAG용 관계 저장 |
| LLM | GPT-4o-mini / Claude-3.5-Sonnet | 추천 이유 생성 |
| Infra | Docker + Nginx + EKS | SSL, Load Balancing, CronJobs |

## 🚀 API 엔드포인트

### 하이브리드 추천 API
```
POST /api/hybrid/recommendations
GET  /api/hybrid/explanation/{user_id}/{item_id}
GET  /api/hybrid/similar-users/{user_id}
GET  /api/hybrid/performance-metrics
POST /api/hybrid/update-preferences/{user_id}
GET  /api/hybrid/health
POST /api/hybrid/initialize-models
```

### 개인화 추천 API
```
POST /api/personalized/recommendations
POST /api/personalized/vote-embedding
POST /api/personalized/restaurant-embedding
GET  /api/personalized/user-history/{emp_no}
GET  /api/personalized/similar-votes/{emp_no}
GET  /api/personalized/similar-restaurants
```

## 🔄 추천 알고리즘

### 1. 하이브리드 추천 생성
```python
def get_hybrid_recommendations(user_id, query_text=None, n_recommendations=10):
    # 1. 협업 필터링 추천 (가중치: 0.6)
    cf_recs = collaborative_filtering.get_recommendations(user_id)
    
    # 2. 벡터 기반 추천 (가중치: 0.4)
    vector_recs = vector_service.get_personalized_recommendations(user_id, query_text)
    
    # 3. 추천 통합 및 점수 계산
    combined = combine_recommendations(cf_recs, vector_recs)
    
    # 4. LightRAG 설명 생성
    for rec in combined:
        context = lightrag.get_recommendation_context(user_id, rec.item_id)
        rec.explanation = lightrag.generate_explanation(user_id, rec.item_id, context)
    
    return combined
```

### 2. 개인화 점수 계산
```python
def calculate_personalization_score(restaurant, user_votes, user_preferences):
    score = 0.0
    
    # 메뉴 타입 매칭 (30%)
    if restaurant.menu_type in user_preferences.favorite_menu_types:
        score += user_preferences.favorite_menu_types[restaurant.menu_type] * 0.3
    
    # 장소 매칭 (50%)
    if restaurant.name in user_preferences.favorite_places:
        score += user_preferences.favorite_places[restaurant.name] * 0.5
    
    # 거리 기반 (20%)
    distance = restaurant.similarity_distance
    score += (1.0 - distance) * 0.2
    
    return min(score, 1.0)
```

## 🎯 설계 철학 (World Best Practice)

| 항목 | 적용 원리 | 구현 방법 |
|------|-----------|-----------|
| **추천 정확도** | Collaborative Filtering + Embedding Hybrid | 가중치 기반 추천 통합 |
| **추천 이유 설명** | LightRAG + LLM으로 관계 기반 문맥 설명 | Neo4j 그래프 + GPT-4o-mini |
| **실시간 반응성** | SSE 기반 스트림 업데이트 | FastAPI SSE + Redis |
| **유지보수성** | DB / Vector / Graph Layer 분리 | 마이크로서비스 아키텍처 |
| **비용 효율성** | Graph는 optional, core는 CF + Embedding | 단계적 확장 가능 |

## 🔧 설정 및 배포

### 환경 변수
```env
# Neo4j 설정
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# OpenAI 설정
OPENAI_API_KEY=your_openai_api_key

# Chroma DB 설정
CHROMA_PERSIST_DIRECTORY=./chroma_db
```

### Docker Compose
```yaml
version: '3.8'
services:
  neo4j:
    image: neo4j:5.0
    environment:
      NEO4J_AUTH: neo4j/password
    ports:
      - "7687:7687"
      - "7474:7474"
  
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: cofriends
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: 1234
    ports:
      - "5432:5432"
  
  redis:
    image: redis:7
    ports:
      - "6379:6379"
```

## 📈 성능 최적화

### 1. 캐싱 전략
- **Redis**: 실시간 추천 결과 캐싱
- **Chroma DB**: 임베딩 벡터 캐싱
- **Neo4j**: 그래프 쿼리 결과 캐싱

### 2. 배치 처리
- **일일 추천 업데이트**: 새벽 2시 배치 작업
- **모델 재훈련**: 주간 단위 모델 업데이트
- **그래프 동기화**: 실시간 투표 시 그래프 업데이트

### 3. 모니터링
- **추천 정확도**: A/B 테스트를 통한 성능 측정
- **응답 시간**: API 응답 시간 모니터링
- **사용자 만족도**: 추천 클릭률, 만족도 조사

## 🚀 향후 확장 계획

### 1. 고급 기능
- **딥러닝 모델**: TensorFlow/PyTorch 기반 추천 모델
- **실시간 학습**: 온라인 학습을 통한 모델 업데이트
- **다중 모달**: 이미지, 텍스트, 음성 통합 추천

### 2. 확장성
- **마이크로서비스**: 추천 엔진 독립 서비스화
- **Kubernetes**: 컨테이너 오케스트레이션
- **MLOps**: 모델 배포 및 관리 자동화

### 3. 사용자 경험
- **개인화 대시보드**: 사용자별 추천 히스토리
- **설명 가능한 AI**: 추천 이유 시각화
- **소셜 추천**: 친구/동료 기반 추천

---

## 📚 참고 자료

- [Collaborative Filtering with Implicit Feedback](https://implicit.readthedocs.io/)
- [Chroma DB Documentation](https://docs.trychroma.com/)
- [Neo4j Graph Database](https://neo4j.com/docs/)
- [LangChain Documentation](https://python.langchain.com/)
- [FastAPI SSE Implementation](https://fastapi.tiangolo.com/advanced/server-sent-events/)
