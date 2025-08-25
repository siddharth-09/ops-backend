"""
Google Gemini 2.5 Pro Integration Service for OpsFlow Guardian 2.0
Handles direct integration with Google's Gemini API for multi-agent workflows
"""

import asyncio
import logging
import json
from typing import Dict, List, Any, Optional, AsyncGenerator
from datetime import datetime
import uuid

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from app.core.config import settings
from app.models.workflow import WorkflowRequest, WorkflowPlan, WorkflowStep

logger = logging.getLogger(__name__)


class GeminiService:
    """Service for Google Gemini 2.5 Pro integration"""
    
    def __init__(self):
        self.client = None
        self.model = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize Gemini service"""
        if self._initialized:
            return
        
        try:
            logger.info("Initializing Gemini 2.5 Pro service...")
            
            # Check if API key is available
            if not settings.GOOGLE_API_KEY or settings.GOOGLE_API_KEY == "your-google-api-key-here":
                logger.warning("GOOGLE_API_KEY not set - running in mock mode for testing")
                self._initialized = True
                return
            
            # Configure Gemini
            genai.configure(api_key=settings.GOOGLE_API_KEY)
            
            # Initialize the model
            self.model = genai.GenerativeModel(
                model_name="gemini-1.5-flash",  # Use base model name for direct API
                safety_settings={
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                },
                generation_config=genai.types.GenerationConfig(
                    candidate_count=1,
                    temperature=0.7,
                    top_p=0.8,
                    top_k=40,
                    max_output_tokens=8192,
                )
            )
            
            self._initialized = True
            logger.info("Gemini 2.5 Pro service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Gemini service: {e}")
            # Allow service to continue in mock mode
            self._initialized = True
    
    async def generate_workflow_plan(self, request: WorkflowRequest) -> Dict[str, Any]:
        """Generate workflow plan using Gemini 2.5 Pro"""
        try:
            logger.info(f"Generating workflow plan with Gemini for: {request.description}")
            
            # If no API key (mock mode), return a sample plan
            if not settings.GOOGLE_API_KEY or settings.GOOGLE_API_KEY == "your-google-api-key-here":
                return self._generate_mock_plan(request)
            
            # Create enhanced planning prompt
            prompt = self._create_planning_prompt(request)
            
            # Generate response with Gemini
            if self.model:
                response = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: self.model.generate_content(prompt)
                )
                
                # Parse the response
                plan_data = await self._parse_gemini_response(response, request)
            else:
                # Fallback to mock if model not available
                plan_data = self._generate_mock_plan(request)
            
            logger.info(f"Successfully generated workflow plan with {len(plan_data.get('steps', []))} steps")
            return plan_data
            
        except Exception as e:
            logger.error(f"Failed to generate workflow plan with Gemini: {e}")
            raise
    
    async def analyze_step_execution(self, step: WorkflowStep, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze step execution strategy using Gemini"""
        try:
            prompt = f"""
As an AI workflow executor, analyze this step and provide execution strategy:

STEP DETAILS:
- Name: {step.name}
- Description: {step.description}
- Tools Required: {', '.join(step.tool_integrations)}
- Risk Level: {step.risk_level}
- Approval Required: {step.requires_approval}

CONTEXT: {json.dumps(context, indent=2)}

Provide a detailed execution strategy including:
1. Pre-execution validation checks
2. Step-by-step execution approach
3. Error handling procedures
4. Success criteria
5. Rollback procedures if needed

Format as structured JSON with clear sections.
            """
            
            response = await asyncio.get_event_loop().run_in_executor(
                None, lambda: self.model.generate_content(prompt)
            )
            
            # Parse execution strategy
            strategy = await self._parse_execution_strategy(response.text)
            
            return strategy
            
        except Exception as e:
            logger.error(f"Failed to analyze step execution: {e}")
            return {"error": str(e)}
    
    async def generate_audit_summary(self, events: List[Dict[str, Any]]) -> str:
        """Generate audit summary using Gemini"""
        try:
            prompt = f"""
As an AI auditor, analyze these workflow events and generate a comprehensive audit summary:

EVENTS: {json.dumps(events, indent=2)}

Provide:
1. Executive summary of activities
2. Risk assessment and compliance status
3. Anomalies or concerns identified
4. Recommendations for improvement
5. Overall security and compliance rating

Keep the summary concise but comprehensive.
            """
            
            response = await asyncio.get_event_loop().run_in_executor(
                None, lambda: self.model.generate_content(prompt)
            )
            
            return response.text
            
        except Exception as e:
            logger.error(f"Failed to generate audit summary: {e}")
            return f"Audit summary generation failed: {str(e)}"
    
    async def chat_with_agent(self, message: str, agent_role: str, context: Dict[str, Any]) -> str:
        """Interactive chat with specific agent using Gemini"""
        try:
            role_prompts = {
                "planner": "You are the Planner Agent. Help users understand and optimize their workflows.",
                "executor": "You are the Executor Agent. Help users with workflow execution and troubleshooting.",
                "auditor": "You are the Auditor Agent. Help users with compliance and audit-related questions."
            }
            
            system_prompt = role_prompts.get(agent_role, "You are an AI assistant.")
            
            prompt = f"""
{system_prompt}

CONTEXT: {json.dumps(context, indent=2)}

USER MESSAGE: {message}

Provide a helpful, accurate, and role-appropriate response.
            """
            
            response = await asyncio.get_event_loop().run_in_executor(
                None, lambda: self.model.generate_content(prompt)
            )
            
            return response.text
            
        except Exception as e:
            logger.error(f"Failed to chat with agent: {e}")
            return f"Sorry, I encountered an error: {str(e)}"
    
    def _create_planning_prompt(self, request: WorkflowRequest) -> str:
        """Create comprehensive planning prompt for Gemini"""
        return f"""
You are the Planner Agent in OpsFlow Guardian 2.0, powered by Google Gemini 2.5 Pro. Create a detailed, actionable workflow plan.

REQUEST DETAILS:
- Description: {request.description}
- User: {request.user_id}
- Priority: {request.priority}
- Context: {request.context or 'None provided'}

AVAILABLE INTEGRATIONS:
- Google Workspace (Gmail, Sheets, Drive, Calendar, Docs)
- Slack (messaging, channels, notifications)
- Notion (pages, databases, workspace management)
- Jira (tickets, projects, sprints)
- Email Services (SMTP, notifications)
- File Management (upload, download, processing)
- Database Operations (queries, updates)
- API Integrations (REST, webhook handling)

TASK:
Create a comprehensive workflow plan with the following structure:

{{
  "plan_summary": "Brief description of what this workflow will accomplish",
  "overall_risk": "low|medium|high",
  "estimated_duration": number_of_minutes,
  "requires_human_approval": boolean,
  "steps": [
    {{
      "step_number": 1,
      "name": "Step name",
      "description": "Detailed description of what this step does",
      "tool_integrations": ["list", "of", "required", "tools"],
      "risk_level": "low|medium|high",
      "requires_approval": boolean,
      "estimated_duration": minutes,
      "dependencies": ["list", "of", "previous", "step", "numbers"],
      "success_criteria": "How to determine if this step succeeded",
      "rollback_procedure": "What to do if this step fails"
    }}
  ],
  "approval_checkpoints": ["List of steps that need human approval"],
  "contingency_plans": {{
    "failure_scenarios": ["What could go wrong"],
    "mitigation_strategies": ["How to handle each scenario"]
  }}
}}

REQUIREMENTS:
1. Break down complex requests into specific, actionable steps
2. Identify realistic tool integrations based on the task
3. Assess risk levels accurately (consider data access, external APIs, user impact)
4. Include proper dependencies between steps
5. Specify clear success criteria for each step
6. Provide practical rollback procedures
7. Estimate realistic timeframes

OUTPUT: Respond with ONLY the JSON structure above, no additional text.
        """.strip()
    
    async def _parse_gemini_response(self, response, request: WorkflowRequest) -> Dict[str, Any]:
        """Parse Gemini response into structured workflow plan data"""
        try:
            # Extract text from response
            response_text = response.text.strip()
            
            # Try to parse as JSON
            try:
                plan_data = json.loads(response_text)
            except json.JSONDecodeError:
                # If not valid JSON, extract JSON from markdown code blocks
                import re
                json_match = re.search(r'```(?:json)?\s*(.*?)\s*```', response_text, re.DOTALL)
                if json_match:
                    plan_data = json.loads(json_match.group(1))
                else:
                    # Fallback: create basic plan structure
                    plan_data = await self._create_fallback_plan(response_text, request)
            
            # Validate and enhance plan data
            plan_data = await self._validate_plan_data(plan_data, request)
            
            return plan_data
            
        except Exception as e:
            logger.error(f"Failed to parse Gemini response: {e}")
            return await self._create_fallback_plan(str(e), request)
    
    async def _validate_plan_data(self, plan_data: Dict[str, Any], request: WorkflowRequest) -> Dict[str, Any]:
        """Validate and enhance plan data structure"""
        # Ensure required fields exist
        if "steps" not in plan_data:
            plan_data["steps"] = []
        
        # Ensure each step has required fields
        for i, step in enumerate(plan_data["steps"]):
            step.setdefault("step_number", i + 1)
            step.setdefault("name", f"Step {i + 1}")
            step.setdefault("description", "Workflow step")
            step.setdefault("tool_integrations", ["internal"])
            step.setdefault("risk_level", "medium")
            step.setdefault("requires_approval", step["risk_level"] == "high")
            step.setdefault("estimated_duration", 10)
            step.setdefault("dependencies", [])
            step.setdefault("success_criteria", "Step completes without errors")
            step.setdefault("rollback_procedure", "Reverse any changes made in this step")
        
        # Set defaults for plan-level fields
        plan_data.setdefault("plan_summary", f"Automated workflow for: {request.description}")
        plan_data.setdefault("overall_risk", "medium")
        plan_data.setdefault("estimated_duration", sum(step.get("estimated_duration", 10) for step in plan_data["steps"]))
        plan_data.setdefault("requires_human_approval", any(step.get("requires_approval", False) for step in plan_data["steps"]))
        plan_data.setdefault("approval_checkpoints", [])
        plan_data.setdefault("contingency_plans", {
            "failure_scenarios": ["Network connectivity issues", "API rate limits", "Authentication failures"],
            "mitigation_strategies": ["Implement retry logic", "Use exponential backoff", "Verify credentials"]
        })
        
        return plan_data
    
    async def _create_fallback_plan(self, response_text: str, request: WorkflowRequest) -> Dict[str, Any]:
        """Create a fallback plan when parsing fails"""
        return {
            "plan_summary": f"Basic workflow plan for: {request.description}",
            "overall_risk": "medium",
            "estimated_duration": 30,
            "requires_human_approval": True,
            "steps": [
                {
                    "step_number": 1,
                    "name": "Initialize Workflow",
                    "description": "Set up workflow environment and validate inputs",
                    "tool_integrations": ["internal"],
                    "risk_level": "low",
                    "requires_approval": False,
                    "estimated_duration": 5,
                    "dependencies": [],
                    "success_criteria": "Workflow environment ready",
                    "rollback_procedure": "Clean up any initialized resources"
                },
                {
                    "step_number": 2,
                    "name": "Execute Main Task",
                    "description": request.description,
                    "tool_integrations": ["google_workspace", "slack"],
                    "risk_level": "medium",
                    "requires_approval": True,
                    "estimated_duration": 20,
                    "dependencies": [1],
                    "success_criteria": "Main task completed successfully",
                    "rollback_procedure": "Undo main task changes"
                },
                {
                    "step_number": 3,
                    "name": "Finalize and Report",
                    "description": "Complete workflow and notify stakeholders",
                    "tool_integrations": ["email"],
                    "risk_level": "low",
                    "requires_approval": False,
                    "estimated_duration": 5,
                    "dependencies": [2],
                    "success_criteria": "Notifications sent successfully",
                    "rollback_procedure": "Send error notification if needed"
                }
            ],
            "approval_checkpoints": ["Step 2: Execute Main Task"],
            "contingency_plans": {
                "failure_scenarios": ["API failures", "Permission errors", "Data validation errors"],
                "mitigation_strategies": ["Retry with exponential backoff", "Verify permissions", "Validate data before processing"]
            }
        }
    
    async def _parse_execution_strategy(self, response_text: str) -> Dict[str, Any]:
        """Parse execution strategy from Gemini response"""
        try:
            # Try to extract JSON from response
            import re
            json_match = re.search(r'```(?:json)?\s*(.*?)\s*```', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
            
            # If no JSON found, create basic strategy
            return {
                "validation_checks": ["Verify inputs", "Check permissions", "Validate dependencies"],
                "execution_approach": response_text.split('\n')[:5],  # First 5 lines as basic approach
                "error_handling": ["Log errors", "Attempt retry", "Escalate if critical"],
                "success_criteria": ["No errors encountered", "Expected outputs generated"],
                "rollback_procedures": ["Reverse changes", "Notify stakeholders", "Update audit log"]
            }
        except:
            return {
                "validation_checks": ["Basic input validation"],
                "execution_approach": ["Execute step according to description"],
                "error_handling": ["Log and report errors"],
                "success_criteria": ["Step completes without exceptions"],
                "rollback_procedures": ["Manual intervention may be required"]
            }
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test Gemini API connection"""
        try:
            if not self._initialized:
                await self.initialize()
            
            # Simple test request
            response = await asyncio.get_event_loop().run_in_executor(
                None, lambda: self.model.generate_content("Hello, this is a connection test. Please respond with 'Connected successfully'.")
            )
            
            return {
                "status": "success",
                "model": settings.GEMINI_MODEL,
                "response": response.text[:100],  # First 100 chars
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current Gemini model"""
        return {
            "provider": "Google",
            "model": settings.GEMINI_MODEL,
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
            "cost_per_1k_tokens": 0.00025,  # Approximate pricing
            "initialized": self._initialized
        }
    
    def _generate_mock_plan(self, request: WorkflowRequest) -> Dict[str, Any]:
        """Generate a mock plan for testing when API key is not available"""
        logger.info("Generating mock workflow plan for testing")
        
        # Analyze request to determine appropriate mock plan
        description_lower = request.description.lower()
        
        if "vendor" in description_lower and "onboard" in description_lower:
            return self._mock_vendor_onboarding_plan(request)
        elif "employee" in description_lower or ("onboard" in description_lower and "engineer" in description_lower):
            return self._mock_employee_onboarding_plan(request)
        elif "incident" in description_lower or "outage" in description_lower or "critical" in description_lower:
            return self._mock_incident_response_plan(request)
        else:
            return self._mock_generic_plan(request)
    
    def _mock_vendor_onboarding_plan(self, request: WorkflowRequest) -> Dict[str, Any]:
        """Mock vendor onboarding workflow plan"""
        return {
            "plan_summary": "Automated Vendor Onboarding Workflow",
            "overall_risk": "medium", 
            "estimated_duration": 45,
            "requires_human_approval": True,
            "steps": [
                {
                    "step_number": 1,
                    "name": "Vendor Information Validation",
                    "description": "Validate vendor documentation and compliance requirements",
                    "tool_integrations": ["google_drive", "compliance_check"],
                    "risk_level": "low",
                    "requires_approval": False,
                    "estimated_duration": 10,
                    "success_criteria": "All required documents verified",
                    "rollback_procedure": "Flag missing documents for manual review"
                },
                {
                    "step_number": 2,
                    "name": "Create Vendor Workspace", 
                    "description": "Set up Google Drive folder and Notion workspace for vendor",
                    "tool_integrations": ["google_drive", "notion"],
                    "risk_level": "low",
                    "requires_approval": False,
                    "estimated_duration": 15,
                    "success_criteria": "Workspace created with proper permissions",
                    "rollback_procedure": "Delete created workspace if setup fails"
                },
                {
                    "step_number": 3,
                    "name": "Contract Review and Setup",
                    "description": "Review contract terms and prepare for signature", 
                    "tool_integrations": ["docusign", "legal_review"],
                    "risk_level": "high",
                    "requires_approval": True,
                    "estimated_duration": 20,
                    "success_criteria": "Contract approved and ready for signature",
                    "rollback_procedure": "Escalate to legal team for review"
                }
            ]
        }
    
    def _mock_employee_onboarding_plan(self, request: WorkflowRequest) -> Dict[str, Any]:
        """Mock employee onboarding workflow plan"""
        return {
            "plan_summary": "Automated Employee Onboarding Workflow",
            "overall_risk": "medium",
            "estimated_duration": 60,
            "requires_human_approval": True,
            "steps": [
                {
                    "step_number": 1,
                    "name": "IT Setup and Account Creation",
                    "description": "Create email account, Slack access, and development tools",
                    "tool_integrations": ["gmail", "slack", "github", "jira"],
                    "risk_level": "medium",
                    "requires_approval": True,
                    "estimated_duration": 20,
                    "success_criteria": "All accounts created and configured",
                    "rollback_procedure": "Disable accounts if setup incomplete"
                },
                {
                    "step_number": 2,
                    "name": "Welcome Package Preparation",
                    "description": "Prepare welcome email, documentation, and schedule meetings",
                    "tool_integrations": ["email", "calendar", "notion"],
                    "risk_level": "low",
                    "requires_approval": False,
                    "estimated_duration": 15,
                    "success_criteria": "Welcome materials sent and meetings scheduled",
                    "rollback_procedure": "Resend materials if delivery fails"
                },
                {
                    "step_number": 3,
                    "name": "Team Introductions",
                    "description": "Notify team members and schedule introduction meetings",
                    "tool_integrations": ["slack", "calendar", "email"],
                    "risk_level": "low",
                    "requires_approval": False,
                    "estimated_duration": 25,
                    "success_criteria": "Team notified and meetings scheduled",
                    "rollback_procedure": "Manual follow-up if automated notifications fail"
                }
            ]
        }
    
    def _mock_incident_response_plan(self, request: WorkflowRequest) -> Dict[str, Any]:
        """Mock incident response workflow plan"""
        return {
            "plan_summary": "Critical Incident Response Workflow",
            "overall_risk": "high",
            "estimated_duration": 30,
            "requires_human_approval": True,
            "steps": [
                {
                    "step_number": 1,
                    "name": "Incident Assessment and Classification",
                    "description": "Assess incident severity and classify impact level",
                    "tool_integrations": ["monitoring", "alerting"],
                    "risk_level": "medium",
                    "requires_approval": False,
                    "estimated_duration": 5,
                    "success_criteria": "Incident properly classified and documented",
                    "rollback_procedure": "Escalate to on-call manager"
                },
                {
                    "step_number": 2,
                    "name": "Team Notification and War Room Setup",
                    "description": "Notify incident response team and create communication channels",
                    "tool_integrations": ["slack", "email", "pagerduty"],
                    "risk_level": "high",
                    "requires_approval": True,
                    "estimated_duration": 10,
                    "success_criteria": "Response team assembled and communication established",
                    "rollback_procedure": "Manual escalation to management"
                },
                {
                    "step_number": 3,
                    "name": "Issue Tracking and Documentation",
                    "description": "Create incident ticket and begin resolution tracking",
                    "tool_integrations": ["jira", "confluence", "slack"],
                    "risk_level": "medium",
                    "requires_approval": False,
                    "estimated_duration": 15,
                    "success_criteria": "Incident properly documented and tracked",
                    "rollback_procedure": "Continue with manual documentation"
                }
            ]
        }
    
    def _mock_generic_plan(self, request: WorkflowRequest) -> Dict[str, Any]:
        """Mock generic workflow plan"""
        return {
            "plan_summary": f"Automated Workflow: {request.description[:50]}...",
            "overall_risk": "medium",
            "estimated_duration": 30,
            "requires_human_approval": False,
            "steps": [
                {
                    "step_number": 1,
                    "name": "Initialize Workflow",
                    "description": "Set up initial parameters and validate inputs",
                    "tool_integrations": ["internal"],
                    "risk_level": "low",
                    "requires_approval": False,
                    "estimated_duration": 10,
                    "success_criteria": "Parameters validated and workflow ready",
                    "rollback_procedure": "Reset parameters and restart"
                },
                {
                    "step_number": 2,
                    "name": "Execute Primary Tasks",
                    "description": "Perform main workflow operations",
                    "tool_integrations": ["google_workspace", "slack"],
                    "risk_level": "medium",
                    "requires_approval": True,
                    "estimated_duration": 15,
                    "success_criteria": "Primary tasks completed successfully",
                    "rollback_procedure": "Undo changes and notify stakeholders"
                },
                {
                    "step_number": 3,
                    "name": "Finalize and Report",
                    "description": "Complete workflow and generate summary report",
                    "tool_integrations": ["email", "audit"],
                    "risk_level": "low",
                    "requires_approval": False,
                    "estimated_duration": 5,
                    "success_criteria": "Workflow completed and stakeholders notified",
                    "rollback_procedure": "Send error notification"
                }
            ]
        }
