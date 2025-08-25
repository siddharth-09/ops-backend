"""
Supabase Integration Service
Provides additional utilities for working with Supabase features
"""

import os
import logging
from typing import Optional, Dict, Any, List
import httpx
from datetime import datetime, timedelta
import asyncio

logger = logging.getLogger(__name__)

class SupabaseService:
    """Service for interacting with Supabase-specific features"""
    
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_anon_key = os.getenv("SUPABASE_ANON_KEY")
        self.supabase_service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        if not all([self.supabase_url, self.supabase_anon_key]):
            logger.warning("Supabase credentials not fully configured - some features may not work")
    
    def get_headers(self, use_service_key: bool = False) -> Dict[str, str]:
        """Get headers for Supabase API requests"""
        key = self.supabase_service_key if use_service_key else self.supabase_anon_key
        return {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }
    
    async def create_user_profile(self, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a user profile in Supabase"""
        if not self.supabase_url:
            return None
            
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.supabase_url}/rest/v1/users",
                    headers=self.get_headers(use_service_key=True),
                    json=user_data
                )
                
                if response.status_code == 201:
                    return response.json()[0]
                else:
                    logger.error(f"Failed to create user profile: {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error creating user profile: {e}")
            return None
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email from Supabase"""
        if not self.supabase_url:
            return None
            
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.supabase_url}/rest/v1/users?email=eq.{email}&select=*",
                    headers=self.get_headers(use_service_key=True)
                )
                
                if response.status_code == 200:
                    users = response.json()
                    return users[0] if users else None
                else:
                    logger.error(f"Failed to get user by email: {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting user by email: {e}")
            return None
    
    async def update_user_login(self, user_uuid: str) -> bool:
        """Update user's last login timestamp"""
        if not self.supabase_url:
            return False
            
        try:
            async with httpx.AsyncClient() as client:
                response = await client.patch(
                    f"{self.supabase_url}/rest/v1/users?user_uuid=eq.{user_uuid}",
                    headers=self.get_headers(use_service_key=True),
                    json={"last_login": datetime.utcnow().isoformat()}
                )
                
                return response.status_code == 200
                
        except Exception as e:
            logger.error(f"Error updating user login: {e}")
            return False
    
    async def log_audit_event(self, event_data: Dict[str, Any]) -> bool:
        """Log an audit event to Supabase"""
        if not self.supabase_url:
            return False
            
        try:
            # Ensure required fields
            event_data.setdefault("created_at", datetime.utcnow().isoformat())
            event_data.setdefault("severity", "info")
            event_data.setdefault("compliance_status", "compliant")
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.supabase_url}/rest/v1/audit_events",
                    headers=self.get_headers(use_service_key=True),
                    json=event_data
                )
                
                return response.status_code == 201
                
        except Exception as e:
            logger.error(f"Error logging audit event: {e}")
            return False
    
    async def get_realtime_connection_url(self) -> Optional[str]:
        """Get WebSocket URL for Supabase Realtime"""
        if not self.supabase_url:
            return None
            
        # Convert REST URL to WebSocket URL
        ws_url = self.supabase_url.replace("https://", "wss://").replace("http://", "ws://")
        return f"{ws_url}/realtime/v1/websocket?apikey={self.supabase_anon_key}&vsn=1.0.0"
    
    async def setup_realtime_subscription(self, table: str, callback) -> Optional[str]:
        """Setup a realtime subscription to a table"""
        # This would be implemented with websockets
        # For now, just return the subscription configuration
        if not self.supabase_url:
            return None
            
        return {
            "event": "*",
            "schema": "public", 
            "table": table,
            "callback": callback
        }
    
    def get_storage_url(self, bucket: str, path: str) -> Optional[str]:
        """Get URL for Supabase Storage file"""
        if not self.supabase_url:
            return None
            
        return f"{self.supabase_url}/storage/v1/object/public/{bucket}/{path}"
    
    async def upload_file(self, bucket: str, path: str, file_data: bytes, content_type: str = "application/octet-stream") -> Optional[str]:
        """Upload file to Supabase Storage"""
        if not self.supabase_url:
            return None
            
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.supabase_url}/storage/v1/object/{bucket}/{path}",
                    headers={
                        **self.get_headers(use_service_key=True),
                        "Content-Type": content_type
                    },
                    content=file_data
                )
                
                if response.status_code == 200:
                    return self.get_storage_url(bucket, path)
                else:
                    logger.error(f"Failed to upload file: {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error uploading file: {e}")
            return None
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Supabase service health"""
        if not self.supabase_url:
            return {
                "status": "unconfigured",
                "message": "Supabase credentials not configured"
            }
        
        try:
            async with httpx.AsyncClient() as client:
                # Test REST API
                response = await client.get(
                    f"{self.supabase_url}/rest/v1/",
                    headers=self.get_headers()
                )
                
                if response.status_code == 200:
                    return {
                        "status": "healthy",
                        "message": "Supabase connection successful",
                        "features": {
                            "database": True,
                            "auth": bool(self.supabase_anon_key),
                            "storage": True,
                            "realtime": True
                        }
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "message": f"Supabase connection failed: {response.status_code}"
                    }
                    
        except Exception as e:
            return {
                "status": "error",
                "message": f"Supabase health check error: {str(e)}"
            }

# Create singleton instance
supabase_service = SupabaseService()

# Utility functions for easy access
async def log_user_action(user_id: str, action: str, resource_type: str = None, resource_id: str = None, metadata: Dict = None):
    """Helper function to log user actions"""
    await supabase_service.log_audit_event({
        "event_type": "user_action",
        "action": action,
        "user_id": user_id,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "metadata": metadata or {},
        "severity": "info"
    })

async def log_system_event(event_type: str, description: str, severity: str = "info", metadata: Dict = None):
    """Helper function to log system events"""
    await supabase_service.log_audit_event({
        "event_type": event_type,
        "action": "system_event",
        "description": description,
        "severity": severity,
        "metadata": metadata or {}
    })
