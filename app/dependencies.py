import os
from dotenv import load_dotenv
from app.services.trading_client import PaperTradingClient

# Load environment variables
load_dotenv()

# Configuration for the trading client
PAPER_CONFIG = {
    'api_key': os.getenv('TRADING_API_KEY', '05XHmPsHJxQ4rkilyW4NLFYVw0rKZ9sqnn7hKTrbwfYB3WLvh37TME1ZkLaj9uZ7'),
    'api_secret': os.getenv('TRADING_API_SECRET'),
    'testnet': True,
    'brokerage_fee': 0.001,
    'recv_window': 10000,
    'symbols': ['BTC/USDT', 'ETH/USDT']
}

# Dependency to get the trading client
def get_trading_client():
    client = PaperTradingClient(PAPER_CONFIG)
    try:
        yield client
    finally:
        client.session.close()