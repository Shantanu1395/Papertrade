#!/bin/bash

# Trading App Server Stop Script
# This script stops both the backend API server and the frontend UI server

echo "🛑 Stopping Trading App Servers..."
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
    local service_name=$2
    local pids=$(lsof -ti:$port)
    if [ ! -z "$pids" ]; then
        echo -e "${YELLOW}Stopping $service_name on port $port...${NC}"
        kill -15 $pids 2>/dev/null  # Try graceful shutdown first
        sleep 3
        
        # Check if still running, force kill if necessary
        if check_port $port; then
            echo -e "${YELLOW}Force killing $service_name...${NC}"
            kill -9 $pids 2>/dev/null
            sleep 2
        fi
        
        if check_port $port; then
            echo -e "${RED}❌ Failed to stop $service_name on port $port${NC}"
        else
            echo -e "${GREEN}✅ $service_name stopped successfully${NC}"
        fi
    else
        echo -e "${BLUE}$service_name not running on port $port${NC}"
    fi
}

# Stop servers using PID files if they exist
cd "$(dirname "$0")"

if [ -f "backend.pid" ]; then
    BACKEND_PID=$(cat backend.pid)
    if ps -p $BACKEND_PID > /dev/null 2>&1; then
        echo -e "${YELLOW}Stopping backend server (PID: $BACKEND_PID)...${NC}"
        kill -15 $BACKEND_PID 2>/dev/null
        sleep 3
        if ps -p $BACKEND_PID > /dev/null 2>&1; then
            kill -9 $BACKEND_PID 2>/dev/null
        fi
    fi
    rm -f backend.pid
fi

if [ -f "ui.pid" ]; then
    UI_PID=$(cat ui.pid)
    if ps -p $UI_PID > /dev/null 2>&1; then
        echo -e "${YELLOW}Stopping UI server (PID: $UI_PID)...${NC}"
        kill -15 $UI_PID 2>/dev/null
        sleep 3
        if ps -p $UI_PID > /dev/null 2>&1; then
            kill -9 $UI_PID 2>/dev/null
        fi
    fi
    rm -f ui.pid
fi

# Also kill any processes on the specific ports (backup method)
echo -e "${BLUE}Checking ports for any remaining processes...${NC}"
kill_port 8500 "Backend API"
kill_port 3500 "Frontend UI"

# Kill any remaining Node.js processes that might be related to our UI
echo -e "${BLUE}Cleaning up any remaining Node.js processes...${NC}"
pkill -f "next-server" 2>/dev/null
pkill -f "npm run dev" 2>/dev/null

# Kill any remaining Python processes that might be related to our backend
echo -e "${BLUE}Cleaning up any remaining Python processes...${NC}"
pkill -f "uvicorn app.main:app" 2>/dev/null

echo ""
echo -e "${GREEN}🏁 All servers stopped successfully!${NC}"
echo "=================================="

# Check final status
echo -e "${BLUE}Final status check:${NC}"
if check_port 8500; then
    echo -e "${RED}⚠️  Port 8500 still in use${NC}"
else
    echo -e "${GREEN}✅ Port 8500 is free${NC}"
fi

if check_port 3500; then
    echo -e "${RED}⚠️  Port 3500 still in use${NC}"
else
    echo -e "${GREEN}✅ Port 3500 is free${NC}"
fi

echo ""
echo -e "${YELLOW}Log files preserved:${NC}"
echo -e "  Backend: backend.log"
echo -e "  UI:      ui.log"
echo ""
echo -e "${BLUE}To start servers again:${NC} ./start-servers.sh"
