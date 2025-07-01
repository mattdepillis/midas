from typing import Dict, List

from deps.coingecko import get_market_data_cache
from fetchers.coinbase import CoinbaseRequestHandler
from fetchers.coingecko import MarketDataCache
from models.portfolio import CryptoAsset


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
        id = cache.get_id_from_symbol(symbol)
        if id is None:
            print(
                f"Asset with symbol '{symbol}' not in the top {cache.page_limit * cache.number_pages} assets by market cap; not including in portfolio report."
            )
            continue
        asset_md = cache.id_to_market_data[id]

        # --- Add all enriched fields from CoinGecko ---
        for key in [
            "image",
            "market_cap",
            "market_cap_rank",
            "fully_diluted_valuation",
            "total_volume",
            "high_24h",
            "low_24h",
            "price_change_24h",
            "price_change_percentage_24h",
            "market_cap_change_24h",
            "market_cap_change_percentage_24h",
            "circulating_supply",
            "total_supply",
            "max_supply",
            "ath",
            "ath_change_percentage",
            "ath_date",
            "atl",
            "atl_change_percentage",
            "atl_date",
            "price_change_percentage_7d_in_currency",
            "price_change_percentage_14d_in_currency",
            "price_change_percentage_30d_in_currency",
            "price_change_percentage_200d_in_currency",
            "price_change_percentage_1y_in_currency",
            "last_updated",
        ]:
            if key in asset_md:
                short_key = key.replace("_in_currency", "")
                asset[short_key] = asset_md[key]

        enriched_assets.append(CryptoAsset(**asset))

    return enriched_assets
