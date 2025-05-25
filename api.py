from fastapi import FastAPI, HTTPException, Depends, Query, Path
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union
import os
from dotenv import load_dotenv
import logging
from datetime import datetime
import json
import uvicorn

# Import the PaperTradingClient from main.py
from main import PaperTradingClient, TradingAPIError

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Create FastAPI app
app = FastAPI(
    title="Paper Trading API",
    description="API for paper trading on cryptocurrency exchanges",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration for the trading client
PAPER_CONFIG = {
    'api_key': os.getenv('TRADING_API_KEY', '05XHmPsHJxQ4rkilyW4NLFYVw0rKZ9sqnn7hKTrbwfYB3WLvh37TME1ZkLaj9uZ7'),
    'api_secret': os.getenv('TRADING_API_SECRET'),
    'testnet': True,
    'brokerage_fee': 0.001,
    'recv_window': 10000,
    'symbols': ['BTC/USDT', 'ETH/USDT']
}

# Dependency to get the trading client
def get_trading_client():
    client = PaperTradingClient(PAPER_CONFIG)
    try:
        yield client
    finally:
        client.session.close()

# Pydantic models for request and response
class Balance(BaseModel):
    asset: str
    free: float
    locked: float

class OrderRequest(BaseModel):
    symbol: str
    side: str
    quantity: Optional[float] = None
    price: Optional[float] = None
    quote_order_qty: Optional[float] = None

class PercentageSellRequest(BaseModel):
    symbol: str
    percentage: Optional[float] = 100

class TimeRangeRequest(BaseModel):
    start_time: str
    end_time: str

# API Routes
@app.get("/", tags=["Root"])
async def root():
    return {"message": "Welcome to the Paper Trading API"}

@app.get("/account/balance", response_model=List[Balance], tags=["Account"])
async def get_account_balance(client: PaperTradingClient = Depends(get_trading_client)):
    try:
        return client.view_account_balance()
    except TradingAPIError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/account/usdt-balance", response_model=float, tags=["Account"])
async def get_usdt_balance(client: PaperTradingClient = Depends(get_trading_client)):
    return client.view_usdt_balance()

@app.get("/portfolio", response_model=List[Balance], tags=["Account"])
async def get_portfolio(client: PaperTradingClient = Depends(get_trading_client)):
    return client.view_portfolio()

@app.get("/market/pairs", response_model=List[str], tags=["Market"])
async def get_currency_pairs(client: PaperTradingClient = Depends(get_trading_client)):
    return client.view_all_currency_pairs()

@app.get("/market/price/{symbol}", tags=["Market"])
async def get_current_price(symbol: str = Path(..., description="Trading pair symbol (e.g., BTC/USDT)"), 
                           client: PaperTradingClient = Depends(get_trading_client)):
    try:
        price = client.view_current_price(symbol)
        return {"symbol": symbol, "price": price}
    except TradingAPIError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/orders/fulfilled", tags=["Orders"])
async def get_fulfilled_orders(client: PaperTradingClient = Depends(get_trading_client)):
    return client.view_all_fulfilled_orders()

@app.get("/orders/open", tags=["Orders"])
async def get_open_orders(symbol: Optional[str] = None, client: PaperTradingClient = Depends(get_trading_client)):
    return client.view_open_orders(symbol)

@app.post("/orders/limit", tags=["Orders"])
async def create_limit_order(order: OrderRequest, client: PaperTradingClient = Depends(get_trading_client)):
    try:
        result = client.place_limit_order(order.symbol, order.side, order.quantity, order.price)
        if result is None:
            raise HTTPException(status_code=400, detail="Failed to place limit order")
        return result
    except TradingAPIError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/orders/market", tags=["Orders"])
async def create_market_order(order: OrderRequest, client: PaperTradingClient = Depends(get_trading_client)):
    try:
        result = client.place_market_order(order.symbol, order.side, order.quantity, order.quote_order_qty)
        if result is None:
            raise HTTPException(status_code=400, detail="Failed to place market order")
        return result
    except TradingAPIError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/orders/sell-percentage", tags=["Orders"])
async def sell_by_percentage(request: PercentageSellRequest, client: PaperTradingClient = Depends(get_trading_client)):
    try:
        result = client.sell_asset_by_percentage(request.symbol, request.percentage)
        if result is None:
            raise HTTPException(status_code=400, detail="Failed to sell asset")
        return result
    except TradingAPIError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/orders/sell-all-to-usdt", tags=["Orders"])
async def sell_all_to_usdt(client: PaperTradingClient = Depends(get_trading_client)):
    try:
        return {"usdt_balance": client.sell_all_to_usdt()}
    except TradingAPIError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/trades/time-range", tags=["Trades"])
async def get_trades_in_time_range(time_range: TimeRangeRequest, client: PaperTradingClient = Depends(get_trading_client)):
    try:
        return client.get_trades_in_time_range(time_range.start_time, time_range.end_time)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/pnl/calculate", tags=["PNL"])
async def calculate_pnl(time_range: TimeRangeRequest, client: PaperTradingClient = Depends(get_trading_client)):
    try:
        return client.calculate_pnl_in_time_range(time_range.start_time, time_range.end_time)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)