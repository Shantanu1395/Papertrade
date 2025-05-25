from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
from datetime import datetime

from app.services.trading_client import PaperTradingClient, TradingAPIError
from app.models.schemas import TimeRangeRequest
from app.dependencies import get_trading_client
from app.core import format_timestamp

router = APIRouter(
    prefix="/trades",
    tags=["Trades"],
    responses={404: {"description": "Not found"}},
)

@router.post("/time-range")
async def get_trades_in_time_range(
    time_range: TimeRangeRequest,
    client: PaperTradingClient = Depends(get_trading_client)
):
    """Get trades in time range with formatted timestamps."""
    try:
        trades = client.get_trades_in_time_range(time_range.start_time, time_range.end_time)

        # Format timestamps to readable format
        formatted_trades = []
        for trade in trades:
            formatted_trade = trade.copy()
            # Convert millisecond timestamp to readable format
            formatted_trade["time"] = format_timestamp(trade["time"])
            # Keep original timestamp as well for reference
            formatted_trade["timestamp_ms"] = trade["time"]
            formatted_trades.append(formatted_trade)

        return formatted_trades
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/history")
async def get_trade_history(client: PaperTradingClient = Depends(get_trading_client)):
    """Get all trade history with formatted timestamps."""
    try:
        trades = client.view_all_fulfilled_orders()

        # Format timestamps to readable format
        formatted_trades = []
        for trade in trades:
            formatted_trade = trade.copy()
            # Convert millisecond timestamp to readable format
            formatted_trade["time"] = format_timestamp(trade["time"])
            # Keep original timestamp as well for reference
            formatted_trade["timestamp_ms"] = trade["time"]
            formatted_trades.append(formatted_trade)

        return formatted_trades
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/pnl/calculate")
async def calculate_pnl(
    time_range: TimeRangeRequest,
    client: PaperTradingClient = Depends(get_trading_client)
):
    try:
        return client.calculate_pnl_in_time_range(time_range.start_time, time_range.end_time)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))