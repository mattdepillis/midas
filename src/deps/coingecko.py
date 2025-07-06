from fetchers.coingecko import MarketDataCache

_market_data_cache: MarketDataCache | None = None
# _coingecko: CoinGeckoFetcher | None = None


async def get_market_data_cache() -> MarketDataCache:
    """
    Lazily initializes and returns a globally cached instance of the SymbolCache.
    Ensures the symbol-to-CoinGecko-ID mapping is loaded only once per runtime.

    Returns:
        An initialized SymbolCache instance.
    """
    global _market_data_cache
    if _market_data_cache is None:
        _market_data_cache = MarketDataCache()
        await _market_data_cache.initialize()
    else:
        await _market_data_cache.maybe_refresh()
    return _market_data_cache


# async def get_coingecko_fetcher() -> CoinGeckoFetcher:
#     """
#     Lazily initializes and returns a globally cached instance of the CoinGeckoFetcher.
#     Ensures consistent use of the API client throughout the application.

#     Returns:
#         A CoinGeckoFetcher instance.
#     """
#     global _coingecko
#     if _coingecko is None:
#         _coingecko = CoinGeckoFetcher()
#     return _coingecko
