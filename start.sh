#!/bin/bash

# OpsFlow Guardian 2.0 Backend Startup Script
echo "🚀 Starting OpsFlow Guardian 2.0 Backend..."

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "${BLUE}📦 Creating virtual environment...${NC}"
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "❌ Failed to create virtual environment"
        exit 1
    fi
fi

# Activate virtual environment
echo -e "${BLUE}🔧 Activating virtual environment...${NC}"
source venv/bin/activate

# Install dependencies
echo -e "${BLUE}📋 Installing dependencies...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚙️  Creating .env file from template...${NC}"
    cp .env.example .env
    echo -e "${YELLOW}📝 Please edit .env file with your actual configuration values!${NC}"
fi

# Start the FastAPI server
echo -e "${GREEN}🎯 Starting OpsFlow Guardian 2.0 API Server...${NC}"
echo -e "${BLUE}📊 Dashboard will be available at: http://localhost:8000/docs${NC}"
echo -e "${BLUE}🔗 Health check at: http://localhost:8000/health${NC}"
echo ""

# Use python3 and handle uvicorn import gracefully
python3 -c "
import sys
import subprocess
try:
    import uvicorn
    uvicorn.run('main:app', host='0.0.0.0', port=8000, reload=True, log_level='info')
except ImportError:
    print('❌ uvicorn not installed, trying alternative startup...')
    subprocess.run([sys.executable, '-m', 'uvicorn', 'main:app', '--host', '0.0.0.0', '--port', '8000', '--reload'])
except Exception as e:
    print(f'❌ Failed to start server: {e}')
    print('📝 Make sure you have installed all dependencies with: pip install -r requirements.txt')
"
