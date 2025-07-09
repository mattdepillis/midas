import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import httpx  # type: ignore

from models.market_data import MarketData


class CoinGeckoBaseModel:
    """
    Base class for shared CoinGecko configuration, including API key handling,
    base URL, and request headers.

    Attributes:
        api_key (str): API key loaded from environment variable.
        base_url (str): Base URL for the CoinGecko API.
        coins_market_api (str): Endpoint for querying market data.
        headers (Dict[str, str]): Common headers used for API requests.
        page_limit (int): Default pagination size for market requests.
        num_pages (int): Default number of pages to fetch for market requests.
    """

    def __init__(self):
        # vars - apis
        self.api_key = os.getenv("COINGECKO_API_KEY")
        self.base_url = "https://api.coingecko.com/api/v3"
        self.coins_market_api = "/coins/markets"
        self.headers = {
            "accept": "application/json",
            "x-cg-demo-api-key": f"{self.api_key}",
        }
        self.page_limit = 250
        self.num_pages = 3


class CoinGeckoFetcher(CoinGeckoBaseModel):
    """
    Client for querying enriched market metadata (e.g., price changes, market cap)
    from CoinGecko's `/coins/markets` endpoint.

    Inherits:
        CoinGeckoBaseModel: Provides shared base URL, headers, and config values.
    """

    def __init__(self):
        super().__init__()
        # Timeframes to extract price change percentages for
        self.timeframes = ["7d", "14d", "30d", "200d", "1y"]

        # Query params for fetching specific symbols (by comma-separated symbol string)
        self.query_params_specific_symbols = lambda symbols: {
            "vs_currency": "usd",
            "order": "market_cap_desc",  # to ensure that we grab the most relevant
            "symbols": symbols,
            "price_change_percentage": ",".join(self.timeframes),
        }
        # Query params for fetching paginated top assets (e.g., top 750)
        self.query_params_top_assets = lambda page_num: {
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": self.page_limit,
            "page": page_num,
            "price_change_percentage": ",".join(self.timeframes),
        }

    def _extract_clean_price_changes(self, coin: dict) -> dict:
        """
        Extracts simplified price change fields from CoinGecko's
        `_in_currency` fields and renames them to match internal model format.

        Example: price_change_percentage_7d_in_currency → price_change_percentage_7d
        """
        return {
            f"price_change_percentage_{t}": coin.get(
                f"price_change_percentage_{t}_in_currency"
            )
            for t in self.timeframes
        }

    async def get_top_assets(self) -> Tuple[Dict[str, str], Dict[str, dict]]:
        """
        Fetches multiple pages of top coins by market cap using the `/coins/markets` endpoint.
        Returns both a symbol → CoinGecko ID mapping, and a CoinGecko ID → enriched market data mapping.

        Returns:
            - symbol_to_id: Maps lowercase symbols (e.g., 'eth') to CoinGecko IDs (e.g., 'ethereum')
            - id_to_market_data: Maps CoinGecko IDs to `MarketData` objects with price changes and metadata
        """
        try:
            async with httpx.AsyncClient() as client:
                # for now, limit coins to the top 500 by market cap
                symbol_to_id = {}
                id_to_market_data = {}
                for page in range(1, 4):
                    response = await client.get(
                        self.base_url + self.coins_market_api,
                        headers=self.headers,
                        params=self.query_params_top_assets(page),
                    )

                    if response.status_code != 200:
                        raise Exception(
                            f"Failed to fetch list of coins + symbols: {response.status_code} {response.text}"
                        )

                    for coin in response.json():
                        symbol = coin.get("symbol", "").lower()
                        coin_id = coin.get("id")
                        if symbol and coin_id and symbol not in symbol_to_id:
                            symbol_to_id[symbol] = coin_id
                            cleaned_data = {
                                **coin,
                                **self._extract_clean_price_changes(coin),
                            }
                            id_to_market_data[coin_id] = MarketData(**cleaned_data)

            return (symbol_to_id, id_to_market_data)

        except Exception as e:
            print(
                f"Failed to fetch top {self.page_limit * self.num_pages} with error: {e}"
            )
            return ({}, {})

    async def get_coin_market_data_by_symbol(self, symbols: List[str]) -> bool:
        """
        Fetches market data for one or more specific symbols using the `/coins/markets` endpoint.
        Intended to be used for fallback enrichment of non-top-N assets.

        Args:
            symbols: A list of lowercase symbol strings (e.g., ['doge'])

        Returns:
            - CoinGecko ID for the fetched coin (if found)
            - Enriched MarketData object with price and change percentages

            Returns (None, None) if fetch fails or data is not available.
        """
        try:
            async with httpx.AsyncClient() as client:
                # join symbols together in comma-separated string
                symbol_str = ",".join(symbols)
                response = await client.get(
                    self.base_url + self.coins_market_api,
                    headers=self.headers,
                    params=self.query_params_specific_symbols(symbol_str),
                )

                if response.status_code != 200:
                    raise Exception(
                        f"Failed to fetch list of coins + symbols: {response.status_code} {response.text}"
                    )

                coin = response.json()[
                    0
                ]  # for now, assume this is only called for one coin at a time
                coin_id = coin.get("id")
                cleaned_data = {
                    **coin,
                    **self._extract_clean_price_changes(coin),
                }
                coin_market_data = MarketData(**cleaned_data)

                return coin_id, coin_market_data

        except Exception as e:
            print(
                f"Failed to fetch data for coins with symbols '{symbol_str}' with error: {e}"
            )
            return (None, {})


class MarketDataCache(CoinGeckoBaseModel):
    """
    In-memory cache for mapping asset symbols (e.g., 'btc') to CoinGecko IDs
    (e.g., 'bitcoin'), and storing enriched market data for those assets.

    Fetches top-N assets from CoinGecko using the `/coins/markets` endpoint,
    and supports fallback for assets outside the top list.

    Attributes:
        symbol_to_id (Dict[str, str]): Maps lowercase symbols to CoinGecko IDs.
        id_to_market_data (Dict[str, MarketData]): Cached market data for each asset ID.
        ttl_seconds (int): Time-to-live for the cache before triggering refresh.
    """

    def __init__(
        self, ttl_seconds: int = 3600, store_backend=None, market_store_backend=None
    ):
        """
        Initializes the MarketDataCache instance.

        Args:
            ttl_seconds: Duration (in seconds) before cached data is considered stale.
            store_backend: Optional external dict to inject for symbol-to-ID mapping.
            market_store_backend: Optional external dict to inject for market data.
        """
        super().__init__()
        # cache dict implementation
        self.symbol_to_id: Dict[str, str] = store_backend or {}
        self.id_to_market_data: Dict[str, MarketData] = market_store_backend or {}
        self._last_refreshed: Optional[datetime] = None
        self.ttl_seconds = ttl_seconds

        # Internal fetcher that wraps CoinGecko API calls
        self._fetcher = CoinGeckoFetcher()

    async def initialize(self):
        """
        Initializes the cache by refreshing symbol-to-ID mappings and top asset metadata.
        Intended to be called once at application startup.
        """
        await self._refresh_cache()

    async def maybe_refresh(self):
        """
        Checks whether the cache is stale based on the TTL.
        If expired or never initialized, triggers a refresh.
        """
        if (
            self._last_refreshed is None
            or datetime.now() - self._last_refreshed
            > timedelta(seconds=self.ttl_seconds)
        ):
            await self._refresh_cache()

    async def _refresh_cache(self):
        """
        Fetches and caches the top N CoinGecko assets (e.g., top 750 by market cap).

        Populates:
            - symbol_to_id: for resolving symbols to IDs
            - id_to_market_data: for enriched asset metadata
        """
        print("[MarketDataCache] Refreshing cache...")
        (symbol_to_id, id_to_market_data) = await self._fetcher.get_top_assets()
        self.symbol_to_id = {**symbol_to_id}
        self.id_to_market_data = {**id_to_market_data}
        self._last_refreshed = datetime.now()

    def get_id_from_symbol(self, symbol: str) -> Optional[str]:
        """
        Retrieves the CoinGecko ID for a given asset symbol.

        Args:
            symbol (str): Asset symbol (e.g., 'btc', 'eth').

        Returns:
            Optional[str]: Corresponding CoinGecko ID if found; otherwise None.
        """
        coin_id = self.symbol_to_id.get(symbol.lower())
        if not coin_id:
            print(f"[SymbolCache] Warning: No CoinGecko ID found for symbol '{symbol}'")
        return coin_id

    async def get_asset_fallback(self, symbol: str) -> Optional[str]:
        """
        Attempts to fetch market data for an asset not in the top N list,
        using the `/coins/markets?symbols=` fallback endpoint.

        Args:
            symbol (str): Asset symbol to fetch (e.g., 'doge').

        Returns:
            Optional[str]: CoinGecko ID if the fallback fetch succeeds; otherwise None.
        """
        (asset_id, market_data) = await self._fetcher.get_coin_market_data_by_symbol(
            list(symbol)
        )
        if asset_id is not None:
            self.symbol_to_id[symbol] = asset_id
            self.id_to_market_data[asset_id] = market_data
            return asset_id
        print(f"Could not fetch market data for asset with symbol '{symbol}'.")
        return None
