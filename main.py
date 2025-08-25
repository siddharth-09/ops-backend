"""
OpsFlow Guardian 2.0 - Simplified Main Application Entry Point
FastAPI-based backend with Supabase (PostgreSQL) database integration
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import logging
import os
from dotenv import load_dotenv
import asyncio

# Load environment variables
load_dotenv()

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import database initialization
from app.db.database import initialize_database, get_database_health

# Create FastAPI application
app = FastAPI(
    title="OpsFlow Guardian 2.0",
    description="AI-Powered Enterprise Workflow Automation with Supabase Database & Human Oversight",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:8082", 
        "http://localhost:8081", 
        "http://localhost:8080",
        "http://localhost:3000", 
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8082",
        "http://127.0.0.1:8081",
        "http://127.0.0.1:8080",
        "http://127.0.0.1:3000",
        "https://opsflow-guardian.vercel.app",
        "https://ops-backend-production-9594.up.railway.app"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)

# Import simplified API endpoints
from app.api.v1 import endpoints

# Try to import Google OAuth router
try:
    from app.api.v1.auth import router as google_auth_router
    google_oauth_available = True
except ImportError as e:
    logger.warning(f"Google OAuth not available: {e}")
    google_oauth_available = False

# Register routes directly
app.include_router(endpoints.agents.router, prefix="/api/v1/agents", tags=["Agents"])
app.include_router(endpoints.workflows.router, prefix="/api/v1/workflows", tags=["Workflows"])
app.include_router(endpoints.approvals.router, prefix="/api/v1/approvals", tags=["Approvals"])
app.include_router(endpoints.audit.router, prefix="/api/v1/audit", tags=["Audit"])
app.include_router(endpoints.analytics.router, prefix="/api/v1/analytics", tags=["Analytics"])
app.include_router(endpoints.auth.router, prefix="/api/v1/auth", tags=["Authentication"])
if google_oauth_available:
    app.include_router(google_auth_router, tags=["Google Authentication"])
app.include_router(endpoints.company.router, prefix="/api/v1", tags=["Company Profile"])


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    logger.info("🚀 Starting OpsFlow Guardian 2.0...")
    
    # Initialize database connection
    try:
        initialize_database()
        logger.info("✅ Database initialization successful")
    except Exception as e:
        logger.error(f"❌ Database startup error: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up database connections on shutdown"""
    logger.info("🛑 Shutting down OpsFlow Guardian 2.0...")
    logger.info("✅ Shutdown complete")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "OpsFlow Guardian 2.0 - AI-Powered Workflow Automation",
        "version": "2.0.0",
        "status": "operational",
        "docs": "/docs",
        "database": "supabase (postgresql)",
        "features": [
            "Supabase database integration",
            "AI-powered workflow automation",
            "Google OAuth authentication",
            "Company-specific personalization", 
            "Complete audit trails",
            "Human approval workflows",
            "Real-time monitoring"
        ]
    }


@app.get("/health")
async def health_check():
    """Health check endpoint with database status"""
    try:
        db_health = get_database_health()
        
        return {
            "status": "healthy" if db_health["status"] == "healthy" else "degraded",
            "version": "2.0.0",
            "services": {
                "api": "operational",
                "database": db_health["status"],
                "database_type": db_health["database_type"]
            },
            "database_info": db_health.get("database_info", {}),
            "connection_pool": db_health.get("connection_pool", {})
        }
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {
            "status": "unhealthy",
            "version": "2.0.0", 
            "error": str(e)
        }


@app.get("/database/status")
async def database_status():
    """Detailed database status endpoint"""
    try:
        db_health = get_database_health()
        
        return {
            "connected": db_health["status"] == "healthy",
            "database_type": db_health["database_type"],
            "database_info": db_health.get("database_info", {}),
            "connection_pool": db_health.get("connection_pool", {}),
            "features": db_health.get("features", {}),
            "status": db_health["status"],
            "connection_url": os.getenv("DATABASE_URL", "").replace("password", "***") if "DATABASE_URL" in os.environ else "not configured"
        }
        
    except Exception as e:
        return {
            "connected": False,
            "error": str(e),
            "setup_instructions": [
                "1. Create Supabase project at supabase.com",
                "2. Run the supabase_setup.sql script in SQL Editor",
                "3. Update DATABASE_URL environment variable with Supabase connection string"
            ]
        }

