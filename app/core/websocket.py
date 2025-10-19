"""
WebSocket manager for real-time vote updates
Redis Pub/Sub 기반 실시간 투표 시스템
"""
import json
import asyncio
from typing import Dict, Set
from fastapi import WebSocket, WebSocketDisconnect
import redis.asyncio as aioredis
from datetime import datetime

from app.core.config import settings


class ConnectionManager:
    """WebSocket 연결 관리자"""
    
    def __init__(self):
        # 활성 WebSocket 연결들
        self.active_connections: Set[WebSocket] = set()
        # Redis Pub/Sub 클라이언트
        self.redis: aioredis.Redis = None
        self.pubsub = None
        # 투표 채널
        self.VOTE_CHANNEL = "vote_updates"
        
    async def initialize(self):
        """Redis 연결 초기화"""
        if not self.redis:
            self.redis = await aioredis.from_url(
                f"redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}",
                encoding="utf-8",
                decode_responses=True
            )
            self.pubsub = self.redis.pubsub()
            await self.pubsub.subscribe(self.VOTE_CHANNEL)
            # 백그라운드에서 메시지 리스닝 시작
            asyncio.create_task(self._listen_to_redis())
    
    async def connect(self, websocket: WebSocket):
        """새 WebSocket 연결 추가"""
        await websocket.accept()
        self.active_connections.add(websocket)
        print(f"✅ WebSocket connected. Total: {len(self.active_connections)}")
        
    def disconnect(self, websocket: WebSocket):
        """WebSocket 연결 제거"""
        self.active_connections.discard(websocket)
        print(f"❌ WebSocket disconnected. Total: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict):
        """모든 연결된 클라이언트에게 메시지 전송"""
        disconnected = set()
        
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"Error sending to client: {e}")
                disconnected.add(connection)
        
        # 연결 끊긴 클라이언트 제거
        for conn in disconnected:
            self.disconnect(conn)
    
    async def publish_vote_update(self, event_type: str, data: dict):
        """
        Redis Pub/Sub로 투표 업데이트 발행
        다른 서버 인스턴스들과 동기화
        """
        if not self.redis:
            await self.initialize()
        
        message = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        
        await self.redis.publish(
            self.VOTE_CHANNEL,
            json.dumps(message)
        )
        print(f"📢 Published to Redis: {event_type}")
    
    async def _listen_to_redis(self):
        """Redis Pub/Sub 메시지 리스닝 (백그라운드)"""
        print("🎧 Listening to Redis Pub/Sub...")
        
        try:
            async for message in self.pubsub.listen():
                if message["type"] == "message":
                    data = json.loads(message["data"])
                    # 모든 WebSocket 클라이언트에게 브로드캐스트
                    await self.broadcast(data)
        except Exception as e:
            print(f"Redis listener error: {e}")
    
    async def cleanup(self):
        """리소스 정리"""
        if self.pubsub:
            await self.pubsub.unsubscribe(self.VOTE_CHANNEL)
            await self.pubsub.close()
        if self.redis:
            await self.redis.close()


# 전역 ConnectionManager 인스턴스
manager = ConnectionManager()

