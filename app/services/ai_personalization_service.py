"""
OpsFlow Guardian 2.0 - AI Personalization Service
Uses company profile data to customize AI agent behavior and recommendations
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class AIPersonalizationService:
    """Service to personalize AI behavior based on company profile data"""
    
    def __init__(self):
        self.industry_templates = {
            "technology": {
                "preferred_models": ["gemini-2.5-pro", "gemini-2.5-flash"],
                "automation_focus": ["code_review", "deployment", "testing", "monitoring"],
                "common_tools": ["git", "jira", "slack", "kubernetes", "monitoring"],
                "risk_tolerance": "medium",
                "approval_threshold": 0.7,
                "business_language": "technical, precise, development-focused"
            },
            "finance": {
                "preferred_models": ["gemini-2.5-pro"],
                "automation_focus": ["compliance", "reporting", "analysis", "audit"],
                "common_tools": ["excel", "quickbooks", "bloomberg", "compliance"],
                "risk_tolerance": "low",
                "approval_threshold": 0.9,
                "business_language": "formal, compliance-focused, risk-aware"
            },
            "healthcare": {
                "preferred_models": ["gemini-2.5-pro"],
                "automation_focus": ["compliance", "documentation", "patient_care", "reporting"],
                "common_tools": ["ehr", "compliance", "scheduling", "communication"],
                "risk_tolerance": "very_low",
                "approval_threshold": 0.95,
                "business_language": "precise, HIPAA-compliant, patient-focused"
            },
            "manufacturing": {
                "preferred_models": ["gemini-2.5-flash"],
                "automation_focus": ["quality_control", "monitoring", "optimization", "reporting"],
                "common_tools": ["erp", "quality_systems", "monitoring", "scheduling"],
                "risk_tolerance": "medium",
                "approval_threshold": 0.8,
                "business_language": "operational, efficiency-focused, safety-conscious"
            },
            "retail": {
                "preferred_models": ["gemini-2.5-flash"],
                "automation_focus": ["inventory", "customer_service", "analytics", "marketing"],
                "common_tools": ["pos", "crm", "inventory", "marketing"],
                "risk_tolerance": "medium",
                "approval_threshold": 0.75,
                "business_language": "customer-focused, sales-oriented, dynamic"
            },
            "consulting": {
                "preferred_models": ["gemini-2.5-pro"],
                "automation_focus": ["client_management", "reporting", "analysis", "communication"],
                "common_tools": ["crm", "project_management", "analytics", "presentation"],
                "risk_tolerance": "medium",
                "approval_threshold": 0.8,
                "business_language": "professional, client-focused, analytical"
            }
        }
        
        self.company_size_configs = {
            "startup": {
                "agent_limit": 5,
                "complexity": "simple",
                "automation_approach": "lightweight, flexible, rapid iteration",
                "priority_areas": ["customer_acquisition", "product_development", "efficiency"]
            },
            "small": {
                "agent_limit": 15,
                "complexity": "moderate",
                "automation_approach": "scalable, cost-effective, growth-oriented",
                "priority_areas": ["process_automation", "customer_service", "growth"]
            },
            "medium": {
                "agent_limit": 35,
                "complexity": "advanced",
                "automation_approach": "comprehensive, integrated, performance-focused",
                "priority_areas": ["integration", "optimization", "compliance"]
            },
            "large": {
                "agent_limit": 75,
                "complexity": "enterprise",
                "automation_approach": "sophisticated, secure, enterprise-grade",
                "priority_areas": ["governance", "compliance", "integration", "optimization"]
            },
            "enterprise": {
                "agent_limit": 150,
                "complexity": "enterprise_plus",
                "automation_approach": "cutting-edge, highly secure, fully integrated",
                "priority_areas": ["digital_transformation", "compliance", "innovation", "scale"]
            }
        }
    
    def get_personalized_system_prompt(self, company_profile: Dict[str, Any], agent_purpose: str) -> str:
        """Generate a personalized system prompt based on company profile"""
        
        company_name = company_profile.get("company_name", "your organization")
        industry = company_profile.get("industry", "technology").lower()
        size = self._extract_size_key(company_profile.get("company_size", "medium"))
        primary_goals = company_profile.get("primary_goals", [])
        automation_needs = company_profile.get("automation_needs", [])
        business_processes = company_profile.get("business_processes", [])
        
        # Get industry and size configs
        industry_config = self.industry_templates.get(industry, self.industry_templates["technology"])
        size_config = self.company_size_configs.get(size, self.company_size_configs["medium"])
        
        # Build personalized prompt
        prompt_parts = [
            f"You are an AI agent specialized in helping {company_name}, a {company_profile.get('company_size', 'medium-sized')} company in the {industry} industry.",
            f"Your purpose: {agent_purpose}",
            "",
            "COMPANY CONTEXT:",
            f"- Industry: {industry.title()}",
            f"- Size: {company_profile.get('company_size', 'Medium')}",
            f"- Business Language Style: {industry_config['business_language']}",
            f"- Automation Approach: {size_config['automation_approach']}",
        ]
        
        if primary_goals:
            prompt_parts.extend([
                "",
                "PRIMARY COMPANY GOALS:",
                *[f"- {goal}" for goal in primary_goals[:5]]
            ])
        
        if automation_needs:
            prompt_parts.extend([
                "",
                "KEY AUTOMATION NEEDS:",
                *[f"- {need}" for need in automation_needs[:5]]
            ])
        
        if business_processes:
            prompt_parts.extend([
                "",
                "IMPORTANT BUSINESS PROCESSES:",
                *[f"- {process}" for process in business_processes[:5]]
            ])
        
        # Add industry-specific guidance
        prompt_parts.extend([
            "",
            "INDUSTRY-SPECIFIC GUIDANCE:",
            f"- Focus areas: {', '.join(industry_config['automation_focus'])}",
            f"- Risk tolerance: {industry_config['risk_tolerance']}",
            f"- Approval threshold: {industry_config['approval_threshold']}",
        ])
        
        # Add behavioral guidelines
        prompt_parts.extend([
            "",
            "BEHAVIORAL GUIDELINES:",
            "- Always consider the company's specific industry context and constraints",
            "- Prioritize solutions that align with stated company goals",
            "- Use appropriate business language for the industry",
            "- Consider company size when suggesting solutions (scalability, complexity)",
            "- Be proactive in identifying automation opportunities",
            "- Always prioritize security and compliance for the industry",
            "- Provide clear, actionable recommendations",
            "",
            "Remember: You are representing OpsFlow Guardian's AI automation platform. Be helpful, professional, and focused on delivering value to this specific organization."
        ])
        
        return "\n".join(prompt_parts)
    
    def get_recommended_agent_config(self, company_profile: Dict[str, Any], agent_type: str) -> Dict[str, Any]:
        """Get recommended agent configuration based on company profile"""
        
        industry = company_profile.get("industry", "technology").lower()
        size = self._extract_size_key(company_profile.get("company_size", "medium"))
        
        industry_config = self.industry_templates.get(industry, self.industry_templates["technology"])
        size_config = self.company_size_configs.get(size, self.company_size_configs["medium"])
        
        return {
            "llm_provider": "gemini",
            "llm_model": industry_config["preferred_models"][0],
            "auto_approve_threshold": industry_config["approval_threshold"],
            "max_execution_time": 300 if size in ["startup", "small"] else 600,
            "requires_human_approval": industry_config["risk_tolerance"] in ["low", "very_low"],
            "recommended_tools": industry_config["common_tools"],
            "complexity_level": size_config["complexity"],
            "suggested_integrations": self._get_industry_integrations(industry),
            "performance_monitoring": True,
            "audit_logging": True
        }
    
    def get_workflow_recommendations(self, company_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get recommended workflows based on company profile"""
        
        industry = company_profile.get("industry", "technology").lower()
        size = self._extract_size_key(company_profile.get("company_size", "medium"))
        automation_needs = company_profile.get("automation_needs", [])
        business_processes = company_profile.get("business_processes", [])
        
        recommendations = []
        
        # Industry-specific workflow recommendations
        industry_workflows = {
            "technology": [
                {
                    "name": "Code Deployment Pipeline",
                    "description": "Automate code review, testing, and deployment processes",
                    "priority": "high",
                    "estimated_impact": "High time savings, improved quality"
                },
                {
                    "name": "Bug Triage Automation",
                    "description": "Automatically categorize and assign bugs based on severity",
                    "priority": "medium",
                    "estimated_impact": "Faster issue resolution"
                }
            ],
            "finance": [
                {
                    "name": "Invoice Processing Automation",
                    "description": "Automate invoice validation, approval, and payment processing",
                    "priority": "high",
                    "estimated_impact": "Reduced processing time, fewer errors"
                },
                {
                    "name": "Compliance Reporting",
                    "description": "Generate automated compliance reports for regulatory requirements",
                    "priority": "high",
                    "estimated_impact": "Ensure compliance, reduce manual work"
                }
            ],
            "healthcare": [
                {
                    "name": "Patient Scheduling Optimization",
                    "description": "Optimize patient scheduling based on availability and urgency",
                    "priority": "high",
                    "estimated_impact": "Better patient experience, efficient resource use"
                },
                {
                    "name": "Medical Record Processing",
                    "description": "Automate medical record categorization and filing",
                    "priority": "medium",
                    "estimated_impact": "Improved record management"
                }
            ]
        }
        
        # Add industry-specific recommendations
        if industry in industry_workflows:
            recommendations.extend(industry_workflows[industry])
        
        # Add recommendations based on automation needs
        for need in automation_needs[:3]:
            if need.lower() == "data processing":
                recommendations.append({
                    "name": "Data Processing Pipeline",
                    "description": f"Automate data processing workflows for {company_profile.get('company_name', 'your organization')}",
                    "priority": "high",
                    "estimated_impact": "Faster data insights, reduced manual work"
                })
            elif need.lower() == "report generation":
                recommendations.append({
                    "name": "Automated Report Generation",
                    "description": "Generate business reports automatically based on your data",
                    "priority": "medium",
                    "estimated_impact": "Timely insights, consistent reporting"
                })
        
        return recommendations[:5]  # Return top 5 recommendations
    
    def get_integration_recommendations(self, company_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get recommended integrations based on company profile"""
        
        industry = company_profile.get("industry", "technology").lower()
        tech_stack = company_profile.get("tech_stack", [])
        
        # Base recommendations for all industries
        base_integrations = [
            {
                "name": "Email Integration",
                "provider": "gmail/outlook",
                "priority": "high",
                "description": "Enable email automation and notifications"
            },
            {
                "name": "Calendar Integration", 
                "provider": "google/microsoft",
                "priority": "medium",
                "description": "Schedule and manage automated tasks"
            }
        ]
        
        recommendations = base_integrations.copy()
        
        # Add tech stack specific integrations
        for tech in tech_stack:
            tech_lower = tech.lower()
            if "google workspace" in tech_lower:
                recommendations.append({
                    "name": "Google Workspace Integration",
                    "provider": "google",
                    "priority": "high",
                    "description": "Integrate with Google Drive, Docs, Sheets, Gmail"
                })
            elif "salesforce" in tech_lower:
                recommendations.append({
                    "name": "Salesforce Integration",
                    "provider": "salesforce",
                    "priority": "high", 
                    "description": "Automate CRM processes and data synchronization"
                })
            elif "slack" in tech_lower:
                recommendations.append({
                    "name": "Slack Integration",
                    "provider": "slack",
                    "priority": "medium",
                    "description": "Send notifications and enable team collaboration"
                })
        
        # Industry-specific integrations
        if industry == "finance":
            recommendations.extend([
                {
                    "name": "Banking API Integration",
                    "provider": "plaid/yodlee",
                    "priority": "medium",
                    "description": "Connect to banking systems for financial data"
                },
                {
                    "name": "Accounting Software Integration",
                    "provider": "quickbooks/xero",
                    "priority": "high",
                    "description": "Sync with accounting systems"
                }
            ])
        elif industry == "technology":
            recommendations.extend([
                {
                    "name": "GitHub Integration",
                    "provider": "github",
                    "priority": "high",
                    "description": "Automate code review and deployment processes"
                },
                {
                    "name": "Jira Integration",
                    "provider": "atlassian",
                    "priority": "medium",
                    "description": "Automate issue tracking and project management"
                }
            ])
        
        return recommendations[:6]  # Return top 6 recommendations
    
    def get_ai_insights_for_company(self, company_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Generate AI-powered insights based on company profile"""
        
        industry = company_profile.get("industry", "technology").lower()
        size = self._extract_size_key(company_profile.get("company_size", "medium"))
        goals = company_profile.get("primary_goals", [])
        
        industry_config = self.industry_templates.get(industry, self.industry_templates["technology"])
        size_config = self.company_size_configs.get(size, self.company_size_configs["medium"])
        
        insights = {
            "automation_readiness": self._calculate_automation_readiness(company_profile),
            "recommended_starting_points": self._get_starting_points(company_profile),
            "potential_time_savings": self._estimate_time_savings(company_profile),
            "recommended_ai_models": industry_config["preferred_models"],
            "key_success_factors": self._get_success_factors(industry, size),
            "industry_best_practices": self._get_industry_best_practices(industry),
            "next_steps": self._get_recommended_next_steps(company_profile),
            "risk_considerations": self._get_risk_considerations(industry_config, size_config)
        }
        
        return insights
    
    def _extract_size_key(self, company_size: str) -> str:
        """Extract size key from company size string"""
        size_lower = company_size.lower()
        if "startup" in size_lower or "1-10" in size_lower:
            return "startup"
        elif "small" in size_lower or "11-50" in size_lower:
            return "small"
        elif "medium" in size_lower or "51-200" in size_lower:
            return "medium"
        elif "large" in size_lower or "201-1000" in size_lower:
            return "large"
        elif "enterprise" in size_lower or "1000+" in size_lower:
            return "enterprise"
        return "medium"
    
    def _get_industry_integrations(self, industry: str) -> List[str]:
        """Get recommended integrations for industry"""
        industry_integrations = {
            "technology": ["github", "jira", "slack", "kubernetes", "monitoring"],
            "finance": ["quickbooks", "banking_api", "compliance_tools", "reporting"],
            "healthcare": ["ehr_systems", "scheduling", "compliance", "communication"],
            "manufacturing": ["erp", "quality_systems", "monitoring", "inventory"],
            "retail": ["pos", "inventory", "crm", "marketing_tools"],
            "consulting": ["crm", "project_management", "time_tracking", "presentation"]
        }
        return industry_integrations.get(industry, ["email", "calendar", "document_management"])
    
    def _calculate_automation_readiness(self, company_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate automation readiness score"""
        score = 0
        factors = []
        
        # Check completion of profile
        if company_profile.get("primary_goals"):
            score += 25
            factors.append("Clear automation goals defined")
        
        if company_profile.get("business_processes"):
            score += 25  
            factors.append("Business processes identified")
        
        if company_profile.get("tech_stack"):
            score += 20
            factors.append("Technology stack documented")
        
        if company_profile.get("automation_needs"):
            score += 30
            factors.append("Specific automation needs identified")
        
        readiness_level = "low"
        if score >= 80:
            readiness_level = "high"
        elif score >= 50:
            readiness_level = "medium"
        
        return {
            "score": score,
            "level": readiness_level,
            "contributing_factors": factors,
            "recommendations": self._get_readiness_recommendations(score)
        }
    
    def _get_readiness_recommendations(self, score: int) -> List[str]:
        """Get recommendations based on readiness score"""
        if score >= 80:
            return [
                "Your organization is ready for advanced automation",
                "Consider implementing multi-step workflows",
                "Explore AI-powered decision making",
                "Focus on integration with existing systems"
            ]
        elif score >= 50:
            return [
                "Start with simple automation workflows",
                "Focus on high-impact, low-complexity tasks",
                "Build automation literacy within your team",
                "Document processes for automation candidates"
            ]
        else:
            return [
                "Begin with process documentation and analysis", 
                "Identify repetitive manual tasks for automation",
                "Start with basic workflow automation",
                "Invest in team training on automation concepts"
            ]
    
    def _get_starting_points(self, company_profile: Dict[str, Any]) -> List[str]:
        """Get recommended starting points for automation"""
        automation_needs = company_profile.get("automation_needs", [])
        business_processes = company_profile.get("business_processes", [])
        
        starting_points = []
        
        # High-impact, low-complexity starting points
        if "email automation" in [need.lower() for need in automation_needs]:
            starting_points.append("Email notification automation")
        
        if "report generation" in [need.lower() for need in automation_needs]:
            starting_points.append("Automated report generation")
        
        if "data entry" in [process.lower() for process in business_processes]:
            starting_points.append("Data entry workflow automation")
        
        # Default starting points if none match
        if not starting_points:
            starting_points = [
                "Simple notification workflows",
                "Document processing automation", 
                "Basic approval workflows"
            ]
        
        return starting_points[:3]
    
    def _estimate_time_savings(self, company_profile: Dict[str, Any]) -> Dict[str, str]:
        """Estimate potential time savings"""
        business_processes = len(company_profile.get("business_processes", []))
        automation_needs = len(company_profile.get("automation_needs", []))
        
        weekly_hours = (business_processes + automation_needs) * 2
        monthly_hours = weekly_hours * 4
        annual_hours = weekly_hours * 50  # 50 working weeks
        
        return {
            "weekly": f"{weekly_hours}-{weekly_hours * 2} hours",
            "monthly": f"{monthly_hours}-{monthly_hours * 2} hours", 
            "annual": f"{annual_hours}-{annual_hours * 2} hours"
        }
    
    def _get_success_factors(self, industry: str, size: str) -> List[str]:
        """Get key success factors for industry and size"""
        base_factors = [
            "Clear automation objectives",
            "Stakeholder buy-in and support",
            "Proper change management"
        ]
        
        if industry == "finance":
            base_factors.extend([
                "Compliance and regulatory considerations",
                "Risk management protocols",
                "Audit trail maintenance"
            ])
        elif industry == "technology":
            base_factors.extend([
                "Integration with development workflows",
                "Scalable infrastructure",
                "Developer adoption"
            ])
        
        if size in ["large", "enterprise"]:
            base_factors.append("Enterprise governance and security")
        
        return base_factors[:5]
    
    def _get_industry_best_practices(self, industry: str) -> List[str]:
        """Get industry-specific best practices"""
        practices = {
            "technology": [
                "Implement continuous integration/deployment automation",
                "Use infrastructure as code",
                "Automate testing and quality assurance",
                "Implement monitoring and alerting"
            ],
            "finance": [
                "Maintain comprehensive audit trails",
                "Implement multi-level approval processes",
                "Ensure regulatory compliance in all automations",
                "Use secure data handling practices"
            ],
            "healthcare": [
                "Maintain HIPAA compliance in all processes",
                "Implement patient data security measures",
                "Use clinical decision support systems",
                "Ensure care coordination automation"
            ]
        }
        
        return practices.get(industry, [
            "Start with low-risk, high-impact processes",
            "Implement proper monitoring and alerting", 
            "Maintain human oversight for critical decisions",
            "Document all automated processes"
        ])
    
    def _get_recommended_next_steps(self, company_profile: Dict[str, Any]) -> List[str]:
        """Get recommended next steps"""
        steps = [
            "Deploy your first AI agent for a simple workflow",
            "Set up monitoring and alerting",
            "Configure approval processes"
        ]
        
        if not company_profile.get("tech_stack"):
            steps.insert(0, "Document your current technology stack")
        
        if len(company_profile.get("automation_needs", [])) < 3:
            steps.insert(0, "Identify additional automation opportunities")
        
        return steps[:4]
    
    def _get_risk_considerations(self, industry_config: Dict, size_config: Dict) -> List[str]:
        """Get risk considerations"""
        considerations = [
            "Implement proper access controls and permissions",
            "Maintain data backup and recovery procedures",
            "Test automation thoroughly before production deployment"
        ]
        
        if industry_config["risk_tolerance"] == "low":
            considerations.extend([
                "Implement multi-level approval processes",
                "Maintain detailed audit logs",
                "Consider regulatory compliance requirements"
            ])
        
        if size_config["complexity"] == "enterprise":
            considerations.append("Ensure enterprise-grade security and governance")
        
        return considerations[:5]

# Global instance
ai_personalization_service = AIPersonalizationService()
