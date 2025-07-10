from typing import Dict, List

from deps.caches import get_fiat_rate_cache, get_market_data_cache
from fetchers.coinbase import CoinbaseRequestHandler
from fetchers.coingecko import MarketDataCache
from fetchers.frankfurter import FiatRateCache
from models.portfolio_assets import CryptoAsset, FiatAsset
from utils.portfolio_helpers import (
    enrich_crypto_asset,
    enrich_fiat_asset,
    resolve_cg_id,
)


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

        if cg_id is None:
            fiat = enrich_fiat_asset(asset, fiat_cache)
            if fiat:
                enriched_assets.append(fiat)
            continue

        crypto = enrich_crypto_asset(asset, cg_id, market_cache)
        if crypto:
            enriched_assets.append(crypto)

    return enriched_assets
