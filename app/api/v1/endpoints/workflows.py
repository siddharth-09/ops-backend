"""
Workflows API endpoints for OpsFlow Guardian 2.0
"""

from fastapi import APIRouter, HTTPException, Body, Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Dict, Any
from pydantic import BaseModel
import logging
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

# Authentication setup
security = HTTPBearer()

class AuthenticationError(HTTPException):
    def __init__(self, detail: str = "Authentication required to create or manage workflows"):
        super().__init__(status_code=401, detail=detail)

def verify_auth(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify authentication token for workflow operations"""
    if not credentials or not credentials.credentials:
        raise AuthenticationError("Valid authentication token required")
    
    # In production, validate the JWT token here
    # For now, we'll accept any non-empty token
    token = credentials.credentials
    if len(token) < 10:  # Basic validation
        raise AuthenticationError("Invalid authentication token")
    
    return token

def get_user_from_auth(authorization: str = Header(None)):
    """Extract user information from authorization header"""
    if not authorization or not authorization.startswith("Bearer "):
        raise AuthenticationError("Bearer token required for user identification")
    
    token = authorization.replace("Bearer ", "")
    # In production, decode JWT to get user info
    # For now, return mock user info
    return {
        "user_id": str(uuid.uuid4()),
        "email": "user@company.com",
        "organization_id": str(uuid.uuid4()),
        "role": "admin"
    }

router = APIRouter()

# Pydantic models for request validation
class WorkflowCreateRequest(BaseModel):
    name: str = ""
    description: str
    status: str = "pending"
    estimated_duration: int = 300

# In-memory storage for demo (replace with database in production)
workflows_storage: Dict[str, Any] = {}

@router.post("/")
async def create_workflow_direct(
    workflow_data: WorkflowCreateRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    authorization: str = Header(None)
):
    """Create a new workflow directly (Authentication Required)"""
    try:
        # Verify authentication
        verify_auth(credentials)
        user_info = get_user_from_auth(authorization)
        
        logger.info(f"🔐 Creating workflow for authenticated user: {user_info['email']}")
        
        workflow_id = str(uuid.uuid4())[:8]  # Short UUID
        
        # Generate workflow name if not provided
        workflow_name = workflow_data.name or f"Workflow: {workflow_data.description[:50]}"
        
        new_workflow = {
            "id": workflow_id,
            "name": workflow_name,
            "description": workflow_data.description,
            "status": workflow_data.status,
            "created_at": datetime.now().isoformat(),
            "created_by": user_info['user_id'],
            "created_by_email": user_info['email'],
            "organization_id": user_info['organization_id'],
            "risk_level": "medium",
            "estimated_duration": workflow_data.estimated_duration,
            "steps": [
                {
                    "id": f"step-{uuid.uuid4()}",
                    "name": "Initialize workflow",
                    "status": "pending",
                    "description": "Setting up workflow environment"
                },
                {
                    "id": f"step-{uuid.uuid4()}",
                    "name": "Process automation",
                    "status": "pending", 
                    "description": workflow_data.description
                },
                {
                    "id": f"step-{uuid.uuid4()}",
                    "name": "Finalize results",
                    "status": "pending",
                    "description": "Completing workflow execution"
                }
            ],
            "integrations_used": ["automation", "processing"],
            "approval_required": False
        }
        
        # Store the workflow
        workflows_storage[workflow_id] = new_workflow
        
        logger.info(f"Created new workflow: {workflow_name} (ID: {workflow_id})")
        
        return {
            "success": True,
            "data": new_workflow,
            "message": f"Workflow '{workflow_name}' created successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to create workflow: {e}")
        raise HTTPException(status_code=500, detail="Failed to create workflow")


@router.patch("/{workflow_id}")
async def update_workflow_status(workflow_id: str, update_data: Dict[str, Any] = Body(...)):
    """Update workflow status"""
    try:
        if workflow_id not in workflows_storage:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        workflow = workflows_storage[workflow_id]
        
        # Update status if provided
        if "status" in update_data:
            new_status = update_data["status"]
            old_status = workflow["status"]
            
            # Handle workflow control actions
            if new_status == "running" and old_status == "pending":
                # Starting workflow
                workflow["status"] = "running"
                workflow["started_at"] = datetime.now().isoformat()
                # Update first step to running
                if workflow.get("steps") and len(workflow["steps"]) > 0:
                    workflow["steps"][0]["status"] = "running"
                logger.info(f"Started workflow {workflow_id}")
                
            elif new_status == "paused" and old_status == "running":
                # Pausing workflow
                workflow["status"] = "pending"  # Using pending as paused state
                workflow["paused_at"] = datetime.now().isoformat()
                # Update running steps to pending
                for step in workflow.get("steps", []):
                    if step["status"] == "running":
                        step["status"] = "pending"
                logger.info(f"Paused workflow {workflow_id}")
                
            elif new_status == "running" and old_status == "pending":
                # Resuming workflow
                workflow["status"] = "running"
                workflow["resumed_at"] = datetime.now().isoformat()
                # Resume first pending step
                for step in workflow.get("steps", []):
                    if step["status"] == "pending":
                        step["status"] = "running"
                        break
                logger.info(f"Resumed workflow {workflow_id}")
                
            else:
                # Standard status update
                workflow["status"] = new_status
            
            workflow["updated_at"] = datetime.now().isoformat()
        
        return {
            "success": True,
            "data": workflow,
            "message": f"Workflow status updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update workflow {workflow_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update workflow")


@router.delete("/{workflow_id}")
async def delete_workflow(workflow_id: str):
    """Delete a workflow"""
    try:
        if workflow_id not in workflows_storage:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        deleted_workflow = workflows_storage.pop(workflow_id)
        
        logger.info(f"Deleted workflow: {deleted_workflow['name']} (ID: {workflow_id})")
        
        return {
            "success": True,
            "message": f"Workflow '{deleted_workflow['name']}' deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete workflow {workflow_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete workflow")


@router.post("/create")
async def create_workflow(request: Dict[str, Any] = Body(...)):
    """Create a new workflow from natural language description"""
    try:
        description = request.get("description", "")
        user_id = request.get("user_id", "anonymous")
        priority = request.get("priority", "medium")
        
        if not description:
            raise HTTPException(status_code=400, detail="Description is required")
        
        # Mock workflow creation - replace with actual PortiaService call
        workflow_id = str(uuid.uuid4())
        
        # Simulate plan generation
        mock_plan = {
            "id": workflow_id,
            "name": f"Workflow: {description[:50]}...",
            "description": description,
            "status": "pending_approval",
            "risk_level": "medium",
            "estimated_duration": 25,
            "created_at": datetime.utcnow().isoformat(),
            "created_by": user_id,
            "steps": [
                {
                    "id": f"step-{uuid.uuid4()}",
                    "name": "Initialize Process",
                    "description": "Set up initial parameters and validate inputs",
                    "step_order": 1,
                    "tool_integrations": ["internal"],
                    "risk_level": "low",
                    "requires_approval": False,
                    "estimated_duration": 5,
                    "status": "pending"
                },
                {
                    "id": f"step-{uuid.uuid4()}",
                    "name": "Execute Main Actions",
                    "description": "Perform the primary workflow operations",
                    "step_order": 2,
                    "tool_integrations": ["google_workspace", "slack"],
                    "risk_level": "medium",
                    "requires_approval": True,
                    "estimated_duration": 15,
                    "status": "pending"
                },
                {
                    "id": f"step-{uuid.uuid4()}",
                    "name": "Finalize and Notify",
                    "description": "Complete workflow and send notifications",
                    "step_order": 3,
                    "tool_integrations": ["email", "audit"],
                    "risk_level": "low",
                    "requires_approval": False,
                    "estimated_duration": 5,
                    "status": "pending"
                }
            ],
            "approval_required": True,
            "integrations_used": ["google_workspace", "slack", "email"]
        }
        
        return {
            "success": True,
            "message": "Workflow plan created successfully",
            "data": mock_plan
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create workflow: {e}")
        raise HTTPException(status_code=500, detail="Failed to create workflow")


@router.get("/")
async def get_workflows():
    """Get all workflows"""
    try:
        # Convert storage to list format
        workflows_data = list(workflows_storage.values())
        
        return {
            "success": True,
            "data": workflows_data,
            "total": len(workflows_data)
        }
        
    except Exception as e:
        logger.error(f"Failed to get workflows: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve workflows")


@router.get("/templates")
async def get_workflow_templates():
    """Get available workflow templates"""
    try:
        # Mock workflow templates
        templates_data = [
            {
                "id": "template-001",
                "name": "Employee Onboarding",
                "description": "Complete employee onboarding automation",
                "category": "HR",
                "estimated_duration": 45,
                "risk_level": "low",
                "steps": [
                    "Create email account",
                    "Setup Slack access", 
                    "Configure development tools",
                    "Send welcome materials"
                ],
                "integrations": ["google_workspace", "slack", "github", "email"]
            },
            {
                "id": "template-002",
                "name": "Vendor Onboarding",
                "description": "New vendor registration and setup",
                "category": "Procurement",
                "estimated_duration": 90,
                "risk_level": "medium",
                "steps": [
                    "Vendor verification",
                    "Contract generation",
                    "System integration",
                    "Approval workflow"
                ],
                "integrations": ["salesforce", "docusign", "legal_docs"]
            },
            {
                "id": "template-003",
                "name": "Report Generation",
                "description": "Automated business report creation",
                "category": "Analytics",
                "estimated_duration": 15,
                "risk_level": "low",
                "steps": [
                    "Data collection",
                    "Report generation",
                    "Format and style",
                    "Distribution"
                ],
                "integrations": ["database", "reporting_engine", "email"]
            }
        ]
        
        return {
            "success": True,
            "data": templates_data,
            "total": len(templates_data)
        }
        
    except Exception as e:
        logger.error(f"Failed to get workflow templates: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve workflow templates")


@router.get("/{workflow_id}")
async def get_workflow(workflow_id: str):
    """Get specific workflow details"""
    try:
        # Mock workflow detail
        if workflow_id == "workflow-001":
            workflow_data = {
                "id": "workflow-001",
                "name": "Employee Onboarding - John Doe",
                "description": "Complete onboarding process for new software engineer",
                "status": "running",
                "progress": 65,
                "risk_level": "low",
                "created_at": "2025-01-23T08:30:00Z",
                "estimated_completion": "2025-01-23T11:00:00Z",
                "created_by": "hr-manager",
                "current_step_index": 2,
                "steps": [
                    {
                        "id": "step-001",
                        "name": "Create Email Account",
                        "description": "Set up corporate email account",
                        "status": "completed",
                        "completed_at": "2025-01-23T08:45:00Z",
                        "duration": "15m",
                        "tools_used": ["google_workspace"]
                    },
                    {
                        "id": "step-002", 
                        "name": "Setup Slack Access",
                        "description": "Add to company Slack workspace",
                        "status": "completed",
                        "completed_at": "2025-01-23T09:00:00Z",
                        "duration": "10m",
                        "tools_used": ["slack"]
                    },
                    {
                        "id": "step-003",
                        "name": "Development Environment",
                        "description": "Configure development tools and access",
                        "status": "running",
                        "started_at": "2025-01-23T09:00:00Z",
                        "tools_used": ["github", "jira"]
                    },
                    {
                        "id": "step-004",
                        "name": "Send Welcome Package",
                        "description": "Email welcome materials and first-day schedule",
                        "status": "pending",
                        "tools_used": ["email"]
                    }
                ],
                "execution_log": [
                    {
                        "timestamp": "2025-01-23T08:30:00Z",
                        "event": "workflow_started",
                        "message": "Employee onboarding workflow initiated"
                    },
                    {
                        "timestamp": "2025-01-23T08:45:00Z", 
                        "event": "step_completed",
                        "message": "Email account created successfully"
                    },
                    {
                        "timestamp": "2025-01-23T09:00:00Z",
                        "event": "step_started",
                        "message": "Starting development environment setup"
                    }
                ]
            }
            return {"success": True, "data": workflow_data}
        else:
            raise HTTPException(status_code=404, detail="Workflow not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get workflow {workflow_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve workflow")


@router.post("/{workflow_id}/execute")
async def execute_workflow(workflow_id: str):
    """Execute an approved workflow"""
    try:
        # Mock execution start
        execution_data = {
            "workflow_id": workflow_id,
            "execution_id": str(uuid.uuid4()),
            "status": "started",
            "started_at": datetime.utcnow().isoformat(),
            "message": "Workflow execution started successfully"
        }
        
        return {
            "success": True,
            "message": "Workflow execution started",
            "data": execution_data
        }
        
    except Exception as e:
        logger.error(f"Failed to execute workflow {workflow_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to execute workflow")


@router.get("/{workflow_id}/status")
async def get_workflow_status(workflow_id: str):
    """Get real-time workflow status"""
    try:
        # Mock status data
        status_data = {
            "workflow_id": workflow_id,
            "status": "running",
            "progress": 65,
            "current_step": "Setting up development environment",
            "estimated_time_remaining": "25 minutes",
            "last_updated": datetime.utcnow().isoformat()
        }
        
        return {"success": True, "data": status_data}
        
    except Exception as e:
        logger.error(f"Failed to get workflow status {workflow_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get workflow status")
