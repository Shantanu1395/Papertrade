from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any

from app.services.trading_client import PaperTradingClient, TradingAPIError
from app.models.schemas import OrderRequest, PercentageSellRequest, OrderResponse, SellAllResponse
from app.dependencies import get_trading_client

router = APIRouter(
    prefix="/orders",
    tags=["Orders"],
    responses={404: {"description": "Not found"}},
)

@router.get("/fulfilled")
async def get_fulfilled_orders(client: PaperTradingClient = Depends(get_trading_client)):
    return client.view_all_fulfilled_orders()

@router.get("/open")
async def get_open_orders(
    symbol: Optional[str] = None, 
    client: PaperTradingClient = Depends(get_trading_client)
):
    return client.view_open_orders(symbol)

@router.post("/limit")
async def create_limit_order(
    order: OrderRequest, 
    client: PaperTradingClient = Depends(get_trading_client)
):
    try:
        result = client.place_limit_order(order.symbol, order.side, order.quantity, order.price)
        if result is None:
            raise HTTPException(status_code=400, detail="Failed to place limit order")
        return result
    except TradingAPIError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/market")
async def create_market_order(
    order: OrderRequest, 
    client: PaperTradingClient = Depends(get_trading_client)
):
    try:
        result = client.place_market_order(order.symbol, order.side, order.quantity, order.quote_order_qty)
        if result is None:
            raise HTTPException(status_code=400, detail="Failed to place market order")
        return result
    except TradingAPIError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/sell-percentage")
async def sell_by_percentage(
    request: PercentageSellRequest, 
    client: PaperTradingClient = Depends(get_trading_client)
):
    try:
        result = client.sell_asset_by_percentage(request.symbol, request.percentage)
        if result is None:
            raise HTTPException(status_code=400, detail="Failed to sell asset")
        return result
    except TradingAPIError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/sell-all-to-usdt", response_model=SellAllResponse)
async def sell_all_to_usdt(client: PaperTradingClient = Depends(get_trading_client)):
    try:
        return {"usdt_balance": client.sell_all_to_usdt()}
    except TradingAPIError as e:
        raise HTTPException(status_code=400, detail=str(e))