from typing import Dict, List

from fetchers.coinbase import CoinbaseRequestHandler
from fetchers.coingecko import CoinGeckoFetcher, SymbolCache
from models.portfolio import CryptoAsset

# init CoinGecko classes for constant service across multiple portfolio method invocations


async def get_portfolio() -> List[CryptoAsset]:
    """ """
    cache = SymbolCache()
    await cache.initialize()
    handler = CoinbaseRequestHandler()
    holdings = await handler.get_holdings()
    return await enrich_holdings_with_prices(cache, holdings)


# --- Function to enrich raw assets --- #
async def enrich_holdings_with_prices(
    cache, raw_assets: List[Dict]
) -> List[CryptoAsset]:
    ids = [
        cache.get_id(a["symbol"].lower())
        for a in raw_assets
        if cache.get_id(a["symbol"].lower())
    ]

    valid_ids = []
    asset_to_id_map = {}

    for asset in raw_assets:
        symbol = asset["symbol"].lower()
        cg_id = cache.get_id(symbol)
        if cg_id:
            valid_ids.append(cg_id)
            asset_to_id_map[symbol] = cg_id

    coingecko = CoinGeckoFetcher()
    price_metadata = await coingecko.get_price_metadata(ids)
    print("PM", price_metadata)

    enriched_assets = []
    for asset in raw_assets:
        symbol = asset["symbol"].lower()
        cg_id = asset_to_id_map.get(symbol)
        cg_meta = price_metadata.get(cg_id, {})

        # Add fields to asset
        asset["price_change_24h"] = cg_meta.get("price_change_24h")
        asset["price_change_percentage_24h"] = cg_meta.get(
            "price_change_percentage_24h"
        )
        asset["price_change_7d"] = cg_meta.get("price_change_7d")
        asset["price_change_percentage_7d_in_currency"] = cg_meta.get(
            "price_change_percentage_7d_in_currency"
        )
        asset["price_change_percentage_14d_in_currency"] = cg_meta.get(
            "price_change_percentage_14d_in_currency"
        )
        asset["market_cap"] = cg_meta.get("market_cap")
        asset["image"] = cg_meta.get("image")
        asset["last_updated"] = cg_meta.get("last_updated")

        print("\n", asset)

        enriched_assets.append(CryptoAsset(**asset))

    return enriched_assets
