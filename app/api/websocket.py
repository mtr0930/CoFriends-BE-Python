"""
WebSocket API for real-time vote updates
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.core.websocket import manager
from app.api.realtime import get_vote_stats

router = APIRouter(prefix="/ws", tags=["WebSocket"])


@router.websocket("/votes")
async def websocket_votes(
    websocket: WebSocket,
    emp_no: Optional[str] = None
):
    """
    실시간 투표 업데이트 WebSocket 엔드포인트
    
    연결 URL: ws://localhost:5000/ws/votes?emp_no=12345
    
    서버에서 클라이언트로 전송하는 메시지 타입:
    1. connection_ack: 연결 확인
    2. vote_update: 투표 업데이트
    3. stats_update: 전체 통계 업데이트
    
    클라이언트에서 서버로 전송할 수 있는 메시지:
    1. get_stats: 현재 통계 요청
    2. ping: 연결 유지
    """
    # WebSocket 연결 수락
    await manager.initialize()
    await manager.connect(websocket)
    
    # 연결 확인 메시지
    await websocket.send_json({
        "type": "connection_ack",
        "data": {
            "emp_no": emp_no,
            "active_connections": len(manager.active_connections),
            "message": "Connected to real-time vote updates"
        }
    })
    
    try:
        while True:
            # 클라이언트로부터 메시지 수신
            data = await websocket.receive_json()
            message_type = data.get("type")
            
            if message_type == "get_stats":
                # 현재 투표 통계 조회 및 전송
                # Note: get_db()를 직접 호출할 수 없으므로 별도 처리 필요
                await websocket.send_json({
                    "type": "stats_response",
                    "data": {
                        "message": "Use polling API for initial stats"
                    }
                })
            
            elif message_type == "ping":
                # 연결 유지 응답
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": data.get("timestamp")
                })
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print(f"Client {emp_no} disconnected")
    
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)


@router.on_event("startup")
async def startup_event():
    """서버 시작 시 Redis 연결 초기화"""
    await manager.initialize()


@router.on_event("shutdown")
async def shutdown_event():
    """서버 종료 시 리소스 정리"""
    await manager.cleanup()

