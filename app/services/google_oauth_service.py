"""
Google OAuth Service for OpsFlow Guardian
Handles Google OAuth authentication flow
"""

import os
import httpx
import logging
from typing import Dict, Optional
from fastapi import HTTPException
from google.oauth2 import id_token
from google.auth.transport import requests
from datetime import datetime, timedelta
import jwt
import secrets

logger = logging.getLogger(__name__)

class GoogleOAuthService:
    def __init__(self):
        self.client_id = os.getenv("GOOGLE_CLIENT_ID")
        self.client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        self.redirect_uri = "https://opsflow-guardian.vercel.app/auth/callback"
        self.secret_key = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
        
        if not self.client_id or not self.client_secret:
            logger.warning("Google OAuth credentials not configured")
    
    def get_authorization_url(self, state: str = None) -> str:
        """Generate Google OAuth authorization URL"""
        if not state:
            state = secrets.token_urlsafe(32)
        
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": "openid email profile",
            "response_type": "code",
            "state": state,
            "access_type": "offline",
            "prompt": "consent"
        }
        
        query_string = "&".join([f"{key}={value}" for key, value in params.items()])
        return f"https://accounts.google.com/o/oauth2/v2/auth?{query_string}"
    
    async def exchange_code_for_tokens(self, code: str, state: str = None) -> Dict:
        """Exchange authorization code for access and ID tokens"""
        try:
            token_url = "https://oauth2.googleapis.com/token"
            
            data = {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": self.redirect_uri,
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(token_url, data=data)
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            logger.error(f"Failed to exchange code for tokens: {e}")
            raise HTTPException(status_code=400, detail="Failed to authenticate with Google")
    
    def verify_id_token(self, id_token_str: str) -> Dict:
        """Verify and decode Google ID token"""
        try:
            # Verify the token
            id_info = id_token.verify_oauth2_token(
                id_token_str, 
                requests.Request(), 
                self.client_id
            )
            
            # Verify the issuer
            if id_info['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                raise ValueError('Wrong issuer.')
            
            return id_info
            
        except Exception as e:
            logger.error(f"Failed to verify ID token: {e}")
            raise HTTPException(status_code=400, detail="Invalid Google ID token")
    
    def create_jwt_token(self, user_info: Dict) -> Dict:
        """Create JWT tokens for authenticated user"""
        try:
            # Create payload
            payload = {
                "user_id": user_info.get("sub"),
                "email": user_info.get("email"),
                "name": user_info.get("name"),
                "picture": user_info.get("picture"),
                "email_verified": user_info.get("email_verified", False),
                "exp": datetime.utcnow() + timedelta(hours=24),
                "iat": datetime.utcnow(),
                "iss": "opsflow-guardian"
            }
            
            # Create access token
            access_token = jwt.encode(payload, self.secret_key, algorithm="HS256")
            
            # Create refresh token (longer expiry)
            refresh_payload = {
                "user_id": user_info.get("sub"),
                "type": "refresh",
                "exp": datetime.utcnow() + timedelta(days=30),
                "iat": datetime.utcnow(),
            }
            refresh_token = jwt.encode(refresh_payload, self.secret_key, algorithm="HS256")
            
            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "expires_in": 86400,  # 24 hours
                "user": {
                    "id": user_info.get("sub"),
                    "email": user_info.get("email"),
                    "name": user_info.get("name"),
                    "picture": user_info.get("picture"),
                    "email_verified": user_info.get("email_verified", False)
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to create JWT token: {e}")
            raise HTTPException(status_code=500, detail="Failed to create authentication token")
    
    def verify_jwt_token(self, token: str) -> Dict:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")
    
    async def get_user_info(self, access_token: str) -> Dict:
        """Get user info from Google using access token"""
        try:
            user_info_url = f"https://www.googleapis.com/oauth2/v1/userinfo?access_token={access_token}"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(user_info_url)
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            logger.error(f"Failed to get user info: {e}")
            raise HTTPException(status_code=400, detail="Failed to get user information")

# Global instance
google_oauth = GoogleOAuthService()
