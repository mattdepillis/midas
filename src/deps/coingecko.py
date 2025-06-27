from fetchers.coingecko import CoinGeckoFetcher, SymbolCache

_symbol_cache: SymbolCache | None = None
_coingecko: CoinGeckoFetcher | None = None


async def get_symbol_cache() -> SymbolCache:
    """."""
    global _symbol_cache
    if _symbol_cache is None:
        _symbol_cache = SymbolCache()
        await _symbol_cache.initialize()
    return _symbol_cache


async def get_coingecko_fetcher() -> CoinGeckoFetcher:
    """."""
    global _coingecko
    if _coingecko is None:
        _coingecko = CoinGeckoFetcher()
    return _coingecko
