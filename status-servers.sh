#!/bin/bash

# Trading App Server Status Script
# This script checks the status of both servers

echo "📊 Trading App Server Status"
echo "============================"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to check if port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Function to get process info for port
get_process_info() {
    local port=$1
    lsof -Pi :$port -sTCP:LISTEN | tail -n +2
}

# Function to check HTTP endpoint
check_endpoint() {
    local url=$1
    local timeout=5
    if curl -s --max-time $timeout "$url" > /dev/null 2>&1; then
        return 0  # Endpoint is responding
    else
        return 1  # Endpoint is not responding
    fi
}

echo -e "${BLUE}Backend API Server (Port 8500):${NC}"
if check_port 8500; then
    echo -e "${GREEN}✅ Running${NC}"
    if check_endpoint "http://localhost:8500/health" || check_endpoint "http://localhost:8500/docs"; then
        echo -e "${GREEN}✅ API responding${NC}"
        echo -e "${BLUE}   URL: http://localhost:8500${NC}"
        echo -e "${BLUE}   Docs: http://localhost:8500/docs${NC}"
    else
        echo -e "${YELLOW}⚠️  Port occupied but API not responding${NC}"
    fi
    echo -e "${BLUE}Process info:${NC}"
    get_process_info 8500 | head -1
else
    echo -e "${RED}❌ Not running${NC}"
fi

echo ""
echo -e "${BLUE}Frontend UI Server (Port 3500):${NC}"
if check_port 3500; then
    echo -e "${GREEN}✅ Running${NC}"
    if check_endpoint "http://localhost:3500"; then
        echo -e "${GREEN}✅ UI responding${NC}"
        echo -e "${BLUE}   URL: http://localhost:3500${NC}"
    else
        echo -e "${YELLOW}⚠️  Port occupied but UI not responding${NC}"
    fi
    echo -e "${BLUE}Process info:${NC}"
    get_process_info 3500 | head -1
else
    echo -e "${RED}❌ Not running${NC}"
fi

echo ""
echo -e "${BLUE}PID Files:${NC}"
cd "$(dirname "$0")"
if [ -f "backend.pid" ]; then
    BACKEND_PID=$(cat backend.pid)
    if ps -p $BACKEND_PID > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Backend PID: $BACKEND_PID (running)${NC}"
    else
        echo -e "${RED}❌ Backend PID: $BACKEND_PID (not running)${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  No backend PID file${NC}"
fi

if [ -f "ui.pid" ]; then
    UI_PID=$(cat ui.pid)
    if ps -p $UI_PID > /dev/null 2>&1; then
        echo -e "${GREEN}✅ UI PID: $UI_PID (running)${NC}"
    else
        echo -e "${RED}❌ UI PID: $UI_PID (not running)${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  No UI PID file${NC}"
fi

echo ""
echo -e "${BLUE}Log Files:${NC}"
if [ -f "backend.log" ]; then
    BACKEND_LOG_SIZE=$(wc -l < backend.log)
    echo -e "${GREEN}✅ backend.log ($BACKEND_LOG_SIZE lines)${NC}"
else
    echo -e "${YELLOW}⚠️  No backend.log file${NC}"
fi

if [ -f "ui.log" ]; then
    UI_LOG_SIZE=$(wc -l < ui.log)
    echo -e "${GREEN}✅ ui.log ($UI_LOG_SIZE lines)${NC}"
else
    echo -e "${YELLOW}⚠️  No ui.log file${NC}"
fi

echo ""
echo -e "${BLUE}Quick Actions:${NC}"
echo -e "  Start:   ./start-servers.sh"
echo -e "  Stop:    ./stop-servers.sh"
echo -e "  Restart: ./restart-servers.sh"
echo -e "  Logs:    tail -f backend.log ui.log"
