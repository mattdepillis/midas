from typing import Optional

from pydantic import BaseModel  # type: ignore


class CryptoAsset(BaseModel):
    id: str
    name: str
    symbol: str
    balance: float
    usd_price: float
    usd_value: float
    is_staked: bool
    apy: Optional[float] = None
    estimated_annual_yield_usd: Optional[float] = 0
    # performance_24h: Optional[float] = None  # % change
    # performance_7d: Optional[float] = None   # % change
