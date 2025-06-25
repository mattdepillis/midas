from typing import List

from fetchers.coinbase import CoinbaseRequestHandler
from fetchers.coingecko import SymbolCache
from models.portfolio import CryptoAsset


async def get_portfolio() -> List[CryptoAsset]:
    handler = CoinbaseRequestHandler()

    ##### TESTING CODE
    cache = SymbolCache()
    await cache.initialize()
    print(cache.symbol_to_id)
    print("\n")
    print(cache.get_id("btc"), cache.get_id("eth"))
    ##### TESTING CODE

    return await handler.get_holdings()
