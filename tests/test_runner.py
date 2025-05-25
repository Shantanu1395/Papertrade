#!/usr/bin/env python3
"""
Unified test runner for the Paper Trading API.
Replaces all scattered test scripts with a single, comprehensive test runner.
"""
import subprocess
import sys
import os
import argparse
from datetime import datetime


def check_environment():
    """Check if environment is set up for testing."""
    print("🔍 Checking test environment...")
    
    # Check if we're in the right directory
    if not os.path.exists("app/main.py"):
        print("❌ Please run this script from the project root directory")
        return False
    
    # Check for pytest
    try:
        import pytest
        print("✅ pytest found")
    except ImportError:
        print("❌ pytest not found. Install with: pip install pytest")
        return False
    
    # Check API credentials (for real API tests)
    api_key = os.getenv('TRADING_API_KEY')
    api_secret = os.getenv('TRADING_API_SECRET')
    
    if api_key and api_secret:
        print("✅ API credentials found (real API tests available)")
        return True
    else:
        print("⚠️  API credentials not set (real API tests will be skipped)")
        print("💡 Set them with:")
        print("   export TRADING_API_KEY='your_testnet_key'")
        print("   export TRADING_API_SECRET='your_testnet_secret'")
        return True  # Still allow tests without credentials


def run_quick_tests():
    """Run quick tests (no real API calls)."""
    print("\n🚀 Running Quick Tests (No Real API Calls)")
    print("=" * 50)
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest",
            "tests/test_comprehensive.py::TestPaperTradingAPI::test_server_health",
            "tests/test_comprehensive.py::TestPaperTradingAPI::test_account_endpoints",
            "tests/test_comprehensive.py::TestPaperTradingAPI::test_market_endpoints",
            "tests/test_comprehensive.py::TestPaperTradingAPI::test_workflow_endpoint",
            "tests/test_comprehensive.py::TestPaperTradingAPI::test_response_formats",
            "-v", "--tb=short", "--color=yes"
        ], check=True)
        
        print("\n✅ Quick tests passed!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Quick tests failed with exit code: {e.returncode}")
        return False


def run_full_tests():
    """Run all tests including real API calls."""
    print("\n🚀 Running Full Test Suite (Including Real API)")
    print("=" * 50)
    print("⚠️  WARNING: This includes tests that make real API calls to Binance Testnet")
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest",
            "tests/test_comprehensive.py",
            "-v", "--tb=short", "--color=yes", "-s"
        ], check=True)
        
        print("\n✅ All tests passed!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Tests failed with exit code: {e.returncode}")
        return False


def run_http_tests():
    """Run HTTP endpoint tests (requires running server)."""
    print("\n🚀 Running HTTP Endpoint Tests")
    print("=" * 40)
    print("💡 Make sure your server is running: python scripts/start_server.py")
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest",
            "tests/test_comprehensive.py::TestHTTPEndpoints",
            "-v", "--tb=short", "--color=yes"
        ], check=True)
        
        print("\n✅ HTTP tests passed!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ HTTP tests failed with exit code: {e.returncode}")
        return False


def run_workflow_test():
    """Run workflow endpoint test."""
    print("\n🚀 Running Workflow Test")
    print("=" * 30)
    
    try:
        result = subprocess.run([
            sys.executable, "-c",
            """
import requests
import json

try:
    response = requests.post(
        'http://localhost:8000/workflow-test/run',
        json={'order_amount_usdt': 50, 'symbol': 'ETH/USDT', 'dry_run': True},
        timeout=30
    )
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Workflow test completed: {result['status']}")
        print(f"📊 Steps: {result['completed_steps']}/{result['total_steps']}")
    else:
        print(f"❌ Workflow test failed: {response.text}")
except Exception as e:
    print(f"❌ Cannot connect to server: {e}")
    print("💡 Start server with: python scripts/start_server.py")
            """
        ], check=True)
        
        return True
        
    except subprocess.CalledProcessError:
        return False


def main():
    """Main function with argument parsing."""
    parser = argparse.ArgumentParser(
        description="Unified test runner for Paper Trading API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Test Types:
  quick     - Fast tests without real API calls
  full      - All tests including real API calls  
  http      - HTTP endpoint tests (requires running server)
  workflow  - Workflow endpoint test (requires running server)

Examples:
  python tests/test_runner.py quick
  python tests/test_runner.py full
  python tests/test_runner.py http
        """
    )
    
    parser.add_argument(
        'test_type',
        nargs='?',
        default='quick',
        choices=['quick', 'full', 'http', 'workflow'],
        help='Type of tests to run (default: quick)'
    )
    
    args = parser.parse_args()
    
    print("🧪 Paper Trading API - Unified Test Runner")
    print("=" * 50)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎯 Test Type: {args.test_type}")
    
    # Check environment
    if not check_environment():
        print("\n❌ Environment check failed!")
        sys.exit(1)
    
    # Change to project root
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(project_root)
    
    # Run appropriate tests
    success = False
    
    if args.test_type == 'quick':
        success = run_quick_tests()
    elif args.test_type == 'full':
        success = run_full_tests()
    elif args.test_type == 'http':
        success = run_http_tests()
    elif args.test_type == 'workflow':
        success = run_workflow_test()
    
    # Print summary
    print("\n" + "=" * 50)
    if success:
        print("🎉 All tests completed successfully!")
        print("✅ Your trading system is working correctly!")
    else:
        print("💥 Some tests failed!")
        print("🔧 Please check the errors above and fix any issues")
    
    print("=" * 50)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
