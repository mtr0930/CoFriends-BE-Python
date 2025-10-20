"""
Application configuration using pydantic-settings
"""
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from .secrets_manager import load_secrets_to_environment


class Settings(BaseSettings):
    """Application settings"""
    
    # Server Configuration
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 5000
    ENVIRONMENT: str = "local"
    
    # PostgreSQL Configuration
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "1234"
    POSTGRES_DB: str = "cofriends"
    
    # MongoDB Configuration
    MONGODB_HOST: str = "mongodb"
    MONGODB_PORT: int = 27017
    MONGODB_USERNAME: str = "mongo"
    MONGODB_PASSWORD: str = "1234"
    MONGODB_DATABASE: str = "cofriends_chat"
    MONGODB_AUTH_SOURCE: str = "admin"
    
    # Redis Configuration
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = "1234"
    REDIS_DB: int = 0
    
    
    # Slack Configuration
    SLACK_CLIENT_ID: str = ""
    SLACK_CLIENT_SECRET: str = ""
    SLACK_REDIRECT_URI: str = ""
    
    # CORS Configuration - will be set dynamically based on environment
    CORS_ORIGINS: str = ""
    
    # AWS Bedrock Configuration
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "ap-northeast-2"
    BEDROCK_MODEL_ID: str = "anthropic.claude-3-sonnet-20240229-v1:0"
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Get CORS origins as list"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    def get_cors_origins_for_environment(self) -> str:
        """Get CORS origins based on environment"""
        if self.ENVIRONMENT.lower() in ["prod", "production"]:
            return "http://54.180.71.13:3000,http://54.180.71.13:5173,https://buildpechatbot.com,https://buildpechatbot.com:5000"
        else:
            return "http://localhost:3000,http://localhost:5173,http://localhost:5000"
    
    @property
    def DATABASE_URL(self) -> str:
        """PostgreSQL database URL"""
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"  # 추가 환경 변수 허용
    )


# Load secrets from AWS Secrets Manager before creating settings
load_secrets_to_environment()

settings = Settings()

# Set CORS origins based on environment after settings creation
settings.CORS_ORIGINS = settings.get_cors_origins_for_environment()

