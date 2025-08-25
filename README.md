# OpsFlow Guardian 2.0 Backend

AI-powered enterprise workflow automation platform built with FastAPI and PostgreSQL database integration.

## 🚀 Quick Start

### Option 1: Automatic Setup (Recommended)
```bash
cd backend
chmod +x quick_start.sh
./quick_start.sh
```

### Option 2: Docker Compose
```bash
cd backend
docker-compose up -d
```

### Option 3: Manual Setup
```bash
cd backend

# Create virtual environment (Python 3.12 recommended)
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Setup PostgreSQL Database
# Ubuntu/Debian: sudo apt install postgresql postgresql-contrib
# macOS: brew install postgresql
# Or using Docker: docker run --name postgres-opsflow -e POSTGRES_PASSWORD=password -d -p 5432:5432 postgres

# Create database user and database
sudo -u postgres psql
CREATE USER opsflow WITH PASSWORD 'password';
ALTER USER opsflow CREATEDB;
CREATE DATABASE opsflow_guardian OWNER opsflow;
\q

# Initialize database with schema
python setup_database.py

# Start the server
python main.py
```

**Note**: The system now uses PostgreSQL for production-ready data persistence with complete audit trails.

## 📁 Project Structure

```
backend/
├── main.py                 # FastAPI application entry point
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
├── start.sh              # Quick start script
├── Dockerfile            # Docker configuration
├── docker-compose.yml    # Multi-service setup
├── app/
│   ├── __init__.py
│   ├── api/              # API endpoints
│   │   └── v1/
│   │       ├── __init__.py
│   │       └── endpoints/
│   │           ├── agents.py      # Agent management
│   │           ├── analytics.py   # Analytics & reporting
│   │           ├── approvals.py   # Approval workflows
│   │           ├── audit.py       # Audit trails
│   │           ├── auth.py        # Authentication
│   │           └── workflows.py   # Workflow management
│   ├── core/             # Core configuration
│   │   ├── __init__.py
│   │   ├── config.py     # Settings management
│   │   ├── database.py   # Database setup
│   │   ├── middleware.py # Custom middleware
│   │   └── websocket.py  # WebSocket manager
│   ├── models/           # Data models
│   │   ├── __init__.py
│   │   ├── agent.py      # Agent models
│   │   ├── user.py       # User models
│   │   └── workflow.py   # Workflow models
│   └── services/         # Business logic
│       ├── __init__.py
│       ├── integration_service.py  # External integrations
│       ├── portia_service.py      # Portia SDK integration
│       └── redis_service.py       # Redis operations
└── logs/                 # Application logs
```

## 🔧 Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

**Required:**
- `PORTIA_API_KEY`: Your Portia API key
- `SECRET_KEY`: Secure random string for JWT tokens
- `DATABASE_URL`: Database connection string

**Optional but Recommended:**
- `REDIS_URL`: Redis connection for caching
- `OPENAI_API_KEY`: OpenAI API for enhanced AI features
- External service API keys (Google, Slack, Notion, Jira)

### Database Setup

**PostgreSQL (Production Ready):**
```
DATABASE_URL=postgresql://opsflow:password@localhost:5432/opsflow_guardian
```

The system includes a complete PostgreSQL schema with:
- 10 production tables (users, organizations, agents, workflows, etc.)
- Audit logging with triggers
- Analytics views and indexes
- Sample data for testing
- Database health monitoring

**Initialize Database:**
```bash
python setup_database.py
```

**Test Database Connection:**
```bash
python setup_database.py test
```

## 🤖 Multi-Agent System

The backend implements a three-agent architecture using Portia SDK:

### 1. **Planner Agent**
- Analyzes workflow requirements
- Creates detailed execution plans
- Identifies dependencies and resources

### 2. **Executor Agent** 
- Executes workflow steps
- Handles external integrations
- Manages state transitions

### 3. **Auditor Agent**
- Monitors execution progress
- Validates completions
- Generates audit trails

## 🔌 API Endpoints

### Authentication
- `POST /auth/login` - User authentication
- `POST /auth/register` - User registration
- `POST /auth/refresh` - Token refresh

### Agents
- `GET /agents` - List all agents
- `POST /agents` - Create new agent
- `GET /agents/{id}` - Get agent details
- `PUT /agents/{id}` - Update agent
- `DELETE /agents/{id}` - Delete agent
- `POST /agents/{id}/activate` - Activate agent
- `POST /agents/{id}/deactivate` - Deactivate agent

### Workflows
- `GET /workflows` - List workflows
- `POST /workflows` - Create workflow
- `GET /workflows/{id}` - Get workflow details
- `PUT /workflows/{id}` - Update workflow
- `DELETE /workflows/{id}` - Delete workflow
- `POST /workflows/{id}/execute` - Execute workflow
- `GET /workflows/{id}/status` - Get execution status

### Approvals
- `GET /approvals` - List pending approvals
- `POST /approvals/{id}/approve` - Approve request
- `POST /approvals/{id}/reject` - Reject request
- `GET /approvals/stats` - Approval statistics

### Audit
- `GET /audit` - List audit trails
- `GET /audit/{id}` - Get audit details
- `GET /audit/export` - Export audit data

### Analytics
- `GET /analytics/dashboard` - Dashboard metrics
- `GET /analytics/performance` - Performance metrics
- `GET /analytics/costs` - Cost analysis

## 🔄 Real-time Features

### WebSocket Connections
```javascript
// Frontend integration
const ws = new WebSocket('ws://localhost:8000/ws');
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    // Handle real-time updates
};
```

### Supported Events
- `workflow_started` - Workflow execution began
- `workflow_completed` - Workflow finished
- `workflow_failed` - Workflow encountered error
- `agent_status_changed` - Agent status update
- `approval_requested` - New approval needed

## 🛠 Development

### Adding New Endpoints
1. Create endpoint in `app/api/v1/endpoints/`
2. Add models in `app/models/`
3. Implement business logic in `app/services/`
4. Register routes in `main.py`

### Testing
```bash
# Install dev dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest

# Run with coverage
pytest --cov=app
```

### Code Quality
```bash
# Format code
black app/
isort app/

# Lint code
flake8 app/
mypy app/
```

## 🚀 Deployment

### Docker Production
```bash
# Build image
docker build -t opsflow-guardian-backend .

# Run container
docker run -p 8000:8000 --env-file .env opsflow-guardian-backend
```

### Traditional Deployment
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment
export ENV=production
export DEBUG=false

# Run with gunicorn
pip install gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
```

## 📊 Monitoring

### Health Checks
- `GET /health` - Application health
- `GET /metrics` - Prometheus metrics
- `GET /docs` - API documentation

### Logging
Logs are written to `logs/` directory:
- `app.log` - Application logs
- `error.log` - Error logs
- `access.log` - API access logs

## 🔐 Security Features

- JWT token authentication
- Rate limiting middleware
- CORS configuration
- Request validation
- SQL injection prevention
- XSS protection headers

## 🤝 Integration Examples

### Slack Integration
```python
# Send workflow notification to Slack
await integration_service.send_slack_message(
    channel="#workflows",
    message="Workflow 'Invoice Processing' completed successfully"
)
```

### Google Workspace
```python
# Create Google Calendar event
await integration_service.create_calendar_event(
    title="Workflow Review Meeting",
    start_time="2024-01-15T14:00:00Z",
    attendees=["team@company.com"]
)
```

## 🆘 Troubleshooting

### Common Issues

**Port already in use:**
```bash
lsof -ti:8000 | xargs kill -9
```

**Database connection error:**
- Check DATABASE_URL in .env
- Ensure database server is running
- Verify credentials

**Portia API errors:**
- Verify PORTIA_API_KEY is correct
- Check API quota limits
- Review logs for detailed errors

### Getting Help

1. Check logs in `logs/` directory
2. Review environment configuration
3. Test API endpoints with `/docs`
4. Verify all services are running

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**Status**: ✅ Demo Ready | 🚧 Production Setup Required | 📈 Scalable Architecture
