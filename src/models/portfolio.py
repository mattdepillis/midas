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
    price_change_24h: Optional[float] = None  # % change
    price_change_percentage_24h: Optional[float] = None
    price_change_7d: Optional[float] = None  # % change
    price_change_percentage_7d_in_currency: Optional[float] = None
    price_change_percentage_7d_in_currency: Optional[float] = None
    market_cap: Optional[int] = 0
    image: Optional[str] = None
    last_updated: Optional[str] = None
