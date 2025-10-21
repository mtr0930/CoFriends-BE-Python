"""
SSE Manager - Server-Sent Events 관리 서비스
"""
import asyncio
import json
import logging
from typing import Dict, Any, Set, Optional
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

class SSEManager:
    """SSE 연결 관리자"""
    
    def __init__(self):
        self.connections: Dict[str, Dict[str, Any]] = {}
        self.channels: Dict[str, Set[str]] = {}  # channel -> set of client_ids
        self.client_channels: Dict[str, Set[str]] = {}  # client_id -> set of channels
        
        logger.info("SSEManager initialized")
    
    async def add_connection(self, client_id: str, channels: list = None) -> str:
        """
        SSE 연결 추가
        
        Args:
            client_id: 클라이언트 ID
            channels: 구독할 채널 리스트
            
        Returns:
            연결 ID
        """
        try:
            if channels is None:
                channels = ["default"]
            
            # 연결 정보 저장
            self.connections[client_id] = {
                "client_id": client_id,
                "channels": set(channels),
                "connected_at": datetime.now().isoformat(),
                "last_activity": datetime.now().isoformat()
            }
            
            # 채널별 클라이언트 등록
            for channel in channels:
                if channel not in self.channels:
                    self.channels[channel] = set()
                self.channels[channel].add(client_id)
            
            # 클라이언트별 채널 등록
            self.client_channels[client_id] = set(channels)
            
            logger.info(f"Added SSE connection: {client_id} to channels: {channels}")
            return client_id
            
        except Exception as e:
            logger.error(f"Error adding SSE connection: {str(e)}")
            raise
    
    async def remove_connection(self, client_id: str):
        """
        SSE 연결 제거
        
        Args:
            client_id: 클라이언트 ID
        """
        try:
            if client_id in self.connections:
                # 채널에서 클라이언트 제거
                channels = self.connections[client_id].get("channels", set())
                for channel in channels:
                    if channel in self.channels:
                        self.channels[channel].discard(client_id)
                
                # 연결 정보 제거
                del self.connections[client_id]
                
                if client_id in self.client_channels:
                    del self.client_channels[client_id]
                
                logger.info(f"Removed SSE connection: {client_id}")
            
        except Exception as e:
            logger.error(f"Error removing SSE connection: {str(e)}")
    
    async def send_to_client(self, client_id: str, data: Dict[str, Any]) -> bool:
        """
        특정 클라이언트에게 메시지 전송
        
        Args:
            client_id: 클라이언트 ID
            data: 전송할 데이터
            
        Returns:
            전송 성공 여부
        """
        try:
            if client_id not in self.connections:
                logger.warning(f"Client {client_id} not found")
                return False
            
            # 실제 구현에서는 WebSocket이나 SSE 스트림으로 전송
            # 여기서는 로깅만 수행
            logger.info(f"Sent to client {client_id}: {data}")
            
            # 연결 활동 시간 업데이트
            self.connections[client_id]["last_activity"] = datetime.now().isoformat()
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending to client {client_id}: {str(e)}")
            return False
    
    async def send_to_channel(self, channel: str, data: Dict[str, Any]) -> int:
        """
        특정 채널의 모든 클라이언트에게 메시지 전송
        
        Args:
            channel: 채널명
            data: 전송할 데이터
            
        Returns:
            전송된 클라이언트 수
        """
        try:
            if channel not in self.channels:
                logger.warning(f"Channel {channel} not found")
                return 0
            
            sent_count = 0
            for client_id in self.channels[channel]:
                if await self.send_to_client(client_id, data):
                    sent_count += 1
            
            logger.info(f"Sent to channel {channel}: {sent_count} clients")
            return sent_count
            
        except Exception as e:
            logger.error(f"Error sending to channel {channel}: {str(e)}")
            return 0
    
    async def send_to_session(self, session_id: str, data: Dict[str, Any]) -> bool:
        """
        세션 ID로 메시지 전송 (클라이언트 ID와 동일)
        
        Args:
            session_id: 세션 ID
            data: 전송할 데이터
            
        Returns:
            전송 성공 여부
        """
        return await self.send_to_client(session_id, data)
    
    async def broadcast(self, data: Dict[str, Any]) -> int:
        """
        모든 연결된 클라이언트에게 브로드캐스트
        
        Args:
            data: 전송할 데이터
            
        Returns:
            전송된 클라이언트 수
        """
        try:
            sent_count = 0
            for client_id in self.connections:
                if await self.send_to_client(client_id, data):
                    sent_count += 1
            
            logger.info(f"Broadcasted to {sent_count} clients")
            return sent_count
            
        except Exception as e:
            logger.error(f"Error broadcasting: {str(e)}")
            return 0
    
    def get_connection_info(self, client_id: str) -> Optional[Dict[str, Any]]:
        """
        클라이언트 연결 정보 조회
        
        Args:
            client_id: 클라이언트 ID
            
        Returns:
            연결 정보 또는 None
        """
        return self.connections.get(client_id)
    
    def get_all_connections(self) -> Dict[str, Dict[str, Any]]:
        """
        모든 연결 정보 조회
        
        Returns:
            모든 연결 정보
        """
        return self.connections.copy()
    
    def get_channel_clients(self, channel: str) -> Set[str]:
        """
        특정 채널의 클라이언트 목록 조회
        
        Args:
            channel: 채널명
            
        Returns:
            클라이언트 ID 집합
        """
        return self.channels.get(channel, set()).copy()
    
    def get_client_channels(self, client_id: str) -> Set[str]:
        """
        특정 클라이언트의 채널 목록 조회
        
        Args:
            client_id: 클라이언트 ID
            
        Returns:
            채널명 집합
        """
        return self.client_channels.get(client_id, set()).copy()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        SSE 매니저 통계 정보 조회
        
        Returns:
            통계 정보
        """
        try:
            total_connections = len(self.connections)
            total_channels = len(self.channels)
            
            # 채널별 클라이언트 수
            channel_stats = {}
            for channel, clients in self.channels.items():
                channel_stats[channel] = len(clients)
            
            # 클라이언트별 채널 수
            client_stats = {}
            for client_id, channels in self.client_channels.items():
                client_stats[client_id] = len(channels)
            
            return {
                "total_connections": total_connections,
                "total_channels": total_channels,
                "channel_stats": channel_stats,
                "client_stats": client_stats,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting stats: {str(e)}")
            return {"error": str(e)}
    
    async def cleanup_inactive_connections(self, timeout_minutes: int = 30):
        """
        비활성 연결 정리
        
        Args:
            timeout_minutes: 타임아웃 시간 (분)
        """
        try:
            current_time = datetime.now()
            inactive_clients = []
            
            for client_id, connection_info in self.connections.items():
                last_activity = datetime.fromisoformat(connection_info["last_activity"])
                time_diff = (current_time - last_activity).total_seconds() / 60
                
                if time_diff > timeout_minutes:
                    inactive_clients.append(client_id)
            
            # 비활성 연결 제거
            for client_id in inactive_clients:
                await self.remove_connection(client_id)
                logger.info(f"Cleaned up inactive connection: {client_id}")
            
            logger.info(f"Cleaned up {len(inactive_clients)} inactive connections")
            
        except Exception as e:
            logger.error(f"Error cleaning up connections: {str(e)}")
    
    async def add_client_to_channel(self, client_id: str, channel: str) -> bool:
        """
        클라이언트를 채널에 추가
        
        Args:
            client_id: 클라이언트 ID
            channel: 채널명
            
        Returns:
            추가 성공 여부
        """
        try:
            if client_id not in self.connections:
                logger.warning(f"Client {client_id} not found")
                return False
            
            # 채널에 클라이언트 추가
            if channel not in self.channels:
                self.channels[channel] = set()
            self.channels[channel].add(client_id)
            
            # 클라이언트에 채널 추가
            if client_id not in self.client_channels:
                self.client_channels[client_id] = set()
            self.client_channels[client_id].add(channel)
            
            # 연결 정보 업데이트
            self.connections[client_id]["channels"].add(channel)
            
            logger.info(f"Added client {client_id} to channel {channel}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding client to channel: {str(e)}")
            return False
    
    async def remove_client_from_channel(self, client_id: str, channel: str) -> bool:
        """
        클라이언트를 채널에서 제거
        
        Args:
            client_id: 클라이언트 ID
            channel: 채널명
            
        Returns:
            제거 성공 여부
        """
        try:
            if client_id not in self.connections:
                logger.warning(f"Client {client_id} not found")
                return False
            
            # 채널에서 클라이언트 제거
            if channel in self.channels:
                self.channels[channel].discard(client_id)
            
            # 클라이언트에서 채널 제거
            if client_id in self.client_channels:
                self.client_channels[client_id].discard(channel)
            
            # 연결 정보 업데이트
            self.connections[client_id]["channels"].discard(channel)
            
            logger.info(f"Removed client {client_id} from channel {channel}")
            return True
            
        except Exception as e:
            logger.error(f"Error removing client from channel: {str(e)}")
            return False
