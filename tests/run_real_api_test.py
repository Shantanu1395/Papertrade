#!/usr/bin/env python3
"""
Script to run the REAL API integration test for the trading API.
This test makes actual calls to Binance Testnet API.
"""
import sys
import os
import pytest
from fastapi.testclient import TestClient
from app.main import app


def check_environment():
    """Check if the environment is properly set up for real API testing."""
    print("🔍 Checking environment setup...")

    # Check if we're in the right directory
    if not os.path.exists("app/services/trading_client.py"):
        print("❌ Please run this script from the project root directory")
        return False

    # Check for API credentials
    api_key = os.getenv('TRADING_API_KEY')
    api_secret = os.getenv('TRADING_API_SECRET')

    if not api_key:
        print("❌ TRADING_API_KEY environment variable not set")
        print("💡 Set it with: export TRADING_API_KEY='your_testnet_api_key'")
        return False

    if not api_secret:
        print("❌ TRADING_API_SECRET environment variable not set")
        print("💡 Set it with: export TRADING_API_SECRET='your_testnet_api_secret'")
        return False

    print("✅ API credentials found")
    print(f"🔑 API Key: {api_key[:8]}...{api_key[-4:]}")
    print("🔑 API Secret: [HIDDEN]")

    return True


def run_real_api_test():
    """Run the real API integration test directly."""
    print("\n" + "="*70)
    print("🚀 Running REAL API Integration Test")
    print("="*70)
    print("⚠️  WARNING: This test makes ACTUAL API calls to Binance Testnet")
    print("⚠️  It will place real orders using your testnet account")
    print("⚠️  Make sure you have sufficient testnet USDT balance")
    print("="*70)

    # Ask for confirmation
    response = input("\n❓ Do you want to proceed? (y/N): ").strip().lower()
    if response not in ['y', 'yes']:
        print("❌ Test cancelled by user")
        return False

    try:
        # Import the test class and run it directly
        from tests.test_integration_trading import TestTradingWorkflow

        # Create test client
        client = TestClient(app)

        # Create test instance
        test_instance = TestTradingWorkflow()

        # Create a mock clean environment fixture
        class MockCleanEnvironment:
            def __enter__(self):
                return self
            def __exit__(self, *_):
                pass

        clean_env = MockCleanEnvironment()

        # Run the real API test
        print("\n🧪 Executing real API test...")
        test_instance.test_complete_trading_workflow_real_api(client, clean_env)

        print("\n✅ Real API integration test passed!")
        print("🎉 Your trading system is working correctly with Binance Testnet!")
        return True

    except Exception as e:
        print(f"\n❌ Real API integration test failed!")
        print(f"💡 Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def show_test_info():
    """Show information about what the test does."""
    print("\n📋 What this test does:")
    print("1. 📊 Gets your initial portfolio and USDT balance")
    print("2. 📈 Places a market BUY order for ETH/USDT")
    print("3. ✅ Verifies ETH appears in your portfolio")
    print("4. ✅ Verifies USDT balance decreased")
    print("5. 📉 Places a market SELL order for 100% of ETH")
    print("6. ✅ Verifies ETH is removed from portfolio")
    print("7. ✅ Verifies USDT balance increased")
    print("8. 📋 Checks trade history for the 2 trades")
    print("9. 📈 Calculates and displays P&L")

    print("\n💡 Tips:")
    print("• Ensure you have at least 1000 USDT in your testnet account")
    print("• The test uses Binance Testnet (not real money)")
    print("• Get testnet funds from: https://testnet.binance.vision/")
    print("• Get testnet API keys from: https://testnet.binance.vision/")


def main():
    """Main function to run the real API test."""
    print("🧪 Trading API Real Integration Test Runner")
    print("=" * 50)

    # Show test information
    show_test_info()

    # Check environment
    if not check_environment():
        print("\n❌ Environment check failed!")
        print("💡 Please fix the issues above and try again")
        sys.exit(1)

    # Run the test
    success = run_real_api_test()

    if success:
        print("\n🎉 All tests completed successfully!")
        print("✅ Your trading system is ready for real-world usage!")
        sys.exit(0)
    else:
        print("\n💥 Tests failed!")
        print("🔧 Please check the errors and fix any issues")
        sys.exit(1)


if __name__ == "__main__":
    main()
