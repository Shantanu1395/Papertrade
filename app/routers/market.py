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

@router.get("/symbol-info/{symbol}")
async def get_symbol_info(
    symbol: str = Path(..., description="Trading pair symbol (e.g., BTC/USDT)"),
    client: PaperTradingClient = Depends(get_trading_client)
):
    """Get symbol information including minimum order requirements."""
    try:
        symbol = symbol.replace("/", "")
        response = client._make_request("GET", "/v3/exchangeInfo")

        for s in response.get("symbols", []):
            if s["symbol"] == symbol:
                symbol_info = {
                    "symbol": symbol,
                    "status": s.get("status"),
                    "baseAsset": s.get("baseAsset"),
                    "quoteAsset": s.get("quoteAsset"),
                    "minQty": None,
                    "maxQty": None,
                    "stepSize": None,
                    "minPrice": None,
                    "maxPrice": None,
                    "tickSize": None,
                    "minNotional": 10.0,
                    "maxNotional": None
                }

                for f in s.get("filters", []):
                    if f["filterType"] == "LOT_SIZE":
                        symbol_info["minQty"] = float(f["minQty"])
                        symbol_info["maxQty"] = float(f["maxQty"])
                        symbol_info["stepSize"] = float(f["stepSize"])
                    elif f["filterType"] == "PRICE_FILTER":
                        symbol_info["minPrice"] = float(f["minPrice"])
                        symbol_info["maxPrice"] = float(f["maxPrice"])
                        symbol_info["tickSize"] = float(f["tickSize"])
                    elif f["filterType"] == "MIN_NOTIONAL":
                        symbol_info["minNotional"] = float(f["minNotional"])
                    elif f["filterType"] == "NOTIONAL":
                        symbol_info["minNotional"] = float(f["minNotional"])
                        symbol_info["maxNotional"] = float(f.get("maxNotional", 0))

                return symbol_info

        raise HTTPException(status_code=404, detail=f"Symbol {symbol} not found")
    except TradingAPIError as e:
        raise HTTPException(status_code=400, detail=str(e))