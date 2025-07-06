from datetime import datetime
from typing import Optional

from models.market_data import MarketData

# from pydantic import BaseModel  # type: ignore


class CryptoAsset(MarketData):
    id: str
    name: str
    symbol: str
    balance: float
    usd_price: float
    usd_value: float
    is_staked: bool
    apy: Optional[float] = None
    estimated_annual_yield_usd: Optional[float] = 0

    # custom field
    last_updated: Optional[datetime] = None
