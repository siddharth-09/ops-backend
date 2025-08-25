"""
External Integration Service for OpsFlow Guardian 2.0
Handles connections to external tools and services
"""

import logging
from typing import Dict, List, Any, Optional
import httpx
from app.core.config import settings
from app.services.gmail_service import gmail_service

logger = logging.getLogger(__name__)


class IntegrationService:
    """Service for managing external tool integrations"""
    
    def __init__(self):
        self.integrations: Dict[str, Any] = {}
        self._initialized = False
    
    async def initialize(self):
        """Initialize integration service"""
        if self._initialized:
            return
        
        try:
            logger.info("Initializing integration service...")
            
            # Initialize available integrations
            await self._setup_integrations()
            
            self._initialized = True
            logger.info("Integration service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize integration service: {e}")
            # Don't raise - allow service to continue with basic functionality
            self._initialized = True
    
    async def _setup_integrations(self):
        """Setup available integrations"""
        # Google Workspace
        if settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET:
            self.integrations["google_workspace"] = {
                "name": "Google Workspace",
                "tools": ["gmail", "sheets", "drive", "calendar"],
                "status": "available"
            }
        
        # Slack
        if settings.SLACK_BOT_TOKEN:
            self.integrations["slack"] = {
                "name": "Slack",
                "tools": ["messaging", "notifications", "channels"],
                "status": "available"
            }
        
        # Notion
        if settings.NOTION_TOKEN:
            self.integrations["notion"] = {
                "name": "Notion",
                "tools": ["pages", "databases", "blocks"],
                "status": "available"
            }
        
        # Jira
        if settings.JIRA_SERVER and settings.JIRA_API_TOKEN:
            self.integrations["jira"] = {
                "name": "Jira",
                "tools": ["issues", "projects", "workflows"],
                "status": "available"
            }
        
        # Email (Gmail SMTP)
        if settings.EMAIL_HOST_USER and settings.EMAIL_HOST_PASSWORD:
            self.integrations["email"] = {
                "name": "Gmail Email Service",
                "tools": ["send", "notifications", "approvals"],
                "status": "available"
            }
        elif settings.EMAIL_HOST_USER:  # Partial configuration
            self.integrations["email"] = {
                "name": "Email Service (Needs Password)",
                "tools": ["send", "notifications"],
                "status": "partial"
            }
        
        logger.info(f"Initialized {len(self.integrations)} integrations")
    
    async def get_available_tools(self):
        """Get available tools for Portia"""
        # This would return actual Portia Tool objects
        # For now, return empty list
        return []
    
    async def get_integrations_status(self) -> Dict[str, Any]:
        """Get status of all integrations"""
        return self.integrations
    
    async def test_integration(self, integration_name: str) -> bool:
        """Test an integration connection"""
        try:
            if integration_name not in self.integrations:
                return False
            
            # Add specific tests for each integration
            if integration_name == "slack" and settings.SLACK_BOT_TOKEN:
                return await self._test_slack_connection()
            elif integration_name == "google_workspace" and settings.GOOGLE_CLIENT_ID:
                return await self._test_google_connection()
            elif integration_name == "email":
                return await self._test_gmail_connection()
            # Add more integration tests
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to test integration {integration_name}: {e}")
            return False
    
    async def _test_slack_connection(self) -> bool:
        """Test Slack connection"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://slack.com/api/auth.test",
                    headers={"Authorization": f"Bearer {settings.SLACK_BOT_TOKEN}"}
                )
                return response.status_code == 200 and response.json().get("ok", False)
        except Exception as e:
            logger.error(f"Slack connection test failed: {e}")
            return False
    
    async def _test_google_connection(self) -> bool:
        """Test Google connection"""
        # This would require proper OAuth flow implementation
        # For now, just return True if credentials are configured
        return bool(settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET)
    
    async def _test_gmail_connection(self) -> bool:
        """Test Gmail SMTP connection."""
        try:
            from .gmail_service import GmailSMTPService
            gmail_service = GmailSMTPService()
            return await gmail_service.test_connection()
        except Exception as e:
            logger.error(f"Gmail connection test failed: {e}")
            return False
