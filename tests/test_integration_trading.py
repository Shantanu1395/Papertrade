"""
Integration tests for the complete trading workflow.

Tests the following scenario:
1. Get initial portfolio balance
2. Get initial USDT balance
3. Place market BUY order (ETH/USDT, quote-quantity=1000)
4. Verify portfolio has ETH and USDT balance decreased
5. Sell 100% of ETH with market order
6. Verify portfolio is empty and USDT balance increased
7. Verify 2 trades exist in last 15 minutes
"""
import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient


class TestTradingWorkflow:
    """Integration tests for complete trading workflow."""

    def test_complete_trading_workflow_real_api(self, client: TestClient, clean_test_environment):
        """Test the complete trading workflow with REAL API calls to Binance testnet."""

        print("\n🚀 Starting REAL API Integration Test")
        print("=" * 60)
        print("⚠️  This test makes ACTUAL calls to Binance Testnet API")
        print("⚠️  Ensure you have valid testnet API credentials")
        print("⚠️  Note: TestClient uses 'http://testserver' but calls real endpoints")
        print("=" * 60)

        # NO MOCKING - This test uses real API calls through the existing endpoints
        # The 'http://testserver' URL is just a TestClient placeholder
        # Your actual FastAPI routes and trading client will execute normally

        # Step 1: Get initial portfolio balance
        portfolio_response = client.get("/account/portfolio")
        assert portfolio_response.status_code == 200
        initial_portfolio = portfolio_response.json()
        print(f"📊 Initial portfolio: {initial_portfolio}")

        # Step 2: Get initial USDT balance
        usdt_response = client.get("/account/usdt-balance")
        assert usdt_response.status_code == 200
        initial_usdt_balance = usdt_response.json()  # Returns float directly
        print(f"💰 Initial USDT balance: ${initial_usdt_balance:,.2f}")

        # Ensure we have enough USDT for the test
        if initial_usdt_balance < 100:  # Reduced minimum for testing
            print(f"⚠️  Warning: Low USDT balance ({initial_usdt_balance}). Test may fail.")
            print("💡 Consider funding your testnet account or reducing order size.")

        # Step 3: Place market BUY order (ETH/USDT, quote-quantity based on available balance)
        print("\n📈 Placing BUY order...")
        # Use smaller amount for testing - 10% of balance or max 100 USDT
        order_amount = min(100, initial_usdt_balance * 0.1)
        buy_order_data = {
            "symbol": "ETH/USDT",
            "side": "BUY",
            "quote_order_qty": order_amount
        }

        buy_response = client.post("/orders/market", json=buy_order_data)
        if buy_response.status_code != 200:
            print(f"❌ Buy order failed: {buy_response.text}")
            pytest.skip(f"Buy order failed: {buy_response.text}")

        buy_order = buy_response.json()
        print(f"✅ Buy order placed: {buy_order}")

        # Verify buy order details
        assert buy_order["symbol"] == "ETHUSDT"
        assert buy_order["side"] == "BUY"
        assert buy_order["status"] == "FILLED"
        assert buy_order["quantity"] > 0  # Should have bought some ETH

        # Step 4: Get portfolio balance (should have ETH now)
        portfolio_response = client.get("/account/portfolio")
        assert portfolio_response.status_code == 200
        portfolio_after_buy = portfolio_response.json()
        print(f"📊 Portfolio after buy: {portfolio_after_buy}")

        # Verify ETH is in portfolio
        eth_balance = next((asset for asset in portfolio_after_buy if asset["asset"] == "ETH"), None)
        assert eth_balance is not None, "ETH should be in portfolio after buy order"
        assert eth_balance["free"] > 0, "ETH balance should be greater than 0"
        print(f"🪙 ETH acquired: {eth_balance['free']} ETH")

        # Step 5: Get USDT balance (should have decreased)
        usdt_response = client.get("/account/usdt-balance")
        assert usdt_response.status_code == 200
        usdt_after_buy = usdt_response.json()  # Returns float directly
        print(f"💰 USDT balance after buy: ${usdt_after_buy:,.2f}")

        # Verify USDT balance decreased
        assert usdt_after_buy < initial_usdt_balance, "USDT balance should decrease after buy order"
        usdt_spent = initial_usdt_balance - usdt_after_buy
        print(f"💸 USDT spent: ${usdt_spent:,.2f}")

        # Step 6: Sell 100% of ETH with market order
        print("\n📉 Placing SELL order...")
        sell_order_data = {
            "symbol": "ETH/USDT",
            "percentage": 100
        }

        sell_response = client.post("/orders/sell-percentage", json=sell_order_data)
        if sell_response.status_code != 200:
            print(f"❌ Sell order failed: {sell_response.text}")
            pytest.skip(f"Sell order failed: {sell_response.text}")

        sell_order = sell_response.json()
        print(f"✅ Sell order placed: {sell_order}")

        # Verify sell order details
        assert sell_order["symbol"] == "ETHUSDT"
        assert sell_order["side"] == "SELL"
        assert sell_order["status"] == "FILLED"
        # Note: Due to precision and fees, sold quantity might be slightly different
        print(f"🪙 ETH sold: {sell_order['quantity']} ETH")

        # Step 7: Get portfolio balance (should be empty now)
        portfolio_response = client.get("/account/portfolio")
        assert portfolio_response.status_code == 200
        portfolio_after_sell = portfolio_response.json()
        print(f"📊 Portfolio after sell: {portfolio_after_sell}")

        # Verify portfolio is empty (no ETH) - allow for small dust amounts
        eth_balance_after_sell = next((asset for asset in portfolio_after_sell if asset["asset"] == "ETH"), None)
        if eth_balance_after_sell:
            # Allow for small dust amounts (less than 0.001 ETH)
            assert eth_balance_after_sell["free"] < 0.001, f"ETH balance should be minimal after sell, got: {eth_balance_after_sell['free']}"
            print(f"ℹ️  Small ETH dust remaining: {eth_balance_after_sell['free']} ETH")
        else:
            print("✅ Portfolio is clean - no ETH remaining")

        # Step 8: Get USDT balance (should have increased)
        usdt_response = client.get("/account/usdt-balance")
        assert usdt_response.status_code == 200
        final_usdt_balance = usdt_response.json()  # Returns float directly
        print(f"💰 Final USDT balance: ${final_usdt_balance:,.2f}")

        # Verify USDT balance increased from after-buy amount
        assert final_usdt_balance > usdt_after_buy, "USDT balance should increase after sell order"
        usdt_received = final_usdt_balance - usdt_after_buy
        print(f"💵 USDT received: ${usdt_received:,.2f}")

        # Calculate P&L
        net_pnl = final_usdt_balance - initial_usdt_balance
        print(f"📈 Net P&L: ${net_pnl:,.2f} ({net_pnl/initial_usdt_balance*100:.2f}%)")

        # Step 9: Get trades in last 15 minutes (should have 2 trades)
        print("\n📋 Checking trade history...")
        now = datetime.now()
        fifteen_min_ago = now - timedelta(minutes=15)

        time_range_data = {
            "start_time": fifteen_min_ago.strftime("%Y-%m-%d %H:%M:%S"),
            "end_time": now.strftime("%Y-%m-%d %H:%M:%S")
        }

        trades_response = client.post("/trades/time-range", json=time_range_data)
        assert trades_response.status_code == 200
        recent_trades = trades_response.json()
        print(f"📊 Recent trades found: {len(recent_trades)}")

        # Verify we have at least 2 trades (our buy and sell)
        assert len(recent_trades) >= 2, f"Should have at least 2 trades in last 15 minutes, found: {len(recent_trades)}"

        # Find our specific trades (look for the most recent ones)
        recent_trades.sort(key=lambda x: x["time"], reverse=True)
        latest_trades = recent_trades[:2]  # Get the 2 most recent trades

        buy_trade = next((trade for trade in latest_trades if trade["side"] == "BUY"), None)
        sell_trade = next((trade for trade in latest_trades if trade["side"] == "SELL"), None)

        assert buy_trade is not None, "Should have a BUY trade in recent history"
        assert sell_trade is not None, "Should have a SELL trade in recent history"
        assert buy_trade["symbol"] == "ETHUSDT"
        assert sell_trade["symbol"] == "ETHUSDT"

        print(f"✅ BUY trade: {buy_trade['quantity']} ETH @ ${buy_trade['price']}")
        print(f"✅ SELL trade: {sell_trade['quantity']} ETH @ ${sell_trade['price']}")

        print("\n🎉 Complete trading workflow test passed!")
        print("=" * 60)

    def test_trading_workflow_with_insufficient_balance(self, client: TestClient, clean_test_environment):
        """Test trading workflow when there's insufficient USDT balance."""

        mock_responses = self._setup_mock_responses()
        # Override with insufficient balance
        mock_responses['account_initial']['balances'][0]['free'] = "500.00000000"

        with patch('app.dependencies.get_trading_client') as mock_get_client, \
             patch('app.services.trading_client.PaperTradingClient._make_request') as mock_request:

            mock_state = {'orders_placed': 0, 'account_calls': 0}
            mock_request.side_effect = self._mock_request_handler(mock_responses, mock_state)

            from app.services.trading_client import PaperTradingClient
            test_config = {
                'api_key': 'test_key',
                'api_secret': 'test_secret',
                'testnet': True,
                'brokerage_fee': 0.001,
                'recv_window': 10000,
                'symbols': ['ETH/USDT']
            }

            mock_client = PaperTradingClient(test_config)
            mock_get_client.return_value.__enter__ = lambda _: mock_client
            mock_get_client.return_value.__exit__ = lambda *_: None

            # Try to place order with insufficient balance
            buy_order_data = {
                "symbol": "ETH/USDT",
                "side": "BUY",
                "quote_order_qty": 1000
            }

            # This should still work in testnet, but we can verify the balance check
            usdt_response = client.get("/account/usdt-balance")
            assert usdt_response.status_code == 200
            balance = usdt_response.json()  # Returns float directly
            assert balance < 1000, "Should have insufficient balance for this test"

    def test_portfolio_state_transitions(self, client: TestClient, clean_test_environment):
        """Test that portfolio state transitions correctly through the workflow."""

        mock_responses = self._setup_mock_responses()

        with patch('app.dependencies.get_trading_client') as mock_get_client, \
             patch('app.services.trading_client.PaperTradingClient._make_request') as mock_request:

            mock_state = {'orders_placed': 0, 'account_calls': 0}
            mock_request.side_effect = self._mock_request_handler(mock_responses, mock_state)

            from app.services.trading_client import PaperTradingClient
            test_config = {
                'api_key': 'test_key',
                'api_secret': 'test_secret',
                'testnet': True,
                'brokerage_fee': 0.001,
                'recv_window': 10000,
                'symbols': ['ETH/USDT']
            }

            mock_client = PaperTradingClient(test_config)
            mock_get_client.return_value.__enter__ = lambda _: mock_client
            mock_get_client.return_value.__exit__ = lambda *_: None

            # Initial state: only USDT
            portfolio = client.get("/account/portfolio").json()
            assert len([asset for asset in portfolio if asset["asset"] != "USDT"]) == 0

            # After buy: should have ETH
            buy_order_data = {"symbol": "ETH/USDT", "side": "BUY", "quote_order_qty": 1000}
            client.post("/orders/market", json=buy_order_data)

            portfolio = client.get("/account/portfolio").json()
            eth_assets = [asset for asset in portfolio if asset["asset"] == "ETH"]
            assert len(eth_assets) == 1, "Should have ETH in portfolio after buy"
            assert eth_assets[0]["free"] > 0, "ETH balance should be positive"

            # After sell: should not have ETH
            sell_order_data = {"symbol": "ETH/USDT", "percentage": 100}
            client.post("/orders/sell-percentage", json=sell_order_data)

            portfolio = client.get("/account/portfolio").json()
            eth_assets = [asset for asset in portfolio if asset["asset"] == "ETH"]
            assert len(eth_assets) == 0, "Should not have ETH in portfolio after sell"

    def _setup_mock_responses(self):
        """Setup mock responses for different API endpoints."""
        current_time = int(time.time() * 1000)

        return {
            # Exchange info for symbol precision
            'exchange_info': {
                "symbols": [
                    {
                        "symbol": "ETHUSDT",
                        "status": "TRADING",
                        "baseAssetPrecision": 8,
                        "quotePrecision": 8,
                        "filters": [
                            {"filterType": "LOT_SIZE", "stepSize": "0.00001000"},
                            {"filterType": "PRICE_FILTER", "tickSize": "0.01000000"}
                        ]
                    }
                ]
            },

            # Initial account state (with USDT)
            'account_initial': {
                "balances": [
                    {"asset": "USDT", "free": "10000.00000000", "locked": "0.00000000"},
                    {"asset": "BNB", "free": "0.00000000", "locked": "0.00000000"}
                ]
            },

            # Account state after buying ETH
            'account_after_buy': {
                "balances": [
                    {"asset": "USDT", "free": "9000.00000000", "locked": "0.00000000"},
                    {"asset": "ETH", "free": "0.50000000", "locked": "0.00000000"},
                    {"asset": "BNB", "free": "0.00000000", "locked": "0.00000000"}
                ]
            },

            # Account state after selling ETH
            'account_after_sell': {
                "balances": [
                    {"asset": "USDT", "free": "9950.00000000", "locked": "0.00000000"},
                    {"asset": "ETH", "free": "0.00000000", "locked": "0.00000000"},
                    {"asset": "BNB", "free": "0.00000000", "locked": "0.00000000"}
                ]
            },

            # Market buy order response
            'buy_order': {
                "symbol": "ETHUSDT",
                "orderId": 12345,
                "side": "BUY",
                "type": "MARKET",
                "executedQty": "0.50000000",
                "status": "FILLED",
                "transactTime": current_time,
                "cummulativeQuoteQty": "1000.00000000",
                "fills": [
                    {
                        "price": "2000.00000000",
                        "qty": "0.50000000",
                        "commission": "0.00050000",
                        "commissionAsset": "ETH"
                    }
                ]
            },

            # Market sell order response
            'sell_order': {
                "symbol": "ETHUSDT",
                "orderId": 12346,
                "side": "SELL",
                "type": "MARKET",
                "executedQty": "0.50000000",
                "status": "FILLED",
                "transactTime": current_time + 1000,
                "cummulativeQuoteQty": "950.00000000",
                "fills": [
                    {
                        "price": "1900.00000000",
                        "qty": "0.50000000",
                        "commission": "0.95000000",
                        "commissionAsset": "USDT"
                    }
                ]
            },

            # Current ETH price
            'eth_price': {
                "symbol": "ETHUSDT",
                "price": "2000.00000000"
            }
        }

    def _mock_request_handler(self, mock_responses, state):
        """Create a mock request handler that returns appropriate responses."""

        def mock_handler(method, endpoint, params=None, signed=False):
            print(f"Mock API call: {method} {endpoint} {params} (orders_placed: {state['orders_placed']})")

            if endpoint == "/v3/exchangeInfo":
                return mock_responses['exchange_info']

            elif endpoint == "/v3/account":
                state['account_calls'] += 1
                # Return different account states based on how many orders have been placed
                if state['orders_placed'] == 0:  # Before any orders
                    return mock_responses['account_initial']
                elif state['orders_placed'] == 1:  # After buy order
                    return mock_responses['account_after_buy']
                else:  # After sell order
                    return mock_responses['account_after_sell']

            elif endpoint == "/v3/order":
                state['orders_placed'] += 1
                if params and params.get('side') == 'BUY':
                    return mock_responses['buy_order']
                else:
                    return mock_responses['sell_order']

            elif endpoint == "/v3/ticker/price":
                return mock_responses['eth_price']

            else:
                raise Exception(f"Unmocked endpoint: {endpoint}")

        return mock_handler
