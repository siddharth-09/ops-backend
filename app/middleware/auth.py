"""
Authentication middleware for OpsFlow Guardian 2.0
"""

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    """Authentication middleware"""
    
    def __init__(self, app):
        super().__init__(app)
        # Paths that don't require authentication
        self.public_paths = {
            "/",
            "/health",
            "/api/docs",
            "/api/redoc",
            "/api/openapi.json",
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/api/v1/auth/refresh"
        }
    
    async def dispatch(self, request: Request, call_next):
        """Process request and check authentication"""
        
        # Skip auth for public paths
        if request.url.path in self.public_paths:
            return await call_next(request)
        
        # Skip auth for development
        from app.core.config import settings
        if settings.DEBUG:
            return await call_next(request)
        
        # Check for authorization header
        auth_header = request.headers.get("authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
        
        # Extract token
        token = auth_header.split(" ")[1]
        
        # Mock token validation - replace with real JWT validation
        if not token.startswith("mock-jwt-token"):
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Add user info to request state (mock)
        request.state.user = {
            "user_id": "user-001",
            "email": "admin@opsflow.com",
            "role": "administrator"
        }
        
        return await call_next(request)
