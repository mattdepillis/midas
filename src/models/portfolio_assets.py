from datetime import datetime
from typing import Optional

from pydantic import BaseModel  # type: ignore

from models.market_data import MarketData


class CryptoAsset(MarketData):
    """
    Represents a cryptocurrency holding, enriched with both portfolio-specific
    data (balance, staking info) and market metadata (via MarketData).

    Inherits:
        MarketData: Includes price change percentages, volume, market cap, etc.

    Attributes:
        id (str): CoinGecko asset ID (e.g., 'ethereum').
        name (str): Full name of the asset (e.g., 'Ethereum').
        symbol (str): Lowercase asset symbol (e.g., 'eth').
        balance (float): Amount of this asset held in the user's wallet.
        usd_price (float): Current price of the asset in USD.
        usd_value (float): Current USD-equivalent value of the holding (balance * price).
        is_staked (bool): Indicates whether the asset is currently staked.
        apy (Optional[float]): Annual percentage yield (if staked).
        estimated_annual_yield_usd (Optional[float]): Estimated USD earned in a year from staking.
        last_updated (Optional[datetime]): When the asset data was last updated.
    """

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


class FiatAsset(BaseModel):
    """
    Represents a fiat currency balance held in the user's account,
    enriched with its equivalent USD value.

    Attributes:
        id (str): Identifier for the asset (can be the same as symbol).
        symbol (str): Currency symbol (e.g., 'usd', 'eur').
        name (str): Full name of the currency (e.g., 'US Dollar').
        balance (float): Amount of fiat held.
        usd_value (float): Equivalent USD value of the fiat balance.
    """

    id: str
    symbol: str
    name: str
    balance: float
    usd_value: float
