#!/usr/bin/env python3
"""
Server startup script using the new configuration system.
"""
import uvicorn
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core import settings

def main():
    """Start the FastAPI server with configuration from settings."""
    print(f"🚀 Starting {settings.api_title} v{settings.api_version}")
    print(f"📁 Generated files directory: {settings.generated_dir}")
    print(f"🌐 Server will run on: http://{settings.host}:{settings.port}")
    print(f"📊 Swagger docs: http://{settings.host}:{settings.port}/docs")
    
    # Check API credentials
    if not settings.binance_api_key or not settings.binance_api_secret:
        print("⚠️  Warning: API credentials not found!")
        print("💡 Set them with:")
        print("   export TRADING_API_KEY='your_testnet_key'")
        print("   export TRADING_API_SECRET='your_testnet_secret'")
    else:
        print("✅ API credentials found")
    
    print("\n" + "="*50)
    
    # Start the server
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload
    )

if __name__ == "__main__":
    main()
