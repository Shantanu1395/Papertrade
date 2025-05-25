import requests
import logging
import time
import hashlib
import hmac
from urllib.parse import urlencode
import os
from decimal import Decimal, ROUND_DOWN
from dotenv import load_dotenv
import json
import threading

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
                            price_precision = len(tick_size.split('.')[1]) if '.' in tick_size else 0
                        if f["filterType"] == "LOT_SIZE":
                            step_size = f["stepSize"]
                            quantity_precision = len(step_size.split('.')[1]) if '.' in step_size else 0
                        if f["filterType"] == "MIN_NOTIONAL":
                            min_notional = float(f["minNotional"])
                    return quantity_precision, price_precision, min_notional
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
            for b in response.get("balances", [])
            if float(b["free"]) > 0 or float(b["locked"]) > 0
        ]
        logging.info(f"Account balances: {balances}")
        print(json.dumps(balances, indent=2))
        return balances

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
                    required_keys = ['symbol', 'side', 'price', 'qty', 'quoteQty', 'commission', 'commissionAsset', 'time', 'id']
                    if not all(key in t for key in required_keys):
                        logging.warning(f"Skipping invalid trade for {symbol}: {t}")
                        continue
                    try:
                        trade = {
                            "symbol": t["symbol"],
                            "side": t["side"],
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
                logging.info(f"Fetched {len(trades)} trades for {symbol}")
            except TradingAPIError as e:
                logging.error(f"API error for {symbol}: {e}")
                continue
        logging.info(f"Total fulfilled orders: {len(all_trades)}")
        return sorted(all_trades, key=lambda x: x["time"])

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
            return order
        logging.error(f"Failed to place limit order for {symbol}")
        return None

    def place_market_order(self, symbol, side, quantity=None, quote_order_qty=None):
        self._validate_order_params(symbol, side, quantity=quantity, quote_order_qty=quote_order_qty)
        symbol = symbol.replace("/", "")
        quantity_precision, _ = self._get_symbol_precision(symbol)
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
            return order
        logging.error(f"Failed to place market order for {symbol}")
        return None

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
        file_lock = threading.Lock()
        try:
            with file_lock:
                if os.path.exists(exclusion_file):
                    with open(exclusion_file, 'r') as f:
                        excluded_currencies = json.load(f)
                else:
                    excluded_currencies = []
                    with open(exclusion_file, 'w') as f:
                        json.dump(excluded_currencies, f, indent=2)
        except Exception as e:
            logging.error(f"Failed to load exclusion list: {e}")
            excluded_currencies = []
        
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
                        continue
                    notional = quantity * price
                    if notional < min_notional:
                        logging.warning(f"Skipping {asset}: Notional value {notional} USDT below minimum {min_notional} USDT")
                        try:
                            with file_lock:
                                if asset not in excluded_currencies:
                                    excluded_currencies.append(asset)
                                    with open(exclusion_file, 'w') as f:
                                        json.dump(excluded_currencies, f, indent=2)
                                    logging.info(f"Added {asset} to exclusion list")
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
                        else:
                            logging.error(f"Failed to sell {asset}: {response}")
                    except TradingAPIError as e:
                        logging.error(f"Failed to sell {asset}: {e}")
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
            # market_order = client.place_market_order('ETH/USDT', 'BUY', quote_order_qty=1000)
            # print("Market Order:", market_order)
            # print("USDT Balance After Selling All:", client.sell_all_to_usdt())
            print("Account Balances:", client.view_account_balance())
    except Exception as e:
        logging.error(f"Script execution failed: {e}")