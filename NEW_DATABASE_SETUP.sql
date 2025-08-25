-- ================================================
-- OpsFlow Guardian 2.0 - Complete Database Schema
-- Execute this file to create all required tables
-- ================================================

-- ================================
-- 1. USERS AND AUTHENTICATION
-- ================================

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    user_uuid VARCHAR(255) UNIQUE NOT NULL DEFAULT gen_random_uuid()::TEXT,
    
    -- Basic information
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    company VARCHAR(255),
    department VARCHAR(255),
    job_title VARCHAR(255),
    
    -- Authentication
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    is_admin BOOLEAN DEFAULT FALSE,
    
    -- Profile settings
    timezone VARCHAR(50) DEFAULT 'UTC',
    notification_preferences TEXT,
    avatar_url VARCHAR(500),
    
    -- Security tracking
    failed_login_attempts INTEGER DEFAULT 0,
    last_failed_login TIMESTAMP,
    password_changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    two_factor_enabled BOOLEAN DEFAULT FALSE,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    last_activity TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_user_uuid ON users(user_uuid);
CREATE INDEX idx_users_active ON users(is_active);

-- ================================
-- 2. USER EMAIL CONFIGURATION
-- ================================

CREATE TABLE user_email_configs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Email credentials (encrypted)
    email_address VARCHAR(255) NOT NULL,
    encrypted_password TEXT NOT NULL,
    
    -- SMTP server settings
    email_host VARCHAR(255) DEFAULT 'smtp.gmail.com',
    email_port INTEGER DEFAULT 587,
    email_use_tls BOOLEAN DEFAULT TRUE,
    
    -- Display settings
    from_name VARCHAR(255) NOT NULL,
    
    -- Status tracking
    is_verified BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_tested TIMESTAMP
);

CREATE INDEX idx_email_config_user_id ON user_email_configs(user_id);
CREATE INDEX idx_email_config_active ON user_email_configs(is_active);

-- ================================
-- 3. COMPANIES/ORGANIZATIONS
-- ================================

CREATE TABLE companies (
    id SERIAL PRIMARY KEY,
    company_uuid VARCHAR(255) UNIQUE NOT NULL DEFAULT gen_random_uuid()::TEXT,
    
    -- Basic information
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    
    -- Company details
    industry VARCHAR(100),
    company_size VARCHAR(50), -- 'startup', 'small', 'medium', 'large', 'enterprise'
    website_url VARCHAR(500),
    logo_url VARCHAR(500),
    
    -- Business information
    business_model VARCHAR(100), -- 'b2b', 'b2c', 'b2b2c', 'marketplace'
    annual_revenue_range VARCHAR(50),
    employee_count INTEGER,
    founded_year INTEGER,
    
    -- Contact information
    primary_contact_email VARCHAR(255),
    support_email VARCHAR(255),
    phone_number VARCHAR(50),
    
    -- Address
    address_line1 VARCHAR(255),
    address_line2 VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(100),
    country VARCHAR(100),
    postal_code VARCHAR(20),
    
    -- Settings and preferences
    automation_preferences JSONB DEFAULT '{}'::jsonb,
    integration_settings JSONB DEFAULT '{}'::jsonb,
    notification_settings JSONB DEFAULT '{}'::jsonb,
    security_settings JSONB DEFAULT '{}'::jsonb,
    
    -- Subscription and billing
    subscription_tier VARCHAR(50) DEFAULT 'free',
    trial_expires_at TIMESTAMP,
    subscription_expires_at TIMESTAMP,
    billing_cycle VARCHAR(20) DEFAULT 'monthly',
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    onboarding_completed BOOLEAN DEFAULT FALSE,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    verified_at TIMESTAMP,
    onboarded_at TIMESTAMP
);

CREATE INDEX idx_companies_slug ON companies(slug);
CREATE INDEX idx_companies_industry ON companies(industry);
CREATE INDEX idx_companies_size ON companies(company_size);
CREATE INDEX idx_companies_active ON companies(is_active);
CREATE INDEX idx_companies_subscription ON companies(subscription_tier);

-- ================================
-- 4. USER-COMPANY RELATIONSHIPS
-- ================================

CREATE TABLE user_companies (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    
    -- Role and permissions
    role VARCHAR(50) DEFAULT 'member', -- 'owner', 'admin', 'manager', 'member', 'viewer'
    permissions JSONB DEFAULT '[]'::jsonb,
    department VARCHAR(100),
    job_title VARCHAR(100),
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    is_primary BOOLEAN DEFAULT FALSE,
    
    -- Invitation details
    invited_by INTEGER REFERENCES users(id),
    invited_at TIMESTAMP,
    joined_at TIMESTAMP,
    invitation_accepted BOOLEAN DEFAULT FALSE,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(user_id, company_id)
);

CREATE INDEX idx_user_companies_user ON user_companies(user_id);
CREATE INDEX idx_user_companies_company ON user_companies(company_id);
CREATE INDEX idx_user_companies_role ON user_companies(role);
CREATE INDEX idx_user_companies_active ON user_companies(is_active);

-- ================================
-- 5. WORKFLOW MANAGEMENT
-- ================================

CREATE TABLE workflows (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    company_id INTEGER REFERENCES companies(id) ON DELETE CASCADE,
    workflow_uuid VARCHAR(255) UNIQUE NOT NULL DEFAULT gen_random_uuid()::TEXT,
    
    -- Basic information
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100),
    
    -- Workflow definition
    workflow_steps JSONB NOT NULL,
    input_schema JSONB,
    output_schema JSONB,
    
    -- Configuration
    timeout_minutes INTEGER DEFAULT 60,
    max_retries INTEGER DEFAULT 3,
    risk_level VARCHAR(20) DEFAULT 'MEDIUM',
    requires_approval BOOLEAN DEFAULT FALSE,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    is_template BOOLEAN DEFAULT FALSE,
    is_public BOOLEAN DEFAULT FALSE,
    version INTEGER DEFAULT 1,
    
    -- Metadata
    tags JSONB,
    metadata JSONB,
    
    -- Performance metrics
    total_executions INTEGER DEFAULT 0,
    successful_executions INTEGER DEFAULT 0,
    failed_executions INTEGER DEFAULT 0,
    average_execution_time DECIMAL(10,2) DEFAULT 0.0,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_executed_at TIMESTAMP
);

CREATE INDEX idx_workflows_user_id ON workflows(user_id);
CREATE INDEX idx_workflows_company_id ON workflows(company_id);
CREATE INDEX idx_workflows_uuid ON workflows(workflow_uuid);
CREATE INDEX idx_workflows_active ON workflows(is_active);
CREATE INDEX idx_workflows_category ON workflows(category);
CREATE INDEX idx_workflows_risk_level ON workflows(risk_level);

-- ================================
-- 6. WORKFLOW EXECUTIONS
-- ================================

CREATE TABLE workflow_executions (
    id SERIAL PRIMARY KEY,
    workflow_id INTEGER NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    company_id INTEGER REFERENCES companies(id) ON DELETE CASCADE,
    execution_uuid VARCHAR(255) UNIQUE NOT NULL DEFAULT gen_random_uuid()::TEXT,
    
    -- Execution details
    status VARCHAR(50) DEFAULT 'PENDING',
    input_data JSONB,
    output_data JSONB,
    error_details TEXT,
    
    -- Timing
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    duration_seconds INTEGER,
    
    -- Agent assignments
    planner_agent_id VARCHAR(255),
    executor_agent_id VARCHAR(255),
    auditor_agent_id VARCHAR(255),
    
    -- Approval workflow
    requires_approval BOOLEAN DEFAULT FALSE,
    approval_status VARCHAR(50),
    approved_by INTEGER REFERENCES users(id),
    approved_at TIMESTAMP,
    approval_notes TEXT,
    
    -- Progress tracking
    current_step INTEGER DEFAULT 1,
    total_steps INTEGER DEFAULT 1,
    step_details JSONB DEFAULT '[]'::jsonb,
    
    -- Resource usage
    cpu_usage DECIMAL(5,2),
    memory_usage DECIMAL(10,2),
    api_calls_made INTEGER DEFAULT 0,
    
    -- Metadata
    execution_metadata JSONB,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_executions_workflow_id ON workflow_executions(workflow_id);
CREATE INDEX idx_executions_user_id ON workflow_executions(user_id);
CREATE INDEX idx_executions_company_id ON workflow_executions(company_id);
CREATE INDEX idx_executions_uuid ON workflow_executions(execution_uuid);
CREATE INDEX idx_executions_status ON workflow_executions(status);
CREATE INDEX idx_executions_created_at ON workflow_executions(created_at);

-- ================================
-- 7. AGENTS
-- ================================

CREATE TABLE agents (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id) ON DELETE CASCADE,
    agent_uuid VARCHAR(255) UNIQUE NOT NULL DEFAULT gen_random_uuid()::TEXT,
    
    -- Agent details
    name VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'IDLE',
    description TEXT,
    
    -- AI Configuration
    llm_provider VARCHAR(50) DEFAULT 'openai',
    llm_model VARCHAR(100) DEFAULT 'gpt-4',
    system_prompt TEXT,
    max_tokens INTEGER DEFAULT 4000,
    temperature DECIMAL(3,2) DEFAULT 0.7,
    
    -- Capabilities
    capabilities JSONB,
    configuration JSONB,
    available_tools JSONB DEFAULT '[]'::jsonb,
    
    -- Performance metrics
    total_tasks_completed INTEGER DEFAULT 0,
    total_tasks_failed INTEGER DEFAULT 0,
    success_rate DECIMAL(5,2) DEFAULT 0.0,
    average_execution_time_seconds DECIMAL(10,2) DEFAULT 0.0,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    current_task_id VARCHAR(255),
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_agents_company_id ON agents(company_id);
CREATE INDEX idx_agents_uuid ON agents(agent_uuid);
CREATE INDEX idx_agents_role ON agents(role);
CREATE INDEX idx_agents_status ON agents(status);
CREATE INDEX idx_agents_active ON agents(is_active);

-- ================================
-- 8. APPROVAL REQUESTS
-- ================================

CREATE TABLE approval_requests (
    id SERIAL PRIMARY KEY,
    request_uuid VARCHAR(255) UNIQUE NOT NULL DEFAULT gen_random_uuid()::TEXT,
    workflow_execution_id INTEGER NOT NULL REFERENCES workflow_executions(id) ON DELETE CASCADE,
    company_id INTEGER REFERENCES companies(id) ON DELETE CASCADE,
    
    -- Request details
    requested_by INTEGER NOT NULL REFERENCES users(id),
    approver_email VARCHAR(255) NOT NULL,
    approver_user_id INTEGER REFERENCES users(id),
    
    -- Approval details
    workflow_name VARCHAR(255) NOT NULL,
    risk_level VARCHAR(20) NOT NULL,
    description TEXT,
    justification TEXT,
    
    -- Request context
    requested_action JSONB NOT NULL,
    impact_assessment JSONB,
    
    -- Status
    status VARCHAR(50) DEFAULT 'PENDING',
    decision_reason TEXT,
    confidence_score DECIMAL(3,2),
    
    -- URLs
    approval_url VARCHAR(500),
    
    -- Timing
    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    decided_at TIMESTAMP,
    
    -- Email tracking
    email_sent BOOLEAN DEFAULT FALSE,
    email_sent_at TIMESTAMP,
    reminder_count INTEGER DEFAULT 0,
    last_reminder_at TIMESTAMP
);

CREATE INDEX idx_approval_requests_execution_id ON approval_requests(workflow_execution_id);
CREATE INDEX idx_approval_requests_company_id ON approval_requests(company_id);
CREATE INDEX idx_approval_requests_requested_by ON approval_requests(requested_by);
CREATE INDEX idx_approval_requests_approver ON approval_requests(approver_user_id);
CREATE INDEX idx_approval_requests_status ON approval_requests(status);

-- ================================
-- 9. EMAIL NOTIFICATIONS
-- ================================

CREATE TABLE email_notifications (
    id SERIAL PRIMARY KEY,
    notification_uuid VARCHAR(255) UNIQUE NOT NULL DEFAULT gen_random_uuid()::TEXT,
    company_id INTEGER REFERENCES companies(id) ON DELETE CASCADE,
    
    -- Sender (user who configured the email)
    sender_user_id INTEGER NOT NULL REFERENCES users(id),
    sender_email VARCHAR(255) NOT NULL,
    sender_name VARCHAR(255) NOT NULL,
    
    -- Recipient
    recipient_email VARCHAR(255) NOT NULL,
    recipient_name VARCHAR(255),
    
    -- Email details
    subject VARCHAR(500) NOT NULL,
    email_type VARCHAR(100) NOT NULL,
    template_used VARCHAR(100),
    
    -- Related resources
    workflow_id INTEGER REFERENCES workflows(id),
    execution_id INTEGER REFERENCES workflow_executions(id),
    approval_request_id INTEGER REFERENCES approval_requests(id),
    
    -- Status
    status VARCHAR(50) DEFAULT 'PENDING',
    error_message TEXT,
    
    -- Timing
    scheduled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sent_at TIMESTAMP,
    delivered_at TIMESTAMP,
    
    -- Email content (for audit)
    email_content_hash VARCHAR(255),
    
    -- Metadata
    smtp_response TEXT,
    metadata JSONB
);

CREATE INDEX idx_notifications_sender_user_id ON email_notifications(sender_user_id);
CREATE INDEX idx_notifications_company_id ON email_notifications(company_id);
CREATE INDEX idx_notifications_recipient ON email_notifications(recipient_email);
CREATE INDEX idx_notifications_type ON email_notifications(email_type);
CREATE INDEX idx_notifications_status ON email_notifications(status);
CREATE INDEX idx_notifications_sent_at ON email_notifications(sent_at);

-- ================================
-- 10. INTEGRATIONS
-- ================================

CREATE TABLE integrations (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    integration_uuid VARCHAR(255) UNIQUE NOT NULL DEFAULT gen_random_uuid()::TEXT,
    
    -- Integration details
    name VARCHAR(255) NOT NULL,
    integration_type VARCHAR(100) NOT NULL,
    category VARCHAR(100),
    
    -- Connection details
    connection_status VARCHAR(50) DEFAULT 'DISCONNECTED',
    auth_type VARCHAR(50),
    
    -- Configuration
    config JSONB DEFAULT '{}'::jsonb,
    credentials JSONB DEFAULT '{}'::jsonb, -- Encrypted
    webhook_url VARCHAR(500),
    
    -- Usage metrics
    total_api_calls INTEGER DEFAULT 0,
    successful_calls INTEGER DEFAULT 0,
    failed_calls INTEGER DEFAULT 0,
    last_used_at TIMESTAMP,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_integrations_company_id ON integrations(company_id);
CREATE INDEX idx_integrations_type ON integrations(integration_type);
CREATE INDEX idx_integrations_status ON integrations(connection_status);

-- ================================
-- 11. AUDIT TRAIL
-- ================================

CREATE TABLE audit_trail (
    id SERIAL PRIMARY KEY,
    audit_uuid VARCHAR(255) UNIQUE NOT NULL DEFAULT gen_random_uuid()::TEXT,
    company_id INTEGER REFERENCES companies(id) ON DELETE CASCADE,
    
    -- Event details
    event_type VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100),
    resource_id VARCHAR(255),
    
    -- Actor information
    user_id INTEGER REFERENCES users(id),
    agent_id INTEGER REFERENCES agents(id),
    
    -- Event data
    event_description TEXT NOT NULL,
    old_values JSONB,
    new_values JSONB,
    metadata JSONB,
    
    -- Request context
    ip_address INET,
    user_agent TEXT,
    session_id VARCHAR(255),
    
    -- Status
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    
    -- Timestamp
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_trail_company_id ON audit_trail(company_id);
CREATE INDEX idx_audit_trail_user_id ON audit_trail(user_id);
CREATE INDEX idx_audit_trail_agent_id ON audit_trail(agent_id);
CREATE INDEX idx_audit_trail_event_type ON audit_trail(event_type);
CREATE INDEX idx_audit_trail_resource_type ON audit_trail(resource_type);
CREATE INDEX idx_audit_trail_created_at ON audit_trail(created_at);

-- ================================
-- 12. SYSTEM SETTINGS
-- ================================

CREATE TABLE system_settings (
    id SERIAL PRIMARY KEY,
    setting_key VARCHAR(255) UNIQUE NOT NULL,
    setting_value JSONB NOT NULL,
    setting_type VARCHAR(50) NOT NULL,
    description TEXT,
    
    -- Access control
    is_public BOOLEAN DEFAULT FALSE,
    requires_admin BOOLEAN DEFAULT TRUE,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ================================
-- 13. TRIGGERS FOR AUTO-UPDATES
-- ================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_companies_updated_at BEFORE UPDATE ON companies FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_workflows_updated_at BEFORE UPDATE ON workflows FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_workflow_executions_updated_at BEFORE UPDATE ON workflow_executions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_agents_updated_at BEFORE UPDATE ON agents FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_user_email_configs_updated_at BEFORE UPDATE ON user_email_configs FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_integrations_updated_at BEFORE UPDATE ON integrations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ================================
-- 14. SAMPLE DATA FOR DEMO
-- ================================

-- Insert sample companies
INSERT INTO companies (
    name, slug, description, industry, company_size, website_url,
    business_model, employee_count, subscription_tier, is_active, is_verified
) VALUES 
(
    'TechFlow Industries',
    'techflow-industries',
    'Leading technology solutions provider specializing in workflow automation and AI integration',
    'Technology',
    'medium',
    'https://techflow.com',
    'b2b',
    150,
    'pro',
    TRUE,
    TRUE
),
(
    'DataSync Corp',
    'datasync-corp',
    'Enterprise data integration and synchronization platform',
    'Software',
    'large',
    'https://datasync.com',
    'b2b2c',
    500,
    'enterprise',
    TRUE,
    TRUE
),
(
    'AutoMate Solutions',
    'automate-solutions',
    'Business process automation consultancy for small and medium businesses',
    'Consulting',
    'small',
    'https://automate-solutions.com',
    'b2b',
    25,
    'free',
    TRUE,
    TRUE
);

-- Insert demo users
INSERT INTO users (
    email, username, full_name, company, department, job_title,
    hashed_password, is_active, is_verified, is_admin
) VALUES 
(
    'admin@techflow.com',
    'admin_techflow',
    'John Smith',
    'TechFlow Industries',
    'DevOps',
    'Technical Lead',
    '$2b$12$dummy_hashed_password_for_admin_user_12345',
    TRUE,
    TRUE,
    TRUE
),
(
    'user@datasync.com',
    'user_datasync',
    'Sarah Johnson',
    'DataSync Corp',
    'Operations',
    'Operations Manager',
    '$2b$12$dummy_hashed_password_for_regular_user_123',
    TRUE,
    TRUE,
    FALSE
),
(
    'demo@automate.com',
    'demo_automate',
    'Mike Wilson',
    'AutoMate Solutions',
    'Consulting',
    'Senior Consultant',
    '$2b$12$dummy_hashed_password_for_demo_user_12345',
    TRUE,
    TRUE,
    FALSE
);

-- Link users to companies
INSERT INTO user_companies (user_id, company_id, role, is_active, is_primary, joined_at) VALUES 
(1, 1, 'owner', TRUE, TRUE, CURRENT_TIMESTAMP),
(2, 2, 'admin', TRUE, TRUE, CURRENT_TIMESTAMP),
(3, 3, 'manager', TRUE, TRUE, CURRENT_TIMESTAMP);

-- Insert sample agents
INSERT INTO agents (company_id, name, role, description, capabilities, is_active) VALUES
(1, 'TechFlow AI Planner', 'PLANNER', 'Plans and coordinates workflow execution for technology processes', '["workflow_planning", "task_scheduling", "resource_allocation", "tech_integration"]'::jsonb, TRUE),
(1, 'TechFlow AI Executor', 'EXECUTOR', 'Executes workflow steps and technical tasks', '["api_calls", "database_operations", "file_processing", "deployment"]'::jsonb, TRUE),
(2, 'DataSync AI Auditor', 'AUDITOR', 'Monitors and audits data synchronization workflows', '["compliance_checking", "performance_monitoring", "audit_reporting", "data_validation"]'::jsonb, TRUE),
(3, 'AutoMate AI Assistant', 'EXECUTOR', 'General purpose automation assistant for small businesses', '["document_processing", "email_automation", "basic_integrations"]'::jsonb, TRUE);

-- Insert sample workflows
INSERT INTO workflows (
    user_id, company_id, name, description, category, workflow_steps, risk_level, requires_approval
) VALUES 
(
    1, 1,
    'Production Database Backup',
    'Automated database backup and cloud storage process for production systems',
    'Database Management',
    '[
        {"step": 1, "name": "Create Backup", "type": "DATABASE_BACKUP", "timeout": 300},
        {"step": 2, "name": "Verify Backup", "type": "BACKUP_VERIFICATION", "timeout": 120},
        {"step": 3, "name": "Upload to Cloud", "type": "CLOUD_UPLOAD", "timeout": 600},
        {"step": 4, "name": "Send Notification", "type": "EMAIL_NOTIFICATION", "timeout": 30}
    ]'::jsonb,
    'MEDIUM',
    TRUE
),
(
    2, 2,
    'Customer Data Synchronization', 
    'Synchronize customer data across multiple systems and platforms',
    'Data Integration',
    '[
        {"step": 1, "name": "Extract Customer Data", "type": "DATA_EXTRACTION", "timeout": 180},
        {"step": 2, "name": "Transform Data Format", "type": "DATA_TRANSFORMATION", "timeout": 120},
        {"step": 3, "name": "Validate Data Quality", "type": "DATA_VALIDATION", "timeout": 90},
        {"step": 4, "name": "Load to Target Systems", "type": "DATA_LOAD", "timeout": 240},
        {"step": 5, "name": "Generate Sync Report", "type": "REPORT_GENERATION", "timeout": 60}
    ]'::jsonb,
    'HIGH',
    TRUE
),
(
    3, 3,
    'Weekly Report Automation',
    'Automated generation and distribution of weekly business reports',
    'Reporting',
    '[
        {"step": 1, "name": "Collect Weekly Data", "type": "DATA_COLLECTION", "timeout": 180},
        {"step": 2, "name": "Generate Charts", "type": "CHART_GENERATION", "timeout": 120},
        {"step": 3, "name": "Create PDF Report", "type": "PDF_GENERATION", "timeout": 90},
        {"step": 4, "name": "Email to Stakeholders", "type": "EMAIL_DISTRIBUTION", "timeout": 60}
    ]'::jsonb,
    'LOW',
    FALSE
);

-- Insert system settings
INSERT INTO system_settings (setting_key, setting_value, setting_type, description, is_public) VALUES
('app_name', '"OpsFlow Guardian 2.0"', 'STRING', 'Application name', TRUE),
('version', '"2.0.0"', 'STRING', 'Application version', TRUE),
('max_workflow_steps', '50', 'INTEGER', 'Maximum steps per workflow', FALSE),
('max_execution_time_minutes', '120', 'INTEGER', 'Maximum execution time per workflow', FALSE),
('default_approval_timeout_hours', '24', 'INTEGER', 'Default timeout for approval requests', FALSE),
('enable_audit_logging', 'true', 'BOOLEAN', 'Enable comprehensive audit logging', FALSE);

-- ================================
-- 15. DASHBOARD VIEWS
-- ================================

-- User dashboard summary
CREATE VIEW user_dashboard_summary AS
SELECT 
    u.id as user_id,
    u.full_name,
    u.email,
    u.company,
    uc.role as company_role,
    c.name as company_name,
    c.industry as company_industry,
    COUNT(DISTINCT w.id) as total_workflows,
    COUNT(DISTINCT we.id) as total_executions,
    COUNT(DISTINCT CASE WHEN we.status = 'SUCCESS' THEN we.id END) as successful_executions,
    COUNT(DISTINCT CASE WHEN we.status = 'FAILED' THEN we.id END) as failed_executions,
    COUNT(DISTINCT en.id) as total_emails_sent,
    COALESCE(uec.is_verified, FALSE) as email_configured
FROM users u
LEFT JOIN user_companies uc ON u.id = uc.user_id AND uc.is_primary = TRUE
LEFT JOIN companies c ON uc.company_id = c.id
LEFT JOIN workflows w ON u.id = w.user_id
LEFT JOIN workflow_executions we ON w.id = we.workflow_id
LEFT JOIN email_notifications en ON u.id = en.sender_user_id
LEFT JOIN user_email_configs uec ON u.id = uec.user_id
WHERE u.is_active = TRUE
GROUP BY u.id, u.full_name, u.email, u.company, uc.role, c.name, c.industry, uec.is_verified;

-- Company dashboard summary
CREATE VIEW company_dashboard_summary AS
SELECT 
    c.id as company_id,
    c.name as company_name,
    c.slug,
    c.industry,
    c.company_size,
    c.subscription_tier,
    COUNT(DISTINCT uc.user_id) as total_users,
    COUNT(DISTINCT a.id) as total_agents,
    COUNT(DISTINCT w.id) as total_workflows,
    COUNT(DISTINCT we.id) as total_executions,
    COUNT(DISTINCT CASE WHEN we.status = 'SUCCESS' THEN we.id END) as successful_executions,
    COUNT(DISTINCT CASE WHEN we.status = 'FAILED' THEN we.id END) as failed_executions,
    ROUND(
        CASE 
            WHEN COUNT(we.id) > 0 THEN 
                COUNT(CASE WHEN we.status = 'SUCCESS' THEN 1 END) * 100.0 / COUNT(we.id)
            ELSE 0 
        END, 2
    ) as success_rate_percentage,
    COUNT(DISTINCT i.id) as total_integrations
FROM companies c
LEFT JOIN user_companies uc ON c.id = uc.company_id AND uc.is_active = TRUE
LEFT JOIN agents a ON c.id = a.company_id AND a.is_active = TRUE
LEFT JOIN workflows w ON c.id = w.company_id AND w.is_active = TRUE
LEFT JOIN workflow_executions we ON w.id = we.workflow_id
LEFT JOIN integrations i ON c.id = i.company_id AND i.is_active = TRUE
WHERE c.is_active = TRUE
GROUP BY c.id, c.name, c.slug, c.industry, c.company_size, c.subscription_tier;

-- Workflow performance view
CREATE VIEW workflow_performance AS
SELECT 
    w.id as workflow_id,
    w.name as workflow_name,
    w.category,
    w.risk_level,
    u.full_name as owner_name,
    c.name as company_name,
    c.industry as company_industry,
    COUNT(we.id) as total_executions,
    COUNT(CASE WHEN we.status = 'SUCCESS' THEN 1 END) as successful_executions,
    COUNT(CASE WHEN we.status = 'FAILED' THEN 1 END) as failed_executions,
    COUNT(CASE WHEN we.status = 'PENDING' THEN 1 END) as pending_executions,
    ROUND(AVG(CASE WHEN we.duration_seconds > 0 THEN we.duration_seconds END), 2) as avg_duration_seconds,
    MAX(we.completed_at) as last_execution,
    ROUND(
        CASE 
            WHEN COUNT(we.id) > 0 THEN 
                COUNT(CASE WHEN we.status = 'SUCCESS' THEN 1 END) * 100.0 / COUNT(we.id)
            ELSE 0 
        END, 2
    ) as success_rate_percentage
FROM workflows w
LEFT JOIN users u ON w.user_id = u.id
LEFT JOIN companies c ON w.company_id = c.id
LEFT JOIN workflow_executions we ON w.id = we.workflow_id
WHERE w.is_active = TRUE
GROUP BY w.id, w.name, w.category, w.risk_level, u.full_name, c.name, c.industry;

-- Agent performance view
CREATE VIEW agent_performance AS
SELECT 
    a.id as agent_id,
    a.name as agent_name,
    a.role,
    a.status,
    c.name as company_name,
    c.industry as company_industry,
    a.total_tasks_completed,
    a.total_tasks_failed,
    a.success_rate,
    a.average_execution_time_seconds,
    COUNT(DISTINCT w.id) as associated_workflows,
    a.last_active,
    CASE 
        WHEN a.last_active IS NULL THEN 'Never Active'
        WHEN a.last_active > CURRENT_TIMESTAMP - INTERVAL '1 hour' THEN 'Recently Active'
        WHEN a.last_active > CURRENT_TIMESTAMP - INTERVAL '1 day' THEN 'Active Today'
        WHEN a.last_active > CURRENT_TIMESTAMP - INTERVAL '1 week' THEN 'Active This Week'
        ELSE 'Inactive'
    END as activity_status
FROM agents a
LEFT JOIN companies c ON a.company_id = c.id
LEFT JOIN workflows w ON a.id::TEXT = w.workflow_steps->0->>'agent_id'
WHERE a.is_active = TRUE
GROUP BY a.id, a.name, a.role, a.status, c.name, c.industry, 
         a.total_tasks_completed, a.total_tasks_failed, a.success_rate, 
         a.average_execution_time_seconds, a.last_active;

-- ================================
-- 16. AUDIT TRIGGERS
-- ================================

-- Function to create audit trail entries
CREATE OR REPLACE FUNCTION create_audit_trail()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        INSERT INTO audit_trail (
            event_type, resource_type, resource_id, event_description,
            old_values, success, created_at
        ) VALUES (
            'DELETE', TG_TABLE_NAME, OLD.id::TEXT, 
            'Record deleted from ' || TG_TABLE_NAME,
            row_to_json(OLD), TRUE, CURRENT_TIMESTAMP
        );
        RETURN OLD;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO audit_trail (
            event_type, resource_type, resource_id, event_description,
            old_values, new_values, success, created_at
        ) VALUES (
            'UPDATE', TG_TABLE_NAME, NEW.id::TEXT,
            'Record updated in ' || TG_TABLE_NAME,
            row_to_json(OLD), row_to_json(NEW), TRUE, CURRENT_TIMESTAMP
        );
        RETURN NEW;
    ELSIF TG_OP = 'INSERT' THEN
        INSERT INTO audit_trail (
            event_type, resource_type, resource_id, event_description,
            new_values, success, created_at
        ) VALUES (
            'INSERT', TG_TABLE_NAME, NEW.id::TEXT,
            'Record created in ' || TG_TABLE_NAME,
            row_to_json(NEW), TRUE, CURRENT_TIMESTAMP
        );
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Apply audit triggers to important tables
CREATE TRIGGER audit_users AFTER INSERT OR UPDATE OR DELETE ON users FOR EACH ROW EXECUTE FUNCTION create_audit_trail();
CREATE TRIGGER audit_companies AFTER INSERT OR UPDATE OR DELETE ON companies FOR EACH ROW EXECUTE FUNCTION create_audit_trail();
CREATE TRIGGER audit_workflows AFTER INSERT OR UPDATE OR DELETE ON workflows FOR EACH ROW EXECUTE FUNCTION create_audit_trail();
CREATE TRIGGER audit_workflow_executions AFTER INSERT OR UPDATE OR DELETE ON workflow_executions FOR EACH ROW EXECUTE FUNCTION create_audit_trail();
CREATE TRIGGER audit_agents AFTER INSERT OR UPDATE OR DELETE ON agents FOR EACH ROW EXECUTE FUNCTION create_audit_trail();

-- ================================
-- SETUP COMPLETE MESSAGE
-- ================================

SELECT 
    'Database setup complete!' as message,
    COUNT(*) as tables_created
FROM information_schema.tables 
WHERE table_schema = 'public' 
    AND table_type = 'BASE TABLE'
    AND table_name NOT LIKE 'pg_%'
    AND table_name NOT LIKE 'information_schema%';

-- Display table summary
SELECT 
    table_name,
    (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name) as column_count
FROM information_schema.tables t
WHERE table_schema = 'public' 
    AND table_type = 'BASE TABLE'
    AND table_name NOT LIKE 'pg_%'
ORDER BY table_name;
