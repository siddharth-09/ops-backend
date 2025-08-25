"""
OpsFlow Guardian 2.0 - Company Management API
Enterprise AI Configuration and Onboarding
"""

import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from uuid import uuid4
from datetime import datetime, timezone

# Configure logging
logger = logging.getLogger(__name__)

# Initialize router  
router = APIRouter()

# Pydantic Models for Company Management
class CompanyProfile(BaseModel):
    company_name: str = Field(..., description="Company name")
    industry: str = Field(..., description="Industry sector")
    company_size: str = Field(..., description="Company size")
    primary_business: str = Field(..., description="Primary business description")
    key_processes: List[str] = Field(..., description="Key business processes")
    automation_goals: List[str] = Field(..., description="Automation objectives")
    risk_tolerance: str = Field(default="medium", description="Risk tolerance level")
    
    # AI Configuration Settings
    ai_configuration: Optional[Dict[str, Any]] = Field(default={}, description="AI system configuration")
    workflow_preferences: Optional[Dict[str, Any]] = Field(default={}, description="Workflow automation preferences")
    approval_settings: Optional[Dict[str, Any]] = Field(default={}, description="Approval workflow settings")
    integration_requirements: Optional[List[str]] = Field(default=[], description="Required integrations")
    
    # Contact and Setup Information
    admin_contact: Optional[Dict[str, str]] = Field(default={}, description="Administrator contact info")
    setup_preferences: Optional[Dict[str, Any]] = Field(default={}, description="Initial setup preferences")

class CompanyUpdate(BaseModel):
    company_name: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    primary_business: Optional[str] = None
    key_processes: Optional[List[str]] = None
    automation_goals: Optional[List[str]] = None
    risk_tolerance: Optional[str] = None
    ai_configuration: Optional[Dict[str, Any]] = None
    workflow_preferences: Optional[Dict[str, Any]] = None
    approval_settings: Optional[Dict[str, Any]] = None
    integration_requirements: Optional[List[str]] = None
    admin_contact: Optional[Dict[str, str]] = None
    setup_preferences: Optional[Dict[str, Any]] = None

# Mock storage (replace with database)
company_storage = {}

@router.post("/")
async def create_company_profile(profile: CompanyProfile):
    """Create comprehensive company profile with AI configuration"""
    try:
        company_id = str(uuid4())[:8]
        
        # Generate intelligent AI configuration based on company profile
        ai_config = generate_ai_configuration(profile)
        
        # Create enhanced company profile
        enhanced_profile = {
            "id": company_id,
            **profile.dict(),
            "ai_configuration": {
                **profile.ai_configuration,
                **ai_config["recommended_ai_config"]
            },
            "workflow_preferences": {
                **profile.workflow_preferences,
                **ai_config["workflow_preferences"]  
            },
            "approval_settings": {
                **profile.approval_settings,
                **ai_config["approval_settings"]
            },
            "system_recommendations": ai_config["recommendations"],
            "agent_templates": ai_config["agent_templates"],
            "integration_roadmap": ai_config["integration_roadmap"],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "onboarding_status": "in_progress",
            "setup_progress": {
                "profile_complete": True,
                "ai_configured": True,
                "agents_deployed": False,
                "workflows_active": False,
                "integrations_connected": False
            }
        }
        
        # Store company profile
        company_storage[company_id] = enhanced_profile
        
        logger.info(f"Created company profile: {profile.company_name} (ID: {company_id})")
        
        return {
            "success": True,
            "company_id": company_id,
            "profile": enhanced_profile,
            "message": f"Company profile created for {profile.company_name}",
            "next_steps": ai_config["next_steps"]
        }
        
    except Exception as e:
        logger.error(f"Failed to create company profile: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Company profile creation failed: {str(e)}")

@router.get("/")
async def list_companies():
    """Get all company profiles"""
    try:
        companies_list = list(company_storage.values())
        
        return {
            "companies": companies_list,
            "total_count": len(companies_list),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to list companies: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve companies: {str(e)}")

@router.get("/{company_id}")
async def get_company_profile(company_id: str):
    """Get detailed company profile"""
    try:
        if company_id not in company_storage:
            raise HTTPException(status_code=404, detail="Company not found")
        
        profile = company_storage[company_id]
        
        # Add runtime analytics
        profile_with_analytics = {
            **profile,
            "analytics": {
                "profile_completeness": calculate_profile_completeness(profile),
                "ai_readiness_score": calculate_ai_readiness(profile),
                "automation_potential": assess_automation_potential(profile),
                "recommended_next_actions": get_next_actions(profile)
            },
            "last_accessed": datetime.now(timezone.utc).isoformat()
        }
        
        return profile_with_analytics
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get company profile {company_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve company profile: {str(e)}")

@router.put("/{company_id}")
async def update_company_profile(company_id: str, updates: CompanyUpdate):
    """Update company profile"""
    try:
        if company_id not in company_storage:
            raise HTTPException(status_code=404, detail="Company not found")
        
        current_profile = company_storage[company_id]
        
        # Update profile with provided changes
        update_data = {k: v for k, v in updates.dict().items() if v is not None}
        
        updated_profile = {
            **current_profile,
            **update_data,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Regenerate AI configuration if key fields changed
        if any(field in update_data for field in ['industry', 'company_size', 'key_processes', 'automation_goals']):
            # Create temporary profile object for AI config generation
            temp_profile = CompanyProfile(**{
                k: v for k, v in updated_profile.items() 
                if k in CompanyProfile.__fields__
            })
            
            ai_config = generate_ai_configuration(temp_profile)
            updated_profile["ai_configuration"].update(ai_config["recommended_ai_config"])
            updated_profile["system_recommendations"] = ai_config["recommendations"]
        
        company_storage[company_id] = updated_profile
        
        logger.info(f"Updated company profile: {company_id}")
        
        return {
            "success": True,
            "profile": updated_profile,
            "message": "Company profile updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update company profile {company_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update company profile: {str(e)}")

@router.delete("/{company_id}")
async def delete_company_profile(company_id: str):
    """Delete company profile"""
    try:
        if company_id not in company_storage:
            raise HTTPException(status_code=404, detail="Company not found")
        
        company_name = company_storage[company_id].get("company_name", "Unknown")
        del company_storage[company_id]
        
        logger.info(f"Deleted company profile: {company_name} (ID: {company_id})")
        
        return {
            "success": True,
            "message": f"Company profile for {company_name} deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete company profile {company_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete company profile: {str(e)}")

@router.post("/{company_id}/ai-recommendations")
async def get_ai_recommendations(company_id: str):
    """Get personalized AI recommendations for company"""
    try:
        if company_id not in company_storage:
            raise HTTPException(status_code=404, detail="Company not found")
        
        profile = company_storage[company_id]
        
        recommendations = {
            "agent_recommendations": get_recommended_agents(profile),
            "workflow_suggestions": get_workflow_suggestions(profile),
            "integration_priorities": get_integration_priorities(profile),
            "automation_roadmap": get_automation_roadmap(profile),
            "risk_assessments": get_risk_assessments(profile),
            "roi_projections": get_roi_projections(profile),
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
        
        return recommendations
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get AI recommendations for {company_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate recommendations: {str(e)}")

# Helper Functions
def generate_ai_configuration(profile: CompanyProfile) -> Dict[str, Any]:
    """Generate intelligent AI configuration based on company profile"""
    
    # Industry-specific configurations
    industry_configs = {
        "technology": {
            "preferred_models": ["gemini-2.5-pro", "gemini-2.5-flash"],
            "automation_focus": ["code_review", "deployment", "testing"],
            "risk_tolerance": "high",
            "approval_threshold": 0.7
        },
        "finance": {
            "preferred_models": ["gemini-2.5-pro"],
            "automation_focus": ["compliance", "reporting", "analysis"],
            "risk_tolerance": "low", 
            "approval_threshold": 0.9
        },
        "healthcare": {
            "preferred_models": ["gemini-2.5-pro"],
            "automation_focus": ["compliance", "documentation", "workflow"],
            "risk_tolerance": "low",
            "approval_threshold": 0.95
        },
        "manufacturing": {
            "preferred_models": ["gemini-2.5-flash"],
            "automation_focus": ["monitoring", "optimization", "quality"],
            "risk_tolerance": "medium",
            "approval_threshold": 0.8
        }
    }
    
    # Company size configurations
    size_configs = {
        "startup": {"agent_limit": 5, "complexity": "simple"},
        "small": {"agent_limit": 10, "complexity": "medium"},
        "medium": {"agent_limit": 25, "complexity": "advanced"},
        "large": {"agent_limit": 50, "complexity": "enterprise"},
        "enterprise": {"agent_limit": 100, "complexity": "enterprise"}
    }
    
    industry_key = profile.industry.lower()
    size_key = profile.company_size.lower()
    
    industry_config = industry_configs.get(industry_key, industry_configs["technology"])
    size_config = size_configs.get(size_key, size_configs["medium"])
    
    return {
        "recommended_ai_config": {
            "primary_llm_provider": "gemini",
            "preferred_models": industry_config["preferred_models"],
            "max_agents": size_config["agent_limit"],
            "complexity_level": size_config["complexity"],
            "auto_approve_threshold": industry_config["approval_threshold"],
            "risk_assessment_enabled": True,
            "human_oversight_required": profile.risk_tolerance.lower() in ["low", "medium"],
            "audit_logging": True,
            "performance_monitoring": True
        },
        "workflow_preferences": {
            "automation_focus_areas": industry_config["automation_focus"],
            "parallel_execution": size_key in ["medium", "large", "enterprise"],
            "batch_processing": True,
            "real_time_monitoring": True,
            "custom_workflows": size_key in ["large", "enterprise"]
        },
        "approval_settings": {
            "default_approval_required": profile.risk_tolerance.lower() != "high",
            "approval_timeout_hours": 24,
            "escalation_enabled": True,
            "approval_chains": size_key in ["medium", "large", "enterprise"]
        },
        "agent_templates": get_agent_templates(profile),
        "integration_roadmap": get_integration_roadmap_for_profile(profile),
        "recommendations": get_setup_recommendations(profile, industry_config, size_config),
        "next_steps": get_onboarding_next_steps(profile)
    }

def get_agent_templates(profile: CompanyProfile) -> List[Dict[str, Any]]:
    """Generate recommended agent templates based on company profile"""
    
    base_templates = [
        {
            "name": f"{profile.company_name} Assistant", 
            "type": "general",
            "description": f"General purpose AI assistant for {profile.company_name}",
            "recommended_model": "gemini-2.5-flash",
            "tools": ["email", "calendar", "documentation"]
        }
    ]
    
    # Add industry-specific agents
    if "technology" in profile.industry.lower():
        base_templates.extend([
            {
                "name": "DevOps Automation Agent",
                "type": "devops", 
                "description": "Automate deployment, monitoring, and infrastructure management",
                "recommended_model": "gemini-2.5-pro",
                "tools": ["git", "kubernetes", "monitoring", "slack"]
            },
            {
                "name": "Code Review Agent",
                "type": "code_review",
                "description": "Automated code analysis and review",
                "recommended_model": "gemini-2.5-pro", 
                "tools": ["github", "jira", "code_analysis"]
            }
        ])
    
    if "finance" in profile.industry.lower():
        base_templates.extend([
            {
                "name": "Financial Compliance Agent",
                "type": "compliance",
                "description": "Ensure regulatory compliance and risk management",
                "recommended_model": "gemini-2.5-pro",
                "tools": ["compliance_check", "reporting", "audit"]
            }
        ])
    
    return base_templates

def calculate_profile_completeness(profile: Dict[str, Any]) -> float:
    """Calculate how complete the company profile is"""
    required_fields = [
        "company_name", "industry", "company_size", "primary_business",
        "key_processes", "automation_goals", "ai_configuration"
    ]
    
    completed_fields = sum(1 for field in required_fields if profile.get(field))
    return round((completed_fields / len(required_fields)) * 100, 2)

def calculate_ai_readiness(profile: Dict[str, Any]) -> float:
    """Calculate AI readiness score"""
    readiness_factors = {
        "has_clear_goals": len(profile.get("automation_goals", [])) >= 3,
        "defined_processes": len(profile.get("key_processes", [])) >= 2,
        "risk_assessment": profile.get("risk_tolerance") is not None,
        "ai_config_present": bool(profile.get("ai_configuration")),
        "integration_requirements": len(profile.get("integration_requirements", [])) > 0
    }
    
    score = sum(readiness_factors.values()) / len(readiness_factors) * 100
    return round(score, 2)

def assess_automation_potential(profile: Dict[str, Any]) -> Dict[str, Any]:
    """Assess automation potential based on company profile"""
    processes = profile.get("key_processes", [])
    goals = profile.get("automation_goals", [])
    
    return {
        "high_potential_areas": processes[:3] if len(processes) >= 3 else processes,
        "automation_readiness": "high" if len(goals) >= 3 else "medium",
        "estimated_time_savings": f"{len(processes) * 2}-{len(processes) * 4} hours/week",
        "complexity_assessment": "medium" if len(processes) <= 5 else "high"
    }

def get_next_actions(profile: Dict[str, Any]) -> List[str]:
    """Get recommended next actions for the company"""
    actions = ["Complete company profile setup"]
    
    if profile.get("setup_progress", {}).get("profile_complete"):
        actions.append("Deploy first AI agent")
    
    if not profile.get("setup_progress", {}).get("agents_deployed"):
        actions.append("Create workflow automation")
    
    if len(profile.get("integration_requirements", [])) > 0:
        actions.append("Configure system integrations")
    
    return actions

def get_integration_roadmap_for_profile(profile: CompanyProfile) -> Dict[str, Any]:
    """Get integration roadmap based on company profile"""
    return {
        "phase_1": ["Basic API integrations", "Email notifications"],
        "phase_2": ["CRM integration", "Slack/Teams integration"],  
        "phase_3": ["Advanced analytics", "Custom integrations"],
        "estimated_timeline": "3-6 months",
        "priority_integrations": profile.integration_requirements[:3]
    }

def get_setup_recommendations(profile: CompanyProfile, industry_config: Dict, size_config: Dict) -> List[str]:
    """Get setup recommendations"""
    recommendations = [
        f"Configure {industry_config['preferred_models'][0]} as primary LLM",
        f"Set up {size_config['agent_limit']} agent limit based on company size", 
        f"Enable {industry_config['risk_tolerance']} risk tolerance settings"
    ]
    
    if profile.risk_tolerance.lower() != "high":
        recommendations.append("Enable human approval workflows for safety")
    
    return recommendations

def get_onboarding_next_steps(profile: CompanyProfile) -> List[str]:
    """Get onboarding next steps"""
    return [
        "Review AI configuration settings",
        "Deploy recommended agent templates",
        "Configure approval workflows",
        "Set up system integrations",
        "Train team on AI automation platform"
    ]

def get_recommended_agents(profile: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get recommended agents for the company"""
    return get_agent_templates(CompanyProfile(**{
        k: v for k, v in profile.items() 
        if k in CompanyProfile.__fields__
    }))

def get_workflow_suggestions(profile: Dict[str, Any]) -> List[Dict[str, str]]:
    """Get workflow suggestions based on company profile"""
    processes = profile.get("key_processes", [])
    goals = profile.get("automation_goals", [])
    
    suggestions = []
    for process in processes[:3]:
        suggestions.append({
            "name": f"Automate {process}",
            "description": f"Streamline {process} workflow with AI automation",
            "estimated_impact": "High"
        })
    
    return suggestions

def get_integration_priorities(profile: Dict[str, Any]) -> List[Dict[str, str]]:
    """Get integration priorities"""
    requirements = profile.get("integration_requirements", [])
    
    return [
        {"integration": req, "priority": "High", "complexity": "Medium"} 
        for req in requirements[:3]
    ]

def get_automation_roadmap(profile: Dict[str, Any]) -> Dict[str, List[str]]:
    """Get automation roadmap"""
    return {
        "month_1": ["Agent deployment", "Basic workflows"],
        "month_2": ["Advanced workflows", "Integration setup"], 
        "month_3": ["Optimization", "Advanced features"],
        "ongoing": ["Monitoring", "Continuous improvement"]
    }

def get_risk_assessments(profile: Dict[str, Any]) -> Dict[str, Any]:
    """Get risk assessments"""
    risk_level = profile.get("risk_tolerance", "medium").lower()
    
    return {
        "overall_risk": risk_level,
        "mitigation_strategies": ["Human oversight", "Approval workflows", "Audit logging"],
        "compliance_requirements": ["Data privacy", "Industry regulations"],
        "monitoring_recommended": True
    }

def get_roi_projections(profile: Dict[str, Any]) -> Dict[str, Any]:
    """Get ROI projections"""
    processes_count = len(profile.get("key_processes", []))
    
    return {
        "time_savings_per_week": f"{processes_count * 3}-{processes_count * 6} hours",
        "cost_reduction_estimate": f"{processes_count * 500}-{processes_count * 1500} USD/month", 
        "payback_period": "3-6 months",
        "efficiency_gain": f"{processes_count * 15}-{processes_count * 25}%"
    }

from fastapi import APIRouter, HTTPException, Body
from typing import List, Dict, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory storage for demo (replace with database in production)
company_profiles_storage: Dict[str, Any] = {}

@router.post("/company-profile")
async def save_company_profile(profile_data: Dict[str, Any] = Body(...)):
    """Save company profile information with AI personalization"""
    try:
        from app.services.ai_personalization_service import ai_personalization_service
        
        # Extract profile data
        required_fields = ["companyName", "industry", "size"]
        for field in required_fields:
            if field not in profile_data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        profile_id = "default_profile"  # For demo, single profile
        
        # Create enhanced profile data
        enhanced_profile = {
            "id": profile_id,
            "company_name": profile_data.get("companyName"),
            "industry": profile_data.get("industry"),
            "company_size": profile_data.get("size"),
            "primary_goals": profile_data.get("primaryGoals", []),
            "automation_needs": profile_data.get("automationNeeds", []),
            "tech_stack": profile_data.get("techStack", []),
            "business_processes": profile_data.get("businessProcesses", []),
            "additional_description": profile_data.get("description", ""),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "onboarding_completed": True,
            "onboarding_completed_at": datetime.now().isoformat()
        }
        
        # Generate AI-powered insights and recommendations
        ai_insights = ai_personalization_service.get_ai_insights_for_company(enhanced_profile)
        workflow_recommendations = ai_personalization_service.get_workflow_recommendations(enhanced_profile)
        integration_recommendations = ai_personalization_service.get_integration_recommendations(enhanced_profile)
        
        # Add AI-generated content to profile
        enhanced_profile.update({
            "ai_insights": ai_insights,
            "recommended_workflows": workflow_recommendations,
            "recommended_integrations": integration_recommendations,
            "automation_readiness": ai_insights.get("automation_readiness", {}),
            "personalization_applied": True,
            "ai_configuration": {
                "system_prompt_template": ai_personalization_service.get_personalized_system_prompt(
                    enhanced_profile, "General AI Assistant"
                ),
                "recommended_models": ai_insights.get("recommended_ai_models", ["gemini-2.5-flash"]),
                "auto_approve_threshold": ai_personalization_service.get_recommended_agent_config(
                    enhanced_profile, "general"
                ).get("auto_approve_threshold", 0.8)
            }
        })
        
        # Save to storage
        company_profiles_storage[profile_id] = enhanced_profile
        
        logger.info(f"💾 Saved enhanced company profile for: {profile_data.get('companyName')}")
        logger.info(f"🤖 Applied AI personalization - Readiness: {ai_insights.get('automation_readiness', {}).get('level', 'unknown')}")
        
        return {
            "success": True,
            "message": "Company profile saved with AI personalization applied",
            "data": {
                "profile": enhanced_profile,
                "ai_insights": ai_insights,
                "recommendations": {
                    "workflows": workflow_recommendations,
                    "integrations": integration_recommendations
                },
                "next_steps": ai_insights.get("next_steps", [])
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to save company profile: {e}")
        raise HTTPException(status_code=500, detail="Failed to save company profile")


@router.get("/company-profile")
async def get_company_profile():
    """Get company profile information"""
    try:
        profile_id = "default_profile"
        
        if profile_id not in company_profiles_storage:
            raise HTTPException(status_code=404, detail="Company profile not found")
        
        profile = company_profiles_storage[profile_id]
        
        return {
            "success": True,
            "data": profile
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get company profile: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve company profile")


@router.put("/company-profile")
async def update_company_profile(profile_data: Dict[str, Any] = Body(...)):
    """Update company profile information"""
    try:
        profile_id = "default_profile"
        
        if profile_id not in company_profiles_storage:
            # Create new profile if it doesn't exist
            return await save_company_profile(profile_data)
        
        # Update existing profile
        existing_profile = company_profiles_storage[profile_id]
        existing_profile.update({
            "company_name": profile_data.get("companyName", existing_profile["company_name"]),
            "industry": profile_data.get("industry", existing_profile["industry"]),
            "size": profile_data.get("size", existing_profile["size"]),
            "primary_goals": profile_data.get("primaryGoals", existing_profile["primary_goals"]),
            "automation_needs": profile_data.get("automationNeeds", existing_profile["automation_needs"]),
            "tech_stack": profile_data.get("techStack", existing_profile["tech_stack"]),
            "business_processes": profile_data.get("businessProcesses", existing_profile["business_processes"]),
            "description": profile_data.get("description", existing_profile["description"]),
            "updated_at": datetime.now().isoformat()
        })
        
        company_profiles_storage[profile_id] = existing_profile
        
        logger.info(f"Updated company profile for: {profile_data.get('companyName')}")
        
        return {
            "success": True,
            "message": "Company profile updated successfully",
            "data": existing_profile
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update company profile: {e}")
        raise HTTPException(status_code=500, detail="Failed to update company profile")
