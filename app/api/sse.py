"""
Server-Sent Events API - Production-ready SSE implementation
Following world best practices for SSE in production environments
"""
from fastapi import APIRouter, Request, HTTPException, Query
from fastapi.responses import StreamingResponse
from typing import Optional, List
import json
import asyncio
import logging
from datetime import datetime
from app.core.config import settings

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sse", tags=["Server-Sent Events"])


def get_sse_headers(request: Request) -> dict:
    """Get optimized SSE headers following best practices"""
    origin = request.headers.get('origin', '*')
    return {
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Connection": "keep-alive",
        "Content-Type": "text/event-stream; charset=utf-8",
        "Access-Control-Allow-Origin": origin,
        "Access-Control-Allow-Methods": "GET, OPTIONS",
        "Access-Control-Allow-Headers": "*",
        "Access-Control-Allow-Credentials": "true",
        "X-Accel-Buffering": "no",  # Disable nginx buffering
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
    }

def get_cors_headers(request: Request) -> dict:
    """Get CORS headers for SSE"""
    origin = request.headers.get('origin', '*')
    return {
        "Access-Control-Allow-Origin": origin,
        "Access-Control-Allow-Methods": "GET, OPTIONS",
        "Access-Control-Allow-Headers": "*",
        "Access-Control-Allow-Credentials": "true",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Content-Type": "text/event-stream; charset=utf-8",
    }


@router.options("/events")
async def sse_events_options(request: Request):
    """OPTIONS handler for CORS preflight"""
    from fastapi.responses import Response
    origin = request.headers.get('origin', '*')
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Credentials": "true",
        }
    )


@router.get("/events")
async def sse_events(
    request: Request,
    client_id: str = Query(..., description="Client identifier for SSE connection"),
    channels: Optional[str] = Query(None, description="Comma-separated list of channels to subscribe to")
):
    """
    Production-ready Server-Sent Events endpoint
    Features:
    - Proper error handling and logging
    - Connection validation
    - Graceful disconnection
    - Optimized for production environments
    """
    
    # Validate client_id
    if not client_id or len(client_id.strip()) == 0:
        raise HTTPException(status_code=400, detail="client_id is required")
    
    # Parse channels
    channel_list = []
    if channels:
        channel_list = [ch.strip() for ch in channels.split(',') if ch.strip()]
    
    logger.info(f"SSE connection initiated: client_id={client_id}, channels={channel_list}, origin={request.headers.get('origin', 'unknown')}")
    
    async def event_generator():
        """Production-ready SSE event stream generator"""
        connection_start = datetime.now()
        ping_count = 0
        
        try:
            # Send connection acknowledgment
            ack_data = {
                'type': 'connection_ack',
                'data': {
                    'client_id': client_id,
                    'channels': channel_list,
                    'message': 'Connected to real-time events',
                    'server_time': datetime.now().isoformat(),
                    'connection_id': f"{client_id}_{int(connection_start.timestamp())}"
                }
            }
            yield f"data: {json.dumps(ack_data, ensure_ascii=False)}\n\n"
            
            # Send initial data
            initial_data = {
                "menu_votes": [],
                "place_votes": [],
                "date_votes": [],
                "total_voters": 0,
                "active_voters": 0,
                "last_updated": int(datetime.now().timestamp() * 1000)
            }
            yield f"data: {json.dumps({'type': 'initial_stats', 'data': initial_data}, ensure_ascii=False)}\n\n"
            
            # Production-optimized keep-alive loop
            ping_interval = 30  # 30 seconds
            max_connection_time = 3600  # 1 hour max connection time
            
            while True:
                try:
                    # Check if client disconnected
                    if await request.is_disconnected():
                        logger.info(f"SSE client disconnected: {client_id}")
                        break
                    
                    # Check connection duration
                    if (datetime.now() - connection_start).seconds > max_connection_time:
                        logger.info(f"SSE connection timeout: {client_id}")
                        yield f"data: {json.dumps({'type': 'timeout', 'message': 'Connection timeout'}, ensure_ascii=False)}\n\n"
                        break
                    
                    # Send keep-alive ping
                    ping_count += 1
                    ping_data = {
                        'type': 'ping',
                        'timestamp': datetime.now().isoformat(),
                        'ping_count': ping_count,
                        'uptime': (datetime.now() - connection_start).seconds
                    }
                    yield f"data: {json.dumps(ping_data, ensure_ascii=False)}\n\n"
                    
                    # Wait for next ping
                    await asyncio.sleep(ping_interval)
                    
                except asyncio.CancelledError:
                    logger.info(f"SSE connection cancelled: {client_id}")
                    break
                except Exception as e:
                    logger.error(f"SSE ping error for {client_id}: {e}")
                    break
                
        except asyncio.CancelledError:
            logger.info(f"SSE connection cancelled: {client_id}")
        except Exception as e:
            logger.error(f"SSE error for {client_id}: {e}")
        finally:
            logger.info(f"SSE connection closed: {client_id}, duration: {(datetime.now() - connection_start).seconds}s")
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream; charset=utf-8",
        headers=get_sse_headers(request)
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
        headers=get_cors_headers(request)
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
        headers=get_cors_headers(request)
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
        headers=get_cors_headers(request)
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