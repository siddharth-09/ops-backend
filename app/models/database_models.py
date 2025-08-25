"""
SQLAlchemy database models for OpsFlow Guardian 2.0 - Supabase compatible
These models match the Supabase schema defined in supabase_setup.sql
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Numeric, JSON, ForeignKey, BigInteger
from sqlalchemy.dialects.postgresql import UUID, INET, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    
    id = Column(BigInteger, primary_key=True, index=True)
    user_uuid = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4, index=True)
    
    # Basic information
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    company = Column(String(255))
    department = Column(String(255))
    job_title = Column(String(255))
    
    # Authentication
    hashed_password = Column(String(255))
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)
    
    # OAuth fields
    google_id = Column(String(255), unique=True, index=True)
    provider = Column(String(50), default="email")
    avatar_url = Column(String(500))
    
    # Profile settings
    timezone = Column(String(50), default="UTC")
    notification_preferences = Column(Text)
    
    # Security tracking
    failed_login_attempts = Column(Integer, default=0)
    last_failed_login = Column(DateTime(timezone=True))
    password_changed_at = Column(DateTime(timezone=True), default=func.now())
    two_factor_enabled = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_login = Column(DateTime(timezone=True))
    last_activity = Column(DateTime(timezone=True))
    
    # Relationships
    user_companies = relationship("UserCompany", back_populates="user")
    workflows = relationship("Workflow", back_populates="user")
    workflow_executions = relationship("WorkflowExecution", back_populates="user")


class UserEmailConfig(Base):
    __tablename__ = "user_email_configs"
    
    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    # Email credentials (encrypted)
    email_address = Column(String(255), nullable=False)
    encrypted_password = Column(Text, nullable=False)
    
    # SMTP server settings
    email_host = Column(String(255), default="smtp.gmail.com")
    email_port = Column(Integer, default=587)
    email_use_tls = Column(Boolean, default=True)
    
    # Display settings
    from_name = Column(String(255), nullable=False)
    
    # Status tracking
    is_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_tested = Column(DateTime(timezone=True))
    
    # Relationships
    user = relationship("User")


class Company(Base):
    __tablename__ = "companies"
    
    id = Column(BigInteger, primary_key=True, index=True)
    company_uuid = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)
    
    # Basic information
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    
    # Company details
    industry = Column(String(100), index=True)
    company_size = Column(String(50), index=True)
    website_url = Column(String(500))
    logo_url = Column(String(500))
    
    # Business information
    business_model = Column(String(100))
    annual_revenue_range = Column(String(50))
    employee_count = Column(Integer)
    founded_year = Column(Integer)
    
    # Contact information
    primary_contact_email = Column(String(255))
    support_email = Column(String(255))
    phone_number = Column(String(50))
    
    # Address
    address_line1 = Column(String(255))
    address_line2 = Column(String(255))
    city = Column(String(100))
    state = Column(String(100))
    country = Column(String(100))
    postal_code = Column(String(20))
    
    # Settings and preferences
    automation_preferences = Column(JSONB, default=dict)
    integration_settings = Column(JSONB, default=dict)
    notification_settings = Column(JSONB, default=dict)
    security_settings = Column(JSONB, default=dict)
    
    # Subscription and billing
    subscription_tier = Column(String(50), default="free", index=True)
    trial_expires_at = Column(DateTime(timezone=True))
    subscription_expires_at = Column(DateTime(timezone=True))
    billing_cycle = Column(String(20), default="monthly")
    
    # Status
    is_active = Column(Boolean, default=True, index=True)
    is_verified = Column(Boolean, default=False)
    onboarding_completed = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    verified_at = Column(DateTime(timezone=True))
    onboarded_at = Column(DateTime(timezone=True))
    
    # Relationships
    user_companies = relationship("UserCompany", back_populates="company")
    agents = relationship("Agent", back_populates="company")
    workflows = relationship("Workflow", back_populates="company")


class UserCompany(Base):
    __tablename__ = "user_companies"
    
    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    company_id = Column(BigInteger, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Role and permissions
    role = Column(String(50), default="member", index=True)
    permissions = Column(JSONB, default=list)
    department = Column(String(100))
    job_title = Column(String(100))
    
    # Status
    is_active = Column(Boolean, default=True, index=True)
    is_primary = Column(Boolean, default=False)
    
    # Invitation details
    invited_by = Column(BigInteger, ForeignKey("users.id"))
    invited_at = Column(DateTime(timezone=True))
    joined_at = Column(DateTime(timezone=True))
    invitation_accepted = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="user_companies", foreign_keys=[user_id])
    company = relationship("Company", back_populates="user_companies")
    inviter = relationship("User", foreign_keys=[invited_by])


class Agent(Base):
    __tablename__ = "agents"
    
    id = Column(BigInteger, primary_key=True, index=True)
    company_id = Column(BigInteger, ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    agent_uuid = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4, index=True)
    
    # Agent details
    name = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, index=True)
    status = Column(String(50), default="IDLE", index=True)
    description = Column(Text)
    
    # AI Configuration
    llm_provider = Column(String(50), default="gemini")
    llm_model = Column(String(100), default="gemini-2.5-flash")
    system_prompt = Column(Text)
    max_tokens = Column(Integer, default=4000)
    temperature = Column(Numeric(3, 2), default=0.7)
    
    # Capabilities
    capabilities = Column(JSONB)
    configuration = Column(JSONB)
    available_tools = Column(JSONB, default=list)
    
    # Performance metrics
    total_tasks_completed = Column(Integer, default=0)
    total_tasks_failed = Column(Integer, default=0)
    success_rate = Column(Numeric(5, 2), default=0.0)
    average_execution_time_seconds = Column(Numeric(10, 2), default=0.0)
    
    # Status
    is_active = Column(Boolean, default=True, index=True)
    current_task_id = Column(String(255))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_active = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    company = relationship("Company", back_populates="agents")


class Workflow(Base):
    __tablename__ = "workflows"
    
    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    company_id = Column(BigInteger, ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    workflow_uuid = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4, index=True)
    
    # Basic information
    name = Column(String(255), nullable=False)
    description = Column(Text)
    category = Column(String(100), index=True)
    
    # Workflow definition
    workflow_steps = Column(JSONB, nullable=False)
    input_schema = Column(JSONB)
    output_schema = Column(JSONB)
    
    # Configuration
    timeout_minutes = Column(Integer, default=60)
    max_retries = Column(Integer, default=3)
    risk_level = Column(String(20), default="MEDIUM", index=True)
    requires_approval = Column(Boolean, default=False)
    
    # Status
    is_active = Column(Boolean, default=True, index=True)
    is_template = Column(Boolean, default=False)
    is_public = Column(Boolean, default=False)
    version = Column(Integer, default=1)
    
    # Metadata
    tags = Column(JSONB)
    
    # Performance metrics
    total_executions = Column(Integer, default=0)
    successful_executions = Column(Integer, default=0)
    failed_executions = Column(Integer, default=0)
    average_execution_time = Column(Numeric(10, 2), default=0.0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_executed_at = Column(DateTime(timezone=True))
    
    # Relationships
    user = relationship("User", back_populates="workflows")
    company = relationship("Company", back_populates="workflows")
    executions = relationship("WorkflowExecution", back_populates="workflow")


class WorkflowExecution(Base):
    __tablename__ = "workflow_executions"
    
    id = Column(BigInteger, primary_key=True, index=True)
    workflow_id = Column(BigInteger, ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    company_id = Column(BigInteger, ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    execution_uuid = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4, index=True)
    
    # Execution details
    status = Column(String(50), default="PENDING", index=True)
    input_data = Column(JSONB)
    output_data = Column(JSONB)
    error_details = Column(Text)
    
    # Timing
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    duration_seconds = Column(Integer)
    
    # Agent assignments
    planner_agent_id = Column(String(255))
    executor_agent_id = Column(String(255))
    auditor_agent_id = Column(String(255))
    
    # Approval workflow
    requires_approval = Column(Boolean, default=False)
    approval_status = Column(String(50))
    approved_by = Column(BigInteger, ForeignKey("users.id"))
    approved_at = Column(DateTime(timezone=True))
    approval_notes = Column(Text)
    
    # Progress tracking
    current_step = Column(Integer, default=1)
    total_steps = Column(Integer, default=1)
    step_details = Column(JSONB, default=list)
    
    # Resource usage
    cpu_usage = Column(Numeric(5, 2))
    memory_usage = Column(Numeric(10, 2))
    api_calls_made = Column(Integer, default=0)
    
    # Metadata
    execution_metadata = Column(JSONB)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    workflow = relationship("Workflow", back_populates="executions")
    user = relationship("User", back_populates="workflow_executions")
    approver = relationship("User", foreign_keys=[approved_by])


class ApprovalRequest(Base):
    __tablename__ = "approval_requests"
    
    id = Column(BigInteger, primary_key=True, index=True)
    request_uuid = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)
    workflow_execution_id = Column(BigInteger, ForeignKey("workflow_executions.id", ondelete="CASCADE"), nullable=False, index=True)
    company_id = Column(BigInteger, ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    
    # Request details
    requested_by = Column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)
    approver_email = Column(String(255), nullable=False)
    approver_user_id = Column(BigInteger, ForeignKey("users.id"), index=True)
    
    # Approval details
    workflow_name = Column(String(255), nullable=False)
    risk_level = Column(String(20), nullable=False)
    description = Column(Text)
    justification = Column(Text)
    
    # Request context
    requested_action = Column(JSONB, nullable=False)
    impact_assessment = Column(JSONB)
    
    # Status
    status = Column(String(50), default="PENDING", index=True)
    decision_reason = Column(Text)
    confidence_score = Column(Numeric(3, 2))
    
    # URLs
    approval_url = Column(String(500))
    
    # Timing
    requested_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True))
    decided_at = Column(DateTime(timezone=True))
    
    # Email tracking
    email_sent = Column(Boolean, default=False)
    email_sent_at = Column(DateTime(timezone=True))
    reminder_count = Column(Integer, default=0)
    last_reminder_at = Column(DateTime(timezone=True))
    
    # Relationships
    requester = relationship("User", foreign_keys=[requested_by])
    approver = relationship("User", foreign_keys=[approver_user_id])
    execution = relationship("WorkflowExecution")


class EmailNotification(Base):
    __tablename__ = "email_notifications"
    
    id = Column(BigInteger, primary_key=True, index=True)
    notification_uuid = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)
    company_id = Column(BigInteger, ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    
    # Sender (user who configured the email)
    sender_user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)
    sender_email = Column(String(255), nullable=False)
    sender_name = Column(String(255), nullable=False)
    
    # Recipient
    recipient_email = Column(String(255), nullable=False, index=True)
    recipient_name = Column(String(255))
    
    # Email details
    subject = Column(String(500), nullable=False)
    email_type = Column(String(100), nullable=False, index=True)
    template_used = Column(String(100))
    
    # Related resources
    workflow_id = Column(BigInteger, ForeignKey("workflows.id"))
    execution_id = Column(BigInteger, ForeignKey("workflow_executions.id"))
    approval_request_id = Column(BigInteger, ForeignKey("approval_requests.id"))
    
    # Status
    status = Column(String(50), default="PENDING", index=True)
    error_message = Column(Text)
    
    # Timing
    scheduled_at = Column(DateTime(timezone=True), server_default=func.now())
    sent_at = Column(DateTime(timezone=True), index=True)
    delivered_at = Column(DateTime(timezone=True))
    
    # Email content (for audit)
    email_content_hash = Column(String(255))
    
    # Metadata
    smtp_response = Column(Text)
    
    # Relationships
    sender = relationship("User")
    workflow = relationship("Workflow")
    execution = relationship("WorkflowExecution")
    approval_request = relationship("ApprovalRequest")


class Integration(Base):
    __tablename__ = "integrations"
    
    id = Column(BigInteger, primary_key=True, index=True)
    company_id = Column(BigInteger, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    integration_uuid = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)
    
    # Integration details
    name = Column(String(255), nullable=False)
    integration_type = Column(String(100), nullable=False, index=True)
    category = Column(String(100))
    
    # Connection details
    connection_status = Column(String(50), default="DISCONNECTED", index=True)
    auth_type = Column(String(50))
    
    # Configuration
    config = Column(JSONB, default=dict)
    credentials = Column(JSONB, default=dict)  # Encrypted
    webhook_url = Column(String(500))
    
    # Usage metrics
    total_api_calls = Column(Integer, default=0)
    successful_calls = Column(Integer, default=0)
    failed_calls = Column(Integer, default=0)
    last_used_at = Column(DateTime(timezone=True))
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    company = relationship("Company")


class AuditTrail(Base):
    __tablename__ = "audit_trail"
    
    id = Column(BigInteger, primary_key=True, index=True)
    audit_uuid = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)
    company_id = Column(BigInteger, ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    
    # Event details
    event_type = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(100), index=True)
    resource_id = Column(String(255))
    
    # Actor information
    user_id = Column(BigInteger, ForeignKey("users.id"), index=True)
    agent_id = Column(BigInteger, ForeignKey("agents.id"), index=True)
    
    # Event data
    event_description = Column(Text, nullable=False)
    old_values = Column(JSONB)
    new_values = Column(JSONB)
    
    # Request context
    ip_address = Column(INET)
    user_agent = Column(Text)
    session_id = Column(String(255))
    
    # Status
    success = Column(Boolean, default=True)
    error_message = Column(Text)
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    user = relationship("User")
    agent = relationship("Agent")
    company = relationship("Company")


class SystemSettings(Base):
    __tablename__ = "system_settings"
    
    id = Column(BigInteger, primary_key=True, index=True)
    setting_key = Column(String(255), unique=True, nullable=False)
    setting_value = Column(JSONB, nullable=False)
    setting_type = Column(String(50), nullable=False)
    description = Column(Text)
    
    # Access control
    is_public = Column(Boolean, default=False)
    requires_admin = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
