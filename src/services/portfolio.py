from typing import List

from fetchers.coinbase import CoinbaseRequestHandler
from models.portfolio import CoinbasePortfolioAsset


async def get_portfolio() -> List[CoinbasePortfolioAsset]:
    handler = CoinbaseRequestHandler()
    return await handler.get_holdings()
