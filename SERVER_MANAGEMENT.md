# Trading App Server Management

This document explains how to manage the Trading App servers using the provided shell scripts.

## 🚀 Quick Start

### Start Both Servers
```bash
./start-servers.sh
```
- **Backend API**: http://localhost:8500
- **Frontend UI**: http://localhost:3500
- **API Documentation**: http://localhost:8500/docs

### Stop Both Servers
```bash
./stop-servers.sh
```

### Check Server Status
```bash
./status-servers.sh
```

### Restart Both Servers
```bash
./restart-servers.sh
```

## 📋 Available Scripts

| Script | Purpose | Description |
|--------|---------|-------------|
| `start-servers.sh` | Start servers | Starts both backend (port 8500) and UI (port 3500) |
| `stop-servers.sh` | Stop servers | Gracefully stops both servers |
| `restart-servers.sh` | Restart servers | Stops and then starts both servers |
| `status-servers.sh` | Check status | Shows detailed status of both servers |

## 🔧 Server Configuration

### Backend API Server
- **Port**: 8500
- **URL**: http://localhost:8500
- **Documentation**: http://localhost:8500/docs
- **Log File**: `backend.log`
- **PID File**: `backend.pid`

### Frontend UI Server
- **Port**: 3500
- **URL**: http://localhost:3500
- **Log File**: `ui.log`
- **PID File**: `ui.pid`

## 📊 Monitoring

### View Live Logs
```bash
# Both servers
tail -f backend.log ui.log

# Backend only
tail -f backend.log

# UI only
tail -f ui.log
```

### Check Process Status
```bash
# Quick status check
./status-servers.sh

# Manual port check
lsof -i :8500  # Backend
lsof -i :3500  # UI
```

## 🛠 Troubleshooting

### Port Already in Use
The scripts automatically detect and kill existing processes on the required ports.

### Failed to Start
1. Check log files for errors:
   ```bash
   cat backend.log
   cat ui.log
   ```

2. Ensure dependencies are installed:
   ```bash
   # Backend dependencies
   source venv/bin/activate
   pip install -r requirements.txt
   
   # UI dependencies
   cd trading-ui
   npm install
   ```

3. Check if virtual environment exists:
   ```bash
   ls -la venv/
   ```

### Manual Cleanup
If scripts fail to stop servers properly:
```bash
# Kill processes on specific ports
sudo lsof -ti:8500 | xargs kill -9
sudo lsof -ti:3500 | xargs kill -9

# Remove PID files
rm -f backend.pid ui.pid
```

## 🔄 Development Workflow

### Typical Development Session
```bash
# Start servers
./start-servers.sh

# Check status
./status-servers.sh

# Make changes to code...

# Restart to apply changes
./restart-servers.sh

# Stop when done
./stop-servers.sh
```

### Hot Reload
Both servers support hot reload:
- **Backend**: Automatically reloads on Python file changes
- **Frontend**: Automatically reloads on React/TypeScript file changes

## 📁 File Structure

```
Trading/
├── start-servers.sh      # Start both servers
├── stop-servers.sh       # Stop both servers
├── restart-servers.sh    # Restart both servers
├── status-servers.sh     # Check server status
├── backend.log          # Backend server logs
├── ui.log               # UI server logs
├── backend.pid          # Backend process ID
├── ui.pid               # UI process ID
├── app/                 # Backend source code
├── trading-ui/          # Frontend source code
└── venv/                # Python virtual environment
```

## 🎯 Features

### Smart Process Management
- Automatic port conflict detection and resolution
- Graceful shutdown with fallback to force kill
- PID file tracking for reliable process management
- Comprehensive status reporting

### Colored Output
- 🟢 Green: Success/Running
- 🟡 Yellow: Warning/In Progress
- 🔴 Red: Error/Not Running
- 🔵 Blue: Information

### Logging
- Separate log files for backend and UI
- Log rotation and management
- Real-time log viewing capabilities

## 🚨 Important Notes

1. **Virtual Environment**: Ensure Python virtual environment is activated for backend
2. **Node Dependencies**: Ensure npm dependencies are installed for UI
3. **Port Conflicts**: Scripts handle port conflicts automatically
4. **Permissions**: Scripts are executable (`chmod +x` applied)
5. **Background Processes**: Servers run in background with log redirection

## 🎉 Happy Trading!

Your trading app is now ready to use with professional server management! 📈
