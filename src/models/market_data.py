from datetime import datetime
from typing import Optional

from pydantic import BaseModel, HttpUrl  # type: ignore


class MarketData(BaseModel):
    id: Optional[str]
    symbol: Optional[str]
    name: Optional[str]
    image: Optional[HttpUrl]
    current_price: Optional[float]
    market_cap: Optional[float]
    market_cap_rank: Optional[int]
    fully_diluted_valuation: Optional[float]
    total_volume: Optional[float]
    high_24h: Optional[float]
    low_24h: Optional[float]
    price_change_24h: Optional[float]
    price_change_percentage_24h: Optional[float]
    market_cap_change_24h: Optional[float]
    market_cap_change_percentage_24h: Optional[float]
    circulating_supply: Optional[float]
    total_supply: Optional[float]
    max_supply: Optional[float]
    ath: Optional[float]
    ath_change_percentage: Optional[float]
    ath_date: Optional[datetime]
    atl: Optional[float]
    atl_change_percentage: Optional[float]
    atl_date: Optional[datetime]
    last_updated: Optional[datetime]

    # Change keys that end in `_in_currency` to cleaner names
    price_change_percentage_7d: Optional[float]
    price_change_percentage_14d: Optional[float]
    price_change_percentage_30d: Optional[float]
    price_change_percentage_200d: Optional[float]
    price_change_percentage_1y: Optional[float]
