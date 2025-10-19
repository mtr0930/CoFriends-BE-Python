"""
Server-Sent Events API - 단순하고 안정적인 구현
복잡한 매니저 없이 직접 스트림
"""
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse
from typing import Optional
import json
import asyncio
from datetime import datetime

router = APIRouter(prefix="/sse", tags=["Server-Sent Events"])


@router.get("/events")
async def sse_events(
    request: Request,
    client_id: str,
    channels: Optional[str] = None
):
    """
    Server-Sent Events 엔드포인트 - 단순한 구현
    """
    
    async def event_generator():
        """SSE 이벤트 스트림 생성"""
        try:
            print(f"✅ SSE connected: {client_id}")
            
            # 연결 확인 메시지
            yield f"data: {json.dumps({'type': 'connection_ack', 'data': {'client_id': client_id, 'channels': channels, 'message': 'Connected to real-time events'}})}\n\n"
            
            # 초기 데이터 전송
            initial_data = {
                "menu_votes": [],
                "place_votes": [],
                "date_votes": [],
                "total_voters": 0,
                "active_voters": 0,
                "last_updated": int(datetime.now().timestamp() * 1000)
            }
            yield f"data: {json.dumps({'type': 'initial_stats', 'data': initial_data})}\n\n"
            
            # Keep-alive 루프
            ping_interval = 30  # 30초마다 핑 (안정성 향상)
            
            while True:
                try:
                    # 연결 상태 확인
                    if await request.is_disconnected():
                        print(f"❌ SSE disconnected: {client_id}")
                        break
                    
                    # Keep-alive ping
                    yield f"data: {json.dumps({'type': 'ping', 'timestamp': datetime.now().isoformat()})}\n\n"
                    
                    # 30초 대기
                    await asyncio.sleep(ping_interval)
                except asyncio.CancelledError:
                    print(f"SSE ping cancelled for {client_id}")
                    break
                except Exception as e:
                    print(f"SSE ping error for {client_id}: {e}")
                    break
                
        except asyncio.CancelledError:
            print(f"SSE connection cancelled for {client_id}")
        except Exception as e:
            print(f"SSE error for {client_id}: {e}")
        finally:
            print(f"❌ SSE disconnected: {client_id}")
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control",
            "X-Accel-Buffering": "no",
            "X-Content-Type-Options": "nosniff"
        }
    )


@router.get("/votes")
async def sse_votes(
    request: Request,
    client_id: str
):
    """투표 전용 SSE 스트림"""
    
    async def vote_event_generator():
        try:
            print(f"✅ Vote SSE connected: {client_id}")
            
            # 초기 데이터
            initial_data = {
                "menu_votes": [],
                "place_votes": [],
                "date_votes": [],
                "total_voters": 0,
                "active_voters": 0,
                "last_updated": int(datetime.now().timestamp() * 1000)
            }
            yield f"data: {json.dumps({'type': 'initial_stats', 'data': initial_data})}\n\n"
            
            while True:
                yield f"data: {json.dumps({'type': 'ping', 'timestamp': datetime.now().isoformat()})}\n\n"
                await asyncio.sleep(30)
                
        except asyncio.CancelledError:
            pass
        finally:
            print(f"❌ Vote SSE disconnected: {client_id}")
    
    return StreamingResponse(
        vote_event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/chat")
async def sse_chat(
    request: Request,
    client_id: str
):
    """채팅 전용 SSE 스트림"""
    
    async def chat_event_generator():
        try:
            print(f"✅ Chat SSE connected: {client_id}")
            
            while True:
                yield f"data: {json.dumps({'type': 'ping', 'timestamp': datetime.now().isoformat()})}\n\n"
                await asyncio.sleep(30)
                
        except asyncio.CancelledError:
            pass
        finally:
            print(f"❌ Chat SSE disconnected: {client_id}")
    
    return StreamingResponse(
        chat_event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/ai")
async def sse_ai(
    request: Request,
    client_id: str
):
    """AI 응답 전용 SSE 스트림"""
    
    async def ai_event_generator():
        try:
            print(f"✅ AI SSE connected: {client_id}")
            
            while True:
                yield f"data: {json.dumps({'type': 'ping', 'timestamp': datetime.now().isoformat()})}\n\n"
                await asyncio.sleep(30)
                
        except asyncio.CancelledError:
            pass
        finally:
            print(f"❌ AI SSE disconnected: {client_id}")
    
    return StreamingResponse(
        ai_event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "X-Accel-Buffering": "no"
        }
    )


# SSE 이벤트 전송 함수
async def send_sse_event(event_type: str, data: dict, client_id: str = None):
    """SSE 이벤트를 전송하는 함수"""
    try:
        # Redis를 통해 SSE 이벤트 전송
        import redis
        from app.core.config import settings
        
        redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True
        )
        
        event_data = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        
        # 특정 클라이언트에게만 전송
        if client_id:
            redis_client.publish(f"sse:{client_id}", json.dumps(event_data))
        else:
            # 모든 클라이언트에게 브로드캐스트
            redis_client.publish("sse:broadcast", json.dumps(event_data))
            
        print(f"📡 SSE Event sent: {event_type} - {data}")
        
    except Exception as e:
        print(f"❌ Error sending SSE event: {e}")


# SSE 이벤트를 모든 사용자에게 브로드캐스트하는 함수
async def send_sse_event_to_all_users(event_type: str, data: dict):
    """모든 사용자에게 SSE 이벤트를 브로드캐스트"""
    await send_sse_event(event_type, data)