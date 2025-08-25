"""
Configuration management for OpsFlow Guardian 2.0
"""

from pydantic_settings import BaseSettings
from typing import List, Optional, Literal
import os


class Settings(BaseSettings):
    """Application settings with multi-provider LLM support"""
    
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
    DATABASE_URL: str = "sqlite:///./opsflow_guardian.db"
    
    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # API Keys for LLM Providers
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None  # For Google Gemini
    MISTRAL_API_KEY: Optional[str] = None
    OLLAMA_API_KEY: Optional[str] = None
    
    # LLM Configuration
    LLM_PROVIDER: Literal["openai", "anthropic", "google", "mistral", "ollama"] = "google"
    OPENAI_MODEL: str = "gpt-4o-mini"
    ANTHROPIC_MODEL: str = "claude-3-5-sonnet-20241022"
    GEMINI_MODEL: str = "google/gemini-1.5-flash"  # Portia format
    MISTRAL_MODEL: str = "mistral-large-2411"
    OLLAMA_MODEL: str = "llama3.2"
    
    # AI Configuration
    MAX_TOKENS: int = 2000
    TEMPERATURE: float = 0.1
    
    # Integration API Keys
    SLACK_BOT_TOKEN: Optional[str] = None
    SLACK_SIGNING_SECRET: Optional[str] = None
    NOTION_TOKEN: Optional[str] = None
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    JIRA_DOMAIN: Optional[str] = None
    JIRA_API_TOKEN: Optional[str] = None
    JIRA_USER_EMAIL: Optional[str] = None
    
    # Email Configuration
    SMTP_SERVER: str = "localhost"
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    
    # File Upload Configuration
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    UPLOAD_FOLDER: str = "./uploads"
    
    # Rate Limiting Configuration
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 3600
    
    # Monitoring Configuration
    ENABLE_MONITORING: bool = True
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Utility functions for LLM provider management
def get_llm_provider() -> str:
    """Get the current LLM provider"""
    return settings.LLM_PROVIDER


def get_current_model() -> str:
    """Get the current model based on provider"""
    provider = get_llm_provider()
    
    if provider == "openai":
        return settings.OPENAI_MODEL
    elif provider == "anthropic":
        return settings.ANTHROPIC_MODEL
    elif provider == "google":
        return settings.GEMINI_MODEL
    elif provider == "mistral":
        return settings.MISTRAL_MODEL
    elif provider == "ollama":
        return settings.OLLAMA_MODEL
    else:
        return settings.GEMINI_MODEL  # Default to Gemini


def get_current_api_key() -> Optional[str]:
    """Get the current API key based on provider"""
    provider = get_llm_provider()
    
    if provider == "openai":
        return settings.OPENAI_API_KEY
    elif provider == "anthropic":
        return settings.ANTHROPIC_API_KEY
    elif provider == "google":
        return settings.GOOGLE_API_KEY
    elif provider == "mistral":
        return settings.MISTRAL_API_KEY
    elif provider == "ollama":
        return settings.OLLAMA_API_KEY
    else:
        return settings.GOOGLE_API_KEY  # Default to Google


# Create settings instance
settings = Settings()
