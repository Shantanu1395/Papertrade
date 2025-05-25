from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union
from datetime import datetime

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

class OrderResponse(BaseModel):
    symbol: str
    orderId: int
    side: str
    type: str
    quantity: float
    price: float
    status: str
    time: int
    commission: float

class PriceResponse(BaseModel):
    symbol: str
    price: float

class USDTBalanceResponse(BaseModel):
    balance: float

class SellAllResponse(BaseModel):
    usdt_balance: float

# Add more models as needed for specific responses