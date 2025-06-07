#!/bin/bash

# Paper Trading Application Startup Script
# This script starts both the API server and UI on custom ports

echo "🚀 Starting Paper Trading Application..."
echo "=" | tr -d '\n' | head -c 50; echo

# Check if we're in the right directory
if [ ! -f "main.py" ]; then
    echo "❌ Error: Please run this script from the Trade directory"
    exit 1
fi

# Start API server on port 8001 (background)
echo "📡 Starting API Server on port 8001..."
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload &
API_PID=$!

# Wait a moment for API to start
sleep 3

# Start UI on port 3500 (background)
echo "🌐 Starting UI on port 3500..."
cd trading-ui
npm run dev:3500 &
UI_PID=$!

# Go back to main directory
cd ..

echo ""
echo "✅ Both servers started successfully!"
echo ""
echo "🌐 Frontend UI: http://localhost:3500"
echo "📡 Backend API: http://localhost:8001"
echo "📚 API Docs: http://localhost:8001/docs"
echo ""
echo "💡 To stop both servers, press Ctrl+C"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping servers..."
    kill $API_PID 2>/dev/null
    kill $UI_PID 2>/dev/null
    echo "✅ Servers stopped"
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup SIGINT SIGTERM

# Wait for user to stop
echo "⏳ Servers running... Press Ctrl+C to stop"
wait
