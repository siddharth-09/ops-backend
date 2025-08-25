#!/bin/bash

echo "🎉 OpsFlow Guardian 2.0 - Quick Setup & Start"
echo "=============================================="

# Navigate to backend directory
cd "$(dirname "$0")"

echo "📍 Current directory: $(pwd)"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "🐍 Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Check if PostgreSQL is running
echo "🔍 Checking PostgreSQL status..."
if ! pgrep -x "postgres" > /dev/null; then
    echo "⚠️ PostgreSQL is not running!"
    echo "📋 To start PostgreSQL:"
    echo "   Ubuntu/Debian: sudo systemctl start postgresql"
    echo "   macOS: brew services start postgresql"
    echo "   Docker: docker run --name postgres-opsflow -e POSTGRES_PASSWORD=password -d -p 5432:5432 postgres"
    echo ""
    echo "❓ Do you want to continue anyway? (y/N)"
    read -r continue_anyway
    if [[ ! $continue_anyway =~ ^[Yy]$ ]]; then
        echo "❌ Stopping setup. Please start PostgreSQL first."
        exit 1
    fi
fi

# Setup database
echo "🔧 Setting up database..."
python setup_database.py

# Check if setup was successful
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Database setup completed!"
    echo "🚀 Starting OpsFlow Guardian 2.0 backend..."
    echo ""
    python main.py
else
    echo "❌ Database setup failed!"
    echo "🔧 Manual setup instructions:"
    echo "1. Ensure PostgreSQL is running"
    echo "2. Create user: createuser -s opsflow"
    echo "3. Set password: psql -c \"ALTER USER opsflow PASSWORD 'password';\""
    echo "4. Create database: createdb -O opsflow opsflow_guardian" 
    echo "5. Run setup: python setup_database.py"
    exit 1
fi
