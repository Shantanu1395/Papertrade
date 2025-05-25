from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union
from datetime import datetime

class Balance(BaseModel):
    asset: str
    free: float = Field(..., description="Free balance")
    locked: float = Field(..., description="Locked balance")

    class Config:
        json_encoders = {
            float: lambda v: round(v, 2)
        }

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
    balance: float = Field(..., description="USDT balance rounded to 2 decimal places")

    class Config:
        json_encoders = {
            float: lambda v: round(v, 2)
        }

class SellAllResponse(BaseModel):
    usdt_balance: float = Field(..., description="Final USDT balance after selling all assets")

    class Config:
        json_encoders = {
            float: lambda v: round(v, 2)
        }

# Add more models as needed for specific responses