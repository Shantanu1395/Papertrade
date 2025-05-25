from fastapi import APIRouter, HTTPException, Depends
from typing import List

from app.services.trading_client import PaperTradingClient, TradingAPIError
from app.models.schemas import Balance, USDTBalanceResponse
from app.dependencies import get_trading_client

router = APIRouter(
    prefix="/account",
    tags=["Account"],
    responses={404: {"description": "Not found"}},
)

@router.get("/balance", response_model=List[Balance])
async def get_account_balance(client: PaperTradingClient = Depends(get_trading_client)):
    try:
        return client.view_account_balance()
    except TradingAPIError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/usdt-balance", response_model=float)
async def get_usdt_balance(client: PaperTradingClient = Depends(get_trading_client)):
    return client.view_usdt_balance()

@router.get("/portfolio", response_model=List[Balance])
async def get_portfolio(client: PaperTradingClient = Depends(get_trading_client)):
    return client.view_portfolio()