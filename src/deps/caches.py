from fetchers.coingecko import MarketDataCache
from fetchers.frankfurter import FiatRateCache

_fiat_rate_cache: FiatRateCache | None = None
_market_data_cache: MarketDataCache | None = None


async def get_fiat_rate_cache() -> FiatRateCache:
    """
    Lazily initializes and returns a globally cached instance of the FiatRateCache.

    This ensures that fiat-to-USD exchange rates are loaded only once per runtime,
    and automatically refreshed if the cache has expired (based on TTL).

    Returns:
        An initialized FiatRateCache instance with up-to-date exchange rates.
    """
    global _fiat_rate_cache
    if _fiat_rate_cache is None:
        _fiat_rate_cache = FiatRateCache()
        await _fiat_rate_cache.initialize()
    else:
        await _fiat_rate_cache.maybe_refresh()
    return _fiat_rate_cache


async def get_market_data_cache() -> MarketDataCache:
    """
    Lazily initializes and returns a globally cached instance of the MarketDataCache.

    Ensures that CoinGecko market data (symbol-to-ID mapping and top-N asset metadata)
    is loaded only once per runtime, with optional TTL-based refresh.

    Returns:
        An initialized MarketDataCache instance with enriched CoinGecko data.
    """
    global _market_data_cache
    if _market_data_cache is None:
        _market_data_cache = MarketDataCache()
        await _market_data_cache.initialize()
    else:
        await _market_data_cache.maybe_refresh()
    return _market_data_cache
