"""
OpsFlow Guardian 2.0 - Portia SDK Integration
Real AI Agent Implementation with Gemini 2.5 Models
"""

import os
import asyncio
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timezone
import uuid

# Portia SDK imports
from portia import Agent, Message, Plan, Tool, ToolCall, ToolResult
from portia.provider.gemini import GeminiProvider
from portia.storage.memory import MemoryStorage

# Google Gemini imports  
import google.generativeai as genai
from google.generativeai.types import GenerationConfig, SafetySetting, HarmCategory, HarmBlockThreshold

# FastAPI and Pydantic
from pydantic import BaseModel, Field
from fastapi import HTTPException

# Configure logging
logger = logging.getLogger(__name__)

class OpsFlowPortiaManager:
    """
    Portia SDK manager for OpsFlow Guardian 2.0
    Handles AI agent creation, execution, and plan management
    """
    
    def __init__(self):
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')
        self.portia_storage = MemoryStorage()  # Can be upgraded to Redis/PostgreSQL
        self.agents: Dict[str, Agent] = {}
        self.active_plans: Dict[str, Plan] = {}
        
        # Initialize Gemini API
        if self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
            logger.info("✅ Gemini API configured successfully")
        else:
            logger.warning("⚠️  GEMINI_API_KEY not found - AI features will be limited")
    
    async def create_ai_agent(
        self, 
        organization_id: str,
        agent_config: Dict[str, Any],
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Create a new AI agent using Portia SDK with Gemini
        """
        try:
            # Extract configuration
            agent_id = agent_config.get('id', str(uuid.uuid4()))
            name = agent_config.get('name', 'OpsFlow Agent')
            system_prompt = agent_config.get('system_prompt', self._get_default_system_prompt())
            model = agent_config.get('llm_model', 'gemini-2.5-flash')
            
            # Configure Gemini provider
            gemini_provider = GeminiProvider(
                model=model,
                api_key=self.gemini_api_key,
                generation_config=GenerationConfig(
                    temperature=agent_config.get('temperature', 0.7),
                    top_k=agent_config.get('top_k', 40),
                    top_p=agent_config.get('top_p', 0.95),
                    max_output_tokens=agent_config.get('max_output_tokens', 8192),
                    response_mime_type="application/json"
                ),
                safety_settings=[
                    SafetySetting(
                        category=HarmCategory.HARM_CATEGORY_HARASSMENT,
                        threshold=HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE
                    ),
                    SafetySetting(
                        category=HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                        threshold=HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE
                    ),
                    SafetySetting(
                        category=HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                        threshold=HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE
                    ),
                    SafetySetting(
                        category=HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                        threshold=HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE
                    )
                ]
            )
            
            # Create tools for the agent
            agent_tools = []
            if tools:
                agent_tools = await self._create_portia_tools(tools)
            
            # Create Portia agent
            agent = Agent(
                id=agent_id,
                name=name,
                description=agent_config.get('description', f'AI Agent for {name}'),
                provider=gemini_provider,
                storage=self.portia_storage,
                tools=agent_tools,
                system_prompt=system_prompt
            )
            
            # Store agent reference
            self.agents[agent_id] = agent
            
            logger.info(f"✅ Created AI agent '{name}' (ID: {agent_id}) with {len(agent_tools)} tools")
            
            return {
                "id": agent_id,
                "name": name,
                "status": "created",
                "model": model,
                "tools_count": len(agent_tools),
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to create AI agent: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Agent creation failed: {str(e)}")
    
    async def execute_workflow_plan(
        self,
        agent_id: str,
        workflow_request: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a workflow using AI agent with plan-based approach
        """
        try:
            if agent_id not in self.agents:
                raise ValueError(f"Agent {agent_id} not found")
            
            agent = self.agents[agent_id]
            
            # Create execution context
            execution_context = {
                "workflow_id": workflow_request.get('workflow_id'),
                "organization_id": workflow_request.get('organization_id'),
                "user_request": workflow_request.get('description', ''),
                "parameters": workflow_request.get('parameters', {}),
                "constraints": workflow_request.get('constraints', {}),
                "additional_context": context or {}
            }
            
            # Create initial message
            user_message = Message(
                role="user",
                content=self._format_workflow_request(workflow_request, execution_context)
            )
            
            # Generate execution plan
            plan = await agent.create_plan([user_message])
            plan_id = str(uuid.uuid4())
            self.active_plans[plan_id] = plan
            
            # Execute the plan
            execution_result = await self._execute_plan_with_monitoring(
                agent=agent,
                plan=plan,
                execution_context=execution_context
            )
            
            # Format response
            response = {
                "plan_id": plan_id,
                "agent_id": agent_id,
                "status": execution_result.get("status", "unknown"),
                "steps_completed": execution_result.get("steps_completed", 0),
                "total_steps": execution_result.get("total_steps", 0),
                "execution_time": execution_result.get("execution_time", 0),
                "ai_reasoning": execution_result.get("ai_reasoning", ""),
                "confidence_score": execution_result.get("confidence_score", 0.0),
                "results": execution_result.get("results", {}),
                "requires_approval": execution_result.get("requires_approval", True),
                "risk_assessment": execution_result.get("risk_assessment", {}),
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            logger.info(f"✅ Plan execution completed for agent {agent_id} - Status: {response['status']}")
            return response
            
        except Exception as e:
            logger.error(f"❌ Workflow execution failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Workflow execution failed: {str(e)}")
    
    async def get_plan_status(self, plan_id: str) -> Dict[str, Any]:
        """
        Get the status of an executing plan
        """
        try:
            if plan_id not in self.active_plans:
                raise ValueError(f"Plan {plan_id} not found")
            
            plan = self.active_plans[plan_id]
            
            return {
                "plan_id": plan_id,
                "status": plan.status,
                "current_step": getattr(plan, 'current_step', 0),
                "total_steps": len(plan.steps) if hasattr(plan, 'steps') else 0,
                "progress_percentage": self._calculate_progress(plan),
                "last_updated": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get plan status: {str(e)}")
            raise HTTPException(status_code=404, detail=f"Plan status unavailable: {str(e)}")
    
    async def _execute_plan_with_monitoring(
        self,
        agent: Agent,
        plan: Plan,
        execution_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute plan with comprehensive monitoring and error handling
        """
        start_time = datetime.now()
        steps_completed = 0
        total_steps = len(plan.steps) if hasattr(plan, 'steps') else 1
        
        try:
            # Execute the plan
            result = await agent.execute_plan(plan)
            
            # Calculate execution metrics
            execution_time = (datetime.now() - start_time).total_seconds()
            steps_completed = total_steps  # Assume all steps completed if no error
            
            # Extract AI reasoning and confidence
            ai_reasoning = self._extract_ai_reasoning(result)
            confidence_score = self._calculate_confidence_score(result)
            
            # Assess risk level
            risk_assessment = self._assess_execution_risk(result, execution_context)
            
            # Determine if approval is required
            requires_approval = self._requires_human_approval(
                confidence_score, 
                risk_assessment, 
                execution_context
            )
            
            return {
                "status": "completed" if result.success else "failed",
                "steps_completed": steps_completed,
                "total_steps": total_steps,
                "execution_time": execution_time,
                "ai_reasoning": ai_reasoning,
                "confidence_score": confidence_score,
                "results": result.data if hasattr(result, 'data') else {},
                "requires_approval": requires_approval,
                "risk_assessment": risk_assessment,
                "error": result.error if hasattr(result, 'error') else None
            }
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "status": "failed",
                "steps_completed": steps_completed,
                "total_steps": total_steps,
                "execution_time": execution_time,
                "error": str(e),
                "requires_approval": True,  # Always require approval on error
                "risk_assessment": {"level": "high", "reason": "execution_failed"}
            }
    
    async def _create_portia_tools(self, tools_config: List[Dict[str, Any]]) -> List[Tool]:
        """
        Create Portia tools from configuration
        """
        portia_tools = []
        
        for tool_config in tools_config:
            try:
                # Create tool implementation
                async def tool_implementation(**kwargs):
                    return await self._execute_tool_function(tool_config, kwargs)
                
                tool = Tool(
                    name=tool_config.get('name'),
                    description=tool_config.get('description'),
                    parameters=tool_config.get('parameters', {}),
                    implementation=tool_implementation
                )
                
                portia_tools.append(tool)
                
            except Exception as e:
                logger.warning(f"⚠️ Failed to create tool {tool_config.get('name')}: {str(e)}")
                continue
        
        return portia_tools
    
    async def _execute_tool_function(
        self, 
        tool_config: Dict[str, Any], 
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a tool function based on configuration
        """
        tool_name = tool_config.get('name')
        
        # Mock implementations for common tools
        if tool_name == 'analyze_code_diff':
            return await self._analyze_code_diff(parameters)
        elif tool_name == 'check_security_vulnerabilities':
            return await self._check_security(parameters)
        elif tool_name == 'send_notification':
            return await self._send_notification(parameters)
        elif tool_name == 'create_jira_ticket':
            return await self._create_jira_ticket(parameters)
        else:
            # Generic tool execution
            return {
                "tool": tool_name,
                "parameters": parameters,
                "result": "Tool executed successfully",
                "success": True
            }
    
    # Tool implementations (can be extended)
    async def _analyze_code_diff(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Mock code diff analysis"""
        return {
            "analysis": "Code quality is good",
            "issues": [],
            "suggestions": ["Consider adding more tests"],
            "score": 85
        }
    
    async def _check_security(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Mock security check"""
        return {
            "vulnerabilities": [],
            "risk_level": "low",
            "recommendations": ["All security checks passed"]
        }
    
    async def _send_notification(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Mock notification sending"""
        return {
            "sent": True,
            "channel": params.get("channel", "email"),
            "message": "Notification sent successfully"
        }
    
    async def _create_jira_ticket(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Mock Jira ticket creation"""
        return {
            "ticket_id": f"TICKET-{uuid.uuid4().hex[:8].upper()}",
            "status": "created",
            "url": "https://company.atlassian.net/browse/TICKET-12345"
        }
    
    # Helper methods
    def _format_workflow_request(
        self, 
        workflow_request: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> str:
        """Format workflow request for AI processing"""
        return f"""
        You are an AI agent for OpsFlow Guardian 2.0. Please analyze and execute the following workflow request:
        
        **Workflow Request:** {workflow_request.get('description', 'No description provided')}
        
        **Parameters:** {workflow_request.get('parameters', {})}
        
        **Context:** {context}
        
        **Your Task:**
        1. Understand the request and context
        2. Create a step-by-step execution plan
        3. Execute the plan using available tools
        4. Provide clear reasoning for each decision
        5. Assess the risk level of each action
        6. Return comprehensive results with confidence scores
        
        Please respond with a structured JSON format including your reasoning, confidence level, and recommended actions.
        """
    
    def _extract_ai_reasoning(self, result: Any) -> str:
        """Extract AI reasoning from execution result"""
        if hasattr(result, 'reasoning'):
            return str(result.reasoning)
        elif hasattr(result, 'messages'):
            # Extract from messages
            for msg in result.messages:
                if hasattr(msg, 'content') and 'reasoning' in str(msg.content).lower():
                    return str(msg.content)
        return "AI reasoning not available"
    
    def _calculate_confidence_score(self, result: Any) -> float:
        """Calculate confidence score from execution result"""
        # Mock calculation - in reality, this would analyze the result
        if hasattr(result, 'confidence'):
            return float(result.confidence)
        else:
            # Default confidence based on success
            return 0.85 if getattr(result, 'success', False) else 0.3
    
    def _assess_execution_risk(
        self, 
        result: Any, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess risk level of execution"""
        risk_factors = []
        risk_level = "low"
        
        # Check for high-impact operations
        if context.get('parameters', {}).get('affects_production'):
            risk_factors.append("Production environment impact")
            risk_level = "high"
        
        # Check for data modifications
        if context.get('parameters', {}).get('modifies_data'):
            risk_factors.append("Data modification operation")
            risk_level = "medium"
        
        # Check for external integrations
        if context.get('parameters', {}).get('external_integrations'):
            risk_factors.append("External system integration")
            risk_level = "medium"
        
        return {
            "level": risk_level,
            "factors": risk_factors,
            "assessment_time": datetime.now(timezone.utc).isoformat()
        }
    
    def _requires_human_approval(
        self, 
        confidence_score: float, 
        risk_assessment: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> bool:
        """Determine if human approval is required"""
        # Low confidence always requires approval
        if confidence_score < 0.7:
            return True
        
        # High risk always requires approval
        if risk_assessment.get("level") == "high":
            return True
        
        # Medium risk with medium confidence requires approval
        if risk_assessment.get("level") == "medium" and confidence_score < 0.9:
            return True
        
        # Check organization preferences
        org_preferences = context.get("organization_preferences", {})
        if org_preferences.get("always_require_approval", False):
            return True
        
        return False
    
    def _calculate_progress(self, plan: Plan) -> float:
        """Calculate plan execution progress"""
        if not hasattr(plan, 'steps') or not plan.steps:
            return 0.0
        
        completed_steps = getattr(plan, 'completed_steps', 0)
        total_steps = len(plan.steps)
        
        return (completed_steps / total_steps) * 100.0 if total_steps > 0 else 0.0
    
    def _get_default_system_prompt(self) -> str:
        """Get default system prompt for AI agents"""
        return """
        You are an AI agent for OpsFlow Guardian 2.0, an enterprise workflow automation platform.
        
        Your core responsibilities:
        1. Analyze workflow requests with precision and context awareness
        2. Create detailed, step-by-step execution plans
        3. Execute plans using available tools and integrations
        4. Provide clear reasoning for all decisions and actions
        5. Assess risk levels and recommend appropriate oversight
        6. Ensure compliance with organizational policies and constraints
        7. Maintain detailed audit trails for all operations
        
        Key principles:
        - Always prioritize safety and compliance
        - Provide transparent reasoning for all decisions
        - Ask for clarification when requests are ambiguous
        - Respect data privacy and security requirements
        - Collaborate effectively with human oversight
        - Learn from feedback and improve performance
        
        Response format: Always structure your responses as JSON with clear sections for reasoning, actions, confidence, and risk assessment.
        """

# Global manager instance
portia_manager = OpsFlowPortiaManager()

# Integration functions for FastAPI endpoints
async def create_real_ai_agent(organization_id: str, agent_config: Dict[str, Any]) -> Dict[str, Any]:
    """Create a real AI agent using Portia SDK"""
    return await portia_manager.create_ai_agent(organization_id, agent_config)

async def execute_real_workflow(agent_id: str, workflow_request: Dict[str, Any]) -> Dict[str, Any]:
    """Execute workflow using real AI agent"""
    return await portia_manager.execute_workflow_plan(agent_id, workflow_request)

async def get_real_plan_status(plan_id: str) -> Dict[str, Any]:
    """Get real plan execution status"""
    return await portia_manager.get_plan_status(plan_id)

# Environment setup helper
def setup_environment():
    """Setup environment for Portia SDK integration"""
    required_vars = ['GEMINI_API_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.warning(f"⚠️  Missing environment variables: {missing_vars}")
        logger.info("Create a .env file with the following variables:")
        logger.info("GEMINI_API_KEY=your_gemini_api_key_here")
        return False
    
    logger.info("✅ Environment setup complete")
    return True

if __name__ == "__main__":
    # Test the integration
    async def test_integration():
        setup_environment()
        
        # Test agent creation
        test_config = {
            "name": "Test Agent",
            "description": "Test AI agent for OpsFlow Guardian",
            "llm_model": "gemini-2.5-flash",
            "system_prompt": "You are a helpful AI assistant for workflow automation."
        }
        
        try:
            result = await portia_manager.create_ai_agent("test-org", test_config)
            print(f"✅ Test agent created: {result}")
        except Exception as e:
            print(f"❌ Test failed: {e}")
    
    # Run test if executed directly
    asyncio.run(test_integration())
