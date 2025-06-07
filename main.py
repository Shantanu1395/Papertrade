import requests
import logging
import time
import hashlib
import hmac
from urllib.parse import urlencode
import os
from decimal import Decimal, ROUND_DOWN, ROUND_HALF_UP
from dotenv import load_dotenv
import json
import threading
from datetime import datetime
from collections import defaultdict, deque

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class TradingAPIError(Exception):
    pass

class PaperTradingClient:
    def __init__(self, config):
        self.api_key = config['api_key']
        self.api_secret = config.get('api_secret') or os.getenv('TRADING_API_SECRET')
        if not self.api_secret:
            raise ValueError("API secret must be provided in config or TRADING_API_SECRET env variable")
        self.base_url = "https://testnet.binance.vision/api" if config.get('testnet', True) else "https://api.binance.com/api"
        self.brokerage_fee = config.get('brokerage_fee', 0.001)
        self.symbols = config.get('symbols', [])
        self.recv_window = config.get('recv_window', 10000)
        self.session = requests.Session()
        self.session.headers.update({"X-MBX-APIKEY": self.api_key})
        self.valid_pairs = self.view_all_currency_pairs()
        if not self.valid_pairs:
            self.valid_pairs = ['BTCUSDT', 'ETHUSDT']
            logging.warning("Failed to fetch valid trading pairs, using fallback: BTCUSDT, ETHUSDT")
        else:
            logging.info(f"Successfully fetched {len(self.valid_pairs)} trading pairs")
        self.trade_history_file = 'trade_history.json'
        self.file_lock = threading.Lock()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()

    def _generate_signature(self, query_string):
        return hmac.new(
            self.api_secret.encode('ascii'),
            query_string.encode('ascii'),
            hashlib.sha256
        ).hexdigest()

    def _make_request(self, method, endpoint, params=None, signed=False):
        if params is None:
            params = {}
        request_params = {k: str(v) for k, v in params.items()}
        if signed:
            request_params['recvWindow'] = str(self.recv_window)
            request_params['timestamp'] = str(int(time.time() * 1000))
        
        query_string = urlencode(request_params, safe='')
        
        if signed:
            signature = self._generate_signature(query_string)
            request_params['signature'] = signature
            query_string = urlencode(request_params, safe='')
        
        url = f"{self.base_url}{endpoint}{'?' + query_string if query_string else ''}"
        
        try:
            response = self.session.request(method, url)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logging.error(f"Request failed for {endpoint}: {str(e)}")
            logging.error(f"Response: {response.text if 'response' in locals() else 'No response'}")
            raise TradingAPIError(f"API request failed: {str(e).split('Authorization')[0]}")

    def _save_trade_to_json(self, trade_data):
        """Save trade details to trade_history.json in a thread-safe manner."""
        try:
            with self.file_lock:
                trade_history = []
                if os.path.exists(self.trade_history_file):
                    try:
                        with open(self.trade_history_file, 'r') as f:
                            trade_history = json.load(f)
                    except (json.JSONDecodeError, IOError) as e:
                        logging.warning(f"Failed to read trade_history.json: {e}. Starting with empty history.")
                
                trade_history.append(trade_data)
                
                with open(self.trade_history_file, 'w') as f:
                    json.dump(trade_history, f, indent=2)
                logging.info(f"Saved trade to {self.trade_history_file}: {trade_data['symbol']} {trade_data['side']}")
        except Exception as e:
            logging.error(f"Failed to save trade to {self.trade_history_file}: {e}")

    def _get_symbol_precision(self, symbol):
        response = self._make_request("GET", "/v3/exchangeInfo")
        if response:
            for s in response.get("symbols", []):
                if s["symbol"] == symbol.replace("/", ""):
                    quantity_precision = 8
                    price_precision = 2
                    min_notional = 10.0
                    for f in s.get("filters", []):
                        if f["filterType"] == "PRICE_FILTER":
                            tick_size = f["tickSize"]
                            if '.' in tick_size:
                                # Count decimal places, but handle scientific notation
                                if 'e' in tick_size.lower():
                                    price_precision = abs(int(tick_size.lower().split('e')[1]))
                                else:
                                    price_precision = len(tick_size.split('.')[1].rstrip('0'))
                            else:
                                price_precision = 0
                        if f["filterType"] == "LOT_SIZE":
                            step_size = f["stepSize"]
                            if '.' in step_size:
                                # Count decimal places, but handle scientific notation
                                if 'e' in step_size.lower():
                                    quantity_precision = abs(int(step_size.lower().split('e')[1]))
                                else:
                                    quantity_precision = len(step_size.split('.')[1].rstrip('0'))
                            else:
                                quantity_precision = 0
                        if f["filterType"] == "MIN_NOTIONAL":
                            min_notional = float(f["minNotional"])
                    logging.info(f"Symbol {symbol}: quantity_precision={quantity_precision}, price_precision={price_precision}, min_notional={min_notional}")
                    return quantity_precision, price_precision, min_notional
        logging.warning(f"Could not get precision for {symbol}, using defaults")
        return 8, 2, 10.0

    def _validate_order_params(self, symbol, side, quantity=None, price=None, quote_order_qty=None):
        symbol = symbol.replace("/", "")
        if symbol not in self.valid_pairs:
            raise ValueError(f"Invalid trading pair: {symbol}")
        if side.upper() not in ['BUY', 'SELL']:
            raise ValueError(f"Invalid side: {side}, must be BUY or SELL")
        if quantity is not None and quantity <= 0:
            raise ValueError(f"Quantity must be positive: {quantity}")
        if price is not None and price <= 0:
            raise ValueError(f"Price must be positive: {price}")
        if quote_order_qty is not None and quote_order_qty <= 0:
            raise ValueError(f"Quote order quantity must be positive: {quote_order_qty}")

    def view_account_balance(self):
        response = self._make_request("GET", "/v3/account", signed=True)
        balances = [
            {"asset": b["asset"], "free": float(b["free"]), "locked": float(b["locked"])}
            for b in response.get("balances", []) if float(b["free"]) > 0 or float(b["locked"]) > 0
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
        exclusion_file = 'excluded_currencies.json'
        with self.file_lock:
            if os.path.exists(exclusion_file):
                try:
                    with open(exclusion_file, 'r') as f:
                        excluded_currencies = json.load(f)
                except Exception as e:
                    logging.error(f"Failed to load exclusion list: {e}")
                    excluded_currencies = []
            else:
                excluded_currencies = []
        
        try:
            response = self._make_request("GET", "/v3/account", signed=True)
            portfolio = [
                {"asset": b["asset"], "free": float(b["free"]), "locked": float(b["locked"])}
                for b in response.get("balances", [])
                if (float(b["free"]) > 0 or float(b["locked"]) > 0) and b["asset"] != "USDT" and b["asset"] not in excluded_currencies
            ]
            return portfolio
        except TradingAPIError as e:
            logging.error(f"Failed to fetch portfolio: {e}")
            return []

    def view_all_currency_pairs(self):
        try:
            response = self._make_request("GET", "/v3/exchangeInfo", params={})
            pairs = [
                s["symbol"]
                for s in response.get("symbols", [])
                if s["status"] == "TRADING"
            ]
            logging.info(f"Found {len(pairs)} trading pairs")
            return pairs
        except TradingAPIError:
            logging.error("Failed to fetch trading pairs")
            return []

    def view_current_price(self, symbol):
        symbol = symbol.replace("/", "")
        if symbol not in self.valid_pairs:
            logging.error(f"Invalid trading pair: {symbol}")
            return None
        response = self._make_request("GET", "/v3/ticker/price", params={"symbol": symbol})
        if response and "price" in response:
            price = float(response["price"])
            logging.info(f"Current price of {symbol}: {price} USDT")
            return price
        logging.error(f"Failed to fetch price for {symbol}")
        return None

    def view_all_fulfilled_orders(self):
        symbols = [s.replace("/", "") for s in self.symbols if s.replace("/", "") in self.valid_pairs]
        if not symbols:
            balances = self.view_account_balance()
            symbols = [
                f"{b['asset']}USDT"
                for b in balances
                if b["asset"] != "USDT" and f"{b['asset']}USDT" in self.valid_pairs
            ]
        all_trades = []
        for symbol in symbols:
            try:
                response = self._make_request("GET", "/v3/myTrades", params={"symbol": symbol, "limit": 1000}, signed=True)
                if isinstance(response, dict) and 'code' in response:
                    logging.warning(f"Failed to fetch trades for {symbol}: {response.get('msg', 'Unknown error')}")
                    continue
                if not isinstance(response, list):
                    logging.warning(f"Unexpected response for {symbol}: {response}")
                    continue
                trades = []
                for t in response:
                    required_keys = ['symbol', 'price', 'qty', 'quoteQty', 'commission', 'commissionAsset', 'time', 'id']
                    if not all(key in t for key in required_keys):
                        logging.warning(f"Skipping invalid trade for {symbol}: {t}")
                        continue
                    try:
                        trade = {
                            "symbol": t["symbol"],
                            "side": "BUY" if t["isBuyer"] else "SELL",
                            "price": float(t["price"]),
                            "qty": float(t["qty"]),
                            "quoteQty": float(t["quoteQty"]),
                            "commission": float(t["commission"]),
                            "commissionAsset": t["commissionAsset"],
                            "time": t["time"],
                            "tradeId": t["id"]
                        }
                        trades.append(trade)
                    except (ValueError, TypeError) as e:
                        logging.warning(f"Error processing trade for {symbol}: {e}, Trade: {t}")
                        continue
                all_trades.extend(trades)
                if trades:
                    logging.info(f"Fetched {len(trades)} trades for {symbol}")
            except TradingAPIError as e:
                logging.error(f"API error for {symbol}: {e}")
                continue
        logging.info(f"Total fulfilled orders: {len(all_trades)}")
        return sorted(all_trades, key=lambda x: x["time"])

    def get_trades_in_time_range(self, start_time, end_time):
        """Retrieve trades from trade_history.json within the specified time range."""
        def to_timestamp(t):
            if isinstance(t, str):
                try:
                    dt = datetime.strptime(t, "%Y-%m-%d %H:%M:%S")
                    return int(dt.timestamp() * 1000)
                except ValueError:
                    raise ValueError(f"Invalid time format: {t}. Use 'YYYY-MM-DD HH:MM:SS' or milliseconds")
            return int(t)
        
        start_ms = to_timestamp(start_time)
        end_ms = to_timestamp(end_time)
        
        if start_ms >= end_ms:
            raise ValueError(f"start_time ({start_time}) must be before end_time ({end_time})")
        
        logging.info(f"Fetching trades from {self.trade_history_file} for time range {start_time} to {end_time}")
        
        trades = []
        try:
            with self.file_lock:
                if os.path.exists(self.trade_history_file):
                    with open(self.trade_history_file, 'r') as f:
                        trades = json.load(f)
                else:
                    logging.warning(f"{self.trade_history_file} does not exist. No trades found.")
                    return []
        except (json.JSONDecodeError, IOError) as e:
            logging.error(f"Failed to read {self.trade_history_file}: {e}")
            return []
        
        filtered_trades = []
        for trade in trades:
            if not isinstance(trade, dict) or 'time' not in trade:
                logging.warning(f"Skipping invalid trade entry: {trade}")
                continue
            try:
                trade_time = int(trade['time'])
                if start_ms <= trade_time <= end_ms:
                    filtered_trade = {
                        "symbol": str(trade.get('symbol', '')),
                        "side": str(trade.get('side', '')),
                        "price": float(trade.get('price', 0.0)),
                        "quantity": float(trade.get('quantity', 0.0)),
                        "quoteQty": float(trade.get('quoteQty', 0.0)),
                        "commission": float(trade.get('commission', 0.0)),
                        "commissionAsset": str(trade.get('commissionAsset', '')),
                        "time": trade_time,
                        "tradeId": str(trade.get('tradeId', '')),
                        "orderType": str(trade.get('orderType', ''))
                    }
                    filtered_trades.append(filtered_trade)
            except (ValueError, TypeError) as e:
                logging.warning(f"Error processing trade: {trade}, Error: {e}")
                continue
        
        logging.info(f"Retrieved {len(filtered_trades)} trades from {self.trade_history_file} in time range")
        return sorted(filtered_trades, key=lambda x: x["time"])

    def calculate_pnl_in_time_range(self, start_time, end_time):
        """Calculate realized and unrealized PNL for trades in the given time range."""
        def to_timestamp(t):
            if isinstance(t, str):
                try:
                    dt = datetime.strptime(t, "%Y-%m-%d %H:%M:%S")
                    return int(dt.timestamp() * 1000)
                except ValueError:
                    raise ValueError(f"Invalid time format: {t}. Use 'YYYY-MM-DD HH:MM:SS' or milliseconds")
            return int(t)
        
        start_ms = to_timestamp(start_time)
        end_ms = to_timestamp(end_time)
        
        if start_ms >= end_ms:
            raise ValueError(f"start_time ({start_time}) must be before end_time ({end_time})")
        
        logging.info(f"Calculating PNL for time range {start_time} to {end_time}")
        
        # Fetch trades from trade_history.json
        trades = self.get_trades_in_time_range(start_time, end_time)
        
        # Fetch current portfolio for unrealized PNL
        portfolio = self.view_portfolio()
        
        # Group trades by symbol for realized PNL
        trades_by_symbol = defaultdict(list)
        for trade in trades:
            trades_by_symbol[trade["symbol"]].append(trade)
        
        realized_pnl = 0.0
        unrealized_pnl = 0.0
        symbol_pnl = {}
        open_positions = {}
        
        # Calculate realized PNL
        for symbol, symbol_trades in trades_by_symbol.items():
            buy_queue = deque()  # Store buy trades: (quantity, price, commission_usdt)
            symbol_realized_pnl = 0.0
            
            # Sort trades by time for FIFO
            symbol_trades.sort(key=lambda x: x["time"])
            
            for trade in symbol_trades:
                quantity = trade["quantity"]
                price = trade["price"]
                commission = trade["commission"]
                commission_asset = trade["commissionAsset"]
                
                # Convert commission to USDT
                commission_usdt = commission
                if commission_asset != "USDT" and commission > 0:
                    commission_price = self.view_current_price(f"{commission_asset}USDT")
                    if commission_price:
                        commission_usdt = commission * commission_price
                    else:
                        logging.warning(f"Could not convert commission {commission} {commission_asset} for {symbol}. Ignoring commission.")
                        commission_usdt = 0.0
                
                if trade["side"] == "BUY":
                    buy_queue.append((quantity, price, commission_usdt))
                elif trade["side"] == "SELL":
                    sell_quantity = quantity
                    sell_commission = commission_usdt
                    while sell_quantity > 0 and buy_queue:
                        buy_quantity, buy_price, buy_commission = buy_queue[0]
                        qty_to_match = min(sell_quantity, buy_quantity)
                        
                        # Calculate realized PNL
                        profit = (price - buy_price) * qty_to_match - (buy_commission * (qty_to_match / buy_quantity) + sell_commission * (qty_to_match / quantity))
                        symbol_realized_pnl += profit
                        
                        sell_quantity -= qty_to_match
                        buy_queue[0] = (buy_quantity - qty_to_match, buy_price, buy_commission * ((buy_quantity - qty_to_match) / buy_quantity)) if buy_quantity > qty_to_match else None
                        if buy_queue[0] is None or buy_queue[0][0] <= 0:
                            buy_queue.popleft()
            
            realized_pnl += symbol_realized_pnl
            symbol_pnl[symbol] = {"realized_pnl": symbol_realized_pnl, "unrealized_pnl": 0.0, "total_pnl": symbol_realized_pnl}
        
        # Calculate unrealized PNL using portfolio
        for asset in portfolio:
            base_asset = asset["asset"]
            symbol = f"{base_asset}USDT"
            if symbol not in self.valid_pairs:
                logging.warning(f"Skipping {symbol}: Not in valid trading pairs")
                continue
            
            quantity_held = asset["free"] + asset["locked"]
            if quantity_held <= 0:
                continue
            
            # Fetch all buy trades for this symbol (not just in time range) to calculate avg buy price
            all_trades = []
            try:
                with self.file_lock:
                    if os.path.exists(self.trade_history_file):
                        with open(self.trade_history_file, 'r') as f:
                            all_trades = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logging.error(f"Failed to read {self.trade_history_file}: {e}")
                continue
            
            buy_trades = [
                t for t in all_trades
                if t.get("symbol") == symbol and t.get("side") == "BUY" and isinstance(t, dict) and "quantity" in t and "price" in t and "commission" in t
            ]
            
            if not buy_trades:
                logging.warning(f"No buy trades found for {symbol}. Skipping unrealized PNL.")
                continue
            
            # Calculate average buy price and total commission
            total_quantity = 0.0
            total_cost = 0.0
            total_commission = 0.0
            for trade in buy_trades:
                qty = float(trade["quantity"])
                price = float(trade["price"])
                commission = float(trade["commission"])
                commission_asset = trade["commissionAsset"]
                
                commission_usdt = commission
                if commission_asset != "USDT" and commission > 0:
                    commission_price = self.view_current_price(f"{commission_asset}USDT")
                    if commission_price:
                        commission_usdt = commission * commission_price
                    else:
                        logging.warning(f"Could not convert commission {commission} {commission_asset} for {symbol}. Ignoring commission.")
                        commission_usdt = 0.0
                
                total_quantity += qty
                total_cost += qty * price
                total_commission += commission_usdt
            
            avg_buy_price = total_cost / total_quantity if total_quantity > 0 else 0.0
            
            # Fetch current market price
            current_price = self.view_current_price(symbol)
            if current_price is None:
                logging.warning(f"Could not fetch current price for {symbol}. Skipping unrealized PNL.")
                continue
            
            # Estimate sell commission
            estimated_sell_commission = quantity_held * current_price * self.brokerage_fee
            
            # Unrealized PNL = (current_price - avg_buy_price) * quantity_held - commissions
            symbol_unrealized_pnl = (current_price - avg_buy_price) * quantity_held - total_commission * (quantity_held / total_quantity) - estimated_sell_commission
            
            unrealized_pnl += symbol_unrealized_pnl
            open_positions[symbol] = {
                "quantity": quantity_held,
                "avg_buy_price": avg_buy_price,
                "current_price": current_price,
                "unrealized_pnl": symbol_unrealized_pnl
            }
            
            # Update symbol_pnl
            if symbol in symbol_pnl:
                symbol_pnl[symbol]["unrealized_pnl"] = symbol_unrealized_pnl
                symbol_pnl[symbol]["total_pnl"] = symbol_pnl[symbol]["realized_pnl"] + symbol_unrealized_pnl
            else:
                symbol_pnl[symbol] = {
                    "realized_pnl": 0.0,
                    "unrealized_pnl": symbol_unrealized_pnl,
                    "total_pnl": symbol_unrealized_pnl
                }
        
        total_pnl = realized_pnl + unrealized_pnl
        
        result = {
            "total_pnl": total_pnl,
            "realized_pnl": realized_pnl,
            "unrealized_pnl": unrealized_pnl,
            "symbol_pnl": symbol_pnl,
            "open_positions": open_positions
        }
        
        logging.info(f"PNL Summary: Total PNL = {total_pnl:.2f} USDT, Realized = {realized_pnl:.2f} USDT, Unrealized = {unrealized_pnl:.2f} USDT")
        return result

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
        quantity_precision, _, _ = self._get_symbol_precision(symbol)
        params = {
            "symbol": symbol,
            "side": side.upper(),
            "type": "MARKET",
            "newOrderRespType": "FULL"
        }
        if quantity:
            quantity = float(Decimal(str(quantity)).quantize(Decimal(f"0.{'0' * quantity_precision}"), rounding=ROUND_DOWN))
            params["quantity"] = quantity
        elif quote_order_qty:
            params["quoteOrderQty"] = float(Decimal(str(quote_order_qty)).quantize(Decimal("0.01"), rounding=ROUND_DOWN))
        else:
            raise ValueError("Either quantity or quoteOrderQty must be provided")
        response = self._make_request("POST", "/v3/order", params, signed=True)
        if response and "cummulativeQuoteQty" in response:
            order = {
                "symbol": response["symbol"],
                "orderId": response["orderId"],
                "side": response["side"],
                "type": response["type"],
                "executedQty": float(response["executedQty"]),
                "quoteQty": float(response["cummulativeQuoteQty"]),
                "status": response["status"],
                "time": response["transactTime"],
                "commission": float(response.get("fills", [{}])[0].get("commission", 0))
            }
            logging.info(f"Placed market order: {order}")
            trade_data = {
                "symbol": order["symbol"],
                "side": order["side"],
                "quantity": order["executedQty"],
                "price": order["quoteQty"] / order["executedQty"] if order["executedQty"] > 0 else 0.0,
                "quoteQty": order["quoteQty"],
                "commission": order["commission"],
                "commissionAsset": response.get("fills", [{}])[0].get("commissionAsset", "Unknown"),
                "time": order["time"],
                "tradeId": order["orderId"],
                "orderType": order["type"]
            }
            self._save_trade_to_json(trade_data)
            return order
        logging.error(f"Failed to place market order for {symbol}")
        return None

    def sell_asset_by_percentage(self, symbol, percentage=100):
        if not 0 < percentage <= 100:
            raise ValueError(f"Percentage must be between 0 and 100, got {percentage}")
        
        base_asset = symbol.split('/')[0]
        symbol = symbol.replace("/", "")
        
        if symbol not in self.valid_pairs:
            logging.error(f"Invalid trading pair: {symbol}")
            return None
        
        balances = self.view_account_balance()
        asset_balance = next((b["free"] for b in balances if b["asset"] == base_asset), 0)
        
        if asset_balance <= 0:
            logging.info(f"No {base_asset} available to sell")
            print(f"No {base_asset} available to sell")
            return None
        
        quantity = asset_balance * (percentage / 100)
        quantity_precision, _, min_notional = self._get_symbol_precision(symbol)

        logging.info(f"Sell calculation for {symbol}: asset_balance={asset_balance}, percentage={percentage}, raw_quantity={quantity}, precision={quantity_precision}")

        # Use ROUND_HALF_UP instead of ROUND_DOWN to avoid rounding to 0
        quantity = float(Decimal(str(quantity)).quantize(Decimal(f"0.{'0' * quantity_precision}"), rounding=ROUND_HALF_UP))

        logging.info(f"Rounded quantity: {quantity}")
        
        price = self.view_current_price(symbol)
        if price is None:
            logging.error(f"Failed to fetch price for {symbol}")
            return None
        
        notional = quantity * price
        if notional < min_notional:
            logging.warning(f"Skipping sell: Notional value {notional} USDT below minimum {min_notional} USDT")
            print(f"Cannot sell: Notional value {notional} USDT below minimum {min_notional} USDT")
            return None
        
        logging.info(f"Selling {percentage}% of {base_asset} ({quantity} {base_asset})")
        print(f"Selling {percentage}% of {base_asset} ({quantity} {base_asset})")
        order = self.place_market_order(symbol, 'SELL', quantity=quantity)
        return order

    def view_open_orders(self, symbol=None):
        params = {}
        if symbol:
            symbol = symbol.replace("/", "")
            if symbol not in self.valid_pairs:
                logging.error(f"Invalid trading pair: {symbol}")
                return []
            params["symbol"] = symbol
        response = self._make_request("GET", "/v3/openOrders", params, signed=True)
        if response:
            orders = [
                {
                    "symbol": o["symbol"],
                    "orderId": o["orderId"],
                    "side": o["side"],
                    "type": o["type"],
                    "quantity": float(o["origQty"]),
                    "price": float(o["price"]),
                    "status": o["status"],
                    "time": o["time"]
                }
                for o in response
            ]
            logging.info(f"Found {len(orders)} open orders")
            return orders
        logging.info("No open orders found")
        return []

    def sell_all_to_usdt(self):
        exclusion_file = 'excluded_currencies.json'
        with self.file_lock:
            if os.path.exists(exclusion_file):
                try:
                    with open(exclusion_file, 'r') as f:
                        excluded_currencies = json.load(f)
                except Exception as e:
                    logging.error(f"Failed to load exclusion list: {e}")
                    excluded_currencies = []
            else:
                excluded_currencies = []
                with open(exclusion_file, 'w') as f:
                    json.dump(excluded_currencies, f, indent=2)
        
        balances = self.view_account_balance()
        usdt_balance = next((b["free"] for b in balances if b["asset"] == "USDT"), 0)
        for balance in balances:
            asset = balance["asset"]
            if asset != "USDT" and balance["free"] > 0:
                if asset in excluded_currencies:
                    logging.info(f"Skipping {asset}: In exclusion list")
                    continue
                symbol = f"{asset}USDT"
                if symbol in self.valid_pairs:
                    quantity_precision, _, min_notional = self._get_symbol_precision(symbol)
                    quantity = float(Decimal(str(balance["free"])).quantize(Decimal(f"0.{'0' * quantity_precision}"), rounding=ROUND_DOWN))
                    price = self.view_current_price(symbol)
                    if price is None:
                        logging.warning(f"Skipping {asset}: Failed to fetch price")
                        try:
                            with self.file_lock:
                                if asset not in excluded_currencies:
                                    excluded_currencies.append(asset)
                                    with open(exclusion_file, 'w') as f:
                                        json.dump(excluded_currencies, f, indent=2)
                                    logging.info(f"Added {asset} to exclusion list: No price available")
                        except Exception as e:
                            logging.error(f"Failed to update exclusion list for {asset}: {e}")
                        continue
                    notional = quantity * price
                    if notional < min_notional:
                        logging.warning(f"Skipping {asset}: Notional value {notional} USDT below minimum {min_notional} USDT")
                        try:
                            with self.file_lock:
                                if asset not in excluded_currencies:
                                    excluded_currencies.append(asset)
                                    with open(exclusion_file, 'w') as f:
                                        json.dump(excluded_currencies, f, indent=2)
                                    logging.info(f"Added {asset} to exclusion list: Below min_notional")
                        except Exception as e:
                            logging.error(f"Failed to update exclusion list for {asset}: {e}")
                        continue
                    params = {
                        "symbol": symbol,
                        "side": "SELL",
                        "type": "MARKET",
                        "quantity": quantity,
                        "newOrderRespType": "FULL"
                    }
                    try:
                        response = self._make_request("POST", "/v3/order", params, signed=True)
                        if response and "cummulativeQuoteQty" in response:
                            value = float(response["cummulativeQuoteQty"])
                            usdt_balance += value
                            logging.info(f"Sold {quantity} {asset} for {value} USDT")
                            trade_data = {
                                "symbol": response["symbol"],
                                "side": "SELL",
                                "quantity": float(response["executedQty"]),
                                "price": value / float(response["executedQty"]) if float(response["executedQty"]) > 0 else 0.0,
                                "quoteQty": value,
                                "commission": float(response.get("fills", [{}])[0].get("commission", 0)),
                                "commissionAsset": response.get("fills", [{}])[0].get("commissionAsset", "Unknown"),
                                "time": response["transactTime"],
                                "tradeId": response["orderId"],
                                "orderType": "MARKET"
                            }
                            self._save_trade_to_json(trade_data)
                        else:
                            logging.error(f"Failed to sell {asset}: {response}")
                            try:
                                with self.file_lock:
                                    if asset not in excluded_currencies:
                                        excluded_currencies.append(asset)
                                        with open(exclusion_file, 'w') as f:
                                            json.dump(excluded_currencies, f, indent=2)
                                        logging.info(f"Added {asset} to exclusion list: Sell failed")
                            except Exception as e:
                                logging.error(f"Failed to update exclusion list for {asset}: {e}")
                    except TradingAPIError as e:
                        logging.error(f"Failed to sell {asset}: {e}")
                        try:
                            with self.file_lock:
                                if asset not in excluded_currencies:
                                    excluded_currencies.append(asset)
                                    with open(exclusion_file, 'w') as f:
                                        json.dump(excluded_currencies, f, indent=2)
                                    logging.info(f"Added {asset} to exclusion list: API error")
                        except Exception as e:
                            logging.error(f"Failed to update exclusion list for {asset}: {e}")
                else:
                    logging.warning(f"Skipping {asset}: {symbol} not in valid trading pairs")
                    try:
                        with self.file_lock:
                            if asset not in excluded_currencies:
                                excluded_currencies.append(asset)
                                with open(exclusion_file, 'w') as f:
                                    json.dump(excluded_currencies, f, indent=2)
                                logging.info(f"Added {asset} to exclusion list: Invalid trading pair")
                    except Exception as e:
                        logging.error(f"Failed to update exclusion list for {asset}: {e}")
        final_balance = self.view_account_balance()
        usdt_final = next((b["free"] for b in final_balance if b["asset"] == "USDT"), usdt_balance)
        logging.info(f"Total USDT after selling: {usdt_final}")
        return usdt_final

if __name__ == "__main__":
    PAPER_CONFIG = {
        'api_key': os.getenv('TRADING_API_KEY', '05XHmPsHJxQ4rkilyW4NLFYVw0rKZ9sqnn7hKTrbwfYB3WLvh37TME1ZkLaj9uZ7'),
        'api_secret': os.getenv('TRADING_API_SECRET'),
        'testnet': True,
        'brokerage_fee': 0.001,
        'recv_window': 10000,
        'symbols': ['BTC/USDT', 'ETH/USDT']
    }
    try:
        with PaperTradingClient(PAPER_CONFIG) as client:
            # print("Account Balances:", client.view_account_balance())
            # print("Currency Pairs:", client.valid_pairs[:5])
            # symbol = PAPER_CONFIG['symbols'][0]
            # print(f"{symbol} Price:", client.view_current_price(symbol))
            # print("Fulfilled Orders:", client.view_all_fulfilled_orders())
            # print("Open Orders:", client.view_open_orders())
            # limit_order = client.place_limit_order(symbol, 'BUY', 0.01, 100000)
            # print("Limit Order:", limit_order)
            # print("USDT Balance After Selling All:", client.sell_all_to_usdt())


            # Buying and selling in percentages
            #################################
            print("Initial USDT Balance:", client.view_usdt_balance())
            print("Initial Portfolio:", client.view_portfolio())
            
            # Buy 1000 USDT worth of ETH
            buy_order = client.place_market_order('ETH/USDT', 'BUY', quote_order_qty=1000)
            print("Buy Market Order:", buy_order)
            print("USDT Balance After Buy:", client.view_usdt_balance())
            print("Portfolio After Buy:", client.view_portfolio())
            
            # Sell 50% of ETH
            sell_order_50 = client.sell_asset_by_percentage('ETH/USDT', percentage=50)
            print("Sell 50% Market Order:", sell_order_50)
            print("USDT Balance After Selling 50%:", client.view_usdt_balance())
            print("Portfolio After Selling 50%:", client.view_portfolio())
            
            # Sell 100% of remaining ETH
            sell_order_100 = client.sell_asset_by_percentage('ETH/USDT')
            print("Sell 100% Market Order:", sell_order_100)
            print("USDT Balance After Selling 100%:", client.view_usdt_balance())
            print("Portfolio After Selling 100%:", client.view_portfolio())
            
            # Example: Fetch trades in time range
            # trades = client.get_trades_in_time_range(
            #     "2025-05-25 12:00:00",
            #     "2025-05-25 14:18:00"
            # )
            # print("Trades in Time Range:", json.dumps(trades, indent=2))
            
            # Calculate PNL
            pnl = client.calculate_pnl_in_time_range(
                "2025-05-25 12:00:00",
                "2025-05-25 14:18:00"
            )
            print("PNL Report:", json.dumps(pnl, indent=2))
    except Exception as e:
        logging.error(f"Script execution failed: {e}")