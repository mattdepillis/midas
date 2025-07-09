from typing import Dict, List, Optional

from deps.caches import get_fiat_rate_cache, get_market_data_cache
from fetchers.coinbase import CoinbaseRequestHandler
from fetchers.coingecko import MarketDataCache
from fetchers.frankfurter import FiatRateCache
from models.portfolio_assets import CryptoAsset, FiatAsset


async def get_portfolio() -> List[CryptoAsset]:
    """
    Fetches the user's portfolio from Coinbase and enriches each asset
    with real-time metadata from CoinGecko or fiat exchange rates.

    This serves as the main entry point to retrieve a unified view of all
    user holdings, including crypto and fiat assets.

    Returns:
        A list of enriched CryptoAsset and FiatAsset objects.
    """
    fiat_rate_cache = await get_fiat_rate_cache()
    market_data_cache = await get_market_data_cache()
    handler = CoinbaseRequestHandler()
    holdings = await handler.get_holdings()
    return await enrich_holdings(fiat_rate_cache, market_data_cache, holdings)


async def enrich_holdings(
    fiat_cache: FiatRateCache, market_cache: MarketDataCache, raw_assets: List[Dict]
) -> List[CryptoAsset | FiatAsset]:
    """
    Enriches raw Coinbase asset records with external metadata.

    This includes:
    - Enriching crypto assets with CoinGecko market data (price, % changes, etc.)
    - Enriching fiat assets with USD conversion rates

    Args:
        fiat_cache: A FiatRateCache instance used to convert fiat balances to USD.
        market_cache: A MarketDataCache instance used to resolve CoinGecko IDs and market data.
        raw_assets: A list of raw asset dictionaries returned by the Coinbase API.

    Returns:
        A list of enriched CryptoAsset and FiatAsset instances.
    """

    enriched_assets = []
    for asset in raw_assets:
        symbol = asset["symbol"].lower()
        cg_id = await resolve_cg_id(market_cache, symbol)

        # Handle fiat fallback
        if cg_id is None:
            fiat_asset = enrich_fiat_asset(asset, fiat_cache)
            if fiat_asset:
                enriched_assets.append(fiat_asset)
            continue

        # Merge market metadata with Coinbase asset data
        asset_md = market_cache.id_to_market_data[cg_id]
        asset_md_dict = asset_md.dict()
        merged = dict(asset)  # start with coinbase asset

        # Clean up keys from asset_md and merge
        for k, v in asset_md_dict.items():
            cleaned_key = (
                k.replace("_in_currency", "") if k.endswith("_in_currency") else k
            )
            if cleaned_key not in merged:  # avoid overwriting fields like "id"
                merged[cleaned_key] = v

        try:
            enriched_assets.append(CryptoAsset(**merged))
        except Exception as e:
            print(f"Failed to parse CryptoAsset for {symbol}: {e}")

    return enriched_assets


async def resolve_cg_id(cache: MarketDataCache, symbol: str) -> Optional[str]:
    """
    Resolves the CoinGecko ID for a given asset symbol, using both the top-N cache
    and a fallback API call for less common or newly listed assets.

    Args:
        cache: The MarketDataCache instance with top asset mappings and fallback support.
        symbol: The asset symbol to resolve (e.g., 'sol', 'doge').

    Returns:
        The corresponding CoinGecko ID if found, or None if resolution fails.
    """
    cg_id = cache.get_id_from_symbol(symbol)
    if cg_id is not None:
        return cg_id

    print(
        f"Asset with symbol '{symbol}' not in the top {cache.page_limit * cache.num_pages} assets. Trying fallback lookup."
    )
    fallback_id = await cache.get_asset_fallback(symbol)
    if not fallback_id:
        print(f"No fallback CoinGecko ID found for symbol: {symbol}")
        return None

    return fallback_id


def enrich_fiat_asset(asset: dict, fiat_cache: FiatRateCache) -> Optional[FiatAsset]:
    """
    Converts a fiat currency balance from Coinbase into a FiatAsset object
    by applying the cached USD conversion rate.

    Args:
        asset: A single raw Coinbase asset dictionary (must be fiat).
        fiat_cache: The FiatRateCache instance for USD conversion rates.

    Returns:
        A FiatAsset object enriched with USD value, or None if the rate is missing.
    """
    symbol = asset["symbol"].lower()
    rate = fiat_cache.get_rate(symbol)
    if rate is None:
        print(f"No USD conversion rate for {symbol}. Skipping.")
        return None

    balance = asset.get("balance", 0.0)
    return FiatAsset(
        id=asset.get("id"),
        symbol=symbol,
        name=asset.get("name", symbol.upper()),
        balance=balance,
        usd_value=balance * rate,
    )
