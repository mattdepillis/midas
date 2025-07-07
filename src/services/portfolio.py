from typing import Dict, List, Optional

from deps.coingecko import get_market_data_cache
from fetchers.coinbase import CoinbaseRequestHandler
from fetchers.coingecko import MarketDataCache
from models.portfolio_assets import CryptoAsset


async def get_portfolio() -> List[CryptoAsset]:
    """
    Fetches the user's crypto holdings from Coinbase and enriches them with real-time
    market metadata from CoinGecko.

    Returns:
        A list of CryptoAsset objects with both Coinbase and CoinGecko data combined.
    """
    cache = await get_market_data_cache()
    handler = CoinbaseRequestHandler()
    holdings = await handler.get_holdings()
    return await enrich_holdings(cache, holdings)


async def enrich_holdings(
    cache: MarketDataCache, raw_assets: List[Dict]
) -> List[CryptoAsset]:
    """
    Enriches a list of raw Coinbase assets with additional market metadata
    (e.g., price changes, market cap, volume, etc.) from CoinGecko.

    Args:
        cache: A MarketDataCache instance used to map symbols to CoinGecko IDs, and IDs to comprehensive asset market data.
        raw_assets: A list of dicts representing raw asset data from Coinbase.

    Returns:
        A list of CryptoAsset instances with additional CoinGecko metadata.
    """

    enriched_assets = []
    for asset in raw_assets:
        symbol = asset["symbol"].lower()
        cg_id = await resolve_cg_id(cache, symbol)
        if cg_id is None:
            continue

        asset_md = cache.id_to_market_data[cg_id]
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
    """ """
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
