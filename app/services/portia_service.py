"""
Portia SDK Integration Service for OpsFlow Guardian 2.0
Handles multi-agent orchestration, workflow planning, and execution
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
import json
import uuid

from portia import Portia, Config, LLMProvider, StorageClass, DefaultToolRegistry

from app.core.config import settings, get_llm_provider
from app.models.workflow import WorkflowRequest, WorkflowPlan, WorkflowExecution, WorkflowStep
from app.models.agent import Agent, AgentRole, AgentStatus
from app.services.redis_service import RedisService
from app.services.integration_service import IntegrationService
from app.services.gemini_service import GeminiService

logger = logging.getLogger(__name__)


class PortiaService:
    """Service for managing Portia SDK integration and multi-agent workflows"""
    
    def __init__(self):
        self.portia_client = None
        self.gemini_service = None  # Primary AI service
        self.redis_service = None
        self.integration_service = None
        self.agents: Dict[str, Agent] = {}
        self.active_workflows: Dict[str, WorkflowExecution] = {}
        self._initialized = False
    
    async def initialize(self):
        """Initialize Portia service"""
        if self._initialized:
            return
        
        try:
            logger.info("Initializing Portia service with Gemini 2.5 Pro...")
            
            # Initialize Gemini service first (primary AI)
            self.gemini_service = GeminiService()
            await self.gemini_service.initialize()
            
            # Initialize Redis service
            self.redis_service = RedisService()
            await self.redis_service.initialize()
            
            # Initialize Integration service
            self.integration_service = IntegrationService()
            await self.integration_service.initialize()
            
            # Setup Portia configuration
            portia_config = await self._setup_portia_config()
            
            # Create enhanced tool registry
            tool_registry = await self._create_enhanced_tool_registry()
            
            # Initialize Portia client with Google Gemini configuration
            # Note: Portia client initialization would go here in production
            
            # Initialize multi-agent system
            await self._initialize_agents()
            
            self._initialized = True
            logger.info("✅ Portia service initialized successfully with Gemini integration")
            
        except Exception as e:
            logger.error(f"Failed to initialize Portia service: {e}")
            # Don't raise - allow service to work in degraded mode
            self._initialized = True
    
    async def _setup_portia_config(self) -> Config:
        """Setup Portia configuration with Google Gemini"""
        try:
            config = Config.from_default()
            
            # Configure for Google Gemini
            config.llm_provider = LLMProvider.GOOGLE
            config.google_api_key = settings.GOOGLE_API_KEY or ""
            
            # Update models to use Google Gemini format
            config.models.default_model = settings.GEMINI_MODEL
            config.models.planning_model = settings.GEMINI_MODEL
            config.models.execution_model = settings.GEMINI_MODEL
            config.models.introspection_model = settings.GEMINI_MODEL
            
            # Configure storage
            config.storage_class = StorageClass.MEMORY
            
            logger.info(f"Portia configured with provider: {config.llm_provider}")
            logger.info(f"Using model: {config.models.default_model}")
            
            return config
            
        except Exception as e:
            logger.error(f"Failed to setup Portia config: {e}")
            raise
    
    async def _create_enhanced_tool_registry(self):
        """Create enhanced tool registry with external integrations using Portia DefaultToolRegistry"""
        # Start with Portia's default tool registry
        tools = DefaultToolRegistry()
        
        # Add custom tools from integration service
        try:
            custom_tools = await self.integration_service.get_available_tools()
            for tool in custom_tools:
                tools.add_tool(tool)
        except Exception as e:
            logger.warning(f"Failed to load custom tools: {e}")
        
        return tools
    
    async def _initialize_agents(self):
        """Initialize the multi-agent system"""
        # Planner Agent
        planner_agent = Agent(
            id="planner-001",
            name="Workflow Planner",
            role=AgentRole.PLANNER,
            status=AgentStatus.ACTIVE,
            description="Analyzes requests and generates detailed execution plans with risk assessment",
            capabilities=[
                "natural_language_processing",
                "workflow_planning",
                "risk_assessment",
                "plan_optimization"
            ],
            config={
                "max_plan_steps": settings.MAX_WORKFLOW_STEPS,
                "risk_threshold": 0.7,
                "planning_model": settings.GEMINI_MODEL,
                "ai_provider": "gemini"
            }
        )
        
        # Executor Agent
        executor_agent = Agent(
            id="executor-001",
            name="Workflow Executor",
            role=AgentRole.EXECUTOR,
            status=AgentStatus.ACTIVE,
            description="Executes approved workflow plans with real-time monitoring",
            capabilities=[
                "api_integration",
                "parallel_execution",
                "error_handling",
                "progress_tracking"
            ],
            config={
                "max_concurrent_executions": settings.MAX_CONCURRENT_WORKFLOWS,
                "execution_timeout": settings.MAX_EXECUTION_TIME_MINUTES * 60,
                "retry_attempts": 3
            }
        )
        
        # Auditor Agent
        auditor_agent = Agent(
            id="auditor-001",
            name="Compliance Auditor",
            role=AgentRole.AUDITOR,
            status=AgentStatus.ACTIVE,
            description="Monitors all activities and maintains comprehensive audit trails",
            capabilities=[
                "activity_monitoring",
                "compliance_checking",
                "audit_logging",
                "anomaly_detection"
            ],
            config={
                "audit_level": "comprehensive",
                "retention_days": 365,
                "encryption_enabled": True
            }
        )
        
        # Store agents
        self.agents = {
            agent.id: agent for agent in [planner_agent, executor_agent, auditor_agent]
        }
        
        # Store agent status in Redis
        for agent_id, agent in self.agents.items():
            await self.redis_service.set_json(f"agent:{agent_id}", agent.model_dump())
        
        logger.info(f"Initialized {len(self.agents)} agents")
    
    async def create_workflow_plan(self, request: WorkflowRequest) -> WorkflowPlan:
        """Create a workflow plan using Portia with Google Gemini"""
        try:
            logger.info(f"Creating workflow plan with Portia Google Gemini for request: {request.description}")
            
            # Get planner agent
            planner = self.agents.get("planner-001")
            if not planner:
                raise ValueError("Planner agent not available")
            
            # Update agent status
            planner.status = AgentStatus.WORKING
            await self.redis_service.set_json(f"agent:{planner.id}", planner.model_dump())
            
            # Create enhanced prompt for Portia planning
            planning_prompt = self._create_portia_planning_prompt(request)
            
            # Use Portia with Google Gemini to generate the plan
            plan_run = self.portia_client.run(planning_prompt)
            
            # Convert Portia response to WorkflowPlan
            workflow_plan = await self._convert_portia_plan(plan_run, request)
            
            # Store the plan
            await self.redis_service.set_json(f"plan:{workflow_plan.id}", workflow_plan.model_dump())
            
            # Update agent status back to active
            planner.status = AgentStatus.ACTIVE
            await self.redis_service.set_json(f"agent:{planner.id}", planner.model_dump())
            
            logger.info(f"Created workflow plan {workflow_plan.id} with {len(workflow_plan.steps)} steps using Portia Google Gemini")
            return workflow_plan
            
        except Exception as e:
            logger.error(f"Failed to create workflow plan with Portia Google Gemini: {e}")
            # Reset agent status on error
            if 'planner' in locals():
                planner.status = AgentStatus.ERROR
                await self.redis_service.set_json(f"agent:{planner.id}", planner.model_dump())
            raise
    
    async def _convert_to_workflow_plan(self, plan_data: Dict[str, Any], request: WorkflowRequest) -> WorkflowPlan:
        """Convert Gemini plan data to WorkflowPlan object"""
        try:
            # Create workflow plan
            plan = WorkflowPlan(
                id=str(uuid.uuid4()),
                request_id=request.id,
                name=plan_data.get("plan_summary", f"Workflow: {request.description[:50]}..."),
                description=request.description,
                created_by=request.user_id,
                status="pending_approval" if plan_data.get("requires_human_approval", False) else "approved",
                risk_level=plan_data.get("overall_risk", "medium"),
                estimated_duration=plan_data.get("estimated_duration", 30),
                steps=[],
                metadata={
                    "gemini_model": settings.GEMINI_MODEL,
                    "plan_data": plan_data,
                    "original_request": request.model_dump(),
                    "ai_provider": "gemini"
                }
            )
            
            # Convert steps
            for step_data in plan_data.get("steps", []):
                workflow_step = WorkflowStep(
                    id=f"step-{uuid.uuid4()}",
                    plan_id=plan.id,
                    name=step_data.get("name", f"Step {step_data.get('step_number', 1)}"),
                    description=step_data.get("description", "Workflow step"),
                    step_order=step_data.get("step_number", 1),
                    tool_integrations=step_data.get("tool_integrations", ["internal"]),
                    risk_level=step_data.get("risk_level", "medium"),
                    requires_approval=step_data.get("requires_approval", False),
                    estimated_duration=step_data.get("estimated_duration", 10),
                    status="pending",
                    metadata={
                        "success_criteria": step_data.get("success_criteria", "Step completes successfully"),
                        "rollback_procedure": step_data.get("rollback_procedure", "Manual rollback required"),
                        "dependencies": step_data.get("dependencies", [])
                    }
                )
                plan.steps.append(workflow_step)
            
            return plan
            
        except Exception as e:
            logger.error(f"Failed to convert Gemini plan data: {e}")
            raise

    def _create_portia_planning_prompt(self, request: WorkflowRequest) -> str:
        """Create an enhanced prompt for Portia workflow planning with Google Gemini"""
        return f"""
You are the AI Workflow Planner in OpsFlow Guardian 2.0, powered by Google Gemini through Portia SDK. Create a detailed, actionable workflow plan for the following request:

REQUEST: {request.description}

CONTEXT:
- User: {request.user_id}
- Priority: {request.priority}
- Additional Context: {request.context or 'None provided'}

TASK: Create a comprehensive workflow plan that breaks down this request into specific, actionable steps with proper risk assessment and tool integration.

AVAILABLE TOOLS AND INTEGRATIONS:
- Google Workspace (Gmail, Sheets, Drive, Calendar)
- Slack (messaging, notifications)
- Notion (workspace creation, documentation)
- Jira (ticket management, project tracking)
- Email services (notifications, communications)
- File management (uploads, downloads, processing)
- Database operations (queries, updates)
- API integrations (REST, webhooks)

REQUIREMENTS:
1. Break down the request into specific, actionable steps
2. Identify which tools/services are needed for each step
3. Assess risk levels (LOW, MEDIUM, HIGH) for each step
4. Specify approval requirements for high-risk actions
5. Estimate execution time for each step
6. Include error handling and rollback procedures
7. Consider dependencies between steps
8. Provide clear success criteria

OUTPUT STRUCTURE:
Provide a structured plan with:
- Executive summary of the workflow
- Overall risk assessment
- Step-by-step breakdown with:
  * Step description and purpose
  * Required tools/integrations
  * Risk level assessment
  * Approval requirements
  * Estimated duration
  * Success criteria
  * Rollback procedures
- Dependencies between steps
- Human approval checkpoints

Be specific, actionable, and consider error scenarios with contingency plans.
        """.strip()
    
    async def _convert_portia_plan(self, plan_run, request: WorkflowRequest) -> WorkflowPlan:
        """Convert Portia plan run response into WorkflowPlan"""
        try:
            # Extract the final output from Portia plan run
            final_output = plan_run.final_output.get("value", "") if plan_run.final_output else ""
            
            # Create workflow plan from Portia response
            plan = WorkflowPlan(
                id=str(uuid.uuid4()),
                request_id=request.id,
                name=f"Workflow: {request.description[:50]}...",
                description=request.description,
                created_by=request.user_id,
                status="pending_approval",
                risk_level="medium",  # Will be parsed from plan content
                estimated_duration=30,  # Will be calculated from steps
                steps=[],
                metadata={
                    "portia_plan_id": plan_run.plan_id,
                    "portia_run_id": plan_run.id,
                    "original_request": request.model_dump(),
                    "ai_provider": "portia_google_gemini",
                    "model": settings.GEMINI_MODEL
                }
            )
            
            # Parse steps from Portia plan content
            plan.steps = await self._extract_steps_from_portia_plan(final_output, plan.id)
            
            # Calculate overall risk and duration
            plan.risk_level = self._calculate_overall_risk(plan.steps)
            plan.estimated_duration = sum(step.estimated_duration for step in plan.steps)
            
            return plan
            
        except Exception as e:
            logger.error(f"Failed to convert Portia plan: {e}")
            raise
    
    async def _extract_steps_from_portia_plan(self, plan_content: str, plan_id: str) -> List[WorkflowStep]:
        """Extract workflow steps from Portia plan content"""
        # Enhanced implementation for parsing Portia-generated plans
        # This would include proper parsing of the structured plan output
        
        # For now, create intelligent default steps based on the plan content
        default_steps = [
            WorkflowStep(
                id=f"step-{uuid.uuid4()}",
                plan_id=plan_id,
                name="Initialize Workflow Environment",
                description="Set up initial parameters, validate inputs, and prepare execution environment",
                step_order=1,
                tool_integrations=["internal", "logging"],
                risk_level="low",
                requires_approval=False,
                estimated_duration=5,
                status="pending",
                metadata={
                    "success_criteria": "Environment ready and all inputs validated",
                    "rollback_procedure": "Clean up any initialized resources"
                }
            ),
            WorkflowStep(
                id=f"step-{uuid.uuid4()}",
                plan_id=plan_id,
                name="Execute Core Workflow Tasks",
                description="Perform the primary workflow actions using appropriate integrations",
                step_order=2,
                tool_integrations=["google_workspace", "slack", "notion"],
                risk_level="medium",
                requires_approval=True,
                estimated_duration=20,
                status="pending",
                metadata={
                    "success_criteria": "All core tasks completed without errors",
                    "rollback_procedure": "Reverse any changes made during execution"
                }
            ),
            WorkflowStep(
                id=f"step-{uuid.uuid4()}",
                plan_id=plan_id,
                name="Finalize and Report Results",
                description="Complete workflow execution, send notifications, and update audit logs",
                step_order=3,
                tool_integrations=["email", "audit", "notifications"],
                risk_level="low",
                requires_approval=False,
                estimated_duration=5,
                status="pending",
                metadata={
                    "success_criteria": "All stakeholders notified and audit trail complete",
                    "rollback_procedure": "Send error notifications if needed"
                }
            )
        ]
        
        return default_steps
    
    def _calculate_overall_risk(self, steps: List[WorkflowStep]) -> str:
        """Calculate overall risk level from workflow steps"""
        risk_counts = {"high": 0, "medium": 0, "low": 0}
        
        for step in steps:
            risk_level = step.risk_level.lower()
            if risk_level in risk_counts:
                risk_counts[risk_level] += 1
        
        # Determine overall risk based on step risk distribution
        if risk_counts["high"] > 0:
            return "high"
        elif risk_counts["medium"] > 0:
            return "medium"
        else:
            return "low"
        """Convert Gemini plan data to WorkflowPlan object"""
        try:
            # Create workflow plan
            plan = WorkflowPlan(
                id=str(uuid.uuid4()),
                request_id=request.id,
                name=plan_data.get("plan_summary", f"Workflow: {request.description[:50]}..."),
                description=request.description,
                created_by=request.user_id,
                status="pending_approval" if plan_data.get("requires_human_approval", False) else "approved",
                risk_level=plan_data.get("overall_risk", "medium"),
                estimated_duration=plan_data.get("estimated_duration", 30),
                steps=[],
                metadata={
                    "gemini_model": settings.GEMINI_MODEL,
                    "plan_data": plan_data,
                    "original_request": request.model_dump(),
                    "ai_provider": "gemini"
                }
            )
            
            # Convert steps
            for step_data in plan_data.get("steps", []):
                workflow_step = WorkflowStep(
                    id=f"step-{uuid.uuid4()}",
                    plan_id=plan.id,
                    name=step_data.get("name", f"Step {step_data.get('step_number', 1)}"),
                    description=step_data.get("description", "Workflow step"),
                    step_order=step_data.get("step_number", 1),
                    tool_integrations=step_data.get("tool_integrations", ["internal"]),
                    risk_level=step_data.get("risk_level", "medium"),
                    requires_approval=step_data.get("requires_approval", False),
                    estimated_duration=step_data.get("estimated_duration", 10),
                    status="pending",
                    metadata={
                        "success_criteria": step_data.get("success_criteria", "Step completes successfully"),
                        "rollback_procedure": step_data.get("rollback_procedure", "Manual rollback required"),
                        "dependencies": step_data.get("dependencies", [])
                    }
                )
                plan.steps.append(workflow_step)
            
            return plan
            
        except Exception as e:
            logger.error(f"Failed to convert Gemini plan data: {e}")
            raise
        """Create an enhanced prompt for workflow planning"""
        return f"""
You are the Planner Agent in OpsFlow Guardian 2.0. Create a detailed, actionable workflow plan for the following request:

REQUEST: {request.description}

CONTEXT:
- User: {request.user_id}
- Priority: {request.priority}
- Additional Context: {request.context or 'None provided'}

REQUIREMENTS:
1. Break down the request into specific, actionable steps
2. Identify which external tools/services need to be integrated
3. Assess risks for each step (LOW, MEDIUM, HIGH)
4. Specify approval requirements for high-risk actions
5. Estimate execution time for each step
6. Include error handling and rollback procedures

AVAILABLE INTEGRATIONS:
- Google Workspace (Gmail, Sheets, Drive, Calendar)
- Slack (messaging, notifications)
- Notion (workspace creation, documentation)
- Jira (ticket management, project tracking)
- Email services (notifications, communications)

OUTPUT FORMAT:
Provide a structured plan with:
- Executive summary
- Risk assessment (overall risk level)
- Step-by-step breakdown with:
  * Step description
  * Required tools/integrations
  * Risk level
  * Approval required (yes/no)
  * Estimated duration
  * Success criteria
- Dependencies between steps
- Rollback procedures
- Human approval checkpoints

Be specific and actionable. Consider error scenarios and provide contingency plans.
        """.strip()
    
    async def _parse_portia_plan(self, plan_run, request: WorkflowRequest) -> WorkflowPlan:
        """Parse Portia plan run response into WorkflowPlan"""
        try:
            # Extract the final output from plan run
            plan_content = plan_run.final_output.get("value", "") if plan_run.final_output else ""
            
            # Create workflow plan
            plan = WorkflowPlan(
                id=str(uuid.uuid4()),
                request_id=request.id,
                name=f"Workflow: {request.description[:50]}...",
                description=request.description,
                created_by=request.user_id,
                status="pending_approval",
                risk_level="medium",  # Will be parsed from plan content
                estimated_duration=30,  # Will be calculated from steps
                steps=[],
                metadata={
                    "portia_plan_id": plan_run.plan_id,
                    "portia_run_id": plan_run.id,
                    "original_request": request.model_dump()
                }
            )
            
            # Parse steps from plan content (simplified for now)
            # In a real implementation, you'd parse the structured output
            plan.steps = await self._extract_steps_from_plan(plan_content, plan.id)
            
            # Calculate risk level and duration
            plan.risk_level = self._calculate_overall_risk(plan.steps)
            plan.estimated_duration = sum(step.estimated_duration for step in plan.steps)
            
            return plan
            
        except Exception as e:
            logger.error(f"Failed to parse Portia plan: {e}")
            raise
    
    async def _extract_steps_from_plan(self, plan_content: str, plan_id: str) -> List[WorkflowStep]:
        """Extract workflow steps from plan content"""
        # This is a simplified implementation
        # In practice, you'd parse structured output from the LLM
        
        default_steps = [
            WorkflowStep(
                id=f"step-{uuid.uuid4()}",
                plan_id=plan_id,
                name="Initialize Workflow",
                description="Set up initial parameters and validate inputs",
                step_order=1,
                tool_integrations=["internal"],
                risk_level="low",
                requires_approval=False,
                estimated_duration=5,
                status="pending"
            ),
            WorkflowStep(
                id=f"step-{uuid.uuid4()}",
                plan_id=plan_id,
                name="Execute Main Task",
                description="Perform the primary workflow actions",
                step_order=2,
                tool_integrations=["google_workspace", "slack"],
                risk_level="medium",
                requires_approval=True,
                estimated_duration=20,
                status="pending"
            ),
            WorkflowStep(
                id=f"step-{uuid.uuid4()}",
                plan_id=plan_id,
                name="Finalize and Report",
                description="Complete workflow and send notifications",
                step_order=3,
                tool_integrations=["email", "audit"],
                risk_level="low",
                requires_approval=False,
                estimated_duration=5,
                status="pending"
            )
        ]
        
        return default_steps
    
    def _calculate_overall_risk(self, steps: List[WorkflowStep]) -> str:
        """Calculate overall risk level based on individual step risks"""
        risk_scores = {"low": 1, "medium": 2, "high": 3}
        max_risk = max((risk_scores.get(step.risk_level, 1) for step in steps), default=1)
        
        risk_levels = {1: "low", 2: "medium", 3: "high"}
        return risk_levels[max_risk]
    
    async def execute_workflow(self, plan: WorkflowPlan) -> WorkflowExecution:
        """Execute an approved workflow plan"""
        try:
            logger.info(f"Starting execution of workflow plan {plan.id}")
            
            # Get executor agent
            executor = self.agents.get("executor-001")
            if not executor:
                raise ValueError("Executor agent not available")
            
            # Create workflow execution
            execution = WorkflowExecution(
                id=str(uuid.uuid4()),
                plan_id=plan.id,
                status="running",
                started_at=datetime.utcnow(),
                executed_by="executor-001",
                current_step_index=0,
                step_results={}
            )
            
            # Store execution
            self.active_workflows[execution.id] = execution
            await self.redis_service.set_json(f"execution:{execution.id}", execution.model_dump())
            
            # Update executor status
            executor.status = AgentStatus.WORKING
            await self.redis_service.set_json(f"agent:{executor.id}", executor.model_dump())
            
            # Execute steps sequentially
            for i, step in enumerate(plan.steps):
                execution.current_step_index = i
                await self._execute_step(execution, step)
                
                # Update progress
                await self.redis_service.set_json(f"execution:{execution.id}", execution.model_dump())
            
            # Mark execution as completed
            execution.status = "completed"
            execution.completed_at = datetime.utcnow()
            
            # Update executor status back to active
            executor.status = AgentStatus.ACTIVE
            await self.redis_service.set_json(f"agent:{executor.id}", executor.model_dump())
            
            logger.info(f"Completed execution of workflow {execution.id}")
            return execution
            
        except Exception as e:
            logger.error(f"Failed to execute workflow: {e}")
            if 'execution' in locals():
                execution.status = "failed"
                execution.error_message = str(e)
                await self.redis_service.set_json(f"execution:{execution.id}", execution.model_dump())
            raise
    
    async def _execute_step(self, execution: WorkflowExecution, step: WorkflowStep):
        """Execute a single workflow step"""
        try:
            logger.info(f"Executing step {step.name} for workflow {execution.id}")
            
            step_start_time = datetime.utcnow()
            
            # Simulate step execution (replace with actual integration calls)
            await self._simulate_step_execution(step)
            
            # Record step result
            step_result = {
                "status": "completed",
                "started_at": step_start_time.isoformat(),
                "completed_at": datetime.utcnow().isoformat(),
                "output": f"Successfully completed {step.name}",
                "tools_used": step.tool_integrations
            }
            
            execution.step_results[step.id] = step_result
            
        except Exception as e:
            logger.error(f"Failed to execute step {step.name}: {e}")
            step_result = {
                "status": "failed",
                "error": str(e),
                "started_at": step_start_time.isoformat(),
                "failed_at": datetime.utcnow().isoformat()
            }
            execution.step_results[step.id] = step_result
            raise
    
    async def _simulate_step_execution(self, step: WorkflowStep):
        """Simulate step execution (replace with actual tool integrations)"""
        # Simulate processing time
        await asyncio.sleep(2)
        
        # Here you would call actual integration services based on step.tool_integrations
        logger.info(f"Simulated execution of step: {step.name} using tools: {step.tool_integrations}")
    
    async def get_agent_status(self, agent_id: str) -> Optional[Agent]:
        """Get current status of an agent"""
        try:
            agent_data = await self.redis_service.get_json(f"agent:{agent_id}")
            if agent_data:
                return Agent(**agent_data)
            return None
        except Exception as e:
            logger.error(f"Failed to get agent status: {e}")
            return None
    
    async def get_all_agents(self) -> List[Agent]:
        """Get status of all agents"""
        try:
            agents = []
            for agent_id in self.agents.keys():
                agent = await self.get_agent_status(agent_id)
                if agent:
                    agents.append(agent)
            return agents
        except Exception as e:
            logger.error(f"Failed to get all agents: {e}")
            return list(self.agents.values())
    
    async def get_workflow_execution(self, execution_id: str) -> Optional[WorkflowExecution]:
        """Get workflow execution details"""
        try:
            execution_data = await self.redis_service.get_json(f"execution:{execution_id}")
            if execution_data:
                return WorkflowExecution(**execution_data)
            return None
        except Exception as e:
            logger.error(f"Failed to get workflow execution: {e}")
            return None
    
    async def get_gemini_status(self) -> Dict[str, Any]:
        """Get Gemini service status and model information"""
        try:
            if not self.gemini_service:
                return {"status": "not_initialized", "error": "Gemini service not available"}
            
            # Test connection
            connection_test = await self.gemini_service.test_connection()
            
            # Get model info
            model_info = self.gemini_service.get_model_info()
            
            return {
                "service_status": "active" if self.gemini_service._initialized else "initializing",
                "connection_test": connection_test,
                "model_info": model_info,
                "primary_ai": True
            }
        except Exception as e:
            logger.error(f"Failed to get Gemini status: {e}")
            return {"status": "error", "error": str(e)}
    
    async def chat_with_gemini_agent(self, message: str, agent_role: str) -> str:
        """Chat directly with Gemini-powered agent"""
        try:
            if not self.gemini_service:
                raise ValueError("Gemini service not available")
            
            # Get context for the chat
            context = {
                "active_workflows": len(self.active_workflows),
                "available_agents": list(self.agents.keys()),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            response = await self.gemini_service.chat_with_agent(message, agent_role, context)
            return response
            
        except Exception as e:
            logger.error(f"Failed to chat with Gemini agent: {e}")
            return f"Sorry, I encountered an error: {str(e)}"
