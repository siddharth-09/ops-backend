"""
Configuration management for OpsFlow Guardian 2.0
"""

from pydantic_settings import BaseSettings
from typing import List, Optional
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # Application Configuration
    APP_NAME: str = "OpsFlow Guardian 2.0"
    VERSION: str = "2.0.0"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    
    # Security Configuration
    SECRET_KEY: str = "your_very_secure_secret_key_here_minimum_32_characters"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS Configuration
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000"
    ]
    
    # Database Configuration
    DATABASE_URL: str = "postgresql://opsflow:password@localhost:5432/opsflow_guardian"
    DATABASE_URL_TEST: Optional[str] = None
    
    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_CACHE_URL: str = "redis://localhost:6379/1"
    
    # LLM Provider Configuration (Google Gemini via Portia)
    GOOGLE_API_KEY: Optional[str] = None  # Primary: Google Gemini via Portia
    GEMINI_MODEL: str = "google/gemini-1.5-flash"  # Portia format: provider/model
    OPENAI_API_KEY: Optional[str] = None  # Fallback
    ANTHROPIC_API_KEY: Optional[str] = None  # Fallback
    
    # Portia Configuration
    PORTIA_API_KEY: Optional[str] = None
    
    # External Service API Keys
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    SLACK_BOT_TOKEN: Optional[str] = None
    SLACK_APP_TOKEN: Optional[str] = None
    NOTION_TOKEN: Optional[str] = None
    JIRA_SERVER: Optional[str] = None
    JIRA_USERNAME: Optional[str] = None
    JIRA_API_TOKEN: Optional[str] = None
    STRIPE_SECRET_KEY: Optional[str] = None
    SENDGRID_API_KEY: Optional[str] = None
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    
    # Monitoring and Logging
    LOG_LEVEL: str = "INFO"
    ENABLE_METRICS: bool = True
    ENABLE_TRACING: bool = True
    
    # File Upload Configuration
    MAX_FILE_SIZE_MB: int = 50
    UPLOAD_DIR: str = "./uploads"
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_BURST: int = 10
    
    # WebSocket Configuration
    WS_MAX_CONNECTIONS: int = 100
    WS_HEARTBEAT_INTERVAL: int = 30
    
    # Workflow Configuration
    MAX_WORKFLOW_STEPS: int = 50
    MAX_EXECUTION_TIME_MINUTES: int = 60
    MAX_CONCURRENT_WORKFLOWS: int = 10
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        
    def get_database_url(self) -> str:
        """Get the appropriate database URL"""
        if self.ENVIRONMENT == "test" and self.DATABASE_URL_TEST:
            return self.DATABASE_URL_TEST
        return self.DATABASE_URL


# Create global settings instance
settings = Settings()


# Validation functions
def validate_required_env_vars():
    """Validate that required environment variables are set"""
    required_vars = []
    
    # Check LLM provider (prioritize Gemini)
    if not any([settings.GOOGLE_API_KEY, settings.OPENAI_API_KEY, settings.ANTHROPIC_API_KEY]):
        required_vars.append("At least one LLM API key (GOOGLE_API_KEY for Gemini, OPENAI_API_KEY, or ANTHROPIC_API_KEY)")
    
    # Check database
    if not settings.DATABASE_URL or settings.DATABASE_URL == "postgresql://opsflow:password@localhost:5432/opsflow_guardian":
        required_vars.append("DATABASE_URL (configure your actual database connection)")
    
    # Check Redis
    if not settings.REDIS_URL:
        required_vars.append("REDIS_URL")
    
    # Check secret key
    if settings.SECRET_KEY == "your_very_secure_secret_key_here_minimum_32_characters":
        required_vars.append("SECRET_KEY (set a secure secret key)")
    
    if required_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(required_vars)}")


def get_llm_provider() -> str:
    """Get the primary LLM provider (prioritize Gemini 2.5)"""
    if settings.GOOGLE_API_KEY:
        return "google"
    elif settings.OPENAI_API_KEY:
        return "openai"
    elif settings.ANTHROPIC_API_KEY:
        return "anthropic"
    else:
        raise ValueError("No LLM provider configured. Please set GOOGLE_API_KEY for Gemini 2.5")
