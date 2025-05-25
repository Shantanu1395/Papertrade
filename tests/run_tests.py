#!/usr/bin/env python3
"""
Script to run the integration tests for the trading API.
"""
import subprocess
import sys
import os


def install_test_dependencies():
    """Install test dependencies if not already installed."""
    print("Installing test dependencies...")
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", 
            "pytest>=7.4.0", "pytest-asyncio>=0.21.0", "httpx>=0.24.0"
        ])
        print("✅ Test dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install test dependencies: {e}")
        return False
    return True


def run_integration_tests():
    """Run the integration tests."""
    print("\n" + "="*60)
    print("🚀 Running Trading API Integration Tests")
    print("="*60)
    
    try:
        # Run pytest with verbose output
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/test_integration_trading.py",
            "-v", "--tb=short", "-s"
        ], capture_output=False)
        
        if result.returncode == 0:
            print("\n✅ All integration tests passed!")
        else:
            print("\n❌ Some tests failed. Check the output above.")
        
        return result.returncode == 0
        
    except FileNotFoundError:
        print("❌ pytest not found. Please install pytest first.")
        return False
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False


def main():
    """Main function to run tests."""
    print("Trading API Integration Test Runner")
    print("="*40)
    
    # Check if we're in the right directory
    if not os.path.exists("app/services/trading_client.py"):
        print("❌ Please run this script from the project root directory")
        sys.exit(1)
    
    # Install dependencies
    if not install_test_dependencies():
        sys.exit(1)
    
    # Run tests
    success = run_integration_tests()
    
    if success:
        print("\n🎉 Integration tests completed successfully!")
        sys.exit(0)
    else:
        print("\n💥 Integration tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
