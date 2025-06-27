from typing import Dict, List

from deps.coingecko import get_coingecko_fetcher, get_symbol_cache
from fetchers.coinbase import CoinbaseRequestHandler
from fetchers.coingecko import SymbolCache
from models.portfolio import CryptoAsset


async def get_portfolio() -> List[CryptoAsset]:
    """
    Fetches the user's crypto holdings from Coinbase and enriches them with real-time
    market metadata from CoinGecko.

    Returns:
        A list of CryptoAsset objects with both Coinbase and CoinGecko data combined.
    """
    cache = await get_symbol_cache()
    handler = CoinbaseRequestHandler()
    holdings = await handler.get_holdings()
    return await enrich_holdings_with_prices(cache, holdings)


async def enrich_holdings_with_prices(
    cache: SymbolCache, raw_assets: List[Dict]
) -> List[CryptoAsset]:
    """
    Enriches a list of raw Coinbase assets with additional market metadata
    (e.g., price changes, market cap, volume, etc.) from CoinGecko.

    Args:
        cache: A SymbolCache instance used to map symbols to CoinGecko IDs.
        raw_assets: A list of dicts representing raw asset data from Coinbase.

    Returns:
        A list of CryptoAsset instances with additional CoinGecko metadata.
    """
    valid_ids = []
    asset_to_id_map = {}

    for asset in raw_assets:
        symbol = asset["symbol"].lower()
        cg_id = cache.get_id(symbol)
        if cg_id:
            valid_ids.append(cg_id)
            asset_to_id_map[symbol] = cg_id

    coingecko = await get_coingecko_fetcher()
    price_metadata = await coingecko.get_price_metadata(valid_ids)

    enriched_assets = []
    for asset in raw_assets:
        symbol = asset["symbol"].lower()
        cg_id = asset_to_id_map.get(symbol)
        cg_meta = price_metadata.get(cg_id, {})

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
            if key in cg_meta:
                short_key = key.replace("_in_currency", "")
                asset[short_key] = cg_meta[key]

        enriched_assets.append(CryptoAsset(**asset))

    return enriched_assets
