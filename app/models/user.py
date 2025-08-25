"""
User models for OpsFlow Guardian 2.0
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.orm import relationship
from app.db.database import Base
from datetime import datetime
import uuid


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    user_uuid = Column(String, unique=True, default=lambda: str(uuid.uuid4()), index=True)
    
    # Basic user information
    email = Column(String, unique=True, nullable=False, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    full_name = Column(String, nullable=False)
    company = Column(String)
    department = Column(String)
    job_title = Column(String)
    
    # Authentication
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)
    
    # Profile settings
    timezone = Column(String, default="UTC")
    notification_preferences = Column(Text)  # JSON string
    avatar_url = Column(String)
    
    # Security
    failed_login_attempts = Column(Integer, default=0)
    last_failed_login = Column(DateTime)
    password_changed_at = Column(DateTime, default=datetime.utcnow)
    two_factor_enabled = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime)
    last_activity = Column(DateTime)
    
    # Relationships
    email_config = relationship("UserEmailConfig", back_populates="user", uselist=False, cascade="all, delete-orphan")
    workflows = relationship("Workflow", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', username='{self.username}')>"
    
    @property
    def display_name(self) -> str:
        """Get display name for the user"""
        return self.full_name or self.username or self.email.split("@")[0]
    
    @property
    def has_email_configured(self) -> bool:
        """Check if user has email configuration"""
        return bool(self.email_config and self.email_config.is_configured)
    
    def to_dict(self, include_sensitive=False):
        """Convert user to dictionary"""
        data = {
            "id": self.id,
            "user_uuid": self.user_uuid,
            "email": self.email,
            "username": self.username,
            "full_name": self.full_name,
            "company": self.company,
            "department": self.department,
            "job_title": self.job_title,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "is_admin": self.is_admin,
            "timezone": self.timezone,
            "avatar_url": self.avatar_url,
            "two_factor_enabled": self.two_factor_enabled,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "has_email_configured": self.has_email_configured
        }
        
        if include_sensitive:
            data.update({
                "failed_login_attempts": self.failed_login_attempts,
                "last_failed_login": self.last_failed_login.isoformat() if self.last_failed_login else None,
                "password_changed_at": self.password_changed_at.isoformat() if self.password_changed_at else None,
            })
        
        return data


class UserSession(Base):
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    session_token = Column(String, unique=True, nullable=False, index=True)
    refresh_token = Column(String, unique=True, nullable=False, index=True)
    
    # Session metadata
    ip_address = Column(String)
    user_agent = Column(Text)
    device_info = Column(Text)
    
    # Session status
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    last_accessed = Column(DateTime, default=datetime.utcnow)
    
    def is_expired(self) -> bool:
        """Check if session is expired"""
        return datetime.utcnow() > self.expires_at
    
    def __repr__(self):
        return f"<UserSession(id={self.id}, user_id={self.user_id}, active={self.is_active})>"


class UserActivity(Base):
    __tablename__ = "user_activities"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    
    # Activity details
    action = Column(String, nullable=False)  # e.g., 'login', 'create_workflow', 'send_email'
    resource_type = Column(String)  # e.g., 'workflow', 'email', 'user'
    resource_id = Column(String)
    description = Column(Text)
    
    # Request metadata
    ip_address = Column(String)
    user_agent = Column(Text)
    
    # Result
    success = Column(Boolean, default=True)
    error_message = Column(Text)
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f"<UserActivity(id={self.id}, user_id={self.user_id}, action='{self.action}')>"
