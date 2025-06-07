"""
Dependencies for the trading application.
"""
from fastapi import Header, HTTPException
from typing import Optional
from app.services.trading_client import PaperTradingClient
from app.core import settings

def get_trading_client(
    x_api_key: Optional[str] = Header(None),
    x_api_secret: Optional[str] = Header(None)
):
    """Get a configured trading client instance."""
    # Use headers if provided, otherwise fall back to global settings
    api_key = x_api_key or settings.binance_api_key
    api_secret = x_api_secret or settings.binance_api_secret

    if not api_key or not api_secret:
        raise HTTPException(
            status_code=401,
            detail="API credentials required. Please provide X-API-KEY and X-API-SECRET headers."
        )

    client = PaperTradingClient(config={
        'api_key': api_key,
        'api_secret': api_secret
    })
    try:
        yield client
    finally:
        client.session.close()