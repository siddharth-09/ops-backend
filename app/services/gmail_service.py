"""
User-Specific Email Service for OpsFlow Guardian 2.0
Each user configures their own email credentials for sending notifications
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List, Dict, Any
from app.core.config import settings
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

logger = logging.getLogger(__name__)

class UserEmailService:
    """User-specific email service - each user uses their own email configuration"""
    
    def __init__(self, user_id: int, db_session):
        self.user_id = user_id
        self.db = db_session
        self.email_config: Optional = None
        self.user: Optional = None
        self.executor = ThreadPoolExecutor(max_workers=2)
        self._load_user_config()
    
    def _load_user_config(self):
        """Load user's email configuration from database"""
        try:
            from app.models.user import User
            from app.models.user_email_config import UserEmailConfig
            
            # Load user and email config
            self.user = self.db.query(User).filter(User.id == self.user_id).first()
            
            if self.user:
                self.email_config = self.db.query(UserEmailConfig).filter(
                    UserEmailConfig.user_id == self.user_id,
                    UserEmailConfig.is_active == True
                ).first()
                
            if not self.email_config:
                logger.warning(f"No email configuration found for user {self.user_id}")
        except Exception as e:
            logger.error(f"Failed to load email config for user {self.user_id}: {e}")
    
    def is_configured(self) -> bool:
        """Check if user has properly configured email"""
        return bool(self.email_config and self.email_config.is_configured)
    
    def get_config_status(self) -> Dict[str, Any]:
        """Get email configuration status"""
        if not self.email_config:
            return {
                "configured": False,
                "verified": False,
                "email": None,
                "from_name": None
            }
        
        return {
            "configured": self.email_config.is_configured,
            "verified": self.email_config.is_verified,
            "email": self.email_config.email_address,
            "from_name": self.email_config.from_name,
            "last_tested": self.email_config.last_tested.isoformat() if self.email_config.last_tested else None
        }
            return False
        
        try:
            # Test connection
            await self.test_connection()
            logger.info("Gmail SMTP service initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Gmail SMTP service: {e}")
            return False
    
    async def test_connection(self):
        """Test SMTP connection"""
        try:
            context = ssl.create_default_context()
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls(context=context)
            server.login(self.username, self.password)
            server.quit()
            return True
        except Exception as e:
            logger.error(f"SMTP connection test failed: {e}")
            raise
    
    async def send_email(
        self,
        to_emails: List[str],
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """Send email via Gmail SMTP"""
        try:
            if not self.username or not self.password:
                logger.warning("Gmail SMTP not configured - skipping email send")
                return False
            
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{self.from_name} <{self.from_address}>"
            message["To"] = ", ".join(to_emails)
            
            # Add text content
            if text_content:
                text_part = MIMEText(text_content, "plain")
                message.attach(text_part)
            
            # Add HTML content
            html_part = MIMEText(html_content, "html")
            message.attach(html_part)
            
            # Send email
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.username, self.password)
                server.sendmail(self.from_address, to_emails, message.as_string())
            
            logger.info(f"Email sent successfully to {to_emails}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
    
    async def send_workflow_notification(
        self,
        to_email: str,
        workflow_id: str,
        workflow_description: str,
        status: str,
        details: Optional[str] = None
    ) -> bool:
        """Send workflow notification email"""
        
        subject = f"OpsFlow Guardian - Workflow {status.title()}"
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <div style="text-align: center; margin-bottom: 30px;">
                    <h1 style="color: #2563eb; margin: 0;">🚀 OpsFlow Guardian 2.0</h1>
                    <p style="color: #666; margin: 5px 0;">AI-Powered Workflow Automation</p>
                </div>
                
                <div style="background-color: #f8fafc; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                    <h2 style="color: #1e40af; margin-top: 0;">Workflow Update</h2>
                    <p><strong>Status:</strong> <span style="color: #059669;">{status.upper()}</span></p>
                    <p><strong>Workflow ID:</strong> {workflow_id}</p>
                    <p><strong>Description:</strong> {workflow_description}</p>
                    {f'<p><strong>Details:</strong> {details}</p>' if details else ''}
                </div>
                
                <div style="background-color: #eff6ff; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                    <h3 style="color: #1e40af; margin-top: 0;">🤖 Multi-Agent System Active</h3>
                    <ul style="margin: 10px 0; padding-left: 20px;">
                        <li><strong>Planner Agent:</strong> Analyzed and created workflow plan</li>
                        <li><strong>Executor Agent:</strong> Executing automated tasks</li>
                        <li><strong>Auditor Agent:</strong> Recording audit trail</li>
                    </ul>
                </div>
                
                <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb;">
                    <p style="color: #666; font-size: 14px; margin: 0;">
                        This notification was sent automatically by OpsFlow Guardian 2.0<br>
                        Powered by Google Gemini AI | 99.5% cost reduction vs OpenAI
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
OpsFlow Guardian 2.0 - Workflow Update

Status: {status.upper()}
Workflow ID: {workflow_id}
Description: {workflow_description}
{f'Details: {details}' if details else ''}

This notification was sent automatically by OpsFlow Guardian 2.0
Powered by Google Gemini AI
        """
        
        return await self.send_email([to_email], subject, html_content, text_content)
    
    async def send_approval_request(
        self,
        to_email: str,
        workflow_id: str,
        workflow_description: str,
        risk_level: str,
        approval_url: Optional[str] = None
    ) -> bool:
        """Send approval request email for high-risk workflows"""
        
        subject = f"🔐 Approval Required - {risk_level.upper()} Risk Workflow"
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #fef2f2;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); border-left: 5px solid #dc2626;">
                <div style="text-align: center; margin-bottom: 30px;">
                    <h1 style="color: #dc2626; margin: 0;">🔐 Approval Required</h1>
                    <p style="color: #666; margin: 5px 0;">OpsFlow Guardian 2.0</p>
                </div>
                
                <div style="background-color: #fef2f2; padding: 20px; border-radius: 8px; margin-bottom: 20px; border: 1px solid #fecaca;">
                    <h2 style="color: #991b1b; margin-top: 0;">⚠️ High-Risk Workflow Detected</h2>
                    <p><strong>Risk Level:</strong> <span style="color: #dc2626; font-weight: bold;">{risk_level.upper()}</span></p>
                    <p><strong>Workflow ID:</strong> {workflow_id}</p>
                    <p><strong>Description:</strong> {workflow_description}</p>
                </div>
                
                <div style="background-color: #f0fdf4; padding: 20px; border-radius: 8px; margin-bottom: 20px; border: 1px solid #bbf7d0;">
                    <h3 style="color: #166534; margin-top: 0;">🤖 AI Analysis Complete</h3>
                    <p style="margin: 0;">Our Planner Agent has analyzed this workflow and determined it requires human approval due to its risk level. Please review the details and approve if appropriate.</p>
                </div>
                
                {f'''
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{approval_url}" style="background-color: #059669; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block;">
                        ✅ Review & Approve Workflow
                    </a>
                </div>
                ''' if approval_url else ''}
                
                <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb;">
                    <p style="color: #666; font-size: 14px; margin: 0;">
                        This approval request was sent automatically by OpsFlow Guardian 2.0<br>
                        Human-in-the-loop security ensures safe automation
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
OpsFlow Guardian 2.0 - APPROVAL REQUIRED

⚠️ HIGH-RISK WORKFLOW DETECTED

Risk Level: {risk_level.upper()}
Workflow ID: {workflow_id}
Description: {workflow_description}

Our AI Planner Agent has determined this workflow requires human approval.
Please review and approve if appropriate.

{f'Approval URL: {approval_url}' if approval_url else 'Please check the OpsFlow dashboard to approve.'}

This approval request was sent automatically by OpsFlow Guardian 2.0
        """
        
        return await self.send_email([to_email], subject, html_content, text_content)

# Create global instance
gmail_service = GmailSMTPService()
