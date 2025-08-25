from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.db.database import Base
import json
from cryptography.fernet import Fernet
import os
from datetime import datetime

class UserEmailConfig(Base):
    __tablename__ = "user_email_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    
    # Email credentials (encrypted for security)
    email_address = Column(String, nullable=False)
    encrypted_password = Column(String, nullable=False)  # Encrypted app password
    
    # Email server settings
    email_host = Column(String, default="smtp.gmail.com")
    email_port = Column(Integer, default=587)
    email_use_tls = Column(Boolean, default=True)
    
    # Display settings
    from_name = Column(String, nullable=False)
    
    # Status tracking
    is_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_tested = Column(DateTime)
    
    # Relationship
    user = relationship("User", back_populates="email_config")
    
    def encrypt_password(self, password: str):
        """Encrypt the email password for secure storage"""
        key = self._get_encryption_key()
        f = Fernet(key)
        self.encrypted_password = f.encrypt(password.encode()).decode()
    
    def decrypt_password(self) -> str:
        """Decrypt the email password for use"""
        try:
            key = self._get_encryption_key()
            f = Fernet(key)
            return f.decrypt(self.encrypted_password.encode()).decode()
        except Exception:
            return ""
    
    def _get_encryption_key(self) -> bytes:
        """Get or generate encryption key"""
        key = os.getenv("ENCRYPTION_KEY")
        if not key:
            # Generate a new key if none exists
            key = Fernet.generate_key().decode()
            # In production, you should store this securely
        
        if isinstance(key, str):
            # Ensure key is proper length
            if len(key) < 44:  # Fernet keys are 44 characters when base64 encoded
                key = Fernet.generate_key().decode()
            return key.encode()
        return key
    
    @property
    def is_configured(self) -> bool:
        """Check if email is properly configured"""
        return bool(
            self.email_address and 
            self.encrypted_password and 
            self.from_name and
            self.is_active
        )
    
    def to_dict(self):
        """Convert to dictionary (excluding sensitive data)"""
        return {
            "id": self.id,
            "email_address": self.email_address,
            "from_name": self.from_name,
            "email_host": self.email_host,
            "email_port": self.email_port,
            "email_use_tls": self.email_use_tls,
            "is_verified": self.is_verified,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_tested": self.last_tested.isoformat() if self.last_tested else None
        }
