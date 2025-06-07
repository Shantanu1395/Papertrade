import requests
import logging
import time
import hashlib
import hmac
import os
import json
import threading
from urllib.parse import urlencode
from decimal import Decimal, ROUND_DOWN
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Optional, Any

from app.core import (
    settings,
    TradingAPIError,
    InvalidSymbolError,
    OrderValidationError,
    file_manager,
    to_timestamp,
    validate_symbol,
    validate_side,
    validate_positive_number
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class PaperTradingClient:
    def __init__(self, config: Optional[Dict] = None):
        # Use config or fall back to global settings
        if config is None:
            config = {}

        self.api_key = config.get('api_key') or settings.binance_api_key
        self.api_secret = config.get('api_secret') or settings.binance_api_secret

        if not self.api_key or not self.api_secret:
            raise ValueError("API key and secret must be provided in config or environment variables")

        self.base_url = settings.binance_base_url if config.get('testnet', settings.binance_testnet) else "https://api.binance.com/api"
        self.brokerage_fee = config.get('brokerage_fee', settings.default_brokerage_fee)
        self.symbols = config.get('symbols', settings.default_symbols)
        self.recv_window = config.get('recv_window', settings.binance_recv_window)

        # Initialize HTTP session
        self.session = requests.Session()
        self.session.headers.update({"X-MBX-APIKEY": self.api_key})

        # Initialize valid trading pairs
        self.valid_pairs = self.view_all_currency_pairs()
        if not self.valid_pairs:
            self.valid_pairs = settings.default_symbols
            logging.warning(f"Failed to fetch valid trading pairs, using fallback: {settings.default_symbols}")
        else:
            logging.info(f"Successfully fetched {len(self.valid_pairs)} trading pairs")

        # File paths using settings
        self.trade_history_file = settings.trade_history_file
        self.excluded_currencies_file = settings.excluded_currencies_file
        self.file_lock = threading.Lock()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()

    def _generate_signature(self, query_string):
        return hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

    def _make_request(self, method, endpoint, params=None, signed=False):
        url = f"{self.base_url}{endpoint}"
        params = params or {}

        if signed:
            params['timestamp'] = int(time.time() * 1000)
            params['recvWindow'] = self.recv_window
            query_string = urlencode(params)
            signature = self._generate_signature(query_string)
            params['signature'] = signature

        try:
            if method == "GET":
                response = self.session.get(url, params=params)
            elif method == "POST":
                response = self.session.post(url, params=params)
            elif method == "DELETE":
                response = self.session.delete(url, params=params)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            error_msg = f"API request failed: {e}"
            if hasattr(e, 'response') and e.response:
                try:
                    error_data = e.response.json()
                    error_msg = f"API error: {error_data.get('msg', str(e))}"
                except ValueError:
                    error_msg = f"API error: {e.response.text}"
            logging.error(error_msg)
            raise TradingAPIError(error_msg)

    def _save_trade_to_json(self, trade_data):
        """Save trade data to JSON file using file manager."""
        success = file_manager.append_json_list("trade_history.json", trade_data)
        if success:
            logging.info(f"Trade saved to {self.trade_history_file}")
        else:
            logging.error(f"Failed to save trade to {self.trade_history_file}")

    def _get_symbol_precision(self, symbol):
        try:
            response = self._make_request("GET", "/v3/exchangeInfo")
            for s in response.get("symbols", []):
                if s["symbol"] == symbol:
                    quantity_precision = int(s.get("baseAssetPrecision", 8))
                    price_precision = int(s.get("quotePrecision", 8))

                    # Look for specific filters
                    for f in s.get("filters", []):
                        if f["filterType"] == "LOT_SIZE":
                            step_size = f["stepSize"]
                            # Handle scientific notation properly
                            if 'e' in step_size.lower():
                                quantity_precision = abs(int(step_size.lower().split('e')[1]))
                            elif '.' in step_size:
                                quantity_precision = len(step_size.split('.')[1].rstrip('0'))
                            else:
                                quantity_precision = 0
                        elif f["filterType"] == "PRICE_FILTER":
                            tick_size = f["tickSize"]
                            # Handle scientific notation properly
                            if 'e' in tick_size.lower():
                                price_precision = abs(int(tick_size.lower().split('e')[1]))
                            elif '.' in tick_size:
                                price_precision = len(tick_size.split('.')[1].rstrip('0'))
                            else:
                                price_precision = 0

                    logging.info(f"Symbol {symbol}: quantity_precision={quantity_precision}, price_precision={price_precision}")
                    return quantity_precision, price_precision

            # Default values if symbol not found
            logging.warning(f"Symbol {symbol} not found, using defaults")
            return 8, 8
        except Exception as e:
            logging.error(f"Failed to get symbol precision: {e}")
            return 8, 8

    def _validate_order_params(self, symbol, side, quantity=None, price=None, quote_order_qty=None):
        if side.upper() not in ["BUY", "SELL"]:
            raise ValueError(f"Invalid side: {side}. Must be 'BUY' or 'SELL'")

        symbol = symbol.replace("/", "")
        if symbol not in self.valid_pairs:
            raise ValueError(f"Invalid symbol: {symbol}. Must be one of {self.valid_pairs}")

        if quantity is None and quote_order_qty is None:
            raise ValueError("Either quantity or quote_order_qty must be provided")

        if quantity is not None and quantity <= 0:
            raise ValueError(f"Invalid quantity: {quantity}. Must be greater than 0")

        if quote_order_qty is not None and quote_order_qty <= 0:
            raise ValueError(f"Invalid quote_order_qty: {quote_order_qty}. Must be greater than 0")

        if price is not None and price <= 0:
            raise ValueError(f"Invalid price: {price}. Must be greater than 0")

    def view_account_balance(self):
        """Get account balance excluding currencies in exclusion list."""
        excluded_currencies = file_manager.read_json("excluded_currencies.json", [])

        response = self._make_request("GET", "/v3/account", signed=True)
        balances = [
            {"asset": b["asset"], "free": float(b["free"]), "locked": float(b["locked"])}
            for b in response.get("balances", [])
            if (float(b["free"]) > 0 or float(b["locked"]) > 0)
            and b["asset"] not in excluded_currencies  # Apply exclusion filter
        ]
        return balances

    def view_usdt_balance(self):
        try:
            response = self._make_request("GET", "/v3/account", signed=True)
            for b in response.get("balances", []):
                if b["asset"] == "USDT":
                    usdt_balance = float(b["free"])
                    logging.info(f"USDT balance: {usdt_balance}")
                    return usdt_balance
            logging.warning("USDT balance not found")
            return 0.0
        except TradingAPIError as e:
            logging.error(f"Failed to fetch USDT balance: {e}")
            return 0.0

    def view_portfolio(self):
        """Get portfolio (non-USDT assets) excluding currencies in exclusion list."""
        excluded_currencies = file_manager.read_json("excluded_currencies.json", [])

        try:
            response = self._make_request("GET", "/v3/account", signed=True)
            portfolio = [
                {"asset": b["asset"], "free": float(b["free"]), "locked": float(b["locked"])}
                for b in response.get("balances", [])
                if (float(b["free"]) > 0.000001 or float(b["locked"]) > 0.000001)  # Filter out dust amounts
                and b["asset"] != "USDT"
                and b["asset"] not in excluded_currencies
            ]
            return portfolio
        except TradingAPIError as e:
            logging.error(f"Failed to fetch portfolio: {e}")
            return []

    def view_all_currency_pairs(self):
        try:
            response = self._make_request("GET", "/v3/exchangeInfo")
            pairs = [s["symbol"] for s in response.get("symbols", []) if s.get("status") == "TRADING"]
            return pairs
        except TradingAPIError as e:
            logging.error(f"Failed to fetch currency pairs: {e}")
            return []

    def view_current_price(self, symbol):
        symbol = symbol.replace("/", "")
        try:
            response = self._make_request("GET", "/v3/ticker/price", {"symbol": symbol})
            return float(response["price"])
        except TradingAPIError as e:
            logging.error(f"Failed to fetch current price for {symbol}: {e}")
            raise

    def view_all_fulfilled_orders(self):
        """Get all fulfilled orders from trade history."""
        try:
            trades = file_manager.read_json("trade_history.json", [])

            # Format trades for display
            formatted_trades = []
            for trade in trades:
                formatted_trade = {
                    "symbol": trade["symbol"],
                    "side": trade["side"],
                    "quantity": trade["quantity"],
                    "price": trade["price"],
                    "quoteQty": trade.get("quoteQty", trade["quantity"] * trade["price"]),
                    "commission": trade.get("commission", 0),
                    "commissionAsset": trade.get("commissionAsset", "Unknown"),
                    "time": trade["time"],
                    "tradeId": trade.get("tradeId", "Unknown"),
                    "orderType": trade.get("orderType", "Unknown")
                }
                formatted_trades.append(formatted_trade)

            return formatted_trades
        except Exception as e:
            logging.error(f"Failed to fetch fulfilled orders: {e}")
            return []

    def get_trades_in_time_range(self, start_time, end_time):
        """Get trades within a specific time range."""
        start_ts = to_timestamp(start_time)
        end_ts = to_timestamp(end_time)

        try:
            all_trades = file_manager.read_json("trade_history.json", [])

            # Filter trades by time range
            filtered_trades = []
            for trade in all_trades:
                trade_time = trade["time"]
                if start_ts <= trade_time <= end_ts:
                    filtered_trades.append(trade)

            # Sort by time
            filtered_trades.sort(key=lambda x: x["time"])

            return filtered_trades
        except Exception as e:
            logging.error(f"Failed to fetch trades in time range: {e}")
            return []

    def calculate_pnl_in_time_range(self, start_time, end_time):
        """Calculate PnL for trades within a specific time range."""
        start_ts = to_timestamp(start_time)
        end_ts = to_timestamp(end_time)

        try:
            trades = self.get_trades_in_time_range(start_ts, end_ts)

            # Simple approach: Calculate total USDT in vs USDT out
            total_usdt_spent = 0  # Money spent buying assets
            total_usdt_received = 0  # Money received selling assets
            fees = defaultdict(float)

            # Track current holdings and sales from trades in this period
            asset_holdings = defaultdict(float)
            asset_cost_basis = defaultdict(float)  # Total cost for each asset
            asset_sales_revenue = defaultdict(float)  # Total sales revenue for each asset

            # Process each trade
            for trade in trades:
                symbol = trade["symbol"]
                base_asset = symbol.replace("USDT", "")
                side = trade["side"]
                quantity = float(trade["quantity"])
                price = float(trade["price"])
                quote_qty = float(trade.get("quoteQty", quantity * price))
                commission = float(trade.get("commission", 0))
                commission_asset = trade.get("commissionAsset", "USDT")

                # Track fees
                fees[commission_asset] += commission

                if side == "BUY":
                    # Spent USDT to buy asset
                    total_usdt_spent += quote_qty
                    asset_holdings[base_asset] += quantity
                    asset_cost_basis[base_asset] += quote_qty

                    # Adjust for commission in base asset
                    if commission_asset == base_asset:
                        asset_holdings[base_asset] -= commission

                elif side == "SELL":
                    # Received USDT from selling asset
                    total_usdt_received += quote_qty
                    asset_holdings[base_asset] -= quantity
                    asset_sales_revenue[base_asset] += quote_qty

                    # Adjust for commission in USDT
                    if commission_asset == "USDT":
                        total_usdt_received -= commission
                        asset_sales_revenue[base_asset] -= commission

            # Calculate realized PnL (simple approach)
            # Realized PnL = Total USDT received from sales - Total USDT spent on purchases
            realized_pnl_total = total_usdt_received - total_usdt_spent

            # Calculate unrealized PnL for remaining holdings
            unrealized_pnl_total = 0
            current_prices = {}
            asset_details = {}

            # Get current actual portfolio to verify our calculations
            try:
                actual_portfolio = self.view_account_balance()
                actual_holdings = {asset["asset"]: asset["free"] for asset in actual_portfolio}
            except:
                actual_holdings = {}

            # Process all assets that were involved in trades
            all_assets = set(asset_holdings.keys()) | set(asset_cost_basis.keys()) | set(asset_sales_revenue.keys())

            for asset in all_assets:
                # Use actual portfolio balance if available, otherwise use calculated balance
                if asset in actual_holdings:
                    current_holding = actual_holdings[asset]
                else:
                    current_holding = asset_holdings.get(asset, 0)

                # Calculate individual asset realized PnL
                cost_basis = asset_cost_basis.get(asset, 0)
                sales_revenue = asset_sales_revenue.get(asset, 0)
                asset_realized_pnl = sales_revenue - cost_basis

                # Only calculate unrealized PnL if we have positive holdings
                if current_holding > 0:
                    try:
                        current_price = self.view_current_price(f"{asset}USDT")
                        current_prices[asset] = current_price
                        current_value = current_holding * current_price

                        # For unrealized PnL, we need the cost basis of remaining holdings
                        # Since we don't have perfect FIFO tracking, use a simplified approach
                        # If we have remaining holdings, assume they have proportional cost basis
                        if cost_basis > 0 and sales_revenue > 0:
                            # We bought and sold some, remaining holdings have remaining cost basis
                            remaining_cost_basis = max(0, cost_basis - sales_revenue)
                            unrealized_pnl = current_value - remaining_cost_basis
                        elif cost_basis > 0:
                            # We bought but didn't sell, all cost basis applies to current holdings
                            unrealized_pnl = current_value - cost_basis
                        else:
                            # No cost basis tracked
                            unrealized_pnl = current_value

                        unrealized_pnl_total += unrealized_pnl

                        asset_details[asset] = {
                            "current_balance": current_holding,
                            "total_cost": cost_basis,
                            "total_sales": sales_revenue,
                            "current_price": current_price,
                            "current_value": current_value,
                            "realized_pnl": asset_realized_pnl,
                            "unrealized_pnl": unrealized_pnl,
                            "total_pnl": asset_realized_pnl + unrealized_pnl
                        }

                    except Exception as e:
                        logging.error(f"Failed to get current price for {asset}: {e}")
                        current_prices[asset] = 0
                        asset_details[asset] = {
                            "current_balance": current_holding,
                            "total_cost": cost_basis,
                            "total_sales": sales_revenue,
                            "current_price": 0,
                            "current_value": 0,
                            "realized_pnl": asset_realized_pnl,
                            "unrealized_pnl": 0,
                            "total_pnl": asset_realized_pnl
                        }
                else:
                    # No current holdings - all PnL is realized
                    try:
                        current_price = self.view_current_price(f"{asset}USDT")
                        current_prices[asset] = current_price
                    except:
                        current_price = 0
                        current_prices[asset] = 0

                    asset_details[asset] = {
                        "current_balance": 0,
                        "total_cost": cost_basis,
                        "total_sales": sales_revenue,
                        "current_price": current_price,
                        "current_value": 0,
                        "realized_pnl": asset_realized_pnl,
                        "unrealized_pnl": 0,  # No unrealized since no holdings
                        "total_pnl": asset_realized_pnl
                    }

            # Total PnL
            total_pnl = realized_pnl_total + unrealized_pnl_total

            # Format the report
            report = {
                "time_range": {
                    "start": datetime.fromtimestamp(start_ts/1000).strftime("%Y-%m-%d %H:%M:%S"),
                    "end": datetime.fromtimestamp(end_ts/1000).strftime("%Y-%m-%d %H:%M:%S")
                },
                "summary": {
                    "usdt_spent": total_usdt_spent,
                    "usdt_received": total_usdt_received,
                    "total_realized_pnl": realized_pnl_total,
                    "total_unrealized_pnl": unrealized_pnl_total,
                    "total_pnl": total_pnl,
                    "roi_percentage": (total_pnl / total_usdt_spent * 100) if total_usdt_spent > 0 else 0
                },
                "assets": asset_details,
                "fees": dict(fees)
            }

            return report
        except Exception as e:
            logging.error(f"Failed to calculate PNL: {e}")
            raise

    def place_limit_order(self, symbol, side, quantity, price):
        self._validate_order_params(symbol, side, quantity=quantity, price=price)
        symbol = symbol.replace("/", "")
        quantity_precision, price_precision = self._get_symbol_precision(symbol)
        quantity = float(Decimal(str(quantity)).quantize(Decimal(f"0.{'0' * quantity_precision}"), rounding=ROUND_DOWN))
        price = float(Decimal(str(price)).quantize(Decimal(f"0.{'0' * price_precision}"), rounding=ROUND_DOWN))
        params = {
            "symbol": symbol,
            "side": side.upper(),
            "type": "LIMIT",
            "quantity": quantity,
            "price": price,
            "timeInForce": "GTC",
            "newOrderRespType": "FULL"
        }
        response = self._make_request("POST", "/v3/order", params, signed=True)
        if response and "orderId" in response:
            order = {
                "symbol": response["symbol"],
                "orderId": response["orderId"],
                "side": response["side"],
                "type": response["type"],
                "quantity": float(response["origQty"]),
                "price": float(response["price"]),
                "status": response["status"],
                "time": response["transactTime"],
                "commission": float(response.get("fills", [{}])[0].get("commission", 0))
            }
            logging.info(f"Placed limit order: {order}")
            if response.get("status") == "FILLED":
                trade_data = {
                    "symbol": order["symbol"],
                    "side": order["side"],
                    "quantity": order["quantity"],
                    "price": order["price"],
                    "quoteQty": float(response.get("cummulativeQuoteQty", order["quantity"] * order["price"])),
                    "commission": order["commission"],
                    "commissionAsset": response.get("fills", [{}])[0].get("commissionAsset", "Unknown"),
                    "time": order["time"],
                    "tradeId": response.get("orderId"),
                    "orderType": order["type"]
                }
                self._save_trade_to_json(trade_data)
            return order
        logging.error(f"Failed to place limit order for {symbol}")
        return None

    def place_market_order(self, symbol, side, quantity=None, quote_order_qty=None):
        self._validate_order_params(symbol, side, quantity=quantity, quote_order_qty=quote_order_qty)
        symbol = symbol.replace("/", "")
        params = {
            "symbol": symbol,
            "side": side.upper(),
            "type": "MARKET",
            "newOrderRespType": "FULL"
        }

        if quantity is not None:
            quantity_precision, _ = self._get_symbol_precision(symbol)
            logging.info(f"Sell order for {symbol}: original_quantity={quantity}, precision={quantity_precision}")

            # Use ROUND_HALF_UP instead of ROUND_DOWN to avoid rounding to 0
            from decimal import ROUND_HALF_UP
            quantity = float(Decimal(str(quantity)).quantize(Decimal(f"0.{'0' * quantity_precision}"), rounding=ROUND_HALF_UP))
            logging.info(f"Rounded quantity: {quantity}")

            if quantity <= 0:
                logging.error(f"Quantity rounded to 0 for {symbol}. Original: {quantity}, Precision: {quantity_precision}")
                raise ValueError(f"Quantity too small after rounding: {quantity}")

            params["quantity"] = quantity
        elif quote_order_qty is not None:
            # Add minimum quote order quantity validation
            if quote_order_qty < 0.001:
                raise ValueError(f"Quote order quantity too small: {quote_order_qty}. Minimum is 0.001")
            params["quoteOrderQty"] = quote_order_qty

        response = self._make_request("POST", "/v3/order", params, signed=True)
        if response and "orderId" in response:
            order = {
                "symbol": response["symbol"],
                "orderId": response["orderId"],
                "side": response["side"],
                "type": response["type"],
                "quantity": float(response["executedQty"]),
                "price": float(response.get("fills", [{}])[0].get("price", 0)),
                "status": response["status"],
                "time": response["transactTime"],
                "commission": sum(float(fill.get("commission", 0)) for fill in response.get("fills", []))
            }
            logging.info(f"Placed market order: {order}")

            if response.get("status") == "FILLED":
                trade_data = {
                    "symbol": order["symbol"],
                    "side": order["side"],
                    "quantity": order["quantity"],
                    "price": order["price"],
                    "quoteQty": float(response.get("cummulativeQuoteQty", 0)),
                    "commission": order["commission"],
                    "commissionAsset": response.get("fills", [{}])[0].get("commissionAsset", "Unknown"),
                    "time": order["time"],
                    "tradeId": response.get("orderId"),
                    "orderType": order["type"]
                }
                self._save_trade_to_json(trade_data)
            return order
        logging.error(f"Failed to place market order for {symbol}")
        return None

    def sell_asset_by_percentage(self, symbol, percentage=100):
        if percentage <= 0 or percentage > 100:
            raise ValueError(f"Invalid percentage: {percentage}. Must be between 0 and 100")

        symbol = symbol.replace("/", "")
        base_asset = symbol.replace("USDT", "")

        # Get current balance
        balances = self.view_account_balance()
        asset_balance = next((b["free"] for b in balances if b["asset"] == base_asset), 0)

        if asset_balance <= 0:
            logging.warning(f"No {base_asset} balance to sell")
            return None

        # Calculate quantity to sell
        sell_quantity = asset_balance * (percentage / 100)
        if sell_quantity <= 0:
            logging.warning(f"Calculated sell quantity is too small: {sell_quantity}")
            return None

        # Place market sell order
        return self.place_market_order(symbol, "SELL", quantity=sell_quantity)

    def view_open_orders(self, symbol=None):
        params = {}
        if symbol:
            params["symbol"] = symbol.replace("/", "")

        try:
            response = self._make_request("GET", "/v3/openOrders", params, signed=True)
            orders = []
            for order in response:
                formatted_order = {
                    "symbol": order["symbol"],
                    "orderId": order["orderId"],
                    "side": order["side"],
                    "type": order["type"],
                    "price": float(order["price"]),
                    "origQty": float(order["origQty"]),
                    "executedQty": float(order["executedQty"]),
                    "status": order["status"],
                    "time": order["time"]
                }
                orders.append(formatted_order)
            return orders
        except TradingAPIError as e:
            logging.error(f"Failed to fetch open orders: {e}")
            return []

    def sell_all_to_usdt(self):
        portfolio = self.view_portfolio()
        if not portfolio:
            logging.info("No assets to sell")
            return self.view_usdt_balance()

        usdt_initial = self.view_usdt_balance()
        logging.info(f"Initial USDT balance: {usdt_initial}")

        for asset in portfolio:
            symbol = f"{asset['asset']}USDT"
            if symbol.replace("/", "") not in self.valid_pairs:
                logging.warning(f"Cannot sell {asset['asset']}: No USDT pair available")
                continue

            # Skip very small amounts that would cause errors
            if asset['free'] < 0.000001:
                logging.info(f"Skipping {asset['asset']}: Amount too small ({asset['free']})")
                continue

            logging.info(f"Selling {asset['free']} {asset['asset']} to USDT")
            try:
                self.place_market_order(symbol, "SELL", quantity=asset["free"])
            except Exception as e:
                logging.error(f"Failed to sell {asset['asset']}: {e}")
                # Add to exclusion list if sell fails
                excluded_currencies = file_manager.read_json("excluded_currencies.json", [])
                if asset['asset'] not in excluded_currencies:
                    excluded_currencies.append(asset['asset'])
                    file_manager.write_json("excluded_currencies.json", excluded_currencies)
                    logging.info(f"Added {asset['asset']} to exclusion list")

        # Wait a moment for orders to process
        time.sleep(1)

        usdt_final = self.view_usdt_balance()
        logging.info(f"Final USDT balance: {usdt_final}")
        logging.info(f"Gained: {usdt_final - usdt_initial} USDT")

        return usdt_final