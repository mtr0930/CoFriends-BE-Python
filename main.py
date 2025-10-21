"""
FastAPI main application
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 한국 시간대 설정
from app.utils.timezone_utils import set_korean_timezone
set_korean_timezone()

from app.core.config import settings
from app.core.database import init_db, MongoDB, RedisClient
# SSE 매니저 제거 - 단순한 SSE 구현 사용
from app.api import api_router
from app.api.sse import router as sse_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan events
    """
    # Startup
    print("Starting up CoFriends FastAPI server...")
    
    # Initialize PostgreSQL tables
    init_db()
    print("PostgreSQL database initialized")
    
    # Connect to MongoDB
    MongoDB.connect()
    
    # Connect to Redis
    await RedisClient.connect()
    
    # SSE 매니저 제거 - 단순한 SSE 구현 사용
    print("SSE endpoints ready")
    
    yield
    
    # Shutdown
    print("Shutting down CoFriends FastAPI server...")
    
    # Close MongoDB connection
    MongoDB.close()
    
    # Close Redis connection
    await RedisClient.close()
    
    # SSE 매니저 제거 - 단순한 SSE 구현 사용


# Create FastAPI application
app = FastAPI(
    title="CoFriends API",
    description="Co-Friends Backend API - Employee dining preference management service with real-time updates",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS - 개발 환경용 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173", 
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "https://buildpechatbot.com",
        "http://buildpechatbot.com"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include API routes with /api prefix
app.include_router(api_router, prefix="/api")

# Include auth routes separately (no /api prefix for nginx routing)
from app.api import slack
app.include_router(slack.router)

# Include SSE routes separately (no /api prefix for nginx routing)
app.include_router(sse_router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to CoFriends API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "sse": "/sse/events"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "sse_endpoints": ["/sse/events", "/sse/votes", "/sse/chat", "/sse/ai"]
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
        reload=True if settings.ENVIRONMENT == "local" else False
    )

