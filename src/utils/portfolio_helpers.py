from typing import Optional

from fetchers.coingecko import MarketDataCache
from fetchers.frankfurter import FiatRateCache
from models.portfolio_assets import CryptoAsset, FiatAsset


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


def enrich_crypto_asset(
    asset: dict, cg_id: str, market_cache: MarketDataCache
) -> Optional[CryptoAsset]:
    """
    Merges raw Coinbase asset data with CoinGecko market data to produce a CryptoAsset.
    """
    try:
        asset_md = market_cache.id_to_market_data[cg_id]
        asset_md_dict = asset_md.dict()
        merged = dict(asset)

        for k, v in asset_md_dict.items():
            cleaned_key = (
                k.replace("_in_currency", "") if k.endswith("_in_currency") else k
            )
            if cleaned_key not in merged:
                merged[cleaned_key] = v

        return CryptoAsset(**merged)

    except Exception as e:
        print(f"Failed to enrich crypto asset '{asset.get('symbol')}': {e}")
        return None


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
