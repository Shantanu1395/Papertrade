#!/usr/bin/env python3
"""
Process management utility for the Paper Trading API.
Helps identify, start, stop, and manage server processes.
"""
import subprocess
import sys
import os
import signal
import time
import json
from datetime import datetime


class ProcessManager:
    """Manage Paper Trading API processes."""
    
    def __init__(self):
        self.process_name = "paper-trading-api"
        self.default_port = 8000
        self.pid_file = "scripts/.server.pid"
        self.log_file = "scripts/.server.log"
    
    def find_processes_by_port(self, port=None):
        """Find processes using a specific port."""
        port = port or self.default_port
        try:
            result = subprocess.run(
                ["lsof", "-i", f":{port}"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]  # Skip header
                processes = []
                for line in lines:
                    parts = line.split()
                    if len(parts) >= 2:
                        processes.append({
                            "command": parts[0],
                            "pid": int(parts[1]),
                            "user": parts[2],
                            "port": port
                        })
                return processes
            return []
        except Exception as e:
            print(f"❌ Error finding processes: {e}")
            return []
    
    def find_processes_by_name(self, name=None):
        """Find processes by name."""
        name = name or self.process_name
        try:
            result = subprocess.run(
                ["pgrep", "-f", name],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                pids = [int(pid.strip()) for pid in result.stdout.strip().split('\n') if pid.strip()]
                processes = []
                for pid in pids:
                    try:
                        # Get process info
                        ps_result = subprocess.run(
                            ["ps", "-p", str(pid), "-o", "pid,ppid,command"],
                            capture_output=True,
                            text=True
                        )
                        if ps_result.returncode == 0:
                            lines = ps_result.stdout.strip().split('\n')[1:]  # Skip header
                            for line in lines:
                                parts = line.strip().split(None, 2)
                                if len(parts) >= 3:
                                    processes.append({
                                        "pid": int(parts[0]),
                                        "ppid": int(parts[1]),
                                        "command": parts[2],
                                        "name": name
                                    })
                    except:
                        continue
                return processes
            return []
        except Exception as e:
            print(f"❌ Error finding processes by name: {e}")
            return []
    
    def get_process_status(self):
        """Get comprehensive process status."""
        print("🔍 Checking Paper Trading API Process Status")
        print("=" * 60)
        
        # Check by port
        port_processes = self.find_processes_by_port()
        if port_processes:
            print(f"📡 Processes using port {self.default_port}:")
            for proc in port_processes:
                print(f"   PID: {proc['pid']} | Command: {proc['command']} | User: {proc['user']}")
        else:
            print(f"✅ Port {self.default_port} is free")
        
        # Check by name
        name_processes = self.find_processes_by_name()
        if name_processes:
            print(f"\n🏷️  Processes with name '{self.process_name}':")
            for proc in name_processes:
                print(f"   PID: {proc['pid']} | Command: {proc['command']}")
        else:
            print(f"\n✅ No processes found with name '{self.process_name}'")
        
        # Check PID file
        if os.path.exists(self.pid_file):
            with open(self.pid_file, 'r') as f:
                stored_pid = int(f.read().strip())
            print(f"\n📄 Stored PID file: {stored_pid}")
            
            # Check if stored PID is still running
            try:
                os.kill(stored_pid, 0)  # Check if process exists
                print(f"   ✅ PID {stored_pid} is still running")
            except OSError:
                print(f"   ❌ PID {stored_pid} is not running (stale PID file)")
                os.remove(self.pid_file)
        else:
            print(f"\n📄 No PID file found")
        
        print("=" * 60)
    
    def stop_server(self, force=False):
        """Stop the Paper Trading API server."""
        print("🛑 Stopping Paper Trading API Server")
        print("=" * 40)
        
        stopped_any = False
        
        # Stop by PID file first
        if os.path.exists(self.pid_file):
            with open(self.pid_file, 'r') as f:
                stored_pid = int(f.read().strip())
            
            try:
                if force:
                    os.kill(stored_pid, signal.SIGKILL)
                    print(f"💀 Force killed PID {stored_pid}")
                else:
                    os.kill(stored_pid, signal.SIGTERM)
                    print(f"🛑 Gracefully stopped PID {stored_pid}")
                stopped_any = True
                time.sleep(1)
            except OSError:
                print(f"⚠️  PID {stored_pid} was not running")
            
            os.remove(self.pid_file)
        
        # Stop by port
        port_processes = self.find_processes_by_port()
        for proc in port_processes:
            try:
                if force:
                    os.kill(proc['pid'], signal.SIGKILL)
                    print(f"💀 Force killed PID {proc['pid']} (port {self.default_port})")
                else:
                    os.kill(proc['pid'], signal.SIGTERM)
                    print(f"🛑 Gracefully stopped PID {proc['pid']} (port {self.default_port})")
                stopped_any = True
                time.sleep(1)
            except OSError:
                print(f"⚠️  Could not stop PID {proc['pid']}")
        
        # Stop by name
        name_processes = self.find_processes_by_name()
        for proc in name_processes:
            try:
                if force:
                    os.kill(proc['pid'], signal.SIGKILL)
                    print(f"💀 Force killed PID {proc['pid']} (name: {self.process_name})")
                else:
                    os.kill(proc['pid'], signal.SIGTERM)
                    print(f"🛑 Gracefully stopped PID {proc['pid']} (name: {self.process_name})")
                stopped_any = True
                time.sleep(1)
            except OSError:
                print(f"⚠️  Could not stop PID {proc['pid']}")
        
        if not stopped_any:
            print("✅ No Paper Trading API processes were running")
        else:
            print("✅ All Paper Trading API processes stopped")
        
        print("=" * 40)
    
    def start_server(self, background=False):
        """Start the Paper Trading API server."""
        print("🚀 Starting Paper Trading API Server")
        print("=" * 40)
        
        # Check if already running
        if self.find_processes_by_port() or self.find_processes_by_name():
            print("⚠️  Server appears to be already running!")
            print("💡 Use 'stop' command first, or 'restart' to restart")
            return False
        
        # Start the server
        try:
            if background:
                # Start in background
                with open(self.log_file, 'w') as log:
                    process = subprocess.Popen(
                        [sys.executable, "scripts/start_server.py"],
                        stdout=log,
                        stderr=subprocess.STDOUT,
                        preexec_fn=os.setsid  # Create new process group
                    )
                
                # Save PID
                with open(self.pid_file, 'w') as f:
                    f.write(str(process.pid))
                
                print(f"✅ Server started in background (PID: {process.pid})")
                print(f"📄 Logs: {self.log_file}")
                print(f"🌐 Server: http://localhost:{self.default_port}")
                print(f"📊 Docs: http://localhost:{self.default_port}/docs")
            else:
                # Start in foreground
                print("🌐 Starting server in foreground...")
                print("💡 Press Ctrl+C to stop")
                subprocess.run([sys.executable, "scripts/start_server.py"])
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to start server: {e}")
            return False


def main():
    """Main CLI interface."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Paper Trading API Process Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/process_manager.py status
  python scripts/process_manager.py start
  python scripts/process_manager.py start --background
  python scripts/process_manager.py stop
  python scripts/process_manager.py stop --force
  python scripts/process_manager.py restart
        """
    )
    
    parser.add_argument(
        'action',
        choices=['status', 'start', 'stop', 'restart'],
        help='Action to perform'
    )
    
    parser.add_argument(
        '--background', '-b',
        action='store_true',
        help='Start server in background'
    )
    
    parser.add_argument(
        '--force', '-f',
        action='store_true',
        help='Force stop (SIGKILL instead of SIGTERM)'
    )
    
    args = parser.parse_args()
    
    manager = ProcessManager()
    
    if args.action == 'status':
        manager.get_process_status()
    
    elif args.action == 'start':
        manager.start_server(background=args.background)
    
    elif args.action == 'stop':
        manager.stop_server(force=args.force)
    
    elif args.action == 'restart':
        manager.stop_server(force=args.force)
        time.sleep(2)
        manager.start_server(background=args.background)


if __name__ == "__main__":
    main()
