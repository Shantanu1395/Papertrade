from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any

from app.services.trading_client import PaperTradingClient, TradingAPIError
from app.models.schemas import TimeRangeRequest
from app.dependencies import get_trading_client

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
    try:
        return client.get_trades_in_time_range(time_range.start_time, time_range.end_time)
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