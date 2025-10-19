"""
채팅 이력 관리 서비스 - MongoDB 기반
World Best Practice 적용:
1. 세션 기반 대화 관리
2. 메시지 스트리밍 지원
3. 효율적인 인덱싱
4. 데이터 압축 및 아카이빙
"""
import asyncio
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, AsyncGenerator
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from pymongo import ASCENDING, DESCENDING
from bson import ObjectId
import json
import logging

from app.models.mongodb import ChatSession, ChatMessage, ChatHistory, CHAT_INDEXES
from app.core.config import settings

logger = logging.getLogger(__name__)


class ChatHistoryService:
    """채팅 이력 관리 서비스"""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None
        self.sessions_collection: Optional[AsyncIOMotorCollection] = None
        self.history_collection: Optional[AsyncIOMotorCollection] = None
    
    async def connect(self):
        """MongoDB 연결"""
        try:
            self.client = AsyncIOMotorClient(
                f"mongodb://{settings.MONGODB_HOST}:{settings.MONGODB_PORT}",
                username=settings.MONGODB_USERNAME,
                password=settings.MONGODB_PASSWORD,
                authSource=settings.MONGODB_AUTH_SOURCE
            )
            self.db = self.client[settings.MONGODB_DATABASE]
            
            # 컬렉션 초기화
            self.sessions_collection = self.db["chat_sessions"]
            self.history_collection = self.db["chat_history"]
            
            # 인덱스 생성
            await self._create_indexes()
            
            logger.info("✅ MongoDB 연결 성공")
            
        except Exception as e:
            logger.error(f"❌ MongoDB 연결 실패: {str(e)}")
            raise
    
    async def disconnect(self):
        """MongoDB 연결 해제"""
        if self.client:
            self.client.close()
            logger.info("MongoDB 연결 해제")
    
    async def _create_indexes(self):
        """인덱스 생성"""
        try:
            # 세션 컬렉션 인덱스
            await self.sessions_collection.create_index([("user_id", ASCENDING), ("created_at", DESCENDING)])
            await self.sessions_collection.create_index([("user_id", ASCENDING), ("is_active", ASCENDING)])
            await self.sessions_collection.create_index([("created_at", DESCENDING)])
            
            # 이력 컬렉션 인덱스
            await self.history_collection.create_index([("user_id", ASCENDING)])
            await self.history_collection.create_index([("last_activity", DESCENDING)])
            
            logger.info("✅ MongoDB 인덱스 생성 완료")
            
        except Exception as e:
            logger.error(f"❌ 인덱스 생성 실패: {str(e)}")
    
    async def create_session(self, user_id: str, session_name: Optional[str] = None) -> str:
        """새 채팅 세션 생성"""
        try:
            # 기존 활성 세션 비활성화
            await self.sessions_collection.update_many(
                {"user_id": user_id, "is_active": True},
                {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
            )
            
            # 새 세션 생성
            session = ChatSession(
                user_id=user_id,
                session_name=session_name or f"대화 {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                messages=[],
                is_active=True
            )
            
            result = await self.sessions_collection.insert_one(session.dict())
            session_id = str(result.inserted_id)
            
            # 사용자 이력 업데이트
            await self._update_user_history(user_id)
            
            logger.info(f"✅ 새 채팅 세션 생성: {session_id}")
            return session_id
            
        except Exception as e:
            logger.error(f"❌ 세션 생성 실패: {str(e)}")
            raise
    
    async def add_message(self, session_id: str, role: str, content: str, metadata: Optional[Dict] = None) -> str:
        """메시지 추가"""
        try:
            message = ChatMessage(
                role=role,
                content=content,
                timestamp=datetime.utcnow(),
                metadata=metadata or {}
            )
            
            # 세션에 메시지 추가
            await self.sessions_collection.update_one(
                {"_id": ObjectId(session_id)},
                {
                    "$push": {"messages": message.dict()},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
            
            # 사용자 이력 업데이트
            session = await self.get_session(session_id)
            if session:
                await self._update_user_history(session["user_id"])
            
            logger.info(f"✅ 메시지 추가: {session_id}")
            return message.id
            
        except Exception as e:
            logger.error(f"❌ 메시지 추가 실패: {str(e)}")
            raise
    
    async def get_session(self, session_id: str) -> Optional[Dict]:
        """세션 조회"""
        try:
            session = await self.sessions_collection.find_one({"_id": ObjectId(session_id)})
            if session:
                session["_id"] = str(session["_id"])
                return session
            return None
            
        except Exception as e:
            logger.error(f"❌ 세션 조회 실패: {str(e)}")
            return None
    
    async def get_active_session(self, user_id: str) -> Optional[Dict]:
        """사용자의 활성 세션 조회 (메시지 포함)"""
        try:
            session = await self.sessions_collection.find_one({
                "user_id": user_id,
                "is_active": True
            })
            
            if session:
                session["_id"] = str(session["_id"])
                session["id"] = str(session["_id"])  # id 필드도 추가
                
                # 메시지가 없으면 빈 배열로 초기화
                if "messages" not in session:
                    session["messages"] = []
                
                print(f"📚 세션 메시지 수: {len(session.get('messages', []))}")
                return session
            return None
            
        except Exception as e:
            logger.error(f"❌ 활성 세션 조회 실패: {str(e)}")
            return None
    
    async def get_user_sessions(self, user_id: str, limit: int = 20, offset: int = 0) -> List[Dict]:
        """사용자 세션 목록 조회"""
        try:
            cursor = self.sessions_collection.find(
                {"user_id": user_id}
            ).sort("created_at", DESCENDING).skip(offset).limit(limit)
            
            sessions = []
            async for session in cursor:
                session["_id"] = str(session["_id"])
                sessions.append(session)
            
            return sessions
            
        except Exception as e:
            logger.error(f"❌ 사용자 세션 조회 실패: {str(e)}")
            return []
    
    async def get_session_messages(self, session_id: str, limit: int = 50) -> List[Dict]:
        """세션 메시지 조회"""
        try:
            session = await self.sessions_collection.find_one(
                {"_id": ObjectId(session_id)},
                {"messages": {"$slice": -limit}}  # 최근 N개 메시지만
            )
            
            if session and "messages" in session:
                return session["messages"]
            return []
            
        except Exception as e:
            logger.error(f"❌ 세션 메시지 조회 실패: {str(e)}")
            return []
    
    async def stream_messages(self, session_id: str) -> AsyncGenerator[Dict, None]:
        """메시지 스트리밍 (실시간 대화용)"""
        try:
            # 최신 메시지부터 스트리밍
            last_timestamp = None
            
            while True:
                query = {"_id": ObjectId(session_id)}
                if last_timestamp:
                    query["messages.timestamp"] = {"$gt": last_timestamp}
                
                session = await self.sessions_collection.find_one(query)
                if not session or "messages" not in session:
                    await asyncio.sleep(0.1)
                    continue
                
                # 새로운 메시지만 필터링
                new_messages = []
                for msg in session["messages"]:
                    if not last_timestamp or msg["timestamp"] > last_timestamp:
                        new_messages.append(msg)
                        last_timestamp = msg["timestamp"]
                
                # 새 메시지 스트리밍
                for message in new_messages:
                    yield message
                
                await asyncio.sleep(0.1)
                
        except Exception as e:
            logger.error(f"❌ 메시지 스트리밍 실패: {str(e)}")
    
    async def archive_old_sessions(self, days: int = 30):
        """오래된 세션 아카이빙"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # 오래된 세션 비활성화
            result = await self.sessions_collection.update_many(
                {
                    "created_at": {"$lt": cutoff_date},
                    "is_active": True
                },
                {"$set": {"is_active": False}}
            )
            
            logger.info(f"✅ {result.modified_count}개 세션 아카이빙 완료")
            return result.modified_count
            
        except Exception as e:
            logger.error(f"❌ 세션 아카이빙 실패: {str(e)}")
            return 0
    
    async def _update_user_history(self, user_id: str):
        """사용자 이력 통계 업데이트"""
        try:
            # 사용자 세션 통계 계산
            total_sessions = await self.sessions_collection.count_documents({"user_id": user_id})
            
            # 총 메시지 수 계산
            pipeline = [
                {"$match": {"user_id": user_id}},
                {"$unwind": "$messages"},
                {"$count": "total_messages"}
            ]
            result = await self.sessions_collection.aggregate(pipeline).to_list(1)
            total_messages = result[0]["total_messages"] if result else 0
            
            # 마지막 활동 시간
            last_session = await self.sessions_collection.find_one(
                {"user_id": user_id},
                sort=[("updated_at", DESCENDING)]
            )
            last_activity = last_session["updated_at"] if last_session else None
            
            # 이력 업데이트 또는 생성
            await self.history_collection.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "total_sessions": total_sessions,
                        "total_messages": total_messages,
                        "last_activity": last_activity,
                        "updated_at": datetime.utcnow()
                    },
                    "$setOnInsert": {
                        "created_at": datetime.utcnow()
                    }
                },
                upsert=True
            )
            
        except Exception as e:
            logger.error(f"❌ 사용자 이력 업데이트 실패: {str(e)}")
    
    async def get_user_history(self, user_id: str) -> Optional[Dict]:
        """사용자 이력 조회"""
        try:
            history = await self.history_collection.find_one({"user_id": user_id})
            if history:
                history["_id"] = str(history["_id"])
            return history
            
        except Exception as e:
            logger.error(f"❌ 사용자 이력 조회 실패: {str(e)}")
            return None


# 전역 서비스 인스턴스
chat_history_service = ChatHistoryService()
