#!/bin/bash

# OpsFlow Guardian Backend Test Script
echo "🚀 Testing OpsFlow Guardian Backend..."

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Base URL
BASE_URL="http://localhost:8000"

# Function to test endpoint
test_endpoint() {
    local endpoint=$1
    local expected_status=$2
    local description=$3
    
    echo -e "\n${BLUE}Testing:${NC} $description"
    echo "Endpoint: $endpoint"
    
    response=$(curl -s -w "\n%{http_code}" "$BASE_URL$endpoint" 2>/dev/null)
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n -1)
    
    if [ "$http_code" -eq "$expected_status" ]; then
        echo -e "${GREEN}✅ PASS${NC} - HTTP $http_code"
    else
        echo -e "${RED}❌ FAIL${NC} - Expected HTTP $expected_status, got HTTP $http_code"
        echo "Response: $body"
    fi
}

# Wait for server to be ready
echo "Waiting for server to start..."
sleep 3

# Health check
test_endpoint "/health" 200 "Health Check"

# API Documentation
test_endpoint "/docs" 200 "API Documentation"

# Agent endpoints
test_endpoint "/api/v1/agents" 200 "List Agents"
test_endpoint "/api/v1/agents/stats" 200 "Agent Statistics"

# Workflow endpoints
test_endpoint "/api/v1/workflows" 200 "List Workflows"
test_endpoint "/api/v1/workflows/templates" 200 "Workflow Templates"

# Approval endpoints
test_endpoint "/api/v1/approvals" 200 "List Approvals"
test_endpoint "/api/v1/approvals/stats" 200 "Approval Statistics"

# Audit endpoints
test_endpoint "/api/v1/audit" 200 "List Audit Trails"

# Analytics endpoints
test_endpoint "/api/v1/analytics/dashboard" 200 "Analytics Dashboard"
test_endpoint "/api/v1/analytics/performance" 200 "Performance Metrics"
test_endpoint "/api/v1/analytics/costs" 200 "Cost Analysis"

echo -e "\n${BLUE}🎉 Testing complete!${NC}"
echo "If all tests passed, your backend is ready for frontend integration."
echo -e "\nNext steps:"
echo "1. Update your React app to use http://localhost:8000/api/v1/ endpoints"
echo "2. Test WebSocket connections at ws://localhost:8000/ws"
echo "3. Check the API documentation at http://localhost:8000/docs"
