#!/bin/bash

echo "🗄️ PostgreSQL Database Setup for OpsFlow Guardian 2.0"
echo "=================================================="

# Check if PostgreSQL is running
if ! pgrep -x "postgres" > /dev/null; then
    echo "❌ PostgreSQL is not running!"
    echo "To start PostgreSQL:"
    echo "   sudo systemctl start postgresql"
    echo "   # OR"
    echo "   sudo service postgresql start"
    exit 1
fi

echo "✅ PostgreSQL is running"

# Database configuration
DB_NAME="opsflow_guardian"
DB_USER="opsflow" 
DB_PASSWORD="password"

echo "🔧 Setting up database: $DB_NAME"
echo "👤 User: $DB_USER"
echo ""

# Create database and user
echo "1️⃣ Creating database and user..."

# Switch to postgres user and create database
sudo -u postgres psql << EOF
-- Drop database if exists (for fresh start)
DROP DATABASE IF EXISTS $DB_NAME;
DROP USER IF EXISTS $DB_USER;

-- Create user
CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
ALTER USER $DB_USER CREATEDB;

-- Create database
CREATE DATABASE $DB_NAME OWNER $DB_USER;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;

\q
EOF

if [ $? -eq 0 ]; then
    echo "✅ Database and user created successfully"
else
    echo "❌ Failed to create database and user"
    exit 1
fi

# Execute the schema file
echo ""
echo "2️⃣ Creating tables and inserting sample data..."

# Execute the SQL file
if [ -f "NEW_DATABASE_SETUP.sql" ]; then
    PGPASSWORD=$DB_PASSWORD psql -h localhost -U $DB_USER -d $DB_NAME -f NEW_DATABASE_SETUP.sql
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "✅ Database schema created successfully!"
        echo ""
        echo "3️⃣ Verifying setup..."
        
        # Check tables
        PGPASSWORD=$DB_PASSWORD psql -h localhost -U $DB_USER -d $DB_NAME -c "
        SELECT 
            'Tables created: ' || COUNT(*) as summary
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_type = 'BASE TABLE';"
        
        echo ""
        echo "4️⃣ Checking sample data..."
        
        # Check sample data
        PGPASSWORD=$DB_PASSWORD psql -h localhost -U $DB_USER -d $DB_NAME -c "
        SELECT 'Companies: ' || COUNT(*) FROM companies;
        SELECT 'Users: ' || COUNT(*) FROM users;
        SELECT 'Workflows: ' || COUNT(*) FROM workflows;
        SELECT 'Agents: ' || COUNT(*) FROM agents;"
        
        echo ""
        echo "🎉 Database setup completed successfully!"
        echo ""
        echo "📋 Connection Details:"
        echo "   Database: $DB_NAME"
        echo "   Host: localhost"
        echo "   Port: 5432"  
        echo "   Username: $DB_USER"
        echo "   Password: $DB_PASSWORD"
        echo ""
        echo "🔗 Connection String:"
        echo "   postgresql://$DB_USER:$DB_PASSWORD@localhost:5432/$DB_NAME"
        echo ""
        echo "🚀 Ready to start your application!"
        echo "   You can now update your .env file with the connection string"
        
    else
        echo "❌ Failed to execute schema file"
        exit 1
    fi
else
    echo "❌ NEW_DATABASE_SETUP.sql file not found"
    echo "Make sure you're running this script from the backend directory"
    exit 1
fi
