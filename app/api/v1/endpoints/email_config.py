"""
Email Configuration API Endpoints for OpsFlow Guardian 2.0
Allows users to configure their own email settings
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.user_email_config import UserEmailConfig
from app.models.user import User
from app.services.user_email_service import get_user_email_service
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/email-config", tags=["Email Configuration"])

# Pydantic models for request/response
class EmailConfigCreate(BaseModel):
    email_address: EmailStr = Field(..., description="Gmail address to send emails from")
    app_password: str = Field(..., min_length=16, max_length=16, description="16-character Gmail app password")
    from_name: str = Field(..., min_length=1, max_length=100, description="Display name for emails")
    email_host: Optional[str] = Field(default="smtp.gmail.com", description="SMTP server")
    email_port: Optional[int] = Field(default=587, description="SMTP port")
    email_use_tls: Optional[bool] = Field(default=True, description="Use TLS encryption")

    class Config:
        schema_extra = {
            "example": {
                "email_address": "user@gmail.com",
                "app_password": "abcd efgh ijkl mnop",
                "from_name": "John Doe - OpsFlow",
                "email_host": "smtp.gmail.com",
                "email_port": 587,
                "email_use_tls": True
            }
        }

class EmailConfigResponse(BaseModel):
    id: int
    email_address: str
    from_name: str
    email_host: str
    email_port: int
    email_use_tls: bool
    is_verified: bool
    is_active: bool
    created_at: Optional[str]
    last_tested: Optional[str]

class EmailTestResult(BaseModel):
    success: bool
    message: str
    tested_at: str

# Dependency to get current user (mock for now)
def get_current_user(db: Session = Depends(get_db)) -> User:
    """Get current authenticated user - mock implementation"""
    # In a real app, this would decode JWT token and get user
    # For demo purposes, return user with ID 1
    user = db.query(User).filter(User.id == 1).first()
    if not user:
        # Create demo user if doesn't exist
        user = User(
            email="demo@opsflow.com",
            username="demo_user",
            full_name="Demo User",
            hashed_password="dummy_hash",
            is_active=True,
            is_verified=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    return user

@router.post("/configure", response_model=EmailConfigResponse, status_code=status.HTTP_201_CREATED)
async def configure_user_email(
    config_data: EmailConfigCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Configure email settings for the current user.
    
    This allows users to set up their own Gmail SMTP credentials
    so all workflow notifications come from their email address.
    """
    try:
        # Check if user already has email config
        existing_config = db.query(UserEmailConfig).filter(
            UserEmailConfig.user_id == current_user.id
        ).first()
        
        if existing_config:
            # Update existing configuration
            existing_config.email_address = config_data.email_address
            existing_config.encrypt_password(config_data.app_password.replace(" ", ""))  # Remove spaces
            existing_config.from_name = config_data.from_name
            existing_config.email_host = config_data.email_host
            existing_config.email_port = config_data.email_port
            existing_config.email_use_tls = config_data.email_use_tls
            existing_config.is_verified = False  # Re-verify after update
            existing_config.updated_at = datetime.utcnow()
            
            email_config = existing_config
            logger.info(f"Updated email config for user {current_user.id}")
        else:
            # Create new configuration
            email_config = UserEmailConfig(
                user_id=current_user.id,
                email_address=config_data.email_address,
                from_name=config_data.from_name,
                email_host=config_data.email_host,
                email_port=config_data.email_port,
                email_use_tls=config_data.email_use_tls
            )
            email_config.encrypt_password(config_data.app_password.replace(" ", ""))  # Remove spaces
            db.add(email_config)
            logger.info(f"Created new email config for user {current_user.id}")
        
        db.commit()
        db.refresh(email_config)
        
        return EmailConfigResponse(
            id=email_config.id,
            email_address=email_config.email_address,
            from_name=email_config.from_name,
            email_host=email_config.email_host,
            email_port=email_config.email_port,
            email_use_tls=email_config.email_use_tls,
            is_verified=email_config.is_verified,
            is_active=email_config.is_active,
            created_at=email_config.created_at.isoformat() if email_config.created_at else None,
            last_tested=email_config.last_tested.isoformat() if email_config.last_tested else None
        )
        
    except Exception as e:
        logger.error(f"Failed to configure email for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save email configuration"
        )

@router.post("/test", response_model=EmailTestResult)
async def test_user_email(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Test the user's email configuration by sending a test email.
    
    This sends a test email to the user's registered email address
    to verify that their Gmail SMTP configuration is working.
    """
    try:
        email_service = get_user_email_service(current_user.id, db)
        
        if not email_service.is_configured():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email not configured. Please configure your email settings first."
            )
        
        # Test the connection
        success = await email_service.test_connection()
        
        if success:
            return EmailTestResult(
                success=True,
                message="✅ Test email sent successfully! Check your inbox. Your email configuration is working perfectly.",
                tested_at=datetime.utcnow().isoformat()
            )
        else:
            return EmailTestResult(
                success=False,
                message="❌ Failed to send test email. Please check your Gmail app password and try again.",
                tested_at=datetime.utcnow().isoformat()
            )
            
    except Exception as e:
        logger.error(f"Email test failed for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Email test failed: {str(e)}"
        )

@router.get("/status", response_model=Optional[EmailConfigResponse])
async def get_email_config_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the current user's email configuration status.
    
    Returns the user's email configuration details (excluding sensitive data)
    or null if no configuration exists.
    """
    email_config = db.query(UserEmailConfig).filter(
        UserEmailConfig.user_id == current_user.id,
        UserEmailConfig.is_active == True
    ).first()
    
    if not email_config:
        return None
    
    return EmailConfigResponse(
        id=email_config.id,
        email_address=email_config.email_address,
        from_name=email_config.from_name,
        email_host=email_config.email_host,
        email_port=email_config.email_port,
        email_use_tls=email_config.email_use_tls,
        is_verified=email_config.is_verified,
        is_active=email_config.is_active,
        created_at=email_config.created_at.isoformat() if email_config.created_at else None,
        last_tested=email_config.last_tested.isoformat() if email_config.last_tested else None
    )

@router.delete("/remove", status_code=status.HTTP_204_NO_CONTENT)
async def remove_email_config(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Remove the user's email configuration.
    
    This deactivates the user's email configuration, preventing
    email notifications from being sent.
    """
    email_config = db.query(UserEmailConfig).filter(
        UserEmailConfig.user_id == current_user.id,
        UserEmailConfig.is_active == True
    ).first()
    
    if email_config:
        email_config.is_active = False
        email_config.updated_at = datetime.utcnow()
        db.commit()
        logger.info(f"Removed email config for user {current_user.id}")
    
    return None

@router.get("/setup-guide")
async def get_gmail_setup_guide():
    """
    Get step-by-step instructions for setting up Gmail app passwords.
    
    Returns detailed instructions for users to generate Gmail app passwords
    for use with OpsFlow Guardian.
    """
    return {
        "title": "Gmail SMTP Setup Guide",
        "description": "Follow these steps to configure Gmail for OpsFlow Guardian",
        "steps": [
            {
                "step": 1,
                "title": "Enable 2-Factor Authentication",
                "description": "Gmail app passwords require 2-Factor Authentication to be enabled on your Google account.",
                "action": "Go to https://myaccount.google.com/security and enable 2-Step Verification"
            },
            {
                "step": 2,
                "title": "Generate App Password",
                "description": "Create a specific app password for OpsFlow Guardian.",
                "action": "Visit https://myaccount.google.com/apppasswords and generate a new app password"
            },
            {
                "step": 3,
                "title": "Select Mail Application",
                "description": "Choose 'Mail' as the app type when generating the password.",
                "action": "In the app password generator, select 'Mail' from the dropdown"
            },
            {
                "step": 4,
                "title": "Copy the Password",
                "description": "Google will show you a 16-character password. Copy this exactly.",
                "action": "Copy the password (format: 'abcd efgh ijkl mnop') and paste it into OpsFlow"
            },
            {
                "step": 5,
                "title": "Configure in OpsFlow",
                "description": "Use your Gmail address and the app password in OpsFlow Guardian.",
                "action": "Fill in the email configuration form and test the connection"
            }
        ],
        "troubleshooting": [
            {
                "issue": "Authentication failed",
                "solution": "Make sure 2-Factor Authentication is enabled and you're using an app password, not your regular Gmail password"
            },
            {
                "issue": "App password option not available",
                "solution": "Ensure 2-Step Verification is fully set up and activated on your Google account"
            },
            {
                "issue": "Emails not sending",
                "solution": "Check that 'Less secure app access' is enabled or use an app password instead"
            }
        ],
        "security_notes": [
            "App passwords are more secure than using your main Gmail password",
            "Each app password is unique and can be revoked independently",
            "OpsFlow encrypts and securely stores your app password",
            "You can revoke the app password anytime from your Google account settings"
        ]
    }
