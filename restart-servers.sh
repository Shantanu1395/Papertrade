#!/bin/bash

# Trading App Server Restart Script
# This script stops and then starts both servers

echo "🔄 Restarting Trading App Servers..."
echo "===================================="

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

cd "$(dirname "$0")"

echo -e "${YELLOW}Step 1: Stopping existing servers...${NC}"
./stop-servers.sh

echo ""
echo -e "${YELLOW}Step 2: Starting servers...${NC}"
./start-servers.sh

echo ""
echo -e "${GREEN}🎉 Restart complete!${NC}"
