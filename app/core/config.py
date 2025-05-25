"""
Configuration settings for the trading application.
"""
import os
from typing import List, Optional

try:
    from pydantic_settings import BaseSettings
except ImportError:
    # Fallback for older pydantic versions
    from pydantic import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # API Configuration
    api_title: str = "Paper Trading API"
    api_description: str = "API for paper trading on cryptocurrency exchanges"
    api_version: str = "1.0.0"

    # Binance API Configuration
    binance_api_key: Optional[str] = None
    binance_api_secret: Optional[str] = None
    binance_testnet: bool = True
    binance_base_url: str = "https://testnet.binance.vision/api"
    binance_recv_window: int = 10000

    # Trading Configuration
    default_brokerage_fee: float = 0.001
    default_symbols: List[str] = ["BTCUSDT", "ETHUSDT"]

    # File Paths
    generated_dir: str = "generated"
    trade_history_file: str = "generated/trade_history.json"
    excluded_currencies_file: str = "generated/excluded_currencies.json"

    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = True

    # CORS Configuration
    cors_origins: List[str] = ["*"]
    cors_credentials: bool = True
    cors_methods: List[str] = ["*"]
    cors_headers: List[str] = ["*"]

    model_config = {
        "env_file": ".env",
        "env_prefix": "TRADING_",
        "case_sensitive": False,
        "extra": "ignore"  # Ignore extra environment variables
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Set API credentials from environment if not provided
        if not self.binance_api_key:
            self.binance_api_key = os.getenv('TRADING_API_KEY')
        if not self.binance_api_secret:
            self.binance_api_secret = os.getenv('TRADING_API_SECRET')

        # Ensure generated directory exists
        os.makedirs(self.generated_dir, exist_ok=True)


# Global settings instance
settings = Settings()
