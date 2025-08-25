"""
Authentication API routes for OpsFlow Guardian
Handles Google OAuth authentication endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional
import logging
from app.services.google_oauth_service import google_oauth

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])
security = HTTPBearer(auto_error=False)

class GoogleAuthRequest(BaseModel):
    code: str
    state: Optional[str] = None

class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    user: dict

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    picture: str
    email_verified: bool

@router.get("/google/url")
async def get_google_auth_url():
    """Get Google OAuth authorization URL"""
    try:
        auth_url = google_oauth.get_authorization_url()
        return {
            "success": True,
            "data": {
                "auth_url": auth_url,
                "message": "Redirect user to this URL for Google authentication"
            }
        }
    except Exception as e:
        logger.error(f"Failed to generate Google auth URL: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate authentication URL")

@router.post("/google/callback", response_model=LoginResponse)
async def google_auth_callback(auth_request: GoogleAuthRequest):
    """Handle Google OAuth callback"""
    try:
        # Exchange code for tokens
        tokens = await google_oauth.exchange_code_for_tokens(
            code=auth_request.code,
            state=auth_request.state
        )
        
        # Verify ID token and get user info
        user_info = google_oauth.verify_id_token(tokens.get("id_token"))
        
        # Create our JWT tokens
        jwt_tokens = google_oauth.create_jwt_token(user_info)
        
        # Here you would typically save user to database
        # For now, we'll just return the tokens
        
        logger.info(f"User {user_info.get('email')} authenticated successfully")
        
        return LoginResponse(**jwt_tokens)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Google auth callback failed: {e}")
        raise HTTPException(status_code=400, detail="Authentication failed")

@router.post("/google/login")
async def google_login(auth_request: GoogleAuthRequest):
    """Alternative login endpoint (same as callback)"""
    return await google_auth_callback(auth_request)

@router.get("/me", response_model=UserResponse)
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user info"""
    if not credentials:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        # Verify JWT token
        payload = google_oauth.verify_jwt_token(credentials.credentials)
        
        return UserResponse(
            id=payload.get("user_id"),
            email=payload.get("email"),
            name=payload.get("name"),
            picture=payload.get("picture"),
            email_verified=payload.get("email_verified", False)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user info: {e}")
        raise HTTPException(status_code=401, detail="Invalid authentication token")

@router.post("/refresh")
async def refresh_token(refresh_token: str):
    """Refresh access token using refresh token"""
    try:
        # Verify refresh token
        payload = google_oauth.verify_jwt_token(refresh_token)
        
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        
        # Create new access token
        user_info = {
            "sub": payload.get("user_id"),
            "email": payload.get("email"),
            "name": payload.get("name"),
            "picture": payload.get("picture"),
            "email_verified": payload.get("email_verified", False)
        }
        
        new_tokens = google_oauth.create_jwt_token(user_info)
        
        return {
            "access_token": new_tokens["access_token"],
            "token_type": "bearer",
            "expires_in": 86400
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh failed: {e}")
        raise HTTPException(status_code=401, detail="Failed to refresh token")

@router.post("/logout")
async def logout():
    """Logout user (client should delete tokens)"""
    return {
        "success": True,
        "message": "Logout successful. Please delete tokens from client storage."
    }

@router.get("/health")
async def auth_health():
    """Health check for auth service"""
    return {
        "status": "healthy",
        "service": "authentication",
        "google_oauth_configured": bool(google_oauth.client_id and google_oauth.client_secret)
    }
