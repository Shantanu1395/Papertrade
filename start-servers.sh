#!/bin/bash

# Trading App Server Startup Script
# This script starts both the backend API server and the frontend UI server

echo "🚀 Starting Trading App Servers..."
echo "=================================="

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

# Function to kill process on port
kill_port() {
    local port=$1
    local pids=$(lsof -ti:$port)
    if [ ! -z "$pids" ]; then
        echo -e "${YELLOW}Killing existing processes on port $port...${NC}"
        kill -9 $pids 2>/dev/null
        sleep 2
    fi
}

# Check and kill existing processes
echo -e "${BLUE}Checking for existing processes...${NC}"

if check_port 8500; then
    echo -e "${YELLOW}Backend server already running on port 8500${NC}"
    kill_port 8500
fi

if check_port 3500; then
    echo -e "${YELLOW}UI server already running on port 3500${NC}"
    kill_port 3500
fi

# Start Backend Server
echo -e "${BLUE}Starting Backend API Server on port 8500...${NC}"
cd "$(dirname "$0")"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${RED}Virtual environment not found. Please run: python -m venv venv${NC}"
    exit 1
fi

# Activate virtual environment and start backend
source venv/bin/activate
python -m uvicorn app.main:app --reload --port 8500 --host 0.0.0.0 > backend.log 2>&1 &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Check if backend started successfully
if check_port 8500; then
    echo -e "${GREEN}✅ Backend server started successfully on http://localhost:8500${NC}"
    echo -e "${BLUE}   API Documentation: http://localhost:8500/docs${NC}"
else
    echo -e "${RED}❌ Failed to start backend server${NC}"
    echo -e "${RED}   Check backend.log for details${NC}"
    exit 1
fi

# Start Frontend UI Server
echo -e "${BLUE}Starting Frontend UI Server on port 3500...${NC}"
cd trading-ui

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}Installing UI dependencies...${NC}"
    npm install
fi

# Start UI server
npm run dev:3500 > ../ui.log 2>&1 &
UI_PID=$!

# Wait a moment for UI to start
sleep 5

# Check if UI started successfully
if check_port 3500; then
    echo -e "${GREEN}✅ UI server started successfully on http://localhost:3500${NC}"
else
    echo -e "${RED}❌ Failed to start UI server${NC}"
    echo -e "${RED}   Check ui.log for details${NC}"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

# Save PIDs for stop script
echo $BACKEND_PID > ../backend.pid
echo $UI_PID > ../ui.pid

echo ""
echo -e "${GREEN}🎉 All servers started successfully!${NC}"
echo "=================================="
echo -e "${BLUE}Backend API:${NC} http://localhost:8500"
echo -e "${BLUE}API Docs:${NC}    http://localhost:8500/docs"
echo -e "${BLUE}Frontend UI:${NC} http://localhost:3500"
echo ""
echo -e "${YELLOW}Logs:${NC}"
echo -e "  Backend: backend.log"
echo -e "  UI:      ui.log"
echo ""
echo -e "${YELLOW}To stop servers:${NC} ./stop-servers.sh"
echo -e "${YELLOW}To view logs:${NC}    tail -f backend.log ui.log"
echo ""
echo -e "${GREEN}Happy Trading! 📈${NC}"
