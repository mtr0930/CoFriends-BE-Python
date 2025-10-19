"""
Chat service layer for MongoDB chat message storage
"""
from typing import Any, Dict, List, Optional
from datetime import datetime
from pymongo.database import Database
from redis.asyncio import Redis

from app.core.constants import CHAT_KEY_PREFIX, CHAT_EXPIRATION_DAYS


class ChatService:
    """Chat service for handling chat messages"""
    
    def __init__(self, mongodb: Database, redis: Optional[Redis] = None):
        self.mongodb = mongodb
        self.redis = redis
        self.collection = mongodb["chat_sessions"]
    
    async def save_chat_messages(self, emp_no: str, messages: List[Dict[str, Any]]):
        """Save chat messages to MongoDB"""
        # Update or insert chat session
        self.collection.update_one(
            {"empNo": emp_no},
            {
                "$set": {
                    "messages": messages,
                    "updatedAt": datetime.now()
                },
                "$setOnInsert": {
                    "empNo": emp_no,
                    "createdAt": datetime.now()
                }
            },
            upsert=True
        )
        
        # Also save to Redis for fast access
        if self.redis:
            await self.save_to_redis(emp_no, messages)
    
    async def save_to_redis(self, emp_no: str, messages: List[Dict[str, Any]]):
        """Save chat messages to Redis cache"""
        if not self.redis:
            return
        
        import json
        key = f"{CHAT_KEY_PREFIX}{emp_no}"
        value = json.dumps(messages, ensure_ascii=False)
        await self.redis.setex(key, CHAT_EXPIRATION_DAYS * 86400, value)
    
    async def get_chat_messages(self, emp_no: str) -> List[Dict[str, Any]]:
        """Get chat messages from Redis first, then MongoDB"""
        # Try Redis first
        if self.redis:
            messages = await self.get_from_redis(emp_no)
            if messages is not None:
                return messages
        
        # Fall back to MongoDB
        session = self.collection.find_one({"empNo": emp_no})
        
        if session and "messages" in session:
            messages = session["messages"]
            # Update Redis cache
            if self.redis:
                await self.save_to_redis(emp_no, messages)
            return messages
        
        return []
    
    async def get_from_redis(self, emp_no: str) -> Optional[List[Dict[str, Any]]]:
        """Get chat messages from Redis"""
        if not self.redis:
            return None
        
        import json
        key = f"{CHAT_KEY_PREFIX}{emp_no}"
        value = await self.redis.get(key)
        
        if value:
            return json.loads(value)
        
        return None
    
    def delete_chat_messages(self, emp_no: str):
        """Delete chat messages for a user"""
        self.collection.delete_one({"empNo": emp_no})

