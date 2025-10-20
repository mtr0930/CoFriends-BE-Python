"""
FastAPI main application
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

# Configure CORS - 모든 origin 허용 (SSE 호환성을 위해)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 origin 허용
    allow_credentials=True,  # credentials 허용 (SSE를 위해)
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include API routes with /api prefix
app.include_router(api_router, prefix="/api")

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

