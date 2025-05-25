from fastapi import APIRouter, HTTPException, Depends, Path
from typing import List

from app.services.trading_client import PaperTradingClient, TradingAPIError
from app.models.schemas import PriceResponse
from app.dependencies import get_trading_client

router = APIRouter(
    prefix="/market",
    tags=["Market"],
    responses={404: {"description": "Not found"}},
)

@router.get("/pairs", response_model=List[str])
async def get_currency_pairs(client: PaperTradingClient = Depends(get_trading_client)):
    return client.view_all_currency_pairs()

@router.get("/price/{symbol}", response_model=PriceResponse)
async def get_current_price(
    symbol: str = Path(..., description="Trading pair symbol (e.g., BTC/USDT)"),
    client: PaperTradingClient = Depends(get_trading_client)
):
    try:
        price = client.view_current_price(symbol)
        return {"symbol": symbol, "price": price}
    except TradingAPIError as e:
        raise HTTPException(status_code=400, detail=str(e))