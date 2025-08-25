"""
Example: How to use the User-Specific Email System in OpsFlow Guardian
"""

from typing import Dict, Any
from sqlalchemy.orm import Session
from app.services.user_email_service import get_user_email_service
from app.db.database import get_db

async def send_workflow_completion_notification(
    user_id: int,
    workflow_name: str,
    workflow_status: str,
    details: str,
    recipient_email: str = None
):
    """
    Send workflow completion notification using the user's configured email.
    
    This function demonstrates how to send personalized emails from each user's
    own Gmail account instead of a shared system email.
    
    Args:
        user_id: ID of the user who owns the workflow
        workflow_name: Name of the completed workflow
        workflow_status: Status (SUCCESS, FAILED, etc.)
        details: Detailed information about the workflow
        recipient_email: Optional specific recipient (defaults to user's email)
    """
    
    # Get database session
    db = next(get_db())
    
    try:
        # Get the user's personal email service
        email_service = get_user_email_service(user_id, db)
        
        # Check if user has configured email
        if not email_service.is_configured():
            print(f"⚠️  User {user_id} has not configured email - notification skipped")
            return False
        
        # Use user's email if no specific recipient provided
        if not recipient_email:
            recipient_email = email_service.user.email
        
        # Send the notification from the user's personal Gmail
        success = await email_service.send_workflow_notification(
            recipient_email=recipient_email,
            workflow_name=workflow_name,
            workflow_status=workflow_status,
            details=details
        )
        
        if success:
            print(f"✅ Workflow notification sent from {email_service.email_config.email_address}")
        else:
            print(f"❌ Failed to send notification for user {user_id}")
        
        return success
        
    except Exception as e:
        print(f"❌ Error sending notification: {e}")
        return False
    finally:
        db.close()


async def send_approval_request_to_manager(
    requesting_user_id: int,
    manager_email: str,
    workflow_name: str,
    risk_level: str,
    approval_url: str
):
    """
    Send approval request from the requesting user to their manager.
    
    This shows how approval requests come from the actual user, not a system email.
    
    Args:
        requesting_user_id: ID of user requesting approval
        manager_email: Email of the manager who needs to approve
        workflow_name: Name of workflow requiring approval  
        risk_level: HIGH, MEDIUM, or LOW
        approval_url: URL for manager to approve/reject
    """
    
    db = next(get_db())
    
    try:
        # Get the requesting user's email service
        email_service = get_user_email_service(requesting_user_id, db)
        
        if not email_service.is_configured():
            print(f"⚠️  User {requesting_user_id} needs to configure email first")
            return False
        
        # Send approval request from user's personal email
        success = await email_service.send_approval_request(
            approver_email=manager_email,
            workflow_name=workflow_name,
            risk_level=risk_level,
            approval_url=approval_url,
            workflow_details=f"Approval requested by {email_service.user.full_name}"
        )
        
        if success:
            print(f"✅ Approval request sent from {email_service.email_config.email_address} to {manager_email}")
        else:
            print(f"❌ Failed to send approval request")
        
        return success
        
    except Exception as e:
        print(f"❌ Error sending approval request: {e}")
        return False
    finally:
        db.close()


async def demonstrate_user_email_system():
    """
    Demonstration of how the user-specific email system works
    """
    
    print("🚀 OpsFlow Guardian - User-Specific Email Demo")
    print("=" * 55)
    
    # Example usage scenarios
    scenarios = [
        {
            "title": "📋 Workflow Completion Notification", 
            "description": "User completes a data migration workflow",
            "user_id": 1,
            "workflow": "Database Migration - Production",
            "status": "SUCCESS"
        },
        {
            "title": "🔐 High-Risk Approval Request",
            "description": "User needs approval for server deployment", 
            "user_id": 2,
            "workflow": "Production Server Deployment",
            "risk_level": "HIGH"
        },
        {
            "title": "📊 Audit Report Generation",
            "description": "Weekly compliance audit completed",
            "user_id": 1, 
            "workflow": "Weekly Security Audit",
            "status": "COMPLETED"
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{i}. {scenario['title']}")
        print(f"   {scenario['description']}")
        
        if 'status' in scenario:
            print(f"   📤 Email sent from: user_{scenario['user_id']}@company.com")
            print(f"   📨 Workflow: {scenario['workflow']} - {scenario['status']}")
        elif 'risk_level' in scenario:
            print(f"   📤 Email sent from: user_{scenario['user_id']}@company.com") 
            print(f"   📨 Approval needed: {scenario['workflow']} ({scenario['risk_level']} risk)")
    
    print("\n" + "=" * 55)
    print("💡 KEY BENEFITS:")
    print("   🏢 Professional - emails from actual employees")
    print("   🔒 Secure - each user controls their own credentials") 
    print("   📧 Personal - managers see who's actually requesting")
    print("   ⚖️  Compliant - audit trail tied to real users")
    print("   🚀 Scalable - works for unlimited users")
    
    print(f"\n🎯 PERFECT FOR HACKATHON JUDGING!")
    print("   'Look, when Sarah runs a workflow, the approval email")
    print("    comes from her actual Gmail, not a generic system email!'")


if __name__ == "__main__":
    import asyncio
    asyncio.run(demonstrate_user_email_system())
