"""
Database configuration and connection management
"""
from typing import Generator, Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from pymongo import MongoClient
from pymongo.database import Database
import redis.asyncio as aioredis
from redis.asyncio import Redis

from app.core.config import settings
from app.models.postgres import Base


# PostgreSQL Configuration
DATABASE_URL = (
    f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@"
    f"{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
)

# SQLAlchemy engine (sync version for initial setup)
engine = create_engine(DATABASE_URL, echo=False)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# MongoDB Configuration
class MongoDB:
    client: Optional[MongoClient] = None
    db: Optional[Database] = None

    @classmethod
    def connect(cls):
        """Connect to MongoDB"""
        if settings.MONGODB_USERNAME and settings.MONGODB_PASSWORD:
            mongo_uri = (
                f"mongodb://{settings.MONGODB_USERNAME}:{settings.MONGODB_PASSWORD}@"
                f"{settings.MONGODB_HOST}:{settings.MONGODB_PORT}/"
            )
        else:
            mongo_uri = f"mongodb://{settings.MONGODB_HOST}:{settings.MONGODB_PORT}/"
        
        cls.client = MongoClient(mongo_uri)
        cls.db = cls.client[settings.MONGODB_DATABASE]
        print(f"Connected to MongoDB: {settings.MONGODB_DATABASE}")

    @classmethod
    def close(cls):
        """Close MongoDB connection"""
        if cls.client:
            cls.client.close()
            print("Closed MongoDB connection")

    @classmethod
    def get_database(cls) -> Database:
        """Get MongoDB database instance"""
        if cls.db is None:
            cls.connect()
        return cls.db


# Redis Configuration
class RedisClient:
    client: Optional[Redis] = None

    @classmethod
    async def connect(cls):
        """Connect to Redis"""
        cls.client = await aioredis.from_url(
            f"redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}",
            encoding="utf-8",
            decode_responses=True
        )
        print("Connected to Redis")

    @classmethod
    async def close(cls):
        """Close Redis connection"""
        if cls.client:
            await cls.client.close()
            print("Closed Redis connection")

    @classmethod
    def get_client(cls) -> Redis:
        """Get Redis client instance"""
        if cls.client is None:
            raise RuntimeError("Redis client not initialized. Call connect() first.")
        return cls.client


# Dependency for getting Redis client
async def get_redis() -> Redis:
    """Get Redis client"""
    return RedisClient.get_client()


# Dependency for getting MongoDB
def get_mongodb() -> Database:
    """Get MongoDB database"""
    return MongoDB.get_database()

