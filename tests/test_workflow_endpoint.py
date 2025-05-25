#!/usr/bin/env python3
"""
Script to test the workflow testing endpoint.
This makes HTTP calls to the /workflow-test/run endpoint.
"""
import requests
import json
import sys
import os
from datetime import datetime


def check_environment():
    """Check if environment is set up."""
    api_key = os.getenv('TRADING_API_KEY')
    api_secret = os.getenv('TRADING_API_SECRET')
    
    if not api_key or not api_secret:
        print("❌ API credentials not set!")
        print("💡 Set them with:")
        print("   export TRADING_API_KEY='your_testnet_key'")
        print("   export TRADING_API_SECRET='your_testnet_secret'")
        return False
    
    print("✅ API credentials found")
    return True


def check_server_running(base_url):
    """Check if server is running."""
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code == 200:
            print(f"✅ Server is running at {base_url}")
            return True
        else:
            print(f"❌ Server responded with status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to server: {e}")
        return False


def test_workflow_endpoint(base_url, dry_run=True, order_amount=50.0):
    """Test the workflow endpoint."""
    
    print(f"\n🧪 Testing Workflow Endpoint")
    print("=" * 50)
    print(f"🌐 Server: {base_url}")
    print(f"💰 Order Amount: ${order_amount}")
    print(f"🎭 Dry Run: {dry_run}")
    print("=" * 50)
    
    # Prepare request
    request_data = {
        "order_amount_usdt": order_amount,
        "symbol": "ETH/USDT",
        "dry_run": dry_run
    }
    
    try:
        print("\n📤 Sending workflow test request...")
        print(f"Request: {json.dumps(request_data, indent=2)}")
        
        # Make the request
        response = requests.post(
            f"{base_url}/workflow-test/run",
            json=request_data,
            timeout=60  # Workflow might take time
        )
        
        print(f"\n📥 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print_workflow_results(result)
            return True
        else:
            print(f"❌ Request failed: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out (workflow took too long)")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def print_workflow_results(result):
    """Print formatted workflow results."""
    
    print(f"\n🎯 Workflow Test Results")
    print("=" * 60)
    print(f"📋 Test ID: {result['test_id']}")
    print(f"📊 Status: {result['status'].upper()}")
    print(f"✅ Completed Steps: {result['completed_steps']}/{result['total_steps']}")
    print(f"⏱️  Duration: {result['summary'].get('duration_seconds', 0):.2f} seconds")
    print(f"📈 Success Rate: {result['summary'].get('success_rate', 0):.1f}%")
    
    # Print summary
    summary = result['summary']
    if 'initial_usdt_balance' in summary:
        print(f"\n💰 Financial Summary:")
        print(f"   Initial USDT: ${summary.get('initial_usdt_balance', 0):,.2f}")
        print(f"   Final USDT:   ${summary.get('final_usdt_balance', 0):,.2f}")
        print(f"   Net P&L:      ${summary.get('net_pnl', 0):,.2f}")
        print(f"   P&L %:        {summary.get('pnl_percentage', 0):,.2f}%")
        print(f"   Order Amount: ${summary.get('order_amount', 0):,.2f}")
    
    # Print step details
    print(f"\n📋 Step-by-Step Results:")
    print("-" * 60)
    
    for step in result['steps']:
        status_emoji = "✅" if step['status'] == 'success' else "❌" if step['status'] == 'failed' else "⏸️"
        print(f"{status_emoji} Step {step['step_number']}: {step['step_name']}")
        print(f"   {step['message']}")
        
        # Print key data for important steps
        if step['step_number'] == 3 and 'buy_order' in step['data']:  # Buy order
            buy_order = step['data']['buy_order']
            print(f"   📈 Buy Order: {buy_order.get('quantity', 'N/A')} @ ${buy_order.get('price', 'N/A')}")
        
        elif step['step_number'] == 6 and 'sell_order' in step['data']:  # Sell order
            sell_order = step['data']['sell_order']
            print(f"   📉 Sell Order: {sell_order.get('quantity', 'N/A')} @ ${sell_order.get('price', 'N/A')}")
        
        elif step['step_number'] == 9 and 'trade_count' in step['data']:  # Trade history
            trade_count = step['data']['trade_count']
            print(f"   📊 Trades Found: {trade_count}")
        
        print()
    
    # Print overall assessment
    if result['status'] == 'completed':
        print("🎉 Workflow test completed successfully!")
        print("✅ All trading functions are working correctly")
    elif result['status'] == 'partial':
        print("⚠️  Workflow test partially completed")
        print("💡 Some steps failed - check the details above")
    else:
        print("❌ Workflow test failed")
        print("🔧 Check your API credentials and server configuration")


def main():
    """Main function."""
    print("🧪 Workflow Endpoint Tester")
    print("=" * 30)
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    # Get server URL
    server_url = input("\n🌐 Enter server URL (default: http://localhost:8000): ").strip()
    if not server_url:
        server_url = "http://localhost:8000"
    
    # Check server
    if not check_server_running(server_url):
        print("\n💡 Start your server with: uvicorn app.main:app --reload")
        sys.exit(1)
    
    # Get test parameters
    print("\n⚙️  Test Configuration:")
    
    dry_run_input = input("🎭 Dry run mode? (Y/n): ").strip().lower()
    dry_run = dry_run_input not in ['n', 'no']
    
    order_amount_input = input("💰 Order amount in USDT (default: 50): ").strip()
    try:
        order_amount = float(order_amount_input) if order_amount_input else 50.0
    except ValueError:
        order_amount = 50.0
    
    # Confirm
    mode = "DRY RUN" if dry_run else "REAL TRADING"
    print(f"\n⚠️  About to run workflow test in {mode} mode")
    print(f"💰 Order amount: ${order_amount}")
    
    if not dry_run:
        print("🚨 WARNING: This will place REAL orders on Binance Testnet!")
    
    confirm = input("\n❓ Continue? (y/N): ").strip().lower()
    if confirm not in ['y', 'yes']:
        print("❌ Test cancelled")
        sys.exit(1)
    
    # Run the test
    success = test_workflow_endpoint(server_url, dry_run, order_amount)
    
    if success:
        print("\n🎉 Workflow endpoint test completed!")
    else:
        print("\n💥 Workflow endpoint test failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
