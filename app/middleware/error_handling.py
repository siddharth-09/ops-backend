"""
Error handling middleware for OpsFlow Guardian 2.0
"""

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import logging
import traceback

logger = logging.getLogger(__name__)


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Global error handling middleware"""
    
    async def dispatch(self, request: Request, call_next):
        """Process request with error handling"""
        
        try:
            response = await call_next(request)
            return response
            
        except HTTPException:
            # Re-raise HTTP exceptions as they are handled by FastAPI
            raise
            
        except Exception as e:
            # Log the error
            logger.error(f"Unhandled exception in {request.method} {request.url}: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            # Return generic error response
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": "Internal server error",
                    "detail": "An unexpected error occurred"
                }
            )
