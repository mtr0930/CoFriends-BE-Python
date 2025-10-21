"""
Realtime Recommendation Service - 실시간 추천 시스템
"""
import asyncio
import json
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
import uuid

from app.services.hybrid_recommendation_service import HybridRecommendationService
from app.services.sse_manager import SSEManager

logger = logging.getLogger(__name__)

class RealtimeRecommendationService:
    """실시간 추천 서비스"""
    
    def __init__(self):
        self.hybrid_service = HybridRecommendationService()
        self.sse_manager = SSEManager()
        self.active_sessions = {}  # 사용자별 활성 세션
        self.recommendation_cache = {}  # 추천 캐시
        
        logger.info("RealtimeRecommendationService initialized")
    
    async def start_realtime_recommendations(self, user_id: str, channels: List[str] = None) -> str:
        """
        실시간 추천 시작
        
        Args:
            user_id: 사용자 ID
            channels: 구독할 채널 리스트
            
        Returns:
            세션 ID
        """
        try:
            # 세션 ID 생성
            session_id = str(uuid.uuid4())
            
            # 활성 세션 등록
            self.active_sessions[session_id] = {
                "user_id": user_id,
                "channels": channels or ["recommendations", "votes", "chat"],
                "started_at": datetime.now().isoformat(),
                "last_activity": datetime.now().isoformat()
            }
            
            # 초기 추천 생성
            await self._generate_initial_recommendations(user_id, session_id)
            
            # 실시간 업데이트 태스크 시작
            asyncio.create_task(self._realtime_update_loop(session_id))
            
            logger.info(f"Started realtime recommendations for user {user_id}, session {session_id}")
            return session_id
            
        except Exception as e:
            logger.error(f"Error starting realtime recommendations: {str(e)}")
            raise
    
    async def _generate_initial_recommendations(self, user_id: str, session_id: str):
        """초기 추천 생성"""
        try:
            # 하이브리드 추천 생성
            recommendations = self.hybrid_service.get_hybrid_recommendations(
                user_id=user_id,
                n_recommendations=5
            )
            
            # 추천 캐시에 저장
            self.recommendation_cache[session_id] = recommendations
            
            # SSE로 전송
            await self.sse_manager.send_to_session(
                session_id,
                {
                    "type": "initial_recommendations",
                    "data": {
                        "recommendations": recommendations,
                        "user_id": user_id,
                        "generated_at": datetime.now().isoformat()
                    }
                }
            )
            
            logger.info(f"Generated initial recommendations for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error generating initial recommendations: {str(e)}")
    
    async def _realtime_update_loop(self, session_id: str):
        """실시간 업데이트 루프"""
        try:
            while session_id in self.active_sessions:
                # 세션 정보 가져오기
                session_info = self.active_sessions[session_id]
                user_id = session_info["user_id"]
                
                # 새로운 투표나 활동이 있는지 확인
                has_new_activity = await self._check_new_activity(user_id)
                
                if has_new_activity:
                    # 추천 업데이트
                    await self._update_recommendations(user_id, session_id)
                
                # 30초 대기
                await asyncio.sleep(30)
                
        except Exception as e:
            logger.error(f"Error in realtime update loop: {str(e)}")
        finally:
            # 세션 정리
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
            if session_id in self.recommendation_cache:
                del self.recommendation_cache[session_id]
    
    async def _check_new_activity(self, user_id: str) -> bool:
        """새로운 활동 확인"""
        try:
            # 실제 구현에서는 데이터베이스에서 최근 활동 확인
            # 여기서는 간단히 랜덤하게 반환
            import random
            return random.random() < 0.1  # 10% 확률로 새로운 활동
            
        except Exception as e:
            logger.error(f"Error checking new activity: {str(e)}")
            return False
    
    async def _update_recommendations(self, user_id: str, session_id: str):
        """추천 업데이트"""
        try:
            # 새로운 추천 생성
            recommendations = self.hybrid_service.get_hybrid_recommendations(
                user_id=user_id,
                n_recommendations=5
            )
            
            # 추천 캐시 업데이트
            self.recommendation_cache[session_id] = recommendations
            
            # SSE로 업데이트 전송
            await self.sse_manager.send_to_session(
                session_id,
                {
                    "type": "recommendation_update",
                    "data": {
                        "recommendations": recommendations,
                        "user_id": user_id,
                        "updated_at": datetime.now().isoformat()
                    }
                }
            )
            
            logger.info(f"Updated recommendations for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error updating recommendations: {str(e)}")
    
    async def handle_vote_event(self, user_id: str, vote_data: Dict[str, Any]):
        """투표 이벤트 처리"""
        try:
            # 사용자 선호도 업데이트
            self.hybrid_service.update_user_preferences(user_id, vote_data)
            
            # 해당 사용자의 활성 세션 찾기
            active_sessions = [
                session_id for session_id, info in self.active_sessions.items()
                if info["user_id"] == user_id
            ]
            
            # 모든 활성 세션에 투표 이벤트 전송
            for session_id in active_sessions:
                await self.sse_manager.send_to_session(
                    session_id,
                    {
                        "type": "vote_event",
                        "data": {
                            "user_id": user_id,
                            "vote_data": vote_data,
                            "timestamp": datetime.now().isoformat()
                        }
                    }
                )
                
                # 추천 업데이트
                await self._update_recommendations(user_id, session_id)
            
            logger.info(f"Handled vote event for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error handling vote event: {str(e)}")
    
    async def handle_chat_event(self, user_id: str, chat_data: Dict[str, Any]):
        """채팅 이벤트 처리"""
        try:
            # 채팅 내용에서 추천 힌트 추출
            chat_text = chat_data.get("message", "")
            if self._contains_recommendation_hint(chat_text):
                # 추천 요청으로 처리
                await self._handle_recommendation_request(user_id, chat_text)
            
            # 해당 사용자의 활성 세션에 채팅 이벤트 전송
            active_sessions = [
                session_id for session_id, info in self.active_sessions.items()
                if info["user_id"] == user_id
            ]
            
            for session_id in active_sessions:
                await self.sse_manager.send_to_session(
                    session_id,
                    {
                        "type": "chat_event",
                        "data": {
                            "user_id": user_id,
                            "chat_data": chat_data,
                            "timestamp": datetime.now().isoformat()
                        }
                    }
                )
            
            logger.info(f"Handled chat event for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error handling chat event: {str(e)}")
    
    def _contains_recommendation_hint(self, text: str) -> bool:
        """추천 힌트 포함 여부 확인"""
        recommendation_keywords = [
            "추천", "recommend", "좋은", "맛있는", "어디", "식당", "음식"
        ]
        
        return any(keyword in text.lower() for keyword in recommendation_keywords)
    
    async def _handle_recommendation_request(self, user_id: str, chat_text: str):
        """추천 요청 처리"""
        try:
            # 채팅 내용 기반 추천 생성
            recommendations = self.hybrid_service.get_hybrid_recommendations(
                user_id=user_id,
                query_text=chat_text,
                n_recommendations=3
            )
            
            # 활성 세션에 추천 전송
            active_sessions = [
                session_id for session_id, info in self.active_sessions.items()
                if info["user_id"] == user_id
            ]
            
            for session_id in active_sessions:
                await self.sse_manager.send_to_session(
                    session_id,
                    {
                        "type": "chat_based_recommendation",
                        "data": {
                            "user_id": user_id,
                            "chat_text": chat_text,
                            "recommendations": recommendations,
                            "generated_at": datetime.now().isoformat()
                        }
                    }
                )
            
            logger.info(f"Handled recommendation request for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error handling recommendation request: {str(e)}")
    
    async def stop_realtime_recommendations(self, session_id: str):
        """실시간 추천 중지"""
        try:
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
            
            if session_id in self.recommendation_cache:
                del self.recommendation_cache[session_id]
            
            logger.info(f"Stopped realtime recommendations for session {session_id}")
            
        except Exception as e:
            logger.error(f"Error stopping realtime recommendations: {str(e)}")
    
    def get_active_sessions(self) -> Dict[str, Any]:
        """활성 세션 정보 조회"""
        return {
            "active_sessions": len(self.active_sessions),
            "sessions": list(self.active_sessions.keys()),
            "timestamp": datetime.now().isoformat()
        }
    
    def get_recommendation_cache(self, session_id: str) -> Optional[List[Dict[str, Any]]]:
        """추천 캐시 조회"""
        return self.recommendation_cache.get(session_id)
