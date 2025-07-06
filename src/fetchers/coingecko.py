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
        self.page_limit = 250  # to start!
        self.num_pages = 3  # to start!


class CoinGeckoFetcher(CoinGeckoBaseModel):
    """
    Client for querying enriched market metadata (e.g., price changes, market cap)
    from CoinGecko's /coins/markets endpoint.

    Inherits:
        CoinGeckoBaseModel: For shared API config and headers.
    """

    def __init__(self):
        super().__init__()
        # api vars
        self.query_params = lambda page_num: {
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": self.page_limit,
            "page": page_num,
            "price_change_percentage": "24h,7d,14d,30d,200d,1y",
        }

    async def get_top_assets(self) -> Tuple[Dict[str, str], Dict[str, dict]]:
        """
        Calls the CoinGecko /coins/list endpoint and builds a symbol-to-ID mapping.
        Only symbols with both 'symbol' and 'id' fields are included.
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
                        params=self.query_params(page),
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
                                "price_change_percentage_7d": coin.get(
                                    "price_change_percentage_7d_in_currency"
                                ),
                                "price_change_percentage_14d": coin.get(
                                    "price_change_percentage_14d_in_currency"
                                ),
                                "price_change_percentage_30d": coin.get(
                                    "price_change_percentage_30d_in_currency"
                                ),
                                "price_change_percentage_200d": coin.get(
                                    "price_change_percentage_200d_in_currency"
                                ),
                                "price_change_percentage_1y": coin.get(
                                    "price_change_percentage_1y_in_currency"
                                ),
                            }
                            id_to_market_data[coin_id] = MarketData(**cleaned_data)

            return (symbol_to_id, id_to_market_data)

        except Exception as e:
            print(
                f"Failed to fetch top {self.page_limit * self.num_pages} with error: {e}"
            )
            return ({}, {})


class MarketDataCache(CoinGeckoBaseModel):
    """
    In-memory cache for mapping asset symbols (e.g., 'btc') to CoinGecko IDs
    (e.g., 'bitcoin') using the /coins/list endpoint.

    Attributes:
        symbol_to_id (Dict[str, str]): Maps lowercase asset symbols to CoinGecko IDs.
    """

    def __init__(
        self, ttl_seconds: int = 3600, store_backend=None, market_store_backend=None
    ):
        super().__init__()
        # cache dict implementation
        self.symbol_to_id: Dict[str, str] = store_backend or {}
        self.id_to_market_data: Dict[str, MarketData] = market_store_backend or {}
        self._last_refreshed: Optional[datetime] = None
        self.ttl_seconds = ttl_seconds
        # external assets
        self._fetcher = CoinGeckoFetcher()

    async def initialize(self):
        """
        Initializes the symbol cache by calling refresh(). Intended to be used once at startup.
        """
        await self._refresh_cache()

    async def maybe_refresh(self):
        """ """
        if (
            self._last_refreshed is None
            or datetime.now() - self._last_refreshed
            > timedelta(seconds=self.ttl_seconds)
        ):
            await self._refresh_cache()

    async def _refresh_cache(self):
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
