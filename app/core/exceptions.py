"""
Custom exceptions for the trading application.
"""


class TradingAPIError(Exception):
    """Base exception for trading API errors."""
    pass


class InsufficientBalanceError(TradingAPIError):
    """Raised when there's insufficient balance for a trade."""
    pass


class InvalidSymbolError(TradingAPIError):
    """Raised when an invalid trading symbol is provided."""
    pass


class OrderValidationError(TradingAPIError):
    """Raised when order parameters are invalid."""
    pass


class PriceNotAvailableError(TradingAPIError):
    """Raised when price information is not available."""
    pass


class ConfigurationError(Exception):
    """Raised when there's a configuration error."""
    pass
