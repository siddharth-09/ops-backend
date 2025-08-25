"""
Rate limiting middleware for OpsFlow Guardian 2.0
"""

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import time
import logging
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware"""
    
    def __init__(self, app):
        super().__init__(app)
        # Store request timestamps per IP
        self.requests = defaultdict(deque)
        self.rate_limit = 60  # requests per minute
        self.window_size = 60  # seconds
    
    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting"""
        
        # Skip rate limiting in development
        from app.core.config import settings
        if settings.DEBUG:
            return await call_next(request)
        
        # Get client IP
        client_ip = request.client.host
        current_time = time.time()
        
        # Clean old requests
        self._clean_old_requests(client_ip, current_time)
        
        # Check rate limit
        if len(self.requests[client_ip]) >= self.rate_limit:
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please try again later."
            )
        
        # Add current request
        self.requests[client_ip].append(current_time)
        
        return await call_next(request)
    
    def _clean_old_requests(self, client_ip: str, current_time: float):
        """Remove old requests outside the time window"""
        cutoff_time = current_time - self.window_size
        while (self.requests[client_ip] and 
               self.requests[client_ip][0] < cutoff_time):
            self.requests[client_ip].popleft()
