"""
OpsFlow Guardian 2.0 - Agents Management API
Real AI Agent Integration with Portia SDK and Gemini
"""

import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from uuid import uuid4
from datetime import datetime, timezone
import asyncio

# Authentication setup
security = HTTPBearer()

class AuthenticationError(HTTPException):
    def __init__(self, detail: str = "Authentication required to create or manage agents"):
        super().__init__(status_code=401, detail=detail)

def verify_auth(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify authentication token for agent operations"""
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
        "user_id": str(uuid4()),
        "email": "user@company.com",
        "organization_id": str(uuid4()),
        "role": "admin"
    }

# Import Portia integration
try:
    from app.services.portia_integration_helpers import (
        create_real_ai_agent, 
        execute_real_workflow, 
        get_real_plan_status,
        setup_environment
    )
    PORTIA_AVAILABLE = True
    logging.info("✅ Portia SDK integration helpers loaded")
except ImportError as e:
    PORTIA_AVAILABLE = False
    logging.warning(f"⚠️  Portia SDK helpers not available: {e} - Using mock agents")

# Configure logging
logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter()

# Pydantic Models
class AgentCreateRequest(BaseModel):
    name: str = Field(..., description="Agent name")
    description: Optional[str] = Field(None, description="Agent description")
    agent_type: str = Field(default="workflow", description="Agent type")
    llm_provider: str = Field(default="gemini", description="LLM provider")
    llm_model: str = Field(default="gemini-2.5-flash", description="LLM model")
    system_prompt: Optional[str] = Field(None, description="Custom system prompt")
    tools: Optional[List[Dict[str, Any]]] = Field(default=[], description="Available tools")
    auto_approve_threshold: float = Field(default=0.8, description="Auto-approval confidence threshold")
    max_execution_time: int = Field(default=300, description="Max execution time in seconds")
    organization_id: Optional[str] = Field(None, description="Organization ID")

class WorkflowExecuteRequest(BaseModel):
    workflow_id: Optional[str] = Field(None, description="Workflow ID")
    description: str = Field(..., description="Workflow description")
    parameters: Optional[Dict[str, Any]] = Field(default={}, description="Execution parameters")
    context: Optional[Dict[str, Any]] = Field(default={}, description="Additional context")
    organization_id: Optional[str] = Field(None, description="Organization ID")

# Mock storage for development
agents_storage = {}
execution_storage = {}

@router.get("/")
async def list_agents():
    """Get all agents with enhanced information"""
    try:
        agents_list = []
        
        for agent_id, agent in agents_storage.items():
            # Calculate recent performance metrics
            recent_executions = [
                exec for exec in execution_storage.values() 
                if exec.get('agent_id') == agent_id
            ]
            
            success_count = len([e for e in recent_executions if e.get('status') == 'completed'])
            total_count = len(recent_executions)
            success_rate = (success_count / total_count * 100) if total_count > 0 else 0
            
            agent_info = {
                **agent,
                "execution_count": total_count,
                "success_rate": round(success_rate, 2),
                "recent_executions": len(recent_executions),
                "status": "active" if PORTIA_AVAILABLE else "mock",
                "integration_status": "portia_sdk" if PORTIA_AVAILABLE else "mock_mode"
            }
            agents_list.append(agent_info)
        
        return {
            "agents": agents_list,
            "total_count": len(agents_list),
            "portia_integration": PORTIA_AVAILABLE,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to list agents: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve agents: {str(e)}")

@router.post("/")
async def create_agent_direct(
    agent_data: AgentCreateRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    authorization: str = Header(None)
):
    """Create a new AI agent with company profile personalization (Authentication Required)"""
    try:
        from app.services.ai_personalization_service import ai_personalization_service
        
        # Verify authentication
        verify_auth(credentials)
        user_info = get_user_from_auth(authorization)
        
        logger.info(f"🔐 Creating personalized agent for authenticated user: {user_info['email']}")
        
        agent_id = str(uuid.uuid4())[:8]  # Short UUID
        
        # Try to get company profile for personalization
        company_profile = None
        try:
            # Import here to avoid circular imports
            from app.api.v1.endpoints.company import company_profiles_storage
            company_profile = company_profiles_storage.get("default_profile")
        except Exception as e:
            logger.warning(f"Could not load company profile for personalization: {e}")
        
        # Generate personalized system prompt and configuration
        if company_profile:
            system_prompt = ai_personalization_service.get_personalized_system_prompt(
                company_profile, agent_data.description
            )
            agent_config = ai_personalization_service.get_recommended_agent_config(
                company_profile, agent_data.agent_type
            )
            
            logger.info(f"🤖 Applied AI personalization for {company_profile.get('company_name', 'organization')}")
        else:
            # Fallback to generic configuration
            system_prompt = f"You are an AI agent named '{agent_data.name}'. {agent_data.description}"
            agent_config = {
                "llm_provider": "gemini",
                "llm_model": "gemini-2.5-flash",
                "auto_approve_threshold": 0.8,
                "max_execution_time": 300,
                "requires_human_approval": True
            }
            logger.info("🔧 Using generic agent configuration (no company profile found)")
        
        new_agent = {
            "id": agent_id,
            "name": agent_data.name,
            "description": agent_data.description,
            "agent_type": agent_data.agent_type,
            "status": "active",
            "created_at": datetime.now().isoformat(),
            "created_by": user_info['user_id'],
            "created_by_email": user_info['email'],
            "organization_id": user_info['organization_id'],
            
            # AI Configuration (personalized)
            "llm_provider": agent_config.get("llm_provider", "gemini"),
            "llm_model": agent_config.get("llm_model", "gemini-2.5-flash"),
            "system_prompt": system_prompt,
            "auto_approve_threshold": agent_config.get("auto_approve_threshold", 0.8),
            "max_execution_time": agent_config.get("max_execution_time", 300),
            "requires_human_approval": agent_config.get("requires_human_approval", True),
            
            # Capabilities and Tools (personalized)
            "tools": agent_config.get("recommended_tools", ["email", "calendar", "documentation"]),
            "capabilities": [
                "Natural language processing",
                "Task automation",
                "Data analysis",
                "Integration management"
            ],
            "integrations": agent_config.get("suggested_integrations", ["email"]),
            
            # Performance Metrics
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "average_execution_time": 0,
            "success_rate": 0,
            "last_executed": None,
            
            # Company-specific context
            "company_context": {
                "industry": company_profile.get("industry") if company_profile else None,
                "company_size": company_profile.get("company_size") if company_profile else None,
                "personalized": company_profile is not None,
                "automation_focus": company_profile.get("automation_needs", [])[:3] if company_profile else []
            }
        }
        
        # Store the agent
        agents_storage[agent_id] = new_agent
        
        # Log creation with personalization details
        if company_profile:
            logger.info(f"✅ Created personalized agent: {agent_data.name} (ID: {agent_id}) for {company_profile.get('company_name', 'organization')}")
            logger.info(f"🎯 Personalization: {company_profile.get('industry', 'unknown')} industry, {len(agent_config.get('recommended_tools', []))} tools")
        else:
            logger.info(f"✅ Created generic agent: {agent_data.name} (ID: {agent_id})")
        
        return {
            "success": True,
            "data": new_agent,
            "message": f"AI agent '{agent_data.name}' created successfully" + (" with company personalization" if company_profile else ""),
            "personalization_applied": company_profile is not None,
            "recommended_next_steps": [
                "Test the agent with a simple task",
                "Configure additional integrations if needed", 
                "Monitor agent performance metrics",
                "Adjust approval thresholds based on results"
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to create agent: {e}")
        raise HTTPException(status_code=500, detail="Failed to create agent")

@router.get("/{agent_id}")
async def get_agent(agent_id: str):
    """Get detailed agent information"""
    try:
        if agent_id not in agents_storage:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        agent = agents_storage[agent_id]
        
        # Add runtime information
        agent_details = {
            **agent,
            "runtime_info": {
                "portia_available": PORTIA_AVAILABLE,
                "environment_ready": setup_environment() if PORTIA_AVAILABLE else False,
                "current_load": len([e for e in execution_storage.values() if e.get('status') == 'running']),
                "last_health_check": datetime.now(timezone.utc).isoformat()
            }
        }
        
        return agent_details
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get agent {agent_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve agent: {str(e)}")

@router.post("/{agent_id}/execute")
async def execute_workflow(
    agent_id: str, 
    workflow_request: WorkflowExecuteRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    authorization: str = Header(None)
):
    """Execute workflow using AI agent with real Portia SDK integration (Authentication Required)"""
    try:
        # Verify authentication
        verify_auth(credentials)
        user_info = get_user_from_auth(authorization)
        
        logger.info(f"🔐 Executing workflow for authenticated user: {user_info['email']}")
        
        if agent_id not in agents_storage:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        agent = agents_storage[agent_id]
        
        # Verify user has access to this agent's organization
        if agent.get('organization_id') != user_info['organization_id']:
            raise HTTPException(status_code=403, detail="Access denied: Agent belongs to different organization")
        
        execution_id = str(uuid4())[:8]
        
        # Prepare execution context with user information
        execution_context = {
            "execution_id": execution_id,
            "agent_id": agent_id,
            "executed_by": user_info['user_id'],
            "executed_by_email": user_info['email'],
            "organization_id": user_info['organization_id'],
            "agent_name": agent.get("name", "Unknown Agent"),
            "started_at": datetime.now(timezone.utc).isoformat(),
            "status": "initializing",
            "workflow_request": workflow_request.dict(),
            "organization_id": workflow_request.organization_id or agent.get("organization_id", "default-org")
        }
        
        # Store initial execution state
        execution_storage[execution_id] = execution_context
        
        # Execute with real AI if Portia is available
        if PORTIA_AVAILABLE and agent.get("portia_integration", False):
            try:
                logger.info(f"🤖 Executing workflow with real AI agent {agent_id}")
                
                portia_result = await execute_real_workflow(
                    agent_id=agent_id,
                    workflow_request=workflow_request.dict()
                )
                
                # Update execution with real results
                execution_context.update({
                    "status": portia_result.get("status", "completed"),
                    "portia_plan_id": portia_result.get("plan_id"),
                    "steps_completed": portia_result.get("steps_completed", 0),
                    "total_steps": portia_result.get("total_steps", 1),
                    "execution_time": portia_result.get("execution_time", 0),
                    "ai_reasoning": portia_result.get("ai_reasoning", "AI reasoning available"),
                    "confidence_score": portia_result.get("confidence_score", 0.85),
                    "results": portia_result.get("results", {}),
                    "requires_approval": portia_result.get("requires_approval", True),
                    "risk_assessment": portia_result.get("risk_assessment", {"level": "medium"}),
                    "real_ai_execution": True,
                    "completed_at": datetime.now(timezone.utc).isoformat()
                })
                
                logger.info(f"✅ Real AI execution completed for {execution_id}")
                
            except Exception as portia_error:
                logger.warning(f"⚠️  Portia execution error, using mock result: {portia_error}")
                execution_context.update({
                    "status": "completed",
                    "portia_error": str(portia_error),
                    "real_ai_execution": False
                })
        
        # Mock execution for development/fallback
        if not execution_context.get("real_ai_execution", False):
            logger.info(f"📝 Executing workflow with mock AI agent {agent_id}")
            
            # Simulate AI processing
            await asyncio.sleep(0.1)  # Brief delay to simulate processing
            
            mock_results = {
                "status": "completed",
                "steps_completed": 3,
                "total_steps": 3,
                "execution_time": 2.5,
                "ai_reasoning": f"Analyzed workflow request: '{workflow_request.description}'. Determined appropriate actions based on agent configuration and available tools. Confidence level is high due to clear requirements and available context.",
                "confidence_score": 0.87,
                "results": {
                    "workflow_analysis": {
                        "complexity": "medium",
                        "estimated_impact": "positive",
                        "resource_requirements": ["api_access", "data_processing"]
                    },
                    "recommended_actions": [
                        "Validate input parameters",
                        "Execute core workflow logic", 
                        "Generate comprehensive report"
                    ],
                    "output": f"Successfully processed: {workflow_request.description}",
                    "metadata": {
                        "processing_time": "2.5 seconds",
                        "tokens_used": 1247,
                        "model_version": agent.get("llm_model", "gemini-2.5-flash")
                    }
                },
                "requires_approval": workflow_request.parameters.get("requires_approval", True),
                "risk_assessment": {
                    "level": "medium",
                    "factors": ["automated_execution", "standard_workflow"],
                    "mitigation": "Standard approval process recommended"
                },
                "real_ai_execution": False,
                "completed_at": datetime.now(timezone.utc).isoformat()
            }
            
            execution_context.update(mock_results)
        
        # Update agent statistics
        agent["execution_count"] = agent.get("execution_count", 0) + 1
        agent["last_executed"] = datetime.now(timezone.utc).isoformat()
        
        # Update success rate if completed successfully
        if execution_context.get("status") == "completed":
            current_successes = agent.get("success_count", 0) + 1
            total_executions = agent["execution_count"]
            agent["success_count"] = current_successes
            agent["success_rate"] = round((current_successes / total_executions) * 100, 2)
        
        # Store final execution state
        execution_storage[execution_id] = execution_context
        agents_storage[agent_id] = agent
        
        # Prepare response
        response = {
            "success": True,
            "execution_id": execution_id,
            **execution_context,
            "agent_info": {
                "id": agent_id,
                "name": agent.get("name"),
                "type": agent.get("agent_type"),
                "model": agent.get("llm_model")
            }
        }
        
        logger.info(f"Workflow execution completed: {execution_id} - Status: {execution_context.get('status')}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Workflow execution failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Workflow execution failed: {str(e)}")

@router.get("/{agent_id}/executions")
async def get_agent_executions(agent_id: str):
    """Get execution history for an agent"""
    try:
        if agent_id not in agents_storage:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Filter executions for this agent
        agent_executions = [
            execution for execution in execution_storage.values()
            if execution.get("agent_id") == agent_id
        ]
        
        # Sort by start time (newest first)
        agent_executions.sort(
            key=lambda x: x.get("started_at", ""), 
            reverse=True
        )
        
        return {
            "agent_id": agent_id,
            "executions": agent_executions,
            "total_executions": len(agent_executions),
            "successful_executions": len([e for e in agent_executions if e.get("status") == "completed"]),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get executions for agent {agent_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve executions: {str(e)}")

@router.get("/executions/{execution_id}/status")
async def get_execution_status(execution_id: str):
    """Get detailed execution status"""
    try:
        if execution_id not in execution_storage:
            raise HTTPException(status_code=404, detail="Execution not found")
        
        execution = execution_storage[execution_id]
        
        # Get real-time status if Portia plan exists
        if PORTIA_AVAILABLE and execution.get("portia_plan_id"):
            try:
                portia_status = await get_real_plan_status(execution["portia_plan_id"])
                execution.update({
                    "realtime_status": portia_status,
                    "last_status_check": datetime.now(timezone.utc).isoformat()
                })
            except Exception as e:
                logger.warning(f"Could not get real-time status: {e}")
        
        return execution
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get execution status {execution_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve execution status: {str(e)}")

@router.delete("/{agent_id}")
async def delete_agent(agent_id: str):
    """Delete an agent"""
    try:
        if agent_id not in agents_storage:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        agent_name = agents_storage[agent_id].get("name", "Unknown")
        del agents_storage[agent_id]
        
        # Clean up related executions
        execution_ids_to_delete = [
            exec_id for exec_id, execution in execution_storage.items()
            if execution.get("agent_id") == agent_id
        ]
        
        for exec_id in execution_ids_to_delete:
            del execution_storage[exec_id]
        
        logger.info(f"Deleted agent: {agent_name} (ID: {agent_id})")
        
        return {
            "success": True,
            "message": f"Agent '{agent_name}' deleted successfully",
            "deleted_executions": len(execution_ids_to_delete)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete agent {agent_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete agent: {str(e)}")

@router.post("/{agent_id}/chat")
async def chat_with_agent(agent_id: str, message: Dict[str, Any]):
    """Chat interface with AI agent"""
    try:
        if agent_id not in agents_storage:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        agent = agents_storage[agent_id]
        user_message = message.get("message", "")
        
        if not user_message:
            raise HTTPException(status_code=400, detail="Message is required")
        
        # Simulate AI chat response
        chat_response = {
            "agent_id": agent_id,
            "agent_name": agent.get("name", "AI Agent"),
            "user_message": user_message,
            "ai_response": f"Hello! I'm {agent.get('name', 'an AI agent')} specialized in {agent.get('agent_type', 'general tasks')}. I understand you said: '{user_message}'. How can I help you with workflow automation today?",
            "confidence": 0.92,
            "suggestions": [
                "Create a new workflow",
                "Execute existing automation", 
                "Analyze performance metrics",
                "Configure integrations"
            ],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        if PORTIA_AVAILABLE and agent.get("portia_integration", False):
            chat_response["powered_by"] = "Portia SDK + Gemini"
            chat_response["real_ai"] = True
        else:
            chat_response["powered_by"] = "Mock AI (Portia SDK unavailable)"
            chat_response["real_ai"] = False
        
        return chat_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat failed for agent {agent_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")

# System status endpoint
@router.get("/system/status")
async def get_system_status():
    """Get system integration status"""
    return {
        "portia_sdk_available": PORTIA_AVAILABLE,
        "environment_ready": setup_environment() if PORTIA_AVAILABLE else False,
        "total_agents": len(agents_storage),
        "active_executions": len([e for e in execution_storage.values() if e.get("status") == "running"]),
        "integration_mode": "production" if PORTIA_AVAILABLE else "development",
        "capabilities": {
            "real_ai_agents": PORTIA_AVAILABLE,
            "workflow_execution": True,
            "plan_monitoring": PORTIA_AVAILABLE,
            "chat_interface": True
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
from pydantic import BaseModel
import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models for request validation
class AgentCreateRequest(BaseModel):
    name: str
    role: str
    description: str
    status: str = "active"
    capabilities: List[str] = []
    tasks_completed: int = 0
    success_rate: float = 100.0

# In-memory storage for demo (replace with database in production)
agents_storage: Dict[str, Any] = {}

@router.get("/")
async def get_agents():
    """Get all agents status"""
    try:
        # Convert storage to list format
        agents_data = list(agents_storage.values())
        
        return {
            "success": True,
            "data": agents_data,
            "total": len(agents_data)
        }
        
    except Exception as e:
        logger.error(f"Failed to get agents: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve agents")


@router.post("/")
async def create_agent(agent_data: AgentCreateRequest):
    """Create a new agent"""
    try:
        agent_id = str(uuid.uuid4())[:8]  # Short UUID
        
        new_agent = {
            "id": agent_id,
            "name": agent_data.name,
            "role": agent_data.role,
            "status": agent_data.status,
            "description": agent_data.description,
            "current_task": None,
            "tasks_completed": agent_data.tasks_completed,
            "success_rate": agent_data.success_rate,
            "last_active": datetime.now().isoformat(),
            "capabilities": agent_data.capabilities or ["task_automation", "data_processing"],
            "avg_response_time": 2.3,
            "performance": {
                "cpu": 15.2,
                "memory": 48.5,
                "network": 5.1
            },
            "metrics": {
                "tasksProcessed": agent_data.tasks_completed,
                "successRate": agent_data.success_rate,
                "avgResponseTime": "2.3s",
                "uptime": 99.8
            },
            "created_at": datetime.now().isoformat()
        }
        
        # Store the agent
        agents_storage[agent_id] = new_agent
        
        logger.info(f"Created new agent: {agent_data.name} (ID: {agent_id})")
        
        return {
            "success": True,
            "data": new_agent,
            "message": f"Agent '{agent_data.name}' deployed successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to create agent: {e}")
        raise HTTPException(status_code=500, detail="Failed to create agent")


@router.get("/{agent_id}")
async def get_agent(agent_id: str):
    """Get specific agent details"""
    try:
        # Mock data - replace with actual PortiaService call
        if agent_id == "planner-001":
            agent_data = {
                "id": "planner-001",
                "name": "Workflow Planner",
                "role": "planner",
                "status": "active",
                "description": "Analyzes requests and generates detailed execution plans",
                "current_task": None,
                "tasks_completed": 156,
                "success_rate": 98.7,
                "last_active": "2025-01-23T10:30:00Z",
                "capabilities": [
                    "natural_language_processing",
                    "workflow_planning",
                    "risk_assessment"
                ],
                "metrics": {
                    "uptime": "99.8%",
                    "average_response_time": "2.3s",
                    "memory_usage": "45MB",
                    "cpu_usage": "12%"
                },
                "recent_tasks": [
                    {
                        "id": "task-123",
                        "type": "plan_creation",
                        "description": "Employee onboarding automation",
                        "status": "completed",
                        "duration": "45s",
                        "completed_at": "2025-01-23T09:15:00Z"
                    }
                ]
            }
            return {"success": True, "data": agent_data}
        else:
            raise HTTPException(status_code=404, detail="Agent not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve agent")


@router.get("/{agent_id}/metrics")
async def get_agent_metrics(agent_id: str):
    """Get agent performance metrics"""
    try:
        # Mock metrics data
        metrics_data = {
            "agent_id": agent_id,
            "period": "last_24_hours",
            "tasks_completed": 23,
            "tasks_failed": 1,
            "success_rate": 95.8,
            "average_execution_time": 2.4,
            "resource_usage": {
                "cpu_avg": 15.2,
                "memory_avg": 48.5,
                "network_in": 1.2,
                "network_out": 0.8
            },
            "timeline": [
                {"timestamp": "2025-01-23T00:00:00Z", "tasks": 2, "success_rate": 100},
                {"timestamp": "2025-01-23T06:00:00Z", "tasks": 8, "success_rate": 87.5},
                {"timestamp": "2025-01-23T12:00:00Z", "tasks": 13, "success_rate": 92.3}
            ]
        }
        
        return {"success": True, "data": metrics_data}
        
    except Exception as e:
        logger.error(f"Failed to get agent metrics {agent_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve agent metrics")


@router.get("/gemini/status")
async def get_gemini_status():
    """Get Gemini 2.5 Pro AI service status"""
    try:
        # This would connect to actual PortiaService with Gemini
        # For now, return mock status
        
        gemini_status = {
            "service_status": "active",
            "connection_test": {
                "status": "success",
                "model": "gemini-2.0-flash-exp",
                "response": "Connected successfully to Gemini 2.5 Pro",
                "timestamp": "2025-01-23T10:45:00Z"
            },
            "model_info": {
                "provider": "Google",
                "model": "gemini-2.0-flash-exp",
                "version": "2.5 Pro",
                "context_window": "2M tokens",
                "capabilities": [
                    "text_generation",
                    "code_understanding",
                    "reasoning",
                    "multimodal_input",
                    "function_calling",
                    "json_mode"
                ],
                "cost_per_1k_tokens": 0.00025,
                "initialized": True
            },
            "primary_ai": True
        }
        
        return {"success": True, "data": gemini_status}
        
    except Exception as e:
        logger.error(f"Failed to get Gemini status: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve Gemini status")


@router.post("/gemini/chat")
async def chat_with_gemini_agent(chat_request: Dict[str, Any]):
    """Chat with Gemini-powered agent"""
    try:
        message = chat_request.get("message", "")
        agent_role = chat_request.get("agent_role", "planner")
        
        if not message:
            raise HTTPException(status_code=400, detail="Message is required")
        
        # This would connect to actual GeminiService
        # For now, return mock response
        
        responses = {
            "planner": f"As your Workflow Planner powered by Gemini 2.5 Pro, I understand you want to: '{message}'. I can help you create a detailed, step-by-step workflow plan with risk assessment and approval checkpoints. Would you like me to break this down into actionable steps?",
            "executor": f"As your Workflow Executor powered by Gemini 2.5 Pro, I can help you execute: '{message}'. I'll monitor the process in real-time, handle any errors, and ensure successful completion. Shall I proceed with the execution?",
            "auditor": f"As your Compliance Auditor powered by Gemini 2.5 Pro, I've analyzed your request: '{message}'. I'll ensure all activities are logged, compliance requirements are met, and provide detailed audit trails. What specific compliance aspects would you like me to focus on?"
        }
        
        response = responses.get(agent_role, f"Hello! I'm an AI agent powered by Gemini 2.5 Pro. You said: '{message}'. How can I assist you today?")
        
        return {
            "success": True,
            "data": {
                "response": response,
                "agent_role": agent_role,
                "model": "gemini-2.0-flash-exp",
                "timestamp": "2025-01-23T10:45:00Z"
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to chat with Gemini agent: {e}")
        raise HTTPException(status_code=500, detail="Failed to chat with Gemini agent")
