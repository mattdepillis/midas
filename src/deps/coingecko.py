from fetchers.coingecko import CoinGeckoFetcher, SymbolCache

_symbol_cache: SymbolCache | None = None
_coingecko: CoinGeckoFetcher | None = None


async def get_symbol_cache() -> SymbolCache:
    """
    Lazily initializes and returns a globally cached instance of the SymbolCache.
    Ensures the symbol-to-CoinGecko-ID mapping is loaded only once per runtime.

    Returns:
        An initialized SymbolCache instance.
    """
    global _symbol_cache
    if _symbol_cache is None:
        _symbol_cache = SymbolCache()
        await _symbol_cache.initialize()
    return _symbol_cache


async def get_coingecko_fetcher() -> CoinGeckoFetcher:
    """
    Lazily initializes and returns a globally cached instance of the CoinGeckoFetcher.
    Ensures consistent use of the API client throughout the application.

    Returns:
        A CoinGeckoFetcher instance.
    """
    global _coingecko
    if _coingecko is None:
        _coingecko = CoinGeckoFetcher()
    return _coingecko
