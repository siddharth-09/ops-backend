#!/usr/bin/env python3
"""
Database Setup Script for OpsFlow Guardian 2.0
Run this script to set up the PostgreSQL database with all required tables and sample data
"""

import asyncio
import os
import sys
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def setup_database():
    """Setup PostgreSQL database"""
    try:
        import asyncpg
        from app.db.database import DATABASE_URL
        
        logger.info("🔧 Starting database setup...")
        
        # Parse database URL
        if not DATABASE_URL:
            logger.error("❌ DATABASE_URL not found in environment variables")
            return False
            
        # Extract database name from URL
        db_name = DATABASE_URL.split('/')[-1]
        base_url = DATABASE_URL.rsplit('/', 1)[0] + '/postgres'
        
        logger.info(f"📊 Setting up database: {db_name}")
        
        # Connect to postgres database to create our database
        try:
            conn = await asyncpg.connect(base_url)
            
            # Check if database exists
            db_exists = await conn.fetchval(
                "SELECT 1 FROM pg_database WHERE datname = $1", db_name
            )
            
            if not db_exists:
                logger.info(f"🏗️ Creating database: {db_name}")
                await conn.execute(f"CREATE DATABASE {db_name}")
            else:
                logger.info(f"✅ Database {db_name} already exists")
                
            await conn.close()
            
        except Exception as e:
            logger.error(f"❌ Failed to create database: {e}")
            return False
        
        # Now connect to our database and run setup
        logger.info("📋 Reading SQL setup file...")
        
        sql_file_path = os.path.join(os.path.dirname(__file__), "COMPLETE_DATABASE_SETUP.sql")
        
        if not os.path.exists(sql_file_path):
            logger.error(f"❌ SQL setup file not found: {sql_file_path}")
            return False
            
        with open(sql_file_path, 'r') as f:
            sql_content = f.read()
            
        # Split SQL into individual statements
        statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
        
        logger.info(f"🔄 Executing {len(statements)} SQL statements...")
        
        conn = await asyncpg.connect(DATABASE_URL)
        
        success_count = 0
        for i, statement in enumerate(statements, 1):
            try:
                # Skip comments and empty statements
                if statement.startswith('--') or not statement.strip():
                    continue
                    
                await conn.execute(statement)
                success_count += 1
                
                if i % 10 == 0:  # Progress indicator
                    logger.info(f"📈 Progress: {i}/{len(statements)} statements executed")
                    
            except Exception as e:
                # Some statements might fail if objects already exist
                if "already exists" in str(e).lower():
                    logger.debug(f"⚠️ Statement {i} skipped (already exists): {str(e)[:100]}")
                    continue
                else:
                    logger.warning(f"⚠️ Statement {i} failed: {str(e)[:100]}")
        
        # Verify setup
        logger.info("🔍 Verifying database setup...")
        
        table_count = await conn.fetchval("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
        """)
        
        user_count = await conn.fetchval("SELECT COUNT(*) FROM users")
        
        await conn.close()
        
        logger.info(f"✅ Database setup completed!")
        logger.info(f"📊 Tables created: {table_count}")
        logger.info(f"👥 Sample users: {user_count}")
        logger.info(f"🎯 Successful statements: {success_count}/{len(statements)}")
        
        return True
        
    except ImportError:
        logger.error("❌ asyncpg not installed. Run: pip install asyncpg")
        return False
    except Exception as e:
        logger.error(f"❌ Database setup failed: {e}")
        return False


async def test_database():
    """Test database connection and basic queries"""
    try:
        import asyncpg
        from app.db.database import DATABASE_URL
        
        logger.info("🧪 Testing database connection...")
        
        conn = await asyncpg.connect(DATABASE_URL)
        
        # Test basic query
        version = await conn.fetchval("SELECT version()")
        logger.info(f"🗄️ PostgreSQL version: {version.split(',')[0]}")
        
        # Test table queries
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        
        logger.info(f"📋 Available tables: {[t['table_name'] for t in tables]}")
        
        # Test sample data
        org_count = await conn.fetchval("SELECT COUNT(*) FROM organizations")
        user_count = await conn.fetchval("SELECT COUNT(*) FROM users") 
        agent_count = await conn.fetchval("SELECT COUNT(*) FROM agents")
        workflow_count = await conn.fetchval("SELECT COUNT(*) FROM workflows")
        
        logger.info(f"📊 Sample data counts:")
        logger.info(f"   Organizations: {org_count}")
        logger.info(f"   Users: {user_count}")
        logger.info(f"   Agents: {agent_count}")
        logger.info(f"   Workflows: {workflow_count}")
        
        await conn.close()
        
        logger.info("✅ Database test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database test failed: {e}")
        return False


def main():
    """Main setup function"""
    print("🎉 OpsFlow Guardian 2.0 - Database Setup")
    print("=" * 50)
    
    # Check if we have required dependencies
    try:
        import asyncpg
    except ImportError:
        print("❌ Missing required dependency: asyncpg")
        print("📦 Install with: pip install asyncpg")
        sys.exit(1)
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # Test mode
        success = asyncio.run(test_database())
    else:
        # Setup mode
        success = asyncio.run(setup_database())
        
        if success:
            print("\n🔧 Testing the setup...")
            asyncio.run(test_database())
    
    if success:
        print("\n✅ Database setup completed successfully!")
        print("🚀 You can now start the backend server with: python main.py")
    else:
        print("\n❌ Database setup failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
