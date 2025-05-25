#!/usr/bin/env python3
"""
Script to run integration tests against a REAL running server.
This makes HTTP calls to your actual server instead of TestClient.
"""
import sys
import os
import requests
from datetime import datetime, timedelta


def check_environment():
    """Check if the environment is properly set up."""
    print("🔍 Checking environment setup...")
    
    # Check for API credentials
    api_key = os.getenv('TRADING_API_KEY')
    api_secret = os.getenv('TRADING_API_SECRET')
    
    if not api_key:
        print("❌ TRADING_API_KEY environment variable not set")
        return False
    
    if not api_secret:
        print("❌ TRADING_API_SECRET environment variable not set")
        return False
    
    print("✅ API credentials found")
    return True


def check_server_running(base_url):
    """Check if the server is running."""
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code == 200:
            print(f"✅ Server is running at {base_url}")
            return True
        else:
            print(f"❌ Server responded with status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to server at {base_url}: {e}")
        return False


def run_real_server_integration_test(base_url="http://localhost:8000"):
    """Run integration test against real running server."""
    
    print(f"\n🚀 Running Integration Test Against Real Server")
    print("=" * 60)
    print(f"🌐 Server URL: {base_url}")
    print("⚠️  This makes ACTUAL API calls to Binance Testnet")
    print("=" * 60)
    
    try:
        # Step 1: Get initial portfolio balance
        print("\n📊 Step 1: Getting initial portfolio...")
        response = requests.get(f"{base_url}/account/portfolio")
        assert response.status_code == 200
        initial_portfolio = response.json()
        print(f"Initial portfolio: {initial_portfolio}")
        
        # Step 2: Get initial USDT balance
        print("\n💰 Step 2: Getting initial USDT balance...")
        response = requests.get(f"{base_url}/account/usdt-balance")
        assert response.status_code == 200
        initial_usdt_balance = response.json()
        print(f"Initial USDT balance: ${initial_usdt_balance:,.2f}")
        
        if initial_usdt_balance < 100:
            print(f"⚠️  Warning: Low USDT balance ({initial_usdt_balance})")
        
        # Step 3: Place market BUY order
        print("\n📈 Step 3: Placing BUY order...")
        order_amount = min(100, initial_usdt_balance * 0.1)
        buy_order_data = {
            "symbol": "ETH/USDT",
            "side": "BUY",
            "quote_order_qty": order_amount
        }
        
        response = requests.post(f"{base_url}/orders/market", json=buy_order_data)
        if response.status_code != 200:
            print(f"❌ Buy order failed: {response.text}")
            return False
        
        buy_order = response.json()
        print(f"✅ Buy order placed: {buy_order}")
        
        # Step 4: Get portfolio after buy
        print("\n📊 Step 4: Checking portfolio after buy...")
        response = requests.get(f"{base_url}/account/portfolio")
        assert response.status_code == 200
        portfolio_after_buy = response.json()
        print(f"Portfolio after buy: {portfolio_after_buy}")
        
        # Find ETH balance
        eth_balance = next((asset for asset in portfolio_after_buy if asset["asset"] == "ETH"), None)
        if not eth_balance:
            print("❌ No ETH found in portfolio after buy order")
            return False
        
        print(f"🪙 ETH acquired: {eth_balance['free']} ETH")
        
        # Step 5: Get USDT balance after buy
        print("\n💰 Step 5: Checking USDT balance after buy...")
        response = requests.get(f"{base_url}/account/usdt-balance")
        assert response.status_code == 200
        usdt_after_buy = response.json()
        print(f"USDT balance after buy: ${usdt_after_buy:,.2f}")
        
        usdt_spent = initial_usdt_balance - usdt_after_buy
        print(f"💸 USDT spent: ${usdt_spent:,.2f}")
        
        # Step 6: Sell 100% of ETH
        print("\n📉 Step 6: Placing SELL order...")
        sell_order_data = {
            "symbol": "ETH/USDT",
            "percentage": 100
        }
        
        response = requests.post(f"{base_url}/orders/sell-percentage", json=sell_order_data)
        if response.status_code != 200:
            print(f"❌ Sell order failed: {response.text}")
            return False
        
        sell_order = response.json()
        print(f"✅ Sell order placed: {sell_order}")
        
        # Step 7: Get portfolio after sell
        print("\n📊 Step 7: Checking portfolio after sell...")
        response = requests.get(f"{base_url}/account/portfolio")
        assert response.status_code == 200
        portfolio_after_sell = response.json()
        print(f"Portfolio after sell: {portfolio_after_sell}")
        
        # Step 8: Get final USDT balance
        print("\n💰 Step 8: Checking final USDT balance...")
        response = requests.get(f"{base_url}/account/usdt-balance")
        assert response.status_code == 200
        final_usdt_balance = response.json()
        print(f"Final USDT balance: ${final_usdt_balance:,.2f}")
        
        # Calculate P&L
        net_pnl = final_usdt_balance - initial_usdt_balance
        print(f"📈 Net P&L: ${net_pnl:,.2f} ({net_pnl/initial_usdt_balance*100:.2f}%)")
        
        # Step 9: Check trade history
        print("\n📋 Step 9: Checking trade history...")
        now = datetime.now()
        fifteen_min_ago = now - timedelta(minutes=15)
        
        time_range_data = {
            "start_time": fifteen_min_ago.strftime("%Y-%m-%d %H:%M:%S"),
            "end_time": now.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        response = requests.post(f"{base_url}/trades/time-range", json=time_range_data)
        assert response.status_code == 200
        recent_trades = response.json()
        print(f"📊 Recent trades found: {len(recent_trades)}")
        
        if len(recent_trades) >= 2:
            recent_trades.sort(key=lambda x: x["time"], reverse=True)
            latest_trades = recent_trades[:2]
            
            buy_trade = next((trade for trade in latest_trades if trade["side"] == "BUY"), None)
            sell_trade = next((trade for trade in latest_trades if trade["side"] == "SELL"), None)
            
            if buy_trade and sell_trade:
                print(f"✅ BUY trade: {buy_trade['quantity']} ETH @ ${buy_trade['price']}")
                print(f"✅ SELL trade: {sell_trade['quantity']} ETH @ ${sell_trade['price']}")
            else:
                print("⚠️  Could not find both buy and sell trades in recent history")
        else:
            print("⚠️  Less than 2 trades found in recent history")
        
        print("\n🎉 Real server integration test completed successfully!")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function."""
    print("🌐 Real Server Integration Test Runner")
    print("=" * 40)
    
    # Check environment
    if not check_environment():
        print("\n❌ Environment check failed!")
        sys.exit(1)
    
    # Get server URL
    server_url = input("\n🌐 Enter server URL (default: http://localhost:8000): ").strip()
    if not server_url:
        server_url = "http://localhost:8000"
    
    # Check if server is running
    if not check_server_running(server_url):
        print("\n❌ Server is not running!")
        print("💡 Start your server with: uvicorn app.main:app --reload")
        sys.exit(1)
    
    # Ask for confirmation
    response = input(f"\n❓ Run integration test against {server_url}? (y/N): ").strip().lower()
    if response not in ['y', 'yes']:
        print("❌ Test cancelled by user")
        sys.exit(1)
    
    # Run the test
    success = run_real_server_integration_test(server_url)
    
    if success:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print("\n💥 Tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
