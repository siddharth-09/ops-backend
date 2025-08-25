"""
Database configuration for OpsFlow Guardian 2.0 - Supabase Edition
Handles connection pooling, session management, and health checks
"""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from typing import Generator
import logging

logger = logging.getLogger(__name__)

# Database URL
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is required")

# Supabase connection detection and optimization
is_supabase = "supabase.co" in DATABASE_URL
connection_args = {}

if is_supabase:
    # Supabase-specific optimizations
    connection_args = {
        "sslmode": "require",  # Supabase requires SSL
        "connect_timeout": 10,
        "application_name": "OpsFlow Guardian 2.0"
    }
    logger.info("🟢 Detected Supabase database connection")
else:
    logger.info("🟡 Using standard PostgreSQL connection")

# Create database engine with optimized settings for cloud deployment
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=5,  # Reduced for Supabase free tier
    max_overflow=10,
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=3600,  # Recycle connections every hour
    connect_args=connection_args,
    echo=False  # Set to True for SQL query logging in development
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Import all database models to ensure they're registered with SQLAlchemy
try:
    from app.models.database_models import (
        Base, User, UserEmailConfig, Company, UserCompany, Agent, 
        Workflow, WorkflowExecution, ApprovalRequest, EmailNotification,
        Integration, AuditTrail, SystemSettings
    )
    logger.info("✅ Successfully imported all database models")
except ImportError as e:
    logger.error(f"❌ Failed to import database models: {e}")
    raise

def get_database_session() -> Generator:
    """
    Get database session with proper cleanup
    Use this as a dependency in FastAPI endpoints
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """Create all database tables"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created successfully")
    except Exception as e:
        logger.error(f"❌ Failed to create database tables: {e}")
        raise

def get_database_health() -> dict:
    """
    Check database health and return status information
    """
    try:
        with engine.connect() as connection:
            # Test basic connectivity
            result = connection.execute(text("SELECT 1 as health_check"))
            health_check = result.fetchone()[0]
            
            # Get database info
            db_version_result = connection.execute(text("SELECT version()"))
            db_version = db_version_result.fetchone()[0]
            
            # Get connection count (if available)
            try:
                conn_count_result = connection.execute(text("""
                    SELECT count(*) as active_connections 
                    FROM pg_stat_activity 
                    WHERE state = 'active'
                """))
                active_connections = conn_count_result.fetchone()[0]
            except Exception:
                active_connections = "unknown"
            
            # Get table count
            try:
                table_count_result = connection.execute(text("""
                    SELECT COUNT(*) as table_count 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_type = 'BASE TABLE'
                """))
                table_count = table_count_result.fetchone()[0]
            except Exception:
                table_count = "unknown"
            
            return {
                "status": "healthy" if health_check == 1 else "unhealthy",
                "database_type": "Supabase PostgreSQL" if is_supabase else "PostgreSQL",
                "connection_pool": {
                    "size": engine.pool.size(),
                    "checked_in": engine.pool.checkedin(),
                    "checked_out": engine.pool.checkedout(),
                    "overflow": engine.pool.overflow(),
                },
                "database_info": {
                    "version": db_version.split(" ")[1] if " " in db_version else db_version,
                    "active_connections": active_connections,
                    "table_count": table_count,
                },
                "features": {
                    "ssl_enabled": is_supabase,
                    "connection_pooling": True,
                    "auto_reconnect": True,
                    "row_level_security": is_supabase,
                    "realtime_subscriptions": is_supabase,
                }
            }
            
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "database_type": "Supabase PostgreSQL" if is_supabase else "PostgreSQL",
            "connection_pool": {
                "size": 0,
                "checked_in": 0,
                "checked_out": 0,
                "overflow": 0,
            }
        }

def initialize_database():
    """
    Initialize database with tables and basic data
    Called on application startup
    """
    try:
        logger.info("🚀 Initializing database...")
        
        # Create tables
        create_tables()
        
        # Test connection
        health = get_database_health()
        if health["status"] == "healthy":
            logger.info(f"✅ Database initialized successfully")
            logger.info(f"📊 Database type: {health['database_type']}")
            logger.info(f"📈 Tables created: {health['database_info'].get('table_count', 'unknown')}")
            if is_supabase:
                logger.info("🔒 Row Level Security enabled")
                logger.info("⚡ Real-time subscriptions available")
        else:
            logger.error(f"❌ Database health check failed: {health.get('error', 'Unknown error')}")
            
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise

# Dependency for FastAPI route handlers
def get_db():
    """FastAPI dependency to get database session"""
    return get_database_session()

# For backwards compatibility with existing code
get_database = get_database_session

import os
import logging
from typing import Generator
from sqlalchemy import create_engine, text, inspect, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import OperationalError
from dotenv import load_dotenv
import asyncio
import asyncpg

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Get Supabase database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://opsflow:password@localhost:5432/opsflow_guardian")

logger.info(f"🔗 Connecting to Supabase: {DATABASE_URL.replace('password', '***')}")

# SQLAlchemy setup optimized for Supabase
engine = create_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL query logging
    pool_size=5,  # Reduced for Supabase free tier
    max_overflow=10,
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=3600,   # Recycle connections after 1 hour
    connect_args={"sslmode": "require"} if "supabase.co" in DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def test_connection():
    """Test database connection"""
    try:
        # Parse DATABASE_URL for asyncpg connection
        import urllib.parse as urlparse
        url = urlparse.urlparse(DATABASE_URL)
        
        # Connect using asyncpg for testing
        conn = await asyncpg.connect(
            host=url.hostname,
            port=url.port or 5432,
            user=url.username,
            password=url.password,
            database=url.path[1:]  # Remove leading slash
        )
        
        # Test query
        result = await conn.fetchval("SELECT version()")
        logger.info(f"✅ Database connected successfully: {result}")
        
        await conn.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False


def check_database_exists():
    """Check if database exists and is accessible"""
    try:
        # Test connection with SQLAlchemy
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            logger.info("✅ SQLAlchemy database connection successful")
            return True
            
    except OperationalError as e:
        logger.error(f"❌ Database connection error: {e}")
        if "does not exist" in str(e):
            logger.warning("🚨 Database does not exist. Please run the setup SQL script first.")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected database error: {e}")
        return False


async def init_db():
    """Initialize database connection and verify setup"""
    try:
        logger.info("🚀 Initializing database connection...")
        
        # Test async connection
        if await test_connection():
            logger.info("✅ Async database connection test passed")
        else:
            logger.warning("⚠️ Async database connection test failed, but continuing...")
        
        # Test SQLAlchemy connection
        if check_database_exists():
            logger.info("✅ SQLAlchemy database connection verified")
        else:
            raise Exception("Database connection verification failed")
        
        # Check if tables exist
        with engine.connect() as connection:
            result = connection.execute(text("""
                SELECT COUNT(*) as table_count 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
            """))
            table_count = result.fetchone()[0]
            
            if table_count > 0:
                logger.info(f"✅ Found {table_count} tables in database")
            else:
                logger.warning("⚠️ No tables found. Please run COMPLETE_DATABASE_SETUP.sql")
        
        logger.info("✅ Database initialization completed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {e}")
        logger.info("💡 To fix this, please:")
        logger.info("1. Ensure PostgreSQL is running")
        logger.info("2. Run: psql -U postgres -c 'CREATE DATABASE opsflow_guardian;'")
        logger.info("3. Run: psql -U postgres -f COMPLETE_DATABASE_SETUP.sql")
        return False


async def get_database():
    """Get database connection"""
    return SessionLocal()


async def close_db():
    """Close database connections"""
    try:
        logger.info("🔒 Closing database connections...")
        engine.dispose()
        logger.info("✅ Database connections closed")
        
    except Exception as e:
        logger.error(f"❌ Error closing database: {e}")


# Utility functions for raw SQL queries
async def execute_raw_query(query: str, params: dict = None):
    """Execute raw SQL query with asyncpg"""
    try:
        import urllib.parse as urlparse
        url = urlparse.urlparse(DATABASE_URL)
        
        conn = await asyncpg.connect(
            host=url.hostname,
            port=url.port or 5432,
            user=url.username,
            password=url.password,
            database=url.path[1:]
        )
        
        if params:
            result = await conn.fetch(query, *params.values())
        else:
            result = await conn.fetch(query)
            
        await conn.close()
        return result
        
    except Exception as e:
        logger.error(f"Error executing raw query: {e}")
        return None


def execute_sync_query(query: str, params: dict = None):
    """Execute raw SQL query with SQLAlchemy (synchronous)"""
    try:
        with engine.connect() as connection:
            if params:
                result = connection.execute(text(query), params)
            else:
                result = connection.execute(text(query))
            return result.fetchall()
            
    except Exception as e:
        logger.error(f"Error executing sync query: {e}")
        return None
