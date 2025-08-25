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
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class UserEmailService:
    """User-specific email service - each user uses their own email configuration"""
    
    def __init__(self, user_id: int, db_session: Session):
        self.user_id = user_id
        self.db = db_session
        self.email_config: Optional[Any] = None
        self.user: Optional[Any] = None
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

    async def send_workflow_notification(
        self, 
        recipient_email: str,
        workflow_name: str,
        workflow_status: str,
        details: str,
        workflow_id: Optional[str] = None
    ) -> bool:
        """Send workflow notification using user's email configuration"""
        if not self.is_configured():
            logger.warning(f"Email not configured for user {self.user_id}")
            return False
        
        subject = f"[OpsFlow] {workflow_name} - {workflow_status}"
        
        html_content = self._create_workflow_notification_html(
            workflow_name=workflow_name,
            workflow_status=workflow_status,
            details=details,
            workflow_id=workflow_id
        )
        
        return await self._send_email(recipient_email, subject, html_content)
    
    async def send_approval_request(
        self, 
        approver_email: str,
        workflow_name: str,
        risk_level: str,
        approval_url: str,
        workflow_details: str
    ) -> bool:
        """Send approval request using user's email configuration"""
        if not self.is_configured():
            logger.warning(f"Email not configured for user {self.user_id}")
            return False
        
        subject = f"🔐 Approval Required: {workflow_name} ({risk_level} Risk)"
        
        html_content = self._create_approval_request_html(
            workflow_name=workflow_name,
            risk_level=risk_level,
            approval_url=approval_url,
            workflow_details=workflow_details
        )
        
        return await self._send_email(approver_email, subject, html_content)
    
    async def send_audit_report(
        self,
        recipient_email: str,
        report_title: str,
        audit_summary: str,
        report_data: Dict[str, Any]
    ) -> bool:
        """Send audit report using user's email configuration"""
        if not self.is_configured():
            logger.warning(f"Email not configured for user {self.user_id}")
            return False
        
        subject = f"📊 Audit Report: {report_title}"
        
        html_content = self._create_audit_report_html(
            report_title=report_title,
            audit_summary=audit_summary,
            report_data=report_data
        )
        
        return await self._send_email(recipient_email, subject, html_content)
    
    async def test_connection(self) -> bool:
        """Test the email connection"""
        if not self.is_configured():
            return False
        
        try:
            # Test by sending email to user's own email
            success = await self.send_workflow_notification(
                recipient_email=self.user.email,
                workflow_name="Email Configuration Test",
                workflow_status="SUCCESS",
                details="🎉 Your email configuration is working perfectly! You can now receive workflow notifications from OpsFlow Guardian."
            )
            
            if success:
                # Update last tested timestamp
                self.email_config.last_tested = datetime.utcnow()
                self.email_config.is_verified = True
                self.db.commit()
                
            return success
            
        except Exception as e:
            logger.error(f"Email connection test failed for user {self.user_id}: {e}")
            return False
    
    async def _send_email(self, to_email: str, subject: str, html_content: str) -> bool:
        """Send email using user's configured SMTP settings"""
        if not self.email_config:
            return False
        
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                self.executor, 
                self._send_email_sync, 
                to_email, 
                subject, 
                html_content
            )
        except Exception as e:
            logger.error(f"Failed to send email for user {self.user_id}: {e}")
            return False
    
    def _send_email_sync(self, to_email: str, subject: str, html_content: str) -> bool:
        """Synchronous email sending"""
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.email_config.from_name} <{self.email_config.email_address}>"
            msg['To'] = to_email
            
            # Add plain text version
            plain_text = self._html_to_plain_text(html_content)
            text_part = MIMEText(plain_text, 'plain')
            html_part = MIMEText(html_content, 'html')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.email_config.email_host, self.email_config.email_port) as server:
                if self.email_config.email_use_tls:
                    server.starttls()
                
                server.login(
                    self.email_config.email_address, 
                    self.email_config.decrypt_password()
                )
                server.send_message(msg)
            
            logger.info(f"✅ Email sent successfully from user {self.user_id} ({self.email_config.email_address}) to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send email for user {self.user_id}: {e}")
            return False
    
    def _create_workflow_notification_html(
        self, 
        workflow_name: str, 
        workflow_status: str, 
        details: str, 
        workflow_id: Optional[str] = None
    ) -> str:
        """Create HTML content for workflow notifications"""
        status_color = {
            "SUCCESS": "#4caf50",
            "COMPLETED": "#4caf50", 
            "FAILED": "#f44336",
            "ERROR": "#f44336",
            "RUNNING": "#2196f3",
            "IN_PROGRESS": "#2196f3",
            "PENDING": "#ff9800",
            "WAITING": "#ff9800"
        }.get(workflow_status.upper(), "#607d8b")
        
        status_icon = {
            "SUCCESS": "✅",
            "COMPLETED": "✅",
            "FAILED": "❌", 
            "ERROR": "❌",
            "RUNNING": "🔄",
            "IN_PROGRESS": "🔄",
            "PENDING": "⏳",
            "WAITING": "⏳"
        }.get(workflow_status.upper(), "📋")
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>OpsFlow Workflow Notification</title>
        </head>
        <body style="font-family: 'Segoe UI', Arial, sans-serif; background-color: #f5f7fa; margin: 0; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 8px 32px rgba(0,0,0,0.1);">
                
                <!-- Header -->
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center;">
                    <h1 style="margin: 0; font-size: 28px; font-weight: 600;">🚀 OpsFlow Guardian</h1>
                    <p style="margin: 10px 0 0 0; font-size: 16px; opacity: 0.9;">Automated Workflow Management</p>
                </div>
                
                <!-- Status Banner -->
                <div style="background: {status_color}; color: white; padding: 20px; text-align: center;">
                    <h2 style="margin: 0; font-size: 24px; font-weight: 600;">
                        {status_icon} {workflow_status}
                    </h2>
                    <h3 style="margin: 10px 0 0 0; font-size: 20px; font-weight: 400;">{workflow_name}</h3>
                </div>
                
                <!-- Content -->
                <div style="padding: 30px;">
                    <div style="background: #f8f9fc; padding: 25px; border-radius: 8px; border-left: 4px solid {status_color};">
                        <h4 style="margin: 0 0 15px 0; color: #2c3e50; font-size: 18px;">Workflow Details</h4>
                        <p style="color: #5a6c7d; line-height: 1.6; margin: 0; font-size: 15px;">{details}</p>
                    </div>
                    
                    {f'<p style="margin: 20px 0 10px 0; color: #7f8c8d; font-size: 13px;"><strong>Workflow ID:</strong> {workflow_id}</p>' if workflow_id else ''}
                    
                    <div style="margin-top: 30px; padding: 20px; background: #e3f2fd; border-radius: 8px;">
                        <p style="margin: 0; color: #1976d2; font-size: 14px;">
                            <strong>📧 Notification sent by:</strong> {self.email_config.from_name} ({self.email_config.email_address})
                        </p>
                        <p style="margin: 8px 0 0 0; color: #1976d2; font-size: 13px;">
                            <strong>⏰ Timestamp:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
                        </p>
                    </div>
                </div>
                
                <!-- Footer -->
                <div style="background: #2c3e50; color: white; padding: 20px; text-align: center;">
                    <p style="margin: 0; font-size: 14px; opacity: 0.8;">
                        Powered by <strong>OpsFlow Guardian 2.0</strong> • AI-Driven Workflow Automation
                    </p>
                    <p style="margin: 8px 0 0 0; font-size: 12px; opacity: 0.6;">
                        This is an automated notification from your workflow management system
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_content
    
    def _create_approval_request_html(
        self, 
        workflow_name: str, 
        risk_level: str, 
        approval_url: str,
        workflow_details: str
    ) -> str:
        """Create HTML content for approval requests"""
        
        risk_colors = {
            "HIGH": {"bg": "#d32f2f", "text": "#ffebee"},
            "MEDIUM": {"bg": "#f57c00", "text": "#fff3e0"}, 
            "LOW": {"bg": "#388e3c", "text": "#e8f5e8"}
        }
        
        risk_color = risk_colors.get(risk_level.upper(), risk_colors["MEDIUM"])
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>OpsFlow Approval Request</title>
        </head>
        <body style="font-family: 'Segoe UI', Arial, sans-serif; background-color: #f5f7fa; margin: 0; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 8px 32px rgba(0,0,0,0.1);">
                
                <!-- Header -->
                <div style="background: {risk_color['bg']}; color: white; padding: 30px; text-align: center;">
                    <h1 style="margin: 0; font-size: 32px;">🔐</h1>
                    <h2 style="margin: 15px 0 5px 0; font-size: 24px; font-weight: 600;">APPROVAL REQUIRED</h2>
                    <div style="background: rgba(255,255,255,0.2); display: inline-block; padding: 8px 20px; border-radius: 25px; margin: 10px 0;">
                        <span style="font-weight: bold; font-size: 14px;">{risk_level} RISK WORKFLOW</span>
                    </div>
                </div>
                
                <!-- Content -->
                <div style="padding: 30px;">
                    <h3 style="color: #2c3e50; margin: 0 0 20px 0; font-size: 22px; text-align: center;">
                        {workflow_name}
                    </h3>
                    
                    <div style="background: #f8f9fc; padding: 25px; border-radius: 8px; margin: 20px 0;">
                        <h4 style="margin: 0 0 15px 0; color: #2c3e50;">Workflow Description</h4>
                        <p style="color: #5a6c7d; line-height: 1.6; margin: 0;">{workflow_details}</p>
                    </div>
                    
                    <!-- Action Buttons -->
                    <div style="text-align: center; margin: 40px 0;">
                        <a href="{approval_url}?action=approve" 
                           style="display: inline-block; background: #4caf50; color: white; padding: 15px 40px; 
                                  text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 16px;
                                  margin: 10px; box-shadow: 0 4px 12px rgba(76, 175, 80, 0.3);">
                            ✅ APPROVE WORKFLOW
                        </a>
                        
                        <a href="{approval_url}?action=reject" 
                           style="display: inline-block; background: #f44336; color: white; padding: 15px 40px; 
                                  text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 16px;
                                  margin: 10px; box-shadow: 0 4px 12px rgba(244, 67, 54, 0.3);">
                            ❌ REJECT WORKFLOW
                        </a>
                    </div>
                    
                    <div style="background: #fff3cd; border: 1px solid #ffeaa7; padding: 20px; border-radius: 8px; margin: 20px 0;">
                        <p style="margin: 0; color: #856404; font-size: 14px;">
                            <strong>⚠️ Important:</strong> This workflow requires your approval before execution. 
                            Please review the details carefully before making a decision.
                        </p>
                    </div>
                    
                    <div style="margin-top: 30px; padding: 20px; background: #e3f2fd; border-radius: 8px;">
                        <p style="margin: 0; color: #1976d2; font-size: 14px;">
                            <strong>📧 Request sent by:</strong> {self.email_config.from_name} ({self.email_config.email_address})
                        </p>
                        <p style="margin: 8px 0 0 0; color: #1976d2; font-size: 13px;">
                            <strong>⏰ Timestamp:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
                        </p>
                    </div>
                </div>
                
                <!-- Footer -->
                <div style="background: #2c3e50; color: white; padding: 20px; text-align: center;">
                    <p style="margin: 0; font-size: 14px; opacity: 0.8;">
                        Powered by <strong>OpsFlow Guardian 2.0</strong> • Secure Workflow Management
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_content
    
    def _create_audit_report_html(
        self, 
        report_title: str, 
        audit_summary: str,
        report_data: Dict[str, Any]
    ) -> str:
        """Create HTML content for audit reports"""
        
        # Format report data for display
        report_items = []
        for key, value in report_data.items():
            if isinstance(value, (dict, list)):
                value = str(value)[:100] + "..." if len(str(value)) > 100 else str(value)
            report_items.append(f"<li><strong>{key.replace('_', ' ').title()}:</strong> {value}</li>")
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>OpsFlow Audit Report</title>
        </head>
        <body style="font-family: 'Segoe UI', Arial, sans-serif; background-color: #f5f7fa; margin: 0; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 8px 32px rgba(0,0,0,0.1);">
                
                <!-- Header -->
                <div style="background: linear-gradient(135deg, #6a1b9a 0%, #8e24aa 100%); color: white; padding: 30px; text-align: center;">
                    <h1 style="margin: 0; font-size: 32px;">📊</h1>
                    <h2 style="margin: 15px 0 5px 0; font-size: 24px; font-weight: 600;">AUDIT REPORT</h2>
                    <p style="margin: 10px 0 0 0; font-size: 16px; opacity: 0.9;">System Analysis & Compliance</p>
                </div>
                
                <!-- Content -->
                <div style="padding: 30px;">
                    <h3 style="color: #2c3e50; margin: 0 0 20px 0; font-size: 22px; text-align: center;">
                        {report_title}
                    </h3>
                    
                    <div style="background: #f8f9fc; padding: 25px; border-radius: 8px; margin: 20px 0;">
                        <h4 style="margin: 0 0 15px 0; color: #2c3e50;">Executive Summary</h4>
                        <p style="color: #5a6c7d; line-height: 1.6; margin: 0;">{audit_summary}</p>
                    </div>
                    
                    {f'''
                    <div style="background: #fff; padding: 25px; border-radius: 8px; border: 1px solid #e0e4e7; margin: 20px 0;">
                        <h4 style="margin: 0 0 15px 0; color: #2c3e50;">Report Details</h4>
                        <ul style="color: #5a6c7d; line-height: 1.8; padding-left: 20px;">
                            {"".join(report_items)}
                        </ul>
                    </div>
                    ''' if report_items else ''}
                    
                    <div style="margin-top: 30px; padding: 20px; background: #e8f5e8; border-radius: 8px;">
                        <p style="margin: 0; color: #2e7d32; font-size: 14px;">
                            <strong>✅ Report generated by:</strong> {self.email_config.from_name} ({self.email_config.email_address})
                        </p>
                        <p style="margin: 8px 0 0 0; color: #2e7d32; font-size: 13px;">
                            <strong>⏰ Generated:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
                        </p>
                    </div>
                </div>
                
                <!-- Footer -->
                <div style="background: #2c3e50; color: white; padding: 20px; text-align: center;">
                    <p style="margin: 0; font-size: 14px; opacity: 0.8;">
                        Powered by <strong>OpsFlow Guardian 2.0</strong> • Audit & Compliance Automation
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_content
    
    def _html_to_plain_text(self, html: str) -> str:
        """Convert HTML to plain text for email clients that don't support HTML"""
        import re
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', html)
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text


# Factory function to get user's email service
def get_user_email_service(user_id: int, db_session: Session) -> UserEmailService:
    """Get user-specific email service instance"""
    return UserEmailService(user_id, db_session)


# Legacy support for existing code
class GmailSMTPService:
    """Legacy Gmail service - redirects to user-specific service"""
    
    def __init__(self):
        logger.warning("GmailSMTPService is deprecated. Use UserEmailService instead.")
        pass
    
    async def test_connection(self) -> bool:
        logger.error("Cannot test connection without user context. Use UserEmailService instead.")
        return False
