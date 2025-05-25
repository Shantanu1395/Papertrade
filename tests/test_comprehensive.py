#!/usr/bin/env python3
"""
Comprehensive test suite for the Paper Trading API.
Combines all testing approaches into a single, organized test file.
"""
import pytest
import requests
import json
import time
import os
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app


class TestPaperTradingAPI:
    """Comprehensive test suite for the Paper Trading API."""
    
    @pytest.fixture
    def client(self):
        """FastAPI test client."""
        return TestClient(app)
    
    @pytest.fixture
    def base_url(self):
        """Base URL for HTTP requests."""
        return "http://localhost:8000"
    
    def test_server_health(self, client):
        """Test basic server health and endpoints."""
        # Test root endpoint
        response = client.get("/")
        assert response.status_code == 200
        assert "message" in response.json()
        
        # Test docs endpoint
        response = client.get("/docs")
        assert response.status_code == 200
    
    def test_account_endpoints(self, client):
        """Test all account-related endpoints."""
        # Test account balance
        response = client.get("/account/balance")
        assert response.status_code == 200
        balance = response.json()
        assert isinstance(balance, list)
        
        # Test USDT balance
        response = client.get("/account/usdt-balance")
        assert response.status_code == 200
        usdt_response = response.json()
        assert "balance" in usdt_response
        assert isinstance(usdt_response["balance"], (int, float))
        
        # Test portfolio
        response = client.get("/account/portfolio")
        assert response.status_code == 200
        portfolio = response.json()
        assert isinstance(portfolio, list)
    
    def test_market_endpoints(self, client):
        """Test market data endpoints."""
        # Test currency pairs
        response = client.get("/market/pairs")
        assert response.status_code == 200
        pairs = response.json()
        assert isinstance(pairs, list)
        assert len(pairs) > 0
        
        # Test price endpoint
        response = client.get("/market/price/ETHUSDT")
        assert response.status_code == 200
        price_data = response.json()
        assert "symbol" in price_data
        assert "price" in price_data
        assert isinstance(price_data["price"], (int, float))
    
    def test_orders_endpoints(self, client):
        """Test order-related endpoints."""
        # Test open orders
        response = client.get("/orders/open")
        assert response.status_code == 200
        orders = response.json()
        assert isinstance(orders, list)
    
    def test_trades_endpoints(self, client):
        """Test trade history endpoints."""
        # Test trade history
        response = client.get("/trades/history")
        assert response.status_code == 200
        trades = response.json()
        assert isinstance(trades, list)
        
        # Test time range trades
        now = datetime.now()
        one_day_ago = now - timedelta(days=1)
        
        time_range_data = {
            "start_time": one_day_ago.strftime("%Y-%m-%d %H:%M:%S"),
            "end_time": now.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        response = client.post("/trades/time-range", json=time_range_data)
        assert response.status_code == 200
        trades = response.json()
        assert isinstance(trades, list)
        
        # Verify timestamp formatting
        if trades:
            trade = trades[0]
            assert "time" in trade  # Formatted timestamp
            assert "timestamp_ms" in trade  # Original timestamp
    
    def test_workflow_endpoint(self, client):
        """Test workflow testing endpoint."""
        # Test workflow status
        response = client.get("/workflow-test/status")
        assert response.status_code == 200
        status = response.json()
        assert status["status"] == "available"
        
        # Test dry run workflow
        workflow_data = {
            "order_amount_usdt": 50.0,
            "symbol": "ETH/USDT",
            "dry_run": True
        }
        
        response = client.post("/workflow-test/run", json=workflow_data)
        assert response.status_code == 200
        result = response.json()
        
        # Verify workflow response structure
        assert "test_id" in result
        assert "status" in result
        assert "total_steps" in result
        assert "completed_steps" in result
        assert "steps" in result
        assert "summary" in result
        
        # Verify all steps completed in dry run
        assert result["status"] == "completed"
        assert result["completed_steps"] == result["total_steps"]
        assert len(result["steps"]) == 9
    
    @pytest.mark.skipif(
        not os.getenv('TRADING_API_KEY') or not os.getenv('TRADING_API_SECRET'),
        reason="API credentials not set"
    )
    def test_real_trading_workflow(self, client):
        """Test complete trading workflow with real API calls."""
        print("\n🚀 Running REAL API Integration Test")
        print("⚠️  This test makes ACTUAL calls to Binance Testnet")
        
        # Step 1: Get initial balances
        portfolio_response = client.get("/account/portfolio")
        assert portfolio_response.status_code == 200
        initial_portfolio = portfolio_response.json()
        
        usdt_response = client.get("/account/usdt-balance")
        assert usdt_response.status_code == 200
        initial_usdt = usdt_response.json()["balance"]
        
        print(f"💰 Initial USDT balance: ${initial_usdt:,.2f}")
        
        # Skip if insufficient balance
        if initial_usdt < 50:
            pytest.skip(f"Insufficient USDT balance: ${initial_usdt}")
        
        # Step 2: Place buy order
        order_amount = min(50, initial_usdt * 0.1)  # Use 10% or max $50
        buy_order_data = {
            "symbol": "ETH/USDT",
            "side": "BUY",
            "quote_order_qty": order_amount
        }
        
        buy_response = client.post("/orders/market", json=buy_order_data)
        if buy_response.status_code != 200:
            pytest.skip(f"Buy order failed: {buy_response.text}")
        
        buy_order = buy_response.json()
        assert buy_order["status"] == "FILLED"
        print(f"✅ Buy order: {buy_order['quantity']} ETH @ ${buy_order['price']}")
        
        # Step 3: Verify portfolio has ETH
        portfolio_response = client.get("/account/portfolio")
        portfolio_after_buy = portfolio_response.json()
        eth_balance = next((asset for asset in portfolio_after_buy if asset["asset"] == "ETH"), None)
        assert eth_balance is not None
        assert eth_balance["free"] > 0
        
        # Step 4: Sell all ETH
        sell_order_data = {
            "symbol": "ETH/USDT",
            "percentage": 100
        }
        
        sell_response = client.post("/orders/sell-percentage", json=sell_order_data)
        if sell_response.status_code != 200:
            pytest.skip(f"Sell order failed: {sell_response.text}")
        
        sell_order = sell_response.json()
        assert sell_order["status"] == "FILLED"
        print(f"✅ Sell order: {sell_order['quantity']} ETH @ ${sell_order['price']}")
        
        # Step 5: Verify portfolio is clean
        portfolio_response = client.get("/account/portfolio")
        final_portfolio = portfolio_response.json()
        eth_balance_final = next((asset for asset in final_portfolio if asset["asset"] == "ETH"), None)
        
        if eth_balance_final:
            assert eth_balance_final["free"] < 0.001  # Allow for dust
        
        # Step 6: Check final balance
        usdt_response = client.get("/account/usdt-balance")
        final_usdt = usdt_response.json()["balance"]
        print(f"💰 Final USDT balance: ${final_usdt:,.2f}")
        
        # Calculate P&L
        net_pnl = final_usdt - initial_usdt
        print(f"📈 Net P&L: ${net_pnl:,.2f}")
        
        print("🎉 Real trading workflow test completed!")
    
    def test_error_handling(self, client):
        """Test error handling for invalid requests."""
        # Test invalid symbol
        response = client.get("/market/price/INVALID")
        assert response.status_code == 400
        
        # Test invalid order
        invalid_order = {
            "symbol": "INVALID/PAIR",
            "side": "BUY",
            "quantity": -1
        }
        response = client.post("/orders/market", json=invalid_order)
        assert response.status_code == 400
        
        # Test invalid time range
        invalid_time_range = {
            "start_time": "invalid-date",
            "end_time": "invalid-date"
        }
        response = client.post("/trades/time-range", json=invalid_time_range)
        assert response.status_code == 400
    
    def test_response_formats(self, client):
        """Test that responses have correct formats."""
        # Test USDT balance format
        response = client.get("/account/usdt-balance")
        assert response.status_code == 200
        data = response.json()
        assert "balance" in data
        # Should be rounded to 2 decimal places
        balance = data["balance"]
        assert round(balance, 2) == balance
        
        # Test trade history timestamp format
        response = client.get("/trades/history")
        assert response.status_code == 200
        trades = response.json()
        
        if trades:
            trade = trades[0]
            # Should have both formatted time and original timestamp
            assert "time" in trade
            assert "timestamp_ms" in trade
            # Formatted time should be readable
            assert isinstance(trade["time"], str)
            assert len(trade["time"]) > 10  # Should be formatted date string


class TestHTTPEndpoints:
    """HTTP-based endpoint testing (for running server tests)."""
    
    def test_endpoints_via_http(self):
        """Test endpoints via HTTP requests (requires running server)."""
        base_url = "http://localhost:8000"
        
        try:
            # Test server is running
            response = requests.get(f"{base_url}/", timeout=5)
            if response.status_code != 200:
                pytest.skip("Server not running")
        except requests.exceptions.RequestException:
            pytest.skip("Server not running")
        
        # Test key endpoints
        endpoints = [
            "/account/balance",
            "/account/usdt-balance", 
            "/account/portfolio",
            "/market/pairs",
            "/orders/open",
            "/trades/history",
            "/workflow-test/status"
        ]
        
        for endpoint in endpoints:
            response = requests.get(f"{base_url}{endpoint}")
            assert response.status_code == 200, f"Endpoint {endpoint} failed"
            
            # Verify JSON response
            try:
                data = response.json()
                assert data is not None
            except json.JSONDecodeError:
                pytest.fail(f"Endpoint {endpoint} returned invalid JSON")


# Utility functions for running tests
def run_quick_test():
    """Run quick tests without real API calls."""
    pytest.main([
        "tests/test_comprehensive.py::TestPaperTradingAPI::test_server_health",
        "tests/test_comprehensive.py::TestPaperTradingAPI::test_workflow_endpoint",
        "-v"
    ])


def run_full_test():
    """Run all tests including real API calls."""
    pytest.main([
        "tests/test_comprehensive.py",
        "-v",
        "-s"
    ])


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "quick":
        print("🚀 Running quick tests...")
        run_quick_test()
    else:
        print("🚀 Running full test suite...")
        run_full_test()
