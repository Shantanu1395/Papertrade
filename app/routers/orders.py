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
            # Get more detailed error information
            symbol = request.symbol.replace("/", "")
            portfolio = client.view_portfolio()
            asset_name = request.symbol.split("/")[0]
            asset_balance = next((asset for asset in portfolio if asset["asset"] == asset_name), None)

            if not asset_balance or asset_balance["free"] <= 0:
                raise HTTPException(
                    status_code=400,
                    detail=f"Insufficient {asset_name} balance. Available: {asset_balance['free'] if asset_balance else 0}"
                )

            # Check minimum notional value
            try:
                price = client.view_current_price(request.symbol)
                quantity = asset_balance["free"] * (request.percentage / 100)
                notional_value = quantity * price

                # Get symbol info for minimum notional
                response = client._make_request("GET", "/v3/exchangeInfo")
                min_notional = 10.0  # default
                for s in response.get("symbols", []):
                    if s["symbol"] == symbol:
                        for f in s.get("filters", []):
                            if f["filterType"] in ["MIN_NOTIONAL", "NOTIONAL"]:
                                min_notional = float(f["minNotional"])
                                break
                        break

                if notional_value < min_notional:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Order value too small. Minimum required: ${min_notional:.2f} USDT, but order value is ${notional_value:.2f} USDT. Try selling a higher percentage or wait for price increase."
                    )
            except Exception:
                pass

            raise HTTPException(status_code=400, detail="Failed to sell asset. Please check minimum order requirements.")
        return result
    except HTTPException:
        raise
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