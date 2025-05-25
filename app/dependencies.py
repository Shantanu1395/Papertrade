"""
Dependencies for the trading application.
"""
from app.services.trading_client import PaperTradingClient
from app.core import settings

def get_trading_client():
    """Get a configured trading client instance."""
    # The trading client will use global settings by default
    client = PaperTradingClient()
    try:
        yield client
    finally:
        client.session.close()